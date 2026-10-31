"""Conservative crop-health triage using an installed model or configured Groq AI."""
from __future__ import annotations

import base64
import json
import logging
import re

import httpx

from app.core.config import settings
from app.ml.vision_disease_model import predict_vision_disease, vision_model_status

logger = logging.getLogger(__name__)
MAX_PROVIDER_IMAGE_BYTES = 5 * 1024 * 1024
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
SAFE_NEXT_STEP = "Have the crop and symptoms checked in person by an RAB or district agronomist before applying treatment."


def _clean_lines(value: object, maximum: int = 5) -> list[str]:
    if not isinstance(value, list):
        return []
    return [re.sub(r"\s+", " ", str(item)).strip()[:320] for item in value[:maximum] if str(item).strip()]


def _unconfirmed(crop: str | None, note: str) -> dict:
    return {
        "predicted_disease": "Unconfirmed",
        "plant_identification": "Not confirmed",
        "confidence": None,
        "risk_level": "Unknown",
        "urgency": "unclear",
        "observations": [],
        "possible_causes": [],
        "recommended_actions": [SAFE_NEXT_STEP],
        "crop": (crop or "Crop").strip().title(),
        "source": "unavailable",
        "interpretation_note": note,
    }


def _groq_triage(
    crop: str,
    symptoms: str,
    *,
    image_description: str | None,
    image_bytes: bytes | None,
    language: str,
) -> dict | None:
    if not settings.GROQ_API_KEY:
        return None
    if image_bytes and len(image_bytes) > MAX_PROVIDER_IMAGE_BYTES:
        return None

    model = settings.GROQ_VISION_MODEL if image_bytes else settings.GROQ_MODEL
    language_name = "Kinyarwanda" if language == "rw" else "English"
    instructions = (
        "You are Agri-Menya's crop-health visual triage assistant for Rwanda. Inspect the attached photo first; do not "
        "answer as if no photo was supplied. Identify the visible crop only when the image supports it, describe the "
        "specific visible signs, and give the most plausible issue with one or two alternatives. This is preliminary "
        "triage, not a confirmed diagnosis. Separate what is visible from what is inferred. Do not invent a pathogen, "
        "confidence percentage, weather, or treatment efficacy. Give practical steps in this order: what the farmer "
        "can check today, how to limit possible spread safely, and what evidence to send an extension officer. Do not "
        "prescribe pesticide products, dosage, or application schedules. If the image is blurry, too distant, or does "
        "not show a plant, say exactly what prevents identification and request a close photo of both leaf sides and "
        "the whole plant. Use the farmer's reported crop and symptoms as context, not proof. Respond in " + language_name + ". "
        "Return one JSON object only with keys: plant_identification (short string or 'Not confirmed'), likely_issue (short string), observations (2-5 concrete visual signs "
        "or reported symptoms), possible_causes (up to 3 short explanations), next_steps (3-5 specific safe actions), "
        "urgency (routine|soon|urgent|unclear), and limitations (one short sentence). Use urgency=urgent only when "
        "the photo/reports show rapid spread or substantial crop loss needing same-day local expert review."
    )
    user_text = (
        f"Crop reported by user: {crop[:50]}. "
        f"Symptoms reported: {symptoms[:1000] or 'None provided'}. "
        "Additional farmer-provided field/photo notes (not independently verified): "
        f"{(image_description or '').strip()[:1000] or 'None provided'}. Analyze only this case."
    )
    if image_bytes:
        image_data = "data:image/jpeg;base64," + base64.b64encode(image_bytes).decode("ascii")
        content = [
            {"type": "text", "text": user_text},
            {"type": "image_url", "image_url": {"url": image_data}},
        ]
    else:
        content = user_text

    try:
        with httpx.Client(timeout=45.0) as client:
            response = client.post(
                GROQ_CHAT_URL,
                headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": instructions},
                        {"role": "user", "content": content},
                    ],
                    "temperature": 0.1,
                    "max_completion_tokens": 1200,
                    "response_format": {"type": "json_object"},
                },
            )
            response.raise_for_status()
        raw = response.json()["choices"][0]["message"]["content"].strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
        parsed = json.loads(raw)
        likely_issue = re.sub(r"\s+", " ", str(parsed.get("likely_issue") or "Unconfirmed")).strip()[:160]
        plant_identification = re.sub(
            r"\s+", " ", str(parsed.get("plant_identification") or "Not confirmed")
        ).strip()[:100]
        observations = _clean_lines(parsed.get("observations"))
        possible_causes = _clean_lines(parsed.get("possible_causes"))
        next_steps = _clean_lines(parsed.get("next_steps"))
        urgency = str(parsed.get("urgency", "unclear")).casefold()
        if urgency not in {"routine", "soon", "urgent", "unclear"}:
            urgency = "unclear"
        limitations = re.sub(r"\s+", " ", str(parsed.get("limitations") or "")).strip()[:500]
        if likely_issue.casefold() != "unconfirmed" and not observations:
            # Never present an AI disease label without visible/report-based
            # evidence that helps the farmer understand and verify it.
            likely_issue = "Unconfirmed"
            limitations = (limitations + " No specific visual signs were returned, so the issue was not identified.")[:500]
        if not next_steps:
            next_steps = [SAFE_NEXT_STEP]
        return {
            "predicted_disease": likely_issue,
            "plant_identification": plant_identification,
            "confidence": None,
            "risk_level": "Unknown",
            "urgency": urgency,
            "observations": observations,
            "possible_causes": possible_causes,
            "recommended_actions": next_steps,
            "crop": crop.strip().title(),
            "source": "groq_vision_triage" if image_bytes else "groq_symptom_triage",
            "interpretation_note": (
                "AI-assisted preliminary triage, not a confirmed diagnosis. " + limitations
            ).strip(),
        }
    except (httpx.HTTPError, ValueError, KeyError, TypeError, IndexError):
        logger.exception("Groq crop triage failed")
        return None


