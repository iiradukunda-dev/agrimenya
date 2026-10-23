"""Compact, polished, glassmorphic application navigation."""
import streamlit as st
from components.ai_widget import render_floating_ai_widget
from utils.i18n import render_language_selector, t
from utils.pwa import render_pwa_support


def render_navbar() -> None:
    """Show the main workflows first and keep supporting pages one click away."""
    st.markdown("""
      <style>
      @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');
      [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
      
      /* Nav Bar Base Container Styling - Transparent Frosted Glass Capsules */
      [data-testid="stPageLink-NavLink"] {
        background: rgba(255, 255, 255, 0.08) !important;
        backdrop-filter: blur(14px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(14px) saturate(180%) !important;
        border-radius: 10px !important;
        min-height: 2.55rem !important;
        padding: 0.35rem 0.75rem !important;
        border: 1px solid rgba(255, 255, 255, 0.22) !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25) !important;
        justify-content: center !important;
        text-align: center !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
      }
      [data-testid="stPageLink-NavLink"] p {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 0.88rem !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        letter-spacing: -0.01em !important;
        text-shadow: 0 1px 4px rgba(0, 0, 0, 0.7) !important;
        transition: color 0.2s ease !important;
      }
      [data-testid="stPageLink-NavLink"]:hover {
        background: rgba(255, 255, 255, 0.18) !important;
        border-color: rgba(56, 189, 248, 0.65) !important;
        box-shadow: 0 6px 20px rgba(14, 165, 233, 0.35) !important;
        transform: translateY(-1px) !important;
      }
      [data-testid="stPageLink-NavLink"]:hover p {
        color: #38bdf8 !important;
      }
      [data-testid="stPageLink-NavLink"][aria-current="page"] {
        background: rgba(56, 189, 248, 0.24) !important;
        border: 1.5px solid rgba(56, 189, 248, 0.75) !important;
        box-shadow: 0 4px 18px rgba(14, 165, 233, 0.35) !important;
      }
      [data-testid="stPageLink-NavLink"][aria-current="page"] p {
        color: #ffffff !important;
        font-weight: 800 !important;
        text-shadow: 0 0 10px rgba(56, 189, 248, 0.6) !important;
      }

      /* Brand Logo Special Styling - Transparent Cyan Glass Glow */
      [data-testid="stHorizontalBlock"] [data-testid="stColumn"]:first-child [data-testid="stPageLink-NavLink"],
      [data-testid="stHorizontalBlock"] [data-testid="column"]:first-child [data-testid="stPageLink-NavLink"] {
        background: rgba(2, 32, 44, 0.35) !important;
        backdrop-filter: blur(14px) !important;
        -webkit-backdrop-filter: blur(14px) !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3), 0 0 16px rgba(56, 189, 248, 0.25) !important;
        border: 1px solid rgba(56, 189, 248, 0.45) !important;
      }
      [data-testid="stHorizontalBlock"] [data-testid="stColumn"]:first-child [data-testid="stPageLink-NavLink"] p,
      [data-testid="stHorizontalBlock"] [data-testid="column"]:first-child [data-testid="stPageLink-NavLink"] p {
        color: #ffffff !important;
        font-size: 0.96rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em !important;
        text-shadow: 0 0 12px rgba(56, 189, 248, 0.6) !important;
      }
      [data-testid="stHorizontalBlock"] [data-testid="stColumn"]:first-child [data-testid="stPageLink-NavLink"]:hover,
      [data-testid="stHorizontalBlock"] [data-testid="column"]:first-child [data-testid="stPageLink-NavLink"]:hover {
        background: rgba(2, 32, 44, 0.55) !important;
        transform: translateY(-1px) scale(1.02) !important;
        box-shadow: 0 6px 20px rgba(56, 189, 248, 0.45) !important;
        border-color: rgba(56, 189, 248, 0.75) !important;
      }

      /* Hide any icons in navbar links */
      [data-testid="stPageLink-NavLink"] span[data-testid="stIconMaterial"],
      [data-testid="stPageLink-NavLink"] svg,
      [data-testid="stPageLink-NavLink"] i {
        display: none !important;
      }

      /* Column 5: More Popover Button - Transparent Capsule with centered "More" */
      [data-testid="stHorizontalBlock"]:has(a[href*="Dashboard"]) [data-testid="column"]:nth-child(5) button,
      [data-testid="stHorizontalBlock"]:has(a[href*="Dashboard"]) [data-testid="stColumn"]:nth-child(5) button,
      [data-testid="stHorizontalBlock"]:has(a[href*="Dashboard"]) .stPopover button,
      [data-testid="stHorizontalBlock"]:has(a[href*="Dashboard"]) div[data-testid="stPopover"] button {
        border-radius: 10px !important;
        min-height: 2.55rem !important;
        padding: 0.35rem 0.85rem !important;
        border: 1px solid rgba(255, 255, 255, 0.22) !important;
        background: rgba(255, 255, 255, 0.08) !important;
        backdrop-filter: blur(14px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(14px) saturate(180%) !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25) !important;
        transition: all 0.25s ease !important;
      }
      [data-testid="stHorizontalBlock"]:has(a[href*="Dashboard"]) [data-testid="column"]:nth-child(5) button:hover,
      [data-testid="stHorizontalBlock"]:has(a[href*="Dashboard"]) [data-testid="stColumn"]:nth-child(5) button:hover,
      [data-testid="stHorizontalBlock"]:has(a[href*="Dashboard"]) .stPopover button:hover {
        background: rgba(255, 255, 255, 0.18) !important;
        border-color: rgba(56, 189, 248, 0.65) !important;
        box-shadow: 0 6px 20px rgba(14, 165, 233, 0.35) !important;
        transform: translateY(-1px) !important;
      }
      [data-testid="stHorizontalBlock"]:has(a[href*="Dashboard"]) [data-testid="column"]:nth-child(5) button p,
      [data-testid="stHorizontalBlock"]:has(a[href*="Dashboard"]) [data-testid="stColumn"]:nth-child(5) button p,
      [data-testid="stHorizontalBlock"]:has(a[href*="Dashboard"]) .stPopover button p {
        color: #ffffff !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 0.88rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em !important;
        margin: 0 !important;
        text-shadow: 0 1px 4px rgba(0, 0, 0, 0.7) !important;
        transition: color 0.2s ease !important;
      }
      [data-testid="stHorizontalBlock"]:has(a[href*="Dashboard"]) [data-testid="column"]:nth-child(5) button:hover p,
      [data-testid="stHorizontalBlock"]:has(a[href*="Dashboard"]) [data-testid="stColumn"]:nth-child(5) button:hover p,
      [data-testid="stHorizontalBlock"]:has(a[href*="Dashboard"]) .stPopover button:hover p {
        color: #38bdf8 !important;
      }
      /* Completely eliminate the expand_more chevron from the More button */
      [data-testid="stHorizontalBlock"]:has(a[href*="Dashboard"]) [data-testid="column"]:nth-child(5) button div:has(> span.material-symbols-rounded),
      [data-testid="stHorizontalBlock"]:has(a[href*="Dashboard"]) [data-testid="column"]:nth-child(5) button .material-symbols-rounded,
      [data-testid="stHorizontalBlock"]:has(a[href*="Dashboard"]) [data-testid="column"]:nth-child(5) [class*="eqzt73c3"],
      [data-testid="stHorizontalBlock"]:has(a[href*="Dashboard"]) [data-testid="stColumn"]:nth-child(5) [class*="eqzt73c3"],
      [data-testid="stHorizontalBlock"]:has(a[href*="Dashboard"]) .material-symbols-rounded {
        display: none !important;
        visibility: hidden !important;
        font-size: 0 !important;
        width: 0 !important;
        height: 0 !important;
        line-height: 0 !important;
        opacity: 0 !important;
        position: absolute !important;
        pointer-events: none !important;
      }

      div[data-testid="stPopoverBody"] {
        max-height: 520px !important;
        border-radius: 14px !important;
        border: 1px solid rgba(56, 189, 248, 0.38) !important;
        background: rgba(2, 24, 36, 0.92) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.5) !important;
        padding: 0.65rem 0.55rem !important;
      }
      div[data-testid="stPopoverBody"] [data-testid="stPageLink-NavLink"] {
        min-height: 2.2rem !important;
        padding: 0.25rem 0.65rem !important;
        margin: 0.08rem 0 !important;
        background: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
      }
      div[data-testid="stPopoverBody"] [data-testid="stPageLink-NavLink"] p {
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: #e0f2fe !important;
      }
      div[data-testid="stPopoverBody"] [data-testid="stPageLink-NavLink"]:hover p {
        color: #38bdf8 !important;
      }
      div[data-testid="stPopoverBody"] [data-testid="stCaptionContainer"] p {
        color: #7dd3fc !important;
        font-weight: 700 !important;
        letter-spacing: 0.05em !important;
      }

      /* Column 6: Language Selector Button - Strictly scoped to Navbar only */
      [data-testid="stHorizontalBlock"]:has(a[href*="Dashboard"]) [data-testid="column"]:last-child button,
      [data-testid="stHorizontalBlock"]:has(a[href*="Dashboard"]) [data-testid="stColumn"]:last-child button {
        background: rgba(255, 255, 255, 0.08) !important;
        backdrop-filter: blur(14px) !important;
        -webkit-backdrop-filter: blur(14px) !important;
        border: 1px solid rgba(255, 255, 255, 0.22) !important;
        border-radius: 10px !important;
        min-height: 2.55rem !important;
        width: 100% !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25) !important;
        transition: all 0.25s ease !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0 !important;
        position: relative !important;
      }
      [data-testid="stHorizontalBlock"]:has(a[href*="Dashboard"]) [data-testid="column"]:last-child button:hover,
      [data-testid="stHorizontalBlock"]:has(a[href*="Dashboard"]) [data-testid="stColumn"]:last-child button:hover {
        background: rgba(255, 255, 255, 0.18) !important;
        border-color: rgba(56, 189, 248, 0.65) !important;
        box-shadow: 0 6px 20px rgba(14, 165, 233, 0.35) !important;
        transform: translateY(-1px) !important;
      }
      /* Hide the literal text inside the language button */
      [data-testid="stHorizontalBlock"]:has(a[href*="Dashboard"]) [data-testid="column"]:last-child button * {
        font-size: 0 !important;
        color: transparent !important;
        line-height: 0 !important;
        max-width: 0 !important;
        max-height: 0 !important;
        overflow: hidden !important;
        visibility: hidden !important;
      }
      /* Inject crisp vector world icon via ::before */
      [data-testid="stHorizontalBlock"]:has(a[href*="Dashboard"]) [data-testid="column"]:last-child button::before,
      [data-testid="stHorizontalBlock"]:has(a[href*="Dashboard"]) [data-testid="stColumn"]:last-child button::before {
        content: '' !important;
        display: block !important;
        width: 20px !important;
        height: 20px !important;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='%23ffffff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'%3E%3C/circle%3E%3Cline x1='2' y1='12' x2='22' y2='12'%3E%3C/line%3E%3Cpath d='M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z'%3E%3C/path%3E%3C/svg%3E") !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        background-size: contain !important;
        pointer-events: none !important;
        transition: transform 0.25s ease !important;
      }
      [data-testid="stHorizontalBlock"]:has(a[href*="Dashboard"]) [data-testid="column"]:last-child button:hover::before,
      [data-testid="stHorizontalBlock"]:has(a[href*="Dashboard"]) [data-testid="stColumn"]:last-child button:hover::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='%2338bdf8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'%3E%3C/circle%3E%3Cline x1='2' y1='12' x2='22' y2='12'%3E%3C/line%3E%3Cpath d='M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z'%3E%3C/path%3E%3C/svg%3E") !important;
        transform: rotate(18deg) scale(1.1) !important;
      }

      /* Divider rule */
      .ag-nav-rule {
        border: 0;
        height: 1px;
        background: linear-gradient(90deg, rgba(56, 189, 248, 0.5) 0%, rgba(74, 222, 128, 0.45) 35%, rgba(255, 255, 255, 0.15) 70%, rgba(56, 189, 248, 0.3) 100%);
        margin: 0.6rem 0 1.5rem;
      }

      @media(max-width:850px) {
        [data-testid="stPageLink-NavLink"] p { font-size: 0.78rem !important; }
      }
      @media(max-width:700px) {
        .block-container { padding: 1rem 0.8rem 3rem !important; }
        [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 0.5rem !important; }
        [data-testid="stHorizontalBlock"] > [data-testid="column"] { min-width: 105px !important; }
        [data-testid="stPageLink-NavLink"] { min-height: 2.8rem !important; }
      }
      </style>
    """, unsafe_allow_html=True)

    brand, dashboard, zones, decide, more, language = st.columns(
        [1.6, 1.15, 1.05, 1.15, 0.95, 0.55], vertical_alignment="center", gap="medium"
    )
    with brand:
        st.page_link("Home.py", label="agrimenya")
    for col, path, label in [
        (dashboard, "pages/3_Dashboard.py", t("nav.overview", "Overview")),
        (zones, "pages/4_Zones.py", t("nav.zones", "Zones")),
        (decide, "pages/6_Decision_Making.py", t("nav.decisions", "Decisions")),
    ]:
        with col:
            st.page_link(path, label=label)
    with more:
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
                f'<a href="/app/static/offline.html" target="_blank" style="text-decoration:none;display:flex;align-items:center;gap:0.4rem;padding:0.35rem 0.65rem;border-radius:8px;font-size:0.85rem;font-weight:600;color:#38bdf8;background:rgba(56,189,248,0.1);border:1px solid rgba(56,189,248,0.25);margin-top:0.3rem;">⚡ {t("nav.offline_hub", "Offline Field Hub")}</a>',
                unsafe_allow_html=True,
            )
    with language:
        render_language_selector(sidebar=False)
    st.markdown('<hr class="ag-nav-rule">', unsafe_allow_html=True)
    render_floating_ai_widget()
    render_pwa_support()
