import os
import streamlit as st
from components.navbar import render_navbar
from utils.theme import load_theme
from utils.timezone import setup_system_timezone
from views.segment import render_segment

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "logo.jpg")

st.set_page_config(page_title="Segmentation - agrimenya", page_icon=LOGO_PATH, layout="wide")
setup_system_timezone()
load_theme()
render_navbar()

if __name__ == "__main__":
    render_segment()
