"""Authenticated farmer discussion board and administrator moderation."""
from collections import defaultdict, deque
import base64
import hashlib
import logging
import re
import secrets
import threading
import time
from typing import Literal
from uuid import UUID, uuid4
from datetime import date, datetime, timedelta, timezone
from io import BytesIO
from urllib.parse import urlencode, urlparse

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field, field_validator

from app.core.auth import create_token, require_admin, require_community, verify_token
from app.core.audit import audit_admin_action
from app.core.config import settings
from app.db import crud
from app.services.admin_auth import (
    hash_password, send_community_reset_email, send_community_verification_email, verify_password,
)
from app.services.email_delivery import email_delivery_configured

router = APIRouter(prefix="/community", tags=["Farmer Community"])
logger = logging.getLogger(__name__)
_login_attempts: dict[str, deque[float]] = defaultdict(deque)
_write_attempts: dict[str, deque[float]] = defaultdict(deque)
_limits_lock = threading.Lock()
_DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(32))


def _rate_limit(store: dict[str, deque[float]], key: str, maximum: int, window: int = 60) -> None:
    if settings.APP_ENV not in {"development", "test"}:
        try:
            # Rate-limit identifiers can contain email addresses; never persist those in the shared bucket table.
            prefix, _, identifier = key.partition(":")
            scope = f"community:{prefix}:{hashlib.sha256(identifier.encode('utf-8')).hexdigest()}"
            allowed = crud.consume_api_rate_limit(scope, maximum, window)
        except Exception as exc:
            logger.exception("Shared community rate limit is unavailable")
            raise HTTPException(status_code=503, detail="Community service is temporarily unavailable") from exc
        if not allowed:
            raise HTTPException(status_code=429, detail="Too many requests. Please wait and try again.")
        return
    now = time.monotonic()
    with _limits_lock:
        if key not in store and len(store) >= 4096:
            for stale_key in [candidate for candidate, values in store.items()
                              if not values or now - values[-1] > window]:
                store.pop(stale_key, None)
        attempts = store[key]
        while attempts and now - attempts[0] > window:
            attempts.popleft()
        if len(attempts) >= maximum:
            raise HTTPException(status_code=429, detail="Too many requests. Please wait and try again.")
        attempts.append(now)


def _clean_text(value: str) -> str:
    return "".join(char for char in value if char in "\n\t" or ord(char) >= 32).strip()


def _ensure_secure_sessions() -> None:
    if (len(settings.JWT_SECRET) < 32 or settings.JWT_SECRET.startswith("replace-with-") or
            settings.JWT_SECRET == "dev-secret-change-me"):
        raise HTTPException(status_code=503, detail="Configure a private JWT_SECRET of at least 32 characters")


