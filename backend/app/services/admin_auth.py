"""Password and email helpers for named administrator accounts."""
import hashlib
import hmac
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from urllib.parse import urlparse

from app.core.config import settings


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=64)
    return f"scrypt$16384$8$1${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, n, r, p, salt_hex, expected_hex = encoded.split("$", 5)
        if algorithm != "scrypt":
            return False
        actual = hashlib.scrypt(
            password.encode("utf-8"), salt=bytes.fromhex(salt_hex),
            n=int(n), r=int(r), p=int(p), dklen=len(bytes.fromhex(expected_hex)),
        )
        return hmac.compare_digest(actual.hex(), expected_hex)
    except (ValueError, TypeError):
        return False


def new_reset_token() -> tuple[str, str, str]:
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("ascii")).hexdigest()
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
    return token, token_hash, expires_at


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def send_reset_email(email: str, display_name: str, token: str) -> None:
    reset_url = urlparse(settings.ADMIN_PASSWORD_RESET_URL)
    local_development_url = (
        settings.APP_ENV in {"development", "test"}
        and reset_url.scheme == "http"
        and reset_url.hostname in {"localhost", "127.0.0.1"}
    )
    secure_url = reset_url.scheme == "https" and bool(reset_url.netloc)
    if (not settings.SMTP_HOST or not settings.EMAIL_FROM or
            not (secure_url or local_development_url)):
        raise RuntimeError("Administrator password recovery email is not configured")
    if bool(settings.SMTP_USER) != bool(settings.SMTP_PASSWORD):
        raise RuntimeError("SMTP_USER and SMTP_PASSWORD must be configured together")
    url = settings.ADMIN_PASSWORD_RESET_URL.rstrip("/") + "?reset_token=" + token
    message = EmailMessage()
    message["Subject"] = "Reset your Agri-Menya administrator password"
    message["From"] = settings.EMAIL_FROM
    message["To"] = email
    message.set_content(
        f"Hello {display_name},\n\nUse this one-time link to reset your Agri-Menya administrator password. "
        f"It expires in 30 minutes and can only be used once.\n\n{url}\n\n"
        "If you did not request this change, you can ignore this message."
    )
    client_factory = smtplib.SMTP_SSL if settings.SMTP_USE_SSL else smtplib.SMTP
    with client_factory(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
        if settings.SMTP_STARTTLS and not settings.SMTP_USE_SSL:
            smtp.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(message)


def send_community_reset_email(email: str, display_name: str, token: str) -> None:
    """Send a one-time community password link through the configured SMTP provider."""
    reset_url = urlparse(settings.COMMUNITY_PASSWORD_RESET_URL)
    local_development_url = (
        settings.APP_ENV in {"development", "test"}
        and reset_url.scheme == "http"
        and reset_url.hostname in {"localhost", "127.0.0.1"}
    )
    secure_url = reset_url.scheme == "https" and bool(reset_url.netloc)
    if not settings.SMTP_HOST or not settings.EMAIL_FROM or not (secure_url or local_development_url):
        raise RuntimeError("Community password recovery email is not configured")
    if bool(settings.SMTP_USER) != bool(settings.SMTP_PASSWORD):
        raise RuntimeError("SMTP_USER and SMTP_PASSWORD must be configured together")

    separator = "&" if "?" in settings.COMMUNITY_PASSWORD_RESET_URL else "?"
    url = settings.COMMUNITY_PASSWORD_RESET_URL.rstrip("?") + separator + "community_reset_token=" + token
    message = EmailMessage()
    message["Subject"] = "Reset your Agri-Menya community password"
    message["From"] = settings.EMAIL_FROM
    message["To"] = email
    message.set_content(
        f"Hello {display_name},\n\nUse this one-time link to reset your Agri-Menya community password. "
        f"It expires in 30 minutes and can only be used once.\n\n{url}\n\n"
        "If you did not request this change, you can ignore this message."
    )
    client_factory = smtplib.SMTP_SSL if settings.SMTP_USE_SSL else smtplib.SMTP
    with client_factory(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
        if settings.SMTP_STARTTLS and not settings.SMTP_USE_SSL:
            smtp.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(message)
