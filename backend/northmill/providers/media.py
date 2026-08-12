"""Adverse media: multi-theme externality search (trusted domains) for company + key people."""

from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from functools import lru_cache

from northmill.config import DATA_DIR, USE_LIVE_NEWS
from northmill.providers.externalities import (
    COMPANY_EXTERNALITIES,
    PERSON_EXTERNALITIES,
    company_search_plan,
    infer_theme_from_text,
    person_search_plan,
    theme_by_id,
)
from northmill.providers.trustworthy_sources import (
    is_trusted_article_url,
    is_trusted_url,
    source_name_for_url,
    trust_notes,
)
from northmill.schema import AdverseMediaSignal, ExternalityThemeCoverage

MEDIA_PATH = DATA_DIR / "mock_adverse_media.json"
DOSSIER_TOP_N = int(os.getenv("MEDIA_TOP_N", "12"))
# Full taxonomy by default so Research can show news-Code = 0 for empty dimensions.
MAX_COMPANY_THEMES = int(
    os.getenv("MAX_COMPANY_EXTERNALITY_QUERIES", str(len(COMPANY_EXTERNALITIES)))
)
MAX_PERSON_THEMES = int(
    os.getenv("MAX_PERSON_EXTERNALITY_QUERIES", str(len(PERSON_EXTERNALITIES)))
)
MAX_PEOPLE = int(os.getenv("MAX_PERSON_EXTERNALITY_PEOPLE", "1"))  # mockup: CEO only
MEDIA_SEARCH_WORKERS = int(os.getenv("MEDIA_SEARCH_WORKERS", "4"))
PER_THEME_KEEP = int(os.getenv("MEDIA_PER_THEME_KEEP", "2"))

_ALIAS_KEYS: list[tuple[str, str]] = [
    ("northvolt", "northvolt"),
    ("klarna", "klarna"),
    ("spotify", "spotify"),
    ("voi technology", "voi"),
    ("voi ", "voi"),
    ("h & m", "h&m"),
    ("hennes", "h&m"),
    ("ericsson", "ericsson"),
    ("volvo car", "volvo car"),
    ("wolt", "wolt"),
    ("supercell", "supercell"),
    ("nokia", "nokia"),
    ("neste", "neste"),
    ("f-secure", "f-secure"),
    ("f secure", "f-secure"),
    ("vipps", "vipps"),
    ("equinor", "equinor"),
    ("kahoot", "kahoot"),
    ("oda norway", "oda"),
    ("oda ", "oda"),
    ("telenor", "telenor"),
    ("inpost", "inpost"),
    ("cd projekt", "cd projekt"),
    ("allegro", "allegro"),
]

_SEVERITY_RANK = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


@dataclass
class MediaSearchResult:
    signals: list[AdverseMediaSignal] = field(default_factory=list)
    coverage: list[ExternalityThemeCoverage] = field(default_factory=list)
    queries_run: int = 0


@lru_cache(maxsize=1)
def _load_articles() -> dict[str, list[dict]]:
    with MEDIA_PATH.open(encoding="utf-8") as f:
        return json.load(f)["articles"]


def _resolve_key(company_name: str) -> str | None:
    name = company_name.lower()
    for fragment, key in _ALIAS_KEYS:
        if fragment in name:
            return key
    return None


def _infer_category_severity(text: str) -> tuple[str, str]:
    t = text.lower()
    if any(k in t for k in ("bankrupt", "insolven", "reconstruction", "rekonstruktion", "konkurs")):
        return "Financial_Distress", "CRITICAL"
    if any(k in t for k in ("lawsuit", "litigation", "sued", "court", "indict", "charged")):
        return "Litigation", "HIGH"
    if any(k in t for k in ("fine", "sanction", "regulator", "probe", "investigation", "pep")):
        return "Regulatory_Sanction", "HIGH"
    if any(k in t for k in ("fraud", "scandal", "bribe", "corruption", "drugs", "narcotics")):
        return "Reputational", "HIGH"
    if any(k in t for k in ("pollution", "environmental", "emissions", "climate")):
        return "Reputational", "MEDIUM"
    if any(k in t for k in ("resign", "layoff", "loss", "debt", "downgrade")):
        return "Financial_Distress", "MEDIUM"
    return "Reputational", "LOW"


