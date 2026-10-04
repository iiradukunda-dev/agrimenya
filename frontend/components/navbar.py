"""
Navigation bar component for agrimenya.

Renders a floating glass navigation bar with branding, page links,
and an inline language selector.
"""

import streamlit as st
from utils.i18n import render_language_selector


def render_navbar() -> None:
    """
    Renders a premium floating navigation bar with agrimenya branding.
    Hides the default Streamlit sidebar and header.
    """
    st.markdown("""
        <style>
        /* Hide default Streamlit navigation chrome */
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }
        header[data-testid="stHeader"] { display: none !important; }

        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
        }

        /* Floating glass pill for the FIRST horizontal block only */
        .stMainBlockContainer > div > div > [data-testid="stHorizontalBlock"]:first-child {
            background: rgba(255, 255, 255, 0.35) !important;
            backdrop-filter: blur(24px) saturate(180%) !important;
            -webkit-backdrop-filter: blur(24px) saturate(180%) !important;
            border: 1px solid rgba(255, 255, 255, 0.45) !important;
            border-radius: 50px !important;
            padding: 6px 24px !important;
            box-shadow:
                0 4px 20px rgba(0, 0, 0, 0.05),
                inset 0 1px 0 rgba(255, 255, 255, 0.6) !important;
            align-items: center !important;
            margin: 0 auto 2rem auto !important;
            max-width: 1200px !important;
            gap: 0 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Render branded navbar row
    cols = st.columns([1.8, 0.8, 0.9, 0.8, 0.6, 0.8, 0.9, 0.8, 0.5, 1.2])

    with cols[0]:
        st.markdown(
            '<p style="font-family: \'Space Grotesk\', sans-serif; font-weight: 800; '
            'font-size: 1.25rem; margin: 0; padding: 4px 0; '
            'background: linear-gradient(135deg, #2D6A4F, #52B788); '
            '-webkit-background-clip: text; -webkit-text-fill-color: transparent;">'
            'agrimenya</p>',
            unsafe_allow_html=True,
        )

    with cols[1]:
        st.page_link("Home.py", label="Home", icon=":material/home:")
    with cols[2]:
        st.page_link("pages/3_Dashboard.py", label="Dashboard", icon=":material/dashboard:")
    with cols[3]:
        st.page_link("pages/4_Zones.py", label="Zones", icon=":material/map:")
    with cols[4]:
        st.page_link("pages/2_Actions.py", label="Actions", icon=":material/bolt:")
    with cols[5]:
        st.page_link("pages/5_AI_Assistant.py", label="AI", icon=":material/smart_toy:")
    with cols[6]:
        st.page_link("pages/6_Planning.py", label="Planning", icon=":material/edit_calendar:")
    with cols[7]:
        st.page_link("pages/7_Communication.py", label="Alerts", icon=":material/campaign:")
    with cols[8]:
        st.page_link("pages/8_Admin.py", label="Admin", icon=":material/admin_panel_settings:")

    with cols[9]:
        render_language_selector(sidebar=False)

    st.divider()

