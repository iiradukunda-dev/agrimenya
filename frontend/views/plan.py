import logging
from typing import Any
import requests
import streamlit as st
from components.badges import status_badge
from components.errors import error_boundary, render_error_page
from components.icons import render_icon_title
from utils import api_client
from utils.i18n import t

logger = logging.getLogger(__name__)


@error_boundary("Planning")
def render_plan() -> None:
    try:
        render_icon_title(
            "assets/calendar.svg",
            t("plan.header", default="Planification & Roadmaps"),
            t("plan.subtitle", default="Execution roadmaps, milestone tracking, resource costing, and stakeholder dispatch."),
        )

        if st.session_state.pop("plan_saved_flash", False):
            st.success("Plan saved successfully.")
        if st.session_state.pop("action_updated_flash", False):
            st.success("Milestone status updated successfully.")
        if st.session_state.pop("plan_sent_flash", False):
            st.success("Plan email dispatched successfully.")

        zones = api_client.get_zones()
        zone_options = {}
        for zone in zones:
            if not zone.get("id"):
                continue
            label_parts = [
                zone.get("district") or "Unknown district",
                zone.get("sector") or zone.get("cell"),
                zone.get("crop_type") or zone.get("crop"),
            ]
            label = " / ".join(str(part) for part in label_parts if part)
            if label in zone_options:
                label = f"{label} | {str(zone['id'])[:8]}"
            zone_options[label] = zone

        if not zone_options:
            st.info("Add or load an agricultural zone before creating or inspecting execution plans.")
            return

        selected_label = st.selectbox(t("plan.select_zone", default="Select Agricultural Zone"), list(zone_options), key="planning_zone")
        selected_zone = zone_options.get(selected_label) or (list(zone_options.values())[0] if zone_options else {})
        if not selected_zone:
            st.info("No active zone selected.")
            return
        selected_zone_id = str(selected_zone["id"])

        context = [
            ("Crop", selected_zone.get("crop_type") or selected_zone.get("crop")),
            ("Season", selected_zone.get("season")),
            ("Cultivated area", f"{selected_zone['area_cultivated']} ha" if selected_zone.get("area_cultivated") is not None else None),
        ]
        st.caption(" | ".join(f"{label}: {value}" for label, value in context if value not in (None, "")) or "Zone details have not been recorded yet.")

        # Tab Navigation: Active Plans, Create Plan, Disease Response Plan
        tab_plans, tab_create, tab_disease = st.tabs([
            t("plan.tab_active_plans", default="Active Plans & Milestones"),
            t("plan.tab_create_plan", default="Create Custom Plan"),
            t("plan.tab_disease_plan", default="Rapid Disease Response Plan"),
        ])

        # ─────────────────────────────────────────────────────────────
        # TAB 1: ACTIVE PLANS & MILESTONE TRACKING
        # ─────────────────────────────────────────────────────────────
        with tab_plans:
            st.markdown(f"### {t('plan.zone_plans', default='Execution Plans for this Zone')}")
            st.caption("Track progress of each milestone action step, view audit history, or dispatch formatted plans via email.")

            plans = api_client.get_zone_plans(selected_zone_id)
            if not plans:
                st.info("There are no saved execution plans for this zone yet. Create one in the next tab.")
            else:
                for plan in plans:
                    plan_id = str(plan.get("id"))
                    title = plan.get("title") or "Untitled plan"
                    steps = plan.get("roadmap_json") or []
                    resources = plan.get("resources_json") or {}

                    with st.expander(f"📋 {title} ({len(steps)} Action Steps)", expanded=True):
                        # Action steps list with status badge & updater
                        for step in steps:
                            step_num = step.get("step_number", 1)
                            action_title = step.get("title") or f"Action {step_num}"
                            timing = step.get("timeframe") or "Timing not set"
                            curr_status = step.get("status") or "planned"

                            with st.container(border=True):
                                c_left, c_right = st.columns([3, 1.2])
                                with c_left:
                                    st.markdown(f"**Step {step_num}: {action_title}**")
                                    st.caption(f"📅 Target Timeframe: {timing}")
                                    if step.get("description"):
                                        st.write(step["description"])
                                with c_right:
                                    st.markdown(f"**Status:**")
                                    status_badge(curr_status)

                                # Interactive status updater
                                with st.popover(f"Update Step {step_num} Status"):
                                    with st.form(f"status_form_{plan_id}_{step_num}"):
                                        new_status = st.selectbox(
                                            "New Milestone Status",
                                            options=["planned", "in_progress", "completed", "blocked"],
                                            index=["planned", "in_progress", "completed", "blocked"].index(curr_status) if curr_status in ["planned", "in_progress", "completed", "blocked"] else 0,
                                            key=f"status_sel_{plan_id}_{step_num}",
                                        )
                                        note = st.text_input("Change / Progress Note", placeholder="e.g. Field tractor arrived; plowing underway", key=f"status_note_{plan_id}_{step_num}")
                                        sub_status = st.form_submit_button("Confirm Status Update", type="primary")

                                    if sub_status:
                                        up_res = api_client.update_plan_action_status(
                                            plan_id=plan_id,
                                            step_number=step_num,
                                            status=new_status,
                                            change_note=note,
                                        )
                                        if up_res:
                                            st.session_state["action_updated_flash"] = True
                                            api_client.get_zone_plans.clear()
                                            st.rerun()
                                        else:
                                            st.error("Could not update milestone action status.")

                        # Resource estimation summary if attached
                        quantities = resources.get("quantities") or {}
                        costs = resources.get("costs_rwf") or {}
                        total_cost = resources.get("estimated_cost_rwf")
                        if quantities or total_cost is not None:
                            st.markdown("---")
                            st.markdown("##### Attached Resource Budget")
                            col_q, col_c = st.columns(2)
                            with col_q:
                                q_rows = [{"Resource": k.replace("_", " ").title(), "Quantity": f"{v:,.2f}"} for k, v in quantities.items()]
                                if q_rows:
                                    st.dataframe(q_rows, use_container_width=True, hide_index=True)
                            with col_c:
                                if total_cost is not None:
                                    st.metric("Total Estimated Cost", f"RWF {total_cost:,.0f}")
                                    if costs:
                                        st.caption("Budgeted items: " + ", ".join(costs.keys()))

                        # Audit History & Sharing Drawer
                        st.markdown("---")
                        c_share, c_hist = st.columns(2)

                        with c_share:
                            st.markdown("##### Dispatch Plan by Email")
                            with st.form(f"email_plan_form_{plan_id}"):
                                target_email = st.text_input("Recipient Email", placeholder="extension.officer@minagri.gov.rw", key=f"plan_email_{plan_id}")
                                send_btn = st.form_submit_button("Send Plan via SMTP", use_container_width=True)

                            if send_btn:
                                if not target_email or "@" not in target_email:
                                    st.warning("Please provide a valid recipient email address.")
                                else:
                                    with st.spinner("Dispatching formatted plan..."):
                                        send_res = api_client.send_shared_plan(plan_id, target_email.strip())
                                    if send_res and send_res.get("status") == "sent":
                                        st.session_state["plan_sent_flash"] = True
                                        st.rerun()
                                    else:
                                        st.error("Failed to deliver plan email. Check SMTP server configuration.")

                        with c_hist:
                            st.markdown("##### Milestone Audit Trail")
                            hist_records = api_client.get_plan_action_history(plan_id)
                            if not hist_records:
                                st.caption("No status changes recorded yet for this plan.")
                            else:
                                for h in hist_records[:5]:
                                    st.caption(
                                        f"• **Step {h.get('step_number')}** → `{h.get('status')}` "
                                        f"by *{h.get('changed_by', 'user')}* ({str(h.get('changed_at', ''))[:16]} CAT): "
                                        f"{h.get('change_note') or 'No note provided'}"
                                    )

        # ─────────────────────────────────────────────────────────────
        # TAB 2: CREATE CUSTOM PLAN
        # ─────────────────────────────────────────────────────────────
        with tab_create:
            st.markdown(f"### {t('plan.create_plan', default='Author an Execution Plan')}")
            st.caption("Define milestones, deliverables, and timelines agreed upon with local cooperatives. Nothing is pre-filled with generic filler.")

            action_count = st.number_input(
                t("plan.action_count", default="Number of milestone action steps"),
                min_value=1,
                max_value=8,
                value=2,
                step=1,
                key="plan_action_count_custom",
            )

            with st.form("save_plan_form_custom", clear_on_submit=True):
                title = st.text_input(t("plan.plan_title", default="Plan Title"), placeholder="e.g. Season A Sowing & Input Distribution Plan")
                roadmap = []
                for index in range(action_count):
                    st.markdown(f"**Milestone Action {index + 1}**")
                    action_title = st.text_input("Action Name", key=f"plan_action_title_{index}", placeholder="e.g. Distribute certified seeds to cooperative centers")
                    detail_cols = st.columns([2, 1])
                    with detail_cols[0]:
                        description = st.text_area("Operational Notes", key=f"plan_action_notes_{index}", placeholder="Detail responsibilities, logistics, and criteria...", height=80)
                    with detail_cols[1]:
                        timeframe = st.text_input("Target Date / Timeframe", key=f"plan_action_time_{index}", placeholder="e.g. Weeks 1-2, Oct 2026")
                    roadmap.append({
                        "step_number": index + 1,
                        "title": action_title.strip(),
                        "description": description.strip(),
                        "timeframe": timeframe.strip() or None,
                        "status": "planned",
                    })

                submitted = st.form_submit_button(t("plan.save_plan", default="Save Plan & Commit Milestones"), type="primary", use_container_width=True)

            if submitted:
                if not title.strip() or any(not step["title"] or not step["description"] for step in roadmap):
                    st.error("Please provide a plan title, and complete the action name and notes for each milestone.")
                else:
                    result = api_client.create_roadmap({
                        "zone_id": selected_zone_id,
                        "title": title.strip(),
                        "roadmap": roadmap,
                        "resources": st.session_state.get(f"resource_estimate_{selected_zone_id}") or {},
                        "created_by": "frontend_officer",
                    })
                    if result:
                        st.session_state["plan_saved_flash"] = True
                        st.session_state.pop(f"resource_estimate_{selected_zone_id}", None)
                        api_client.get_zone_plans.clear()
                        api_client.get_roadmap.clear()
                        st.rerun()
                    else:
                        st.error("The plan could not be saved. Check backend connectivity and try again.")

            # Optional resource calculator
            with st.expander("Optional Resource Budget Calculator", expanded=False):
                st.caption("Calculate input quantities and expenditure estimates to bind into this plan.")
                zone_area = selected_zone.get("area_cultivated") or selected_zone.get("area_ha")
                with st.form(f"resource_calc_form_{selected_zone_id}"):
                    area = st.number_input(
                        "Cultivated Area (ha)",
                        min_value=0.0,
                        value=float(zone_area) if zone_area is not None else 10.0,
                        key=f"calc_area_{selected_zone_id}",
                    )
                    rainfall = st.number_input(
                        "Expected Seasonal Rainfall (mm, optional)",
                        min_value=0.0,
                        value=None,
                        key=f"calc_rain_{selected_zone_id}",
                    )
                    calc_inputs = {}
                    for input_key, quantity_label, rate_label, price_label in [
                        ("seed", "Seed", "Rate (kg/ha)", "Price (RWF/kg)"),
                        ("dap", "DAP Fertilizer", "Rate (kg/ha)", "Price (RWF/kg)"),
                        ("urea", "Urea Fertilizer", "Rate (kg/ha)", "Price (RWF/kg)"),
                        ("irrigation", "Irrigation Water", "Rate (litres/ha)", "Price (RWF/1,000 litres)"),
                    ]:
                        st.markdown(f"**{quantity_label}**")
                        r_col, p_col = st.columns(2)
                        with r_col:
                            rate = st.number_input(rate_label, min_value=0.0, value=None, key=f"r_{input_key}_{selected_zone_id}")
                        with p_col:
                            price = st.number_input(price_label, min_value=0.0, value=None, key=f"p_{input_key}_{selected_zone_id}")
                        if rate is not None:
                            calc_inputs["irrigation_liters_ha" if input_key == "irrigation" else f"{input_key}_rate_kg_ha"] = rate
                        if price is not None:
                            calc_inputs["irrigation_price_rwf_1000_liters" if input_key == "irrigation" else f"{input_key}_price_rwf_kg"] = price

                    calc_btn = st.form_submit_button("Compute Resource Quantities & Costs", type="primary")

                if calc_btn:
                    if area is None or area <= 0:
                        st.error("Please specify a cultivated area greater than zero.")
                    else:
                        calc_inputs["area_cultivated"] = area
                        if rainfall is not None:
                            calc_inputs["rainfall_mm"] = rainfall
                        calc_res = api_client.get_zone_resources(selected_zone_id, **calc_inputs)
                        if not calc_res:
                            st.error("Could not calculate resource quantities.")
                        else:
                            st.session_state[f"resource_estimate_{selected_zone_id}"] = calc_res
                            st.success("Resource estimates calculated and cached for plan creation.")
                            quantities = calc_res.get("quantities") or {}
                            if quantities:
                                st.dataframe(
                                    [{"Resource": k.replace("_", " ").title(), "Quantity": f"{v:,.2f}"} for k, v in quantities.items()],
                                    use_container_width=True,
                                    hide_index=True,
                                )
                            total = calc_res.get("estimated_cost_rwf")
                            if total is not None:
                                st.metric("Estimated Cost", f"RWF {total:,.0f}")

        # ─────────────────────────────────────────────────────────────
        # TAB 3: RAPID DISEASE RESPONSE PLAN
        # ─────────────────────────────────────────────────────────────
        with tab_disease:
            st.markdown(f"### {t('plan.disease_plan_title', default='Rapid Agronomic Disease Action Plan')}")
            st.caption("Generate an emergency intervention roadmap based on observed disease symptoms in the field.")

            with st.form("disease_plan_form", border=True):
                crop_opts = api_client.get_crops() or ["Maize", "Beans", "Cassava", "Irish Potatoes", "Rice"]
                d_crop = st.selectbox("Cultivated Crop", crop_opts, key="dplan_crop")
                d_symptoms = st.text_area("Field Symptoms", placeholder="Describe disease signs: e.g. necrotic spots, bacterial wilt, rotting tuber...", key="dplan_symptoms")
                gen_dplan_btn = st.form_submit_button("Generate & Save Emergency Response Plan", type="primary", use_container_width=True)

            if gen_dplan_btn:
                if not d_symptoms.strip():
                    st.warning("Please provide symptoms to generate a response plan.")
                else:
                    with st.spinner("Generating emergency response protocol..."):
                        dp_result = api_client.create_disease_plan({
                            "zone_id": selected_zone_id,
                            "crop": d_crop,
                            "symptoms": d_symptoms,
                        })
                    if dp_result:
                        disease_name = dp_result.get("predicted_disease", "Agricultural Pathogen")
                        actions = dp_result.get("recommended_actions", [])
                        st.success(f"Emergency diagnosis: **{disease_name}** ({dp_result.get('risk_level', 'High')} Risk)")

                        # Auto-save as an executable roadmap plan
                        steps_to_save = [
                            {
                                "step_number": idx,
                                "title": f"Intervention: {act[:60]}",
                                "description": act,
                                "timeframe": "Immediate (Days 1-7)",
                                "status": "planned",
                            }
                            for idx, act in enumerate(actions, start=1)
                        ]
                        save_auto = api_client.create_roadmap({
                            "zone_id": selected_zone_id,
                            "title": f"Emergency Response: {disease_name} on {d_crop}",
                            "roadmap": steps_to_save,
                            "resources": {},
                            "created_by": "disease_engine",
                        })
                        if save_auto:
                            st.session_state["plan_saved_flash"] = True
                            api_client.get_zone_plans.clear()
                            st.rerun()
                        else:
                            st.info("Recommendations generated, but auto-save was unavailable.")
                    else:
                        st.error("Failed to generate disease response plan from backend.")

    except requests.exceptions.RequestException as exc:
        logger.exception("Network error in planning view")
        render_error_page("network", str(exc))
    except Exception as exc:
        logger.exception("Unexpected error in planning view")
        render_error_page("system", str(exc))
