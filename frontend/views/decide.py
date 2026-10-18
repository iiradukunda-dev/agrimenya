import requests
import streamlit as st
from components.badges import priority_badge
from components.errors import render_error_page
from components.icons import render_icon_subheader, render_icon_title
from utils import api_client
from utils.i18n import t


def render_decide():
    try:
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
                        priority_badge(rec.get('priority', 'Not assessed'))
                        st.caption(f"{t('common.status')}: {rec.get('status', t('common.pending'))}")
                        if st.button(t("decisions.act_btn"), key=f"act_{rec.get('area', 'X')}_{rec.get('crop', 'Y')}"):
                            st.switch_page("pages/8_Planning.py")

        st.divider()

        render_icon_subheader("assets/bot.svg", t("decisions.ai_title"))
        st.markdown(t("decisions.ai_desc"))
        zones = api_client.get_zones()
        zone_options = {
            f"{z.get('district', 'Unknown district')} / {z.get('sector') or z.get('cell') or z.get('id')}": z.get("id")
            for z in zones
        }
        if not zone_options:
            st.info("Load a zone before using the AI decision advisor.")
        else:
            selected_zone = st.selectbox("Zone context", list(zone_options), key="decision_ai_zone")
            zone_id = str(zone_options[selected_zone])
            field_signal = api_client.get_field_risk(zone_id)
            st.markdown(f"#### {t('decisions.field_signal')}")
            st.caption(t("decisions.field_signal_note"))
            if field_signal and field_signal.get("total_reports", 0):
                st.metric(t("decisions.field_signal_metric"), field_signal.get("risk_level", "Unknown"),
                          delta=t("decisions.field_signal_count", count=field_signal.get("total_reports", 0)))
                latest = field_signal.get("latest_report") or {}
                details = " · ".join(str(latest.get(key)) for key in ("district", "crop", "observed_on") if latest.get(key))
                if details:
                    st.caption(details)
                if latest.get("symptoms") or latest.get("notes"):
                    st.info(" ".join(str(latest.get(key)) for key in ("symptoms", "notes") if latest.get(key)))
            elif field_signal is not None:
                st.caption(t("decisions.field_signal_empty"))
            else:
                st.caption(t("decisions.field_signal_unavailable"))
            messages_key = "decision_ai_messages"
            if messages_key not in st.session_state:
                st.session_state[messages_key] = []

            for message in st.session_state[messages_key]:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            prompt = st.chat_input(t("decisions.ai_placeholder"), key="decision_ai_input")
            if prompt:
                st.session_state[messages_key].append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                with st.chat_message("assistant"):
                    with st.spinner("Checking the selected zone..."):
                        response = api_client.chat(prompt, zone_id=zone_id)
                    if response:
                        answer = response.get("answer", "I could not generate a response.")
                        if response.get("source") == "grounded-context":
                            st.warning(
                                "The chat is connected to the backend, but the AI provider did not return a generated answer. "
                                "Showing the zone data available to the assistant. Check backend LLM access and provider credits."
                            )
                        st.markdown(answer)
                        st.caption(f"Source: {response.get('source', 'unknown')}")
                    else:
                        answer = "The API could not answer this request. Check the backend connection and try again."
                        st.error(answer)
                    st.session_state[messages_key].append({"role": "assistant", "content": answer})

            if st.session_state[messages_key] and st.button("Clear conversation", key="clear_decision_ai"):
                st.session_state[messages_key] = []
                st.rerun()
    except requests.exceptions.RequestException as e:
        import logging
        logging.getLogger(__name__).error(f"Network error in decide.py: {e}")
        render_error_page("network", str(e))
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Unexpected error in decide.py: {e}", exc_info=True)
        render_error_page("system", str(e))
