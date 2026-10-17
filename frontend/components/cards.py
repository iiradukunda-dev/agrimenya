import streamlit as st

def pillar_card(col, title: str, desc: str, btn_text: str, page_route: str) -> None:
    with col:
        with st.container(border=True):
            st.markdown(f"### {title}")
            st.write(desc)
            st.write("")
            if st.button(btn_text, key=f"btn_{page_route}", width="stretch"):
                st.switch_page(page_route)
