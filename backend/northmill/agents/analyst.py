"""
AI analyst: grounded narrative over registry + web evidence.

AI_PROVIDER in backend/.env:
  auto | bedrock | anthropic | rules

The LLM never changes APPROVED / ESCALATE_TO_COMPLIANCE / REJECTED — only explains evidence.
"""

from __future__ import annotations

import json
import re
from typing import Any

from northmill.agents.prompt_lab import ANALYST_SYSTEM, build_analyst_user_message
from northmill.config import (
    AI_PROVIDER,
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    AWS_REGION,
    BEDROCK_MODEL_ID,
    GROQ_API_KEY,
    GROQ_MODEL,
    USE_BEDROCK,
    groq_model_cascade,
    resolve_ai_stack,
)
from northmill.schema import AdverseMediaSignal, AiAnalysis, AiPromptTrace, ResearchDossier

SYSTEM_PROMPT = ANALYST_SYSTEM


def _evidence_pack(dossier: ResearchDossier, media: list[AdverseMediaSignal]) -> dict[str, Any]:
    return {
        "decision_context": {
            "bank": "NorthBank",
            "use_case": "B2B partner / merchant first-pass screening for Partnerships",
            "question": (
                "Connect hard facts with grounded news; separate evident vs non-evident risks; "
                "flag investigation areas. Do not change the locked classification."
            ),
        },
        "company": dossier.company_name,
        "country": dossier.country_code,
        "policy_recommendation": dossier.recommendation,
        "hard_risk_triggers": dossier.hard_risk_triggers,
        "ownership": dossier.ownership.model_dump(),
        "financial_health": {
            "trend": dossier.financial_health.trend,
            "latest_year": dossier.financial_health.latest_year,
            "latest_revenue_eur": dossier.financial_health.latest_revenue_eur,
            "latest_ebitda_eur": dossier.financial_health.latest_ebitda_eur,
            "latest_margin_pct": dossier.financial_health.latest_margin_pct,
            "history": [h.model_dump() for h in dossier.financial_health.history[:5]],
        },
        "compliance_hard_flags": dossier.compliance_hard_flags.model_dump(),
        "creditsafe": dossier.creditsafe.model_dump() if dossier.creditsafe else None,
        "eu_vat_vies": dossier.eu_vat_vies.model_dump() if dossier.eu_vat_vies else None,
        "externality_coverage": [c.model_dump() for c in dossier.externality_coverage],
        "web_evidence": [m.model_dump() for m in media],
        "reading_notes": [
            "news-Code = 0 means no grounded hit this run, not clearance.",
            "Prefer fact↔news connections over restating either alone.",
        ],
        "output_schema": {
            "executive_brief": "string <= 900 chars; Partnerships-ready memo",
            "cross_checks": ["registry/bureau fact vs web evidence"],
            "supported_findings": ["evident finding with source"],
            "contradictions_or_gaps": ["conflicts or missing evidence / meaningful zeros"],
            "residual_risks": ["non-evident risks + investigation areas"],
            "recommendation_alignment": "AGREES | CAUTIONS_AGAINST_POLICY | INSUFFICIENT_EVIDENCE",
            "confidence_0_to_100": "int",
            "model_provider": "string",
        },
    }


def _parse_json_object(text: str) -> dict[str, Any]:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("No JSON object in model response")
    return json.loads(text[start : end + 1])


def _to_ai_analysis(
    data: dict[str, Any],
    provider: str,
    *,
    prompt_trace: AiPromptTrace | None = None,
) -> AiAnalysis:
    return AiAnalysis(
        executive_brief=str(data.get("executive_brief") or "")[:900],
        cross_checks=[str(x) for x in data.get("cross_checks") or []][:10],
        supported_findings=[str(x) for x in data.get("supported_findings") or []][:10],
        contradictions_or_gaps=[str(x) for x in data.get("contradictions_or_gaps") or []][:10],
        residual_risks=[str(x) for x in data.get("residual_risks") or []][:10],
        recommendation_alignment=str(
            data.get("recommendation_alignment") or "INSUFFICIENT_EVIDENCE"
        ),
        confidence_0_to_100=int(data.get("confidence_0_to_100") or 50),
        model_provider=provider,
        prompt_trace=prompt_trace,
    )


