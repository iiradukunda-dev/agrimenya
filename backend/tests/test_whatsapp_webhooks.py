import asyncio
import hashlib
import hmac
import json
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.routers import webhooks
from app.services.whatsapp.consent import parse_keyword

client = TestClient(app)


def test_webhook_handshake_requires_matching_token(monkeypatch):
    monkeypatch.setattr(settings, "WHATSAPP_VERIFY_TOKEN", "verify-me")
    accepted = client.get("/webhooks/whatsapp", params={
        "hub.mode": "subscribe", "hub.verify_token": "verify-me", "hub.challenge": "abc123",
    })
    rejected = client.get("/webhooks/whatsapp", params={
        "hub.mode": "subscribe", "hub.verify_token": "wrong", "hub.challenge": "abc123",
    })
    assert accepted.status_code == 200
    assert accepted.text == "abc123"
    assert rejected.status_code == 403


def test_webhook_post_rejects_invalid_signature(monkeypatch):
    monkeypatch.setattr(settings, "WHATSAPP_MODE", "live")
    monkeypatch.setattr(settings, "WHATSAPP_APP_SECRET", "app-secret")
    response = client.post(
        "/webhooks/whatsapp",
        content=b'{"object":"whatsapp_business_account"}',
        headers={"X-Hub-Signature-256": "sha256=invalid"},
    )
    assert response.status_code == 403


def test_webhook_post_accepts_valid_signature(monkeypatch):
    monkeypatch.setattr(settings, "WHATSAPP_MODE", "live")
    monkeypatch.setattr(settings, "WHATSAPP_APP_SECRET", "app-secret")
    raw = json.dumps({"object": "whatsapp_business_account", "entry": []}).encode()
    signature = hmac.new(b"app-secret", raw, hashlib.sha256).hexdigest()
    with patch("app.routers.webhooks.process_webhook") as process:
        response = client.post(
            "/webhooks/whatsapp", content=raw,
            headers={"X-Hub-Signature-256": f"sha256={signature}"},
        )
    assert response.status_code == 200
    assert response.json() == {"status": "accepted"}
    process.assert_called_once()


def test_duplicate_status_event_is_ignored(monkeypatch):
    monkeypatch.setattr("app.routers.webhooks.crud.insert_webhook_event", lambda *_: False)
    with patch("app.routers.webhooks.crud.get_message_by_wa_id") as get_message:
        asyncio.run(webhooks._process_status({"id": "wamid.1", "status": "sent"}))
    get_message.assert_not_called()


def test_late_sent_status_does_not_downgrade_delivered(monkeypatch):
    monkeypatch.setattr("app.routers.webhooks.crud.insert_webhook_event", lambda *_: True)
    record = {"id": "row-1", "status": "delivered", "contact_id": "contact-1"}
    monkeypatch.setattr("app.routers.webhooks.crud.get_message_by_wa_id", lambda _: record)
    with patch("app.routers.webhooks.crud.update_message_log") as update:
        asyncio.run(webhooks._process_status({"id": "wamid.1", "status": "sent"}))
    update.assert_not_called()


def test_stop_keyword_disables_contact_and_confirms_once(monkeypatch):
    contact = {
        "id": "contact-1", "phone_e164": "+250788123456", "bsuid": None,
        "whatsapp_opt_in": True, "opt_out_at": None,
    }
    monkeypatch.setattr("app.routers.webhooks.crud.insert_webhook_event", lambda *_: True)
    monkeypatch.setattr("app.routers.webhooks.crud.find_contact", lambda **_: contact)
    monkeypatch.setattr("app.routers.webhooks.crud.touch_inbound", lambda *_: contact)
    monkeypatch.setattr("app.routers.webhooks.crud.create_message_log", lambda record: {"id": "log-1", **record})
    monkeypatch.setattr("app.routers.webhooks.crud.set_opt_out", lambda *_: {**contact, "whatsapp_opt_in": False})
    monkeypatch.setattr("app.routers.webhooks.crud.update_message_log", lambda *_: None)
    with patch("app.routers.webhooks._send_logged_reply", new_callable=AsyncMock) as reply:
        asyncio.run(webhooks._process_message(
            {"id": "wamid.in", "from": "250788123456", "type": "text", "text": {"body": "STOP!!!"}},
            {},
        ))
    reply.assert_called_once()


def test_keywords_are_case_and_punctuation_insensitive():
    assert parse_keyword(" hereza!!! ") == "STOP"
    assert parse_keyword("EMERA") == "START"
    assert parse_keyword("can you help") is None
