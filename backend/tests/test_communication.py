import uuid
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.models.alert import Severity

client = TestClient(app)


@patch("app.routers.communication.send_notification")
def test_create_and_list_alerts(mock_send):
    zone_id = uuid.uuid4()
    payload = {"zone_id": str(zone_id), "message": "Test alert", "severity": "Warning", "created_by": "tester"}
    mock_send.return_value = {"status": "unavailable", "deliveries": {}}

    with patch("app.db.crud.create_alert") as mock_create, patch("app.db.crud.list_alerts") as mock_list:
        mock_create.return_value = {"id": str(uuid.uuid4()), **payload}
        mock_list.return_value = [mock_create.return_value]

        r1 = client.post("/communication/alerts", json=payload)
        assert r1.status_code == 200
        assert r1.json()["severity"] == "Warning"

        r2 = client.get(f"/communication/alerts?zone_id={zone_id}")
        assert r2.status_code == 200
        assert isinstance(r2.json(), list)


def test_invalid_severity_rejected():
    zone_id = uuid.uuid4()
    payload = {"zone_id": str(zone_id), "message": "Bad severity", "severity": "Severe", "created_by": "tester"}
    r = client.post("/communication/alerts", json=payload)
    assert r.status_code == 422


@patch("app.db.crud.get_plan")
def test_share_plan(mock_get_plan):
    plan_id = str(uuid.uuid4())
    mock_get_plan.return_value = {"id": plan_id, "title": "P"}
    r = client.get(f"/communication/share/{plan_id}")
    assert r.status_code == 200
    assert r.json()["id"] == plan_id


@patch("app.routers.communication.send_notification")
def test_send_notification_route(mock_send):
    mock_send.return_value = {
        "status": "queued",
        "channels": ["sms", "whatsapp"],
        "message": "Alert queued for delivery",
        "simulated": True,
    }

    payload = {
        "phone": "+250788123456",
        "email": "farmer@example.com",
        "message": "Rain expected in 2 hours.",
        "channels": ["sms", "whatsapp", "email"],
    }

    r = client.post("/communication/notify", json=payload)
    assert r.status_code == 200
    assert r.json()["status"] == "queued"
    assert mock_send.called


@patch("app.routers.communication.send_notification")
@patch("app.db.crud.create_alert")
def test_alert_creation_triggers_notification(mock_create_alert, mock_send):
    zone_id = uuid.uuid4()
    payload = {"zone_id": str(zone_id), "message": "Flood risk detected.", "severity": "Critical", "created_by": "tester"}
    mock_create_alert.return_value = {"id": str(uuid.uuid4()), **payload}
    mock_send.return_value = {"status": "queued", "channels": ["sms"], "simulated": True}

    r = client.post("/communication/alerts", json=payload)
    assert r.status_code == 200
    assert mock_send.called


def test_contact_message_reports_unavailable_without_smtp(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "SMTP_HOST", "")
    monkeypatch.setattr(settings, "EMAIL_FROM", "")
    monkeypatch.setattr(settings, "DEFAULT_NOTIFICATION_EMAIL", "")
    response = client.post(
        "/communication/contact",
        json={"name": "A Farmer", "email": "farmer@example.com", "subject": "Help", "message": "Please call me."},
    )
    assert response.status_code == 503
    assert "configure SMTP_HOST" in response.json()["detail"]


def test_contact_message_sends_to_support_inbox(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "SMTP_PORT", 587)
    monkeypatch.setattr(settings, "SMTP_USER", "smtp-user")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "smtp-password")
    monkeypatch.setattr(settings, "SMTP_USE_SSL", False)
    monkeypatch.setattr(settings, "SMTP_STARTTLS", True)
    monkeypatch.setattr(settings, "EMAIL_FROM", "noreply@example.com")
    monkeypatch.setattr(settings, "DEFAULT_NOTIFICATION_EMAIL", "support@example.com")

    with patch("app.routers.communication.smtplib.SMTP") as smtp_factory:
        smtp = smtp_factory.return_value.__enter__.return_value
        response = client.post(
            "/communication/contact",
            json={"name": "A Farmer", "email": "farmer@example.com", "subject": "Help", "message": "Please call me."},
        )

    assert response.status_code == 200
    assert response.json() == {"status": "sent"}
    smtp_factory.assert_called_once_with("smtp.example.com", 587, timeout=15)
    smtp.starttls.assert_called_once()
    smtp.login.assert_called_once_with("smtp-user", "smtp-password")
    message = smtp.send_message.call_args.args[0]
    assert message["To"] == "support@example.com"
    assert message["Reply-To"] == "farmer@example.com"


def test_smtp_implicit_tls_does_not_starttls(monkeypatch):
    from app.core.config import settings
    from app.routers.communication import _deliver_smtp
    from email.message import EmailMessage

    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "SMTP_PORT", 465)
    monkeypatch.setattr(settings, "SMTP_USER", "")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "")
    monkeypatch.setattr(settings, "SMTP_USE_SSL", True)
    monkeypatch.setattr(settings, "SMTP_STARTTLS", True)
    with patch("app.routers.communication.smtplib.SMTP_SSL") as factory:
        _deliver_smtp(EmailMessage())
    factory.assert_called_once_with("smtp.example.com", 465, timeout=15)
    factory.return_value.__enter__.return_value.starttls.assert_not_called()


def test_twilio_sms_prefers_restricted_api_key(monkeypatch):
    from app.core.config import settings
    from app.routers.communication import _send_sms

    monkeypatch.setattr(settings, "TWILIO_SID", "AC-account")
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", "")
    monkeypatch.setattr(settings, "TWILIO_API_KEY_SID", "SK-key")
    monkeypatch.setattr(settings, "TWILIO_API_KEY_SECRET", "secret")
    monkeypatch.setattr(settings, "TWILIO_PHONE", "+250700000000")
    response = Mock()
    response.json.return_value = {"sid": "SM-message", "status": "queued"}
    with patch("app.routers.communication.httpx.post", return_value=response) as post:
        result = _send_sms("+250711111111", "Test message")

    assert result["status"] == "accepted"
    assert result["message_sid"] == "SM-message"
    assert post.call_args.kwargs["auth"] == ("SK-key", "secret")
    assert post.call_args.kwargs["data"] == {
        "From": "+250700000000",
        "To": "+250711111111",
        "Body": "Test message",
    }


def test_direct_twilio_whatsapp_is_disabled(monkeypatch):
    from app.routers.communication import _send_whatsapp

    with patch("app.routers.communication.httpx.post") as post:
        result = _send_whatsapp("+250711111111", "Test message")

    assert result["status"] == "unavailable"
    assert not post.called


def test_twilio_is_unavailable_when_credentials_are_missing(monkeypatch):
    from app.core.config import settings
    from app.routers.communication import _send_sms

    for key in ("TWILIO_SID", "TWILIO_AUTH_TOKEN", "TWILIO_API_KEY_SID", "TWILIO_API_KEY_SECRET", "TWILIO_PHONE"):
        monkeypatch.setattr(settings, key, "")
    result = _send_sms("+250711111111", "Test message")
    assert result["status"] == "unavailable"
    assert result["provider"] == "twilio"