class CommunityRegister(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    display_name: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=12, max_length=256)

    @field_validator("email")
    @classmethod
    def email_shape(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Enter a valid email address")
        return value

    @field_validator("display_name")
    @classmethod
    def display_name_clean(cls, value: str) -> str:
        value = _clean_text(value).lower()
        if not re.fullmatch(r"[a-z0-9_]{3,30}", value):
            raise ValueError("Username must be 3-30 characters using letters, numbers, and underscores")
        return value


class CommunityLogin(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)

    @field_validator("email")
    @classmethod
    def email_normalized(cls, value: str) -> str:
        return value.strip().lower()


class CommunityForgotPassword(BaseModel):
    email: str = Field(min_length=3, max_length=254)

    @field_validator("email")
    @classmethod
    def email_normalized(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Enter a valid email address")
        return value


class CommunityResetPassword(BaseModel):
    token: str = Field(min_length=20, max_length=4096)
    new_password: str = Field(min_length=12, max_length=256)


class CommunityVerifyEmail(BaseModel):
    # Signed verification JWTs exceed the password-reset token's former
    # 200-character cap; the token is still validated for signature/expiry below.
    token: str = Field(min_length=20, max_length=4096)


class CommunityResendVerification(BaseModel):
    email: str = Field(min_length=3, max_length=254)

    @field_validator("email")
    @classmethod
    def email_normalized(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Enter a valid email address")
        return value


class CommunityGoogleCode(BaseModel):
    code: str = Field(min_length=32, max_length=256)
    browser_binding: str = Field(min_length=32, max_length=128)


def _google_oauth_enabled() -> bool:
    return bool(settings.GOOGLE_OAUTH_CLIENT_ID and settings.GOOGLE_OAUTH_CLIENT_SECRET)


def _community_session(account: dict) -> dict:
    token = create_token("community", 3600, {
        "sub": str(account["id"]),
        "ver": int(account.get("session_version", 1)),
    })
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 3600,
        "account": {
            "id": str(account["id"]),
            "display_name": account["display_name"],
            "role": account["role"],
        },
    }


def _google_username(email: str) -> str:
    local_part = email.partition("@")[0].lower()
    base = re.sub(r"[^a-z0-9_]+", "_", local_part).strip("_")[:30]
    return base if len(base) >= 3 else "farmer"


def _google_frontend_redirect(
    *, code: str | None = None, error: str | None = None, keep_handoff_cookie: bool = False,
) -> RedirectResponse:
    parameters = {}
    if code:
        parameters["community_google_code"] = code
    if error:
        parameters["community_google_error"] = error
    target = settings.COMMUNITY_GOOGLE_CALLBACK_URL
    separator = "&" if "?" in target else "?"
    response = RedirectResponse(f"{target}{separator}{urlencode(parameters)}", status_code=303)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    secure = settings.APP_ENV == "production"
    for cookie_name in ("community_google_state", "community_google_verifier", "community_google_nonce"):
        response.delete_cookie(cookie_name, path="/community/auth/google/callback", secure=secure,
                               httponly=True, samesite="lax")
    if not keep_handoff_cookie:
        response.delete_cookie(
            "community_google_handoff", path="/",
            domain=settings.COMMUNITY_GOOGLE_HANDOFF_COOKIE_DOMAIN or None,
            secure=secure, httponly=True, samesite="lax",
        )
    return response


@router.get("/auth/google/status")
def community_google_status():
    return {"enabled": _google_oauth_enabled()}


@router.get("/auth/google")
def community_google_start():
    _ensure_secure_sessions()
    if not _google_oauth_enabled():
        raise HTTPException(status_code=404, detail="Google sign-in is not enabled")
    if settings.APP_ENV == "production":
        redirect = urlparse(settings.GOOGLE_OAUTH_REDIRECT_URI)
        frontend = urlparse(settings.COMMUNITY_GOOGLE_CALLBACK_URL)
        if redirect.scheme != "https" or frontend.scheme != "https":
            raise HTTPException(status_code=503, detail="Google sign-in requires HTTPS URLs in production")

    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(48)
    handoff_binding = secrets.token_urlsafe(32)
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode("ascii")).digest()
    ).decode("ascii").rstrip("=")
    authorization_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({
        "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "nonce": nonce,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "prompt": "select_account",
    })
    response = RedirectResponse(authorization_url, status_code=302)
    secure = settings.APP_ENV == "production"
    for name, value in (("community_google_state", state),
                        ("community_google_verifier", verifier),
                        ("community_google_nonce", nonce)):
        response.set_cookie(name, value, max_age=600, httponly=True, secure=secure,
                            samesite="lax", path="/community/auth/google/callback")
    response.set_cookie(
        "community_google_handoff", handoff_binding, max_age=120, httponly=True,
        secure=secure, samesite="lax", path="/",
        domain=settings.COMMUNITY_GOOGLE_HANDOFF_COOKIE_DOMAIN or None,
    )
    return response


