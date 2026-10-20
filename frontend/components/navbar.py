"""Compact, polished, glassmorphic application navigation."""
import streamlit as st
from components.ai_widget import render_floating_ai_widget
from utils.i18n import render_language_selector


def render_navbar() -> None:
    """Show the main workflows first and keep supporting pages one click away."""
    st.markdown("""
      <style>
      [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
      
      /* Nav Bar Base Container Styling */
      [data-testid="stPageLink-NavLink"] {
        border-radius: 10px !important;
        min-height: 2.55rem !important;
        padding: 0.35rem 0.75rem !important;
        border: 1px solid transparent !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
      }
      [data-testid="stPageLink-NavLink"] p {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 0.88rem !important;
        font-weight: 650 !important;
        color: #2b454e !important;
        letter-spacing: -0.01em !important;
        transition: color 0.2s ease !important;
      }
      [data-testid="stPageLink-NavLink"]:hover {
        background: rgba(14, 165, 233, 0.08) !important;
        border-color: rgba(56, 189, 248, 0.28) !important;
        transform: translateY(-1px) !important;
      }
      [data-testid="stPageLink-NavLink"]:hover p {
        color: #0284c7 !important;
      }
      [data-testid="stPageLink-NavLink"][aria-current="page"] {
        background: linear-gradient(135deg, rgba(56, 189, 248, 0.16) 0%, rgba(16, 185, 129, 0.1) 100%) !important;
        border: 1px solid rgba(56, 189, 248, 0.38) !important;
        box-shadow: 0 2px 10px rgba(14, 165, 233, 0.14) !important;
      }
      [data-testid="stPageLink-NavLink"][aria-current="page"] p {
        color: #035368 !important;
        font-weight: 750 !important;
      }

      /* Brand Logo Special Styling - Cyan-to-Forest Bulb Theme */
      [data-testid="stHorizontalBlock"] [data-testid="stColumn"]:first-child [data-testid="stPageLink-NavLink"],
      [data-testid="stHorizontalBlock"] [data-testid="column"]:first-child [data-testid="stPageLink-NavLink"] {
        background: linear-gradient(135deg, #02202c 0%, #053b42 50%, #0a4f38 100%) !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 14px rgba(2, 32, 44, 0.25), 0 0 16px rgba(56, 189, 248, 0.18) !important;
        border: 1px solid rgba(56, 189, 248, 0.38) !important;
      }
      [data-testid="stHorizontalBlock"] [data-testid="stColumn"]:first-child [data-testid="stPageLink-NavLink"] p,
      [data-testid="stHorizontalBlock"] [data-testid="column"]:first-child [data-testid="stPageLink-NavLink"] p {
        color: #ffffff !important;
        font-size: 0.96rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em !important;
      }
      [data-testid="stHorizontalBlock"] [data-testid="stColumn"]:first-child [data-testid="stPageLink-NavLink"]:hover,
      [data-testid="stHorizontalBlock"] [data-testid="column"]:first-child [data-testid="stPageLink-NavLink"]:hover {
        transform: translateY(-1px) scale(1.02) !important;
        box-shadow: 0 6px 20px rgba(56, 189, 248, 0.38) !important;
        border-color: rgba(56, 189, 248, 0.6) !important;
      }

      /* Hide any icons in navbar links */
      [data-testid="stPageLink-NavLink"] span[data-testid="stIconMaterial"],
      [data-testid="stPageLink-NavLink"] svg,
      [data-testid="stPageLink-NavLink"] i {
        display: none !important;
      }

      /* More Popover Button & Floating Panel */
      [data-testid="stPopover"] > button {
        border-radius: 10px !important;
        min-height: 2.55rem !important;
        padding: 0.35rem 0.85rem !important;
        border: 1px solid rgba(56, 189, 248, 0.22) !important;
        background: rgba(255, 255, 255, 0.6) !important;
        backdrop-filter: blur(8px) !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 0.88rem !important;
        font-weight: 650 !important;
        color: #2b454e !important;
        transition: all 0.25s ease !important;
      }
      [data-testid="stPopover"] > button:hover {
        background: rgba(14, 165, 233, 0.1) !important;
        border-color: rgba(56, 189, 248, 0.45) !important;
        color: #0284c7 !important;
        transform: translateY(-1px) !important;
      }
      div[data-testid="stPopoverBody"] {
        max-height: 520px !important;
        border-radius: 14px !important;
        border: 1px solid rgba(56, 189, 248, 0.28) !important;
        background: rgba(255, 255, 255, 0.98) !important;
        box-shadow: 0 16px 40px rgba(2, 32, 44, 0.16) !important;
        padding: 0.65rem 0.55rem !important;
      }
      div[data-testid="stPopoverBody"] [data-testid="stPageLink-NavLink"] {
        min-height: 2.2rem !important;
        padding: 0.25rem 0.65rem !important;
        margin: 0.08rem 0 !important;
      }
      div[data-testid="stPopoverBody"] [data-testid="stPageLink-NavLink"] p {
        font-size: 0.85rem !important;
        font-weight: 600 !important;
      }

      /* Divider rule */
      .ag-nav-rule {
        border: 0;
        height: 1px;
        background: linear-gradient(90deg, rgba(56, 189, 248, 0.5) 0%, rgba(74, 222, 128, 0.45) 35%, rgba(216, 229, 232, 0.9) 70%, rgba(56, 189, 248, 0.3) 100%);
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
        (dashboard, "pages/3_Dashboard.py", "Overview"),
        (zones, "pages/4_Zones.py", "Zones"),
        (decide, "pages/6_Decision_Making.py", "Decisions"),
    ]:
        with col:
            st.page_link(path, label=label)
    with more:
        with st.popover("More", width="stretch"):
            st.caption("OPERATIONS & TOOLS")
            st.page_link("pages/8_Planning.py", label="Seasonal planning")
            st.page_link("pages/9_Communication.py", label="Field alerts & comms")
            st.page_link("pages/5_Segmentation.py", label="Zone segmentation")
            st.page_link("pages/7_AI_Assistant.py", label="AI assistant")
            st.divider()
            st.caption("PLATFORM & COMMUNITY")
            st.page_link("pages/10_Admin.py", label="Administration")
            st.page_link("pages/99_Showcase.py", label="Data guide")
            st.page_link("pages/12_Community.py", label="Farmer community")
            st.page_link("pages/1_About.py", label="About agrimenya")
            st.page_link("pages/11_Contact.py", label="Feedback & support")
    with language:
        render_language_selector(sidebar=False)
    st.markdown('<hr class="ag-nav-rule">', unsafe_allow_html=True)
    render_floating_ai_widget()
