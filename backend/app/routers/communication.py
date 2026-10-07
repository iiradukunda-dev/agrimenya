from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.auth import require_user
from app.db import crud
from app.models.alert import AlertCreate

router = APIRouter(prefix="/communication", tags=["Communication"])

VALID_CHANNELS = {"sms", "whatsapp", "email", "voice", "ussd"}


class NotificationRequest(BaseModel):
    phone: str | None = None
    email: str | None = None
    message: str = Field(..., min_length=1, max_length=1000)
    channels: list[str] = Field(default_factory=lambda: ["sms", "whatsapp"])


class ContactMessageRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    email: str = Field(..., min_length=3, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    subject: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=5000)


def _normalize_channels(channels: list[str] | None) -> list[str]:
    if not channels:
        return ["sms", "whatsapp"]
    normalized = []
    for channel in channels:
        name = str(channel).strip().lower()
        if name in VALID_CHANNELS and name not in normalized:
            normalized.append(name)
    return normalized or ["sms", "whatsapp"]


def _twilio_auth() -> tuple[str, str] | None:
    """Prefer restricted API keys; retain Account SID/Auth Token compatibility."""
    if settings.TWILIO_API_KEY_SID and settings.TWILIO_API_KEY_SECRET and settings.TWILIO_SID:
        return settings.TWILIO_API_KEY_SID, settings.TWILIO_API_KEY_SECRET
    if settings.TWILIO_SID and settings.TWILIO_AUTH_TOKEN:
        return settings.TWILIO_SID, settings.TWILIO_AUTH_TOKEN
    return None


def _send_twilio_message(channel: str, phone: str, message: str) -> dict[str, Any]:
    if not phone:
        return {"status": "skipped", "provider": "twilio", "channel": channel, "reason": "No recipient provided"}

    sender = settings.TWILIO_PHONE if channel == "sms" else settings.TWILIO_WHATSAPP_NUMBER
    auth = _twilio_auth()
    if not auth or not settings.TWILIO_SID or not sender:
        return {"status": "unavailable", "provider": "twilio", "channel": channel, "reason": "Twilio credentials or sender are not configured"}

    from_value = f"whatsapp:{sender}" if channel == "whatsapp" else sender
    to_value = f"whatsapp:{phone}" if channel == "whatsapp" else phone
    url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_SID}/Messages.json"
    try:
        response = httpx.post(
            url,
            data={"From": from_value, "To": to_value, "Body": message},
            auth=auth,
            timeout=15.0,
        )
        response.raise_for_status()
        data = response.json()
        return {
            "status": "accepted",
            "provider": "twilio",
            "channel": channel,
            "message_sid": data.get("sid"),
            "provider_status": data.get("status"),
        }
    except Exception:
        logger.exception("Twilio %s request failed", channel)
        return {"status": "failed", "provider": "twilio", "channel": channel, "reason": "Provider request failed"}


def _send_sms(phone: str, message: str) -> dict[str, Any]:
    return _send_twilio_message("sms", phone, message)


def _send_whatsapp(phone: str, message: str) -> dict[str, Any]:
    return _send_twilio_message("whatsapp", phone, message)