@router.get("/auth/google/callback")
def community_google_callback(request: Request, code: str | None = None,
                              state: str | None = None, error: str | None = None):
    _ensure_secure_sessions()
    if error:
        return _google_frontend_redirect(error="cancelled")
    expected_state = request.cookies.get("community_google_state", "")
    verifier = request.cookies.get("community_google_verifier", "")
    expected_nonce = request.cookies.get("community_google_nonce", "")
    handoff_binding = request.cookies.get("community_google_handoff", "")
    if not code or not state or not expected_state or not secrets.compare_digest(state, expected_state):
        return _google_frontend_redirect(error="invalid_state")
    if not verifier or not expected_nonce or not handoff_binding:
        return _google_frontend_redirect(error="expired")

    try:
        import google.auth.transport.requests
        from google.oauth2 import id_token
        import httpx

        token_response = httpx.post("https://oauth2.googleapis.com/token", data={
            "code": code,
            "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
            "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
            "grant_type": "authorization_code",
            "code_verifier": verifier,
        }, timeout=10.0)
        token_response.raise_for_status()
        google_tokens = token_response.json()
        google_claims = id_token.verify_oauth2_token(
            google_tokens.get("id_token", ""),
            google.auth.transport.requests.Request(),
            audience=settings.GOOGLE_OAUTH_CLIENT_ID,
            clock_skew_in_seconds=5,
        )
        if not secrets.compare_digest(str(google_claims.get("nonce", "")), expected_nonce):
            return _google_frontend_redirect(error="invalid_identity")
        email = str(google_claims.get("email", "")).strip().lower()
        subject = str(google_claims.get("sub", "")).strip()
        hosted_domain = str(google_claims.get("hd", "")).strip().lower()
        verified = google_claims.get("email_verified") is True or google_claims.get("email_verified") == "true"
        if not verified or not subject or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            return _google_frontend_redirect(error="unverified_email")
        email_domain = email.rsplit("@", 1)[1]
        google_controls_email = email_domain == "gmail.com" or hosted_domain == email_domain

        account = crud.get_community_account_by_google_subject(subject)
        if account is None:
            account = crud.get_community_account_by_email(email)
            if account:
                if not account.get("is_active"):
                    return _google_frontend_redirect(error="account_unavailable")
                linked_subject = account.get("google_subject")
                if linked_subject and linked_subject != subject:
                    return _google_frontend_redirect(error="account_conflict")
                if not linked_subject:
                    if not google_controls_email:
                        return _google_frontend_redirect(error="account_link_required")
                    account = crud.link_community_google_identity(str(account["id"]), subject)
                    if not account:
                        return _google_frontend_redirect(error="account_conflict")
            else:
                base_username = _google_username(email)
                account = None
                for attempt in range(5):
                    username = base_username if attempt == 0 else f"{base_username[:22]}_{secrets.token_hex(3)}"
                    try:
                        account = crud.create_google_community_account(email, username, subject)
                        break
                    except Exception:
                        account = crud.get_community_account_by_google_subject(subject)
                        if account:
                            break
                        account = crud.get_community_account_by_email(email)
                        if account:
                            if not account.get("is_active"):
                                return _google_frontend_redirect(error="account_unavailable")
                            if not google_controls_email:
                                return _google_frontend_redirect(error="account_link_required")
                            account = crud.link_community_google_identity(str(account["id"]), subject)
                            break
                        if attempt == 4:
                            raise
                        if not crud.get_community_account_by_username(username):
                            raise
                if not account:
                    return _google_frontend_redirect(error="account_unavailable")

        if not account.get("is_active"):
            return _google_frontend_redirect(error="account_unavailable")
        oauth_code = secrets.token_urlsafe(32)
        code_hash = hashlib.sha256(oauth_code.encode("ascii")).hexdigest()
        binding_hash = hashlib.sha256(handoff_binding.encode("ascii")).hexdigest()
        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=2)).isoformat()
        crud.create_community_oauth_login_code(str(account["id"]), code_hash, binding_hash, expires_at)
        return _google_frontend_redirect(code=oauth_code, keep_handoff_cookie=True)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Google Community sign-in failed")
        return _google_frontend_redirect(error="unavailable")


@router.post("/auth/google/exchange")
def community_google_exchange(payload: CommunityGoogleCode, request: Request):
    _ensure_secure_sessions()
    ip = request.client.host if request.client else "unknown"
    _rate_limit(_login_attempts, f"google-exchange:{ip}", 10)
    code_hash = hashlib.sha256(payload.code.encode("utf-8")).hexdigest()
    try:
        binding_hash = hashlib.sha256(payload.browser_binding.encode("utf-8")).hexdigest()
        account_id = crud.consume_community_oauth_login_code(code_hash, binding_hash)
        account = crud.get_community_account_by_id(account_id) if account_id else None
    except Exception as exc:
        logger.exception("Google Community sign-in code exchange failed")
        raise HTTPException(status_code=503, detail="Google sign-in is temporarily unavailable") from exc
    if not account or not account.get("is_active"):
        raise HTTPException(status_code=400, detail="Google sign-in link is invalid, expired, or already used")
    return _community_session(account)


