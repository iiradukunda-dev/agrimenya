"""
Alert / notification card component for the Communication pillar.
"""
from html import escape

import streamlit as st
from components.icons import get_base64_svg
from utils.i18n import t


def render_alert(alert: dict) -> None:
    """
    Renders a single alert card using the ag-alert design system classes.

    Args:
        alert: Dictionary with 'type', 'message', and 'timestamp' keys.
    """
    type_icons = {
        "Warning": "assets/warning.svg",
        "Info":    "assets/info.svg",
        "Urgent":  "assets/urgent.svg",
        "Critical": "assets/urgent.svg",
    }
    raw_type = alert.get("type", "Info")
    icon_path = type_icons.get(raw_type, "assets/bell.svg")

    try:
        icon_b64 = get_base64_svg(icon_path)
        icon_html = (
            f'<img src="data:image/svg+xml;base64,{icon_b64}" '
            f'style="width: 22px; height: 22px; margin-top: 2px; flex-shrink: 0;" />'
        )
    except FileNotFoundError:
        icon_html = ""

    css_class_map = {
        "Warning": "ag-alert ag-alert-warning",
        "Info":    "ag-alert ag-alert-info",
        "Urgent":  "ag-alert ag-alert-urgent",
        "Critical": "ag-alert ag-alert-urgent",
    }
    css_class = css_class_map.get(raw_type, "ag-alert ag-alert-info")
    translated_type = escape(t(f"comm.alert_type.{str(raw_type).lower()}", default=str(raw_type)))
    timestamp = escape(str(alert.get("timestamp") or ""))
    message = escape(str(alert.get("message") or "No details provided."))
    location = escape(str(alert.get("location") or "Location not supplied"))
    source = escape(str(alert.get("source_label") or "Source not supplied"))
    action = escape(str(alert.get("action") or "No action supplied"))
    crop = escape(str(alert.get("crop") or "All crops / not specified"))
    status = escape(str(alert.get("status") or "Status not tracked"))
    expires = escape(str(alert.get("expires_at") or "No expiry supplied"))

    html = f"""
    <div class="{css_class}">
        {icon_html}
        <div>
            <strong style="color: inherit; font-size: 0.88rem;">{translated_type}</strong>
            <span style="color: #64736a; font-size: 0.8rem; margin-left: 8px;">{timestamp}</span>
            <br/>
            <span style="font-size: 0.92rem; margin-top: 4px; display: inline-block; color: #374151; line-height: 1.5;">
                {message}
            </span>
            <div style="margin-top:.45rem;color:#64736a;font-size:.8rem;line-height:1.5">
                <span>{location}</span> · <span>{crop}</span> · <span>Source: {source}</span><br/>
                <span>Next action: {action}</span><br/>
                <span>{status}</span> · <span>{expires}</span>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
