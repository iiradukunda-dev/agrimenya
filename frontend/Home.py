"""Landing page with a live search over saved agricultural zones."""
import os

import streamlit as st

from components.home_hero import render_home_hero
from components.navbar import render_navbar
from utils.theme import load_theme
from utils.timezone import setup_system_timezone

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "logo.jpg")

st.set_page_config(page_title="Agri-Menya", page_icon=LOGO_PATH, layout="wide")
setup_system_timezone()
load_theme()
render_navbar()

render_home_hero()
