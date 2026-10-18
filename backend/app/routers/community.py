"""Authenticated farmer discussion board and administrator moderation."""
from collections import defaultdict, deque
import logging
import re
import secrets
import threading
import time
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field, field_validator

from app.core.auth import create_token, require_admin, require_community
from app.core.audit import audit_admin_action
from app.core.config import settings
from app.db import crud
from app.services.admin_auth import hash_password, verify_password

router = APIRouter(prefix="/community", tags=["Farmer Community"])
logger = logging.getLogger(__name__)
_login_attempts: dict[str, deque[float]] = defaultdict(deque)
_write_attempts: dict[str, deque[float]] = defaultdict(deque)
_limits_lock = threading.Lock()
_DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(32))


def _rate_limit(store: dict[str, deque[float]], key: str, maximum: int, window: int = 60) -> None:
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
    display_name: str = Field(min_length=1, max_length=80)
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
        value = _clean_text(value)
        if not value:
            raise ValueError("Display name is required")
        return value


class CommunityLogin(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)

    @field_validator("email")
    @classmethod
    def email_normalized(cls, value: str) -> str:
        return value.strip().lower()


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
        account = crud.create_community_account(
            payload.email, payload.display_name, hash_password(payload.password)
        )
    except HTTPException:
        raise
    except Exception as exc:
        try:
            if crud.get_community_account_by_email(payload.email):
                raise HTTPException(status_code=409, detail="An account already uses that email") from exc
        except HTTPException:
            raise
        except Exception:
            pass
        logger.exception("Community registration failed")
        raise HTTPException(status_code=503, detail="Account registration is temporarily unavailable") from exc
    token = create_token("community", 3600, {"sub": str(account["id"]), "ver": int(account.get("session_version", 1))})
    return {"access_token": token, "token_type": "bearer", "expires_in": 3600,
            "account": {"id": str(account["id"]), "display_name": account["display_name"],
                        "role": account["role"]}}


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
    token = create_token("community", 3600, {"sub": str(account["id"]), "ver": int(account.get("session_version", 1))})
    return {"access_token": token, "token_type": "bearer", "expires_in": 3600,
            "account": {"id": str(account["id"]), "display_name": account["display_name"],
                        "role": account["role"]}}


@router.get("/posts")
def posts(limit: int = Query(default=30, ge=1, le=50), offset: int = Query(default=0, ge=0, le=10000),
          _: dict = Depends(require_community)):
    try:
        return crud.list_community_posts(limit, offset)
    except Exception as exc:
        logger.exception("Community feed could not be loaded")
        raise HTTPException(status_code=503, detail="Community feed is temporarily unavailable") from exc


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
    post = crud.get_community_post(str(post_id))
    if not post or post.get("status") != "published":
        raise HTTPException(status_code=404, detail="Post not found")
    return crud.list_community_comments(str(post_id))


@router.post("/posts/{post_id}/comments", status_code=status.HTTP_201_CREATED)
def create_comment(post_id: UUID, payload: CommentCreate,
                   account: dict = Depends(require_community)):
    _rate_limit(_write_attempts, f"comment:{account['account_id']}", 30, 3600)
    post = crud.get_community_post(str(post_id))
    if not post or post.get("status") != "published":
        raise HTTPException(status_code=404, detail="Post not found")
    try:
        return crud.create_community_comment(str(post_id), account["account_id"], payload.body)
    except Exception as exc:
        logger.exception("Community comment could not be created")
        raise HTTPException(status_code=503, detail="Comment could not be saved") from exc


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
