from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_deep_health_reports_reachable_supabase_database():
    with patch("app.core.supabase_client.get_supabase") as get_supabase:
        response = client.get("/health/deep")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "database": "reachable"}
    get_supabase.return_value.table.assert_called_once_with("zones")


def test_deep_health_reports_unavailable_supabase_database():
    with patch(
        "app.core.supabase_client.get_supabase",
        side_effect=RuntimeError("database unavailable"),
    ):
        response = client.get("/health/deep")

    assert response.status_code == 503
    assert response.json() == {"status": "unhealthy", "database": "unreachable"}
