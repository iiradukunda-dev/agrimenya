"""Executive Planning & Execution Roadmaps."""
import logging
from typing import Any
import streamlit as st
from components.badges import status_badge
from components.errors import error_boundary, render_error_page
from components.icons import render_icon_title
from utils import api_client
from utils.i18n import t

logger = logging.getLogger(__name__)


@st.dialog("Generate Seasonal Plan Draft", width="large")
def show_seasonal_draft_dialog(zone: dict[str, Any]) -> None:
    """Popup modal using backend build_seasonal_draft based on official crop calendars."""
    zone_id = str(zone["id"])
    district = zone.get("district", "Musanze")
    zone_crop = zone.get("crop_type") or zone.get("crop") or "Maize"
    zone_area = float(zone.get("area_cultivated") or zone.get("area_ha") or 2.0)

    st.markdown(f"**District:** {district} | **Default Area:** {zone_area:g} ha")

    c1, c2 = st.columns(2)
    with c1:
        crop = st.selectbox("Target Crop", ["Maize", "Beans", "Irish Potatoes", "Cassava", "Rice", "Wheat", "Soybeans"], index=0, key="draft_crop_sel")
    with c2:
        area = st.number_input("Cultivated Area (ha)", min_value=0.1, value=zone_area, step=0.5, key="draft_area_inp")

    if st.button("Generate Agro-Ecological Draft", type="primary", use_container_width=True):
        with st.spinner("Compiling planting calendar and seasonal phases..."):
            draft = api_client.get_seasonal_plan_draft(zone_id, crop)
        if draft:
            st.session_state[f"active_draft_{zone_id}"] = draft
        else:
            st.error("Crop calendar unavailable for this selection. Try Maize or Beans.")

    draft_data = st.session_state.get(f"active_draft_{zone_id}")
    if draft_data:
        st.markdown("---")
        st.markdown(f"##### {draft_data.get('title', 'Seasonal Plan Draft')}")
        if draft_data.get("sowing_window"):
            st.caption(f"Optimal Sowing Window: {draft_data['sowing_window']}")

        phases = draft_data.get("phases") or draft_data.get("roadmap") or []
        for i, phase in enumerate(phases, start=1):
            with st.container(border=True):
                st.markdown(f"**Phase {i}: {phase.get('title', 'Action')}**")
                st.caption(f"Timeframe: {phase.get('timeframe', 'Season Schedule')}")
                if phase.get("description"):
                    st.write(phase["description"])

        if st.button("Commit & Save Plan Roadmap", type="primary", use_container_width=True, key=f"commit_draft_{zone_id}"):
            res = api_client.create_roadmap({
                "zone_id": zone_id,
                "title": draft_data.get("title", f"{crop} Seasonal Plan"),
                "roadmap": phases,
                "resources": draft_data.get("resources", {}),
                "created_by": "agronomy_planner",
            })
            if res:
                st.session_state["plan_saved_flash"] = True
                st.session_state.pop(f"active_draft_{zone_id}", None)
                api_client.get_zone_plans.clear()
                st.rerun()
            else:
                st.error("Failed to persist plan roadmap.")


@st.dialog("Create Custom Plan", width="large")
def show_create_plan_dialog(zone: dict[str, Any]) -> None:
    """Popup modal for custom milestone planning."""
    zone_id = str(zone["id"])
    with st.form("custom_plan_modal_form"):
        title = st.text_input("Plan Title", placeholder="e.g. Irrigation Expansion Roadmap")
        num_steps = st.slider("Number of Milestones", min_value=1, max_value=6, value=3)

        steps = []
        for i in range(num_steps):
            st.markdown(f"**Milestone {i + 1}**")
            c1, c2 = st.columns([2, 1])
            with c1:
                name = st.text_input("Milestone Action", key=f"custom_m_title_{i}", placeholder="e.g. Procure certified seed")
                notes = st.text_area("Operational Guidance", key=f"custom_m_notes_{i}", placeholder="Details...", height=65)
            with c2:
                timeframe = st.text_input("Target Date", key=f"custom_m_time_{i}", placeholder="e.g. Week 1")
            steps.append({
                "step_number": i + 1,
                "title": name.strip(),
                "description": notes.strip(),
                "timeframe": timeframe.strip() or None,
                "status": "planned",
            })

        submitted = st.form_submit_button("Save Plan Roadmap", type="primary", use_container_width=True)

    if submitted:
        if not title.strip() or any(not s["title"] for s in steps):
            st.warning("Please provide a title and action name for each milestone.")
            return

        res = api_client.create_roadmap({
            "zone_id": zone_id,
            "title": title.strip(),
            "roadmap": steps,
            "resources": {},
            "created_by": "agronomy_planner",
        })
        if res:
            st.session_state["plan_saved_flash"] = True
            api_client.get_zone_plans.clear()
            st.rerun()
        else:
            st.error("Could not save custom plan roadmap.")


