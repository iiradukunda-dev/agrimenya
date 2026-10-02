import streamlit as st
import base64
import os

def get_base64_svg(file_path):
    # If it's a relative path starting with 'assets/', resolve it correctly
    if file_path.startswith("assets/") or file_path.startswith("assets\\"):
        ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
        file_path = os.path.join(ASSETS_DIR, os.path.basename(file_path))

    with open(file_path, "r", encoding="utf-8") as f:
        svg_content = f.read()
    
    b64 = base64.b64encode(svg_content.encode("utf-8")).decode("utf-8")
    return b64

def render_icon_title(icon_path, title, subtitle=None):
    icon_b64 = get_base64_svg(icon_path)
    
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; margin-bottom: { '8px' if subtitle else '24px' };">
            <div style="width: 48px; height: 48px; border-radius: 12px; background-color: #E8F5E9; display: flex; align-items: center; justify-content: center; margin-right: 16px;">
                <img src="data:image/svg+xml;base64,{icon_b64}" style="width: 28px; height: 28px;" />
            </div>
            <h1 style="margin: 0; padding: 0;">{title}</h1>
        </div>
        """,
        unsafe_allow_html=True
    )
    if subtitle:
        st.markdown(f'<p style="color: #666; font-size: 1.1rem; margin-top: 0; margin-bottom: 24px;">{subtitle}</p>', unsafe_allow_html=True)

def render_icon_subheader(icon_path, title):
    icon_b64 = get_base64_svg(icon_path)
    
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; margin-bottom: 16px; margin-top: 8px;">
            <img src="data:image/svg+xml;base64,{icon_b64}" style="width: 24px; height: 24px; margin-right: 12px; opacity: 0.8;" />
            <h3 style="margin: 0; padding: 0;">{title}</h3>
        </div>
        """,
        unsafe_allow_html=True
    )
