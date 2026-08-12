"""
Deterministic provider mocks: Creditsafe-shaped credit + EU VIES VAT.

These simulate third-party bureau / tax APIs. An LLM must NEVER invent these values.
Future agents call these as MCP tools; they do not auto-approve deals.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date


def _band(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "E"


def _vat_id(company: dict) -> str:
    country = company["basic_information"]["country"]
    cid = str(company["companyId"]).replace("FI", "").replace("NO", "").replace("PL", "")
    # Illustrative VIES-style ids (not guaranteed real)
    prefix = {"SE": "SE", "FI": "FI", "NO": "NO", "PL": "PL"}.get(country, "EU")
    digits = "".join(ch for ch in cid if ch.isdigit())[:10].ljust(10, "0")
    if country == "SE":
        return f"SE{digits[:10]}01"
    if country == "FI":
        return f"FI{digits[:8]}"
    if country == "NO":
        return f"NO{digits[:9]}MVA"
    if country == "PL":
        return f"PL{digits[:10]}"
    return f"{prefix}{digits}"


def build_creditsafe_mock(company: dict) -> dict:
    """Creditsafe-like credit opinion with explicit confidence metadata."""
    if company.get("creditsafe"):
        return company["creditsafe"]

    risk = company["risk_indicators"]
    basic = company["basic_information"]
    hist = sorted(company["financial_statements_history"], key=lambda x: x["year"])
    latest = hist[-1]
    status = str(basic.get("statusCode", "100"))

    # Start from profitability / distress heuristics (deterministic, not LLM)
    score = 78
    if latest["profitability_margin_pct"] < -20 or latest["ebitda_eur"] < -50_000_000:
        score -= 35
    elif latest["profitability_margin_pct"] < 0:
        score -= 12
    if status in {"118", "180", "103", "291"}:
        score = min(score, 25)
    if risk.get("missingAuditor"):
        score -= 20
    if risk.get("vatReg") is False or risk.get("fTaxReg") is False:
        score -= 15
    if risk.get("connectedBankruptcyCompanies", 0) >= 1:
        score -= 10 * int(risk["connectedBankruptcyCompanies"])
    if risk.get("pepCount", 0) > 0:
        score -= 3
    score = max(1, min(99, score))

    pd = round(max(0.2, (100 - score) / 100 * 18), 2)  # illustrative PD %
    payment = "EXCELLENT"
    if score < 40:
        payment = "POOR"
    elif score < 60:
        payment = "IRREGULAR"
    elif score < 75:
        payment = "GOOD"

    return {
        "provider": "Creditsafe (MOCK)",
        "provider_report_id": f"CS-MOCK-{company['companyId']}",
        "as_of_date": "2026-08-01",
        "credit_score": score,
        "rating_band": _band(score),
        "probability_of_default_pct": pd,
        "payment_behavior": payment,
        "credit_limit_recommendation_eur": int(max(0, score - 40) * 50_000),
        "dbt_days_beyond_terms": 0 if score >= 70 else (15 if score >= 50 else 45),
        "confidence": {
            "score_confidence_0_to_100": 92 if status == "100" else 70,
            "data_freshness": "mock_daily_batch",
            "coverage_note": "Illustrative bureau fields for Northmill case study — not a live Creditsafe pull.",
        },
    }


def build_eu_vat_vies_mock(company: dict) -> dict:
    """EU VIES / VAT register-shaped response."""
    if company.get("eu_vat_vies"):
        return company["eu_vat_vies"]

    risk = company["risk_indicators"]
    basic = company["basic_information"]
    country = basic["country"]
    vat_reg = bool(risk.get("vatReg", True))
    # Norway is EEA; still mock a registration check for demo consistency
    valid = vat_reg and str(basic.get("statusCode", "100")) not in {"118", "291", "300"}

    return {
        "provider": "EU VIES VAT (MOCK)",
        "vat_number": _vat_id(company),
        "member_state": country,
        "request_date": date.today().isoformat(),
        "valid": valid,
        "name": basic["name"],
        "address": f"Registered address on file ({country})",
        "consultation_number": f"WAPIAAAA{str(company['companyId'])[-6:]}",
        "trader_company_type": basic.get("legalGroup"),
        "confidence": {
            "match_confidence_0_to_100": 95 if valid else 40,
            "coverage_note": "Mock VIES-style payload. Production would call ec.europa.eu VIES SOAP/REST.",
        },
    }


def enrich_company_with_provider_mocks(company: dict) -> dict:
    enriched = deepcopy(company)
    enriched["creditsafe"] = build_creditsafe_mock(enriched)
    enriched["eu_vat_vies"] = build_eu_vat_vies_mock(enriched)
    return enriched
