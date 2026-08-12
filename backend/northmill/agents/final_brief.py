"""
Final grounded recommendation dialogue.

Uses ONLY the dossier evidence pack. Never invents facts.
Never overrides the deterministic policy recommendation.
"""

from __future__ import annotations

import json

from northmill.agents.analyst import _deterministic_analyst, _parse_json_object
from northmill.agents.prompt_lab import (
    FINAL_SYSTEM,
    build_final_user_message,
    locked_evidence_pack,
)
from northmill.config import (
    AI_PROVIDER,
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    BEDROCK_MODEL_ID,
    GROQ_API_KEY,
    GROQ_MODEL,
    USE_BEDROCK,
    resolve_ai_stack,
)
from northmill.schema import (
    AdverseMediaSignal,
    AiPromptTrace,
    FinalRecommendationBrief,
    ResearchDossier,
)


def _with_trace(
    brief: FinalRecommendationBrief,
    *,
    model: str,
    user_message: str,
    raw_response: str,
    used_llm: bool,
) -> FinalRecommendationBrief:
    return brief.model_copy(
        update={
            "prompt_trace": AiPromptTrace(
                purpose="final_brief",
                model=model,
                system_prompt=FINAL_SYSTEM,
                user_message=user_message,
                raw_response=raw_response,
                used_llm=used_llm,
            )
        }
    )


def _rules_final_brief(
    dossier: ResearchDossier,
    media: list[AdverseMediaSignal],
    *,
    user_message: str,
) -> FinalRecommendationBrief:
    analysis = _deterministic_analyst(dossier, media)
    headline = {
        "APPROVED": "Approved (draft) - clean first-pass rules",
        "ESCALATE_TO_COMPLIANCE": "Escalate to compliance - grey-zone signals need judgment",
        "REJECTED": "Rejected - hard fail in first-pass rules",
    }[dossier.recommendation]

    evidence = list(analysis.supported_findings[:6])
    if dossier.creditsafe:
        evidence.append(
            f"Creditsafe MOCK: score {dossier.creditsafe.credit_score} "
            f"({dossier.creditsafe.rating_band}), payment={dossier.creditsafe.payment_behavior}"
        )
    if dossier.eu_vat_vies:
        evidence.append(
            f"VIES MOCK: {dossier.eu_vat_vies.vat_number} valid={dossier.eu_vat_vies.valid}"
        )

    cited_rules: list[str] = []
    for t in dossier.hard_risk_triggers:
        if t.startswith("[R"):
            cited_rules.append(t[1 : t.index("]")])
    if not cited_rules and dossier.recommendation == "APPROVED":
        cited_rules = ["R10"]

    sources = list(dossier.sources[:12])
    sources.extend(m.source_url for m in media if m.source_url)

    brief = FinalRecommendationBrief(
        recommendation_headline=headline,
        policy_recommendation=dossier.recommendation,
        rationale_for_partnerships=analysis.executive_brief,
        evidence_bullets=evidence[:8],
        open_questions=list(
            dict.fromkeys(
                [
                    *dossier.unsure_or_unverified[:4],
                    *analysis.residual_risks[:3],
                ]
            )
        )[:6],
        cited_rule_ids=list(dict.fromkeys(cited_rules))[:10],
        cited_sources=list(dict.fromkeys(sources))[:15],
        confidence_0_to_100=analysis.confidence_0_to_100,
        model_provider=f"final_brief:{analysis.model_provider}",
        human_review_required=True,
    )
    raw = json.dumps(brief.model_dump(exclude={"prompt_trace"}), indent=2)
    return _with_trace(
        brief,
        model="grounded_rules_analyst",
        user_message=user_message,
        raw_response=raw,
        used_llm=False,
    )


def _from_llm_json(
    data: dict,
    dossier: ResearchDossier,
    provider: str,
    *,
    user_message: str,
    raw_response: str,
) -> FinalRecommendationBrief:
    brief = FinalRecommendationBrief(
        recommendation_headline=str(data.get("recommendation_headline") or "")[:200],
        policy_recommendation=dossier.recommendation,
        rationale_for_partnerships=str(data.get("rationale_for_partnerships") or "")[:800],
        evidence_bullets=[str(x) for x in data.get("evidence_bullets") or []][:8],
        open_questions=[str(x) for x in data.get("open_questions") or []][:6],
        cited_rule_ids=[str(x) for x in data.get("cited_rule_ids") or []][:10],
        cited_sources=[str(x) for x in data.get("cited_sources") or []][:15],
        confidence_0_to_100=int(data.get("confidence_0_to_100") or 50),
        model_provider=provider,
        human_review_required=True,
    )
    return _with_trace(
        brief,
        model=provider,
        user_message=user_message,
        raw_response=raw_response,
        used_llm=True,
    )


def _call_groq(system: str, user_msg: str, model: str) -> str:
    import urllib.error
    import urllib.request

    body = json.dumps(
        {
            "model": model,
            "temperature": 0,
            "max_tokens": 1200,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=body,
        headers={
            "content-type": "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "User-Agent": "northmill-partner-research/0.2",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"Groq HTTP {exc.code}: {detail}") from exc
    return payload["choices"][0]["message"]["content"]


def generate_final_recommendation(
    dossier: ResearchDossier,
    media: list[AdverseMediaSignal] | None = None,
) -> FinalRecommendationBrief:
    media = media if media is not None else list(dossier.adverse_media)
    pack = locked_evidence_pack(dossier, media)
    stack = resolve_ai_stack()
    provider = stack["ai_provider"]
    model = stack["ai_model"]
    user_msg = build_final_user_message(pack)

    try:
        if provider == "bedrock" and (USE_BEDROCK or AI_PROVIDER == "bedrock"):
            import boto3
            from northmill.config import AWS_REGION

            client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
            response = client.converse(
                modelId=model or BEDROCK_MODEL_ID,
                system=[{"text": FINAL_SYSTEM}],
                messages=[{"role": "user", "content": [{"text": user_msg}]}],
                inferenceConfig={"temperature": 0.0, "maxTokens": 1200},
            )
            text = response["output"]["message"]["content"][0]["text"]
            return _from_llm_json(
                _parse_json_object(text),
                dossier,
                f"final_brief:bedrock:{model or BEDROCK_MODEL_ID}",
                user_message=user_msg,
                raw_response=text,
            )

        if provider == "anthropic" and ANTHROPIC_API_KEY:
            import urllib.request

            body = json.dumps(
                {
                    "model": model or ANTHROPIC_MODEL,
                    "max_tokens": 1200,
                    "temperature": 0,
                    "system": FINAL_SYSTEM,
                    "messages": [{"role": "user", "content": user_msg}],
                }
            ).encode("utf-8")
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=body,
                headers={
                    "content-type": "application/json",
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            text = "".join(
                block.get("text", "")
                for block in payload.get("content", [])
                if block.get("type") == "text"
            )
            return _from_llm_json(
                _parse_json_object(text),
                dossier,
                f"final_brief:anthropic:{model or ANTHROPIC_MODEL}",
                user_message=user_msg,
                raw_response=text,
            )

        if provider == "groq" and GROQ_API_KEY:
            text = _call_groq(FINAL_SYSTEM, user_msg, model or GROQ_MODEL)
            return _from_llm_json(
                _parse_json_object(text),
                dossier,
                f"final_brief:groq:{model or GROQ_MODEL}",
                user_message=user_msg,
                raw_response=text,
            )
    except Exception:  # noqa: BLE001
        pass

    return _rules_final_brief(dossier, media, user_message=user_msg)