def _send_verification(account: dict) -> dict:
    token = create_token("community_verify", 86400, {
        "sub": str(account["id"]), "purpose": "community_email_verification",
        "ver": int(account.get("session_version", 1)),
    })
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    crud.create_community_email_verification_token(str(account["id"]), token_hash, expires_at)
    response = {"message": "Check your email for a verification link. You can request another link if it does not arrive."}
    reset_host = (urlparse(settings.COMMUNITY_PASSWORD_RESET_URL).hostname or "").casefold()
    local_development = settings.APP_ENV in {"development", "test"} and reset_host in {"localhost", "127.0.0.1"}
    email_ready = email_delivery_configured()
    if email_ready:
        try:
            send_community_verification_email(account["email"], account["display_name"], token)
            if local_development:
                response["development_email_status"] = "accepted"
        except Exception:
            if not local_development:
                raise
            logger.exception("Development email delivery failed; returning local verification link")
            response["development_email_status"] = "failed"
    elif local_development:
        response["development_email_status"] = "not_configured"
    else:
        raise RuntimeError("Community verification email is not configured")
    if local_development:
        separator = "&" if "?" in settings.COMMUNITY_PASSWORD_RESET_URL else "?"
        response["development_verification_url"] = (
            settings.COMMUNITY_PASSWORD_RESET_URL.rstrip("?") + separator
            + urlencode({"community_verify_token": token})
        )
    return response


class PostCreate(BaseModel):
    title: str = Field(min_length=3, max_length=140)
    body: str = Field(min_length=1, max_length=5000)

    @field_validator("title", "body")
    @classmethod
    def content_clean(cls, value: str) -> str:
        value = _clean_text(value)
        if not value:
            raise ValueError("Content cannot be blank")
        return value


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=1500)

    @field_validator("body")
    @classmethod
    def content_clean(cls, value: str) -> str:
        value = _clean_text(value)
        if not value:
            raise ValueError("Comment cannot be blank")
        return value


class ReportCreate(BaseModel):
    reason: str = Field(min_length=3, max_length=500)
    comment_id: UUID | None = None

    @field_validator("reason")
    @classmethod
    def reason_clean(cls, value: str) -> str:
        value = _clean_text(value)
        if len(value) < 3:
            raise ValueError("A reason of at least three characters is required")
        return value


class ModerationUpdate(BaseModel):
    target_kind: Literal["post", "comment"]
    target_id: UUID
    action: Literal["hide", "restore", "delete", "dismiss"]
    report_id: UUID | None = None
    report_action: Literal["resolved", "dismissed"] = "resolved"


class CommunityAccountStatus(BaseModel):
    is_active: bool


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: CommunityRegister, request: Request):
    _ensure_secure_sessions()
    ip = request.client.host if request.client else "unknown"
    _rate_limit(_login_attempts, f"register:{ip}", 5, 3600)
    try:
        if crud.get_community_account_by_email(payload.email):
            raise HTTPException(status_code=409, detail="An account already uses that email")
        if crud.get_community_account_by_username(payload.display_name):
            raise HTTPException(status_code=409, detail="That username is already taken")
        account = crud.create_community_account(
            payload.email, payload.display_name, hash_password(payload.password)
        )
    except HTTPException:
        raise
    except Exception as exc:
        try:
            if crud.get_community_account_by_email(payload.email):
                raise HTTPException(status_code=409, detail="An account already uses that email") from exc
            if crud.get_community_account_by_username(payload.display_name):
                raise HTTPException(status_code=409, detail="That username is already taken") from exc
        except HTTPException:
            raise
        except Exception:
            pass
        logger.exception("Community registration failed")
        raise HTTPException(status_code=503, detail="Account registration is temporarily unavailable") from exc
    try:
        return _send_verification(account)
    except Exception as exc:
        logger.exception("Community verification email could not be prepared")
        raise HTTPException(status_code=503, detail="Account created, but verification email could not be sent. Use resend verification or contact support.") from exc


@router.post("/email/verify")
def verify_community_email(payload: CommunityVerifyEmail, request: Request):
    _ensure_secure_sessions()
    ip = request.client.host if request.client else "unknown"
    _rate_limit(_login_attempts, f"verify-email:{ip}", 10)
    try:
        claims = verify_token(payload.token, expected_role="community_verify")
        if claims.get("purpose") != "community_email_verification" or not claims.get("sub"):
            raise HTTPException(status_code=400, detail="Verification link is invalid, expired, or already used")
        token_hash = hashlib.sha256(payload.token.encode("utf-8")).hexdigest()
        if not crud.verify_community_email(token_hash):
            raise HTTPException(status_code=400, detail="Verification link is invalid, expired, or already used")
    except HTTPException as exc:
        if exc.status_code == 401:
            raise HTTPException(status_code=400, detail="Verification link is invalid, expired, or already used") from exc
        raise
    except Exception as exc:
        logger.exception("Community email verification failed")
        raise HTTPException(status_code=503, detail="Email verification is temporarily unavailable") from exc
    return {"message": "Email verified. You can now sign in."}


