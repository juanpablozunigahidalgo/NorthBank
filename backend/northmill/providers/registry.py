"""Deterministic registry lookups (simulates Roaring.io / Allabolag company + risk APIs)."""

from __future__ import annotations

import json
from functools import lru_cache

from northmill.config import DATA_DIR
from northmill.providers.bureau import enrich_company_with_provider_mocks

DATA_PATH = DATA_DIR / "mock_corporate_database.json"


@lru_cache(maxsize=1)
def _load_companies() -> list[dict]:
    with DATA_PATH.open(encoding="utf-8") as f:
        payload = json.load(f)
    return payload["companies"]


def list_company_names() -> list[str]:
    return [c["basic_information"]["name"] for c in _load_companies()]


def get_company_registry_data(company_query: str) -> dict | None:
    """Return one company record by name substring or exact companyId."""
    q = company_query.strip().lower()
    if not q:
        return None

    for company in _load_companies():
        name = company["basic_information"]["name"].lower()
        cid = str(company["companyId"]).lower()
        if q == cid or q in name or q.replace("-", "") in cid.replace("-", ""):
            return enrich_company_with_provider_mocks(company)
    return None
