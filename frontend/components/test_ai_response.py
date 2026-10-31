from unittest.mock import MagicMock, patch

from components.ai_response import render_advisor_response


def test_advisor_response_shows_answer_type_scope_and_citation():
    response = {
        "answer": "Check soil moisture before planting.",
        "answer_type": "record_grounded",
        "source": "anthropic",
        "evidence_scope": "Huye / Maize / 2026 Season A",
        "evidence_source_details": [{
            "title": "Seasonal Agricultural Survey",
            "url": "https://example.org/survey",
            "publisher": "NISR",
            "coverage": "2026 Season A",
            "limitations": "District-level historical evidence.",
        }],
    }

    with patch("components.ai_response.st", MagicMock()) as mock_st:
        render_advisor_response(response)

    mock_st.markdown.assert_any_call("Check soil moisture before planting.")
    mock_st.markdown.assert_any_call(
        "- [Seasonal Agricultural Survey](https://example.org/survey) — NISR"
    )
    mock_st.caption.assert_any_call("Scope: Huye / Maize / 2026 Season A")


def test_general_guidance_and_empty_answer_are_not_presented_as_grounded():
    with patch("components.ai_response.st", MagicMock()) as mock_st:
        render_advisor_response({
            "answer": "",
            "answer_type": "general_guidance",
            "source": "grounded-context",
        })

    mock_st.info.assert_called_once()
    assert mock_st.warning.call_count == 1
    mock_st.error.assert_called_once()


def test_offline_nisr_response_is_labeled_as_historical_not_ai_advice():
    with patch("components.ai_response.st", MagicMock()) as mock_st:
        render_advisor_response({
            "answer": "Historical district yields are available.",
            "answer_type": "record_grounded",
            "source": "offline_nisr",
        })

    mock_st.info.assert_called_once()
    mock_st.markdown.assert_any_call("Historical district yields are available.")
