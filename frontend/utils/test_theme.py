"""
Unit tests for theme utilities and design tokens.
"""
import unittest
from unittest.mock import MagicMock, patch
from utils.theme import get_current_theme, load_theme, toggle_theme


class TestTheme(unittest.TestCase):

    @patch("utils.theme.st")
    def test_get_current_theme_default(self, mock_st):
        mock_st.session_state = {}
        theme = get_current_theme()
        self.assertEqual(theme, "light")

    @patch("utils.theme.st")
    def test_get_current_theme_custom(self, mock_st):
        mock_st.session_state = {"ag_theme_mode": "dark"}
        theme = get_current_theme()
        self.assertEqual(theme, "dark")

    @patch("utils.theme.st")
    def test_toggle_theme(self, mock_st):
        mock_st.session_state = {"ag_theme_mode": "light"}
        toggle_theme()
        self.assertEqual(mock_st.session_state["ag_theme_mode"], "dark")
        toggle_theme()
        self.assertEqual(mock_st.session_state["ag_theme_mode"], "light")

    @patch("utils.theme.st")
    def test_load_theme_light_and_dark(self, mock_st):
        # Light mode
        mock_st.session_state = {"ag_theme_mode": "light"}
        load_theme()
        self.assertTrue(mock_st.html.called)
        light_css = mock_st.html.call_args[0][0]
        self.assertIn("--ag-primary: #0284c7;", light_css)
        self.assertIn("--ag-bg-base: #f8fafc;", light_css)

        # Dark mode
        mock_st.session_state = {"ag_theme_mode": "dark"}
        load_theme()
        dark_css = mock_st.html.call_args[0][0]
        self.assertIn("--ag-bg-base: #09111c;", dark_css)


if __name__ == "__main__":
    unittest.main()

