"""Strict output schemas for the Partner Research dossier (forced JSON / low hallucination)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


RiskDecision = Literal["APPROVED", "ESCALATE_TO_COMPLIANCE", "REJECTED"]
RiskCategory = Literal[
    "Litigation",
    "Regulatory_Sanction",
    "Financial_Distress",
    "Reputational",
    "None",
]
SeverityLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class FinancialYear(BaseModel):
    year: int
    revenue_eur: float
    ebitda_eur: float
    profitability_margin_pct: float


class AdverseMediaSignal(BaseModel):
    headline: str
    source_url: str
    source_name: str = "Unknown"
    risk_category: RiskCategory
    severity: SeverityLevel
    verbatim_quote: str = Field(
        description="Exact sentence taken from the source text. Discard signal if empty."
    )
    publication_date: str | None = None
    subject_type: Literal["company", "person"] = "company"
    subject_name: str | None = None
    externality_theme_id: str | None = None
    externality_theme_label: str | None = None


class ExternalityThemeCoverage(BaseModel):
    """Per-dimension news search result (including explicit zeros)."""

    theme_id: str
    news_code: str  # e.g. news-PEP
    label: str
    scope: Literal["company", "person"]
    hit_count: int = 0
    searched: bool = True
    summary: str = ""  # e.g. "news-PEP = 0"


class OwnershipSummary(BaseModel):
    legal_structure: str
    status_code: str
    status_description: str
    ceo: str | None = None
    board_of_directors: list[str] = Field(default_factory=list)
    ultimate_beneficial_owners: list[str] = Field(default_factory=list)
    parent_company: str | None = None
    unusual_ownership_patterns: str | None = None


class FinancialHealthSignal(BaseModel):
    latest_year: int
    latest_revenue_eur: float
    latest_ebitda_eur: float
    latest_margin_pct: float
    trend: Literal["GROWING", "STABLE", "DECLINING", "DISTRESSED", "UNKNOWN"]
    history: list[FinancialYear]
    data_source: str = "mock_registry (Roaring/Allabolag-shaped)"


class ComplianceHardFlags(BaseModel):
    sanctions_list_match: bool = False
    pep_count: int = 0
    missing_auditor: bool = False
    vat_registered: bool | None = None
    f_tax_registered: bool | None = None
    connected_bankruptcy_companies: int = 0
    notes: list[str] = Field(default_factory=list)


class ProviderConfidence(BaseModel):
    score_confidence_0_to_100: int | None = None
    match_confidence_0_to_100: int | None = None
    data_freshness: str | None = None
    coverage_note: str | None = None


class CreditsafeSignal(BaseModel):
    """Creditsafe-shaped credit bureau opinion (MOCK unless wired to live API)."""

    provider: str = "Creditsafe (MOCK)"
    provider_report_id: str
    as_of_date: str
    credit_score: int
    rating_band: str
    probability_of_default_pct: float
    payment_behavior: str
    credit_limit_recommendation_eur: int
    dbt_days_beyond_terms: int = 0
    confidence: ProviderConfidence


class EuVatViesSignal(BaseModel):
    """EU VIES VAT register-shaped response (MOCK unless wired to live VIES)."""

    provider: str = "EU VIES VAT (MOCK)"
    vat_number: str
    member_state: str
    request_date: str
    valid: bool
    name: str
    address: str | None = None
    consultation_number: str | None = None
    trader_company_type: str | None = None
    confidence: ProviderConfidence


class AiPromptTrace(BaseModel):
    """What was sent to the narrative model and what came back (for AI prompt window)."""

    purpose: str  # analyst | final_brief
    model: str
    system_prompt: str
    user_message: str
    raw_response: str
    used_llm: bool = False


class AiAnalysis(BaseModel):

    """LLM (or grounded fallback) reading of registry facts + web evidence."""

    executive_brief: str = Field(max_length=900)
    cross_checks: list[str] = Field(default_factory=list)
    supported_findings: list[str] = Field(default_factory=list)
    contradictions_or_gaps: list[str] = Field(default_factory=list)
    residual_risks: list[str] = Field(default_factory=list)
    recommendation_alignment: str = "INSUFFICIENT_EVIDENCE"
    confidence_0_to_100: int = 50
    model_provider: str = "deterministic_grounded_analyst"
    prompt_trace: AiPromptTrace | None = None


class ResearchDossier(BaseModel):
    """First-pass research dossier returned to Partnerships."""

    company_id: str
    company_name: str
    country_code: str
    recommendation: RiskDecision
    ownership: OwnershipSummary
    financial_health: FinancialHealthSignal
    compliance_hard_flags: ComplianceHardFlags
    creditsafe: CreditsafeSignal | None = None
    eu_vat_vies: EuVatViesSignal | None = None
    adverse_media: list[AdverseMediaSignal] = Field(default_factory=list)
    externality_coverage: list[ExternalityThemeCoverage] = Field(default_factory=list)
    hard_risk_triggers: list[str] = Field(default_factory=list)
    unsure_or_unverified: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    ai_analysis: AiAnalysis | None = None
    audit_summary: str = Field(max_length=400)
    elapsed_ms: int | None = None
    disclaimer: str = (
        "ASSISTED DRAFT ONLY — human review required before any commercial decision. "
        "Registry financials in this prototype are illustrative mock data."
    )


class ResearchResponse(BaseModel):
    dossier: ResearchDossier
    cut_corners: list[str] = Field(
        default_factory=lambda: [
            "Registry/financials are mocked (simulating Roaring.io / Allabolag APIs).",
            "Creditsafe + EU VIES VAT are MOCK provider payloads (swap for live APIs later).",
            "Sanctions/PEP hard checks are simplified flags from mock indicators, not live World-Check.",
            "Adverse media may use grounded mock articles when live search is unavailable.",
            "Recommendation is policy-engine only; LLM cannot change APPROVED/ESCALATE/REJECTED.",
        ]
    )


class FinalRecommendationBrief(BaseModel):
    """Grounded closing dialogue for Partnerships — policy verdict is locked."""

    recommendation_headline: str
    policy_recommendation: RiskDecision
    rationale_for_partnerships: str
    evidence_bullets: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    cited_rule_ids: list[str] = Field(default_factory=list)
    cited_sources: list[str] = Field(default_factory=list)
    confidence_0_to_100: int = 50
    model_provider: str = "final_brief:grounded_rules"
    human_review_required: bool = True
    prompt_trace: AiPromptTrace | None = None


