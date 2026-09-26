import streamlit as st
from components.icons import get_base64_svg

def render_alert(alert):
    type_icons = {
        "Warning": "assets/warning.svg",
        "Info": "assets/info.svg",
        "Urgent": "assets/urgent.svg"
    }
    icon_path = type_icons.get(alert["type"], "assets/bell.svg")
    icon_b64 = get_base64_svg(icon_path)
    
    html = f"""
    <div style="background-color: #f0f2f6; padding: 16px; border-radius: 8px; margin-bottom: 12px; display: flex; align-items: start; gap: 12px;">
        <img src="{icon_b64}" style="width: 24px; height: 24px; margin-top: 2px;" />
        <div>
            <strong>{alert['type']}</strong> • {alert['timestamp']}<br/>
            {alert['message']}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
