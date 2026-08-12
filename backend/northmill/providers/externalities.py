"""
Externalities taxonomy: what Partnerships searches for on the open web.

Company-level and person-level (CEO / board / UBO / PEP) risk dimensions.
Each theme becomes one or more trusted-domain news queries.
The LLM never invents hits — only grounded URL+quote signals may enter the dossier.
"""

from __future__ import annotations

from typing import Literal

SubjectScope = Literal["company", "person"]


# Themes are intentionally broad: legal, fraud, environment, political, regulatory, etc.
# news_code is the short label shown in Research (e.g. news-PEP = 0).
COMPANY_EXTERNALITIES: list[dict] = [
    {
        "id": "legal_litigation",
        "news_code": "news-Legal",
        "label": "Legal / litigation",
        "description": "Lawsuits, court cases, class actions, settlements.",
        "query_or": "lawsuit OR litigation OR sued OR \"class action\" OR court OR indictment",
    },
    {
        "id": "fraud_corruption",
        "news_code": "news-Fraud",
        "label": "Fraud / corruption",
        "description": "Fraud, bribery, embezzlement, accounting scandal.",
        "query_or": "fraud OR bribery OR corruption OR embezzlement OR \"accounting scandal\" OR kickback",
    },
    {
        "id": "financial_distress",
        "news_code": "news-Financial",
        "label": "Financial distress",
        "description": "Bankruptcy, reconstruction, insolvency, default, massive losses.",
        "query_or": "bankruptcy OR insolvency OR reconstruction OR rekonstruktion OR default OR \"going concern\"",
    },
    {
        "id": "regulatory_sanctions",
        "news_code": "news-Regulatory",
        "label": "Regulatory / sanctions",
        "description": "Fines, probes, licences revoked, sanctions lists.",
        "query_or": "fine OR sanction OR regulator OR probe OR investigation OR \"licence revoked\" OR \"license revoked\"",
    },
    {
        "id": "environmental",
        "news_code": "news-Environmental",
        "label": "Environmental",
        "description": "Pollution, climate litigation, environmental fines, ESG scandals.",
        "query_or": "pollution OR environmental OR \"climate lawsuit\" OR \"ESG scandal\" OR spill OR emissions",
    },
    {
        "id": "political_geopolitical",
        "news_code": "news-Political",
        "label": "Political / geopolitical",
        "description": "Political exposure, state capture, geopolitical bans, export controls.",
        "query_or": "political OR geopolitical OR \"export control\" OR \"state aid\" OR lobbying OR \"sanctions evasion\"",
    },
    {
        "id": "labour_human_rights",
        "news_code": "news-Labour",
        "label": "Labour / human rights",
        "description": "Labour abuse, discrimination claims, human-rights investigations.",
        "query_or": "\"labour abuse\" OR \"labor abuse\" OR discrimination OR \"human rights\" OR sweatshop OR \"forced labour\"",
    },
    {
        "id": "data_cyber",
        "news_code": "news-Cyber",
        "label": "Data / cyber",
        "description": "Data breaches, GDPR fines, cyber attacks.",
        "query_or": "\"data breach\" OR GDPR OR hack OR ransomware OR cybersecurity OR \"privacy fine\"",
    },
    {
        "id": "competition_antitrust",
        "news_code": "news-Competition",
        "label": "Competition / antitrust",
        "description": "Cartels, antitrust probes, unfair competition.",
        "query_or": "antitrust OR cartel OR \"competition authority\" OR monopoly OR \"unfair competition\"",
    },
    {
        "id": "reputation_consumer",
        "news_code": "news-Reputation",
        "label": "Reputation / consumer harm",
        "description": "Boycotts, major product recalls, consumer scandals.",
        "query_or": "boycott OR recall OR scandal OR \"consumer complaint\" OR whistleblower",
    },
]

