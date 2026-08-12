"""
MCP server — one tool per provider + policy + grounded final brief.

Configure AI via backend/.env:
  AI_PROVIDER=auto|bedrock|anthropic|rules
  AI_MODEL=<optional model id>
  ANTHROPIC_API_KEY=...
  USE_BEDROCK=true|false
  BEDROCK_MODEL_ID=...

Run:
  python mcp_server.py
"""

from __future__ import annotations

import json

from northmill.agents.final_brief import generate_final_recommendation
from northmill.agents.orchestrator import run_research_sync
from northmill.config import resolve_ai_stack
from northmill.policy.engine import get_policy_rules_document
from northmill.providers.bureau import build_creditsafe_mock, build_eu_vat_vies_mock
from northmill.providers.media import search_company_adverse_media
from northmill.providers.registry import get_company_registry_data, list_company_names

try:
    from fastmcp import FastMCP
except ImportError:  # pragma: no cover
    FastMCP = None  # type: ignore


def build_mcp():
    if FastMCP is None:
        raise RuntimeError("Install fastmcp: pip install fastmcp")

    mcp = FastMCP("northmill-partner-research")

    @mcp.tool()
    def list_companies() -> str:
        """List companies available in the mock Nordic/Polish registry."""
        return json.dumps(list_company_names(), indent=2)

    @mcp.tool()
    def get_ai_config() -> str:
        """Show which AI provider/model drafts narrative (never changes policy verdict)."""
        return json.dumps(resolve_ai_stack(), indent=2)

    @mcp.tool()
    def get_roaring_registry(company_query: str) -> str:
        """Roaring/Allabolag-shaped MOCK registry. LLM must not invent these fields."""
        company = get_company_registry_data(company_query)
        if not company:
            return json.dumps({"error": f"Company not found: {company_query}"})
        slim = {
            k: v
            for k, v in company.items()
            if k not in {"creditsafe", "eu_vat_vies"}
        }
        return json.dumps(slim, indent=2)

    @mcp.tool()
    def get_creditsafe_report(company_query: str) -> str:
        """Creditsafe-shaped MOCK credit opinion with confidence metadata."""
        company = get_company_registry_data(company_query)
        if not company:
            return json.dumps({"error": f"Company not found: {company_query}"})
        return json.dumps(build_creditsafe_mock(company), indent=2)

    @mcp.tool()
    def get_eu_vat_vies(company_query: str) -> str:
        """EU VIES VAT register MOCK."""
        company = get_company_registry_data(company_query)
        if not company:
            return json.dumps({"error": f"Company not found: {company_query}"})
        return json.dumps(build_eu_vat_vies_mock(company), indent=2)

    @mcp.tool()
    def search_adverse_media_tool(company_name: str) -> str:
        """Adverse media + person/PEP deep-dive (trusted domains, URL+quote required)."""
        company = get_company_registry_data(company_name)
        result = search_company_adverse_media(company_name, company)
        return json.dumps(
            {
                "signals": [s.model_dump() for s in result.signals],
                "coverage": [c.model_dump() for c in result.coverage],
                "queries_run": result.queries_run,
            },
            indent=2,
        )

    @mcp.tool()
    def get_externalities() -> str:
        """Company + person externality themes used for multi-query news search."""
        from northmill.providers.externalities import get_externalities_document

        return json.dumps(get_externalities_document(), indent=2)

    @mcp.tool()
    def get_policy_rules() -> str:
        """Deterministic R1–R10 decision matrix. Agents must not override verdicts."""
        return json.dumps(get_policy_rules_document(), indent=2)

    @mcp.tool()
    def generate_research_dossier(company_query: str) -> str:
        """Full first-pass dossier. Recommendation is ASSISTED DRAFT only."""
        response = run_research_sync(company_query)
        return response.model_dump_json(indent=2)

    @mcp.tool()
    def generate_final_recommendation_brief(company_query: str) -> str:
        """
        Grounded closing recommendation dialogue.
        Policy verdict is locked; model may only explain cited evidence.
        """
        response = run_research_sync(company_query)
        brief = generate_final_recommendation(
            response.dossier, response.dossier.adverse_media
        )
        return brief.model_dump_json(indent=2)

    @mcp.tool()
    def propose_decision_stub(company_query: str) -> str:
        """FUTURE decision-agent hook — intentionally does NOT decide today."""
        company = get_company_registry_data(company_query)
        if not company:
            return json.dumps({"error": f"Company not found: {company_query}"})
        return json.dumps(
            {
                "status": "NOT_IMPLEMENTED",
                "agent_role": "future_decision_agent",
                "allowed_now": False,
                "company": company["basic_information"]["name"],
                "ai_config": resolve_ai_stack(),
                "message": (
                    "Scaffold only: future agents may gather MCP evidence and draft "
                    "a recommendation for a human approver. They must not auto-bind "
                    "merchant onboarding or credit limits."
                ),
                "required_inputs": [
                    "get_roaring_registry",
                    "get_creditsafe_report",
                    "get_eu_vat_vies",
                    "search_adverse_media_tool",
                    "get_policy_rules",
                    "generate_final_recommendation_brief",
                ],
                "output_contract": {
                    "proposed_recommendation": "APPROVED|ESCALATE_TO_COMPLIANCE|REJECTED",
                    "must_cite_rule_ids": True,
                    "human_approval_required": True,
                },
            },
            indent=2,
        )

    @mcp.tool()
    def get_company_registry_data_tool(company_query: str) -> str:
        """Alias of get_roaring_registry."""
        return get_roaring_registry(company_query)

    return mcp


def main() -> None:
    build_mcp().run()


if __name__ == "__main__":
    main()
