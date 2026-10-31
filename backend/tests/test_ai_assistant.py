import uuid
import struct
import zlib
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _tiny_png() -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(b"\x00\x00\xff\x00"))
        + chunk(b"IEND", b"")
    )


def test_no_llm_returns_safe_grounded_fallback(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "LLM_API_KEY", "")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    zone_id = str(uuid.uuid4())
    payload = {"zone_id": zone_id, "question": "Tell me more about crops"}

    with patch("app.db.crud.get_zone") as mock_get_zone, \
         patch("app.db.crud.list_predictions") as mock_preds, \
         patch("app.db.crud.list_district_alerts", return_value=[]), \
         patch("app.db.crud.list_district_agri_metrics", return_value=[]), \
         patch("app.db.crud.list_alerts") as mock_alerts:
        mock_get_zone.return_value = {"id": zone_id, "district": "Gasabo", "sector": "S", "cell": "C"}
        mock_preds.return_value = []
        mock_alerts.return_value = []

        r = client.post("/chat", json=payload)
        assert r.status_code == 200
        assert "Choose a crop" not in r.json()["answer"]
        assert ("Official NISR SAS historical table" in r.json()["answer"]
                or "NISR database release" in r.json()["answer"])
        assert "historical district observations" in r.json()["answer"]
        assert "Banana" in r.json()["answer"]
        assert ("Official NISR SAS historical table" in r.json()["evidence_sources"]
                or "NISR database release" in r.json()["evidence_sources"])
        assert r.json()["answer_type"] == "record_grounded"
        assert "Gasabo" in r.json()["evidence_scope"]


def test_general_guidance_is_not_labelled_as_insufficient_evidence():
    zone_id = str(uuid.uuid4())
    with patch("app.routers.chat.ask_assistant_with_source", return_value=(
        "General guidance: Keep soil covered with clean mulch.", "grounded-local", "Musanze", []
    )), patch("app.routers.chat.enforce_request_limit"):
        response = client.post("/chat", json={"zone_id": zone_id, "question": "Teach me something"})

    assert response.status_code == 200
    assert response.json()["answer_type"] == "general_guidance"


def test_general_guidance_does_not_show_an_insufficient_evidence_warning():
    zone_id = str(uuid.uuid4())
    answer = (
        "The available records do not support a specific conclusion for this question.\n\n"
        "Crop rotation can help break pest and disease cycles and balance nutrient use."
    )
    with patch("app.routers.chat.ask_assistant_with_source", return_value=(
        answer, "groq", "Musanze", []
    )), patch("app.routers.chat.enforce_request_limit"):
        response = client.post(
            "/chat",
            json={"zone_id": zone_id, "question": "How can crop rotation help improve soil health?"},
        )

    assert response.status_code == 200
    assert response.json()["answer_type"] == "general_guidance"
    assert response.json()["answer"].startswith("General guidance:")
    assert "available records do not support" not in response.json()["answer"].casefold()


def test_configured_llm_uses_anthropic_messages_api(monkeypatch):
    from app.core.config import settings
    from app.services.ai_assistant import _call_llm

    monkeypatch.setattr(settings, "LLM_API_KEY", "test-anthropic-key")
    monkeypatch.setattr(settings, "LLM_MODEL", "claude-sonnet-4-6")
    response = Mock()
    response.json.return_value = {"content": [{"type": "text", "text": "Use mulching to retain moisture."}]}
    with patch("app.services.ai_assistant.httpx.post", return_value=response) as post:
        answer, source = _call_llm("How can I conserve water?", '{"basis":{},"alerts":[]}')

    assert answer == "Use mulching to retain moisture."
    assert source == "anthropic"
    assert post.call_args.args[0] == "https://api.anthropic.com/v1/messages"
    assert post.call_args.kwargs["headers"]["x-api-key"] == "test-anthropic-key"
    assert post.call_args.kwargs["json"]["model"] == "claude-sonnet-4-6"
    assert post.call_args.kwargs["json"]["max_tokens"] == 1024


def test_missing_zone_returns_404():
    zone_id = str(uuid.uuid4())
    payload = {"zone_id": zone_id, "question": "Q"}
    with patch("app.db.crud.get_zone") as mock_get_zone:
        mock_get_zone.return_value = None
        r = client.post("/chat", json=payload)
        assert r.status_code == 404