PERSON_EXTERNALITIES: list[dict] = [
    {
        "id": "person_pep",
        "news_code": "news-PEP",
        "label": "PEP / political exposure",
        "description": "Politically exposed person signals, political office, state ties.",
        "query_or": "PEP OR \"politically exposed\" OR minister OR parliament OR \"political party\"",
    },
    {
        "id": "person_fraud",
        "news_code": "news-PersonFraud",
        "label": "Fraud / financial crime",
        "description": "Personal fraud, embezzlement, money laundering.",
        "query_or": "fraud OR embezzlement OR \"money laundering\" OR \"financial crime\" OR Ponzi",
    },
    {
        "id": "person_corruption",
        "news_code": "news-PersonCorruption",
        "label": "Bribery / corruption",
        "description": "Bribery, kickbacks, corruption probes.",
        "query_or": "bribery OR corruption OR kickback OR \"corruption probe\"",
    },
    {
        "id": "person_drugs_crime",
        "news_code": "news-Crime",
        "label": "Drugs / serious crime",
        "description": "Narcotics, trafficking, organised crime (high false-positive risk — quotes required).",
        "query_or": "drugs OR narcotics OR trafficking OR \"organised crime\" OR \"organized crime\" OR indictment",
    },
    {
        "id": "person_sanctions",
        "news_code": "news-PersonSanctions",
        "label": "Sanctions / watchlists",
        "description": "Personal sanctions, Interpol notices, asset freezes.",
        "query_or": "sanction OR Interpol OR \"asset freeze\" OR \"watch list\" OR \"wanted\"",
    },
    {
        "id": "person_lawsuit",
        "news_code": "news-PersonLegal",
        "label": "Personal litigation",
        "description": "Lawsuits, charges, convictions against the individual.",
        "query_or": "lawsuit OR charged OR convicted OR indictment OR \"court case\"",
    },
    {
        "id": "person_resign_scandal",
        "news_code": "news-Resign",
        "label": "Resignation / scandal",
        "description": "Forced resignation, personal scandal tied to the company role.",
        "query_or": "resign OR resignation OR scandal OR misconduct OR \"stepped down\"",
    },
    {
        "id": "person_conflict_interest",
        "news_code": "news-Conflict",
        "label": "Conflicts of interest",
        "description": "Related-party deals, undisclosed interests, insider trading.",
        "query_or": "\"conflict of interest\" OR \"related party\" OR \"insider trading\" OR undeclared",
    },
]


def theme_by_id(theme_id: str) -> dict | None:
    for theme in [*COMPANY_EXTERNALITIES, *PERSON_EXTERNALITIES]:
        if theme["id"] == theme_id:
            return theme
    return None


def get_externalities_document() -> dict:
    return {
        "version": "1.1",
        "purpose": (
            "Externalities are the searchable risk dimensions used by the news engine. "
            "Each theme fans out into trusted-domain queries for the company and, separately, "
            "for the company name and the CEO in this mockup (board / UBOs / investors are "
            "out of live search scope for now). Hits need URL + verbatim quote. "
            "Research reports every dimension as news-Code = N (including 0 when nothing found)."
        ),
        "how_it_feeds_research": (
            "Research runs multi-theme searches for company + CEO, reports hit counts per "
            "dimension (e.g. news-PEP = 0), keeps grounded articles grouped by theme, and the "
            "LLM final brief only connects those news hits with hard API facts — it cannot "
            "change Approved / Escalate / Rejected."
        ),
        "company": COMPANY_EXTERNALITIES,
        "person": PERSON_EXTERNALITIES,
        "search_budget": {
            "company_theme_queries": len(COMPANY_EXTERNALITIES),
            "person_theme_queries": len(PERSON_EXTERNALITIES),
            "typical_total_theme_queries": len(COMPANY_EXTERNALITIES)
            + len(PERSON_EXTERNALITIES),
            "dossier_top_n_articles": 10,
        },
    }


