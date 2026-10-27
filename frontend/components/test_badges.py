"""
Unit tests for priority and status badges in frontend components.
"""
import unittest
from unittest.mock import MagicMock, patch
from components.badges import priority_badge, status_badge


class TestBadges(unittest.TestCase):

    @patch("components.badges.st")
    def test_priority_badge_known_levels(self, mock_st):
        for level in ["High", "Medium", "Low", "high", "MEDIUM", "low"]:
            priority_badge(level)
            self.assertTrue(mock_st.markdown.called)
            rendered = mock_st.markdown.call_args[0][0]
            self.assertIn("ag-badge-dot", rendered)
            self.assertIn("ag-badge", rendered)

    @patch("components.badges.st")
    def test_priority_badge_unknown_level(self, mock_st):
        priority_badge("Critical")
        rendered = mock_st.markdown.call_args[0][0]
        self.assertIn("ag-badge-unknown", rendered)
        self.assertIn("Critical", rendered)

    @patch("components.badges.st")
    def test_status_badge_variants(self, mock_st):
        variants = {
            "completed": "ag-badge-low",
            "verified": "ag-badge-low",
            "pending": "ag-badge-medium",
            "warning": "ag-badge-medium",
            "urgent": "ag-badge-high",
            "danger": "ag-badge-high",
            "custom": "ag-badge-unknown",
        }
        for variant, expected_class in variants.items():
            status_badge("Sample Status", variant=variant)
            rendered = mock_st.markdown.call_args[0][0]
            self.assertIn(expected_class, rendered)
            self.assertIn("Sample Status", rendered)


if __name__ == "__main__":
    unittest.main()
