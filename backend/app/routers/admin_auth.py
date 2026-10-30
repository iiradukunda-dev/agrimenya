"""Named administrator sign-in, invitations, and password recovery."""
from collections import defaultdict, deque
import logging
import re
import secrets
import threading
import time
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from app.core.auth import create_token, require_role
from app.core.audit import audit_admin_action
from app.core.config import settings
from app.db import crud
from app.services.email_delivery import email_delivery_configured
from app.services.admin_auth import (
    hash_password, hash_reset_token, new_reset_token, send_reset_email, verify_password,
)

router = APIRouter(prefix="/auth/admin", tags=["Administrator Authentication"])
logger = logging.getLogger(__name__)
_attempts: dict[str, deque[float]] = defaultdict(deque)
_attempts_lock = threading.Lock()
_DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(32))


def _limit(request: Request) -> None:
    key = request.client.host if request.client else "unknown"
    now = time.monotonic()
    with _attempts_lock:
        if key not in _attempts and len(_attempts) >= 4096:
            for stale_key in [
                candidate for candidate, values in _attempts.items()
                if not values or now - values[-1] > 60
            ]:
                _attempts.pop(stale_key, None)
        attempts = _attempts[key]
        while attempts and now - attempts[0] > 60:
            attempts.popleft()
        if len(attempts) >= 10:
            raise HTTPException(status_code=429, detail="Too many authentication requests. Try again in one minute.")
        attempts.append(now)


class AdminLogin(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Enter a valid email address")
        return value


class ForgotPassword(BaseModel):
    email: str = Field(min_length=3, max_length=254)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return AdminLogin.validate_email(value)


class ResetPassword(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    new_password: str = Field(min_length=12, max_length=256)


class CreateAdmin(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    display_name: str = Field(min_length=1, max_length=120)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return AdminLogin.validate_email(value)

    @field_validator("display_name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name is required")
        return value


class AdminAccountStatus(BaseModel):
    is_active: bool


def _issue_reset(account: dict[str, Any]) -> None:
    token, token_hash, expires_at = new_reset_token()
    crud.create_admin_password_reset_token(str(account["id"]), token_hash, expires_at)
    try:
        send_reset_email(account["email"], account["display_name"], token)
    except Exception:
        logger.exception("Administrator recovery email delivery failed")
        raise HTTPException(status_code=503, detail="Password recovery email could not be sent. Contact the system operator.")


@router.post("/login")
def login(payload: AdminLogin, request: Request) -> dict[str, Any]:
    _limit(request)
    try:
        account = crud.get_admin_account_by_email(str(payload.email).lower())
    except Exception as exc:
        logger.exception("Administrator account lookup failed")
        raise HTTPException(status_code=503, detail="Administrator sign-in is temporarily unavailable") from exc
    password_matches = verify_password(
        payload.password,
        account.get("password_hash", "") if account else _DUMMY_PASSWORD_HASH,
    )
    if not account or not account.get("is_active") or not password_matches:
        raise HTTPException(status_code=401, detail="Email or password is incorrect")
    try:
        crud.record_admin_login(str(account["id"]))
    except Exception:
        logger.exception("Could not record administrator sign-in")
    token = create_token("admin", expires_in_seconds=1800, claims={
        "sub": str(account["id"]), "ver": int(account.get("session_version", 1)),
    })
    return {
        "access_token": token, "token_type": "bearer", "expires_in": 1800,
        "admin": {"id": str(account["id"]), "email": account["email"], "display_name": account["display_name"]},
    }


@router.post("/password/forgot")
def forgot_password(payload: ForgotPassword, request: Request) -> dict[str, str]:
    _limit(request)
    try:
        account = crud.get_admin_account_by_email(str(payload.email).lower())
        if account and account.get("is_active"):
            _issue_reset(account)
    except HTTPException as exc:
        # Do not reveal whether the address belongs to an account or whether email is configured.
        if exc.status_code != 503:
            raise
        logger.info("Recovery could not be delivered; returning generic response")
    except Exception:
        logger.exception("Administrator password recovery request failed")
    return {"message": "If an active administrator account matches that email, password reset instructions will be sent."}


@router.post("/password/reset")
def reset_password(payload: ResetPassword, request: Request) -> dict[str, str]:
    _limit(request)
    token_hash = hash_reset_token(payload.token)
    try:
        consumed = crud.consume_admin_password_reset_token(token_hash)
        if not consumed:
            raise HTTPException(status_code=400, detail="Reset link is invalid, expired, or already used")
        account = crud.get_admin_account_by_id(str(consumed["admin_id"]))
        if not account or not account.get("is_active"):
            raise HTTPException(status_code=400, detail="Reset link is invalid, expired, or already used")
        crud.update_admin_password(str(account["id"]), hash_password(payload.new_password))
        crud.invalidate_admin_password_reset_tokens(str(account["id"]))
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Administrator password could not be reset")
        raise HTTPException(status_code=503, detail="Password reset is temporarily unavailable") from exc
    return {"message": "Password updated. Sign in again with your new password."}


@router.post("/accounts", status_code=201)
def create_account(
    payload: CreateAdmin,
    request: Request,
    principal: dict = Depends(require_role("admin")),
) -> dict[str, str]:
    email = str(payload.email).lower()
    if crud.get_admin_account_by_email(email):
        raise HTTPException(status_code=409, detail="An administrator account already uses that email")
    if not email_delivery_configured() or not settings.ADMIN_PASSWORD_RESET_URL:
        raise HTTPException(status_code=503, detail="Configure email delivery and ADMIN_PASSWORD_RESET_URL before inviting administrators")
    try:
        account = crud.create_admin_account(email, payload.display_name.strip(), hash_password(secrets.token_urlsafe(32)))
    except Exception as exc:
        logger.exception("Administrator account creation failed")
        raise HTTPException(status_code=503, detail="Administrator account could not be created") from exc
    audit_admin_action("invite_admin", "admin_accounts", {
        "actor_id": principal.get("account_id"), "account_id": str(account["id"]), "email": email,
    }, request=request)
    try:
        _issue_reset(account)
    except HTTPException as exc:
        raise HTTPException(
            status_code=503,
            detail="The account was created, but the invitation email could not be delivered. Fix email delivery, then use Forgot Password to send the setup link.",
        ) from exc
    return {"id": str(account["id"]), "email": account["email"], "message": "Invitation and password setup link sent."}


@router.get("/accounts")
def list_accounts(_: dict = Depends(require_role("admin"))) -> list[dict[str, Any]]:
    return crud.list_admin_accounts()


@router.patch("/accounts/{account_id}/status")
def set_account_status(
    account_id: UUID,
    payload: AdminAccountStatus,
    request: Request,
    principal: dict = Depends(require_role("admin")),
) -> dict[str, str]:
    account_id = str(account_id)
    account = crud.get_admin_account_by_id(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Administrator account not found")
    if principal.get("account_id") == account_id and not payload.is_active:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own administrator account")
    crud.set_admin_account_active(account_id, payload.is_active)
    audit_admin_action("set_admin_active" if payload.is_active else "disable_admin", "admin_accounts", {
        "actor_id": principal.get("account_id"), "account_id": account_id,
    }, request=request)
    return {"message": "Administrator access updated. Existing sessions have been revoked."}
