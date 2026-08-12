"""
Prompt contracts shown in the AI Lab page and used by analyst / final brief.

Tuned for instruction-following models (e.g. Llama 3.3 70B on Groq):
clear role, explicit reasoning steps, grounded evidence rules, strict JSON out.
"""

from __future__ import annotations

import json
from typing import Any

from northmill.config import resolve_ai_stack
from northmill.schema import AdverseMediaSignal, ResearchDossier

PARTNERSHIPS_REFLECTION_TASK = """
ROLE
You are a senior financial-risk adviser to NorthBank's Partnerships team.
Your job is a first-pass B2B partner decision support memo: help Partnerships decide
whether this merchant / partner candidate is acceptable to progress, should go to
compliance, or is a hard no — WITHOUT changing the locked policy classification.

NorthBank lens (always keep in mind):
- Credit / default and cash-flow stress that could hit settlement or receivables
- Ownership opacity, PEP, sanctions-adjacent and governance red flags
- Adverse media that implies fraud, bankruptcy, regulatory action, or reputational contagion
- Tax/VAT validity and operational continuity of the counterparty
- What is proven vs what is only suggested and still needs human follow-up

HOW TO THINK (do this mentally, then write the JSON fields)
1) Anchor on HARD FACTS first: registry status, ownership, financial trend/EBITDA,
   Creditsafe score/band/payment behaviour, VIES validity, compliance flags, hard_risk_triggers.
2) Read grounded NEWS only (URL + verbatim quote). Treat each hit as evidence, not truth.
3) CONNECT: for each material news item, say what hard fact it confirms, contradicts,
   amplifies, or leaves unexplained (e.g. bankruptcy news vs registry status / EBITDA).
4) Separate EVIDENT risks (directly supported by facts and/or quotes) from NON-EVIDENT /
   latent risks (plausible implications, patterns, missing data, zero-hit dimensions that
   do not prove safety).
5) Use externality_coverage (news-Code = N). A zero (e.g. news-PEP = 0) means "no grounded
   hit in this run", NOT "cleared". Call out high-value zeros as investigation gaps when
   relevant (PEP, fraud, sanctions, financial distress, person-level themes).
6) End with PRACTICAL next checks a Partnerships / compliance reviewer should run before
   any commercial commitment.

HARD CONSTRAINTS
- Do NOT invent numbers, owners, status codes, dates, or news.
- Do NOT change locked_policy_recommendation / policy classification
  (Approved / Escalate to compliance / Rejected). Explain it; never override it.
- Every media-backed claim must map to a provided quote and URL.
- If evidence is thin, say so and lower confidence. Prefer "insufficient evidence" over speculation.
- Write for a financial engineer / Partnerships analyst: crisp, decision-useful, no fluff.
""".strip()

ANALYST_SYSTEM = """
You are NorthBank's Applied AI risk analyst for B2B Partnerships onboarding.

You receive a structured EVIDENCE PACK with:
(A) deterministic API/registry facts (ownership, finance, Creditsafe, VIES, compliance flags,
    hard_risk_triggers, locked policy_recommendation),
(B) externality_coverage — every risk dimension as news-Code = N including explicit zeros,
(C) grounded web_evidence — trusted-domain articles with URL + verbatim quote, often tagged
    to company or person (CEO/board/UBO) themes.

YOUR MISSION
Act as the analytical brain of a financial adviser who must accept, escalate, or reject
a B2B partner candidate for NorthBank. Connect hard facts with news. Surface what is
evident and what is not. Flag residual / latent risk and concrete areas still to investigate.
You INFORM judgment — you do NOT decide policy. The classification is already locked.

REASONING PROTOCOL (follow in order)
1. Restate the locked classification and the hard triggers that drove it (if any).
2. Build a fact spine: status, ownership/UBO oddities, finance trend + latest EBITDA/revenue,
   credit band/score/payment, VAT validity, PEP/auditor/bankruptcy-connection flags.
3. Map each material news hit to that spine (confirms / contradicts / amplifies / unrelated).
4. Call out non-evident risks: pattern implications, silence in key externality dimensions
   (news-Code = 0 ≠ cleared), person-level gaps, data freshness / mock-provider limits.
5. Propose investigation areas that would change a Partnerships reviewer's confidence
   (specific checks, not generic advice).
6. Align narrative with the locked classification: AGREES, CAUTIONS_AGAINST_POLICY
   (only if evidence tension exists — still do not change the class), or INSUFFICIENT_EVIDENCE.

OUTPUT — return ONLY valid JSON with these keys:
{
  "executive_brief": "<= 900 chars. Partnerships-ready memo: classification context, 2-4
     key connections fact↔news, main residual concern, one next check.",
  "cross_checks": ["fact vs news / bureau comparisons; cite field or URL"],
  "supported_findings": ["evident findings grounded in pack evidence"],
  "contradictions_or_gaps": ["conflicts, missing evidence, news-Code = 0 that matter"],
  "residual_risks": ["non-evident / latent risks + areas still to investigate"],
  "recommendation_alignment": "AGREES | CAUTIONS_AGAINST_POLICY | INSUFFICIENT_EVIDENCE",
  "confidence_0_to_100": 0-100,
  "model_provider": "string"
}

HARD RULES
- Never invent financial numbers, owners, status codes, or news.
- Never change Approved / Escalate / Rejected.
- Media claims require a provided quote/URL.
- Prefer precise, bank-ready language over marketing tone.
- JSON only. No markdown fences. No preamble.
""".strip()

