from __future__ import annotations

import json
import smtplib
import logging
import threading
import time
from collections import deque
from email.message import EmailMessage
from typing import Any
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from app.core.config import settings
from app.core.auth import require_user
from app.db import crud
from app.models.alert import AlertCreate

router = APIRouter(prefix="/communication", tags=["Communication"])
logger = logging.getLogger(__name__)

VALID_CHANNELS = {"sms", "whatsapp", "email", "voice", "ussd"}
_request_times: dict[str, deque[float]] = {}
_request_lock = threading.Lock()
_REQUESTS_PER_MINUTE = 8


def _limit_client_requests(request: Request) -> None:
    client = request.client.host if request.client else "unknown"
    now = time.monotonic()
    with _request_lock:
        history = _request_times.setdefault(client, deque())
        while history and now - history[0] >= 60:
            history.popleft()
        if len(history) >= _REQUESTS_PER_MINUTE:
            raise HTTPException(status_code=429, detail="Notification rate limit exceeded")
        history.append(now)
        if len(_request_times) > 4096:
            expired = [key for key, values in _request_times.items() if not values or now - values[-1] >= 60]
            for key in expired:
                _request_times.pop(key, None)


class NotificationRequest(BaseModel):
    phone: str | None = Field(default=None, max_length=16, pattern=r"^\+[1-9]\d{7,14}$")
    email: str | None = Field(default=None, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    message: str = Field(..., min_length=1, max_length=1000)
    channels: list[str] = Field(default_factory=lambda: ["sms", "whatsapp"], max_length=3)

    @field_validator("channels")
    @classmethod
    def validate_channels(cls, channels: list[str]) -> list[str]:
        normalized = [channel.strip().lower() for channel in channels]
        if any(channel not in VALID_CHANNELS for channel in normalized):
            raise ValueError("Unsupported notification channel")
        if len(set(normalized)) != len(normalized):
            raise ValueError("Notification channels must be unique")
        return normalized


class ContactMessageRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    email: str = Field(..., min_length=3, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    subject: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=5000)


class PlanShareRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


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
    return {
        "status": "unavailable",
        "provider": "whatsapp_cloud_api",
        "channel": "whatsapp",
        "reason": "WhatsApp delivery requires an opted-in contact and the approved alert dispatch flow",
    }


@router.get("/whatsapp-status")
def whatsapp_status(_: dict = Depends(require_user)) -> dict[str, Any]:
    """Expose WhatsApp readiness without disclosing provider credentials."""
    sender_configured = bool(settings.WHATSAPP_PHONE_NUMBER_ID)
    credentials_configured = bool(settings.WHATSAPP_ACCESS_TOKEN)
    webhook_configured = bool(settings.WHATSAPP_APP_SECRET and settings.WHATSAPP_VERIFY_TOKEN)
    live_ready = bool(settings.WHATSAPP_GRAPH_VERSION and sender_configured and credentials_configured and webhook_configured)
    return {
        "ready": settings.WHATSAPP_MODE == "mock" or live_ready,
        "mode": settings.WHATSAPP_MODE,
        "provider": "meta_cloud_api",
        "business_account_configured": bool(settings.WHATSAPP_BUSINESS_ACCOUNT_ID),
        "credentials_configured": credentials_configured,
        "sender_configured": sender_configured,
        "webhook_configured": webhook_configured,
    }


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


def _send_email(message: str, email: str | None, subject: str = "Agri-Menya field alert") -> dict[str, Any]:
    target_email = email or settings.DEFAULT_NOTIFICATION_EMAIL
    if not target_email:
        return {"status": "skipped", "reason": "No email provided"}
    if not settings.SMTP_HOST or not settings.EMAIL_FROM:
        return {"status": "unavailable", "provider": "smtp", "channel": "email", "reason": "SMTP is not configured"}

    email_message = EmailMessage()
    email_message["Subject"] = subject
    email_message["From"] = settings.EMAIL_FROM
    email_message["To"] = target_email
    email_message.set_content(message)
    try:
        _deliver_smtp(email_message)
        return {"status": "sent", "provider": "smtp", "channel": "email"}
    except smtplib.SMTPAuthenticationError as exc:
        logger.exception("SMTP notification failed")
        return {
            "status": "failed", "provider": "smtp", "channel": "email",
            "reason": f"SMTP authentication was rejected (code {exc.smtp_code}). Check the SMTP username and app password.",
        }
    except smtplib.SMTPRecipientsRefused:
        logger.exception("SMTP notification recipient was refused")
        return {
            "status": "failed", "provider": "smtp", "channel": "email",
            "reason": "SMTP rejected the recipient address. Check the email address and sender permissions.",
        }
    except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected, TimeoutError, OSError) as exc:
        logger.exception("SMTP connection failed")
        return {
            "status": "failed", "provider": "smtp", "channel": "email",
            "reason": f"Could not connect to the SMTP service ({type(exc).__name__}). Check host, port, TLS, and outbound access.",
        }
    except Exception as exc:
        logger.exception("SMTP notification failed")
        return {
            "status": "failed", "provider": "smtp", "channel": "email",
            "reason": f"SMTP send failed ({type(exc).__name__}). Check backend logs for details.",
        }


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
    }


@router.post("/notify")
def notify(payload: NotificationRequest, request: Request, _: dict = Depends(require_user)):
    _limit_client_requests(request)
    return send_notification(
        message=payload.message,
        phone=payload.phone,
        email=payload.email,
        channels=payload.channels,
    )


