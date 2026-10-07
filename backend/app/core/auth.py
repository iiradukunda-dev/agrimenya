import base64
import hashlib
import hmac
import json
import time
from typing import Any

from fastapi import HTTPException, Request

from app.core.config import settings


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def create_token(role: str, expires_in_seconds: int = 3600) -> str:
    """Create a signed bearer token with the caller's role and expiry time."""
    role = (role or "").lower()
    if not role:
        raise ValueError("Role is required")

    payload = {
        "role": role,
        "exp": int(time.time()) + int(expires_in_seconds),
        "iat": int(time.time()),
    }
    header = {"alg": settings.JWT_ALGORITHM or "HS256", "typ": "JWT"}
    header_segment = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_segment = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{header_segment}.{payload_segment}".encode()
    signature = hmac.new(settings.JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{header_segment}.{payload_segment}.{_b64url_encode(signature)}"


def verify_token(token: str, expected_role: str | None = None) -> dict[str, Any]:
    """Validate a signed bearer token and return its claims."""
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    parts = token.split(".")
    if len(parts) != 3:
        raise HTTPException(status_code=401, detail="Malformed token")

    header_segment, payload_segment, signature_segment = parts
    signing_input = f"{header_segment}.{payload_segment}".encode("utf-8")
    expected_signature = _b64url_encode(
        hmac.new(settings.JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256).digest()
    )
    if not hmac.compare_digest(signature_segment, expected_signature):
        raise HTTPException(status_code=401, detail="Invalid token signature")

    try:
        payload = json.loads(_b64url_decode(payload_segment).decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid token payload") from exc

    now = int(time.time())
    exp = int(payload.get("exp", 0))
    if exp and now > exp:
        raise HTTPException(status_code=401, detail="Token expired")

    role = (payload.get("role") or "").lower()
    if expected_role and role != expected_role.lower():
        raise HTTPException(status_code=401, detail=f"Role mismatch: expected {expected_role}")

    return payload


def _role_key(role: str) -> str:
    role = (role or "").lower()
    if role == "admin":
        return settings.ADMIN_API_KEY
    if role in {"user", "reader", "analyst"}:
        return settings.USER_API_KEY
    return ""


def _extract_token(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth.split(" ", 1)[1].strip()
    return request.headers.get("X-API-Key") or request.headers.get("X-Admin-Key") or ""


def require_role(required_role: str):
    def dependency(request: Request):
        required = (required_role or "").lower()
        configured_key = _role_key(required)
        role_hint = (request.headers.get("X-Role") or "").lower()

        token = request.headers.get("Authorization", "")
        if token.startswith("Bearer "):
            raw_token = token.split(" ", 1)[1].strip()
            payload = verify_token(raw_token, expected_role=required)
            return {"role": payload.get("role"), "token": raw_token}

        token = _extract_token(request)
        if token:
            if token == configured_key:
                if role_hint and role_hint != required:
                    raise HTTPException(status_code=401, detail=f"Role mismatch: expected {required}")
                return {"role": required, "token": token}
            raise HTTPException(status_code=401, detail=f"Invalid or missing {required} credentials")

        if not configured_key:
            raise HTTPException(status_code=401, detail=f"{required.title()} access is not configured")

        raise HTTPException(status_code=401, detail=f"Missing {required} credentials")

    return dependency


def require_admin(request: Request):
    return require_role("admin")(request)


def require_user(request: Request):
    """Require a provisioned user key for writes in production.

    Development remains convenient for local integration and automated tests.
    Production startup separately enforces that USER_API_KEY is configured.
    """
    if settings.APP_ENV != "production":
        return {"role": "user", "token": None}
    return require_role("user")(request)
