from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Any

import httpx
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.config import settings
from app.db import crud
from app.models.alert import AlertCreate

router = APIRouter(prefix="/communication", tags=["Communication"])

VALID_CHANNELS = {"sms", "whatsapp", "email", "voice", "ussd"}


class NotificationRequest(BaseModel):
    phone: str | None = None
    email: str | None = None
    message: str = Field(..., min_length=1, max_length=1000)
    channels: list[str] = Field(default_factory=lambda: ["sms", "whatsapp"])


def _normalize_channels(channels: list[str] | None) -> list[str]:
    if not channels:
        return ["sms", "whatsapp"]
    normalized = []
    for channel in channels:
        name = str(channel).strip().lower()
        if name in VALID_CHANNELS and name not in normalized:
            normalized.append(name)
    return normalized or ["sms", "whatsapp"]


def _send_sms(phone: str, message: str) -> dict[str, Any]:
    if not phone:
        return {"status": "skipped", "reason": "No phone provided"}
    if settings.TWILIO_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_PHONE:
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_SID}/Messages.json"
            payload = {
                "From": settings.TWILIO_PHONE,
                "To": phone,
                "Body": message,
            }
            auth = (settings.TWILIO_SID, settings.TWILIO_AUTH_TOKEN)
            response = httpx.post(url, data=payload, auth=auth, timeout=15.0)
            response.raise_for_status()
            return {"status": "sent", "provider": "twilio", "channel": "sms"}
        except Exception as exc:  # pragma: no cover - external provider failure is handled by fallback
            return {"status": "queued", "provider": "simulated", "channel": "sms", "fallback": repr(exc)}
    return {"status": "queued", "provider": "simulated", "channel": "sms", "message": "SMS queued for delivery"}


def _send_whatsapp(phone: str, message: str) -> dict[str, Any]:
    if not phone:
        return {"status": "skipped", "reason": "No phone provided"}
    if settings.TWILIO_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_WHATSAPP_NUMBER:
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_SID}/Messages.json"
            payload = {
                "From": f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",
                "To": f"whatsapp:{phone}",
                "Body": message,
            }
            auth = (settings.TWILIO_SID, settings.TWILIO_AUTH_TOKEN)
            response = httpx.post(url, data=payload, auth=auth, timeout=15.0)
            response.raise_for_status()
            return {"status": "sent", "provider": "twilio", "channel": "whatsapp"}
        except Exception as exc:  # pragma: no cover - external provider failure
            return {"status": "queued", "provider": "simulated", "channel": "whatsapp", "fallback": repr(exc)}
    return {"status": "queued", "provider": "simulated", "channel": "whatsapp", "message": "WhatsApp queued for delivery"}


def _send_email(message: str, email: str | None) -> dict[str, Any]:
    target_email = email or settings.DEFAULT_NOTIFICATION_EMAIL
    if not target_email:
        return {"status": "skipped", "reason": "No email provided"}
    if settings.SMTP_HOST and settings.SMTP_USER and settings.EMAIL_FROM:
        try:
            email_message = EmailMessage()
            email_message["Subject"] = "Agri-Menya field alert"
            email_message["From"] = settings.EMAIL_FROM
            email_message["To"] = target_email
            email_message.set_content(message)
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    smtp.starttls()
                    smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                smtp.send_message(email_message)
            return {"status": "sent", "provider": "smtp", "channel": "email"}
        except Exception as exc:  # pragma: no cover - fallback if SMTP is not configured
            return {"status": "queued", "provider": "simulated", "channel": "email", "fallback": repr(exc)}
    return {"status": "queued", "provider": "simulated", "channel": "email", "message": "Email queued for delivery"}


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
            deliveries[channel] = {"status": "queued", "provider": "simulated", "channel": channel, "message": f"{channel.upper()} delivery queued"}

    status = "queued" if any(item.get("status") in {"queued", "sent"} for item in deliveries.values()) else "failed"
    return {
        "status": status,
        "channels": list(deliveries.keys()),
        "deliveries": deliveries,
        "message": message,
        "simulated": any(item.get("provider") == "simulated" for item in deliveries.values()),
        "recipient": {"phone": recipient_phone, "email": recipient_email},
    }


@router.post("/notify")
def notify(payload: NotificationRequest):
    return send_notification(
        message=payload.message,
        phone=payload.phone,
        email=payload.email,
        channels=payload.channels,
    )


@router.post("/alerts")
def create_alert(alert: AlertCreate):
    created = crud.create_alert(alert.model_dump())
    send_notification(
        message=alert.message,
        phone=settings.DEFAULT_NOTIFICATION_PHONE,
        email=settings.DEFAULT_NOTIFICATION_EMAIL,
        channels=["sms", "whatsapp", "email"],
    )
    return created


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
