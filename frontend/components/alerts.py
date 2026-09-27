import streamlit as st
from components.icons import get_base64_svg

def render_alert(alert):
    type_icons = {
        "Warning": "assets/warning.svg",
        "Info": "assets/info.svg",
        "Urgent": "assets/urgent.svg"
    }
    icon_path = type_icons.get(alert.get("type"), "assets/bell.svg")
    icon_b64 = get_base64_svg(icon_path)
    
    styles = {
        "Warning": {"bg": "#FFFBEB", "border": "#D97706", "box_border": "#FDE68A", "text": "#92400E"},
        "Info": {"bg": "#EBF5EE", "border": "#2D6A4F", "box_border": "#CBE3D1", "text": "#1B4332"},
        "Urgent": {"bg": "#FEF2F2", "border": "#DC2626", "box_border": "#FECACA", "text": "#991B1B"}
    }
    style = styles.get(alert.get("type"), {"bg": "#EBF5EE", "border": "#2D6A4F", "box_border": "#CBE3D1", "text": "#1B4332"})
    
    html = f"""
    <div style="background-color: {style['bg']}; border: 1px solid {style['box_border']}; border-left: 4px solid {style['border']}; padding: 16px; border-radius: 8px; margin-bottom: 12px; display: flex; align-items: start; gap: 14px;">
        <img src="{icon_b64}" style="width: 24px; height: 24px; margin-top: 2px;" />
        <div style="color: #1B2A1E;">
            <strong style="color: {style['text']};">{alert.get('type', 'Notification')}</strong> • <span style="color: #6B7280; font-size: 0.88rem;">{alert.get('timestamp', '')}</span><br/>
            <span style="font-size: 0.95rem; margin-top: 4px; display: inline-block;">{alert.get('message', 'No details provided.')}</span>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
