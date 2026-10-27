"""
Unit tests for the alert / notification component.
"""
import unittest
from unittest.mock import MagicMock, patch
from components.alerts import render_alert


class TestAlerts(unittest.TestCase):

    @patch("components.alerts.st")
    def test_render_alert_warning(self, mock_st):
        alert = {
            "type": "Warning",
            "message": "Heavy rainfall expected in Rubavu next week.",
            "timestamp": "2 Hours Ago",
        }
        render_alert(alert)
        self.assertTrue(mock_st.markdown.called)
        rendered = mock_st.markdown.call_args[0][0]
        self.assertIn("ag-alert-warning", rendered)
        self.assertIn("Heavy rainfall expected", rendered)

    @patch("components.alerts.st")
    def test_render_alert_urgent(self, mock_st):
        alert = {
            "type": "Urgent",
            "message": "Fall armyworm detected in Bugesera sector.",
            "timestamp": "10 Mins Ago",
        }
        render_alert(alert)
        rendered = mock_st.markdown.call_args[0][0]
        self.assertIn("ag-alert-urgent", rendered)
        self.assertIn("Fall armyworm detected", rendered)

    @patch("components.alerts.st")
    def test_render_alert_info_fallback(self, mock_st):
        alert = {
            "type": "Info",
            "message": "Fertilizer shipment arrived at depot.",
        }
        render_alert(alert)
        rendered = mock_st.markdown.call_args[0][0]
        self.assertIn("ag-alert-info", rendered)
        self.assertIn("Fertilizer shipment", rendered)


if __name__ == "__main__":
    unittest.main()
