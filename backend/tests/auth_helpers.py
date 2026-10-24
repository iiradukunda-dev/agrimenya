"""Test helpers for the named-administrator session contract."""
from uuid import UUID

from app.core.auth import create_token
from app.core.config import settings
from app.db import crud

TEST_ADMIN_ID = "00000000-0000-4000-8000-000000000001"


def admin_headers(monkeypatch) -> dict[str, str]:
    monkeypatch.setattr(settings, "JWT_SECRET", "test-admin-jwt-secret-that-is-at-least-32-chars")
    monkeypatch.setattr(crud, "get_admin_account_by_id", lambda account_id: {
        "id": str(UUID(TEST_ADMIN_ID)), "email": "admin@example.test",
        "display_name": "Test Admin", "is_active": True, "session_version": 1,
    })
    token = create_token("admin", claims={"sub": TEST_ADMIN_ID, "ver": 1})
    return {"Authorization": f"Bearer {token}"}
