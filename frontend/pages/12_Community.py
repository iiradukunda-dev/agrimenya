import os

import streamlit as st

from components.navbar import render_navbar
from utils.theme import load_theme
from utils.timezone import setup_system_timezone
from views.community import render_community

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
st.set_page_config(page_title="Farmer Community - agrimenya", page_icon=os.path.join(ASSETS_DIR, "logo.jpg"), layout="wide")
setup_system_timezone()
load_theme()
render_navbar()
render_community()
