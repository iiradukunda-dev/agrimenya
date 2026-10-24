"""Unified centered floating pill navigation tailored to the agrimenya theme."""
import streamlit as st
from components.ai_widget import render_floating_ai_widget
from utils.i18n import render_language_selector, t
from utils.pwa import render_pwa_support


def render_navbar() -> None:
    """Render the unified centered floating pill navigation styled with agrimenya theme tokens."""
    st.markdown("""
      <style>
      @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
      [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

      /* =========================================================
         AGRIMENYA CENTERED FLOATING NAVBAR
         ========================================================= */
      /* Outer Container: Centered horizontally on the page */
      .st-key-ag_navbar,
      .st-key-ag_navbar > div {
        display: flex !important;
        flex-direction: row !important;
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
        max-width: 100% !important;
        margin: 0.25rem auto 0.75rem auto !important;
        padding: 0 !important;
      }

      /* The Unified Floating Pill Capsule */
      .st-key-ag_navbar [data-testid="stHorizontalBlock"],
      [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) {
        display: inline-flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        justify-content: center !important;
        width: auto !important;
        max-width: fit-content !important;
        margin: 0.2rem auto 0.6rem auto !important;
        padding: 6px 16px !important;
        background: #ffffff !important;
        border-radius: 9999px !important;
        border: 1px solid rgba(2, 132, 199, 0.22) !important;
        box-shadow: 0 8px 30px rgba(2, 132, 199, 0.14), 0 2px 8px rgba(0, 0, 0, 0.04) !important;
        gap: 6px !important;
      }

      /* Ensure each sub-column shrinks to content width and aligns center */
      .st-key-ag_navbar [data-testid="stHorizontalBlock"] > [data-testid="column"],
      .st-key-ag_navbar [data-testid="stHorizontalBlock"] > [data-testid="stColumn"],
      [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) > [data-testid="column"],
      [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) > [data-testid="stColumn"] {
        display: inline-flex !important;
        flex: 0 0 auto !important;
        width: auto !important;
        min-width: unset !important;
        max-width: unset !important;
        margin: 0 !important;
        padding: 0 !important;
        align-items: center !important;
        justify-content: center !important;
      }

      /* Base nav links inside the pill (Overview, Zones, Decisions) */
      .st-key-ag_navbar [data-testid="stPageLink"],
      .st-key-ag_navbar [data-testid="stPageLink-NavLink"],
      .st-key-ag_navbar a[data-testid="stPageLink-NavLink"],
      .st-key-ag_navbar [data-testid="stPageLink"] a,
      [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) [data-testid="stPageLink-NavLink"] {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        border-radius: 9999px !important;
        height: 2.35rem !important;
        min-height: 2.35rem !important;
        padding: 0.45rem 1.15rem !important;
        box-shadow: none !important;
        justify-content: center !important;
        align-items: center !important;
        text-align: center !important;
        display: inline-flex !important;
        text-decoration: none !important;
        line-height: 1 !important;
        margin: 0 !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
      }
      .st-key-ag_navbar [data-testid="stPageLink"] p,
      .st-key-ag_navbar [data-testid="stPageLink-NavLink"] p,
      .st-key-ag_navbar a[data-testid="stPageLink-NavLink"] p,
      .st-key-ag_navbar [data-testid="stPageLink"] a p,
      [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) [data-testid="stPageLink-NavLink"] p {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        color: #0a1f26 !important;
        letter-spacing: -0.01em !important;
        margin: 0 !important;
        line-height: 1 !important;
        transition: color 0.2s ease !important;
      }
      .st-key-ag_navbar [data-testid="stPageLink"]:hover,
      .st-key-ag_navbar [data-testid="stPageLink-NavLink"]:hover,
      .st-key-ag_navbar a[data-testid="stPageLink-NavLink"]:hover,
      .st-key-ag_navbar [data-testid="stPageLink"] a:hover,
      [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) [data-testid="stPageLink-NavLink"]:hover {
        background: rgba(2, 132, 199, 0.08) !important;
        background-color: rgba(2, 132, 199, 0.08) !important;
        transform: none !important;
      }
      .st-key-ag_navbar [data-testid="stPageLink"]:hover p,
      .st-key-ag_navbar [data-testid="stPageLink-NavLink"]:hover p,
      .st-key-ag_navbar a[data-testid="stPageLink-NavLink"]:hover p,
      .st-key-ag_navbar [data-testid="stPageLink"] a:hover p,
      [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) [data-testid="stPageLink-NavLink"]:hover p {
        color: #0284c7 !important;
      }

      /* ACTIVE NAV LINK: Agrimenya Cyan Gradient Pill */
      .st-key-ag_navbar [data-testid="column"]:first-child [data-testid="stPageLink"],
      .st-key-ag_navbar [data-testid="column"]:first-child [data-testid="stPageLink-NavLink"],
      .st-key-ag_navbar [data-testid="column"]:first-child a,
      .st-key-ag_navbar a[href="Home"],
      .st-key-ag_navbar a[href="/"],
      .st-key-ag_navbar a[href=""],
      .st-key-ag_navbar a[aria-current="page"],
      .st-key-ag_navbar [data-testid="stPageLink"][aria-current="page"],
      .st-key-ag_navbar [data-testid="stPageLink-NavLink"][aria-current="page"] {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
        background-color: #0284c7 !important;
        border: none !important;
        border-radius: 9999px !important;
        height: 2.35rem !important;
        min-height: 2.35rem !important;
        padding: 0.45rem 1.35rem !important;
        box-shadow: 0 4px 14px rgba(2, 132, 199, 0.35) !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 0.45rem !important;
      }
      .st-key-ag_navbar [data-testid="column"]:first-child [data-testid="stPageLink"] p,
      .st-key-ag_navbar [data-testid="column"]:first-child [data-testid="stPageLink-NavLink"] p,
      .st-key-ag_navbar [data-testid="column"]:first-child a p,
      .st-key-ag_navbar a[href="Home"] p,
      .st-key-ag_navbar a[href="/"] p,
      .st-key-ag_navbar a[href=""] p,
      .st-key-ag_navbar a[aria-current="page"] p,
      .st-key-ag_navbar [data-testid="stPageLink"][aria-current="page"] p,
      .st-key-ag_navbar [data-testid="stPageLink-NavLink"][aria-current="page"] p {
        color: #ffffff !important;
        font-weight: 700 !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2) !important;
      }
      .st-key-ag_navbar [data-testid="column"]:first-child a:hover,
      .st-key-ag_navbar a[href="Home"]:hover,
      .st-key-ag_navbar a[aria-current="page"]:hover {
        background: linear-gradient(135deg, #0275b1 0%, #02527d 100%) !important;
        box-shadow: 0 6px 18px rgba(2, 132, 199, 0.45) !important;
        transform: none !important;
      }

      /* Outline Home Vector Icon on Active Button */
      .st-key-ag_navbar [data-testid="column"]:first-child a::before,
      .st-key-ag_navbar a[href="Home"]::before,
      .st-key-ag_navbar [data-testid="column"]:first-child [data-testid="stPageLink"]::before {
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

      /* More Popover Button inside the Pill: Pure transparent, pixel-aligned */
      .st-key-ag_navbar div[data-testid="stPopover"],
      .st-key-ag_navbar .stPopover {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 0 !important;
        padding: 0 !important;
        height: 100% !important;
      }
      .st-key-ag_navbar div[data-testid="stPopover"] button,
      .st-key-ag_navbar div[data-testid="stPopover"] button:hover,
      .st-key-ag_navbar .stPopover > button,
      .st-key-ag_navbar .stPopover > button:hover {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        border-radius: 9999px !important;
        height: 2.35rem !important;
        min-height: 2.35rem !important;
        padding: 0.45rem 1.15rem !important;
        box-shadow: none !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 0 !important;
        line-height: 1 !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
      }
      .st-key-ag_navbar div[data-testid="stPopover"] button::before,
      .st-key-ag_navbar div[data-testid="stPopover"] button::after {
        display: none !important;
        content: none !important;
      }
      .st-key-ag_navbar div[data-testid="stPopover"] button p,
      .st-key-ag_navbar div[data-testid="stPopover"] button span,
      .st-key-ag_navbar div[data-testid="stPopover"] button * {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        color: #0a1f26 !important;
        letter-spacing: -0.01em !important;
        margin: 0 !important;
        line-height: 1 !important;
        visibility: visible !important;
        opacity: 1 !important;
        display: inline-block !important;
        transition: color 0.2s ease !important;
      }
      .st-key-ag_navbar div[data-testid="stPopover"] button:hover {
        background: rgba(2, 132, 199, 0.08) !important;
        background-color: rgba(2, 132, 199, 0.08) !important;
      }
      .st-key-ag_navbar div[data-testid="stPopover"] button:hover p,
      .st-key-ag_navbar div[data-testid="stPopover"] button:hover span,
      .st-key-ag_navbar div[data-testid="stPopover"] button:hover * {
        color: #0284c7 !important;
      }
      /* Hide default chevron inside More popover */
      .st-key-ag_navbar div[data-testid="stPopover"] button [data-testid="stIconMaterial"],
      .st-key-ag_navbar div[data-testid="stPopover"] button svg,
      .st-key-ag_navbar div[data-testid="stPopover"] button .material-symbols-rounded {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        height: 0 !important;
      }

      /* Popover Dropdown Styling */
      div[data-testid="stPopoverBody"] {
        max-height: 520px !important;
        border-radius: 16px !important;
        border: 1px solid rgba(2, 132, 199, 0.22) !important;
        background: #ffffff !important;
        box-shadow: 0 16px 40px rgba(4, 31, 38, 0.14), 0 4px 12px rgba(2, 132, 199, 0.08) !important;
        padding: 0.75rem 0.65rem !important;
      }
      div[data-testid="stPopoverBody"] [data-testid="stPageLink"],
      div[data-testid="stPopoverBody"] [data-testid="stPageLink-NavLink"] {
        min-height: 2.2rem !important;
        padding: 0.4rem 0.85rem !important;
        margin: 0.15rem 0 !important;
        background: #f4f8fa !important;
        border: 1px solid rgba(2, 132, 199, 0.10) !important;
        border-radius: 10px !important;
        justify-content: flex-start !important;
      }
      div[data-testid="stPopoverBody"] [data-testid="stPageLink"] p,
      div[data-testid="stPopoverBody"] [data-testid="stPageLink-NavLink"] p {
        font-size: 0.86rem !important;
        font-weight: 600 !important;
        color: #0a1f26 !important;
      }
      div[data-testid="stPopoverBody"] [data-testid="stPageLink"]:hover,
      div[data-testid="stPopoverBody"] [data-testid="stPageLink-NavLink"]:hover {
        background: rgba(2, 132, 199, 0.12) !important;
        border-color: rgba(2, 132, 199, 0.35) !important;
      }
      div[data-testid="stPopoverBody"] [data-testid="stPageLink"]:hover p,
      div[data-testid="stPopoverBody"] [data-testid="stPageLink-NavLink"]:hover p {
        color: #0284c7 !important;
      }
      div[data-testid="stPopoverBody"] [data-testid="stCaptionContainer"] p {
        color: #0284c7 !important;
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
         Sign In Capsule Button inside the Pill
         ========================================================= */
      .st-key-ag_navbar [data-testid="stPageLink"]:has(a[href*="Admin"]),
      .st-key-ag_navbar [data-testid="stPageLink-NavLink"]:has(a[href*="Admin"]),
      .st-key-ag_navbar a[href*="Admin"] {
        background: rgba(2, 132, 199, 0.08) !important;
        background-color: rgba(2, 132, 199, 0.08) !important;
        border: 1.5px solid rgba(2, 132, 199, 0.30) !important;
        border-radius: 9999px !important;
        height: 2.25rem !important;
        min-height: 2.25rem !important;
        padding: 0.4rem 1.15rem !important;
        box-shadow: none !important;
        justify-content: center !important;
        text-align: center !important;
        display: inline-flex !important;
        align-items: center !important;
        text-decoration: none !important;
        line-height: 1 !important;
        margin: 0 !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
      }
      .st-key-ag_navbar [data-testid="stPageLink"]:has(a[href*="Admin"]) p,
      .st-key-ag_navbar [data-testid="stPageLink-NavLink"]:has(a[href*="Admin"]) p,
      .st-key-ag_navbar a[href*="Admin"] p {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 0.86rem !important;
        font-weight: 700 !important;
        color: #0284c7 !important;
        letter-spacing: -0.01em !important;
        margin: 0 !important;
        line-height: 1 !important;
        transition: color 0.2s ease !important;
      }
      .st-key-ag_navbar [data-testid="stPageLink"]:has(a[href*="Admin"]):hover,
      .st-key-ag_navbar [data-testid="stPageLink-NavLink"]:has(a[href*="Admin"]):hover,
      .st-key-ag_navbar a[href*="Admin"]:hover {
        border-color: #0284c7 !important;
        background: #0284c7 !important;
        background-color: #0284c7 !important;
        box-shadow: 0 4px 14px rgba(2, 132, 199, 0.35) !important;
        transform: translateY(-1px) !important;
      }
      .st-key-ag_navbar [data-testid="stPageLink"]:has(a[href*="Admin"]):hover p,
      .st-key-ag_navbar [data-testid="stPageLink-NavLink"]:has(a[href*="Admin"]):hover p,
      .st-key-ag_navbar a[href*="Admin"]:hover p {
        color: #ffffff !important;
      }

      /* =========================================================
         Language Selector Button inside the Pill (Single Globe)
         ========================================================= */
      .st-key-ag_navbar .st-key-lang_cycle_btn,
      .st-key-ag_navbar .st-key-lang_cycle_btn > div {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 0 !important;
        padding: 0 !important;
      }
      .st-key-lang_cycle_btn button,
      .st-key-lang_cycle_btn button:hover,
      .st-key-ag_navbar .st-key-lang_cycle_btn button,
      .st-key-ag_navbar .st-key-lang_cycle_btn button:hover {
        background: rgba(2, 132, 199, 0.08) !important;
        background-color: rgba(2, 132, 199, 0.08) !important;
        border: 1.5px solid rgba(2, 132, 199, 0.30) !important;
        border-radius: 50% !important;
        height: 2.25rem !important;
        min-height: 2.25rem !important;
        width: 2.25rem !important;
        box-shadow: none !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0 !important;
        margin: 0 !important;
        position: relative !important;
      }
      .st-key-lang_cycle_btn button:hover,
      .st-key-ag_navbar .st-key-lang_cycle_btn button:hover {
        background: #0284c7 !important;
        background-color: #0284c7 !important;
        border-color: #0284c7 !important;
        box-shadow: 0 4px 14px rgba(2, 132, 199, 0.35) !important;
        transform: translateY(-1px) scale(1.05) !important;
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
        width: 16px !important;
        height: 16px !important;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='%230284c7' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'%3E%3C/circle%3E%3Cline x1='2' y1='12' x2='22' y2='12'%3E%3C/line%3E%3Cpath d='M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z'%3E%3C/path%3E%3C/svg%3E") !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        background-size: contain !important;
        pointer-events: none !important;
        transition: all 0.25s ease !important;
      }
      .st-key-lang_cycle_btn button:hover::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='%23ffffff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'%3E%3C/circle%3E%3Cline x1='2' y1='12' x2='22' y2='12'%3E%3C/line%3E%3Cpath d='M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z'%3E%3C/path%3E%3C/svg%3E") !important;
        transform: rotate(18deg) scale(1.1) !important;
      }

      /* Subtle theme divider */
      .ag-nav-rule {
        border: 0;
        height: 1px;
        background: transparent;
        margin: 0.2rem 0 1rem;
      }

      @media(max-width:950px) {
        .st-key-ag_navbar [data-testid="stHorizontalBlock"],
        [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) {
          flex-wrap: wrap !important;
          border-radius: 20px !important;
          gap: 0.5rem !important;
        }
      }
      </style>
    """, unsafe_allow_html=True)

    # Single Centered Row Container
    with st.container(key="ag_navbar"):
        c_home, c_overview, c_zones, c_decide, c_more, c_sep, c_signin, c_lang = st.columns(
            [1.15, 1.1, 0.95, 1.15, 0.9, 0.08, 1.05, 0.45], vertical_alignment="center"
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
                    f'<a href="/app/static/offline.html" target="_blank" style="text-decoration:none;display:flex;align-items:center;gap:0.4rem;padding:0.4rem 0.75rem;border-radius:8px;font-size:0.85rem;font-weight:600;color:#0284c7;background:rgba(2,132,199,0.08);border:1px solid rgba(2,132,199,0.22);margin-top:0.3rem;"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"></path></svg> {t("nav.offline_hub", "Offline Field Hub")}</a>',
                    unsafe_allow_html=True,
                )
        with c_sep:
            st.markdown(
                '<div style="width:1.5px;height:20px;background:rgba(2,132,199,0.25);margin:0 4px;border-radius:1px;"></div>',
                unsafe_allow_html=True,
            )
        with c_signin:
            st.page_link("pages/10_Admin.py", label=t("nav.signin", "Sign In"))
        with c_lang:
            render_language_selector(sidebar=False)

    st.markdown('<hr class="ag-nav-rule">', unsafe_allow_html=True)
    render_floating_ai_widget()
    render_pwa_support()
