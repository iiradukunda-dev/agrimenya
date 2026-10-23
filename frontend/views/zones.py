"""
Zones view - zone listing with filters and zone detail inspection.

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
from utils.mock_data import CROPS

logger = logging.getLogger(__name__)

FINANCE_EVIDENCE = {
    "member_registration": "Member registration",
    "land_or_tenure_records": "Land or tenure records",
    "production_history": "Production history",
    "sales_records": "Sales records",
    "bank_or_sacco_statement": "Bank or SACCO statement",
    "loan_repayment_history": "Loan repayment history",
    "group_savings_or_guarantee": "Group savings or guarantee",
}
EXPORT_EVIDENCE = {
    "cooperative_registration": "Cooperative registration",
    "traceability_records": "Traceability records",
    "quality_grading_records": "Quality grading records",
    "phytosanitary_documents": "Phytosanitary documents",
    "buyer_contract_or_order": "Buyer contract or order",
    "certification_records": "Certification records",
}


def _optional_measurement(value: str, label: str, maximum: float) -> tuple[float | None, str | None]:
    if not value.strip():
        return None, None
    try:
        number = float(value)
    except ValueError:
        return None, f"{label} must be a number."
    if not 0 <= number <= maximum:
        return None, f"{label} must be between 0 and {maximum:g}."
    return number, None


def _render_field_reports(zone: dict, crops: list[str]) -> None:
    zone_id = str(zone["id"])
    reports = api_client.get_field_reports(zone_id)
    if reports:
        fields = ["submitted_at", "crop", "rainfall_mm", "soil_moisture_pct", "symptoms", "notes"]
        display = pd.DataFrame(reports)
        display = display[[field for field in fields if field in display.columns]].rename(columns={
            "submitted_at": "Submitted", "crop": "Crop", "rainfall_mm": "Rainfall (mm)",
            "soil_moisture_pct": "Soil moisture (%)", "symptoms": "Symptoms", "notes": "Notes",
        })
        st.dataframe(display, width="stretch", hide_index=True)
    else:
        st.caption("No field observations have been recorded for this zone.")

    crop_default = zone.get("crop_type") or zone.get("crop")
    crop_options = crops or ([str(crop_default)] if crop_default else [])
    if not crop_options:
        st.info("Add a crop to this zone before recording observations.")
        return
    crop_index = crop_options.index(crop_default) if crop_default in crop_options else 0
    with st.form(f"field_report_form_{zone_id}", clear_on_submit=True):
        crop = st.selectbox("Observed crop", crop_options, index=crop_index)
        measure_cols = st.columns(2)
        with measure_cols[0]:
            rainfall_text = st.text_input("Rainfall (mm, optional)", placeholder="Leave blank if unknown")
        with measure_cols[1]:
            moisture_text = st.text_input("Soil moisture (%, optional)", placeholder="Leave blank if unknown")
        symptoms = st.text_area("Symptoms observed (optional)", max_chars=500)
        notes = st.text_area("Field notes (optional)", max_chars=1000)
        submitted = st.form_submit_button("Save field observation", type="primary")
    if submitted:
        rainfall, rainfall_error = _optional_measurement(rainfall_text, "Rainfall", 1000)
        moisture, moisture_error = _optional_measurement(moisture_text, "Soil moisture", 100)
        if rainfall_error or moisture_error:
            st.error(rainfall_error or moisture_error)
        elif not any([rainfall is not None, moisture is not None, symptoms.strip(), notes.strip()]):
            st.error("Enter at least one observation before saving.")
        else:
            result = api_client.submit_field_report({
                "zone_id": zone_id,
                "district": zone.get("district", ""),
                "crop": crop,
                "rainfall_mm": rainfall,
                "soil_moisture_pct": moisture,
                "symptoms": symptoms.strip() or None,
                "notes": notes.strip() or None,
            })
            if result:
                api_client.get_field_reports.clear()
                st.session_state["field_report_saved"] = True
                st.rerun()
            else:
                st.error("The observation could not be saved. Check the zone details and backend connection.")


def _render_readiness(zone_id: str) -> None:
    record = api_client.get_zone_readiness(zone_id)
    if not record:
        st.info("Evidence checklist is unavailable. Check the API connection and database migration.")
        return
    st.caption(record.get("interpretation", "Checklist progress records documents collected; it is not an approval or score."))
    finance_values = record.get("finance_evidence") or {}
    export_values = record.get("export_evidence") or {}
    finance_progress = record.get("finance_checklist") or {}
    export_progress = record.get("export_checklist") or {}
    progress_cols = st.columns(2)
    progress_cols[0].caption(f"Finance evidence: {finance_progress.get('completed_items', 0)} of {finance_progress.get('total_items', len(FINANCE_EVIDENCE))} recorded")
    progress_cols[1].caption(f"Export evidence: {export_progress.get('completed_items', 0)} of {export_progress.get('total_items', len(EXPORT_EVIDENCE))} recorded")

    with st.form(f"readiness_form_{zone_id}"):
        evidence_cols = st.columns(2)
        with evidence_cols[0]:
            st.markdown("**Finance documentation**")
            finance_form = {
                key: st.checkbox(label, value=bool(finance_values.get(key)), key=f"finance_{zone_id}_{key}")
                for key, label in FINANCE_EVIDENCE.items()
            }
        with evidence_cols[1]:
            st.markdown("**Export documentation**")
            export_form = {
                key: st.checkbox(label, value=bool(export_values.get(key)), key=f"export_{zone_id}_{key}")
                for key, label in EXPORT_EVIDENCE.items()
            }
        submitted = st.form_submit_button("Save evidence checklist", type="primary")
    if submitted:
        result = api_client.update_zone_readiness(zone_id, {
            "finance_evidence": finance_form,
            "export_evidence": export_form,
        })
        if result:
            st.session_state["readiness_saved"] = True
            st.rerun()
        st.error("The evidence checklist could not be saved.")


def _render_work_records(zone: dict, crops: list[str]) -> None:
    zone_id = str(zone["id"])
    records = api_client.get_zone_work_records(zone_id)
    if records:
        display = pd.DataFrame(records)
        fields = ["season", "crop", "worker_days", "notes", "created_at"]
        display = display[[field for field in fields if field in display.columns]].rename(columns={
            "season": "Season", "crop": "Crop", "worker_days": "Observed worker-days",
            "notes": "Notes", "created_at": "Recorded",
        })
        st.dataframe(display, width="stretch", hide_index=True)
    else:
        st.caption("No worker-day records have been entered for this zone.")
    st.caption("These are user-recorded worker-days; they are not an estimate of jobs supported.")
    crop_default = zone.get("crop_type") or zone.get("crop")
    crop_options = crops or ([str(crop_default)] if crop_default else [])
    if not crop_options:
        st.info("Add a crop to this zone before recording worker-days.")
        return
    crop_index = crop_options.index(crop_default) if crop_default in crop_options else 0
    with st.form(f"worker_days_form_{zone_id}", clear_on_submit=True):
        season = st.text_input("Season", value=str(zone.get("season") or ""), placeholder="For example, Season A 2026")
        crop = st.selectbox("Crop", crop_options, index=crop_index)
        worker_days = st.number_input("Observed worker-days", min_value=0.0, max_value=1_000_000.0, value=None, step=1.0, placeholder="Enter the observed total")
        notes = st.text_input("Notes (optional)", max_chars=1000)
        submitted = st.form_submit_button("Save worker-day record", type="primary")
    if submitted:
        if not season.strip() or worker_days is None or worker_days <= 0:
            st.error("Enter a season and an observed worker-day total greater than zero.")
        else:
            result = api_client.create_zone_work_record(zone_id, {
                "season": season.strip(), "crop": crop, "worker_days": worker_days, "notes": notes.strip(),
            })
            if result:
                st.session_state["work_record_saved"] = True
                st.rerun()
            st.error("The worker-day record could not be saved.")


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
                    new_latitude = st.number_input("Latitude", min_value=-90.0, max_value=90.0, value=None, format="%.6f", placeholder="Required")
                    new_longitude = st.number_input("Longitude", min_value=-180.0, max_value=180.0, value=None, format="%.6f", placeholder="Required")
                    new_season = st.text_input("Season (optional)", placeholder="e.g. Season A 2026")
                create_submitted = st.form_submit_button("Register zone", type="primary")

            if create_submitted:
                if not new_district.strip() or new_latitude is None or new_longitude is None:
                    st.error("Enter a district and the zone's latitude and longitude before registering it.")
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
        all_districts = sorted({str(z.get("district")) for z in zones if z.get("district")})
        all_crops = sorted({str(z.get("crop")) for z in zones if z.get("crop")})
        all_priorities = sorted({str(z.get("priority") or "Not assessed") for z in zones})

        with filter_cols[0]:
            selected_districts = st.multiselect("District", all_districts, default=all_districts)
        with filter_cols[1]:
            selected_crops = st.multiselect("Crop", all_crops, default=all_crops)
        with filter_cols[2]:
            selected_priorities = st.multiselect("Priority", all_priorities, default=all_priorities)
        with filter_cols[3]:
            search_query = st.text_input("Search zones", placeholder="e.g. Musanze")

        # ── Apply filters ────────────────────────────────────────────
        filtered = [
            z for z in zones
            if (not selected_districts or z.get("district") in selected_districts)
            and (not selected_crops or z.get("crop") in selected_crops)
            and (not selected_priorities or str(z.get("priority") or "Not assessed") in selected_priorities)
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
        st.dataframe(display_df, width="stretch", hide_index=True)

        st.divider()

        # ── Zone detail panel ────────────────────────────────────────
        render_icon_subheader("assets/compass.svg", "Zone Detail")

        zone_by_id = {str(zone["id"]): zone for zone in filtered if zone.get("id")}
        zone_ids = list(zone_by_id)
        selected_zone_id = st.selectbox(
            "Select a zone to inspect",
            zone_ids,
            key="zones_detail_choice",
            format_func=lambda zone_id: " / ".join(filter(None, [
                str(zone_by_id[zone_id].get("district") or "Unknown district"),
                str(zone_by_id[zone_id].get("sector") or zone_by_id[zone_id].get("cell") or ""),
                str(zone_by_id[zone_id].get("crop_type") or zone_by_id[zone_id].get("crop") or ""),
                str(zone_id)[-8:],
            ])),
        )
        selected_zone = zone_by_id[selected_zone_id]

        if selected_zone:
            zone_id = str(selected_zone["id"])

            # Metadata header
            meta_cols = st.columns(4)
            with meta_cols[0]:
                st.metric("District", selected_zone.get("district", "N/A"))
            with meta_cols[1]:
                st.metric("Crop", selected_zone.get("crop_type", selected_zone.get("crop", "N/A")))
            with meta_cols[2]:
                area_value = selected_zone.get("area_ha")
                st.metric("Recorded area", f"{float(area_value):,.2f} ha" if area_value is not None else "Not recorded")
            with meta_cols[3]:
                production_value = selected_zone.get("predicted_production_kg")
                st.metric("Latest predicted output", f"{float(production_value):,.0f} kg" if production_value is not None else "No prediction")

            if st.session_state.pop("field_report_saved", False):
                st.success("Field observation saved.")
            if st.session_state.pop("readiness_saved", False):
                st.success("Evidence checklist saved.")
            if st.session_state.pop("work_record_saved", False):
                st.success("Observed worker-days saved.")

            with st.expander("Field observations and records", expanded=False):
                field_tab, evidence_tab, workers_tab = st.tabs(["Field observations", "Readiness evidence", "Worker-days"])
                crops = api_client.get_crops() or CROPS
                with field_tab:
                    _render_field_reports(selected_zone, crops)
                with evidence_tab:
                    _render_readiness(zone_id)
                with workers_tab:
                    _render_work_records(selected_zone, crops)

            with st.expander("Run a yield prediction"):
                st.caption(
                    "This is a historical NISR-observation baseline for the selected district, crop, and season. "
                    "It is not a weather-adjusted forecast; satellite imagery is visual context and does not change this estimate."
                )
                with st.form(f"zone_yield_prediction_{zone_id}"):
                    prediction_cols = st.columns(2)
                    with prediction_cols[0]:
                        prediction_crops = api_client.get_crops() or CROPS
                        crop_value = selected_zone.get("crop_type") or selected_zone.get("crop")
                        crop_index = prediction_crops.index(crop_value) if crop_value in prediction_crops else 0
                        prediction_crop = st.selectbox("Crop", prediction_crops, index=crop_index, key=f"prediction_crop_{zone_id}")
                    with prediction_cols[1]:
                        prediction_season = st.text_input("Season", value=str(selected_zone.get("season") or ""), placeholder="Enter the season", key=f"prediction_season_{zone_id}")
                    prediction_area = st.number_input(
                        "Cultivated area (ha)", min_value=0.0, value=float(selected_zone.get("area_ha") or 0.0),
                        placeholder="Required to estimate total output", key=f"prediction_area_{zone_id}",
                    )
                    predict_submitted = st.form_submit_button("Predict yield", type="primary")
                if predict_submitted:
                    if not prediction_season.strip() or prediction_area <= 0:
                        st.error("Enter the season and a cultivated area greater than zero.")
                    else:
                        prediction = api_client.predict_yield({
                            "zone_id": zone_id,
                            "season": prediction_season.strip(),
                            "crop": prediction_crop,
                            "area_cultivated": prediction_area,
                        })
                        if not prediction:
                            st.error("Prediction failed. Check the selected zone and backend connection.")
                        else:
                            predicted_total = prediction.get("predicted_yield")
                            if predicted_total is None:
                                st.warning(prediction.get("warning") or "A yield estimate is not available for this crop, district, and season.")
                            else:
                                st.success(f"Estimated total output: {predicted_total:,.0f} kg | {prediction.get('priority_level', 'Not assessed')} priority")
                            if prediction.get("yield_per_ha") is not None:
                                st.caption(f"Yield estimate: {prediction['yield_per_ha']:,.0f} kg/ha")
                            st.caption(f"Basis: {prediction.get('basis', 'unknown')} | Model: {prediction.get('model_version', 'unknown')} | District observations: {prediction.get('district_observations', 0)}")
                            if prediction.get("warning"):
                                st.info(prediction["warning"])
                            if prediction.get("interpretation_note"):
                                st.caption(prediction["interpretation_note"])
                            if prediction.get("priority_reasons"):
                                st.caption("Priority context: " + "; ".join(prediction["priority_reasons"]))

            detail_cols = st.columns(2, gap="medium")

            # Priority + Risk & Nutrition
            with detail_cols[0]:
                with st.container(border=True):
                    st.markdown("**Priority Status & Risk**")
                    priority_badge(selected_zone.get("priority", "Low"))
                    st.caption(f"Risk: {selected_zone.get('risk_status', 'Unknown')}")
                    st.divider()
                    st.markdown("**Nutrition Risk**")
                    nutrition = api_client.get_nutrition_risk(zone_id)
                    if nutrition:
                        risk_level = nutrition.get("nutrition_risk_level", "Unknown")
                        st.metric("Assessment", risk_level or "Not assessed")
                        st.caption(nutrition.get("note", "Household nutrition risk has not been assessed."))
                    else:
                        st.caption("Not assessed. District yield alone cannot establish household nutrition risk.")

            # Finance readiness
            with detail_cols[1]:
                with st.container(border=True):
                    st.markdown("**Finance evidence**")
                    readiness = api_client.get_zone_readiness(zone_id)
                    if readiness:
                        checklist = readiness.get("finance_checklist") or {}
                        st.metric("Documents recorded", f"{checklist.get('completed_items', 0)} / {checklist.get('total_items', len(FINANCE_EVIDENCE))}")
                        st.caption("Evidence checklist only; this is not a credit score.")
                    else:
                        st.caption("Evidence checklist unavailable.")

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
                render_icon_subheader("assets/compass.svg", f"Weather: {district}")
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
