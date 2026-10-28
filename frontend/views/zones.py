import json
import logging
from typing import Any
import requests
import streamlit as st
from components.badges import priority_badge, status_badge
from components.errors import error_boundary, render_error_page
from components.icons import render_icon_subheader, render_icon_title
from utils import api_client
from utils.i18n import t
from utils.mock_data import CROPS

try:
    import pandas as pd
except ImportError:
    pd = None

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


@st.dialog("Register Field / Zone", width="large")
def show_register_zone_dialog() -> None:
    """Modal popup for registering new agricultural zones with site name & polygon boundary support."""
    with st.form("modal_create_zone_form"):
        st.markdown("##### Location & Geographic Identity")
        c1, c2 = st.columns(2)
        with c1:
            district = st.text_input("District*", placeholder="e.g. Musanze")
            site_name = st.text_input("Site / Farm Name (Optional)", placeholder="e.g. Kinigi Terrace Block 3")
            sector = st.text_input("Sector (Optional)", placeholder="e.g. Kinigi")
            cell = st.text_input("Cell (Optional)", placeholder="e.g. Kaguhu")
        with c2:
            lat = st.number_input("Latitude*", min_value=-5.0, max_value=1.0, value=-1.500000, format="%.6f")
            lon = st.number_input("Longitude*", min_value=28.0, max_value=32.0, value=29.600000, format="%.6f")
            crop = st.selectbox("Primary Crop", [""] + (api_client.get_crops() or CROPS))
            season = st.text_input("Season", value="Season A 2026")

        st.markdown("##### Boundary Outline (Optional GeoJSON)")
        boundary_input = st.text_area(
            "GeoJSON Polygon Coordinates",
            placeholder='{"type": "Polygon", "coordinates": [[[29.60, -1.50], [29.61, -1.50], [29.61, -1.51], [29.60, -1.50]]]}',
            height=70,
            help="Closed GeoJSON Polygon ring with coordinates within Rwanda.",
        )

        submitted = st.form_submit_button("Register Field / Zone", type="primary", use_container_width=True)

    if submitted:
        if not district.strip():
            st.error("District name is required.")
            return

        payload: dict[str, Any] = {
            "district": district.strip(),
            "latitude": lat,
            "longitude": lon,
            "crop_type": crop or None,
            "season": season.strip() or None,
        }
        if site_name.strip():
            payload["site_name"] = site_name.strip()
        if sector.strip():
            payload["sector"] = sector.strip()
        if cell.strip():
            payload["cell"] = cell.strip()

        if boundary_input.strip():
            try:
                boundary_obj = json.loads(boundary_input)
                if isinstance(boundary_obj, dict) and boundary_obj.get("type") == "Polygon":
                    payload["field_boundary_geojson"] = boundary_obj
                else:
                    st.error("Invalid GeoJSON format: must be a Polygon object.")
                    return
            except Exception as e:
                st.error(f"Failed to parse GeoJSON: {e}")
                return

        created = api_client.create_zone(payload)
        if created:
            st.session_state["zone_registered_flash"] = True
            st.rerun()
        else:
            st.error("Could not register zone. Check backend validation.")


