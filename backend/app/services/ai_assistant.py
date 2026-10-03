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
from typing import Any

import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.db import crud


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


def _call_llm(prompt: str, context: str) -> str:
    if not settings.LLM_API_KEY:
        # No LLM configured yet - return the grounded context directly
        # so the endpoint still works end-to-end.
        return f"(No LLM configured yet - showing raw context)\n\n{context}"
    # Try calling Anthropic's HTTP API as a simple provider integration.
    # If this fails for any reason, return the grounded context rather than
    # raising an error so the endpoint remains useful.
    try:
        url = "https://api.anthropic.com/v1/complete"
        prompt_text = f"Zone context:\n{context}\n\nQuestion: {prompt}\nAnswer concisely and only using the facts above."
        payload: dict[str, Any] = {
            "model": "claude-2",  # choose a reasonable default
            "prompt": prompt_text,
            "max_tokens": 500,
            "temperature": 0.0,
        }
        headers = {"x-api-key": settings.LLM_API_KEY}
        resp = httpx.post(url, json=payload, headers=headers, timeout=15.0)
        resp.raise_for_status()
        data = resp.json()
        # Anthropic's /complete returns a `completion` or `completion`-like field.
        text = data.get("completion") or data.get("completion_text") or data.get("text")
        if not text and isinstance(data.get("choices"), list):
            text = data["choices"][0].get("text")
        return text or f"(LLM returned no text)\n\n{context}"
    except Exception as e:
        return f"(LLM call failed: {repr(e)})\n\n{context}"


def ask_assistant(zone_id, question: str) -> str:
    # Validate zone exists before spending work/LLM credits
    zone = crud.get_zone(zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    safe_question = _normalize_question(question)
    context = _build_context(zone_id)
    return _call_llm(safe_question, context)
