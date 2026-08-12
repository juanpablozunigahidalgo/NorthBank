"""
FastAPI app — local uvicorn OR AWS Lambda via Mangum.
Serves the built React UI from backend/static when present (single free-host deploy).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from northmill.agents.final_brief import generate_final_recommendation
from northmill.agents.orchestrator import CompanyNotFoundError, run_research_sync
from northmill.config import CORS_ORIGINS, resolve_ai_stack
from northmill.policy.engine import get_policy_rules_document
from northmill.providers.externalities import get_externalities_document
from northmill.providers.registry import get_company_registry_data, list_company_names
from northmill.schema import FinalRecommendationBrief, ResearchResponse

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
STATIC_DIR = _BACKEND_ROOT / "static"

app = FastAPI(
    title="NorthBank Partner Research Assistant",
    description=(
        "First-pass B2B partner research dossier API. "
        "Deterministic policy engine + grounded media + optional LLM narrative."
    ),
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "companies": len(list_company_names()),
        **resolve_ai_stack(),
    }


@app.get("/api/ai-config")
def ai_config() -> dict[str, Any]:
    """Which AI provider/model the narrative layer will use."""
    return resolve_ai_stack()


@app.get("/api/ai-lab")
def ai_lab(
    company: str | None = Query(None, description="Optional company to attach live evidence pack"),
) -> dict[str, Any]:
    """
    Prompt lab: system prompts, model, and optional full evidence pack for a company.
    """
    from northmill.agents.prompt_lab import get_prompt_lab_document

    if company and len(company.strip()) >= 2:
        try:
            response = run_research_sync(company.strip())
            return get_prompt_lab_document(
                response.dossier, response.dossier.adverse_media
            )
        except CompanyNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
    return get_prompt_lab_document()


@app.get("/api/companies")
def companies() -> dict[str, list[str]]:
    return {"companies": list_company_names()}


@app.get("/api/policy-rules")
def policy_rules() -> dict:
    """Explicit R1–R10 matrix — recommendation is never LLM-invented."""
    return get_policy_rules_document()


@app.get("/api/externalities")
def externalities() -> dict:
    """Company + person risk themes that drive multi-query news search."""
    return get_externalities_document()


@app.get("/api/providers/creditsafe")
def creditsafe_provider(
    company: str = Query(..., min_length=2),
) -> dict:
    record = get_company_registry_data(company)
    if not record:
        raise HTTPException(status_code=404, detail=f"Company not found: {company}")
    return record["creditsafe"]


@app.get("/api/providers/eu-vat-vies")
def eu_vat_vies_provider(
    company: str = Query(..., min_length=2),
) -> dict:
    record = get_company_registry_data(company)
    if not record:
        raise HTTPException(status_code=404, detail=f"Company not found: {company}")
    return record["eu_vat_vies"]


@app.get("/api/research", response_model=ResearchResponse)
def research(
    company: str = Query(..., min_length=2, description="Company name or org id"),
) -> ResearchResponse:
    try:
        return run_research_sync(company)
    except CompanyNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/research/final-brief", response_model=FinalRecommendationBrief)
def final_brief(
    company: str = Query(..., min_length=2),
) -> FinalRecommendationBrief:
    """Grounded closing recommendation dialogue (policy verdict locked)."""
    try:
        response = run_research_sync(company)
    except CompanyNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return generate_final_recommendation(response.dossier, response.dossier.adverse_media)


def _mount_spa() -> None:
    """Serve Vite build from backend/static (same-origin /api — free single-service hosting)."""
    if not STATIC_DIR.is_dir() or not (STATIC_DIR / "index.html").is_file():
        return
    assets = STATIC_DIR / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

    @app.get("/")
    def spa_index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str) -> FileResponse:
        blocked = ("api/", "health", "docs", "openapi.json", "redoc")
        if full_path == "health" or full_path.startswith(blocked):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = STATIC_DIR / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(STATIC_DIR / "index.html")


_mount_spa()

try:
    from mangum import Mangum

    handler = Mangum(app)
except ImportError:  # pragma: no cover
    handler = None
