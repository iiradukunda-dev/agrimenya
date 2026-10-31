"""Automated tests for internationalization (i18n) and AI widget translation in agrimenya."""
import streamlit as st
from unittest.mock import MagicMock, patch
from utils.i18n import FALLBACK_TRANSLATIONS, get_current_language, render_language_selector, set_language, t


def test_ai_ask_ai_translations_exist():
    """Verify that 'ai.ask_ai' key exists in all supported languages."""
    for lang in ["en", "rw", "fr"]:
        assert lang in FALLBACK_TRANSLATIONS, f"Language {lang} missing in FALLBACK_TRANSLATIONS"
        assert "ai.ask_ai" in FALLBACK_TRANSLATIONS[lang], f"'ai.ask_ai' missing in {lang}"

    assert FALLBACK_TRANSLATIONS["en"]["ai.ask_ai"] == "Ask AI"
    assert FALLBACK_TRANSLATIONS["rw"]["ai.ask_ai"] == "Baza AI"
    assert FALLBACK_TRANSLATIONS["fr"]["ai.ask_ai"] == "Demander à l'IA"


def test_language_switching_translates_ai_ask_ai():
    """Verify that t('ai.ask_ai') translates dynamically when language changes."""
    # Test English
    set_language("en")
    assert get_current_language() == "en"
    assert t("ai.ask_ai") == "Ask AI"

    # Test Kinyarwanda
    set_language("rw")
    assert get_current_language() == "rw"
    assert t("ai.ask_ai") == "Baza AI"

    # Test French
    set_language("fr")
    assert get_current_language() == "fr"
    assert t("ai.ask_ai") == "Demander à l'IA"

    # Reset to English
    set_language("en")
    assert t("ai.ask_ai") == "Ask AI"


def test_language_selector_uses_globe_icon():
    mock_st = MagicMock()
    with patch("utils.i18n.st", mock_st), patch(
        "utils.i18n.get_current_language", return_value="en"
    ):
        render_language_selector(sidebar=False)

    assert mock_st.button.call_args.kwargs["icon"] == ":material/language:"


def test_navbar_and_home_translation_keys():
    """Verify that navbar and home workflows have translated strings across all languages."""
    keys = [
        "nav.overview",
        "nav.zones",
        "nav.decisions",
        "nav.more",
        "home.workflows_title",
        "home.workflow.zones_title",
        "home.workflow.decisions_title",
        "home.pipeline_badge",
    ]
    for lang in ["en", "rw", "fr"]:
        for key in keys:
            assert key in FALLBACK_TRANSLATIONS[lang], f"Key '{key}' missing for lang '{lang}'"


def test_all_pages_translation_keys_exist():
    """Verify that all main application pages have corresponding translation keys."""
    page_keys = [
        "dashboard.title",
        "dashboard.kpi.zones_alignment",
        "dashboard.weather.live_title",
        "zones.title",
        "zones.register_expander",
        "ai.title",
        "ai.tab.advisor",
        "ai.tab.disease",
        "about.title",
        "about.sections_title",
        "contact.title",
        "contact.submit",
        "guide.title",
        "admin.title",
        "nav.install_app",
    ]
    for lang in ["en", "rw", "fr"]:
        for key in page_keys:
            assert key in FALLBACK_TRANSLATIONS[lang], f"Key '{key}' missing for lang '{lang}'"
            assert len(FALLBACK_TRANSLATIONS[lang][key]) > 0


def test_dynamic_language_switching_across_all_pages():
    """Verify that switching language dynamically updates page text across all views."""
    # Test English
    set_language("en")
    assert t("dashboard.title") == "Dashboard"
    assert t("about.title") == "About agrimenya"
    assert t("contact.title") == "Send feedback"
    assert t("guide.title") == "Data guide"
    assert t("zones.title") == "Agricultural Zones"
    assert t("ai.title") == "AI Assistant"

    # Test Kinyarwanda
    set_language("rw")
    assert t("dashboard.title") == "Incamake"
    assert t("about.title") == "Ibyerekeye agrimenya"
    assert t("contact.title") == "Tanga ibitekerezo"
    assert t("guide.title") == "Igitabo cy'Amakuru"
    assert t("zones.title") == "Uduce tw'Ubuhinzi"
    assert t("ai.title") == "Ubufasha bwa AI"

    # Test French
    set_language("fr")
    assert t("dashboard.title") == "Tableau de Bord"
    assert t("about.title") == "À propos d'agrimenya"
    assert t("contact.title") == "Envoyer un retour"
    assert t("guide.title") == "Guide des données"
    assert t("zones.title") == "Zones Agricoles"
    assert t("ai.title") == "Assistant IA"

    # Reset to English
    set_language("en")