@router.post("/email/verification/resend")
def resend_community_verification(payload: CommunityResendVerification, request: Request):
    _ensure_secure_sessions()
    ip = request.client.host if request.client else "unknown"
    _rate_limit(_login_attempts, f"resend-verification-ip:{ip}", 5, 3600)
    _rate_limit(_login_attempts, f"resend-verification-email:{payload.email}", 3, 3600)
    response = {"message": "If an unverified active account matches that email, a new verification link will be sent."}
    local = (settings.APP_ENV in {"development", "test"}
             and (urlparse(settings.COMMUNITY_PASSWORD_RESET_URL).hostname or "").casefold() in {"localhost", "127.0.0.1"})
    try:
        account = crud.get_community_account_by_email(payload.email)
        if account and account.get("is_active") and not account.get("email_verified_at"):
            response.update(_send_verification(account))
    except Exception as exc:
        logger.exception("Community verification resend failed")
        if local:
            response["development_error"] = "Could not send the link. Confirm SMTP and database configuration."
    return response


@router.post("/login")
def login(payload: CommunityLogin, request: Request):
    _ensure_secure_sessions()
    ip = request.client.host if request.client else "unknown"
    _rate_limit(_login_attempts, f"login:{ip}", 10)
    _rate_limit(_login_attempts, f"login-email:{payload.email}", 10)
    try:
        account = crud.get_community_account_by_email(payload.email)
    except Exception as exc:
        logger.exception("Community account lookup failed")
        raise HTTPException(status_code=503, detail="Community sign-in is temporarily unavailable") from exc
    password_matches = verify_password(
        payload.password, account.get("password_hash", "") if account else _DUMMY_PASSWORD_HASH
    )
    if not account or not account.get("is_active") or not password_matches:
        raise HTTPException(status_code=401, detail="Email or password is incorrect")
    if not account.get("email_verified_at"):
        raise HTTPException(status_code=403, detail="Verify your email before signing in. Request a new verification link if needed.")
    token = create_token("community", 3600, {"sub": str(account["id"]), "ver": int(account.get("session_version", 1))})
    return {"access_token": token, "token_type": "bearer", "expires_in": 3600,
            "account": {"id": str(account["id"]), "display_name": account["display_name"],
                        "role": account["role"]}}


@router.post("/password/forgot")
def community_forgot_password(payload: CommunityForgotPassword, request: Request):
    """Always return the same message so account existence cannot be queried."""
    _ensure_secure_sessions()
    ip = request.client.host if request.client else "unknown"
    _rate_limit(_login_attempts, f"community-reset-ip:{ip}", 5, 3600)
    _rate_limit(_login_attempts, f"community-reset-email:{payload.email}", 3, 3600)
    response = {"message": "If an active community account matches that email, reset instructions will be sent."}
    reset_host = (urlparse(settings.COMMUNITY_PASSWORD_RESET_URL).hostname or "").casefold()
    local_development = (
        settings.APP_ENV in {"development", "test"}
        and reset_host in {"localhost", "127.0.0.1"}
    )
    email_ready = email_delivery_configured()
    try:
        account = crud.get_community_account_by_email(payload.email)
        if account and account.get("is_active"):
            session_version = int(account.get("session_version", 1))
            token = create_token("community_reset", 1800, {
                "sub": str(account["id"]), "ver": session_version,
                "purpose": "community_password_reset",
            })
            if local_development:
                separator = "&" if "?" in settings.COMMUNITY_PASSWORD_RESET_URL else "?"
                response["development_reset_url"] = (
                    settings.COMMUNITY_PASSWORD_RESET_URL.rstrip("?") + separator
                    + urlencode({"community_reset_token": token})
                )
            if email_ready:
                send_community_reset_email(account["email"], account["display_name"], token)
                if local_development:
                    response["development_email_status"] = "accepted"
            elif not local_development:
                raise RuntimeError("Community password reset email is not configured")
            else:
                response["development_email_status"] = "not_configured"
    except Exception as exc:
        # Keep the response indistinguishable for unknown addresses and provider/database errors.
        logger.exception("Community password recovery request failed")
        if local_development:
            response["development_email_status"] = "failed"
            response["development_error"] = "Reset email could not be sent; use the local one-time link instead."
    return response


