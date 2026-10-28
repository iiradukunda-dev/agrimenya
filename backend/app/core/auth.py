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


def create_token(role: str, expires_in_seconds: int = 3600, claims: dict[str, Any] | None = None) -> str:
    """Create a signed bearer token with the caller's role and expiry time."""
    role = (role or "").lower()
    if not role:
        raise ValueError("Role is required")

    payload = {
        "role": role,
        "exp": int(time.time()) + int(expires_in_seconds),
        "iat": int(time.time()),
    }
    if claims:
        payload.update(claims)
    if settings.JWT_ALGORITHM != "HS256":
        raise RuntimeError("Only HS256 JWT tokens are supported")
    header = {"alg": "HS256", "typ": "JWT"}
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
    try:
        header = json.loads(_b64url_decode(header_segment).decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid token header") from exc
    if not isinstance(header, dict) or header.get("alg") != "HS256" or header.get("typ") != "JWT":
        raise HTTPException(status_code=401, detail="Unsupported token header")
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
    if not isinstance(payload, dict):
        raise HTTPException(status_code=401, detail="Invalid token payload")

    now = int(time.time())
    try:
        exp = int(payload["exp"])
        issued_at = int(payload["iat"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Token expiry and issue time are required") from exc
    if exp <= now:
        raise HTTPException(status_code=401, detail="Token expired")
    if issued_at > now or issued_at >= exp:
        raise HTTPException(status_code=401, detail="Invalid token issue time")

    role = (payload.get("role") or "").lower()
    if expected_role and role != expected_role.lower():
        raise HTTPException(status_code=401, detail=f"Role mismatch: expected {expected_role}")

    return payload


def _role_key(role: str) -> str:
    role = (role or "").lower()
    if role == "admin":
        return ""
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
            if required == "admin":
                account_id = payload.get("sub")
                token_version = payload.get("ver")
                if not account_id or not isinstance(token_version, int):
                    raise HTTPException(status_code=401, detail="Administrator account session required")
                from app.db import crud
                account = crud.get_admin_account_by_id(str(account_id))
                if (not account or not account.get("is_active") or
                        int(account.get("session_version", 0)) != token_version):
                    raise HTTPException(status_code=401, detail="Administrator session expired; sign in again")
                payload["email"] = account.get("email")
                payload["name"] = account.get("display_name")
            return {"role": payload.get("role"), "token": raw_token, "account_id": payload.get("sub")}

        token = _extract_token(request)
        if token:
            if required == "admin":
                raise HTTPException(status_code=401, detail="Use an administrator account session")
            if configured_key and hmac.compare_digest(token, configured_key):
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
    if settings.APP_ENV in {"development", "test"}:
        return {"role": "user", "token": None}
    return require_role("user")(request)


def require_community(request: Request) -> dict[str, Any]:
    """Require an individually authenticated community account."""
    if (len(settings.JWT_SECRET) < 32 or settings.JWT_SECRET.startswith("replace-with-") or
            settings.JWT_SECRET == "dev-secret-change-me"):
        raise HTTPException(status_code=503, detail="Community sessions are not securely configured")
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Sign in to the farmer community")
    raw_token = authorization.split(" ", 1)[1].strip()
    payload = verify_token(raw_token, expected_role="community")
    account_id = payload.get("sub")
    token_version = payload.get("ver")
    if not account_id or not isinstance(token_version, int):
        raise HTTPException(status_code=401, detail="Community account session required")
    from app.db import crud

    account = crud.get_community_account_by_id(str(account_id))
    if (not account or not account.get("is_active") or
            int(account.get("session_version", 0)) != token_version):
        raise HTTPException(status_code=401, detail="Community session expired; sign in again")
    return {
        "account_id": str(account["id"]),
        "display_name": account["display_name"],
        "role": account["role"],
    }


def require_community_or_admin(request: Request) -> dict[str, Any]:
    """Allow signed-in farmers and administrators to create mapped farm sites."""
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Sign in to the farmer community to save a farm location")
    payload = verify_token(authorization.split(" ", 1)[1].strip())
    role = str(payload.get("role") or "").lower()
    if role == "community":
        return require_community(request)
    if role == "admin":
        return require_admin(request)
    raise HTTPException(status_code=403, detail="This action requires a farmer account or administrator access")
