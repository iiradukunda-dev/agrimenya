"""Compact, consistent application navigation."""
import streamlit as st
from utils.i18n import render_language_selector


def render_navbar() -> None:
    """Show the main workflows first and keep supporting pages one click away."""
    st.markdown("""
      <style>
      [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
      [data-testid="stPageLink-NavLink"] { border-radius:8px; min-height:2.5rem; }
      [data-testid="stPageLink-NavLink"] p { font-size:.88rem; font-weight:600; color:#40554a; }
      [data-testid="stPageLink-NavLink"][aria-current="page"] { background:#eaf3ec; }
      [data-testid="stPageLink-NavLink"][aria-current="page"] p { color:#194b36; }
      .ag-nav-rule { border:0; border-top:1px solid #e3e9e3; margin:.45rem 0 1.4rem; }
      @media(max-width:850px) { [data-testid="stPageLink-NavLink"] p { font-size:.77rem; } }
      @media(max-width:700px) {
        .block-container { padding:1rem .8rem 3rem !important; }
        [data-testid="stHorizontalBlock"] { flex-wrap:wrap !important; gap:.55rem !important; }
        [data-testid="stHorizontalBlock"] > [data-testid="column"] { min-width:110px !important; }
        [data-testid="stPageLink-NavLink"] { min-height:3rem; }
        [data-testid="stButton"] button, [data-testid="stFormSubmitButton"] button { min-height:3rem; }
        [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea { font-size:16px; }
      }
      </style>
    """, unsafe_allow_html=True)

    brand, dashboard, zones, segment, decide, planning, communication, more, language = st.columns(
        [1.45, 1.05, .8, 1, .85, .8, 1.2, .7, .4], vertical_alignment="center", gap="small"
    )
    with brand:
        st.page_link("Home.py", label="agrimenya")
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
