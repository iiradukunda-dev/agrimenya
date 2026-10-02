import streamlit as st
import os
from utils.theme import load_theme
from utils.i18n import t
from components.navbar import render_navbar
from components.icons import render_icon_title

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "logo.jpg")

st.set_page_config(page_title="About agrimenya", page_icon=LOGO_PATH, layout="wide")
load_theme()
render_navbar()

def main():
    render_icon_title("assets/info.svg", "About agrimenya", "Learn more about our mission and platform")
    
    st.markdown("""
    ### Our Mission
    agrimenya is designed to empower agricultural professionals, cooperatives, and planners with data-driven insights. 
    By leveraging advanced analytics and seamless communication channels, we aim to optimize resource allocation, enhance crop yields, and foster collaboration across the agricultural ecosystem.

    ### Core Pillars
    - **Decision Making**: AI-powered recommendations for interventions based on priority levels and historical data.
    - **Planification**: Interactive roadmaps to track seasonal tasks and ensure timely execution of agricultural activities.
    - **Segmentation**: Geographic insights and yield mapping to identify high-potential areas and allocate resources effectively.
    - **Communication**: Real-time alerts and unified messaging to connect extension officers, cooperatives, and planners.
    """)

    """)

if __name__ == "__main__":
    main()