def test_disease_detection_from_prompt():
    zone_id = str(uuid.uuid4())
    payload = {
        "zone_id": zone_id,
        "crop": "maize",
        "symptoms": "yellowing leaves, brown lesions, wilting across the field",
        "image_description": "brown lesions on leaves with dry patches"
    }

    with patch("app.db.crud.get_zone") as mock_get_zone:
        mock_get_zone.return_value = {"id": zone_id, "district": "Gasabo", "sector": "S", "cell": "C"}
        r = client.post("/chat/disease-detect", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert "predicted_disease" in data
        assert "confidence" in data
        assert "recommended_actions" in data
        assert "observations" in data
        assert "possible_causes" in data
        assert "urgency" in data


def test_disease_detection_from_uploaded_image():
    zone_id = str(uuid.uuid4())
    with patch("app.db.crud.get_zone") as mock_get_zone:
        mock_get_zone.return_value = {"id": zone_id, "district": "Gasabo", "sector": "S", "cell": "C"}
        file_content = _tiny_png()
        r = client.post(
            "/chat/disease-detect-upload",
            data={"zone_id": zone_id, "crop": "maize", "symptoms": "brown lesions and wilting", "image_description": "dry patches on leaves"},
            files={"image": ("leaf_scan.png", file_content, "image/png")},
        )
        assert r.status_code == 200
        data = r.json()
        assert "predicted_disease" in data
        assert "recommended_actions" in data


def test_decision_disease_risk_returns_cautious_triage_details():
    zone_id = str(uuid.uuid4())
    assessment = {
        "crop": "Maize",
        "predicted_disease": "Unconfirmed",
        "plant_identification": "Maize",
        "confidence": None,
        "risk_level": "Unknown",
        "urgency": "unclear",
        "observations": ["Yellowing reported"],
        "possible_causes": ["Nutrient stress"],
        "recommended_actions": ["Ask a district agronomist to inspect the crop."],
        "source": "unavailable",
        "interpretation_note": "Evidence is insufficient.",
    }

    with patch("app.db.crud.get_zone", return_value={"id": zone_id}), \
         patch("app.routers.decision.detect_crop_disease", return_value=assessment) as detect:
        response = client.post(
            "/decision/disease-risk",
            params={
                "zone_id": zone_id,
                "crop": "Maize",
                "symptoms": "Yellowing",
                "image_description": "Lower leaves affected",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] == "Unknown"
    assert data["urgency"] == "unclear"
    assert data["observations"] == ["Yellowing reported"]
    assert data["possible_causes"] == ["Nutrient stress"]
    detect.assert_called_once_with("Maize", "Yellowing", "Lower leaves affected")


def test_disease_triage_includes_additional_field_notes(monkeypatch):
    from app.core.config import settings
    from app.services.disease_detector import _groq_triage

    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key")
    response = Mock()
    response.json.return_value = {
        "choices": [{
            "message": {
                "content": (
                    '{"likely_issue":"Unconfirmed","plant_identification":"Maize",'
                    '"observations":["Brown marks reported"],"possible_causes":[],'
                    '"next_steps":["Ask an agronomist"],"urgency":"unclear","limitations":"Preliminary"}'
                )
            }
        }]
    }

    with patch("app.services.disease_detector.httpx.Client") as client_class:
        post = client_class.return_value.__enter__.return_value.post
        post.return_value = response
        _groq_triage(
            "Maize",
            "Yellowing leaves",
            image_description="Brown marks underneath the leaves",
            image_bytes=None,
            language="en",
        )

    provider_prompt = post.call_args.kwargs["json"]["messages"][1]["content"]
    assert "Yellowing leaves" in provider_prompt
    assert "Brown marks underneath the leaves" in provider_prompt


def test_disease_triage_keeps_safe_unconfirmed_fallback_without_provider(monkeypatch):
    from app.core.config import settings
    from app.services.disease_detector import SAFE_NEXT_STEP, detect_crop_disease

    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    with patch("app.services.disease_detector.vision_model_status", return_value={"trained": False}):
        result = detect_crop_disease("Maize", "Yellowing leaves")

    assert result["predicted_disease"] == "Unconfirmed"
    assert result["confidence"] is None
    assert result["risk_level"] == "Unknown"
    assert result["source"] == "unavailable"
    assert SAFE_NEXT_STEP in result["recommended_actions"]
