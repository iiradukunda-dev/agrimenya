import streamlit as st
from utils.theme import load_theme
from utils.i18n import t, render_language_selector
from utils import api_client
from components.badges import priority_badge
from components.icons import render_icon_title, render_icon_subheader

st.set_page_config(page_title=t("decisions.page_title"), page_icon="assets/brain.svg", layout="wide")
load_theme()
render_language_selector()

render_icon_title("assets/brain.svg", t("decisions.header"), t("decisions.subtitle"))

recs = api_client.get_recommendations()

if not recs:
    st.info(t("decisions.empty"))
else:
    for rec in recs:
        with st.container(border=True):
            col1, col2, col3 = st.columns([1, 4, 1])
            with col1:
                st.markdown(f"**{rec.get('area', t('common.unknown_area'))}**")
                st.caption(f"{t('common.crop')}: {rec.get('crop', t('common.unknown_crop'))}")
            with col2:
                st.markdown(f"{rec.get('text', '')}")
            with col3:
                priority_badge(rec.get('priority', 'Low'))
                st.caption(f"{t('common.status')}: {rec.get('status', t('common.pending'))}")
                st.button(t("decisions.act_btn"), key=f"act_{rec.get('area', 'X')}_{rec.get('crop', 'Y')}")

st.divider()

render_icon_subheader("assets/bot.svg", t("decisions.ai_title"))
st.markdown(t("decisions.ai_desc"))
prompt = st.chat_input(t("decisions.ai_placeholder"))
if prompt:
    with st.chat_message("user"):
        st.write(prompt)
    with st.chat_message("assistant"):
        st.write(t("decisions.ai_response", prompt=prompt))
