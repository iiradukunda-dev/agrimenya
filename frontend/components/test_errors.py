"""Unit tests for errors component: sanitization, categorization, auto-refinement, and error_boundary."""
from unittest.mock import MagicMock, patch

import pytest
import requests
from components.errors import _get_error_config, _sanitize_details, error_boundary, render_error_page


def test_sanitize_details_bearer_token():
    raw = "Failed request with header Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.t-ID"
    sanitized = _sanitize_details(raw)
    assert "Bearer [REDACTED_TOKEN]" in sanitized
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in sanitized


def test_sanitize_details_passwords_and_secrets():
    raw = "Request failed on url http://localhost?password=SuperSecretPassword123&secret=xyz&token=abc"
    sanitized = _sanitize_details(raw)
    assert "password=[REDACTED]" in sanitized
    assert "secret=[REDACTED]" in sanitized
    assert "token=[REDACTED]" in sanitized
    assert "SuperSecretPassword123" not in sanitized


def test_sanitize_details_db_uri():
    raw = "Connection failed to postgresql://postgres:mysecretpassword@db.supabase.co:5432/postgres"
    sanitized = _sanitize_details(raw)
    assert "[REDACTED_DB_CREDENTIALS]" in sanitized
    assert "mysecretpassword" not in sanitized


def test_sanitize_details_empty():
    assert _sanitize_details("") == ""
    assert _sanitize_details(None) == ""


@pytest.mark.parametrize(
    "error_type,expected_key",
    [
        ("404", "404"),
        ("not_found", "404"),
        ("401", "unauthorized"),
        ("unauthorized", "unauthorized"),
        ("403", "forbidden"),
        ("forbidden", "forbidden"),
        ("timeout", "timeout"),
        ("504", "timeout"),
        ("network", "network"),
        ("connection", "network"),
        ("offline", "network"),
        ("validation", "validation"),
        ("422", "validation"),
        ("database", "database"),
        ("503", "database"),
        ("system", "system"),
        ("unknown_xyz", "system"),
    ],
)
def test_get_error_config_categories(error_type, expected_key):
    cfg = _get_error_config(error_type)
    assert cfg["key"] == expected_key
    assert "badge" in cfg
    assert "accent" in cfg
    assert "<svg" in cfg["icon"]


def test_get_error_config_auto_refinement():
    # If error_type is generic "network", but details mention 401 Unauthorized
    cfg_401 = _get_error_config("network", details="401 Client Error: Unauthorized for url https://api")
    assert cfg_401["key"] == "unauthorized"

    # If error_type is "system", but details mention 404
    cfg_404 = _get_error_config("system", details="404 Client Error: Not Found")
    assert cfg_404["key"] == "404"

    # If error_type is "network", but details mention 503
    cfg_503 = _get_error_config("network", details="503 Service Unavailable: Database offline")
    assert cfg_503["key"] == "database"

    # If error_type is "network", but details mention timed out
    cfg_timeout = _get_error_config("network", details="HTTPSConnectionPool: Read timed out.")
    assert cfg_timeout["key"] == "timeout"


def test_error_boundary_context_manager_suppresses_and_renders():
    rendered_types = []

    with patch("components.errors.render_error_page", side_effect=lambda t, **kw: rendered_types.append(t)):
        with error_boundary("Test Workspace"):
            raise ValueError("Invalid season parameter")

    assert rendered_types == ["validation"]


def test_error_boundary_decorator_suppresses_and_renders():
    rendered_types = []

    @error_boundary("Test Decorator")
    def faulty_view():
        raise PermissionError("Access forbidden to sensitive records")

    with patch("components.errors.render_error_page", side_effect=lambda t, **kw: rendered_types.append(t)):
        faulty_view()

    assert rendered_types == ["forbidden"]


def test_error_boundary_handles_http_errors_with_status_codes():
    rendered_types = []

    resp_403 = MagicMock()
    resp_403.status_code = 403
    http_err = requests.exceptions.HTTPError(response=resp_403)

    with patch("components.errors.render_error_page", side_effect=lambda t, **kw: rendered_types.append(t)):
        with error_boundary("Admin Test"):
            raise http_err

    assert rendered_types == ["forbidden"]


def test_error_boundary_handles_timeout_and_connection():
    rendered = []

    with patch("components.errors.render_error_page", side_effect=lambda t, **kw: rendered.append(t)):
        with error_boundary("Network Test"):
            raise requests.exceptions.ConnectionError("Failed to establish a new connection")

    assert rendered == ["network"]

    rendered.clear()
    with patch("components.errors.render_error_page", side_effect=lambda t, **kw: rendered.append(t)):
        with error_boundary("Timeout Test"):
            raise requests.exceptions.Timeout("Operation timed out")

    assert rendered == ["timeout"]


def test_error_boundary_does_not_suppress_base_exceptions():
    with pytest.raises(KeyboardInterrupt):
        with error_boundary("Interrupt Test"):
            raise KeyboardInterrupt()