@router.post("/password/reset")
def community_reset_password(payload: CommunityResetPassword, request: Request):
    _ensure_secure_sessions()
    ip = request.client.host if request.client else "unknown"
    _rate_limit(_login_attempts, f"community-reset-complete:{ip}", 10)
    try:
        try:
            claims = verify_token(payload.token, expected_role="community_reset")
        except HTTPException as exc:
            raise HTTPException(status_code=400, detail="Reset link is invalid, expired, or already used") from exc
        account_id = claims.get("sub")
        version = claims.get("ver")
        if (claims.get("purpose") != "community_password_reset" or not account_id
                or not isinstance(version, int)):
            raise HTTPException(status_code=400, detail="Reset link is invalid, expired, or already used")
        updated = crud.reset_community_password_once(
            str(account_id), version, hash_password(payload.new_password)
        )
        if not updated:
            raise HTTPException(status_code=400, detail="Reset link is invalid, expired, or already used")
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Community password could not be reset")
        raise HTTPException(status_code=503, detail="Password reset is temporarily unavailable") from exc
    return {"message": "Password updated. Sign in with your new password."}


@router.get("/posts")
def posts(limit: int = Query(default=30, ge=1, le=50), offset: int = Query(default=0, ge=0, le=10000),
          _: dict = Depends(require_community)):
    try:
        return crud.list_community_posts(limit, offset)
    except Exception as exc:
        logger.exception("Community feed could not be loaded")
        raise HTTPException(status_code=503, detail="Community feed is temporarily unavailable") from exc


@router.get("/comments")
def comments_for_feed(post_ids: list[UUID] = Query(min_length=1, max_length=50),
                      _: dict = Depends(require_community)):
    """Fetch replies for a feed page with one bounded request."""
    try:
        return crud.list_community_comments_for_posts([str(post_id) for post_id in post_ids])
    except Exception as exc:
        logger.exception("Community feed replies could not be loaded")
        raise HTTPException(status_code=503, detail="Replies are temporarily unavailable") from exc


@router.get("/field-reports")
def community_field_reports(limit: int = Query(default=10, ge=1, le=20),
                           _: dict = Depends(require_community)):
    """Recent farmer observations, explicitly separate from official statistics."""
    try:
        reports = crud.list_community_field_reports(limit)
        storage = crud.get_supabase().storage.from_(settings.COMMUNITY_PHOTO_BUCKET)
        for report in reports:
            path = report.pop("photo_path", None)
            report["photo_url"] = None
            if path:
                try:
                    signed = storage.create_signed_url(path, 900)
                    report["photo_url"] = signed.get("signedURL") or signed.get("signedUrl")
                except Exception:
                    logger.info("Could not sign field report photo URL")
        return reports
    except Exception as exc:
        logger.exception("Field observations could not be loaded")
        raise HTTPException(status_code=503, detail="Field observations are temporarily unavailable") from exc


@router.post("/field-reports", status_code=status.HTTP_201_CREATED)
async def create_community_field_report(
    zone_id: UUID = Form(...), crop: str = Form(..., min_length=1, max_length=50),
    observed_on: date = Form(...), symptoms: str = Form(default="", max_length=500),
    notes: str = Form(default="", max_length=1000),
    photo: UploadFile | None = File(default=None),
    account: dict = Depends(require_community),
):
    _rate_limit(_write_attempts, f"field-report:{account['account_id']}", 10, 3600)
    if observed_on > date.today():
        raise HTTPException(status_code=422, detail="Observation date cannot be in the future")
    zone = crud.get_zone(zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Choose a valid district")
    crop = _clean_text(crop)
    if not crop:
        raise HTTPException(status_code=422, detail="Crop is required")
    photo_path = None
    if photo is not None and photo.filename:
        try:
            from PIL import Image, UnidentifiedImageError
        except ImportError as exc:
            raise HTTPException(status_code=503, detail="Photo uploads require the Pillow backend dependency") from exc
        raw = await photo.read(5 * 1024 * 1024 + 1)
        if len(raw) > 5 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Photo must be 5 MB or smaller")
        try:
            image = Image.open(BytesIO(raw))
            image.verify()
            image = Image.open(BytesIO(raw)).convert("RGB")
            image.thumbnail((1400, 1400))
            output = BytesIO()
            image.save(output, format="JPEG", quality=78, optimize=True)
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="Upload a valid image file") from exc
        if output.tell() > 5 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Compressed photo must be 5 MB or smaller")
        photo_path = f"{account['account_id']}/{uuid4()}.jpg"
        try:
            crud.get_supabase().storage.from_(settings.COMMUNITY_PHOTO_BUCKET).upload(
                photo_path, output.getvalue(),
                file_options={"content-type": "image/jpeg", "upsert": "false"},
            )
        except Exception as exc:
            logger.exception("Field report photo upload failed")
            raise HTTPException(status_code=503, detail="Photo storage is unavailable; try again without a photo") from exc
    if not any((symptoms.strip(), notes.strip(), photo_path)):
        raise HTTPException(status_code=422, detail="Add a short observation or attach a photo")
    try:
        return crud.create_field_report({
            "zone_id": str(zone_id), "district": zone.get("district", ""), "crop": crop,
            "observed_on": observed_on.isoformat(), "symptoms": _clean_text(symptoms),
            "notes": _clean_text(notes), "reporter_id": account["account_id"], "photo_path": photo_path,
        })
    except Exception as exc:
        if photo_path:
            try:
                crud.get_supabase().storage.from_(settings.COMMUNITY_PHOTO_BUCKET).remove([photo_path])
            except Exception:
                logger.warning("Could not remove orphaned field report photo")
        logger.exception("Field observation could not be saved")
        raise HTTPException(status_code=503, detail="Field observation could not be saved") from exc


