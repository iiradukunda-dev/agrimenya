"""Small brand and language header; page navigation stays in Streamlit's sidebar."""
from pathlib import Path

import streamlit as st
from PIL import Image

from utils.i18n import render_language_selector


@st.cache_data(show_spinner=False)
def _brand_mark() -> Image.Image:
    image = Image.open(Path(__file__).resolve().parents[1] / "assets" / "logo.jpg").convert("RGB")
    bounds = image.convert("L").point(lambda value: 255 if value < 245 else 0).getbbox()
    if bounds:
        image = image.crop(bounds)
    side = max(image.size)
    square = Image.new("RGB", (side, side), "white")
    square.paste(image, ((side - image.width) // 2, (side - image.height) // 2))
    return square


def render_navbar() -> None:
    left, _, right = st.columns([1.5, 5.5, 1], vertical_alignment="center")
    with left:
        icon, title = st.columns([.25, 1], vertical_alignment="center", gap="small")
        with icon:
            st.image(_brand_mark(), width=38)
        with title:
            st.markdown(
                '<div style="color:#163b2a;font-weight:760;font-size:1.05rem">Agri-Menya</div>'
                '<div style="color:#647067;font-size:.68rem;letter-spacing:.045em">AGRICULTURAL INTELLIGENCE</div>',
                unsafe_allow_html=True,
            )
    with right:
        render_language_selector(sidebar=False)
    st.markdown('<hr style="border:0;border-top:1px solid #e2e8df;margin:.8rem 0 1.2rem">', unsafe_allow_html=True)
