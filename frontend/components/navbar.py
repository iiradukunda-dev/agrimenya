"""
Navigation bar component for agrimenya.

Renders a floating glass navigation bar with branding, page links,
and an inline language selector.
"""
import streamlit as st
import os
from utils.i18n import t, render_language_selector


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
        }
        </style>
    """, unsafe_allow_html=True)

    # Render branded navbar row
    cols = st.columns([2, 1.2, 1.2, 1.2, 1.2, 0.5, 1.8])

    with cols[0]:
        # Brand mark — app name styled inline
        st.markdown(
            '<p style="font-family: \'Space Grotesk\', sans-serif; font-weight: 800; '
            'font-size: 1.35rem; margin: 0; padding: 6px 0; '
            'background: linear-gradient(135deg, #2D6A4F, #52B788); '
            '-webkit-background-clip: text; -webkit-text-fill-color: transparent;">'
            '🌱 agrimenya</p>',
            unsafe_allow_html=True
        )

    with cols[1]:
        st.page_link("Home.py", label="Home", icon=":material/home:")
    with cols[2]:
        st.page_link("pages/1_About.py", label="About", icon=":material/info:")
    with cols[3]:
        st.page_link("pages/2_Actions.py", label="Actions", icon=":material/bolt:")
    with cols[4]:
        st.page_link("pages/3_Contact.py", label="Contact", icon=":material/mail:")

    with cols[6]:
        render_language_selector(sidebar=False)

    st.divider()
