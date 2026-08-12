"""
Deterministic Northmill partnership risk policy.

IMPORTANT (anti-hallucination):
- Recommendation is computed ONLY from structured registry / bureau / media evidence.
- An LLM may explain the dossier but MUST NOT change APPROVED / ESCALATE / REJECTED.
- Future decision-agents may READ these rules; they must NOT auto-bind commercial approvals.
"""

from __future__ import annotations

from northmill.schema import AdverseMediaSignal, RiskDecision

# Roaring-style status codes that block commercial progress
ESCALATE_STATUS_CODES = {"118", "180", "103", "111", "132", "291"}

POLICY_RULES: list[dict] = [
    {
        "id": "R1_STATUS_CRITICAL",
        "if": "statusCode in {118,180,103,111,132,291}",
        "then": "REJECTED",
        "why": "Bankruptcy / reconstruction / non-active — clear first-pass reject.",
    },
    {
        "id": "R2_MISSING_AUDITOR",
        "if": "missingAuditor == true",
        "then": "REJECTED",
        "why": "Regulatory filing gap serious enough to reject in first-pass.",
    },
    {
        "id": "R3_VAT_INVALID",
        "if": "eu_vat_vies.valid == false OR vatReg/fTaxReg == false",
        "then": "REJECTED",
        "why": "Tax registration / VIES failure — clear reject.",
    },
    {
        "id": "R4_CREDITSAFE_VERY_LOW",
        "if": "creditsafe.credit_score < 40 OR rating_band == E",
        "then": "REJECTED",
        "why": "Very weak bureau credit opinion — reject.",
    },
    {
        "id": "R5_CONNECTED_BANKRUPTCIES",
        "if": "connectedBankruptcyCompanies >= 2",
        "then": "REJECTED",
        "why": "Related-party insolvency pattern — reject.",
    },
    {
        "id": "R6_CRITICAL_ADVERSE_MEDIA",
        "if": "trusted adverse media severity in {HIGH,CRITICAL} and category != None",
        "then": "REJECTED",
        "why": "Grounded serious adverse press — reject.",
    },
    {
        "id": "R7_CREDITSAFE_LOW",
        "if": "40 <= credit_score < 60",
        "then": "ESCALATE_TO_COMPLIANCE",
        "why": "Mid credit / elevated PD — grey zone; compliance judgment.",
    },
    {
        "id": "R8_PEP",
        "if": "pepCount > 0",
        "then": "ESCALATE_TO_COMPLIANCE",
        "why": "PEP exposure — not automatic reject; compliance must clear.",
    },
    {
        "id": "R9_MEDIUM_MEDIA",
        "if": "trusted adverse media severity == MEDIUM",
        "then": "ESCALATE_TO_COMPLIANCE",
        "why": "Material but non-critical press — grey zone for compliance.",
    },
    {
        "id": "R10_DEFAULT",
        "if": "no reject/escalate rules fired",
        "then": "APPROVED",
        "why": "Clean first-pass automated checks.",
    },
]


def infer_financial_trend(history: list[dict]) -> str:
    if not history:
        return "UNKNOWN"
    ordered = sorted(history, key=lambda x: x["year"])
    latest = ordered[-1]
    if latest["ebitda_eur"] < -50_000_000 or latest["profitability_margin_pct"] < -20:
        return "DISTRESSED"
    if len(ordered) < 2:
        return "STABLE"
    prev = ordered[-2]
    rev_delta = latest["revenue_eur"] - prev["revenue_eur"]
    ebitda_improving = latest["ebitda_eur"] > prev["ebitda_eur"]
    if rev_delta > 0 and ebitda_improving:
        return "GROWING"
    if rev_delta < 0 and not ebitda_improving:
        return "DECLINING"
    return "STABLE"


