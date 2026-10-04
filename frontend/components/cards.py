import os
import streamlit as st

def pillar_card(col, icon: str, title: str, desc: str, btn_text: str, page_route: str) -> None:
    """
    Renders a stylized card for the main application pillars.
    Handles SVG reading inline and handles routing.
    """
    with col:
        icon_path = icon
        if icon_path.startswith("assets/") or icon_path.startswith("assets\\"):
            # Ensure path resolves from the frontend root
            assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
            icon_path = os.path.join(assets_dir, os.path.basename(icon_path))

        try:
            with open(icon_path, "r", encoding="utf-8") as f:
                svg_content = f.read()
        except FileNotFoundError:
            svg_content = ""

        st.html(
            f"""
<div class="ag-card">
    <div class="ag-card-icon">
        <div style="width: 26px; height: 26px; color: #40916C; display: flex; align-items: center; justify-content: center;">
            {svg_content}
        </div>
    </div>
    <div class="ag-card-title">{title}</div>
    <div class="ag-card-desc">{desc}</div>
</div>
<br/>
            """
        )
        if st.button(btn_text, key=f"btn_{page_route}"):
            st.switch_page(page_route)
