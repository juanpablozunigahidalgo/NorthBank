"""Build research dossier: deterministic policy first, optional AI narrative."""

from __future__ import annotations

import json
from typing import Any

from northmill.config import AWS_REGION, BEDROCK_MODEL_ID, USE_BEDROCK, resolve_ai_stack
from northmill.policy.engine import evaluate_hard_triggers, infer_financial_trend
from northmill.schema import (
    AdverseMediaSignal,
    ComplianceHardFlags,
    CreditsafeSignal,
    EuVatViesSignal,
    ExternalityThemeCoverage,
    FinancialHealthSignal,
    FinancialYear,
    OwnershipSummary,
    ResearchDossier,
)


def _build_base_dossier(
    company: dict,
    adverse_media: list[AdverseMediaSignal],
    elapsed_ms: int | None = None,
    externality_coverage: list[ExternalityThemeCoverage] | None = None,
) -> ResearchDossier:
    basic = company["basic_information"]
    risk = company["risk_indicators"]
    positions = company["positions"]
    relations = company["corporate_relations"]
    history_raw = company["financial_statements_history"]
    history = [FinancialYear.model_validate(h) for h in history_raw]
    latest = sorted(history, key=lambda h: h.year)[-1]
    unsure = [
        "Confirm similarly-named entities before acting on this draft.",
        "PEP/sanctions should be re-checked in a live compliance provider for production use.",
    ]
    if int(risk.get("pepCount") or 0) > 0:
        unsure.append(
            "PEP flagged: person deep-dive ran on trusted news; "
            "homonym / incomplete coverage remains possible."
        )
    decision, triggers, policy_unsure = evaluate_hard_triggers(company, adverse_media)
    unsure = [*policy_unsure[:2], *unsure]

    visible_media = [m for m in adverse_media if m.verbatim_quote and m.source_url]

    sources = [
        "mock_registry://roaring-allabolag-shaped",
        "mock_creditsafe://bureau-opinion",
        "mock_eu_vies://vat-register",
        "mock_adverse_media://grounded-snippets",
    ]
    sources.extend(sorted({m.source_url for m in visible_media}))

    notes: list[str] = []
    if risk.get("pepCount"):
        notes.append(f"PEP indicator count={risk['pepCount']}")
    if relations.get("unusual_ownership_patterns"):
        notes.append(str(relations["unusual_ownership_patterns"]))

    creditsafe = (
        CreditsafeSignal.model_validate(company["creditsafe"])
        if company.get("creditsafe")
        else None
    )
    eu_vat = (
        EuVatViesSignal.model_validate(company["eu_vat_vies"])
        if company.get("eu_vat_vies")
        else None
    )

    cs_bit = (
        f"Creditsafe={creditsafe.credit_score}/{creditsafe.rating_band}. "
        if creditsafe
        else ""
    )
    vies_bit = f"VIES.valid={eu_vat.valid}. " if eu_vat else ""
    summary = (
        f"{basic['name']} ({basic['country']}) status={basic['statusCode']}. "
        f"Recommendation={decision}. {cs_bit}{vies_bit}"
        f"Hard triggers={len(triggers)}. Media={len(visible_media)}. "
        f"EBITDA {latest.year}=EUR {latest.ebitda_eur:,.0f}."
    )[:400]

    return ResearchDossier(
        company_id=str(company["companyId"]),
        company_name=basic["name"],
        country_code=basic["country"],
        recommendation=decision,
        ownership=OwnershipSummary(
            legal_structure=basic["legalGroup"],
            status_code=str(basic["statusCode"]),
            status_description=basic["statusDescription"],
            ceo=positions.get("ceo"),
            board_of_directors=list(positions.get("board_of_directors") or []),
            ultimate_beneficial_owners=list(
                relations.get("ultimate_beneficial_owners") or []
            ),
            parent_company=relations.get("parent_company"),
            unusual_ownership_patterns=relations.get("unusual_ownership_patterns"),
        ),
        financial_health=FinancialHealthSignal(
            latest_year=latest.year,
            latest_revenue_eur=latest.revenue_eur,
            latest_ebitda_eur=latest.ebitda_eur,
            latest_margin_pct=latest.profitability_margin_pct,
            trend=infer_financial_trend(history_raw),  # type: ignore[arg-type]
            history=sorted(history, key=lambda h: h.year, reverse=True),
        ),
        compliance_hard_flags=ComplianceHardFlags(
            sanctions_list_match=False,
            pep_count=int(risk.get("pepCount") or 0),
            missing_auditor=bool(risk.get("missingAuditor")),
            vat_registered=risk.get("vatReg"),
            f_tax_registered=risk.get("fTaxReg"),
            connected_bankruptcy_companies=int(
                risk.get("connectedBankruptcyCompanies") or 0
            ),
            notes=notes,
        ),
        creditsafe=creditsafe,
        eu_vat_vies=eu_vat,
        adverse_media=visible_media,
        externality_coverage=list(externality_coverage or []),
        hard_risk_triggers=triggers,
        unsure_or_unverified=unsure,
        sources=sources,
        audit_summary=summary,
        elapsed_ms=elapsed_ms,
    )


