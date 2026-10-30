"""
Unit tests for WhatsApp Administration component.
Tests CAT timezone formatting, provider error explanations, and safe rendering.
"""
from unittest.mock import MagicMock, patch
import pytest

from components.whatsapp_admin import (
    _explain_wa_error,
    _format_cat_timestamp,
    render_whatsapp_admin_panel,
)


def test_format_cat_timestamp_valid_utc():
    # 2026-10-26T10:00:00Z should convert to 12:00 CAT (UTC+2)
    formatted = _format_cat_timestamp("2026-10-26T10:00:00Z")
    assert "26 Oct 2026" in formatted
    assert "12:00 CAT" in formatted


def test_format_cat_timestamp_none_or_empty():
    assert _format_cat_timestamp(None) == "Not available"
    assert _format_cat_timestamp("") == "Not available"


def test_format_cat_timestamp_fallback():
    # If date is unparseable, returns string prefix safely without throwing
    res = _format_cat_timestamp("invalid-date-string-sample")
    assert "invalid-date-string" in res


@pytest.mark.parametrize(
    "code,expected_substr",
    [
        ("131026", "undeliverable"),
        ("131047", "24-hour"),
        ("131051", "template does not exist"),
        ("130429", "Rate limit"),
        ("999999", "Provider status"),
    ],
)
def test_explain_wa_error(code, expected_substr):
    explanation = _explain_wa_error(code)
    assert expected_substr.lower() in explanation.lower()


@patch("components.whatsapp_admin.api_client")
@patch("components.whatsapp_admin.st")
def test_render_whatsapp_admin_panel_executes_safely(mock_st, mock_api):
    # Setup mock returns
    mock_api.get_whatsapp_health.return_value = {
        "mode": "mock",
        "approved_templates": 3,
        "failed_messages_24h": 0,
        "last_webhook_received_at": "2026-10-26T10:00:00Z",
    }
    mock_api.get_whatsapp_stats.return_value = {
        "days": 7,
        "by_status": {"queued": 1, "sent": 10, "delivered": 9, "read": 8, "failed": 0},
        "by_kind": {"alert": 10},
        "top_error_codes": {},
    }
    mock_api.get_whatsapp_contacts.return_value = [
        {
            "id": "contact-uuid-1",
            "display_name": "Farmer Habimana",
            "role": "farmer",
            "phone_masked": "+250 788 ••• ••56",
            "language": "rw",
            "crops": ["Maize"],
            "whatsapp_opt_in": True,
            "opt_in_at": "2026-10-26T08:00:00Z",
        }
    ]
    mock_api.get_zones.return_value = []
    mock_api.get_whatsapp_templates.return_value = [
        {"name": "agrimenya_alert_rw", "language": "rw", "param_count": 4, "status": "APPROVED"}
    ]
    mock_api.get_admin_alerts.return_value = []

    # Mock st.tabs to return 5 context managers
    mock_tabs = [MagicMock() for _ in range(5)]
    mock_st.tabs.return_value = mock_tabs
    mock_st.columns.side_effect = lambda n, **kwargs: [MagicMock() for _ in range(n if isinstance(n, int) else len(n))]

    # Execute without errors
    render_whatsapp_admin_panel(key_prefix="test_wa", embedded_mode=True)
    assert mock_st.tabs.called
