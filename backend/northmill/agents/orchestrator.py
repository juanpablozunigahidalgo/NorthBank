"""Agentic tool orchestration: registry + trusted media + AI dossier analysis."""

from __future__ import annotations

import asyncio
import time

from northmill.agents.dossier import synthesize_dossier
from northmill.agents.final_brief import generate_final_recommendation
from northmill.config import resolve_ai_stack
from northmill.providers.media import search_company_adverse_media
from northmill.providers.registry import get_company_registry_data, list_company_names
from northmill.schema import FinalRecommendationBrief, ResearchResponse


class CompanyNotFoundError(LookupError):
    pass


async def _registry_worker(query: str) -> dict:
    return await asyncio.to_thread(get_company_registry_data, query)


async def _media_worker(company_name: str, company: dict):
    return await asyncio.to_thread(search_company_adverse_media, company_name, company)


async def run_research(company_query: str) -> ResearchResponse:
    started = time.perf_counter()
    company = await _registry_worker(company_query)
    if not company:
        raise CompanyNotFoundError(
            f"Company '{company_query}' not found. Try: {', '.join(list_company_names()[:5])}..."
        )

    name = company["basic_information"]["name"]
    media_result = await _media_worker(name, company)
    media = media_result.signals
    dossier, engine_label = synthesize_dossier(
        company,
        media,
        externality_coverage=media_result.coverage,
    )
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    stack = resolve_ai_stack()

    sources = list(
        dict.fromkeys(
            [
                "trust_filter://allowlisted-domains",
                "person_adverse_media://ceo-only-mockup",
                "pep_flag://registry-indicator",
                *dossier.sources,
            ]
        )
    )

    dossier = dossier.model_copy(
        update={
            "sources": sources,
            "elapsed_ms": elapsed_ms,
            "unsure_or_unverified": list(dict.fromkeys(dossier.unsure_or_unverified))[:8],
        }
    )

    cut = [
        f"Analysis engine: {engine_label}",
        f"Configured AI: {stack['ai_provider']} / {stack['ai_model']}",
        "Registry/financials are mocked (Roaring.io / Allabolag-shaped) for this prototype.",
        "Creditsafe + EU VIES VAT are MOCK bureau/tax payloads — swap for live APIs later.",
        "Recommendation = deterministic policy engine (R1–R10); LLM cannot change it.",
        "News engine fans out Externalities themes (company + person); "
        "coverage shows news-Code = N including zeros.",
        "LLM final brief connects news + API facts; cannot change Approved/Escalate/Rejected.",
    ]

    return ResearchResponse(dossier=dossier, cut_corners=cut)


def run_research_sync(company_query: str) -> ResearchResponse:
    return asyncio.run(run_research(company_query))


def run_final_brief_sync(company_query: str) -> FinalRecommendationBrief:
    response = run_research_sync(company_query)
    return generate_final_recommendation(response.dossier, response.dossier.adverse_media)
