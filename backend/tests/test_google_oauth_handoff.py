import hashlib

from fastapi.testclient import TestClient
import pytest

from app.core.config import Settings, settings
from app.db import crud
from app.main import app

client = TestClient(app)


def test_google_exchange_requires_the_initiating_browser_binding(monkeypatch):
    monkeypatch.setattr(settings, "APP_ENV", "test")
    monkeypatch.setattr(settings, "JWT_SECRET", "test-google-handoff-secret-that-is-at-least-32-chars")

    code = "c" * 43
    binding = "b" * 43
    expected_code_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()
    expected_binding_hash = hashlib.sha256(binding.encode("utf-8")).hexdigest()

    def consume_code(code_hash: str, browser_binding_hash: str) -> str | None:
        if code_hash == expected_code_hash and browser_binding_hash == expected_binding_hash:
            return "00000000-0000-4000-8000-000000000001"
        return None

    monkeypatch.setattr(crud, "consume_community_oauth_login_code", consume_code)
    monkeypatch.setattr(crud, "get_community_account_by_id", lambda _: {
        "id": "00000000-0000-4000-8000-000000000001",
        "display_name": "test_farmer",
        "role": "farmer",
        "is_active": True,
        "session_version": 1,
    })

    missing_binding = client.post(
        "/community/auth/google/exchange", json={"code": code},
    )
    assert missing_binding.status_code == 422

    wrong_binding = client.post(
        "/community/auth/google/exchange",
        json={"code": code, "browser_binding": "x" * 43},
    )
    assert wrong_binding.status_code == 400

    valid_binding = client.post(
        "/community/auth/google/exchange",
        json={"code": code, "browser_binding": binding},
    )
    assert valid_binding.status_code == 200
    assert valid_binding.json()["account"]["display_name"] == "test_farmer"


def test_google_oauth_requires_a_cookie_domain_shared_by_callback_hosts():
    config = Settings()
    config.SUPABASE_URL = "https://database.example.test"
    config.SUPABASE_KEY = "test-database-key"
    config.APP_ENV = "test"
    config.GOOGLE_OAUTH_CLIENT_ID = "test-client"
    config.GOOGLE_OAUTH_CLIENT_SECRET = "test-secret"
    config.GOOGLE_OAUTH_REDIRECT_URI = "https://api.example.test/community/auth/google/callback"
    config.COMMUNITY_GOOGLE_CALLBACK_URL = "https://app.example.test/Community"

    with pytest.raises(RuntimeError, match="share a hostname"):
        config.validate()

    config.COMMUNITY_GOOGLE_HANDOFF_COOKIE_DOMAIN = "example.test"
    config.validate()
