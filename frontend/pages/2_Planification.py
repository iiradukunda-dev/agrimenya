import streamlit as st
import requests
from utils.theme import load_theme
from utils.i18n import t, render_language_selector
import plotly.express as px
from utils import api_client
from components.icons import render_icon_title
from components.errors import render_error_page

st.set_page_config(page_title=t("plan.page_title"), page_icon="assets/calendar.svg", layout="wide")
load_theme()
render_language_selector()

def main():
    render_icon_title("assets/calendar.svg", t("plan.header"), t("plan.subtitle"))

    # Sidebar Filters
    st.sidebar.header(t("plan.context_header"))

    zone_options = [
        ("All Regions", t("plan.zone_all")),
        ("Northern Province", t("plan.zone_north")),
        ("Eastern Province", t("plan.zone_east")),
        ("Southern Province", t("plan.zone_south")),
        ("Western Province", t("plan.zone_west")),
    ]
    zone_labels = [opt[1] for opt in zone_options]
    selected_zone_label = st.sidebar.selectbox(t("plan.select_zone"), zone_labels)

    season_options = [
        ("Season A", t("plan.season_a")),
        ("Season B", t("plan.season_b")),
        ("Season C", t("plan.season_c")),
    ]
    season_labels = [opt[1] for opt in season_options]
    selected_season_label = st.sidebar.selectbox(t("plan.season"), season_labels)

    st.subheader(t("plan.roadmap_title", zone=selected_zone_label, season=selected_season_label))

    df_roadmap = api_client.get_roadmap()

    if df_roadmap.empty:
        st.info(t("plan.empty"))
    else:
        # Gantt-style chart using Plotly timeline with robust agricultural color mapping
        phase_colors = {
            # English
            "Preparation": "#C4924A",
            "Execution": "#52B788",
            "Monitoring": "#52B788",
            # Kinyarwanda
            "Imyiteguro": "#C4924A",
            "Gushyira mu Bikorwa": "#52B788",
            "Gukurikirana": "#52B788",
            # French
            "Préparation": "#C4924A",
            "Exécution": "#52B788",
            "Suivi & Évaluation": "#52B788",
        }
        
        fig = px.timeline(
            df_roadmap, 
            x_start="Start", 
            x_end="End", 
            y="Task", 
            color="Phase",
            color_discrete_map=phase_colors,
            title=t("plan.chart_title")
        )
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        st.subheader(t("plan.detailed_steps"))
        for idx, row in df_roadmap.iterrows():
            st.checkbox(
                f"**{row.get('Phase', '')}**: {row.get('Task', t('common.unknown_task'))} ({t('plan.due')}: {row.get('End', 'N/A')})", 
                key=f"task_{idx}"
            )

    if st.button(t("plan.save_btn"), type="primary"):
        st.success(f"{t('plan.header')} - {selected_zone_label} ({selected_season_label})")

try:
    main()
except requests.exceptions.RequestException as e:
    render_error_page("network", str(e))
except Exception as e:
    render_error_page("system", str(e))
