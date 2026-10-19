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
        color: #374b40 !important;
        letter-spacing: -0.01em !important;
        transition: color 0.2s ease !important;
      }
      [data-testid="stPageLink-NavLink"]:hover {
        background: rgba(16, 185, 129, 0.08) !important;
        border-color: rgba(16, 185, 129, 0.2) !important;
        transform: translateY(-1px) !important;
      }
      [data-testid="stPageLink-NavLink"]:hover p {
        color: #0d3b28 !important;
      }
      [data-testid="stPageLink-NavLink"][aria-current="page"] {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.08) 100%) !important;
        border: 1px solid rgba(16, 185, 129, 0.32) !important;
        box-shadow: 0 2px 8px rgba(16, 185, 129, 0.12) !important;
      }
      [data-testid="stPageLink-NavLink"][aria-current="page"] p {
        color: #065f46 !important;
        font-weight: 750 !important;
      }

      /* Brand Logo Special Styling */
      [data-testid="stHorizontalBlock"] [data-testid="stColumn"]:first-child [data-testid="stPageLink-NavLink"],
      [data-testid="stHorizontalBlock"] [data-testid="column"]:first-child [data-testid="stPageLink-NavLink"] {
        background: linear-gradient(135deg, #092e1e 0%, #134e34 100%) !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 12px rgba(9, 46, 30, 0.22) !important;
        border: 1px solid rgba(16, 185, 129, 0.3) !important;
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
        box-shadow: 0 6px 18px rgba(16, 185, 129, 0.35) !important;
      }

      /* Divider rule */
      .ag-nav-rule {
        border: 0;
        height: 1px;
        background: linear-gradient(90deg, rgba(16, 185, 129, 0.4) 0%, rgba(227, 233, 227, 0.9) 35%, rgba(227, 233, 227, 0.9) 70%, rgba(16, 185, 129, 0.3) 100%);
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

    brand, dashboard, zones, segment, decide, planning, communication, more, language = st.columns(
        [1.4, 1.05, 0.8, 0.95, 0.85, 0.8, 1.15, 0.7, 0.45], vertical_alignment="center", gap="small"
    )
    with brand:
        st.page_link("Home.py", label="🌱 agrimenya")
    for col, path, label, icon in [
        (dashboard, "pages/3_Dashboard.py", "Overview", "dashboard"),
        (zones, "pages/4_Zones.py", "Zones", "map"),
        (segment, "pages/5_Segmentation.py", "Segment", "layers"),
        (decide, "pages/6_Decision_Making.py", "Decide", "bolt"),
        (planning, "pages/8_Planning.py", "Plan", "edit_calendar"),
        (communication, "pages/9_Communication.py", "Alerts", "campaign"),
    ]:
        with col:
            st.page_link(path, label=label, icon=f":material/{icon}:")
    with more:
        with st.popover("More", width="stretch"):
            st.page_link("pages/7_AI_Assistant.py", label="AI assistant", icon=":material/smart_toy:")
            st.page_link("pages/10_Admin.py", label="Administration", icon=":material/admin_panel_settings:")
            st.page_link("pages/99_Showcase.py", label="Data guide", icon=":material/menu_book:")
            st.page_link("pages/1_About.py", label="About", icon=":material/info:")
            st.page_link("pages/11_Contact.py", label="Feedback", icon=":material/feedback:")
            st.page_link("pages/12_Community.py", label="Farmer community", icon=":material/forum:")
    with language:
        render_language_selector(sidebar=False)
    st.markdown('<hr class="ag-nav-rule">', unsafe_allow_html=True)
    render_floating_ai_widget()
