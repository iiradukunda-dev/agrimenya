from copy import copy
from email.message import EmailMessage
from unittest.mock import Mock, patch

import httpx
import pytest
from fastapi import HTTPException

from app.core.config import Settings, settings
from app.services.email_delivery import (
    email_delivery_configuration_issue,
    email_delivery_configured,
    send_email_message,
)


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
    with pytest.raises(RuntimeError, match="RESEND_API_KEY is not configured"):
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


def test_gmail_smtp_requires_app_password_and_matching_sender(monkeypatch):
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "smtp")
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setattr(settings, "SMTP_USER", "")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "")
    monkeypatch.setattr(settings, "EMAIL_FROM", "Agri-Menya <sender@gmail.com>")
    assert email_delivery_configuration_issue() == "Gmail SMTP requires a Gmail App Password in SMTP_PASSWORD."
    assert not email_delivery_configured()

    monkeypatch.setattr(settings, "SMTP_PASSWORD", "test-app-password")
    monkeypatch.setattr(settings, "SMTP_USER", "different@gmail.com")
    assert "EMAIL_FROM must match SMTP_USER" in email_delivery_configuration_issue()


def test_gmail_smtp_authenticates_as_configured_sender(monkeypatch):
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "smtp")
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setattr(settings, "SMTP_PORT", 587)
    monkeypatch.setattr(settings, "SMTP_USER", "sender@gmail.com")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "test-app-password")
    monkeypatch.setattr(settings, "SMTP_USE_SSL", False)
    monkeypatch.setattr(settings, "SMTP_STARTTLS", True)
    monkeypatch.setattr(settings, "EMAIL_FROM", "Agri-Menya <sender@gmail.com>")

    message = EmailMessage()
    message["Subject"] = "Test"
    message.set_content("Test")

    with patch("app.services.email_delivery.smtplib.SMTP") as factory:
        result = send_email_message(message, recipient="recipient@example.org")

    smtp = factory.return_value.__enter__.return_value
    assert result == {"provider": "smtp", "message_id": None}
    smtp.starttls.assert_called_once()
    smtp.login.assert_called_once_with("sender@gmail.com", "test-app-password")


def test_email_status_reports_gmail_configuration_issue_without_secrets(monkeypatch):
    from app.routers.communication import email_status

    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "smtp")
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setattr(settings, "SMTP_USER", "")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "")
    monkeypatch.setattr(settings, "EMAIL_FROM", "Agri-Menya <sender@gmail.com>")

    result = email_status()

    assert result["ready"] is False
    assert result["gmail_smtp"] is True
    assert result["gmail_sender_matches_login"] is True
    assert result["configuration_issue"] == "Gmail SMTP requires a Gmail App Password in SMTP_PASSWORD."
    assert "test-app-password" not in str(result)


def test_admin_invitation_error_explains_resend_sender_rejection(monkeypatch):
    import httpx

    from app.routers.admin_auth import _issue_reset

    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "resend")
    response = httpx.Response(403, request=httpx.Request("POST", "https://api.resend.com/emails"))
    rejection = httpx.HTTPStatusError("sender rejected", request=response.request, response=response)

    with patch("app.routers.admin_auth.crud.create_admin_password_reset_token"), \
         patch("app.routers.admin_auth.send_reset_email", side_effect=rejection):
        with pytest.raises(HTTPException) as error:
            _issue_reset({"id": "admin-id", "email": "admin@example.org", "display_name": "Admin"})

    assert error.value.status_code == 503
    assert "verify that EMAIL_FROM uses your Resend-verified domain" in error.value.detail
