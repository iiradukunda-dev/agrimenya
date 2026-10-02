import streamlit as st
import os
from utils.theme import load_theme
from utils.i18n import t
from components.navbar import render_navbar

from views.decision import render_decision_making
from views.planification import render_planification
from views.segmentation import render_segmentation
from views.communication import render_communication

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
        render_decision_making()
        
    with tab2:
        render_planification()
        
    with tab3:
        render_segmentation()
        
    with tab4:
        render_communication()

if __name__ == "__main__":
    main()