def _make_analyst_trace(
    *,
    model: str,
    user_message: str,
    raw_response: str,
    used_llm: bool,
) -> AiPromptTrace:
    return AiPromptTrace(
        purpose="analyst",
        model=model,
        system_prompt=SYSTEM_PROMPT,
        user_message=user_message,
        raw_response=raw_response,
        used_llm=used_llm,
    )


def _deterministic_analyst(
    dossier: ResearchDossier, media: list[AdverseMediaSignal]
) -> AiAnalysis:
    findings: list[str] = []
    cross: list[str] = []
    gaps: list[str] = []
    residual: list[str] = []

    fh = dossier.financial_health
    risk_media = [m for m in media if m.risk_category != "None"]
    context_media = [m for m in media if m.risk_category == "None"]
    person_media = [m for m in media if m.subject_type == "person"]

    cross.append(
        f"Registry finance trend is {fh.trend}; latest EBITDA {fh.latest_year} "
        f"= EUR {fh.latest_ebitda_eur:,.0f} (from registry tool, not from news)."
    )
    if dossier.creditsafe:
        cross.append(
            f"Creditsafe MOCK score={dossier.creditsafe.credit_score} "
            f"band={dossier.creditsafe.rating_band} "
            f"payment={dossier.creditsafe.payment_behavior}."
        )
    if dossier.ownership.status_code in {"118", "180", "103"}:
        findings.append(
            f"Official status {dossier.ownership.status_code} "
            f"({dossier.ownership.status_description}) requires compliance escalation."
        )
    for t in dossier.hard_risk_triggers[:5]:
        findings.append(f"Policy trigger: {t}")

    for m in risk_media[:5]:
        who = m.subject_name or dossier.company_name
        findings.append(
            f"Adverse web [{m.subject_type}/{who} · {m.source_name}/{m.severity}]: "
            f"{m.headline} — \"{m.verbatim_quote[:140]}\""
        )

    for m in context_media[:3]:
        cross.append(f"Context (non-adverse) from {m.source_name}: {m.headline}.")

    if not risk_media:
        gaps.append(
            f"No adverse trusted-domain hits; {len(context_media)} context/neutral article(s)."
        )
    if not person_media:
        gaps.append(
            "No person-level adverse hits for CEO/board in this run "
            "(does not prove absence of risk)."
        )
    if dossier.compliance_hard_flags.pep_count > 0:
        residual.append(
            f"Registry PEP indicator={dossier.compliance_hard_flags.pep_count}: "
            "confirm with live PEP provider; person deep-dive may still miss homonyms."
        )

    why = {
        "APPROVED": "Clean first-pass — no reject/escalate rules fired.",
        "ESCALATE_TO_COMPLIANCE": "Grey zone (PEP / mid credit / medium media) — compliance judgment.",
        "REJECTED": "Hard fail (bankruptcy, invalid VAT, critical media, etc.).",
    }.get(dossier.recommendation, "Human review required.")

    brief = (
        f"{dossier.company_name} -> {dossier.recommendation.replace('_', ' ')}. "
        f"{why} Finance: {fh.trend}. "
        f"Adverse media: {len(risk_media)}; person hits: {len(person_media)}."
    )[:400]

    conf = 70
    if dossier.hard_risk_triggers:
        conf += 5
    if risk_media:
        conf += 10
    conf = min(90, conf)

    return AiAnalysis(
        executive_brief=brief,
        cross_checks=cross[:8],
        supported_findings=findings[:8],
        contradictions_or_gaps=gaps[:8],
        residual_risks=residual[:8],
        recommendation_alignment="AGREES",
        confidence_0_to_100=conf,
        model_provider="grounded_rules_analyst",
    )


def _analyze_via_anthropic(pack: dict[str, Any], model: str, user_message: str) -> AiAnalysis:
    import urllib.request

    body = json.dumps(
        {
            "model": model,
            "max_tokens": 1200,
            "temperature": 0,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_message}],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "content-type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    text = "".join(
        block.get("text", "")
        for block in payload.get("content", [])
        if block.get("type") == "text"
    )
    return _to_ai_analysis(
        _parse_json_object(text),
        f"anthropic:{model}",
        prompt_trace=_make_analyst_trace(
            model=f"anthropic:{model}",
            user_message=user_message,
            raw_response=text,
            used_llm=True,
        ),
    )