def _enrich_theme_fields(item: dict) -> dict:
    theme_id = item.get("externality_theme_id")
    theme = theme_by_id(theme_id) if theme_id else None
    if not theme:
        theme = infer_theme_from_text(
            subject_type=item.get("subject_type") or "company",
            risk_category=item.get("risk_category"),
            text=f"{item.get('headline', '')} {item.get('verbatim_quote', '')}",
        )
    if theme:
        item = {
            **item,
            "externality_theme_id": theme["id"],
            "externality_theme_label": theme["label"],
        }
    return item


def _validate_signal(item: dict, *, require_trusted_domain: bool = True) -> AdverseMediaSignal | None:
    quote = (item.get("verbatim_quote") or "").strip()
    url = (item.get("source_url") or "").strip()
    if not quote or not url:
        return None
    if require_trusted_domain and not is_trusted_article_url(url):
        return None
    if not require_trusted_domain:
        from northmill.providers.trustworthy_sources import is_article_url

        if not is_article_url(url):
            return None
    try:
        return AdverseMediaSignal.model_validate(_enrich_theme_fields(item))
    except Exception:  # noqa: BLE001
        return None


def _mock_signals(company_name: str) -> list[AdverseMediaSignal]:
    key = _resolve_key(company_name)
    raw_items = _load_articles().get(key, []) if key else []
    out: list[AdverseMediaSignal] = []
    for item in raw_items:
        payload = {
            **item,
            "subject_type": item.get("subject_type", "company"),
            "subject_name": item.get("subject_name"),
            "externality_theme_id": item.get("externality_theme_id"),
            "externality_theme_label": item.get("externality_theme_label"),
        }
        sig = _validate_signal(payload, require_trusted_domain=False)
        if sig and (is_trusted_url(sig.source_url) or sig.source_name):
            out.append(sig)
    return out


def _ddgs_client():
    try:
        from ddgs import DDGS

        return DDGS
    except ImportError:
        from duckduckgo_search import DDGS

        return DDGS


def _live_web_signals(
    query_name: str,
    *,
    subject_type: str = "company",
    subject_name: str | None = None,
    risk_suffix: str,
    max_results: int = 4,
    theme_id: str | None = None,
    theme_label: str | None = None,
) -> list[AdverseMediaSignal]:
    try:
        DDGS = _ddgs_client()
    except ImportError:
        return []

    query = f'"{query_name}" {risk_suffix}'
    signals: list[AdverseMediaSignal] = []
    seen: set[str] = set()

    try:
        with DDGS() as ddgs:
            results = list(ddgs.news(query, max_results=max_results)) or []
            if len(results) < 2:
                results.extend(list(ddgs.text(query, max_results=max_results)) or [])
    except Exception:  # noqa: BLE001
        return []

    for row in results:
        url = (row.get("url") or row.get("href") or "").strip()
        if not url or url in seen or not is_trusted_article_url(url):
            continue
        seen.add(url)
        title = (row.get("title") or "").strip()
        body = (row.get("body") or row.get("snippet") or title).strip()
        if not title or not body:
            continue
        quote = re.split(r"(?<=[.!?])\s+", body)[0].strip()
        if len(quote) < 20:
            quote = body[:240].strip()
        category, severity = _infer_category_severity(f"{title} {body}")
        item = {
            "headline": title[:200],
            "source_url": url,
            "source_name": source_name_for_url(url),
            "risk_category": category,
            "severity": severity,
            "verbatim_quote": quote[:400],
            "publication_date": (row.get("date") or None),
            "subject_type": subject_type,
            "subject_name": subject_name or query_name,
            "externality_theme_id": theme_id,
            "externality_theme_label": theme_label,
        }
        sig = _validate_signal(item)
        if sig:
            signals.append(sig)
        if len(signals) >= 3:
            break
    return signals