def _bedrock_enrich_summary(
    dossier: ResearchDossier,
    company: dict,
    adverse_media: list[AdverseMediaSignal],
) -> ResearchDossier:
    import boto3

    client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    payload = {
        "company": company["basic_information"]["name"],
        "recommendation": dossier.recommendation,
        "hard_risk_triggers": dossier.hard_risk_triggers,
        "trend": dossier.financial_health.trend,
        "media": [m.model_dump() for m in adverse_media],
        "instruction": (
            "Write a <=300 char audit_summary for Northmill Partnerships. "
            "Do not invent financial figures. Do not change the recommendation. "
            "Return JSON only: {\"audit_summary\": \"...\"}"
        ),
    }
    response = client.converse(
        modelId=BEDROCK_MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [{"text": json.dumps(payload)}],
            }
        ],
        inferenceConfig={"temperature": 0.0, "maxTokens": 400},
    )
    text = response["output"]["message"]["content"][0]["text"]
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        parsed: dict[str, Any] = json.loads(text[start : end + 1])
        summary = str(parsed.get("audit_summary") or dossier.audit_summary)[:400]
        return dossier.model_copy(update={"audit_summary": summary})
    return dossier


def synthesize_dossier(
    company: dict,
    adverse_media: list[AdverseMediaSignal],
    elapsed_ms: int | None = None,
    externality_coverage: list[ExternalityThemeCoverage] | None = None,
) -> tuple[ResearchDossier, str]:
    from northmill.agents.analyst import analyze_dossier_and_sources

    dossier = _build_base_dossier(
        company,
        adverse_media,
        elapsed_ms=elapsed_ms,
        externality_coverage=externality_coverage,
    )
    stack = resolve_ai_stack()

    if USE_BEDROCK:
        try:
            dossier = _bedrock_enrich_summary(dossier, company, adverse_media)
        except Exception as exc:  # noqa: BLE001
            unsure = list(dossier.unsure_or_unverified)
            unsure.append(
                f"Bedrock summary unavailable ({type(exc).__name__}); kept rules-based summary."
            )
            dossier = dossier.model_copy(update={"unsure_or_unverified": unsure})

    analysis = analyze_dossier_and_sources(dossier, adverse_media)
    engine_label = (
        f"{stack['ai_provider']}:{stack['ai_model']} + policy engine "
        "(LLM cannot change verdict)"
    )

    dossier = dossier.model_copy(
        update={
            "ai_analysis": analysis,
            "audit_summary": analysis.executive_brief[:400] or dossier.audit_summary,
        }
    )
    return dossier, engine_label
