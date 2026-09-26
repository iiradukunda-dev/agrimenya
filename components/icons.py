import streamlit as st
import base64

def get_base64_svg(file_path):
    with open(file_path, "r") as f:
        svg = f.read()
    b64 = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
    return f"data:image/svg+xml;base64,{b64}"

def render_icon_title(icon_path, title, subtitle=None):
    icon_b64 = get_base64_svg(icon_path)
    html = f"""
    <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 24px;">
        <img src="{icon_b64}" style="width: 48px; height: 48px;" />
        <div>
            <h1 style="margin: 0; padding: 0; font-size: 2.2rem; line-height: 1.2;">{title}</h1>
            {"<p style='margin: 4px 0 0 0; font-size: 1.2rem; color: #555;'>" + subtitle + "</p>" if subtitle else ""}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_icon_subheader(icon_path, title):
    icon_b64 = get_base64_svg(icon_path)
    html = f"""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px; margin-top: 16px;">
        <img src="{icon_b64}" style="width: 28px; height: 28px;" />
        <h3 style="margin: 0; padding: 0; font-size: 1.5rem;">{title}</h3>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