def detect_crop_disease(
    crop: str | None,
    symptoms: str | None,
    image_description: str | None = None,
    image_bytes: bytes | None = None,
    language: str = "en",
) -> dict:
    """Use a real trained local image model if installed, otherwise configured Groq triage."""
    crop_name = (crop or "Crop").strip() or "Crop"
    symptoms_text = (symptoms or "").strip()
    if not symptoms_text and not image_bytes and not image_description:
        return _unconfirmed(crop_name, "Add a crop photo or describe the observed symptoms to start triage.")

    # Prefer the multimodal assistant: the local classifier only returns a
    # class label and cannot explain the image or give actionable triage.
    result = _groq_triage(
        crop_name,
        symptoms_text,
        image_description=image_description,
        image_bytes=image_bytes,
        language=language,
    )
    if result:
        return result

    # Keep a real local model as a clearly labeled fallback if the provider is
    # unavailable; never disguise the class score as calibrated confidence.
    if image_bytes and vision_model_status().get("trained"):
        local = predict_vision_disease(image_bytes, crop_hint=crop_name)
        if local.get("model_status") == "trained":
            return {
                "predicted_disease": str(local.get("predicted_disease") or "Unconfirmed").replace("_", " ").title(),
                "plant_identification": "Not confirmed by the local classifier",
                "confidence": None,  # The current local model score is not calibrated.
                "risk_level": "Unknown",
                "urgency": "unclear",
                "observations": [],
                "possible_causes": ["The local classifier's label needs visual confirmation."],
                "recommended_actions": [SAFE_NEXT_STEP],
                "crop": crop_name.title(),
                "source": "local_vision_model_preliminary",
                "interpretation_note": "The Groq vision service was unavailable. This experimental model returned a class label only; check leaf markings, affected plant parts, and spread with an agronomist before acting.",
            }
    return _unconfirmed(
        crop_name,
        "AI triage is unavailable or the evidence is insufficient. The photo and symptoms were not stored as a diagnosis. "
        "Ask an RAB or district agronomist to inspect the crop.",
    )
