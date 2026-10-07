"""
Chat assistant: answers questions grounded in a zone's actual data
(predictions, alignment metrics, recent alerts) rather than free-floating
chat, so answers stay tied to real numbers in the database.

Works with any LLM provider that exposes an OpenAI-compatible or
Anthropic-compatible chat endpoint - fill in `_call_llm()` with your
chosen provider once LLM_API_KEY is set. Until then it returns a
grounded summary without calling an external LLM, so the endpoint is
usable immediately.
"""
import logging

import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.db import crud

logger = logging.getLogger(__name__)


def _normalize_question(question: str) -> str:
    """Normalize and validate user input before it reaches the LLM.

    We keep the contract intentionally strict: empty input is rejected,
    prompt-injection attempts are blocked, and oversized prompts are trimmed
    to a production-safe limit.
    """
    if question is None:
        raise HTTPException(status_code=400, detail="Question is required")

    normalized = str(question).strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    if len(normalized) > 500:
        raise HTTPException(status_code=400, detail="Question is too long")

    blocked_patterns = (
        "ignore previous instructions",
        "system prompt",
        "developer message",
        "jailbreak",
        "pretend you are",
    )
    lower = normalized.lower()
    if any(pattern in lower for pattern in blocked_patterns):
        raise HTTPException(status_code=400, detail="Question contains unsupported instructions")

    return normalized


def _build_context(zone_id) -> str:
    zone = crud.get_zone(zone_id)
    predictions = crud.list_predictions(zone_id)
    alignment = crud.get_alignment_metric(zone_id)
    alerts = crud.list_alerts(zone_id)

    lines = []
    if zone:
        lines.append(f"Zone: {zone.get('district')}, {zone.get('sector')}, {zone.get('cell')}")
    if predictions:
        latest = predictions[0]
        lines.append(
            f"Latest prediction: yield={latest.get('predicted_yield')}, "
            f"priority={latest.get('priority_level')}, confidence={latest.get('confidence')}"
        )
    if alignment:
        lines.append(
            f"Alignment: credit/insurance score={alignment.get('credit_insurance_score')}, "
            f"nutrition risk={alignment.get('nutrition_risk_level')}, "
            f"climate risk={alignment.get('climate_risk_level')}"
        )
    if alerts:
        lines.append(f"Active alerts: {len(alerts)} (most recent: {alerts[0].get('message')})")

    return "\n".join(lines) if lines else "No data available for this zone yet."


def _call_llm(prompt: str, context: str) -> tuple[str, str]:
    if not settings.LLM_API_KEY:
        return f"(No LLM configured yet - showing raw context)\n\n{context}", "grounded-context"
    try:
        response = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.LLM_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": settings.LLM_MODEL,
                "max_tokens": 500,
                "system": "Answer the user using only the supplied agricultural zone context. If the context does not contain the answer, say what is missing. Keep advice practical and concise.",
                "messages": [{"role": "user", "content": f"Zone context:\n{context}\n\nQuestion: {prompt}"}],
            },
            timeout=20.0,
        )
        response.raise_for_status()
        content = response.json().get("content", [])
        answer = "\n".join(item.get("text", "") for item in content if item.get("type") == "text").strip()
        if answer:
            return answer, "anthropic"
        logger.warning("Anthropic returned no text for the assistant request")
    except Exception:
        logger.exception("Anthropic assistant request failed; returning grounded zone context")
    return f"(AI service unavailable - showing grounded context)\n\n{context}", "grounded-context"


def ask_assistant_with_source(zone_id, question: str) -> tuple[str, str]:
    # Validate zone exists before spending work/LLM credits
    zone = crud.get_zone(zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    safe_question = _normalize_question(question)
    context = _build_context(zone_id)
    return _call_llm(safe_question, context)


def ask_assistant(zone_id, question: str) -> str:
    """Backward-compatible answer-only API for callers outside the route."""
    answer, _ = ask_assistant_with_source(zone_id, question)
    return answer
