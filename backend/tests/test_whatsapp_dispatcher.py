import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.services.whatsapp.base import SendResult
from app.services.whatsapp.dispatcher import dispatch_alert, sanitize_alert_text


def _aware(hours_ago: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()


def _setup_dispatch(monkeypatch, contacts, approved_template=None):
    import app.services.whatsapp.dispatcher as dispatcher

    monkeypatch.setattr(dispatcher.crud, "get_alert", lambda _: {
        "id": "alert-1", "zone_id": "zone-1", "status": "approved",
        "severity": "Warning", "crop": "Maize", "message": "Rain is expected",
        "action": "Check drainage", "allow_links": False,
    })
    monkeypatch.setattr(dispatcher.crud, "get_zone", lambda _: {"district": "Gasabo"})
    monkeypatch.setattr(dispatcher.crud, "count_alert_subscription_contacts", lambda *args: len(contacts))
    monkeypatch.setattr(dispatcher.crud, "list_contacts_for_alert", lambda *args: contacts)
    monkeypatch.setattr(dispatcher.crud, "get_alert_contact_delivery", lambda *_: None)
    monkeypatch.setattr(dispatcher.crud, "count_outbound_messages_since", lambda *_: 0)
    monkeypatch.setattr(dispatcher.crud, "create_message_log", lambda record: {"id": "log-1", **record})
    monkeypatch.setattr(dispatcher.crud, "update_message_log", lambda *_: None)
    monkeypatch.setattr(dispatcher, "approved_template", lambda *_: approved_template)
    return dispatcher


def test_alert_must_be_human_approved(monkeypatch):
    import app.services.whatsapp.dispatcher as dispatcher

    monkeypatch.setattr(dispatcher.crud, "get_alert", lambda _: {"id": "alert-1", "status": "draft"})
    with pytest.raises(PermissionError):
        asyncio.run(dispatch_alert("alert-1", "admin"))


def test_within_window_sends_free_form_and_queues_log(monkeypatch):
    contact = {"id": "contact-1", "phone_e164": "+250788123456", "whatsapp_opt_in": True,
               "opt_out_at": None, "deleted_at": None, "last_inbound_at": _aware(2)}
    dispatcher = _setup_dispatch(monkeypatch, [contact])
    provider = type("Provider", (), {"send_text": AsyncMock(return_value=SendResult(True, "wamid.1"))})()
    monkeypatch.setattr(dispatcher, "get_provider", lambda: provider)
    result = asyncio.run(dispatcher.dispatch_alert("alert-1", "admin"))
    assert result["queued"] == 1
    provider.send_text.assert_awaited_once()


def test_outside_window_uses_only_approved_template(monkeypatch):
    contact = {"id": "contact-1", "phone_e164": "+250788123456", "whatsapp_opt_in": True,
               "opt_out_at": None, "deleted_at": None, "language": "rw", "last_inbound_at": _aware(30)}
    template = {"name": "agrimenya_alert", "language": "en", "status": "approved"}
    dispatcher = _setup_dispatch(monkeypatch, [contact], template)
    provider = type("Provider", (), {"send_template": AsyncMock(return_value=SendResult(True, "wamid.2"))})()
    monkeypatch.setattr(dispatcher, "get_provider", lambda: provider)
    result = asyncio.run(dispatcher.dispatch_alert("alert-1", "admin"))
    assert result["queued"] == 1
    provider.send_template.assert_awaited_once()
    assert provider.send_template.call_args.args[2] == "en"


def test_no_template_means_no_provider_call(monkeypatch):
    contact = {"id": "contact-1", "phone_e164": "+250788123456", "whatsapp_opt_in": True,
               "opt_out_at": None, "deleted_at": None, "last_inbound_at": _aware(30)}
    dispatcher = _setup_dispatch(monkeypatch, [contact])
    provider = type("Provider", (), {"send_template": AsyncMock()})()
    monkeypatch.setattr(dispatcher, "get_provider", lambda: provider)
    result = asyncio.run(dispatcher.dispatch_alert("alert-1", "admin"))
    assert result["skipped_no_template"] == 1
    provider.send_template.assert_not_awaited()


def test_opted_out_contact_is_blocked_even_if_crud_returns_it(monkeypatch):
    contact = {"id": "contact-1", "phone_e164": "+250788123456", "whatsapp_opt_in": False,
               "opt_out_at": _aware(1), "deleted_at": None, "last_inbound_at": _aware(2)}
    dispatcher = _setup_dispatch(monkeypatch, [contact])
    provider = type("Provider", (), {"send_text": AsyncMock()})()
    monkeypatch.setattr(dispatcher, "get_provider", lambda: provider)
    result = asyncio.run(dispatcher.dispatch_alert("alert-1", "admin"))
    assert result["skipped_no_consent"] == 1
    provider.send_text.assert_not_awaited()


def test_alert_sanitizer_removes_links_phone_numbers_and_controls():
    text = "Rain\x00 expected https://example.com call +250788123456 now"
    result = sanitize_alert_text(text)
    assert "example.com" not in result
    assert "+250788123456" not in result
    assert "\x00" not in result


def test_dispatch_api_refuses_unapproved_alert(monkeypatch):
    from fastapi.testclient import TestClient
    from app.core.config import settings
    from app.main import app

    monkeypatch.setattr(settings, "ADMIN_API_KEY", "test-admin-secret")
    monkeypatch.setattr("app.routers.whatsapp_admin.crud.get_alert", lambda _: {"id": "alert-1", "status": "draft"})
    response = TestClient(app).post(
        "/communication/alerts/alert-1/dispatch/whatsapp",
        headers={"X-Admin-Key": "test-admin-secret"},
    )
    assert response.status_code == 409
