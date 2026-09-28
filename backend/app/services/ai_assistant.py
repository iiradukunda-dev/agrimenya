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
from app.core.config import settings
from app.db import crud


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

    # Example wiring for the Anthropic API - uncomment and adapt once
    # LLM_API_KEY is set. Left inactive rather than as a dead stub call
    # so nothing breaks before you choose a provider.
    #
    # import anthropic
    # client = anthropic.Anthropic(api_key=settings.LLM_API_KEY)
    # response = client.messages.create(
    #     model="claude-sonnet-4-6",
    #     max_tokens=500,
    #     messages=[{
    #         "role": "user",
    #         "content": f"Zone context:\n{context}\n\nQuestion: {prompt}"
    #     }],
    # )
    # return response.content[0].text

    return f"(LLM_API_KEY set but provider not yet wired in _call_llm)\n\n{context}"


def ask_assistant(zone_id, question: str) -> str:
    context = _build_context(zone_id)
    return _call_llm(question, context)
