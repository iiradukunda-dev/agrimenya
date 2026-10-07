import requests
import streamlit as st
from components.errors import render_error_page
from components.icons import render_icon_title
from utils import api_client
from utils.i18n import t


def render_plan():
    try:
        render_icon_title("assets/calendar.svg", t("plan.header"), t("plan.subtitle"))

        zones = api_client.get_zones()
        zone_options = {
            f"{z.get('district', 'Unknown district')} / {z.get('sector') or z.get('cell') or z.get('id')}": z
            for z in zones
        }
        season_options = [
            ("Season A", t("plan.season_a")),
            ("Season B", t("plan.season_b")),
            ("Season C", t("plan.season_c")),
        ]
        season_labels = [opt[1] for opt in season_options]
        if zone_options:
            with st.container(border=True):
                context_cols = st.columns(2)
                with context_cols[0]:
                    selected_zone_label = st.selectbox(t("plan.select_zone"), list(zone_options))
                with context_cols[1]:
                    selected_season_label = st.selectbox(t("plan.season"), season_labels)
            selected_zone_id = zone_options[selected_zone_label]["id"]
        else:
            selected_zone_label = ""
            selected_season_label = season_labels[0]
            selected_zone_id = None
            st.info("Create or load a zone before planning.")

        st.subheader(f"Saved plans for {selected_zone_label or 'a zone'}")

        df_roadmap = api_client.get_roadmap(selected_zone_id)

        if df_roadmap.empty:
            st.info(t("plan.empty"))
        else:
            st.dataframe(df_roadmap, use_container_width=True, hide_index=True)
            st.divider()
            
            st.subheader(t("plan.detailed_steps"))
            for idx, row in df_roadmap.iterrows():
                st.checkbox(
                    f"**{row.get('Timeframe', 'Not specified')}**: {row.get('Task', t('common.unknown_task'))}", 
                    key=f"task_{idx}"
                )

        st.divider()
        st.subheader("Save a plan for a zone")
        if not zone_options:
            st.info("Create or load a zone before saving a plan.")
        else:
            with st.form("save_plan_form"):
                title = st.text_input("Plan title", value=f"{selected_season_label} support plan")
                step_title = st.text_input("First action", value="Prepare land")
                step_description = st.text_area("Action details", value="Prepare the field before planting.")
                timeframe = st.text_input("Timeframe", value="Week 1")
                submitted = st.form_submit_button(t("plan.save_btn"), type="primary")
            if submitted:
                payload = {
                    "zone_id": selected_zone_id,
                    "title": title,
                    "roadmap": [{"step_number": 1, "title": step_title, "description": step_description, "timeframe": timeframe}],
                    "resources": {},
                    "created_by": "frontend",
                }
                result = api_client.create_roadmap(payload)
                if result:
                    st.success("Plan saved successfully.")
                    api_client.get_roadmap.clear()
                else:
                    st.error("The plan could not be saved. Check the zone and backend connection.")
    except requests.exceptions.RequestException as e:
        import logging
        logging.getLogger(__name__).error(f"Network error in plan.py: {e}")
        render_error_page("network", str(e))
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Unexpected error in plan.py: {e}", exc_info=True)
        render_error_page("system", str(e))