def _deliver_smtp(email_message: EmailMessage) -> None:
    if bool(settings.SMTP_USER) != bool(settings.SMTP_PASSWORD):
        raise ValueError("Both SMTP_USER and SMTP_PASSWORD must be configured together")

    client_factory = smtplib.SMTP_SSL if settings.SMTP_USE_SSL else smtplib.SMTP
    with client_factory(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
        if settings.SMTP_STARTTLS and not settings.SMTP_USE_SSL:
            smtp.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(email_message)


def _send_email(message: str, email: str | None) -> dict[str, Any]:
    target_email = email or settings.DEFAULT_NOTIFICATION_EMAIL
    if not target_email:
        return {"status": "skipped", "reason": "No email provided"}
    if not settings.SMTP_HOST or not settings.EMAIL_FROM:
        return {"status": "unavailable", "provider": "smtp", "channel": "email", "reason": "SMTP is not configured"}

    email_message = EmailMessage()
    email_message["Subject"] = "Agri-Menya field alert"
    email_message["From"] = settings.EMAIL_FROM
    email_message["To"] = target_email
    email_message.set_content(message)
    try:
        _deliver_smtp(email_message)
        return {"status": "sent", "provider": "smtp", "channel": "email"}
    except Exception:
        logger.exception("SMTP notification failed")
        return {"status": "failed", "provider": "smtp", "channel": "email", "reason": "Provider request failed"}


def send_notification(message: str, phone: str | None = None, email: str | None = None, channels: list[str] | None = None) -> dict[str, Any]:
    selected_channels = _normalize_channels(channels)
    recipient_phone = phone or settings.DEFAULT_NOTIFICATION_PHONE
    recipient_email = email or settings.DEFAULT_NOTIFICATION_EMAIL

    deliveries: dict[str, Any] = {}
    for channel in selected_channels:
        if channel == "sms":
            deliveries["sms"] = _send_sms(recipient_phone, message)
        elif channel == "whatsapp":
            deliveries["whatsapp"] = _send_whatsapp(recipient_phone, message)
        elif channel == "email":
            deliveries["email"] = _send_email(message, recipient_email)
        elif channel in {"voice", "ussd"}:
            deliveries[channel] = {"status": "unavailable", "provider": "unsupported", "channel": channel}

    statuses = {item.get("status") for item in deliveries.values()}
    if statuses and statuses <= {"sent"}:
        status = "sent"
    elif statuses and statuses <= {"sent", "accepted"} and "accepted" in statuses:
        status = "accepted"
    elif statuses & {"sent", "accepted"}:
        status = "partial"
    elif "failed" in statuses:
        status = "failed"
    else:
        status = "unavailable"
    return {
        "status": status,
        "channels": list(deliveries.keys()),
        "deliveries": deliveries,
        "message": message,
        "simulated": False,
        "recipient": {"phone": recipient_phone, "email": recipient_email},
    }


@router.post("/notify")
def notify(payload: NotificationRequest, _: dict = Depends(require_user)):
    return send_notification(
        message=payload.message,
        phone=payload.phone,
        email=payload.email,
        channels=payload.channels,
    )


@router.post("/contact")
def submit_contact_message(payload: ContactMessageRequest, _: dict = Depends(require_user)):
    """Deliver the contact form to the configured support inbox."""
    if not settings.SMTP_HOST or not settings.EMAIL_FROM or not settings.DEFAULT_NOTIFICATION_EMAIL:
        raise HTTPException(
            status_code=503,
            detail="Contact email is unavailable: configure SMTP_HOST, EMAIL_FROM, and DEFAULT_NOTIFICATION_EMAIL.",
        )

    email_message = EmailMessage()
    email_message["Subject"] = f"[Agri-Menya Contact] {payload.subject}"
    email_message["From"] = settings.EMAIL_FROM
    email_message["To"] = settings.DEFAULT_NOTIFICATION_EMAIL
    email_message["Reply-To"] = payload.email
    email_message.set_content(
        f"Name: {payload.name}\nEmail: {payload.email}\n\n{payload.message}"
    )

    try:
        _deliver_smtp(email_message)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Contact email could not be delivered.") from exc

    return {"status": "sent"}


@router.post("/alerts")
def create_alert(alert: AlertCreate, _: dict = Depends(require_user)):
    created = crud.create_alert(alert.model_dump())
    notification = send_notification(
        message=alert.message,
        phone=settings.DEFAULT_NOTIFICATION_PHONE,
        email=settings.DEFAULT_NOTIFICATION_EMAIL,
        channels=["sms", "whatsapp", "email"],
    )
    return {**created, "notification": notification}


@router.get("/alerts")
def get_alerts(zone_id: str | None = None):
    return crud.list_alerts(zone_id)


@router.get("/share/{plan_id}")
def get_shareable_plan(plan_id: str):
    """
    Returns a plan formatted for sharing. Extend this to generate a PDF
    or a public read-only link once that requirement is prioritized.
    """
    plans = crud.list_plans()
    plan = next((p for p in plans if p["id"] == plan_id), None)
    return plan or {"error": "Plan not found"}
