import streamlit as st
from utils.i18n import t

def priority_badge(priority: str):
    color_map = {
        "High": {"bg": "#FEE2E2", "text": "#991B1B", "border": "#FCA5A5"},
        "Medium": {"bg": "#FEF3C7", "text": "#92400E", "border": "#FCD34D"},
        "Low": {"bg": "#D8F3DC", "text": "#1B4332", "border": "#95D5B2"}
    }
    style = color_map.get(priority, {"bg": "#E5E7EB", "text": "#374151", "border": "#D1D5DB"})
    display_text = t(f"priority.{priority.lower()}", default=priority)
    
    html = f"""
    <div style='background-color: {style["bg"]}; color: {style["text"]}; border: 1px solid {style["border"]}; border-radius: 12px; padding: 3px 10px; display: inline-block; font-weight: 600; font-size: 0.82rem;'>
        {display_text}
    </div>
    """
    return st.markdown(html, unsafe_allow_html=True)

