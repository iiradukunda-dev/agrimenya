"""Unit tests verifying navbar and tabs styling integrity (no black backgrounds)."""
from unittest.mock import MagicMock, patch
import pytest


def test_navbar_css_has_no_black_background_on_buttons():
    """Verify that navbar CSS explicitly sets transparent backgrounds and no black backgrounds."""
    from components.navbar import render_navbar

    mock_st = MagicMock()
    mock_st.columns.side_effect = [
        [MagicMock() for _ in range(7)],
        [MagicMock() for _ in range(2)],
    ]
    with patch("components.navbar.st", mock_st), \
         patch("components.navbar.render_floating_ai_widget"), \
         patch("components.navbar.render_pwa_support"), \
         patch("components.navbar.render_language_selector"):
        
        render_navbar()

        # Find the st.markdown call that injected the <style>
        css_found = ""
        for call_args in mock_st.markdown.call_args_list:
            arg = str(call_args[0][0])
            if "<style>" in arg:
                css_found += arg

        assert css_found, "Navbar CSS was not injected"
        # Ensure #081a26 is NOT applied to navbar buttons
        assert ".st-key-ag_navbar [data-testid=\"stHorizontalBlock\"] button {\n      background: #081a26" not in css_found
        assert "background: #081a26 !important" not in css_found
        # Ensure transparent background is enforced
        assert "background: transparent !important" in css_found
        # Ensure st.tabs light styles are included
        assert '[data-testid="stTabs"]' in css_found


def test_theme_excludes_tabs_from_card_button_styles():
    """Verify theme.py excludes role='tab' from dark card button backgrounds."""
    from utils.theme import load_theme

    mock_st = MagicMock()
    with patch("utils.theme.st", mock_st):
        load_theme()

        html_calls = [str(call[0][0]) for call in mock_st.html.call_args_list]
        combined_css = "".join(html_calls)

        assert combined_css, "Theme CSS was not injected"
        # Verify card buttons exclude role='tab'
        assert ':not([role="tab"])' in combined_css
        # Verify st.tabs has dedicated light styling
        assert '[data-testid="stTabs"]' in combined_css


def test_navbar_active_tab_is_blue_outline_and_account_has_no_circle():
    """Verify the active navbar item is outlined and the account icon has no circle."""
    from components.navbar import render_navbar

    mock_st = MagicMock()
    mock_st.columns.side_effect = [
        [MagicMock() for _ in range(7)],
        [MagicMock() for _ in range(2)],
    ]
    with patch("components.navbar.st", mock_st), \
         patch("components.navbar.render_floating_ai_widget"), \
         patch("components.navbar.render_pwa_support"), \
         patch("components.navbar.render_language_selector"):
        
        render_navbar()

        css_found = "".join([str(call[0][0]) for call in mock_st.markdown.call_args_list if "<style>" in str(call[0][0])])
        assert 'a[aria-current="page"]' in css_found
        assert "border: 2px solid #0875d1 !important;" in css_found
        assert "background: transparent !important;" in css_found
        assert "#0284c7" in css_found
        assert "#0369a1" in css_found
        assert "border: 2px solid #0875d1 !important" in css_found
        assert "background: #ffffff !important" in css_found
        assert "color: #0875d1 !important" in css_found
        assert "border-radius: 0 !important" in css_found
        assert "background: transparent !important" in css_found
        assert "width: min(100%, 820px) !important" in css_found
        assert "viewBox='0 0 24 24' fill='%236b7280'" in css_found
        account_hover = (
            'html body [data-testid="stAppViewContainer"] .st-key-ag_desktop_navbar '
            '.st-key-ag_navbar [data-testid="stHorizontalBlock"] '
            '[data-testid="stPopover"] button:hover'
        )
        assert account_hover in css_found
        assert "transform: none !important" in css_found
        account_hover_icon = f"{account_hover}::before"
        assert account_hover_icon in css_found
        assert "fill='%236b7280'" in css_found
        assert "transition: none !important" in css_found