@st.dialog("Resource & Cost Estimator", width="large")
def show_resource_estimator_dialog(zone: dict[str, Any]) -> None:
    """Popup modal for dynamic inputs and named fertilizer product estimation."""
    zone_id = str(zone["id"])
    zone_area = float(zone.get("area_cultivated") or zone.get("area_ha") or 2.0)

    with st.form("modal_resource_est_form"):
        st.markdown("##### Production Inputs & Sowing Rates")
        c1, c2 = st.columns(2)
        with c1:
            area = st.number_input("Area (ha)", min_value=0.1, value=zone_area, step=0.5)
            seed_rate = st.number_input("Seed Rate (kg/ha)", min_value=0.0, value=25.0)
            seed_price = st.number_input("Seed Price (RWF/kg)", min_value=0.0, value=850.0)
        with c2:
            rainfall = st.number_input("Expected Rainfall (mm)", min_value=0.0, value=180.0)
            dap_rate = st.number_input("DAP Rate (kg/ha)", min_value=0.0, value=100.0)
            dap_price = st.number_input("DAP Price (RWF/kg)", min_value=0.0, value=920.0)

        st.markdown("##### Named Fertilizer Products (Optional)")
        f1_name = st.text_input("Fertilizer Product Name", value="NPK 17-17-17")
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            f1_rate = st.number_input("Application Rate", min_value=0.0, value=150.0)
        with fc2:
            f1_unit = st.selectbox("Unit", ["kg", "tonnes", "litres"])
        with fc3:
            f1_price = st.number_input("Price per Unit (RWF)", min_value=0.0, value=780.0)

        calc_btn = st.form_submit_button("Calculate Cost & Material Quantities", type="primary", use_container_width=True)

    if calc_btn:
        payload = {
            "area_cultivated": area,
            "rainfall_mm": rainfall,
            "inputs": {
                "seed_rate_kg_ha": seed_rate,
                "seed_price_rwf_kg": seed_price,
                "dap_rate_kg_ha": dap_rate,
                "dap_price_rwf_kg": dap_price,
            },
            "fertilizer_items": [
                {"name": f1_name, "rate_per_ha": f1_rate, "unit": f1_unit, "price_per_unit": f1_price}
            ] if f1_name.strip() else [],
            "area_source": "farmer_reported",
            "rate_source": "RAB guidelines",
            "price_source": "Local agro-dealer survey",
        }
        res = api_client.estimate_resources_advanced(zone_id, payload)
        if res:
            st.session_state[f"last_resource_est_{zone_id}"] = res
            st.rerun()

    est = st.session_state.get(f"last_resource_est_{zone_id}")
    if est:
        st.markdown("---")
        st.markdown("##### Resource Allocation Summary")
        tot = est.get("estimated_cost_rwf")
        tot_str = f"{tot:,.0f} RWF" if tot is not None else "Partial estimate"
        st.metric("Total Input Cost", tot_str, delta=f"Status: {est.get('status', 'computed')}")

        quantities = est.get("quantities") or {}
        q_cols = st.columns(3)
        if "seeds_kg" in quantities:
            q_cols[0].metric("Certified Seeds", f"{quantities['seeds_kg']:,.0f} kg")
        if "dap_kg" in quantities:
            q_cols[1].metric("DAP Fertilizer", f"{quantities['dap_kg']:,.0f} kg")
        if "irrigation_liters" in quantities:
            q_cols[2].metric("Irrigation Water", f"{quantities['irrigation_liters']:,.0f} L")


