"""Dual-island floating pill navigation matching reference design."""
import base64
from pathlib import Path
import streamlit as st
from components.ai_widget import render_floating_ai_widget
from utils.i18n import render_language_selector, t
from utils.pwa import render_pwa_support


def _get_avatar_base64() -> str:
    """Load user profile avatar as base64 data URL."""
    for path in [
        Path(__file__).parent.parent / "assets" / "avatar.jpg",
        Path(__file__).parent.parent / "static" / "avatar.jpg",
        Path("frontend/assets/avatar.jpg"),
        Path("frontend/static/avatar.jpg"),
        Path("static/avatar.jpg"),
    ]:
        if path.exists():
            try:
                data = base64.b64encode(path.read_bytes()).decode("utf-8")
                return f"data:image/jpeg;base64,{data}"
            except Exception:
                pass
    return ""


def render_navbar() -> None:
    """Render the dual-island floating pill navigation."""
    avatar_data_url = _get_avatar_base64()

    st.markdown("""
      <style>
      @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
      [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

      /* Top Navbar Row Alignment */
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) {
        align-items: center !important;
        padding: 0.5rem 0 0.8rem 0 !important;
      }

      /* =========================================================
         LEFT ISLAND: Floating White Pill Capsule for Nav Links
         ========================================================= */
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="column"]:first-child [data-testid="stHorizontalBlock"],
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="stColumn"]:first-child [data-testid="stHorizontalBlock"] {
        background: #ffffff !important;
        border-radius: 9999px !important;
        padding: 5px 8px !important;
        box-shadow: 0 4px 22px rgba(0, 0, 0, 0.06), 0 1px 4px rgba(0, 0, 0, 0.03) !important;
        border: 1px solid rgba(0, 0, 0, 0.08) !important;
        display: inline-flex !important;
        flex-direction: row !important;
        align-items: center !important;
        width: fit-content !important;
        max-width: 100% !important;
        gap: 4px !important;
      }

      /* Ensure each sub-column in left island shrinks to its natural item width */
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="column"]:first-child [data-testid="stHorizontalBlock"] [data-testid="column"],
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="stColumn"]:first-child [data-testid="stHorizontalBlock"] [data-testid="stColumn"] {
        flex: 0 0 auto !important;
        width: auto !important;
        min-width: unset !important;
        padding: 0 !important;
      }

      /* General styling for nav links inside the left pill (Overview, Zones, Decisions) */
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="column"]:first-child [data-testid="stPageLink-NavLink"],
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="stColumn"]:first-child [data-testid="stPageLink-NavLink"] {
        background: transparent !important;
        border: none !important;
        border-radius: 9999px !important;
        min-height: 2.35rem !important;
        padding: 0.45rem 1.15rem !important;
        box-shadow: none !important;
        justify-content: center !important;
        align-items: center !important;
        text-align: center !important;
        display: inline-flex !important;
        text-decoration: none !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
      }
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="column"]:first-child [data-testid="stPageLink-NavLink"] p,
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="stColumn"]:first-child [data-testid="stPageLink-NavLink"] p {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        color: #383431 !important;
        letter-spacing: -0.01em !important;
        margin: 0 !important;
        transition: color 0.2s ease !important;
      }
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="column"]:first-child [data-testid="stPageLink-NavLink"]:hover {
        background: rgba(126, 67, 37, 0.06) !important;
        transform: none !important;
      }
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="column"]:first-child [data-testid="stPageLink-NavLink"]:hover p {
        color: #7e4325 !important;
      }

      /* ACTIVE NAV LINK: Rich Terracotta Capsule Pill with White Text and Outline Home Icon
         Matches:
         - The Home link (by href="/" or href="" or href*="Home")
         - Any link with [aria-current="page"]
      */
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="stPageLink-NavLink"]:has(a[href="/"]),
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="stPageLink-NavLink"]:has(a[href=""]),
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="stPageLink-NavLink"]:has(a[href$="/Home"]),
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="stPageLink-NavLink"]:has(a[href*="Home.py"]),
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="column"]:first-child [data-testid="stHorizontalBlock"] [data-testid="column"]:first-child [data-testid="stPageLink-NavLink"],
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="stColumn"]:first-child [data-testid="stHorizontalBlock"] [data-testid="stColumn"]:first-child [data-testid="stPageLink-NavLink"],
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="column"]:first-child [data-testid="stPageLink-NavLink"][aria-current="page"],
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="column"]:first-child [data-testid="stPageLink-NavLink"]:has([aria-current="page"]) {
        background: #7e4325 !important;
        border: none !important;
        border-radius: 9999px !important;
        padding: 0.45rem 1.35rem !important;
        box-shadow: 0 2px 10px rgba(126, 67, 37, 0.28) !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 0.45rem !important;
      }
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="stPageLink-NavLink"]:has(a[href="/"]) p,
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="stPageLink-NavLink"]:has(a[href=""]) p,
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="stPageLink-NavLink"]:has(a[href$="/Home"]) p,
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="stPageLink-NavLink"]:has(a[href*="Home.py"]) p,
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="column"]:first-child [data-testid="stHorizontalBlock"] [data-testid="column"]:first-child [data-testid="stPageLink-NavLink"] p,
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="stColumn"]:first-child [data-testid="stHorizontalBlock"] [data-testid="stColumn"]:first-child [data-testid="stPageLink-NavLink"] p,
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="column"]:first-child [data-testid="stPageLink-NavLink"][aria-current="page"] p,
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="column"]:first-child [data-testid="stPageLink-NavLink"]:has([aria-current="page"]) p {
        color: #ffffff !important;
        font-weight: 600 !important;
        text-shadow: none !important;
      }
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="stPageLink-NavLink"]:has(a[href="/"]):hover,
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="stPageLink-NavLink"]:has(a[href=""]):hover,
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="stPageLink-NavLink"]:has(a[href$="/Home"]):hover,
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="stPageLink-NavLink"]:has(a[href*="Home.py"]):hover,
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="column"]:first-child [data-testid="stHorizontalBlock"] [data-testid="column"]:first-child [data-testid="stPageLink-NavLink"]:hover,
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="stColumn"]:first-child [data-testid="stHorizontalBlock"] [data-testid="stColumn"]:first-child [data-testid="stPageLink-NavLink"]:hover,
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="column"]:first-child [data-testid="stPageLink-NavLink"][aria-current="page"]:hover {
        background: #6d391e !important;
        transform: none !important;
      }
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="stPageLink-NavLink"]:has(a[href="/"]):hover p,
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="stPageLink-NavLink"]:has(a[href=""]):hover p,
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="stPageLink-NavLink"]:has(a[href$="/Home"]):hover p,
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="stPageLink-NavLink"]:has(a[href*="Home.py"]):hover p,
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="column"]:first-child [data-testid="stHorizontalBlock"] [data-testid="column"]:first-child [data-testid="stPageLink-NavLink"]:hover p,
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="stColumn"]:first-child [data-testid="stHorizontalBlock"] [data-testid="stColumn"]:first-child [data-testid="stPageLink-NavLink"]:hover p,
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="column"]:first-child [data-testid="stPageLink-NavLink"][aria-current="page"]:hover p {
        color: #ffffff !important;
      }

      /* Outline Home Vector Icon on Active Button */
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="stPageLink-NavLink"]:has(a[href="/"])::before,
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="stPageLink-NavLink"]:has(a[href=""])::before,
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="stPageLink-NavLink"]:has(a[href$="/Home"])::before,
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="stPageLink-NavLink"]:has(a[href*="Home.py"])::before,
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="column"]:first-child [data-testid="stHorizontalBlock"] [data-testid="column"]:first-child [data-testid="stPageLink-NavLink"]::before,
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="stColumn"]:first-child [data-testid="stHorizontalBlock"] [data-testid="stColumn"]:first-child [data-testid="stPageLink-NavLink"]::before,
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="column"]:first-child [data-testid="stPageLink-NavLink"][aria-current="page"]::before {
        content: "" !important;
        display: inline-block !important;
        width: 17px !important;
        height: 17px !important;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%23ffffff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 2.5L3 9.5V19.5a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V9.5L12 2.5z'%3E%3C/path%3E%3Ccircle cx='12' cy='14.5' r='2.5'%3E%3C/circle%3E%3C/svg%3E") !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        background-size: contain !important;
        margin-right: 0.35rem !important;
      }

      /* More Popover Button inside the Left Island Pill */
      div[data-testid="stPopover"] button {
        background: transparent !important;
        border: none !important;
        border-radius: 9999px !important;
        min-height: 2.35rem !important;
        padding: 0.45rem 1.15rem !important;
        box-shadow: none !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
      }
      div[data-testid="stPopover"] button::before,
      div[data-testid="stPopover"] button::after {
        display: none !important;
        content: none !important;
      }
      div[data-testid="stPopover"] button p {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        color: #383431 !important;
        letter-spacing: -0.01em !important;
        margin: 0 !important;
        visibility: visible !important;
        opacity: 1 !important;
        display: inline-block !important;
        transition: color 0.2s ease !important;
      }
      div[data-testid="stPopover"] button:hover {
        background: rgba(126, 67, 37, 0.06) !important;
        transform: none !important;
      }
      div[data-testid="stPopover"] button:hover p {
        color: #7e4325 !important;
      }
      /* Hide default expand chevron in More popover button */
      div[data-testid="stPopover"] button [data-testid="stIconMaterial"],
      div[data-testid="stPopover"] button svg,
      div[data-testid="stPopover"] button .material-symbols-rounded {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        height: 0 !important;
      }

      /* Popover Dropdown Styling */
      div[data-testid="stPopoverBody"] {
        max-height: 520px !important;
        border-radius: 16px !important;
        border: 1px solid rgba(0, 0, 0, 0.08) !important;
        background: #ffffff !important;
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.12), 0 4px 12px rgba(0, 0, 0, 0.06) !important;
        padding: 0.75rem 0.65rem !important;
      }
      div[data-testid="stPopoverBody"] [data-testid="stPageLink-NavLink"] {
        min-height: 2.2rem !important;
        padding: 0.4rem 0.85rem !important;
        margin: 0.15rem 0 !important;
        background: #fbf9f7 !important;
        border: 1px solid rgba(0, 0, 0, 0.04) !important;
        border-radius: 10px !important;
        justify-content: flex-start !important;
      }
      div[data-testid="stPopoverBody"] [data-testid="stPageLink-NavLink"] p {
        font-size: 0.86rem !important;
        font-weight: 600 !important;
        color: #2d2926 !important;
      }
      div[data-testid="stPopoverBody"] [data-testid="stPageLink-NavLink"]:hover {
        background: rgba(126, 67, 37, 0.08) !important;
        border-color: rgba(126, 67, 37, 0.25) !important;
      }
      div[data-testid="stPopoverBody"] [data-testid="stPageLink-NavLink"]:hover p {
        color: #7e4325 !important;
      }
      div[data-testid="stPopoverBody"] [data-testid="stCaptionContainer"] p {
        color: #8c827a !important;
        font-weight: 700 !important;
        font-size: 0.72rem !important;
        letter-spacing: 0.06em !important;
      }

      /* Hide any unwanted nested icons in links */
      [data-testid="stPageLink-NavLink"] span[data-testid="stIconMaterial"],
      [data-testid="stPageLink-NavLink"] svg:not([class*="custom"]),
      [data-testid="stPageLink-NavLink"] i {
        display: none !important;
      }

      /* =========================================================
         RIGHT ISLAND: User Avatar, +pro badge, Sign In, Language
         ========================================================= */
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="column"]:last-child [data-testid="stHorizontalBlock"],
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="stColumn"]:last-child [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: flex-end !important;
        gap: 14px !important;
        width: 100% !important;
      }

      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="column"]:last-child [data-testid="stHorizontalBlock"] [data-testid="column"],
      [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) [data-testid="stColumn"]:last-child [data-testid="stHorizontalBlock"] [data-testid="stColumn"] {
        flex: 0 0 auto !important;
        width: auto !important;
        min-width: unset !important;
        padding: 0 !important;
      }

      /* Sign In Button: Crisp Outline Capsule */
      [data-testid="stPageLink-NavLink"]:has(a[href*="Admin"]) {
        background: #ffffff !important;
        border: 1.5px solid #d5cfc9 !important;
        border-radius: 9999px !important;
        min-height: 2.35rem !important;
        padding: 0.45rem 1.35rem !important;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04) !important;
        justify-content: center !important;
        text-align: center !important;
        display: inline-flex !important;
        align-items: center !important;
        text-decoration: none !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
      }
      [data-testid="stPageLink-NavLink"]:has(a[href*="Admin"]) p {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        color: #2b2724 !important;
        letter-spacing: -0.01em !important;
        margin: 0 !important;
        transition: color 0.2s ease !important;
      }
      [data-testid="stPageLink-NavLink"]:has(a[href*="Admin"]):hover {
        border-color: #7e4325 !important;
        background: #ffffff !important;
        box-shadow: 0 2px 8px rgba(126, 67, 37, 0.15) !important;
        transform: none !important;
      }
      [data-testid="stPageLink-NavLink"]:has(a[href*="Admin"]):hover p {
        color: #7e4325 !important;
      }

      /* Language Selector Button in Right Island ONLY */
      .st-key-lang_cycle_btn button {
        background: #ffffff !important;
        border: 1.5px solid #d5cfc9 !important;
        border-radius: 50% !important;
        min-height: 2.35rem !important;
        width: 2.35rem !important;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04) !important;
        transition: all 0.2s ease !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0 !important;
        position: relative !important;
      }
      .st-key-lang_cycle_btn button:hover {
        border-color: #7e4325 !important;
        box-shadow: 0 2px 8px rgba(126, 67, 37, 0.15) !important;
        transform: none !important;
      }
      .st-key-lang_cycle_btn button * {
        font-size: 0 !important;
        color: transparent !important;
        line-height: 0 !important;
        max-width: 0 !important;
        max-height: 0 !important;
        overflow: hidden !important;
        visibility: hidden !important;
      }
      .st-key-lang_cycle_btn button::before {
        content: '' !important;
        display: block !important;
        width: 17px !important;
        height: 17px !important;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='%232b2724' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'%3E%3C/circle%3E%3Cline x1='2' y1='12' x2='22' y2='12'%3E%3C/line%3E%3Cpath d='M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z'%3E%3C/path%3E%3C/svg%3E") !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        background-size: contain !important;
        pointer-events: none !important;
        transition: transform 0.2s ease !important;
      }
      .st-key-lang_cycle_btn button:hover::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='%237e4325' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'%3E%3C/circle%3E%3Cline x1='2' y1='12' x2='22' y2='12'%3E%3C/line%3E%3Cpath d='M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z'%3E%3C/path%3E%3C/svg%3E") !important;
        transform: rotate(15deg) scale(1.08) !important;
      }

      /* Subtle divider */
      .ag-nav-rule {
        border: 0;
        height: 1px;
        background: rgba(0, 0, 0, 0.05);
        margin: 0.4rem 0 1.2rem;
      }

      @media(max-width:900px) {
        [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink-NavLink"]) {
          flex-wrap: wrap !important;
          gap: 0.75rem !important;
        }
      }
      </style>
    """, unsafe_allow_html=True)

    col_nav, col_right = st.columns([3.7, 1.8], vertical_alignment="center", gap="medium")

    with col_nav:
        c_home, c_overview, c_zones, c_decide, c_more = st.columns(
            [1.15, 1.1, 0.95, 1.15, 0.9], vertical_alignment="center"
        )
        with c_home:
            st.page_link("Home.py", label=t("nav.home", "Home"))
        with c_overview:
            st.page_link("pages/3_Dashboard.py", label=t("nav.overview", "Overview"))
        with c_zones:
            st.page_link("pages/4_Zones.py", label=t("nav.zones", "Zones"))
        with c_decide:
            st.page_link("pages/6_Decision_Making.py", label=t("nav.decisions", "Decisions"))
        with c_more:
            with st.popover(t("nav.more", "More"), width="stretch"):
                st.caption(t("nav.operations_tools", "OPERATIONS & TOOLS"))
                st.page_link("pages/8_Planning.py", label=t("nav.planning", "Seasonal planning"))
                st.page_link("pages/9_Communication.py", label=t("nav.comms", "Field alerts & comms"))
                st.page_link("pages/5_Segmentation.py", label=t("nav.segmentation", "Zone segmentation"))
                st.page_link("pages/7_AI_Assistant.py", label=t("nav.ai_assistant", "AI assistant"))
                st.divider()
                st.caption(t("nav.platform_community", "PLATFORM & COMMUNITY"))
                st.page_link("pages/10_Admin.py", label=t("nav.admin", "Administration"))
                st.page_link("pages/99_Showcase.py", label=t("nav.data_guide", "Data guide"))
                st.page_link("pages/12_Community.py", label=t("nav.community", "Farmer community"))
                st.page_link("pages/1_About.py", label=t("nav.about", "About agrimenya"))
                st.page_link("pages/11_Contact.py", label=t("nav.contact", "Feedback & support"))
                st.markdown(
                    f'<a href="/app/static/offline.html" target="_blank" style="text-decoration:none;display:flex;align-items:center;gap:0.4rem;padding:0.4rem 0.75rem;border-radius:8px;font-size:0.85rem;font-weight:600;color:#7e4325;background:rgba(126,67,37,0.06);border:1px solid rgba(126,67,37,0.18);margin-top:0.3rem;"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#7e4325" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"></path></svg> {t("nav.offline_hub", "Offline Field Hub")}</a>',
                    unsafe_allow_html=True,
                )

    with col_right:
        c_user, c_signin, c_lang = st.columns([1.35, 1.1, 0.45], vertical_alignment="center")
        with c_user:
            st.markdown(
                f"""<div style="display:inline-flex;align-items:center;gap:10px;">
                    <img src="{avatar_data_url}" style="width:36px;height:36px;border-radius:50%;object-fit:cover;border:1.5px solid #eae5df;box-shadow:0 2px 6px rgba(0,0,0,0.06);" alt="Profile" />
                    <span style="font-family:'Plus Jakarta Sans',sans-serif;font-size:0.88rem;font-weight:600;color:#2b2724;display:inline-flex;align-items:center;gap:4px;">
                        +pro
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2b2724" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="10"></circle>
                            <path d="M12 6v12M15 9.5a2.5 2.5 0 0 0-5 0c0 4 5 2 5 6a2.5 2.5 0 0 1-5 0"></path>
                        </svg>
                    </span>
                </div>""",
                unsafe_allow_html=True,
            )
        with c_signin:
            st.page_link("pages/10_Admin.py", label=t("nav.signin", "Sign In"))
        with c_lang:
            render_language_selector(sidebar=False)

    st.markdown('<hr class="ag-nav-rule">', unsafe_allow_html=True)
    render_floating_ai_widget()
    render_pwa_support()
