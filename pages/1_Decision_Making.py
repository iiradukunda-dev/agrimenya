import streamlit as st
from utils.theme import load_theme
from utils import api_client
from components.badges import priority_badge
from components.icons import render_icon_title, render_icon_subheader

st.set_page_config(page_title="Decision Making", page_icon="assets/brain.svg", layout="wide")
load_theme()

render_icon_title("assets/brain.svg", "Decision Making", "Automated, proactive recommendations based on predictive agricultural data.")

recs = api_client.get_recommendations()

for rec in recs:
    with st.container(border=True):
        col1, col2, col3 = st.columns([1, 4, 1])
        with col1:
            st.markdown(f"**{rec['area']}**")
            st.caption(f"Crop: {rec['crop']}")
        with col2:
            st.markdown(f"{rec['text']}")
        with col3:
            priority_badge(rec['priority'])
            st.caption(f"Status: {rec['status']}")
            st.button("Act", key=f"act_{rec['area']}_{rec['crop']}")

st.divider()

render_icon_subheader("assets/bot.svg", "AI Assistant")
st.markdown("Ask the AI planner for specific context or adjustments to the recommendations.")
prompt = st.chat_input("E.g., What are the risk factors for Maize in Nyagatare?")
if prompt:
    with st.chat_message("user"):
        st.write(prompt)
    with st.chat_message("assistant"):
        st.write(f"This is a stubbed AI response to: *'{prompt}'*. \n\nIn a live environment, the backend will parse the SAS/EICV7 data to provide targeted insight for this region.")