@router.delete("/field-reports/{report_id}")
def delete_own_field_report(report_id: UUID, account: dict = Depends(require_community)):
    try:
        deleted = crud.delete_community_field_report(str(report_id), account["account_id"])
        if not deleted:
            raise HTTPException(status_code=404, detail="Your field observation was not found")
        if deleted.get("photo_path"):
            try:
                crud.get_supabase().storage.from_(settings.COMMUNITY_PHOTO_BUCKET).remove([deleted["photo_path"]])
            except Exception:
                logger.warning("Field observation deleted but its photo could not be removed")
        return {"status": "deleted", "message": "Your field observation was deleted."}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Community field observation deletion failed")
        raise HTTPException(status_code=503, detail="Field observation could not be deleted") from exc


@router.post("/posts", status_code=status.HTTP_201_CREATED)
def create_post(payload: PostCreate, account: dict = Depends(require_community)):
    _rate_limit(_write_attempts, f"post:{account['account_id']}", 5, 3600)
    try:
        return crud.create_community_post(account["account_id"], payload.title, payload.body)
    except Exception as exc:
        logger.exception("Community post could not be created")
        raise HTTPException(status_code=503, detail="Post could not be saved") from exc


@router.get("/posts/{post_id}/comments")
def comments(post_id: UUID, _: dict = Depends(require_community)):
    try:
        post = crud.get_community_post(str(post_id))
        if not post or post.get("status") != "published":
            raise HTTPException(status_code=404, detail="Post not found")
        return crud.list_community_comments(str(post_id))
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Community comments could not be loaded")
        raise HTTPException(status_code=503, detail="Replies are temporarily unavailable") from exc


@router.post("/posts/{post_id}/comments", status_code=status.HTTP_201_CREATED)
def create_comment(post_id: UUID, payload: CommentCreate,
                   account: dict = Depends(require_community)):
    _rate_limit(_write_attempts, f"comment:{account['account_id']}", 30, 3600)
    try:
        post = crud.get_community_post(str(post_id))
        if not post or post.get("status") != "published":
            raise HTTPException(status_code=404, detail="Post not found")
        return crud.create_community_comment(str(post_id), account["account_id"], payload.body)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Community comment could not be created")
        raise HTTPException(status_code=503, detail="Comment could not be saved") from exc


@router.delete("/posts/{post_id}")
def delete_own_post(post_id: UUID, account: dict = Depends(require_community)):
    """Authors can remove their own post; status is retained for moderation history."""
    try:
        post = crud.get_community_post(str(post_id))
        if not post or post.get("status") != "published":
            raise HTTPException(status_code=404, detail="Post not found")
        if str(post.get("author_id")) != account["account_id"]:
            raise HTTPException(status_code=403, detail="You can delete only your own posts")
        if not crud.moderate_community_content(
            target_kind="post", target_id=str(post_id), status="deleted"
        ):
            raise HTTPException(status_code=404, detail="Post not found")
        return {"status": "deleted", "message": "Your post was deleted."}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Community author deletion failed")
        raise HTTPException(status_code=503, detail="Post could not be deleted") from exc


