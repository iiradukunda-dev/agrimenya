import streamlit as st
from utils.theme import load_theme

st.set_page_config(page_title="Liquid Glass Showcase", layout="wide", initial_sidebar_state="expanded")
load_theme()

st.title("Liquid Glass UI Showcase")
st.markdown("A demonstration of the new Apple-style Liquid Glass design system.")

st.header("1. Cards & Metrics")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Users", "1,234", "+15%")
with col2:
    st.metric("Active Sessions", "892", "-5%")
with col3:
    st.metric("System Health", "99.9%", "Stable")

st.markdown("<br>", unsafe_allow_html=True)
st.html("""
<div class="lg-glass" style="padding: 2rem;">
    <h3 style="margin-top: 0;">Glass Container</h3>
    <p>This is a custom HTML div using the <code>.lg-glass</code> class. Notice the deep blur, semi-transparent background, and crisp specular border highlights.</p>
</div>
""")

st.header("2. Interactive Inputs & Buttons")
col_in1, col_in2 = st.columns(2)
with col_in1:
    st.text_input("Username", placeholder="Enter your username")
    st.selectbox("Theme Preference", ["Auto (System)", "Light", "Dark"])
with col_in2:
    st.button("Secondary Action", use_container_width=True)
    st.button("Primary Action", type="primary", use_container_width=True)

st.header("3. Tabbed Navigation")
tab1, tab2, tab3 = st.tabs(["Overview", "Analytics", "Settings"])
with tab1:
    st.markdown("Overview content goes here. The tabs above are styled as a pill selector.")
with tab2:
    st.markdown("Analytics content...")
with tab3:
    st.markdown("Settings content...")

st.header("4. Chat Interface")
with st.chat_message("user"):
    st.markdown("Hello, can you analyze this resume?")
with st.chat_message("assistant"):
    st.markdown("Certainly! Please upload the resume file and I'll extract the key skills and experience using the Liquid Glass interface.")
