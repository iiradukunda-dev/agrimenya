from copy import copy
from email.message import EmailMessage
from unittest.mock import Mock, patch

import httpx
import pytest

from app.core.config import Settings, settings
from app.services.email_delivery import email_delivery_configured, send_email_message


def test_resend_email_is_sent_over_https_without_exposing_other_recipients(monkeypatch):
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "resend")
    monkeypatch.setattr(settings, "RESEND_API_KEY", "test-resend-key")
    monkeypatch.setattr(settings, "EMAIL_FROM", "Agri-Menya <no-reply@mail.example.org>")

    message = EmailMessage()
    message["Subject"] = "Verify your account"
    message["Reply-To"] = "support@example.org"
    message.set_content("Open the one-time verification link.")
    response = Mock()
    response.json.return_value = {"id": "email_123"}

    with patch("app.services.email_delivery.httpx.post", return_value=response) as post:
        result = send_email_message(message, recipient="farmer@example.net")

    assert result == {"provider": "resend", "message_id": "email_123"}
    post.assert_called_once_with(
        "https://api.resend.com/emails",
        headers={"Authorization": "Bearer test-resend-key"},
        json={
            "from": "Agri-Menya <no-reply@mail.example.org>",
            "to": ["farmer@example.net"],
            "subject": "Verify your account",
            "text": "Open the one-time verification link.\n",
            "reply_to": "support@example.org",
        },
        timeout=15,
    )


def test_resend_requires_api_key_and_sender(monkeypatch):
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "resend")
    monkeypatch.setattr(settings, "RESEND_API_KEY", "")
    monkeypatch.setattr(settings, "EMAIL_FROM", "Agri-Menya <no-reply@mail.example.org>")
    assert not email_delivery_configured()

    message = EmailMessage()
    message["Subject"] = "Test"
    message.set_content("Test")
    with pytest.raises(RuntimeError, match="Email delivery is not configured"):
        send_email_message(message, recipient="farmer@example.net")


def test_resend_provider_error_is_not_reported_as_success(monkeypatch):
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "resend")
    monkeypatch.setattr(settings, "RESEND_API_KEY", "test-resend-key")
    monkeypatch.setattr(settings, "EMAIL_FROM", "Agri-Menya <no-reply@mail.example.org>")
    response = Mock()
    response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "provider rejected the message",
        request=httpx.Request("POST", "https://api.resend.com/emails"),
        response=httpx.Response(403),
    )

    message = EmailMessage()
    message["Subject"] = "Test"
    message.set_content("Test")
    with patch("app.services.email_delivery.httpx.post", return_value=response):
        with pytest.raises(httpx.HTTPStatusError):
            send_email_message(message, recipient="farmer@example.net")


def test_production_validation_accepts_resend_without_smtp():
    production = copy(Settings())
    production.APP_ENV = "production"
    production.SUPABASE_URL = "https://project.supabase.co"
    production.SUPABASE_KEY = "service-role-key"
    production.SUPABASE_SERVICE_ROLE_KEY = "service-role-key"
    production.USER_API_KEY = "u" * 48
    production.JWT_SECRET = "j" * 48
    production.ALLOWED_ORIGINS = ["https://app.example.org"]
    production.ALLOWED_HOSTS = ["api.example.org", "api", "127.0.0.1"]
    production.ADMIN_PASSWORD_RESET_URL = "https://app.example.org/Admin"
    production.COMMUNITY_PASSWORD_RESET_URL = "https://app.example.org/Community"
    production.GOOGLE_OAUTH_CLIENT_ID = ""
    production.GOOGLE_OAUTH_CLIENT_SECRET = ""
    production.EMAIL_PROVIDER = "resend"
    production.RESEND_API_KEY = "test-resend-key"
    production.EMAIL_FROM = "Agri-Menya <no-reply@mail.example.org>"
    production.SMTP_HOST = ""
    production.SMTP_USER = ""
    production.SMTP_PASSWORD = ""

    production.validate_production()
