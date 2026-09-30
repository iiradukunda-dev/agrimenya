import streamlit as st
from utils.i18n import t
from components.icons import get_base64_svg

def render_error_page(error_type: str, details: str = None):
    """
    Renders an error page with the custom green, white, and black theme.
    error_type: "404", "network", "validation", "system"
    """
    title_key = f"error.{error_type}.title"
    desc_key = f"error.{error_type}.desc"
    
    title = t(title_key)
    desc = t(desc_key)
    
    # Try to use a warning icon if available, otherwise just SVG
    import os
    icon_html = ""
    icon_path = "assets/alert.svg"
    
    if not os.path.exists(icon_path):
        alt_path = os.path.join('frontend', icon_path)
        if os.path.exists(alt_path):
            icon_path = alt_path
            
    if os.path.exists(icon_path):
        try:
            icon_b64 = get_base64_svg(icon_path)
            icon_html = f'<img src="data:image/svg+xml;base64,{icon_b64}" style="width: 48px; height: 48px; margin-bottom: 16px;" />'
        except Exception:
            pass
            
    if not icon_html:
        # Fallback SVG icon in green
        icon_html = """
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#52B788" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-bottom: 16px;">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
        """

    _, col, _ = st.columns([1, 2, 1])
    
    with col:
        st.markdown(
            f"""
            <div style="
                background-color: #ffffff;
                border: 2px solid #52B788;
                border-radius: 12px;
                padding: 40px;
                text-align: center;
                box-shadow: 0 4px 12px rgba(45, 106, 79, 0.1);
                margin-top: 40px;
                margin-bottom: 40px;
            ">
                {icon_html}
                <h2 style="
                    color: #000000;
                    font-family: 'Inter', sans-serif;
                    font-size: 2rem;
                    font-weight: 700;
                    margin-bottom: 16px;
                    margin-top: 0;
                ">
                    {title}
                </h2>
                <p style="
                    color: #000000;
                    font-family: 'Inter', sans-serif;
                    font-size: 1.1rem;
                    line-height: 1.6;
                    margin-bottom: 24px;
                ">
                    {desc}
                </p>
                {f'<div style="text-align: left; color: #000000; font-family: monospace; background: #F3F8F3; padding: 12px; border-radius: 6px; font-size: 0.9rem; margin-bottom: 24px; border: 1px solid #DDE7DF; overflow-x: auto;">{details}</div>' if details else ''}
            </div>
            """,
            unsafe_allow_html=True
        )
        
        if st.button(t("error.go_home"), use_container_width=True, key=f"btn_error_{error_type}"):
            st.switch_page("Home.py")
