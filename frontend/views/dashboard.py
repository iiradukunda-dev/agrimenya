"""Compact overview: current saved-zone counts and live district weather."""
import logging

import requests
import streamlit as st
from components.errors import render_error_page
from utils import api_client

logger = logging.getLogger(__name__)


def _render_weather(districts: list[str]) -> None:
    if not districts:
        st.info("Add a district to a saved zone to load local weather.")
        return
    district = st.selectbox("District", districts, key="dashboard_weather_district")
    if st.button("Refresh weather", key="dashboard_weather_refresh"):
        api_client.get_weather.clear()
        st.rerun()
    weather = api_client.get_weather(district)
    if not weather or weather.get("source") == "unavailable":
        st.info("Current weather is unavailable.")
        return
    measures = st.columns(4)
    for column, label, key, suffix in zip(
        measures,
        ("Temperature", "Humidity", "Rainfall", "Wind"),
        ("temperature_c", "humidity_pct", "rainfall_mm", "wind_kph"),
        (" °C", "%", " mm", " km/h"),
    ):
        value = weather.get(key)
        column.metric(label, f"{value}{suffix}" if value is not None else "—")
    st.caption(f"Open-Meteo · {weather.get('updated_at') or 'time unavailable'} · district-centroid estimate")
    forecast = weather.get("forecast") or []
    if forecast:
        st.dataframe(forecast, width="stretch", hide_index=True)


def render_dashboard() -> None:
    try:
        st.title("Overview")
        zones = api_client.get_zones()
        priority_data = api_client.get_priority_data()
        districts = sorted({str(zone.get("district")).strip() for zone in zones if zone.get("district")})
        high_count = int(
            (priority_data["Priority"].astype(str).str.casefold() == "high").sum()
        ) if "Priority" in priority_data.columns else 0
        summary = st.columns(2)
        summary[0].metric("Saved zones", len(zones))
        summary[1].metric("High-priority zones", high_count if not priority_data.empty else "—")
        with st.expander("Current weather", expanded=False):
            _render_weather(districts)
    except requests.exceptions.RequestException as exc:
        logger.error("Network error in dashboard: %s", exc)
        render_error_page("network", str(exc))
    except Exception as exc:
        logger.error("Unexpected error in dashboard: %s", exc, exc_info=True)
        render_error_page("system", str(exc))
