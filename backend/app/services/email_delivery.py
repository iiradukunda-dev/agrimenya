"""Shared email delivery through SMTP or the Resend HTTPS API."""
import smtplib
from email.message import EmailMessage

import httpx

from app.core.config import settings

RESEND_EMAILS_URL = "https://api.resend.com/emails"


def email_delivery_configured() -> bool:
    if not settings.EMAIL_FROM:
        return False
    if settings.EMAIL_PROVIDER == "resend":
        return bool(settings.RESEND_API_KEY)
    if settings.EMAIL_PROVIDER == "smtp":
        return bool(settings.SMTP_HOST) and bool(settings.SMTP_USER) == bool(settings.SMTP_PASSWORD)
    return False


def send_email_message(
    message: EmailMessage,
    *,
    recipient: str,
    timeout: float = 15,
) -> dict[str, str | None]:
    """Deliver one message to one recipient without exposing other recipient addresses."""
    if not email_delivery_configured():
        raise RuntimeError("Email delivery is not configured")
    if not settings.EMAIL_FROM:
        raise RuntimeError("EMAIL_FROM is not configured")

    if not recipient:
        raise ValueError("An email recipient is required")

    if settings.EMAIL_PROVIDER == "resend":
        content = message.get_body(preferencelist=("plain",)) if message.is_multipart() else message
        if content is None:
            raise ValueError("Email message must include a plain-text body")
        payload: dict[str, object] = {
            "from": settings.EMAIL_FROM,
            "to": [recipient],
            "subject": str(message.get("Subject", "")),
            "text": content.get_content(),
        }
        reply_to = message.get("Reply-To")
        if reply_to:
            payload["reply_to"] = str(reply_to)
        response = httpx.post(
            RESEND_EMAILS_URL,
            headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        try:
            message_id = response.json().get("id")
        except (ValueError, AttributeError) as exc:
            raise RuntimeError("Email provider returned an invalid response") from exc
        if not message_id:
            raise RuntimeError("Email provider did not confirm message acceptance")
        return {"provider": "resend", "message_id": str(message_id)}

    if settings.EMAIL_PROVIDER != "smtp":
        raise RuntimeError("EMAIL_PROVIDER must be either 'smtp' or 'resend'")
    if bool(settings.SMTP_USER) != bool(settings.SMTP_PASSWORD):
        raise ValueError("Both SMTP_USER and SMTP_PASSWORD must be configured together")

    if message.get("From"):
        message.replace_header("From", settings.EMAIL_FROM)
    else:
        message["From"] = settings.EMAIL_FROM
    client_factory = smtplib.SMTP_SSL if settings.SMTP_USE_SSL else smtplib.SMTP
    with client_factory(settings.SMTP_HOST, settings.SMTP_PORT, timeout=timeout) as smtp:
        if settings.SMTP_STARTTLS and not settings.SMTP_USE_SSL:
            smtp.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(message, to_addrs=[recipient])
    return {"provider": "smtp", "message_id": None}