@router.get("/email-status")
def email_status(_: dict = Depends(require_user)) -> dict[str, Any]:
    """Expose safe SMTP readiness flags for the authenticated communication UI."""
    auth_pair_valid = bool(settings.SMTP_USER) == bool(settings.SMTP_PASSWORD)
    smtp_configured = bool(settings.SMTP_HOST and settings.EMAIL_FROM and auth_pair_valid)
    if settings.SMTP_USE_SSL:
        transport = "implicit TLS"
    elif settings.SMTP_STARTTLS:
        transport = "STARTTLS"
    else:
        transport = "unencrypted"
    return {
        "ready": smtp_configured,
        "smtp_configured": bool(settings.SMTP_HOST),
        "sender_configured": bool(settings.EMAIL_FROM),
        "authentication_configured": bool(settings.SMTP_USER and settings.SMTP_PASSWORD),
        "authentication_pair_valid": auth_pair_valid,
        "default_recipient_configured": bool(settings.DEFAULT_NOTIFICATION_EMAIL),
        "port": settings.SMTP_PORT,
        "transport": transport,
    }


@router.post("/contact")
def submit_contact_message(payload: ContactMessageRequest, request: Request, _: dict = Depends(require_user)):
    """Deliver the contact form to the configured support inbox."""
    _limit_client_requests(request)
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
def create_alert(alert: AlertCreate, request: Request, _: dict = Depends(require_user)):
    _limit_client_requests(request)
    # Pydantic keeps zone_id as a UUID in Python mode, which the Supabase
    # client's JSON encoder cannot serialize. JSON mode converts it to text.
    created = crud.create_alert(alert.model_dump(mode="json"))
    notification = send_notification(
        message=alert.message,
        phone=settings.DEFAULT_NOTIFICATION_PHONE,
        email=settings.DEFAULT_NOTIFICATION_EMAIL,
        channels=["sms", "whatsapp", "email"],
    )
    return {**created, "notification": notification}


@router.get("/alerts")
def get_alerts(zone_id: str | None = None, _: dict = Depends(require_user)):
    return crud.list_alerts(zone_id)


@router.get("/share/{plan_id}")
def get_shareable_plan(plan_id: UUID, _: dict = Depends(require_user)):
    """
    Returns a plan formatted for sharing. Extend this to generate a PDF
    or a public read-only link once that requirement is prioritized.
    """
    plan = crud.get_plan(plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


def _format_plan_email(plan: dict[str, Any], zone: dict[str, Any] | None) -> str:
    def decode(value: Any, fallback: Any) -> Any:
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return fallback
        return value if value is not None else fallback

    title = str(plan.get("title") or "Saved plan")
    location = " / ".join(
        str(value) for value in (
            (zone or {}).get("district"), (zone or {}).get("sector"), (zone or {}).get("cell")
        ) if value
    ) or "Location not recorded"
    lines = [f"Agri-Menya shared plan: {title}", f"Zone: {location}", "", "ROADMAP"]
    roadmap = decode(plan.get("roadmap_json"), [])
    if isinstance(roadmap, list) and roadmap:
        for index, step in enumerate(roadmap, start=1):
            if not isinstance(step, dict):
                continue
            number = step.get("step_number") or index
            timeframe = step.get("timeframe") or "Time not set"
            lines.append(f"{number}. {step.get('title') or f'Step {number}'} ({timeframe})")
            description = str(step.get("description") or "").strip()
            if description:
                lines.append(f"   {description}")
    else:
        lines.append("No roadmap steps were saved.")

    resources = decode(plan.get("resources_json"), {})
    if isinstance(resources, dict) and resources:
        lines.extend(["", "RESOURCE ESTIMATE"])
        for key, label, unit in (
            ("area_ha", "Area", "ha"),
            ("dap_kg", "DAP", "kg"),
            ("urea_kg", "Urea", "kg"),
            ("seeds_kg", "Seeds", "kg"),
            ("fertilizer_kg", "Total fertilizer", "kg"),
            ("irrigation_liters", "Irrigation", "L"),
            ("estimated_cost_rwf", "Entered-resource cost", "RWF"),
        ):
            value = resources.get(key)
            quantities = resources.get("quantities") or {}
            if key in quantities:
                value = quantities[key]
            if value is not None:
                try:
                    lines.append(f"{label}: {float(value):,.2f} {unit}")
                except (TypeError, ValueError):
                    lines.append(f"{label}: {value} {unit}")
        if resources.get("basis"):
            lines.extend(["", str(resources["basis"])])
    lines.extend(["", "Shared from Agri-Menya."])
    return "\n".join(lines)


@router.post("/share/{plan_id}/send")
def send_shareable_plan(plan_id: UUID, payload: PlanShareRequest, request: Request, _: dict = Depends(require_user)):
    _limit_client_requests(request)
    plan = crud.get_plan(plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    if not settings.SMTP_HOST or not settings.EMAIL_FROM:
        raise HTTPException(status_code=503, detail="Email delivery is not configured on the backend")

    zone_id = plan.get("zone_id")
    zone = crud.get_zone(UUID(str(zone_id))) if zone_id else None
    title = str(plan.get("title") or "Saved plan")
    delivery = _send_email(
        _format_plan_email(plan, zone),
        payload.email,
        subject=f"Agri-Menya plan: {title[:120]}",
    )
    if delivery.get("status") != "sent":
        raise HTTPException(status_code=502, detail=delivery.get("reason", "Plan email could not be delivered"))
    return {"status": "sent", "channel": "email", "recipient": payload.email, "plan_id": str(plan_id)}