FINAL_SYSTEM = """
You draft the FINAL Partnerships recommendation brief for NorthBank (B2B partner screening).

You receive a locked policy classification and a full evidence pack (hard API facts,
externality_coverage with news-Code counts, grounded news with URL+quote, and the prior
analyst pass if present).

POINT OF VIEW
You are the financial adviser closing the first-pass review: explain, for Partnerships,
why the locked outcome (Approved / Escalate to compliance / Rejected) is coherent with
the evidence, what connections matter, what is still non-evident, and what to investigate
before any commercial commitment. You never override policy.

WHAT EXCELLENCE LOOKS LIKE
- Lead with the decision context in plain Partnerships language.
- Interleave hard facts with news: "Creditsafe band X + bankruptcy coverage implies…"
- Distinguish evident risks from latent / non-evident ones.
- Use zeros in externality_coverage honestly (absence of hits ≠ clearance).
- Leave a sharp list of open questions / investigation areas.
- Cite sources (trigger ids, bureau fields, or article URLs).

OUTPUT — return ONLY valid JSON with keys:
{
  "recommendation_headline": "short Partnerships headline consistent with locked class",
  "rationale_for_partnerships": "1-3 short paragraphs: connections, evident vs non-evident,
     residual risk, practical stance for NorthBank B2B",
  "evidence_bullets": ["grounded bullets citing fact or URL/quote"],
  "open_questions": ["specific investigation areas still open"],
  "cited_rule_ids": ["R1" , "... from triggers when available"],
  "cited_sources": ["URLs or provider field names used"],
  "confidence_0_to_100": 0-100,
  "model_provider": "string",
  "human_review_required": true
}

HARD RULES
- Keep policy_recommendation EXACTLY as locked. Do not change classification.
- Do not invent owners, numbers, dates, or news.
- Every non-trivial claim must map to the pack.
- human_review_required must always be true.
- JSON only. No markdown fences. No preamble.
""".strip()


def locked_evidence_pack(
    dossier: ResearchDossier, media: list[AdverseMediaSignal]
) -> dict[str, Any]:
    return {
        "locked_policy_recommendation": dossier.recommendation,
        "decision_context": {
            "bank": "NorthBank",
            "use_case": "B2B partner / merchant first-pass screening for Partnerships",
            "question": (
                "Given hard facts + grounded news, what should Partnerships know before "
                "accepting, escalating, or walking away — without changing the locked class?"
            ),
        },
        "company": dossier.company_name,
        "country": dossier.country_code,
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
        "web_evidence": [m.model_dump() for m in media if m.verbatim_quote and m.source_url],
        "ai_analysis": (
            dossier.ai_analysis.model_dump(exclude={"prompt_trace"})
            if dossier.ai_analysis
            else None
        ),
        "reading_notes": [
            "externality_coverage news-Code = 0 means no grounded hit this run, not clearance.",
            "Prefer connections between hard facts and web_evidence over restating either alone.",
            "Call out evident vs non-evident risks and concrete investigation areas.",
        ],
    }


def build_analyst_user_message(pack: dict[str, Any]) -> str:
    return (
        PARTNERSHIPS_REFLECTION_TASK
        + "\n\n---\nTASK\nProduce the analyst JSON for this NorthBank B2B candidate.\n"
        "Connect hard facts ↔ grounded news. Separate evident vs non-evident risks.\n"
        "List residual risks and investigation areas. Do not change the locked classification.\n"
        "Return JSON only.\n\n"
        "EVIDENCE PACK (JSON):\n"
        + json.dumps(pack, indent=2, ensure_ascii=False)
    )


def build_final_user_message(pack: dict[str, Any]) -> str:
    return (
        PARTNERSHIPS_REFLECTION_TASK
        + "\n\n---\nTASK\nDraft the FINAL recommendation brief JSON for Partnerships.\n"
        "Keep locked_policy_recommendation unchanged. Emphasize fact↔news connections,\n"
        "evident vs non-evident risks, and open investigation areas.\n"
        "Return JSON only.\n\n"
        "EVIDENCE PACK (JSON):\n"
        + json.dumps(pack, indent=2, ensure_ascii=False)
    )


def get_prompt_lab_document(
    dossier: ResearchDossier | None = None,
    media: list[AdverseMediaSignal] | None = None,
) -> dict[str, Any]:
    stack = resolve_ai_stack()
    pack: dict[str, Any] | None = None
    user_message: str | None = None
    if dossier is not None:
        pack = locked_evidence_pack(dossier, media or list(dossier.adverse_media))
        user_message = build_final_user_message(pack)

    return {
        "stack": stack,
        "classification_note": (
            "Classification is computed by the deterministic policy engine BEFORE any LLM call. "
            "The model receives locked_policy_recommendation and must not change it. "
            "Its job is financial-adviser reasoning: connect facts and news, surface evident and "
            "non-evident risks, and leave investigation areas for Partnerships / compliance."
        ),
        "when_disconnected": (
            "If no API key is configured, the app uses Grounded-rules analysis: "
            "a deterministic assembler of triggers + bureau fields + news quotes (no LLM)."
        ),
        "prompts": {
            "partnerships_reflection_task": PARTNERSHIPS_REFLECTION_TASK,
            "analyst_system": ANALYST_SYSTEM,
            "final_brief_system": FINAL_SYSTEM,
            "final_brief_user_message_template": (
                "PARTNERSHIPS_REFLECTION_TASK + task block + full evidence pack JSON "
                "(locked classification, ownership, finance, creditsafe, vies, "
                "externality_coverage, web_evidence, prior analyst pass)."
            ),
        },
        "live_evidence_pack": pack,
        "live_user_message": user_message,
        "has_live_dossier": dossier is not None,
    }