def evaluate_hard_triggers(
    company: dict,
    adverse_media: list[AdverseMediaSignal],
) -> tuple[RiskDecision, list[str], list[str]]:
    """
    Apply bank-safe deterministic rules first.
    Returns (recommendation, hard_risk_triggers, unsure_notes).
    """
    basic = company["basic_information"]
    risk = company["risk_indicators"]
    creditsafe = company.get("creditsafe") or {}
    vies = company.get("eu_vat_vies") or {}
    triggers: list[str] = []
    fired: list[str] = []
    unsure: list[str] = [
        "Re-validate entity identity (similar company names are a common false-positive risk).",
    ]

    status = str(basic.get("statusCode", "100"))
    if status in ESCALATE_STATUS_CODES:
        triggers.append(
            f"[R1] CRITICAL statusCode={status} ({basic.get('statusDescription')})"
        )
        fired.append("R1_STATUS_CRITICAL")

    if risk.get("missingAuditor"):
        triggers.append("[R2] missingAuditor=true - regulatory non-compliance signal")
        fired.append("R2_MISSING_AUDITOR")

    vat_gap = risk.get("vatReg") is False or risk.get("fTaxReg") is False
    vies_invalid = vies.get("valid") is False
    if vat_gap or vies_invalid:
        triggers.append(
            f"[R3] VAT/VIES issue (vatReg={risk.get('vatReg')}, "
            f"fTaxReg={risk.get('fTaxReg')}, vies.valid={vies.get('valid')})"
        )
        fired.append("R3_VAT_INVALID")

    cs_score = int(creditsafe.get("credit_score") or 70)
    cs_band = str(creditsafe.get("rating_band") or "C")
    if cs_score < 40 or cs_band == "E":
        triggers.append(
            f"[R4] Creditsafe MOCK score={cs_score} band={cs_band} "
            f"(PD~{creditsafe.get('probability_of_default_pct')}%)"
        )
        fired.append("R4_CREDITSAFE_VERY_LOW")

    if risk.get("connectedBankruptcyCompanies", 0) >= 2:
        triggers.append(
            f"[R5] connectedBankruptcyCompanies={risk['connectedBankruptcyCompanies']}"
        )
        fired.append("R5_CONNECTED_BANKRUPTCIES")

    critical_media = [
        m
        for m in adverse_media
        if m.severity in ("HIGH", "CRITICAL") and m.risk_category != "None"
    ]
    for m in critical_media:
        triggers.append(f"[R6] Adverse media [{m.severity}/{m.subject_type}]: {m.headline}")
        fired.append("R6_CRITICAL_ADVERSE_MEDIA")

    if 40 <= cs_score < 60 and "R4_CREDITSAFE_VERY_LOW" not in fired:
        triggers.append(f"[R7] Creditsafe MOCK score={cs_score} band={cs_band} - elevated risk")
        fired.append("R7_CREDITSAFE_LOW")

    pep = int(risk.get("pepCount") or 0)
    if pep > 0:
        triggers.append(
            f"[R8] pepCount={pep} - PEP exposure (not approved until cleared)"
        )
        fired.append("R8_PEP")

    medium_media = [
        m for m in adverse_media if m.severity == "MEDIUM" and m.risk_category != "None"
    ]
    for m in medium_media:
        triggers.append(f"[R9] Adverse media [MEDIUM/{m.subject_type}]: {m.headline}")
        fired.append("R9_MEDIUM_MEDIA")

    reject_ids = {
        "R1_STATUS_CRITICAL",
        "R2_MISSING_AUDITOR",
        "R3_VAT_INVALID",
        "R4_CREDITSAFE_VERY_LOW",
        "R5_CONNECTED_BANKRUPTCIES",
        "R6_CRITICAL_ADVERSE_MEDIA",
    }
    escalate_ids = {"R7_CREDITSAFE_LOW", "R8_PEP", "R9_MEDIUM_MEDIA"}

    if any(r in reject_ids for r in fired):
        decision: RiskDecision = "REJECTED"
    elif any(r in escalate_ids for r in fired) or (
        triggers and not any(r in reject_ids for r in fired)
    ):
        decision = "ESCALATE_TO_COMPLIANCE"
    else:
        decision = "APPROVED"
        fired.append("R10_DEFAULT")

    unsure.append(f"policy_rules_fired={','.join(dict.fromkeys(fired))}")
    return decision, triggers, unsure


def get_policy_rules_document() -> dict:
    return {
        "version": "1.2",
        "human_in_the_loop": True,
        "llm_may_change_recommendation": False,
        "outputs": ["APPROVED", "ESCALATE_TO_COMPLIANCE", "REJECTED"],
        "logic_summary": (
            "Classification is 100% DETERMINISTIC: pure numeric thresholds "
            "(credit score/band, pepCount, connected bankruptcies, etc.) and pure "
            "if→then criteria (status codes, VAT validity, media severity). "
            "The LLM never computes or changes Approved / Escalate / Rejected — "
            "it only explains connections between hard facts and grounded news."
        ),
        "future_agents": (
            "Agents may call MCP tools and propose drafts; commercial approval stays human."
        ),
        "rules": POLICY_RULES,
    }
