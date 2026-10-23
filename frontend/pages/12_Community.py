import os

import streamlit as st

from components.navbar import render_navbar
from utils.theme import load_theme
from utils.timezone import setup_system_timezone
from views.community import render_community

LOGO_PATH = os.path.join(ASSETS_DIR, "ai_assistant_bulb.png")
st.set_page_config(page_title="agrimenya", page_icon=LOGO_PATH, layout="wide")
setup_system_timezone()
load_theme()
render_navbar()
render_community()
