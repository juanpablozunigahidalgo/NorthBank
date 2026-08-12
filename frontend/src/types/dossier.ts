export type RiskDecision =
  | 'APPROVED'
  | 'ESCALATE_TO_COMPLIANCE'
  | 'REJECTED'

export type RiskCategory =
  | 'Litigation'
  | 'Regulatory_Sanction'
  | 'Financial_Distress'
  | 'Reputational'
  | 'None'

export type SeverityLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export interface FinancialYear {
  year: number
  revenue_eur: number
  ebitda_eur: number
  profitability_margin_pct: number
}

export interface AdverseMediaSignal {
  headline: string
  source_url: string
  source_name: string
  risk_category: RiskCategory
  severity: SeverityLevel
  verbatim_quote: string
  publication_date?: string | null
  subject_type?: 'company' | 'person'
  subject_name?: string | null
  externality_theme_id?: string | null
  externality_theme_label?: string | null
}

export interface ExternalityThemeCoverage {
  theme_id: string
  news_code: string
  label: string
  scope: 'company' | 'person'
  hit_count: number
  searched: boolean
  summary: string
}

export interface OwnershipSummary {
  legal_structure: string
  status_code: string
  status_description: string
  ceo?: string | null
  board_of_directors: string[]
  ultimate_beneficial_owners: string[]
  parent_company?: string | null
  unusual_ownership_patterns?: string | null
}

export interface FinancialHealthSignal {
  latest_year: number
  latest_revenue_eur: number
  latest_ebitda_eur: number
  latest_margin_pct: number
  trend: 'GROWING' | 'STABLE' | 'DECLINING' | 'DISTRESSED' | 'UNKNOWN'
  history: FinancialYear[]
  data_source: string
}

export interface ComplianceHardFlags {
  sanctions_list_match: boolean
  pep_count: number
  missing_auditor: boolean
  vat_registered?: boolean | null
  f_tax_registered?: boolean | null
  connected_bankruptcy_companies: number
  notes: string[]
}

export interface ProviderConfidence {
  score_confidence_0_to_100?: number | null
  match_confidence_0_to_100?: number | null
  data_freshness?: string | null
  coverage_note?: string | null
}

export interface CreditsafeSignal {
  provider: string
  provider_report_id: string
  as_of_date: string
  credit_score: number
  rating_band: string
  probability_of_default_pct: number
  payment_behavior: string
  credit_limit_recommendation_eur: number
  dbt_days_beyond_terms: number
  confidence: ProviderConfidence
}

export interface EuVatViesSignal {
  provider: string
  vat_number: string
  member_state: string
  request_date: string
  valid: boolean
  name: string
  address?: string | null
  consultation_number?: string | null
  trader_company_type?: string | null
  confidence: ProviderConfidence
}

export interface AiPromptTrace {
  purpose: string
  model: string
  system_prompt: string
  user_message: string
  raw_response: string
  used_llm: boolean
}

export interface AiAnalysis {
  executive_brief: string
  cross_checks: string[]
  supported_findings: string[]
  contradictions_or_gaps: string[]
  residual_risks: string[]
  recommendation_alignment: string
  confidence_0_to_100: number
  model_provider: string
  prompt_trace?: AiPromptTrace | null
}

export interface ResearchDossier {
  company_id: string
  company_name: string
  country_code: string
  recommendation: RiskDecision
  ownership: OwnershipSummary
  financial_health: FinancialHealthSignal
  compliance_hard_flags: ComplianceHardFlags
  creditsafe?: CreditsafeSignal | null
  eu_vat_vies?: EuVatViesSignal | null
  adverse_media: AdverseMediaSignal[]
  externality_coverage?: ExternalityThemeCoverage[]
  hard_risk_triggers: string[]
  unsure_or_unverified: string[]
  sources: string[]
  ai_analysis?: AiAnalysis | null
  audit_summary: string
  elapsed_ms?: number | null
  disclaimer: string
}

export interface ResearchResponse {
  dossier: ResearchDossier
  cut_corners: string[]
}

export interface FinalRecommendationBrief {
  recommendation_headline: string
  policy_recommendation: RiskDecision
  rationale_for_partnerships: string
  evidence_bullets: string[]
  open_questions: string[]
  cited_rule_ids: string[]
  cited_sources: string[]
  confidence_0_to_100: number
  model_provider: string
  human_review_required: boolean
  prompt_trace?: AiPromptTrace | null
}

export interface PolicyRule {
  id: string
  if: string
  then: string
  why: string
}

export interface PolicyRulesDocument {
  version: string
  human_in_the_loop: boolean
  llm_may_change_recommendation: boolean
  future_agents: string
  rules: PolicyRule[]
  outputs?: string[]
  logic_summary?: string
}

export interface ExternalityTheme {
  id: string
  news_code?: string
  label: string
  description: string
  query_or: string
}

export interface ExternalitiesDocument {
  version: string
  purpose: string
  how_it_feeds_research: string
  company: ExternalityTheme[]
  person: ExternalityTheme[]
  search_budget: {
    company_theme_queries: number
    person_theme_queries: number
    typical_total_theme_queries: number
    dossier_top_n_articles: number
  }
}

export interface AiLabDocument {
  stack: {
    ai_provider: string
    ai_model: string
    connected?: boolean
    ux_label?: string
    how_to_connect?: {
      groq_free_tier?: string
      anthropic?: string
      bedrock?: string
      cursor_note?: string
    }
    note?: string
  }
  classification_note: string
  when_disconnected: string
  prompts: {
    partnerships_reflection_task: string
    analyst_system: string
    final_brief_system: string
    final_brief_user_message_template: string
  }
  live_evidence_pack?: unknown
  live_user_message?: string | null
  has_live_dossier: boolean
}
