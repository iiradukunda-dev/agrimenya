import os

import streamlit as st
from components.navbar import render_navbar
from utils.theme import load_theme
from utils.timezone import setup_system_timezone
from views.dashboard import render_dashboard

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "ai_assistant_bulb.png")

st.set_page_config(page_title="agrimenya", page_icon=LOGO_PATH, layout="wide", initial_sidebar_state="auto")
setup_system_timezone()
load_theme(show_sidebar=True)
render_navbar(show_sidebar=True)

if __name__ == "__main__":
    render_dashboard()
