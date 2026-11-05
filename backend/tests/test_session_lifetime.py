from fastapi.testclient import TestClient

from app.core.auth import APPLICATION_SESSION_TTL_SECONDS
from app.main import app
from app.routers import admin_auth, community

client = TestClient(app)


def test_community_login_issues_a_seven_day_session(monkeypatch):
    account = {
        "id": "community-user",
        "display_name": "Farmer",
        "role": "farmer",
        "password_hash": "password-hash",
        "is_active": True,
        "email_verified_at": "2026-01-01T00:00:00+00:00",
        "session_version": 1,
    }
    token_arguments = {}

    monkeypatch.setattr(community, "_ensure_secure_sessions", lambda: None)
    monkeypatch.setattr(community, "_rate_limit", lambda *args, **kwargs: None)
    monkeypatch.setattr(community.crud, "get_community_account_by_email", lambda email: account)
    monkeypatch.setattr(community, "verify_password", lambda password, hashed: True)
    monkeypatch.setattr(
        community,
        "create_token",
        lambda role, ttl, claims: token_arguments.update(role=role, ttl=ttl, claims=claims) or "token",
    )

    response = client.post(
        "/community/login",
        json={"email": "farmer@example.com", "password": "password"},
    )

    assert response.status_code == 200
    assert response.json()["expires_in"] == APPLICATION_SESSION_TTL_SECONDS
    assert token_arguments["ttl"] == APPLICATION_SESSION_TTL_SECONDS


def test_admin_login_issues_a_seven_day_session(monkeypatch):
    account = {
        "id": "admin-user",
        "email": "admin@example.com",
        "display_name": "Administrator",
        "password_hash": "password-hash",
        "is_active": True,
        "session_version": 1,
    }
    token_arguments = {}

    monkeypatch.setattr(admin_auth, "_limit", lambda request: None)
    monkeypatch.setattr(admin_auth.crud, "get_admin_account_by_email", lambda email: account)
    monkeypatch.setattr(admin_auth, "verify_password", lambda password, hashed: True)
    monkeypatch.setattr(admin_auth.crud, "record_admin_login", lambda account_id: None)
    monkeypatch.setattr(
        admin_auth,
        "create_token",
        lambda role, expires_in_seconds, claims: (
            token_arguments.update(role=role, ttl=expires_in_seconds, claims=claims) or "token"
        ),
    )

    response = client.post(
        "/auth/admin/login",
        json={"email": "admin@example.com", "password": "password"},
    )

    assert response.status_code == 200
    assert response.json()["expires_in"] == APPLICATION_SESSION_TTL_SECONDS
    assert token_arguments["ttl"] == APPLICATION_SESSION_TTL_SECONDS
