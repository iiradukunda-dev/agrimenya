"""
Dashboard view - high-level operational overview.

Surfaces KPIs, priority map, alerts, and quick actions in a single pane.
"""
import logging

import pandas as pd
import requests
import streamlit as st
from components.alerts import render_alert
from components.badges import priority_badge
from components.charts import render_yield_chart
from components.errors import render_error_page
from components.icons import render_icon_subheader
from components.maps import render_priority_map
from utils import api_client
from utils.i18n import t

logger = logging.getLogger(__name__)


def _metric_number(value, suffix: str = "", grouped: bool = False) -> str:
    if value is None:
        return "N/A"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "N/A"
    formatted = f"{number:,.0f}" if grouped else f"{number:.0f}"
    return f"{formatted}{suffix}"


def render_dashboard() -> None:
    try:
        st.markdown(
            '<h1 style="font-family: \'Plus Jakarta Sans\', sans-serif; '
            'background: linear-gradient(135deg, #2D6A4F, #52B788); '
            '-webkit-background-clip: text; -webkit-text-fill-color: transparent; '
            'margin-bottom: 0.25rem;">Dashboard</h1>'
            '<p style="color: #6B7280; margin-top: 0;">Operational overview of agricultural zones across Rwanda</p>',
            unsafe_allow_html=True,
        )

        # ── KPI summary cards ────────────────────────────────────────
        dashboard_data = api_client.get_alignment_dashboard()
        kpi_cols = st.columns(5)

        kpi_items = [
            ("Zones with alignment data", dashboard_data.get("total_zones", 0), None),
            ("High Nutrition Risk", dashboard_data.get("zones_high_nutrition_risk") if dashboard_data.get("zones_high_nutrition_risk") is not None else "N/A", None),
            ("Credit Readiness", _metric_number(dashboard_data.get("avg_credit_insurance_score"), "%"), None),
            ("Export Ready", dashboard_data.get("zones_export_ready") if dashboard_data.get("zones_export_ready") is not None else "N/A", None),
            ("Observed Worker-days", _metric_number(dashboard_data.get("observed_worker_days", 0), grouped=True), None),
        ]

        for col, (label, value, delta) in zip(kpi_cols, kpi_items):
            with col:
                st.metric(label, value, delta)

        if dashboard_data.get("estimate_status") == "unavailable_pending_validated_data_and_methods":
            st.caption("Risk, credit, export, and jobs estimates are not shown because validated measures are not configured.")

        st.divider()

        # ── Map + Priority Breakdown ─────────────────────────────────
        render_icon_subheader("assets/compass.svg", "Live Weather")
        weather_zones = api_client.get_zones()
        districts = sorted({
            str(zone.get("district", "")).strip()
            for zone in weather_zones
            if zone.get("district")
        })
        default_district = "Kigali City" if "Kigali City" in districts else (districts[0] if districts else "Kigali City")
        weather_controls = st.columns([3, 1])
        with weather_controls[0]:
            district = st.selectbox(
                "District weather",
                districts or ["Kigali City"],
                index=(districts.index(default_district) if districts else 0),
                key="dashboard_weather_district",
            )
        with weather_controls[1]:
            st.write("")
            if st.button("Refresh weather", width="stretch"):
                api_client.get_weather.clear()
                st.rerun()

        with st.spinner(f"Loading weather for {district}..."):
            weather = api_client.get_weather(district)
        if weather:
            values = st.columns(4)
            temperature = weather.get("temperature_c")
            humidity = weather.get("humidity_pct")
            rainfall = weather.get("rainfall_mm")
            wind = weather.get("wind_kph")
            values[0].metric("Temperature", f"{temperature} C" if temperature is not None else "N/A")
            values[1].metric("Humidity", f"{humidity}%" if humidity is not None else "N/A")
            values[2].metric("Current precipitation", f"{rainfall} mm" if rainfall is not None else "N/A")
            values[3].metric("Wind speed", f"{wind} km/h" if wind is not None else "N/A")

            if weather.get("source") == "open-meteo":
                st.caption(f"Live provider: Open-Meteo | Local observation time: {weather.get('updated_at') or 'not supplied'}")
            else:
                st.warning("The live weather provider is unavailable. Showing a fallback snapshot; do not use it as current conditions.")

            forecast = weather.get("forecast") or []
            if forecast:
                forecast_df = pd.DataFrame(forecast).rename(columns={
                    "date": "Date",
                    "temperature_max_c": "High (C)",
                    "temperature_min_c": "Low (C)",
                    "precipitation_probability_pct": "Rain chance (%)",
                    "precipitation_sum_mm": "Rain (mm)",
                })
                st.dataframe(forecast_df, width="stretch", hide_index=True)
            st.caption("Forecast values are model estimates for the selected district centroid.")
        else:
            st.error("Weather data could not be loaded from the backend.")

        st.divider()

        map_col, chart_col = st.columns([3, 2])

        df = api_client.get_priority_data()

        with map_col:
            render_icon_subheader("assets/map.svg", "Zone Priority Map")
            clicked_zone_id = render_priority_map(df, key="dashboard_priority_map")
            if clicked_zone_id:
                st.session_state["selected_zone_id"] = clicked_zone_id
                st.session_state["segment_zone_select"] = clicked_zone_id

            selected_zone_id = st.session_state.get("selected_zone_id")
            if selected_zone_id:
                selected_row = next(
                    (row for row in df.to_dict("records") if str(row.get("id")) == str(selected_zone_id)),
                    None,
                )
                if selected_row:
                    st.info(
                        f"Selected: {selected_row.get('District', 'Unknown')} | "
                        f"{selected_row.get('Crop', 'Crop not set')} | "
                        f"{selected_row.get('Priority', 'No prediction')} priority"
                    )
                    if st.button("Inspect this zone in Segmentation", key="open_selected_zone_segmentation"):
                        st.switch_page("pages/5_Segmentation.py")

        with chart_col:
            render_icon_subheader("assets/brain.svg", "Yield by District")
            render_yield_chart(df)

        st.divider()

        # ── Alerts + Quick Actions ───────────────────────────────────
        alerts_col, actions_col = st.columns([3, 2])

        with alerts_col:
            render_icon_subheader("assets/bell.svg", "Recent Alerts")
            alerts = api_client.get_alerts()
            if not alerts:
                st.info("No active alerts.")
            else:
                for alert in alerts[:5]:
                    render_alert(alert)

        with actions_col:
            render_icon_subheader("assets/compass.svg", "Quick Actions")
            st.markdown('<div style="display: flex; flex-direction: column; gap: 8px;">', unsafe_allow_html=True)

            if st.button("Predict Zone Yield", icon=":material/query_stats:", width="stretch"):
                st.switch_page("pages/4_Zones.py")
            if st.button("Create New Plan", icon=":material/edit_calendar:", width="stretch"):
                st.switch_page("pages/8_Planning.py")
            if st.button("Detect Crop Disease", icon=":material/biotech:", width="stretch"):
                st.switch_page("pages/7_AI_Assistant.py")
            if st.button("Send Alert", icon=":material/campaign:", width="stretch"):
                st.switch_page("pages/9_Communication.py")

            st.markdown("</div>", unsafe_allow_html=True)

        st.divider()

        # ── Priority Ranking Table ───────────────────────────────────
        render_icon_subheader("assets/brain.svg", "Top Priority Zones")
        recs = api_client.get_recommendations()
        if recs:
            for rec in recs[:5]:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([1, 4, 1])
                    with c1:
                        st.markdown(f"**{rec.get('area', 'Unknown')}**")
                        st.caption(f"Crop: {rec.get('crop', 'N/A')}")
                    with c2:
                        st.markdown(rec.get("text", ""))
                    with c3:
                        priority_badge(rec.get("priority", "Not assessed"))

    except requests.exceptions.RequestException as e:
        logger.error("Network error in dashboard: %s", e)
        render_error_page("network", str(e))
    except Exception as e:
        logger.error("Unexpected error in dashboard: %s", e, exc_info=True)
        render_error_page("system", str(e))