def company_search_plan(company_name: str) -> list[dict]:
    """One query per company externality theme."""
    return [
        {
            "scope": "company",
            "theme_id": theme["id"],
            "theme_label": theme["label"],
            "news_code": theme["news_code"],
            "query_name": company_name,
            "risk_suffix": f"({theme['query_or']})",
        }
        for theme in COMPANY_EXTERNALITIES
    ]


def person_search_plan(person_name: str, *, company_hint: str | None = None) -> list[dict]:
    """One query per person externality theme (optionally tied to company name)."""
    tied = f"{person_name} {company_hint}" if company_hint else person_name
    return [
        {
            "scope": "person",
            "theme_id": theme["id"],
            "theme_label": theme["label"],
            "news_code": theme["news_code"],
            "query_name": tied if theme["id"] in {"person_fraud", "person_drugs_crime"} else person_name,
            "subject_name": person_name,
            "risk_suffix": f"({theme['query_or']})",
        }
        for theme in PERSON_EXTERNALITIES
    ]


def infer_theme_from_text(
    *,
    subject_type: str,
    risk_category: str | None,
    text: str,
) -> dict | None:
    """Best-effort theme tag for curated mocks that lack externality_theme_id."""
    t = (text or "").lower()
    cat = (risk_category or "").lower()

    if subject_type == "person":
        if "pep" in t or "politically exposed" in t or "minister" in t:
            return theme_by_id("person_pep")
        if any(k in t for k in ("bribe", "corruption", "kickback")):
            return theme_by_id("person_corruption")
        if any(k in t for k in ("fraud", "embezzle", "laundering", "ponzi")):
            return theme_by_id("person_fraud")
        if any(k in t for k in ("drug", "narcotic", "traffick", "organised crime", "organized crime")):
            return theme_by_id("person_drugs_crime")
        if any(k in t for k in ("sanction", "interpol", "asset freeze")):
            return theme_by_id("person_sanctions")
        if any(k in t for k in ("resign", "scandal", "misconduct", "stepped down")):
            return theme_by_id("person_resign_scandal")
        if any(k in t for k in ("conflict of interest", "insider", "related party")):
            return theme_by_id("person_conflict_interest")
        if any(k in t for k in ("lawsuit", "charged", "convicted", "indict", "court")):
            return theme_by_id("person_lawsuit")
        return theme_by_id("person_lawsuit")

    if "financial" in cat or any(
        k in t for k in ("bankrupt", "insolven", "reconstruction", "rekonstruktion", "default", "going concern")
    ):
        return theme_by_id("financial_distress")
    if any(k in t for k in ("lawsuit", "litigation", "sued", "class action", "court", "indict")):
        return theme_by_id("legal_litigation")
    if any(k in t for k in ("fraud", "bribe", "corruption", "embezzle", "kickback", "accounting scandal")):
        return theme_by_id("fraud_corruption")
    if "regulatory" in cat or any(
        k in t for k in ("fine", "sanction", "regulator", "probe", "investigation", "licence", "license")
    ):
        return theme_by_id("regulatory_sanctions")
    if any(k in t for k in ("pollution", "environmental", "climate", "emission", "esg", "spill")):
        return theme_by_id("environmental")
    if any(k in t for k in ("geopolitical", "export control", "state aid", "lobbying", "political")):
        return theme_by_id("political_geopolitical")
    if any(k in t for k in ("labour", "labor", "human rights", "discrimination", "forced labour")):
        return theme_by_id("labour_human_rights")
    if any(k in t for k in ("data breach", "gdpr", "ransomware", "cyber", "privacy fine", "hack")):
        return theme_by_id("data_cyber")
    if any(k in t for k in ("antitrust", "cartel", "competition authority", "monopoly")):
        return theme_by_id("competition_antitrust")
    if any(k in t for k in ("boycott", "recall", "scandal", "whistleblower", "consumer")):
        return theme_by_id("reputation_consumer")
    if "reputational" in cat:
        return theme_by_id("reputation_consumer")
    return None
