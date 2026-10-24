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
