import streamlit as st

def priority_badge(priority: str):
    color_map = {
        "High": "#ff4b4b",   # Red
        "Medium": "#ffa500", # Orange
        "Low": "#00cc66"     # Green
    }
    color = color_map.get(priority, "gray")
    
    html = f"""
    <div style='background-color: {color}; color: white; border-radius: 12px; padding: 4px 12px; display: inline-block; font-weight: bold; font-size: 0.9em;'>
        {priority}
    </div>
    """
    return st.markdown(html, unsafe_allow_html=True)
