from contextlib import nullcontext
from unittest.mock import MagicMock, patch

import views.community as community


def _mock_streamlit(query_params: dict) -> MagicMock:
    mock_st = MagicMock()
    mock_st.session_state = {}
    mock_st.query_params = query_params
    mock_st.button.return_value = False
    return mock_st


@patch("views.community.get_current_language", return_value="en")
@patch("views.community._google_sign_in_enabled", return_value=False)
@patch("components.cards.centralized_login_container", return_value=nullcontext())
@patch("components.cards.login_card_header")
@patch("components.cards.security_trust_footer")
def test_email_verification_link_uses_backend_parameter_and_route(
    mock_footer, mock_header, _login_container, _google_enabled, _language
):
    query_params = {"community_verify_token": "verification-token"}
    mock_st = _mock_streamlit(query_params)
    with patch.object(community, "st", mock_st), patch.object(community, "_request") as request:
        community.render_community()

    request.assert_called_once_with(
        "POST", "/community/email/verify", payload={"token": "verification-token"}
    )
    assert "community_verify_token" not in query_params
    mock_st.success.assert_any_call(community.COPY["en"]["verify_success"])


@patch("views.community.get_current_language", return_value="en")
@patch("components.cards.centralized_login_container", return_value=nullcontext())
@patch("components.cards.login_card_header")
@patch("components.cards.security_trust_footer")
def test_password_reset_link_reads_backend_parameter(
    mock_footer, mock_header, _login_container, _language
):
    query_params = {"community_reset_token": "reset-token"}
    mock_st = _mock_streamlit(query_params)
    mock_st.text_input.side_effect = ["StrongPassword123", "StrongPassword123"]
    mock_st.form_submit_button.return_value = True
    with patch.object(community, "st", mock_st), patch.object(community, "_request") as request:
        community.render_community()

    request.assert_called_once_with(
        "POST",
        "/community/password/reset",
        payload={"token": "reset-token", "new_password": "StrongPassword123"},
    )


@patch("views.community.get_current_language", return_value="en")
@patch("views.community._google_sign_in_enabled", return_value=False)
@patch("components.cards.centralized_login_container", return_value=nullcontext())
@patch("components.cards.login_card_header")
@patch("components.cards.security_trust_footer")
def test_google_callback_exchange_includes_browser_binding(
    mock_footer, mock_header, _login_container, _google_enabled, _language
):
    query_params = {"community_google_code": "one-time-code"}
    mock_st = _mock_streamlit(query_params)
    mock_st.context.cookies.get.return_value = "browser-binding"
    with (
        patch.object(community, "st", mock_st),
        patch.object(community, "_request") as request,
        patch.object(community, "_store_community_session"),
    ):
        community.render_community()

    request.assert_called_once_with(
        "POST",
        "/community/auth/google/exchange",
        payload={"code": "one-time-code", "browser_binding": "browser-binding"},
    )
    assert "community_google_code" not in query_params


@patch("views.community.get_current_language", return_value="en")
@patch("components.cards.centralized_login_container", return_value=nullcontext())
@patch("components.cards.login_card_header")
@patch("components.cards.security_trust_footer")
def test_google_callback_without_browser_binding_requests_fresh_sign_in(
    mock_footer, mock_header, _login_container, _language
):
    query_params = {"community_google_code": "one-time-code"}
    mock_st = _mock_streamlit(query_params)
    mock_st.context.cookies.get.return_value = ""
    with patch.object(community, "st", mock_st), patch.object(community, "_request") as request:
        community.render_community()

    request.assert_not_called()
    assert "community_google_code" not in query_params
    mock_st.error.assert_any_call(community.COPY["en"]["google_error_expired"])


@patch("views.community._google_sign_in_enabled", return_value=True)
@patch("views.community.get_current_language", return_value="en")
@patch("components.cards.centralized_login_container", return_value=nullcontext())
@patch("components.cards.login_card_header")
@patch("components.cards.security_trust_footer")
def test_google_sign_in_starts_on_the_frontend_origin(
    mock_footer, mock_header, _login_container, _language, _google_enabled
):
    mock_st = _mock_streamlit({})
    with patch.object(community, "st", mock_st):
        community.render_community()

    mock_st.link_button.assert_called_once_with(
        community.COPY["en"]["google_signin"],
        "/community/auth/google",
        use_container_width=True,
    )
