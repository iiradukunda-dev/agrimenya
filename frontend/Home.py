import os

import streamlit as st
from components.errors import error_boundary
from components.footer import render_footer
from components.home_hero import render_home_hero
from components.navbar import render_navbar
from utils.i18n import t
from utils.theme import load_theme
from utils.timezone import setup_system_timezone

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "ai_assistant_bulb.png")

st.set_page_config(page_title="agrimenya", page_icon=LOGO_PATH, layout="wide", initial_sidebar_state="collapsed")
setup_system_timezone()
load_theme()
render_navbar()


def _render_home_feedback_link() -> None:
    st.markdown(
        """
        <style>
          .st-key-home_feedback_link {
            display: flex;
            justify-content: center;
            width: 100%;
            margin: 0.5rem 0 1.5rem;
          }
          .st-key-home_feedback_link [data-testid="stPageLink"] {
            display: flex !important;
            justify-content: center !important;
            width: 100% !important;
          }
          .st-key-home_feedback_link [data-testid="stPageLink-NavLink"] {
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 0.45rem !important;
            min-height: 2.65rem !important;
            padding: 0.55rem 1rem !important;
            border: 1px solid #d5e2e7 !important;
            border-radius: 999px !important;
            background: #ffffff !important;
            color: #315d70 !important;
            font-size: 0.9rem !important;
            font-weight: 650 !important;
            text-decoration: none !important;
            box-shadow: 0 2px 7px rgba(16, 42, 52, 0.06) !important;
            margin: 0 auto !important;
            transition: border-color 160ms ease, color 160ms ease,
                        background-color 160ms ease, transform 160ms ease !important;
          }
          .st-key-home_feedback_link [data-testid="stPageLink-NavLink"]:hover {
            border-color: #1682bb !important;
            background: #f3f9fc !important;
            color: #126c9b !important;
            transform: translateY(-1px) !important;
          }
          .st-key-home_feedback_link [data-testid="stPageLink-NavLink"]:focus-visible {
            outline: 3px solid rgba(22, 130, 187, 0.3) !important;
            outline-offset: 2px !important;
          }
        </style>
        <p style="margin:0;text-align:center;color:var(--ag-text-muted);font-size:0.9rem;">
          Help us improve agrimenya
        </p>
        """,
        unsafe_allow_html=True,
    )
    with st.container(key="home_feedback_link"):
        st.page_link(
            "pages/11_Contact.py",
            label=t("home.send_feedback", "Send feedback"),
            icon=":material/feedback:",
        )


def main():
    # Animated command-center hero section
    render_home_hero()

    _render_home_feedback_link()

if __name__ == "__main__":
    with error_boundary("Home"):
        main()
    render_footer()