def test_navbar_account_and_language_controls_match_the_visual_layout():
    from components.navbar import render_navbar

    mock_st = MagicMock()
    mock_st.session_state = {"authenticated": True}
    mock_st.columns.side_effect = [
        [MagicMock() for _ in range(7)],
        [MagicMock() for _ in range(2)],
    ]
    with patch("components.navbar.st", mock_st), \
         patch("components.navbar.render_floating_ai_widget"), \
         patch("components.navbar.render_pwa_support"), \
         patch("components.navbar.render_language_selector"):
        render_navbar()

    css = "".join(
        str(call[0][0])
        for call in mock_st.markdown.call_args_list
        if "<style>" in str(call[0][0])
    )
    assert '[data-testid="stPopoverButton"]' in css
    assert "width: min(100%, 820px) !important;" in css
    assert ".st-key-lang_cycle_btn button" in css
    assert "position: sticky !important;" in css
    assert "max-width: 840px" in css
    assert any(
        call.args[0] == " " and call.kwargs.get("help") == "More"
        for call in mock_st.popover.call_args_list
    )


def test_mobile_menu_button_shows_only_the_hamburger():
    """Keep the mobile menu control compact with no extra label."""
    from components.navbar import render_navbar

    mock_st = MagicMock()
    mock_st.columns.side_effect = [
        [MagicMock() for _ in range(7)],
        [MagicMock() for _ in range(2)],
    ]
    with patch("components.navbar.st", mock_st), \
         patch("components.navbar.render_floating_ai_widget"), \
         patch("components.navbar.render_pwa_support"), \
         patch("components.navbar.render_language_selector"):
        render_navbar()

    css_found = "".join(
        str(call[0][0])
        for call in mock_st.markdown.call_args_list
        if "<style>" in str(call[0][0])
    )
    assert '.st-key-ag_mobile_navbar [data-testid="stPopover"] button::after' not in css_found
    assert "min-width: 2.5rem !important" in css_found
    assert "left: 50% !important" in css_found


def test_mobile_menu_links_have_no_background_boxes():
    """Verify mobile popover links render without individual background boxes."""
    from components.navbar import render_navbar

    mock_st = MagicMock()
    mock_st.columns.side_effect = [
        [MagicMock() for _ in range(7)],
        [MagicMock() for _ in range(2)],
    ]
    with patch("components.navbar.st", mock_st), \
         patch("components.navbar.render_floating_ai_widget"), \
         patch("components.navbar.render_pwa_support"), \
         patch("components.navbar.render_language_selector"):
        render_navbar()

        css_found = "".join(
            str(call[0][0])
            for call in mock_st.markdown.call_args_list
            if "<style>" in str(call[0][0])
        )

        assert '[data-testid="stPopoverBody"] [data-testid="stPageLink-NavLink"]' in css_found
        assert 'body:has(.st-key-ag_mobile_navbar [data-testid="stPopover"] button[aria-expanded="true"])' in css_found
        assert "background: transparent !important" in css_found
        assert "width: min(14rem, calc(100vw - 2rem)) !important" in css_found
        assert "background: #f4f8fa !important" not in css_found
        assert "div[data-testid=\"stPopoverBody\"] [data-testid=\"stPageLink-NavLink\"]:hover" in css_found


def test_desktop_menu_hides_default_expand_icon_and_language_icon_remains_visible():
    """Keep the custom menu icon and globe while hiding Streamlit's expand icon."""
    from components.navbar import render_navbar

    mock_st = MagicMock()
    mock_st.columns.side_effect = [
        [MagicMock() for _ in range(7)],
        [MagicMock() for _ in range(2)],
    ]
    with patch("components.navbar.st", mock_st), \
         patch("components.navbar.render_floating_ai_widget"), \
         patch("components.navbar.render_pwa_support"), \
         patch("components.navbar.render_language_selector"):
        render_navbar()

    css_found = "".join(
        str(call[0][0])
        for call in mock_st.markdown.call_args_list
        if "<style>" in str(call[0][0])
    )
    desktop_popover_call = mock_st.popover.call_args_list[0]
    assert desktop_popover_call.args[0] == " "
    assert desktop_popover_call.kwargs["help"] == "More"
    assert '[data-testid="stPopover"] button p' in css_found
    assert "min-width: 2.35rem !important" in css_found
    assert "position: absolute !important" in css_found
    assert "background: rgba(2, 132, 199, 0.08) !important" in css_found
    assert "border: 1px solid rgba(2, 132, 199, 0.24) !important" in css_found
    assert "display: none !important;" in css_found
    assert (
        '.st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stPopover"] '
        'button [data-testid="stIconMaterial"] {\n        display: none !important;'
    ) in css_found
    assert "button [data-testid=\"stMarkdownContainer\"]" in css_found
    assert 'html body [data-testid="stAppViewContainer"] .st-key-ag_desktop_navbar' in css_found
    assert '.st-key-ag_navbar [data-testid="column"]:has(.st-key-lang_cycle_btn)' in css_found
    assert '.st-key-ag_mobile_navbar [data-testid="column"]:has(.st-key-lang_cycle_mobile_btn)' in css_found
    assert "align-self: center !important" in css_found
    assert ".st-key-ag_mobile_navbar .st-key-lang_cycle_mobile_btn button" in css_found
    assert "height: 42px !important" in css_found
    assert "height: 2.35rem !important" in css_found
    assert "body:has(.st-key-ag_desktop_navbar [data-testid=\"stPopover\"] button[aria-expanded=\"true\"]) [data-testid=\"stPopoverBody\"]" in css_found
    assert "width: min(14rem, calc(100vw - 2rem)) !important" in css_found
    assert 'button:not([data-testid="stPopoverButton"])' in css_found
    assert '.st-key-ag_navbar [data-testid="stPopover"] button * {' not in css_found


