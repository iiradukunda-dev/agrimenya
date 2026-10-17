import os

import streamlit as st
from components.home_hero import render_home_hero
from components.navbar import render_navbar
from utils.theme import load_theme
from utils.timezone import setup_system_timezone

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "logo.jpg")

st.set_page_config(page_title="agrimenya", page_icon=LOGO_PATH, layout="wide")
setup_system_timezone()
load_theme()
render_navbar()

def main():
    # Keep the landing view light; the hero is static and has no remote dependencies.
    render_home_hero()

    st.markdown("## Choose where to start")
    st.markdown("Use the tools below to move from local evidence to a field plan and a clear message for your team.")
    from components.cards import pillar_card

    workflows = [
        ("Explore zones", "Browse registered areas, compare crop information, and inspect what has been recorded.", "Open zones", "pages/4_Zones.py"),
        ("Review priorities", "See the available recommendations and the context behind intervention choices.", "Review decisions", "pages/6_Decision_Making.py"),
        ("Build a seasonal plan", "Organise activities, timing, and responsibilities for a selected zone.", "Open planning", "pages/8_Planning.py"),
        ("Coordinate updates", "Review alerts and manage approved communication workflows.", "Open communication", "pages/9_Communication.py"),
    ]
    cards = st.columns(4, gap="medium")
    for col, (title, description, action, route) in zip(cards, workflows):
        pillar_card(col, title, description, action, route)

    st.markdown("### A practical workflow")
    steps = st.columns(3, gap="medium")
    for col, number, title, description in zip(
        steps,
        ("01", "02", "03"),
        ("Find the area", "Check the evidence", "Coordinate the response"),
        ("Select a district, zone, and crop.", "Review the available indicators and recommendations.", "Set tasks in a plan and share updates with the right contacts."),
    ):
        with col:
            st.markdown(f"**{number} · {title}**")
            st.caption(description)

if __name__ == "__main__":
    main()