def _analyze_via_bedrock(pack: dict[str, Any], model: str, user_message: str) -> AiAnalysis:
    import boto3

    client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    response = client.converse(
        modelId=model,
        system=[{"text": SYSTEM_PROMPT}],
        messages=[{"role": "user", "content": [{"text": user_message}]}],
        inferenceConfig={"temperature": 0.0, "maxTokens": 1200},
    )
    text = response["output"]["message"]["content"][0]["text"]
    return _to_ai_analysis(
        _parse_json_object(text),
        f"bedrock:{model}",
        prompt_trace=_make_analyst_trace(
            model=f"bedrock:{model}",
            user_message=user_message,
            raw_response=text,
            used_llm=True,
        ),
    )


def _analyze_via_groq(pack: dict[str, Any], model: str, user_message: str) -> AiAnalysis:
    import urllib.error
    import urllib.request

    body = json.dumps(
        {
            "model": model,
            "temperature": 0,
            "max_tokens": 1200,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=body,
        headers={
            "content-type": "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "User-Agent": "northmill-partner-research/0.2",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"Groq HTTP {exc.code}: {detail}") from exc
    text = payload["choices"][0]["message"]["content"]
    return _to_ai_analysis(
        _parse_json_object(text),
        f"groq:{model}",
        prompt_trace=_make_analyst_trace(
            model=f"groq:{model}",
            user_message=user_message,
            raw_response=text,
            used_llm=True,
        ),
    )


def analyze_dossier_and_sources(
    dossier: ResearchDossier,
    media: list[AdverseMediaSignal],
) -> AiAnalysis:
    pack = _evidence_pack(dossier, media)
    user_message = build_analyst_user_message(pack)
    stack = resolve_ai_stack()
    provider = stack["ai_provider"]
    model = stack["ai_model"]
    errors: list[str] = []

    def _try(label: str, fn):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{label} failed: {type(exc).__name__}: {exc}")
            return None

    result: AiAnalysis | None = None
    if provider == "bedrock" and (USE_BEDROCK or AI_PROVIDER == "bedrock"):
        result = _try(
            "Bedrock",
            lambda: _analyze_via_bedrock(pack, model or BEDROCK_MODEL_ID, user_message),
        )
    elif provider == "anthropic" and ANTHROPIC_API_KEY:
        result = _try(
            "Anthropic",
            lambda: _analyze_via_anthropic(pack, model or ANTHROPIC_MODEL, user_message),
        )
    elif provider == "groq" and GROQ_API_KEY:
        for gm in groq_model_cascade():
            result = _try(
                f"Groq:{gm}",
                lambda m=gm: _analyze_via_groq(pack, m, user_message),
            )
            if result is not None:
                break
    elif AI_PROVIDER == "auto":
        if USE_BEDROCK:
            result = _try(
                "Bedrock",
                lambda: _analyze_via_bedrock(pack, BEDROCK_MODEL_ID, user_message),
            )
        if result is None and ANTHROPIC_API_KEY:
            result = _try(
                "Anthropic",
                lambda: _analyze_via_anthropic(pack, ANTHROPIC_MODEL, user_message),
            )
        if result is None and GROQ_API_KEY:
            for gm in groq_model_cascade():
                result = _try(
                    f"Groq:{gm}",
                    lambda m=gm: _analyze_via_groq(pack, m, user_message),
                )
                if result is not None:
                    break

    if result is not None:
        if errors:
            # Soft note that a cheaper model may have been used after a failure
            note = f"Model cascade notes: {'; '.join(errors[:3])}"
            result = result.model_copy(
                update={
                    "residual_risks": list(result.residual_risks)[:9] + [note],
                }
            )
        return result

    analysis = _deterministic_analyst(dossier, media)
    raw = json.dumps(analysis.model_dump(exclude={"prompt_trace"}), indent=2)
    if errors:
        analysis = analysis.model_copy(
            update={
                "residual_risks": analysis.residual_risks
                + [f"LLM provider fallback → grounded-rules ({'; '.join(errors[:2])})"]
            }
        )
    return analysis.model_copy(
        update={
            "prompt_trace": _make_analyst_trace(
                model="grounded_rules_analyst",
                user_message=user_message,
                raw_response=raw,
                used_llm=False,
            )
        }
    )


def strip_unquoted_claims(text: str) -> str:
    return re.sub(r"“”|\"\"", "", text)
