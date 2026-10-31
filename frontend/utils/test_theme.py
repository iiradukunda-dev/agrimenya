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
    def test_load_theme_keeps_the_light_palette(self, mock_st):
        mock_st.session_state = {"ag_theme_mode": "light"}
        load_theme()
        self.assertTrue(mock_st.html.called)
        light_css = mock_st.html.call_args[0][0]
        self.assertIn("--ag-primary: #0284c7;", light_css)
        self.assertIn("--ag-bg-base: #f8fafc;", light_css)
        self.assertIn('[data-testid="stSkeleton"]', light_css)
        self.assertIn("display: none !important;", light_css)
        self.assertEqual(mock_st.session_state["ag_theme_mode"], "light")

        mock_st.session_state = {"ag_theme_mode": "dark"}
        load_theme()
        forced_light_css = mock_st.html.call_args[0][0]
        self.assertIn("--ag-bg-base: #f8fafc;", forced_light_css)
        self.assertEqual(mock_st.session_state["ag_theme_mode"], "light")

    @patch("utils.theme.st")
    def test_disease_action_buttons_use_triage_style(self, mock_st):
        mock_st.session_state = {"ag_theme_mode": "light"}
        load_theme()

        css = mock_st.html.call_args[0][0]
        self.assertIn(".st-key-disease_triage_button button", css)
        self.assertIn(".st-key-detect_disease_button button", css)
        self.assertIn(".st-key-detect_disease_submit button", css)
        self.assertIn('content: "→"', css)
        self.assertIn("linear-gradient(110deg, #1596f4 0%, #0561ce 100%)", css)
        self.assertIn('button[kind="primary"]', css)
        self.assertIn("color: #ffffff !important;", css)
        self.assertIn("linear-gradient(135deg, #0369a1 0%, #0284c7 100%)", css)
        self.assertIn("@keyframes ag-button-shake", css)
        self.assertIn("animation: ag-button-shake 320ms ease-in-out !important;", css)
        self.assertIn('[data-testid="stAppViewContainer"] button:active', css)
        self.assertIn('[data-testid="stAppViewContainer"] a:active', css)
        self.assertIn("animation: none !important;", css)
        self.assertIn("border-radius: 9999px !important;", css)
        self.assertIn('[data-testid="stFormSubmitButton"] button[kind="primary"]', css)


if __name__ == "__main__":
    unittest.main()