@st.dialog("Milestone Roadmap Details", width="large")
def show_plan_details_dialog(plan: dict[str, Any]) -> None:
    """Popup modal for viewing and updating plan milestones."""
    plan_id = str(plan.get("id"))
    title = plan.get("title") or "Plan Roadmap"
    steps = plan.get("roadmap_json") or []

    st.markdown(f"#### {title}")
    st.caption(f"ID: {plan_id[:8]} • {len(steps)} Milestones")

    # Share via email in popover
    with st.popover("Share Plan via Email"):
        recip = st.text_input("Recipient Email", placeholder="officer@rab.gov.rw", key=f"share_rec_{plan_id}")
        subj = st.text_input("Subject", value=f"Agricultural Plan: {title}", key=f"share_sub_{plan_id}")
        if st.button("Send Email", type="primary", key=f"send_sh_{plan_id}"):
            if recip.strip():
                ok = api_client.send_shared_plan(plan_id, recip.strip(), subj.strip())
                if ok:
                    st.success("Plan email sent.")
            else:
                st.warning("Enter an email address.")

    st.markdown("---")
    for step in steps:
        step_num = step.get("step_number", 1)
        action_title = step.get("title") or f"Milestone {step_num}"
        timeframe = step.get("timeframe") or "Not set"
        curr_status = step.get("status") or "planned"

        with st.container(border=True):
            col_info, col_status = st.columns([3, 1.2])
            with col_info:
                st.markdown(f"**Step {step_num}: {action_title}**")
                st.caption(f"Target: {timeframe}")
                if step.get("description"):
                    st.write(step["description"])
            with col_status:
                status_badge(curr_status)
                new_st = st.selectbox(
                    "Update",
                    options=["planned", "in_progress", "completed", "blocked"],
                    index=["planned", "in_progress", "completed", "blocked"].index(curr_status) if curr_status in ["planned", "in_progress", "completed", "blocked"] else 0,
                    key=f"modal_st_{plan_id}_{step_num}",
                    label_visibility="collapsed",
                )
                if new_st != curr_status:
                    if st.button("Apply", key=f"apply_{plan_id}_{step_num}"):
                        api_client.update_plan_action_status(plan_id, step_num, new_st)
                        st.session_state["action_updated_flash"] = True
                        api_client.get_zone_plans.clear()
                        st.rerun()


@error_boundary("Planning")
def render_plan() -> None:
    try:
        render_icon_title(
            "assets/calendar.svg",
            t("plan.header", default="Planification & Roadmaps"),
            t("plan.subtitle", default="Seasonal calendars, milestone tracking, and input costing."),
        )

        if st.session_state.pop("plan_saved_flash", False):
            st.success("Plan roadmap saved.")
        if st.session_state.pop("action_updated_flash", False):
            st.success("Milestone status updated.")

        zones = api_client.get_zones()
        zone_options = {}
        for zone in zones:
            if not zone.get("id"):
                continue
            label_parts = [
                zone.get("district") or "District",
                zone.get("sector") or zone.get("cell"),
                zone.get("crop_type") or zone.get("crop"),
            ]
            label = " / ".join(str(p) for p in label_parts if p)
            if label in zone_options:
                label = f"{label} | {str(zone['id'])[:6]}"
            zone_options[label] = zone

        if not zone_options:
            st.info("No active agricultural zones available.")
            return

        pending_zone_id = st.session_state.pop("planning_pending_zone_id", None)
        if pending_zone_id:
            for label, zone in zone_options.items():
                if str(zone.get("id")) == str(pending_zone_id):
                    st.session_state["planning_zone_select"] = label
                    break

        c_zone, c_draft, c_custom, c_cost = st.columns([2.5, 1.3, 1.2, 1.2])
        with c_zone:
            selected_label = st.selectbox(
                "Zone",
                list(zone_options),
                key="planning_zone_select",
                label_visibility="collapsed",
            )
        selected_zone = zone_options.get(selected_label) or list(zone_options.values())[0]
        selected_zone_id = str(selected_zone["id"])

        with c_draft:
            if st.button("Seasonal Draft", type="primary", use_container_width=True):
                show_seasonal_draft_dialog(selected_zone)
        with c_custom:
            if st.button("Custom Plan", use_container_width=True):
                show_create_plan_dialog(selected_zone)
        with c_cost:
            if st.button("Cost Estimator", use_container_width=True):
                show_resource_estimator_dialog(selected_zone)

        # Active plans table
        st.markdown("---")
        plans = api_client.get_zone_plans(selected_zone_id)
        if not plans:
            st.info("No execution plans for this zone yet. Click 'Seasonal Draft' above to generate one.")
        else:
            for plan in plans:
                p_id = str(plan.get("id"))
                title = plan.get("title") or "Untitled plan"
                steps = plan.get("roadmap_json") or []
                completed = sum(1 for s in steps if s.get("status") == "completed")
                total = len(steps)
                pct = int((completed / total * 100)) if total else 0

                with st.container(border=True):
                    col_t, col_p, col_act = st.columns([3, 1.5, 1])
                    with col_t:
                        st.markdown(f"**{title}**")
                        st.caption(f"{total} Milestones • Created by {plan.get('created_by', 'agronomist')}")
                    with col_p:
                        st.progress(pct / 100.0, text=f"{pct}% complete ({completed}/{total})")
                    with col_act:
                        if st.button("Inspect", key=f"view_{p_id}", use_container_width=True):
                            show_plan_details_dialog(plan)

    except Exception as exc:
        logger.exception("Error rendering planning page: %s", exc)
        render_error_page(exc)
