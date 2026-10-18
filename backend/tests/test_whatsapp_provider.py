import asyncio
import logging

import httpx
import pytest

from app.core.config import settings
from app.services.whatsapp.base import SendResult
from app.services.whatsapp.live import LiveProvider
from app.services.whatsapp.mock import MockProvider
from app.services.whatsapp.phone import mask_phone, normalize_phone


@pytest.mark.parametrize("raw,expected", [
    ("0788123456", "+250788123456"),
    ("788123456", "+250788123456"),
    ("+250788123456", "+250788123456"),
    ("250 788 123 456", "+250788123456"),
    ("00250788123456", "+250788123456"),
])
def test_normalize_rwanda_phone(raw, expected):
    assert normalize_phone(raw) == expected


@pytest.mark.parametrize("raw", ["", "letters", "+250612345678", "+123", "078812345"])
def test_reject_invalid_phone(raw):
    with pytest.raises(ValueError):
        normalize_phone(raw)


def test_mask_phone_hides_middle_digits():
    assert mask_phone("+250788123456") == "+250•••••456"


def test_mock_provider_records_text_and_forced_failure():
    provider = MockProvider()
    sent = asyncio.run(provider.send_text("+250788123456", "Hello"))
    assert sent.ok and sent.wa_message_id
    assert provider.sent[0]["body"] == "Hello"

    provider.fail_for("+250788123456", SendResult(False, error_code="test_failure"))
    failed = asyncio.run(provider.send_text("+250788123456", "Again"))
    assert not failed.ok
    assert len(provider.sent) == 1


def test_live_provider_posts_meta_text_payload(monkeypatch):
    monkeypatch.setattr(settings, "WHATSAPP_GRAPH_VERSION", "v-test")
    monkeypatch.setattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "phone-id")
    monkeypatch.setattr(settings, "WHATSAPP_ACCESS_TOKEN", "secret-token")
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json={"messages": [{"id": "wamid.test"}]})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = asyncio.run(LiveProvider(client).send_text("+250788123456", "Hello"))
    finally:
        asyncio.run(client.aclose())

    assert result.ok
    assert result.wa_message_id == "wamid.test"
    assert calls[0].url.path.endswith("/phone-id/messages")
    assert calls[0].headers["Authorization"] == "Bearer secret-token"


def test_meta_outside_window_is_not_retried(monkeypatch):
    monkeypatch.setattr(settings, "WHATSAPP_GRAPH_VERSION", "v-test")
    monkeypatch.setattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "phone-id")
    monkeypatch.setattr(settings, "WHATSAPP_ACCESS_TOKEN", "secret-token")
    attempts = []

    def handler(request):
        attempts.append(request)
        return httpx.Response(400, json={"error": {"code": 131047}})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = asyncio.run(LiveProvider(client).send_text("+250788123456", "Hello"))
    finally:
        asyncio.run(client.aclose())

    assert result.error_detail == "outside_window"
    assert not result.retryable
    assert len(attempts) == 1


def test_meta_429_retries(monkeypatch):
    monkeypatch.setattr(settings, "WHATSAPP_GRAPH_VERSION", "v-test")
    monkeypatch.setattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "phone-id")
    monkeypatch.setattr(settings, "WHATSAPP_ACCESS_TOKEN", "secret-token")
    attempts = []

    def handler(request):
        attempts.append(request)
        if len(attempts) == 1:
            return httpx.Response(429, json={"error": {"code": 130429}})
        return httpx.Response(200, json={"messages": [{"id": "wamid.retried"}]})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = asyncio.run(LiveProvider(client).send_text("+250788123456", "Hello"))
    finally:
        asyncio.run(client.aclose())

    assert result.ok
    assert len(attempts) == 2


def test_provider_logs_never_include_token(monkeypatch, caplog):
    monkeypatch.setattr(settings, "WHATSAPP_GRAPH_VERSION", "v-test")
    monkeypatch.setattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "phone-id")
    monkeypatch.setattr(settings, "WHATSAPP_ACCESS_TOKEN", "secret-token")

    def handler(request):
        return httpx.Response(400, json={"error": {"code": 131047, "message": "rejected"}})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        with caplog.at_level(logging.INFO):
            asyncio.run(LiveProvider(client).send_text("+250788123456", "Hello"))
    finally:
        asyncio.run(client.aclose())

    assert "secret-token" not in caplog.text
    assert "+250788123456" not in caplog.text
