"""Runtime config: AI provider/model + feature flags (anti-hallucination defaults)."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# backend/.env regardless of cwd
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_BACKEND_ROOT / ".env")

DATA_DIR = _BACKEND_ROOT / "data"

# AI routing: auto | bedrock | anthropic | groq | rules
AI_PROVIDER = os.getenv("AI_PROVIDER", "auto").strip().lower()
AI_MODEL = os.getenv("AI_MODEL", "").strip()

USE_BEDROCK = os.getenv("USE_BEDROCK", "false").lower() in {"1", "true", "yes"}
AWS_REGION = os.getenv("AWS_REGION", "eu-north-1")
BEDROCK_MODEL_ID = os.getenv(
    "BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20240620-v1:0"
)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

# Free-tier friendly (https://console.groq.com) — OpenAI-compatible chat API
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

USE_LIVE_NEWS = os.getenv("USE_LIVE_NEWS", "true").lower() in {"1", "true", "yes"}
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")


def resolve_ai_stack() -> dict:
    """What the running process will actually use for narrative analysis."""
    provider = AI_PROVIDER
    if provider == "auto":
        if USE_BEDROCK:
            provider = "bedrock"
        elif ANTHROPIC_API_KEY:
            provider = "anthropic"
        elif GROQ_API_KEY:
            provider = "groq"
        else:
            provider = "rules"

    if provider == "bedrock":
        model = AI_MODEL or BEDROCK_MODEL_ID
        connected = True
        label = f"AI connected - {model}"
    elif provider == "anthropic":
        model = AI_MODEL or ANTHROPIC_MODEL
        connected = bool(ANTHROPIC_API_KEY)
        label = (
            f"AI connected - {model}"
            if connected
            else "AI disconnected - Grounded-rules analysis"
        )
        if not connected:
            provider = "rules"
            model = "grounded_rules_analyst"
    elif provider == "groq":
        model = AI_MODEL or GROQ_MODEL
        connected = bool(GROQ_API_KEY)
        label = (
            f"AI connected - {model}"
            if connected
            else "AI disconnected - Grounded-rules analysis"
        )
        if not connected:
            provider = "rules"
            model = "grounded_rules_analyst"
    else:
        provider = "rules"
        model = "grounded_rules_analyst"
        connected = False
        label = "AI disconnected - Grounded-rules analysis"

    return {
        "ai_provider": provider,
        "ai_model": model,
        "connected": connected,
        "ux_label": label,
        "use_live_news": USE_LIVE_NEWS,
        "llm_may_change_recommendation": False,
        "how_to_connect": {
            "groq_free_tier": "https://console.groq.com - create key, set GROQ_API_KEY in backend/.env",
            "anthropic": "https://console.anthropic.com - set ANTHROPIC_API_KEY",
            "bedrock": "AWS account + USE_BEDROCK=true + BEDROCK_MODEL_ID",
            "cursor_note": (
                "Cursor's built-in models are for the IDE agent only. "
                "This app needs its own API key in backend/.env."
            ),
        },
        "note": (
            "Set AI_PROVIDER=auto|groq|anthropic|bedrock|rules and optional AI_MODEL in backend/.env. "
            "Policy verdict is always rule-based; the model only drafts grounded narrative."
        ),
    }
