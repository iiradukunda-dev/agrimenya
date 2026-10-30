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


def test_navbar_active_tab_is_sky_blue():
    """Verify active navbar tab uses sky blue styling."""
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
        assert "border: 2px solid #0875d1" in css_found
        assert "#0284c7" in css_found
        assert "#0369a1" in css_found


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


def test_desktop_dropdown_and_language_icons_remain_visible():
    """Keep the icon-only desktop menu and globe visible inside navbar columns."""
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
    assert "font-size: 1.35rem !important" in css_found
    assert "button [data-testid=\"stMarkdownContainer\"]" in css_found
    assert 'html body [data-testid="stAppViewContainer"] .st-key-ag_desktop_navbar' in css_found
    assert 'button:not([data-testid="stPopoverButton"])' in css_found
    assert '.st-key-ag_navbar [data-testid="stPopover"] button * {' not in css_found


def test_mobile_menu_button_shows_more_label():
    """Keep the hamburger menu identifiable as the More menu on small screens."""
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
    assert '.st-key-ag_mobile_navbar [data-testid="stPopover"] button::after' in css_found
    assert 'content: "More" !important' in css_found
    assert "min-width: 5.4rem !important" in css_found


def test_user_session_and_page_access_control():
    """Verify user session defaults to signed-in and unauthenticated access is gated."""
    from components.navbar import init_user_session, is_authenticated, check_page_access

    session = {}
    mock_st = MagicMock()
    mock_st.session_state = session

    with patch("components.navbar.st", mock_st):
        # 1. Default session should be authenticated
        init_user_session()
        assert session["authenticated"] is True
        assert session["user_profile"]["name"] == "Extension Officer"
        assert is_authenticated() is True

        # 2. Public pages (Home.py, 3_Dashboard.py) allowed when unauthenticated
        session["authenticated"] = False
        with patch("components.navbar.get_current_page_file", return_value="Home.py"):
            assert check_page_access() is True

        with patch("components.navbar.get_current_page_file", return_value="3_Dashboard.py"):
            assert check_page_access() is True

        # 3. Restricted page (e.g. 4_Zones.py) stopped when unauthenticated
        mock_st.stop.side_effect = RuntimeError("st_stopped")
        with patch("components.navbar.get_current_page_file", return_value="4_Zones.py"):
            try:
                check_page_access()
            except RuntimeError as e:
                assert "st_stopped" in str(e)
            assert mock_st.stop.called
