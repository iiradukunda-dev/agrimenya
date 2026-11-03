from contextlib import nullcontext
from unittest.mock import MagicMock, patch

import requests

import views.community as community


def test_community_auth_request_waits_for_backend_before_posting():
    response = MagicMock()
    response.content = b'{"access_token":"test"}'
    response.json.return_value = {"access_token": "test"}
    mock_st = _mock_streamlit({})

    with (
        patch.object(community, "st", mock_st),
        patch("utils.api_client.ensure_api_awake") as ensure_awake,
        patch.object(community, "request_api", return_value=response) as request,
    ):
        community._request("POST", "/community/login", payload={"email": "farmer@example.com"})

    ensure_awake.assert_called_once_with()
    request.assert_called_once()


def _mock_streamlit(query_params: dict) -> MagicMock:
    mock_st = MagicMock()
    mock_st.session_state = {}
    mock_st.query_params = query_params
    mock_st.button.return_value = False
    return mock_st


def test_community_translations_cover_every_supported_language():
    english_keys = set(community.COPY["en"])
    assert set(community.COPY["rw"]) == english_keys
    assert set(community.COPY["fr"]) == english_keys


def test_community_username_conflict_is_localized_in_french():
    response = requests.Response()
    response.status_code = 409
    response._content = b'{"detail":"That username is already in use"}'

    message = community._error_message(
        requests.HTTPError(response=response), "fr",
    )

    assert message == community.COPY["fr"]["profile_conflict"]


def test_google_sign_in_status_retries_after_transient_api_failure():
    response = MagicMock()
    response.json.return_value = {"enabled": True}
    community._google_sign_in_status.clear()
    with patch.object(
        community,
        "request_api",
        side_effect=[requests.Timeout(), response],
    ) as request:
        try:
            assert community._google_sign_in_enabled() is False
            assert community._google_sign_in_enabled() is True
            assert request.call_count == 2
        finally:
            community._google_sign_in_status.clear()


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
    mock_header.assert_called_once()
    assert mock_header.call_args.kwargs["subtitle"] == "Sign in to your account to continue."
    login_css = "".join(
        str(call.args[0])
        for call in mock_st.markdown.call_args_list
        if "<style>" in str(call.args[0])
    )
    assert "width: min(100%, 360px) !important" in login_css
    assert "border-radius: 999px !important" in login_css
    assert "background: linear-gradient(135deg, #3394ff, #0875d1) !important" in login_css
    assert "body:has(.st-key-ag_centralized_login_col) .st-key-ag_desktop_navbar" in login_css
    assert "body:has(.st-key-ag_centralized_login_col) .st-key-ag_mobile_navbar" in login_css
    assert "justify-content: flex-start !important" in login_css
    assert "margin: 0 auto !important" in login_css
    assert "@media (max-height: 900px)" in login_css
    assert "min-height: 1.45rem !important" in login_css
    assert "border: 1px solid #e1e7ef !important" in login_css
    assert 'content: "G"' in login_css
    assert "outline: none !important" in login_css
    assert "box-shadow: none !important" in login_css
    assert 'content: "Show"' not in login_css
    assert 'content: "Hide"' not in login_css
    assert not any(
        icon in login_css
        for icon in (
            'content: "♙"',
            'content: "♧"',
            'content: "✉"',
            'content: "▣"',
            'content: "⊕"',
            'content: "↻"',
            'content: "›"',
        )
    )