@router.post("/posts/{post_id}/report", status_code=status.HTTP_201_CREATED)
def report_post(post_id: UUID, payload: ReportCreate, account: dict = Depends(require_community)):
    _rate_limit(_write_attempts, f"report:{account['account_id']}", 10, 86400)
    post = crud.get_community_post(str(post_id))
    if not post or post.get("status") != "published":
        raise HTTPException(status_code=404, detail="Post not found")
    if str(post.get("author_id")) == account["account_id"]:
        raise HTTPException(status_code=400, detail="You cannot report your own post")
    comment_id = str(payload.comment_id) if payload.comment_id else None
    if comment_id:
        comment = crud.get_community_comment(comment_id)
        if (not comment or comment.get("post_id") != str(post_id) or
                comment.get("status") != "published"):
            raise HTTPException(status_code=404, detail="Comment not found on this post")
        if str(comment.get("author_id")) == account["account_id"]:
            raise HTTPException(status_code=400, detail="You cannot report your own comment")
    try:
        return crud.create_community_report(account["account_id"], reason=payload.reason,
                                            post_id=None if comment_id else str(post_id), comment_id=comment_id)
    except Exception as exc:
        logger.exception("Community report could not be saved")
        raise HTTPException(status_code=409, detail="This content may already have been reported") from exc


@router.get("/moderation/reports")
def moderation_reports(_: dict = Depends(require_admin)):
    return crud.list_community_reports()


@router.get("/moderation/posts")
def moderation_posts(_: dict = Depends(require_admin)):
    return crud.list_community_posts_for_moderation()


@router.get("/moderation/field-reports")
def moderation_field_reports(_: dict = Depends(require_admin)):
    reports = crud.list_community_field_reports(50)
    storage = crud.get_supabase().storage.from_(settings.COMMUNITY_PHOTO_BUCKET)
    for report in reports:
        path = report.pop("photo_path", None)
        report["photo_url"] = None
        if path:
            try:
                signed = storage.create_signed_url(path, 900)
                report["photo_url"] = signed.get("signedURL") or signed.get("signedUrl")
            except Exception:
                logger.info("Could not sign field report photo URL for moderation")
    return reports


@router.delete("/moderation/field-reports/{report_id}")
def delete_moderated_field_report(report_id: UUID, request: Request,
                                  admin: dict = Depends(require_admin)):
    try:
        deleted = crud.delete_community_field_report(str(report_id))
        if not deleted:
            raise HTTPException(status_code=404, detail="Field observation not found")
        if deleted.get("photo_path"):
            try:
                crud.get_supabase().storage.from_(settings.COMMUNITY_PHOTO_BUCKET).remove([deleted["photo_path"]])
            except Exception:
                logger.warning("Field observation deleted but its photo could not be removed")
        audit_admin_action("community_field_report_delete", "field_reports", {
            "actor_id": admin.get("account_id"), "report_id": str(report_id),
        }, request=request)
        return {"status": "deleted", "message": "Field observation deleted."}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Administrator field observation deletion failed")
        raise HTTPException(status_code=503, detail="Field observation could not be deleted") from exc


@router.get("/moderation/accounts")
def moderation_accounts(_: dict = Depends(require_admin)):
    return crud.list_community_accounts()


@router.patch("/moderation/accounts/{account_id}/status")
def moderation_account_status(account_id: UUID, payload: CommunityAccountStatus,
                              request: Request, admin: dict = Depends(require_admin)):
    if not crud.set_community_account_active(str(account_id), payload.is_active):
        raise HTTPException(status_code=404, detail="Community account not found")
    audit_admin_action("community_account_status", "community_accounts", {
        "actor_id": admin.get("account_id"), "account_id": str(account_id),
        "is_active": payload.is_active,
    }, request=request)
    return {"message": "Community account access updated; existing sessions were revoked."}


@router.patch("/moderation")
def moderate(payload: ModerationUpdate, request: Request,
             admin: dict = Depends(require_admin)):
    if payload.action == "dismiss":
        if not payload.report_id:
            raise HTTPException(status_code=400, detail="A report is required to dismiss")
        status_value = "unchanged"
    else:
        status_value = {"hide": "hidden", "restore": "published", "delete": "deleted"}[payload.action]
        if not crud.moderate_community_content(target_kind=payload.target_kind,
                                               target_id=str(payload.target_id), status=status_value):
            raise HTTPException(status_code=404, detail="Content not found")
    if payload.report_id:
        if not crud.resolve_community_report(str(payload.report_id), admin.get("account_id"), payload.report_action):
            raise HTTPException(status_code=404, detail="Open report not found")
    audit_admin_action("community_moderation", "community_content", {
        "actor_id": admin.get("account_id"), "target_kind": payload.target_kind,
        "target_id": str(payload.target_id), "action": payload.action,
    }, request=request)
    return {"status": status_value, "message": "Community moderation saved"}
