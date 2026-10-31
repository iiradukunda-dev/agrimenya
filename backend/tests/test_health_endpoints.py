from unittest.mock import MagicMock, patch

import psycopg
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


client = TestClient(app)


def test_health_endpoints_keep_liveness_independent_of_database():
    with patch("app.main._system_health_status", side_effect=AssertionError):
        assert client.get("/health").json() == {"status": "alive"}
        assert client.get("/health/live").json() == {"status": "alive"}


def test_detailed_health_endpoint_preserves_database_status(monkeypatch):
    status = {
        "status": "degraded",
        "database_status": "unavailable",
        "baselines_present": True,
    }
    monkeypatch.setattr("app.main._system_health_status", lambda: status)

    response = client.get("/health/status")

    assert response.status_code == 200
    assert response.json() == status


def test_deep_health_requires_database_url(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_DB_URL", "")

    response = client.get("/health/deep")

    assert response.status_code == 503
    assert response.json() == {
        "status": "unhealthy",
        "database": "unreachable",
    }


def test_deep_health_runs_a_bounded_select_one(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_DB_URL", "postgresql://example")
    connection = MagicMock()
    connection.__enter__.return_value = connection

    with patch("psycopg.connect", return_value=connection) as connect:
        response = client.get("/health/deep")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "database": "reachable"}
    connect.assert_called_once_with(
        "postgresql://example",
        connect_timeout=5,
        options="-c statement_timeout=5000",
    )
    connection.execute.assert_called_once_with("SELECT 1")


def test_deep_health_hides_database_connection_details(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_DB_URL", "postgresql://secret")

    with patch(
        "psycopg.connect",
        side_effect=psycopg.OperationalError("contains-secret-connection-details"),
    ):
        response = client.get("/health/deep")

    assert response.status_code == 503
    assert response.json() == {
        "status": "unhealthy",
        "database": "unreachable",
    }
    assert "secret" not in response.text
