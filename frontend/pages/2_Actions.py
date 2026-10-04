import os

import streamlit as st
from components.navbar import render_navbar
from utils.i18n import t
from utils.theme import load_theme
from views.communicate import render_communicate
from views.decide import render_decide
from views.plan import render_plan
from views.segment import render_segment

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "logo.jpg")

st.set_page_config(page_title="Actions", page_icon=LOGO_PATH, layout="wide")
load_theme()
render_navbar()

def main():
    st.title("Agricultural Actions & Pillars")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        t("pillar.decisions.title"), 
        t("pillar.planification.title"), 
        t("pillar.segmentation.title"), 
        t("pillar.communication.title")
    ])
    
    with tab1:
        render_decide()
        
    with tab2:
        render_plan()
        
    with tab3:
        render_segment()
        
    with tab4:
        render_communicate()

if __name__ == "__main__":
    main()
