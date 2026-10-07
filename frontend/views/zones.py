"""
Zones view — zone listing with filters and zone detail inspection.

Implements Page 2 of the frontend handoff: Zones list + zone detail.
"""
import logging

import pandas as pd
import requests
import streamlit as st
from components.badges import priority_badge
from components.errors import render_error_page
from components.icons import render_icon_subheader, render_icon_title
from utils import api_client
from utils.i18n import t
from utils.mock_data import CROPS, SEASONS

logger = logging.getLogger(__name__)


def render_zones() -> None:
    try:
        render_icon_title("assets/map.svg", "Agricultural Zones", "Explore, filter, and inspect zones across Rwanda")

        zones = api_client.get_zones()

        with st.expander("Register a zone", expanded=False):
            st.caption("Add a district level map point. Use decimal latitude and longitude for the location.")
            with st.form("create_zone_form"):
                zone_cols = st.columns(2)
                with zone_cols[0]:
                    new_district = st.text_input("District", placeholder="e.g. Musanze")
                    new_sector = st.text_input("Sector (optional)")
                    new_cell = st.text_input("Cell (optional)")
                    new_crop = st.selectbox("Crop (optional)", [""] + api_client.get_crops())
                with zone_cols[1]:
                    new_latitude = st.number_input("Latitude", min_value=-90.0, max_value=90.0, value=-1.95, format="%.6f")
                    new_longitude = st.number_input("Longitude", min_value=-180.0, max_value=180.0, value=29.88, format="%.6f")
                    new_season = st.text_input("Season (optional)", placeholder="e.g. Season A 2026")
                create_submitted = st.form_submit_button("Register zone", type="primary")

            if create_submitted:
                if not new_district.strip():
                    st.error("Enter a district name before registering the zone.")
                else:
                    created = api_client.create_zone({
                        "district": new_district.strip(),
                        "sector": new_sector.strip() or None,
                        "cell": new_cell.strip() or None,
                        "latitude": new_latitude,
                        "longitude": new_longitude,
                        "crop_type": new_crop or None,
                        "season": new_season.strip() or None,
                    })
                    if created:
                        st.success("Zone registered.")
                        st.rerun()
                    else:
                        st.error("The zone could not be registered. Check backend access and try again.")

        # ── Filters ──────────────────────────────────────────────────
        filter_cols = st.columns(4)
        all_districts = sorted({z.get("district", "") for z in zones})
        all_crops = sorted({z.get("crop", "") for z in zones})
        all_priorities = ["High", "Medium", "Low"]

        with filter_cols[0]:
            selected_districts = st.multiselect("District", all_districts, default=all_districts[:5])
        with filter_cols[1]:
            selected_crops = st.multiselect("Crop", all_crops, default=all_crops[:3])
        with filter_cols[2]:
            selected_priorities = st.multiselect("Priority", all_priorities, default=all_priorities)
        with filter_cols[3]:
            search_query = st.text_input("Search zones", placeholder="e.g. Musanze")

        # ── Apply filters ────────────────────────────────────────────
        filtered = [
            z for z in zones
            if (not selected_districts or z.get("district") in selected_districts)
            and (not selected_crops or z.get("crop") in selected_crops)
            and (not selected_priorities or z.get("priority") in selected_priorities)
            and (not search_query or search_query.lower() in z.get("name", "").lower())
        ]

        st.caption(f"Showing {len(filtered)} of {len(zones)} zones")

        if not filtered:
            st.info("No zones match the current filters.")
            return

        # ── Zone table ───────────────────────────────────────────────
        df = pd.DataFrame(filtered)
        display_cols = ["name", "district", "sector", "cell", "crop", "priority", "predicted_production_kg", "risk_status"]
        available_cols = [c for c in display_cols if c in df.columns]
        display_df = df[available_cols].copy()

        col_rename = {
            "name": "Zone",
            "district": "District",
            "sector": "Sector",
            "cell": "Cell",
            "crop": "Crop",
            "priority": "Priority",
            "predicted_production_kg": "Estimated production (kg)",
            "risk_status": "Risk",
        }
        display_df.rename(columns=col_rename, inplace=True)
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.divider()

        # ── Zone detail panel ────────────────────────────────────────
        render_icon_subheader("assets/compass.svg", "Zone Detail")

        zone_names = [z.get("name", f"Zone {z.get('id')}") for z in filtered]
        selected_zone_name = st.selectbox("Select a zone to inspect", zone_names)
        selected_zone = next((z for z in filtered if z.get("name") == selected_zone_name), None)

        if selected_zone:
            zone_id = selected_zone.get("id", 0)

            # Metadata header
            meta_cols = st.columns(4)
            with meta_cols[0]:
                st.metric("District", selected_zone.get("district", "N/A"))
            with meta_cols[1]:
                st.metric("Crop", selected_zone.get("crop_type", selected_zone.get("crop", "N/A")))
            with meta_cols[2]:
                st.metric("Area (ha)", selected_zone.get("area_ha", "N/A"))
            with meta_cols[3]:
                st.metric("Estimated production (kg)", f"{selected_zone.get('predicted_production_kg', 0) or 0:,.0f}")

            with st.expander("Run a yield prediction"):
                with st.form("zone_yield_prediction"):
                    prediction_cols = st.columns(3)
                    with prediction_cols[0]:
                        prediction_crop = st.selectbox("Crop", api_client.get_crops(), key="prediction_crop")
                    with prediction_cols[1]:
                        prediction_season = st.text_input("Season", value=selected_zone.get("season") or "Season A 2026")
                    with prediction_cols[2]:
                        prediction_rainfall = st.number_input("Rainfall (mm)", min_value=0.0, value=0.0)
                    prediction_area = st.number_input(
                        "Cultivated area (ha)", min_value=0.0,
                        value=float(selected_zone.get("area_ha") or 0.5),
                    )
                    predict_submitted = st.form_submit_button("Predict yield", type="primary")
                if predict_submitted:
                    prediction = api_client.predict_yield({
                        "zone_id": zone_id,
                        "season": prediction_season,
                        "crop": prediction_crop,
                        "rainfall_mm": prediction_rainfall or None,
                        "area_cultivated": prediction_area or None,
                    })
                    if prediction:
                        st.success(f"Estimated production: {prediction.get('predicted_yield', 0):,.0f} kg · {prediction.get('priority_level', 'Unknown')} priority")
                        if prediction.get("yield_per_ha") is not None:
                            st.caption(f"Estimated yield: {prediction['yield_per_ha']:,.0f} kg/ha")
                        st.caption(f"Confidence {prediction.get('confidence', 0):.0%} · Model {prediction.get('model_version', 'unknown')}")
                    else:
                        st.error("Prediction failed. Check the selected zone and backend connection.")

            detail_cols = st.columns(3)

            # Priority + Risk
            with detail_cols[0]:
                with st.container(border=True):
                    st.markdown("**Priority Status**")
                    priority_badge(selected_zone.get("priority", "Low"))
                    st.caption(f"Risk: {selected_zone.get('risk_status', 'Unknown')}")

            # Finance readiness
            with detail_cols[1]:
                with st.container(border=True):
                    st.markdown("**Credit Readiness**")
                    readiness = api_client.get_finance_readiness(zone_id)
                    if readiness:
                        score = readiness.get("credit_insurance_score", "N/A")
                        st.metric("Score", f"{score}%")
                        st.caption(readiness.get("recommendation", ""))
                    else:
                        st.caption("No readiness data available.")

            # Nutrition risk
            with detail_cols[2]:
                with st.container(border=True):
                    st.markdown("**Nutrition Risk**")
                    nutrition = api_client.get_nutrition_risk(zone_id)
                    if nutrition:
                        risk_level = nutrition.get("nutrition_risk_level", "Unknown")
                        st.metric("Risk Level", risk_level)
                        st.caption(nutrition.get("summary", ""))
                    else:
                        st.caption("No nutrition data available.")

            # Recommendations
            st.divider()
            render_icon_subheader("assets/brain.svg", "Recommendations")
            rec_data = api_client.get_zone_recommendations(zone_id)
            if rec_data:
                recs = rec_data.get("recommendations", [])
                if recs:
                    for i, rec in enumerate(recs, 1):
                        st.markdown(f"**{i}.** {rec}")
                else:
                    st.info("No specific recommendations for this zone yet.")
            else:
                st.info("Unable to fetch recommendations for this zone.")

            # Weather context
            district = selected_zone.get("district", "")
            if district:
                st.divider()
                render_icon_subheader("assets/compass.svg", f"Weather — {district}")
                weather = api_client.get_weather(district)
                if weather:
                    w_cols = st.columns(4)
                    with w_cols[0]:
                        st.metric("Temperature", f"{weather.get('temperature_c', 'N/A')} C")
                    with w_cols[1]:
                        st.metric("Humidity", f"{weather.get('humidity_pct', 'N/A')}%")
                    with w_cols[2]:
                        st.metric("Rain", f"{weather.get('rainfall_mm_week', weather.get('rainfall_mm', 'N/A'))} mm")
                    with w_cols[3]:
                        st.metric("Wind", f"{weather.get('wind_speed_kmh', weather.get('wind_kph', 'N/A'))} km/h")
                    st.caption(weather.get("forecast_summary") or weather.get("summary", ""))
                else:
                    st.caption("Weather data unavailable.")

    except requests.exceptions.RequestException as e:
        logger.error("Network error in zones view: %s", e)
        render_error_page("network", str(e))
    except Exception as e:
        logger.error("Unexpected error in zones view: %s", e, exc_info=True)
        render_error_page("system", str(e))