def test_user_session_and_page_access_control():
    """Verify anonymous visitors can use public pages and restricted pages redirect home."""
    from components.navbar import init_user_session, is_authenticated, check_page_access

    session = {}
    mock_st = MagicMock()
    mock_st.session_state = session

    with patch("components.navbar.st", mock_st):
        # 1. New sessions remain anonymous until a real login succeeds.
        init_user_session()
        assert session["authenticated"] is False
        assert session["user_profile"] == {}
        assert is_authenticated() is False

        # 2. Public pages (Home.py, 3_Dashboard.py) allowed when unauthenticated
        session["authenticated"] = False
        with patch("components.navbar.get_current_page_file", return_value="Home.py"):
            assert check_page_access() is True

        with patch("components.navbar.get_current_page_file", return_value="3_Dashboard.py"):
            assert check_page_access() is True

        with patch("components.navbar.get_current_page_file", return_value="dashboard.py"):
            assert check_page_access() is True

        with patch("components.navbar.get_current_page_file", return_value="12_Community.py"):
            assert check_page_access() is True

        # 3. Restricted pages immediately return unauthenticated visitors to Home.
        with patch("components.navbar.get_current_page_file", return_value="4_Zones.py"):
            assert check_page_access() is False
            mock_st.switch_page.assert_called_once_with("Home.py")
            mock_st.markdown.assert_not_called()
            mock_st.button.assert_not_called()
            mock_st.page_link.assert_not_called()


def test_logged_out_account_link_is_in_mobile_menu_not_standalone_navbar():
    from components.navbar import render_navbar

    mock_st = MagicMock()
    mock_st.columns.side_effect = [
        [MagicMock() for _ in range(7)],
        [MagicMock() for _ in range(2)],
    ]
    with patch("components.navbar.st", mock_st), \
         patch("components.navbar.is_authenticated", return_value=False), \
         patch("components.navbar.init_user_session"), \
         patch("components.navbar.check_page_access"), \
         patch("components.navbar._render_api_warmup"), \
         patch("components.navbar.render_floating_ai_widget"), \
         patch("components.navbar.render_pwa_support"), \
         patch("components.navbar.render_language_selector"):
        render_navbar()

    css = "".join(
        str(call.args[0])
        for call in mock_st.markdown.call_args_list
        if "<style>" in str(call.args[0])
    )
    account_links = [
        call for call in mock_st.page_link.call_args_list
        if call.args and call.args[0] == "pages/12_Community.py"
    ]
    assert account_links
    assert all(call.kwargs.get("icon") == ":material/account_circle:" for call in account_links)
    assert len(account_links) == 2
    assert 'a[href*="Community"] [data-testid="stIconMaterial"]' in css
    assert '[data-testid="stPageLink-NavLink"]:not(:has(a[href*="Community"]))' in css
    assert '.st-key-ag_mobile_navbar [data-testid="stPageLink"]:has(a[href*="Community"])' in css
    assert ".st-key-ag_mobile_account" not in css
    assert not any(
        call.kwargs.get("key") == "ag_mobile_account"
        for call in mock_st.container.call_args_list
    )
    mock_st.columns.assert_any_call([1, 1], vertical_alignment="center")
    assert 'a[href*="Community"]:hover' in css
    assert "transform: none !important" in css
