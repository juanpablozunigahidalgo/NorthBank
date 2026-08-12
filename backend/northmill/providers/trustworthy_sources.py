"""Trustworthy news source policy for Nordic/EU partnership research."""

from __future__ import annotations

from urllib.parse import urlparse

# Domains we treat as "trustworthy enough" for a first-pass bank research draft.
# Blogs, forums, aggregators without editorial standards are excluded.
TRUSTED_DOMAINS: dict[str, str] = {
    # Global wire / financial press
    "reuters.com": "Reuters",
    "www.reuters.com": "Reuters",
    "bloomberg.com": "Bloomberg",
    "www.bloomberg.com": "Bloomberg",
    "ft.com": "Financial Times",
    "www.ft.com": "Financial Times",
    "wsj.com": "Wall Street Journal",
    "www.wsj.com": "Wall Street Journal",
    "apnews.com": "Associated Press",
    "www.apnews.com": "Associated Press",
    # Sweden
    "di.se": "Dagens Industri",
    "www.di.se": "Dagens Industri",
    "dn.se": "Dagens Nyheter",
    "www.dn.se": "Dagens Nyheter",
    "svd.se": "Svenska Dagbladet",
    "www.svd.se": "Svenska Dagbladet",
    "svt.se": "SVT",
    "www.svt.se": "SVT",
    # Finland
    "hs.fi": "Helsingin Sanomat",
    "www.hs.fi": "Helsingin Sanomat",
    "yle.fi": "Yle",
    "www.yle.fi": "Yle",
    "kauppalehti.fi": "Kauppalehti",
    "www.kauppalehti.fi": "Kauppalehti",
    # Norway
    "e24.no": "E24",
    "www.e24.no": "E24",
    "dn.no": "Dagens Næringsliv",
    "www.dn.no": "Dagens Næringsliv",
    "nrk.no": "NRK",
    "www.nrk.no": "NRK",
    # Poland / EU
    "rp.pl": "Rzeczpospolita",
    "www.rp.pl": "Rzeczpospolita",
    "pb.pl": "Puls Biznesu",
    "www.pb.pl": "Puls Biznesu",
    "pap.pl": "PAP",
    "www.pap.pl": "PAP",
    # Regulators / official
    "fi.se": "Finansinspektionen",
    "www.fi.se": "Finansinspektionen",
    "finanssivalvonta.fi": "FIN-FSA",
    "www.finanssivalvonta.fi": "FIN-FSA",
    "finanstilsynet.no": "Finanstilsynet",
    "www.finanstilsynet.no": "Finanstilsynet",
    "knf.gov.pl": "KNF",
    "www.knf.gov.pl": "KNF",
    "europa.eu": "EU Official",
    "ec.europa.eu": "European Commission",
}

RISK_QUERY_SUFFIX = (
    "(lawsuit OR litigation OR bankruptcy OR reconstruction OR fine OR "
    "sanction OR fraud OR investigation OR layoff OR insolvency)"
)


def hostname(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:  # noqa: BLE001
        return ""


def is_trusted_url(url: str) -> bool:
    host = hostname(url)
    if not host:
        return False
    if host in TRUSTED_DOMAINS or f"www.{host}" in TRUSTED_DOMAINS:
        return True
    # allow subdomains of trusted registrable domains (e.g. markets.ft.com)
    return any(host.endswith("." + d.removeprefix("www.")) for d in TRUSTED_DOMAINS)


def source_name_for_url(url: str) -> str:
    host = hostname(url)
    for domain, name in TRUSTED_DOMAINS.items():
        d = domain.removeprefix("www.")
        if host == d or host.endswith("." + d):
            return name
    return host or "Unknown"


def is_article_url(url: str) -> bool:
    """Reject outlet homepages; require a path that looks like an article permalink."""
    try:
        parsed = urlparse(url)
        path = (parsed.path or "").rstrip("/")
        if not path:
            return False
        # Too shallow: /se, /en, /news alone often aren't articles
        parts = [p for p in path.split("/") if p]
        if len(parts) < 2 and not any(ch.isdigit() for ch in path):
            return False
        # Explicit homepage patterns
        if path.lower() in {"", "/", "/home", "/index.html"}:
            return False
        return True
    except Exception:  # noqa: BLE001
        return False


def is_trusted_article_url(url: str) -> bool:
    return is_trusted_url(url) and is_article_url(url)


def trust_notes() -> list[str]:
    return [
        "Only editorial / wire / regulator domains are accepted for adverse-media flags.",
        "Social media, forums, and unverified blogs are excluded from first-pass risk flags.",
        "A flag without article URL + verbatim quote is discarded (anti-hallucination gate).",
        "Outlet homepages (e.g. ft.com/) are rejected; only article permalinks count as sources.",
    ]
