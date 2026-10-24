"""Automated tests for internationalization (i18n) and AI widget translation in agrimenya."""
import streamlit as st
from utils.i18n import FALLBACK_TRANSLATIONS, get_current_language, set_language, t


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
