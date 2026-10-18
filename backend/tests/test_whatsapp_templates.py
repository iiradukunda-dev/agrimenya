from unittest.mock import patch

import pytest

from app.services.whatsapp.templates import approved_template, render_preview, validate_params


def test_render_preview_substitutes_parameters():
    preview = render_preview("agrimenya_alert", "en", ["Gasabo", "Maize", "Rain expected", "Check drainage"])
    assert preview == "Agri-Menya alert for Gasabo (Maize): Rain expected Suggested action: Check drainage Reply STOP to unsubscribe."


@pytest.mark.parametrize("params", [
    ["Gasabo"],
    ["Gasabo", "Maize", "", "Action"],
    ["Gasabo", "Maize", "line1\nline2", "Action"],
    ["Gasabo", "Maize", "x" * 501, "Action"],
])
def test_template_parameters_are_validated(params):
    with pytest.raises(ValueError):
        validate_params("agrimenya_alert", params)


def test_kigali_template_falls_back_to_approved_english():
    with patch("app.services.whatsapp.templates.crud.get_whatsapp_template") as get_template:
        get_template.side_effect = [None, {"name": "agrimenya_alert", "language": "en", "status": "approved"}]
        result = approved_template("agrimenya_alert", "rw")
    assert result["language"] == "en"
    assert get_template.call_count == 2


def test_non_approved_template_is_unavailable():
    with patch("app.services.whatsapp.templates.crud.get_whatsapp_template", return_value={"status": "draft"}):
        assert approved_template("agrimenya_alert", "en") is None