def _ceo_only(company: dict) -> list[str]:
    """Mockup scope: live person search is CEO only (not board / UBOs / investors)."""
    ceo = (company.get("positions") or {}).get("ceo")
    if not ceo:
        return []
    name = str(ceo).strip()
    return [name] if name else []


def _is_corporate_name(name: str) -> bool:
    lower = name.lower()
    return any(
        tok in lower
        for tok in (
            " ab",
            " as",
            " oy",
            " inc",
            " ltd",
            " ag",
            " ministry",
            " state",
            " family",
            " holding",
            " capital",
            " partners",
        )
    )


def _key_people(company: dict, *, limit: int = 3) -> list[str]:
    """Legacy helper kept for tooling; live dossier search uses _ceo_only."""
    positions = company.get("positions") or {}
    relations = company.get("corporate_relations") or {}
    people: list[str] = []
    ceo = positions.get("ceo")
    if ceo:
        people.append(str(ceo))
    for name in positions.get("board_of_directors") or []:
        people.append(str(name))
    for name in relations.get("ultimate_beneficial_owners") or []:
        if _is_corporate_name(str(name)):
            continue
        people.append(str(name))
    out: list[str] = []
    for p in people:
        if p not in out:
            out.append(p)
    return out[:limit]


def _rank_signals(signals: list[AdverseMediaSignal]) -> list[AdverseMediaSignal]:
    return sorted(
        signals,
        key=lambda m: (
            _SEVERITY_RANK.get(m.severity, 9),
            0 if m.risk_category != "None" else 1,
            m.headline.lower(),
        ),
    )


def _select_for_dossier(signals: list[AdverseMediaSignal]) -> list[AdverseMediaSignal]:
    """Keep diversity across externality themes, then fill by severity."""
    ranked = _rank_signals(signals)
    by_theme: dict[str, list[AdverseMediaSignal]] = defaultdict(list)
    for sig in ranked:
        key = sig.externality_theme_id or "_untagged"
        by_theme[key].append(sig)

    selected: list[AdverseMediaSignal] = []
    seen: set[str] = set()
    for items in by_theme.values():
        for sig in items[:PER_THEME_KEEP]:
            k = f"{sig.source_url}|{sig.headline.lower()}"
            if k in seen:
                continue
            seen.add(k)
            selected.append(sig)

    for sig in ranked:
        if len(selected) >= max(DOSSIER_TOP_N, PER_THEME_KEEP * 6):
            break
        k = f"{sig.source_url}|{sig.headline.lower()}"
        if k in seen:
            continue
        seen.add(k)
        selected.append(sig)

    return _rank_signals(selected)[: max(DOSSIER_TOP_N, min(24, len(selected)))]


def _run_plan(plan: list[dict], *, subject_type: str) -> list[AdverseMediaSignal]:
    if not plan:
        return []

    def _one(step: dict) -> list[AdverseMediaSignal]:
        return _live_web_signals(
            step["query_name"],
            subject_type=subject_type,
            subject_name=step.get("subject_name") or step["query_name"],
            risk_suffix=step["risk_suffix"],
            max_results=3,
            theme_id=step.get("theme_id"),
            theme_label=step.get("theme_label"),
        )

    out: list[AdverseMediaSignal] = []
    workers = max(1, min(MEDIA_SEARCH_WORKERS, len(plan)))
    if workers == 1 or len(plan) == 1:
        for step in plan:
            out.extend(_one(step))
        return out

    from concurrent.futures import ThreadPoolExecutor, as_completed

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_one, step) for step in plan]
        for fut in as_completed(futures):
            try:
                out.extend(fut.result())
            except Exception:  # noqa: BLE001
                continue
    return out