@st.dialog("Record Field Observation", width="large")
def show_field_observation_dialog(zone: dict[str, Any], crops: list[str]) -> None:
    """Modal popup to record extension agent field observations."""
    zone_id = str(zone["id"])
    crop_default = zone.get("crop_type") or zone.get("crop")
    crop_options = crops or ([str(crop_default)] if crop_default else ["Maize"])
    crop_index = crop_options.index(crop_default) if crop_default in crop_options else 0

    with st.form(f"modal_field_report_{zone_id}"):
        st.markdown(f"**Zone:** {zone.get('district', 'District')} / {zone.get('site_name') or zone.get('sector') or 'Field'}")
        c1, c2 = st.columns(2)
        with c1:
            observed_crop = st.selectbox("Observed Crop", crop_options, index=crop_index)
            rainfall = st.number_input("Rainfall (mm, optional)", min_value=0.0, max_value=1000.0, value=None)
        with c2:
            moisture = st.number_input("Soil Moisture (%, optional)", min_value=0.0, max_value=100.0, value=None)

        symptoms = st.text_area("Observed Symptoms (optional)", max_chars=500, height=70)
        notes = st.text_area("Field Notes (optional)", max_chars=1000, height=70)
        submitted = st.form_submit_button("Save Observation", type="primary", use_container_width=True)

    if submitted:
        if rainfall is None and moisture is None and not symptoms.strip() and not notes.strip():
            st.error("Please enter at least one observation measurement or symptom.")
            return

        result = api_client.submit_field_report({
            "zone_id": zone_id,
            "district": zone.get("district", ""),
            "crop": observed_crop,
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
            st.error("Failed to save observation.")


@st.dialog("Readiness Evidence Checklist", width="large")
def show_readiness_dialog(zone_id: str) -> None:
    """Modal popup for financing and export readiness checklist."""
    record = api_client.get_zone_readiness(zone_id)
    if not record:
        st.info("Evidence checklist unavailable.")
        return

    finance_values = record.get("finance_evidence") or {}
    export_values = record.get("export_evidence") or {}

    with st.form(f"modal_readiness_form_{zone_id}"):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Finance Documentation**")
            fin_form = {
                key: st.checkbox(label, value=bool(finance_values.get(key)), key=f"m_fin_{zone_id}_{key}")
                for key, label in FINANCE_EVIDENCE.items()
            }
        with c2:
            st.markdown("**Export Documentation**")
            exp_form = {
                key: st.checkbox(label, value=bool(export_values.get(key)), key=f"m_exp_{zone_id}_{key}")
                for key, label in EXPORT_EVIDENCE.items()
            }
        submitted = st.form_submit_button("Save Evidence Checklist", type="primary", use_container_width=True)

    if submitted:
        res = api_client.update_zone_readiness(zone_id, {
            "finance_evidence": fin_form,
            "export_evidence": exp_form,
        })
        if res:
            st.session_state["readiness_saved"] = True
            st.rerun()
        else:
            st.error("Failed to save checklist.")


@st.dialog("Record Worker-Days", width="large")
def show_work_records_dialog(zone: dict[str, Any], crops: list[str]) -> None:
    """Modal popup to record observed worker days."""
    zone_id = str(zone["id"])
    crop_default = zone.get("crop_type") or zone.get("crop")
    crop_options = crops or ([str(crop_default)] if crop_default else ["Maize"])
    crop_index = crop_options.index(crop_default) if crop_default in crop_options else 0

    with st.form(f"modal_worker_days_{zone_id}"):
        c1, c2 = st.columns(2)
        with c1:
            season = st.text_input("Season", value=str(zone.get("season") or "Season A 2026"))
            crop = st.selectbox("Crop", crop_options, index=crop_index)
        with c2:
            worker_days = st.number_input("Observed Worker-Days", min_value=1.0, max_value=1_000_000.0, value=25.0, step=1.0)
            notes = st.text_input("Notes (optional)", max_chars=200)

        submitted = st.form_submit_button("Save Worker-Days Record", type="primary", use_container_width=True)

    if submitted:
        res = api_client.create_zone_work_record(zone_id, {
            "season": season.strip(),
            "crop": crop,
            "worker_days": worker_days,
            "notes": notes.strip(),
        })
        if res:
            st.session_state["work_record_saved"] = True
            st.rerun()
        else:
            st.error("Could not save worker-days record.")


@st.dialog("Yield Prediction", width="large")
def show_yield_prediction_dialog(zone: dict[str, Any], crops: list[str]) -> None:
    """Modal popup for running yield predictions."""
    zone_id = str(zone["id"])
    crop_default = zone.get("crop_type") or zone.get("crop")
    crop_options = crops or ([str(crop_default)] if crop_default else ["Maize"])
    crop_index = crop_options.index(crop_default) if crop_default in crop_options else 0
    area_default = float(zone.get("area_ha") or zone.get("area_cultivated") or 2.0)

    with st.form(f"modal_prediction_{zone_id}"):
        c1, c2 = st.columns(2)
        with c1:
            crop = st.selectbox("Crop", crop_options, index=crop_index)
            season = st.text_input("Season", value=str(zone.get("season") or "Season A 2026"))
        with c2:
            area = st.number_input("Cultivated Area (ha)", min_value=0.1, value=area_default, step=0.5)

        submitted = st.form_submit_button("Run Prediction", type="primary", use_container_width=True)

    if submitted:
        pred = api_client.predict_yield({
            "zone_id": zone_id,
            "season": season.strip(),
            "crop": crop,
            "area_cultivated": area,
        })
        if pred:
            st.session_state[f"last_pred_{zone_id}"] = pred
            st.rerun()
        else:
            st.error("Prediction could not be completed.")

    last_pred = st.session_state.get(f"last_pred_{zone_id}")
    if last_pred:
        st.markdown("---")
        total = last_pred.get("predicted_yield")
        tot_str = f"{total:,.0f} kg" if total is not None else "N/A"
        st.metric("Estimated Total Output", tot_str, delta=f"{last_pred.get('priority_level', 'Normal')} priority")
        if last_pred.get("yield_per_ha"):
            st.caption(f"Yield Rate: {last_pred['yield_per_ha']:,.0f} kg/ha | Model: {last_pred.get('model_version', 'baseline')}")


@error_boundary("Agricultural Zones")
def render_zones() -> None:
    try:
        render_icon_title(
            "assets/map.svg",
            t("zones.title", default="Agricultural Zones"),
            t("zones.subtitle", default="District & sector zone profiles, yield baselines, and field readiness."),
        )

        if st.session_state.pop("zone_registered_flash", False):
            st.success("Zone registered successfully.")
        if st.session_state.pop("field_report_saved", False):
            st.success("Field observation saved.")
        if st.session_state.pop("readiness_saved", False):
            st.success("Evidence checklist saved.")
        if st.session_state.pop("work_record_saved", False):
            st.success("Worker-days record saved.")

        zones = api_client.get_zones()

        # ── Action & Filter Header ──────────────────────────────────────────
        c_search, c_crop, c_prio, c_add = st.columns([2.5, 1.5, 1.2, 1.3])
        with c_search:
            search_query = st.text_input("Search", placeholder="Search district or site...", label_visibility="collapsed")
        with c_crop:
            crops_list = ["All Crops"] + (api_client.get_crops() or CROPS)
            crop_filter = st.selectbox("Crop", crops_list, label_visibility="collapsed")
        with c_prio:
            prio_filter = st.selectbox("Priority", ["All", "High", "Medium", "Low"], label_visibility="collapsed")
        with c_add:
            if st.button("Register Field", type="primary", use_container_width=True):
                show_register_zone_dialog()

        # Filter zones
        filtered = [
            z for z in zones
            if (not search_query or search_query.lower() in str(z.get("district", "")).lower() or search_query.lower() in str(z.get("site_name", "")).lower() or search_query.lower() in str(z.get("name", "")).lower())
            and (crop_filter == "All Crops" or z.get("crop") == crop_filter or z.get("crop_type") == crop_filter)
            and (prio_filter == "All" or str(z.get("priority", "Low")) == prio_filter)
        ]

        if not filtered:
            st.info("No agricultural zones match the filter.")
            return

        # ── Zone Table ───────────────────────────────────────────────────────
        table_rows = []
        for z in filtered:
            table_rows.append({
                "District": z.get("district", "N/A"),
                "Site / Sector": z.get("site_name") or z.get("sector") or z.get("cell") or "-",
                "Crop": z.get("crop_type") or z.get("crop") or "Unspecified",
                "Priority": z.get("priority") or "Not assessed",
                "Est. Output (kg)": f"{float(z.get('predicted_production_kg') or 0):,.0f}" if z.get("predicted_production_kg") else "-",
                "Risk": z.get("risk_status") or "Normal",
            })
        if pd is not None:
            st.dataframe(pd.DataFrame(table_rows), width="stretch", hide_index=True)

        st.markdown("---")

        # ── Zone Detail Inspection ───────────────────────────────────────────
        render_icon_subheader("assets/compass.svg", "Zone Detail & Field Actions")

        zone_options = {}
        for z in filtered:
            if not z.get("id"):
                continue
            name = " / ".join(filter(None, [
                z.get("district"),
                z.get("site_name") or z.get("sector"),
                z.get("crop_type") or z.get("crop"),
            ]))
            zone_options[f"{name} ({str(z['id'])[:6]})"] = z

        if not zone_options:
            return

        c_select, c_p1, c_p2, c_p3, c_p4 = st.columns([2.5, 1.1, 1.1, 1.1, 1.1])
        with c_select:
            selected_key = st.selectbox("Inspect Zone", list(zone_options), label_visibility="collapsed")
        selected_zone = zone_options[selected_key]
        zone_id = str(selected_zone["id"])
        crops_ref = api_client.get_crops() or CROPS

        with c_p1:
            if st.button("Predict Yield", use_container_width=True):
                show_yield_prediction_dialog(selected_zone, crops_ref)
        with c_p2:
            if st.button("Field Note", use_container_width=True):
                show_field_observation_dialog(selected_zone, crops_ref)
        with c_p3:
            if st.button("Readiness", use_container_width=True):
                show_readiness_dialog(zone_id)
        with c_p4:
            if st.button("Worker-Days", use_container_width=True):
                show_work_records_dialog(selected_zone, crops_ref)

        # Zone KPI Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("District", selected_zone.get("district", "N/A"))
        m2.metric("Target Crop", selected_zone.get("crop_type") or selected_zone.get("crop", "N/A"))
        area_val = selected_zone.get("area_ha") or selected_zone.get("area_cultivated")
        m3.metric("Cultivated Area", f"{float(area_val):,.1f} ha" if area_val else "Not recorded")
        prod_val = selected_zone.get("predicted_production_kg")
        m4.metric("Output Baseline", f"{float(prod_val):,.0f} kg" if prod_val else "No prediction")

        # Two summary cards
        c_left, c_right = st.columns(2)
        with c_left:
            with st.container(border=True):
                st.markdown("**Field Status & Priority**")
                p1, p2 = st.columns(2)
                with p1:
                    priority_badge(selected_zone.get("priority", "Low"))
                with p2:
                    st.caption(f"Risk: {selected_zone.get('risk_status', 'Normal')}")
                st.markdown("---")
                recs = (api_client.get_zone_recommendations(zone_id) or {}).get("recommendations", [])
                if recs:
                    for i, r in enumerate(recs[:2], 1):
                        st.markdown(f"**{i}.** {r}")
                else:
                    st.caption("No urgent field recommendations.")

        with c_right:
            with st.container(border=True):
                st.markdown(f"**Weather: {selected_zone.get('district', '')}**")
                weather = api_client.get_weather(selected_zone.get("district", "Musanze"))
                if weather:
                    w1, w2, w3 = st.columns(3)
                    w1.metric("Temp", f"{weather.get('temperature_c', 'N/A')} °C")
                    w2.metric("Rain", f"{weather.get('rainfall_mm', 'N/A')} mm")
                    w3.metric("Humidity", f"{weather.get('humidity_pct', 'N/A')}%")
                else:
                    st.caption("Weather telemetry unavailable.")

    except requests.exceptions.RequestException as e:
        logger.error("Network error in zones view: %s", e)
        render_error_page("network", str(e))
    except Exception as e:
        logger.error("Unexpected error in zones view: %s", e, exc_info=True)
        render_error_page("system", str(e))