def _build_coverage(
    *,
    signals: list[AdverseMediaSignal],
    searched_theme_ids: set[str],
    include_person_themes: bool,
) -> list[ExternalityThemeCoverage]:
    counts: dict[str, int] = defaultdict(int)
    for sig in signals:
        if sig.externality_theme_id:
            counts[sig.externality_theme_id] += 1

    rows: list[ExternalityThemeCoverage] = []
    for theme in COMPANY_EXTERNALITIES:
        hit = counts.get(theme["id"], 0)
        searched = theme["id"] in searched_theme_ids or not USE_LIVE_NEWS
        rows.append(
            ExternalityThemeCoverage(
                theme_id=theme["id"],
                news_code=theme["news_code"],
                label=theme["label"],
                scope="company",
                hit_count=hit,
                searched=searched,
                summary=f"{theme['news_code']} = {hit}",
            )
        )

    if include_person_themes:
        for theme in PERSON_EXTERNALITIES:
            hit = counts.get(theme["id"], 0)
            searched = theme["id"] in searched_theme_ids or not USE_LIVE_NEWS
            rows.append(
                ExternalityThemeCoverage(
                    theme_id=theme["id"],
                    news_code=theme["news_code"],
                    label=theme["label"],
                    scope="person",
                    hit_count=hit,
                    searched=searched,
                    summary=f"{theme['news_code']} = {hit}",
                )
            )
    return rows


def search_company_adverse_media(
    company_name: str, company: dict | None = None
) -> MediaSearchResult:
    """
    Fan-out externality searches for the company + key persons.
    Returns grounded articles plus per-dimension coverage (including zeros).
    """
    live: list[AdverseMediaSignal] = []
    queries_run = 0
    searched_theme_ids: set[str] = set()
    include_person = bool(company)

    if USE_LIVE_NEWS:
        company_plan = company_search_plan(company_name)[:MAX_COMPANY_THEMES]
        for step in company_plan:
            searched_theme_ids.add(step["theme_id"])
        live.extend(_run_plan(company_plan, subject_type="company"))
        queries_run += len(company_plan)

        if company:
            # Mockup scope: company name themes + CEO themes only (no board / UBO fan-out).
            people = _ceo_only(company)
            hint = company_name.split()[0]
            for person in people:
                person_plan = person_search_plan(person, company_hint=hint)[
                    :MAX_PERSON_THEMES
                ]
                for step in person_plan:
                    searched_theme_ids.add(step["theme_id"])
                live.extend(_run_plan(person_plan, subject_type="person"))
                queries_run += len(person_plan)
    else:
        # Mock / offline: treat full taxonomy as checked against curated corpus.
        searched_theme_ids = {t["id"] for t in COMPANY_EXTERNALITIES}
        if include_person:
            searched_theme_ids |= {t["id"] for t in PERSON_EXTERNALITIES}

    mock = _mock_signals(company_name)
    merged: list[AdverseMediaSignal] = []
    seen: set[str] = set()
    for m in [*live, *mock]:
        key = f"{m.source_url}|{m.headline.lower()}"
        if key in seen:
            continue
        seen.add(key)
        merged.append(m)

    coverage = _build_coverage(
        signals=merged,
        searched_theme_ids=searched_theme_ids,
        include_person_themes=include_person or any(
            m.subject_type == "person" for m in merged
        ),
    )
    top = _select_for_dossier(merged)
    result = MediaSearchResult(signals=top, coverage=coverage, queries_run=queries_run)
    search_company_adverse_media.last_result = result  # type: ignore[attr-defined]
    search_company_adverse_media.last_query_count = queries_run  # type: ignore[attr-defined]
    return result


def news_pipeline_notes(live_count: int, total_count: int) -> list[str]:
    notes = trust_notes()
    notes.append(
        "News engine fans out Externalities for the company name + CEO only (mockup scope)."
    )
    notes.append(
        "Research reports every dimension as news-Code = N (0 when nothing grounded was found)."
    )
    notes.append(
        f"Dossier keeps grounded articles with theme diversity (target ~{DOSSIER_TOP_N})."
    )
    q = getattr(search_company_adverse_media, "last_query_count", None)
    if q is not None:
        notes.append(f"Externality theme queries executed this run≈{q}.")
    if live_count == 0:
        notes.append(
            "Live web search returned 0 trusted-domain hits (or was disabled); "
            "using curated grounded mock articles for demo continuity."
        )
    else:
        notes.append(
            f"Live trusted-domain hits~{live_count}; total after merge/rank={total_count}."
        )
    return notes
