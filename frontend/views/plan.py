import logging

import requests
import streamlit as st
from components.errors import render_error_page
from components.icons import render_icon_title
from utils import api_client
from utils.i18n import t

logger = logging.getLogger(__name__)


def render_plan() -> None:
    try:
        render_icon_title("assets/calendar.svg", t("plan.header", "Planification"), t("plan.subtitle", "Roadmaps and execution timelines for agricultural interventions."))
        if st.session_state.pop("plan_saved_flash", False):
            st.success("Plan saved.")
        zones = api_client.get_zones()
        zone_options = {}
        for zone in zones:
            if not zone.get("id"):
                continue
            label_parts = [zone.get("district") or "Unknown district", zone.get("sector") or zone.get("cell"), zone.get("crop_type") or zone.get("crop")]
            label = " / ".join(str(part) for part in label_parts if part)
            if label in zone_options:
                label = f"{label} | {str(zone['id'])[:8]}"
            zone_options[label] = zone
        if not zone_options:
            st.info("Add or load a zone before creating a plan.")
            return

        selected_label = st.selectbox(t("plan.select_zone"), list(zone_options), key="planning_zone")
        selected_zone = zone_options[selected_label]
        selected_zone_id = str(selected_zone["id"])
        context = [
            ("Crop", selected_zone.get("crop_type") or selected_zone.get("crop")),
            ("Season", selected_zone.get("season")),
            ("Cultivated area", f"{selected_zone['area_cultivated']} ha" if selected_zone.get("area_cultivated") is not None else None),
        ]
        st.caption(" | ".join(f"{label}: {value}" for label, value in context if value not in (None, "")) or "Zone details have not been recorded yet.")

        st.markdown(f"## {t('plan.zone_plans', 'Plans for this zone')}")
        plans = api_client.get_zone_plans(selected_zone_id)
        if not plans:
            st.info("There are no saved plans for this zone yet.")
        else:
            for plan in plans:
                title = plan.get("title") or "Untitled plan"
                steps = plan.get("roadmap_json") or []
                resources = plan.get("resources_json") or {}
                with st.expander(f"{title} | {len(steps)} actions", expanded=False):
                    for step in steps:
                        timing = step.get("timeframe") or "Timing not set"
                        st.markdown(f"**{step.get('step_number', '')}. {step.get('title') or 'Untitled action'}** | {timing}")
                        if step.get("description"):
                            st.write(step["description"])
                    missing = resources.get("missing_inputs") or []
                    if missing:
                        st.caption("Resource estimate incomplete; missing inputs: " + ", ".join(str(item) for item in missing))

        st.markdown(f"## {t('plan.create_plan', 'Create a plan')}")
        st.caption("Write the actions your team has agreed on. Nothing is pre-filled with generic farming advice.")
        st.caption("If you calculate resource quantities below before saving, that estimate will be attached to this zone's plan.")
        action_count = st.number_input(t("plan.action_count", "Number of actions"), min_value=1, max_value=8, value=1, step=1, key="plan_action_count")
        with st.form("save_plan_form", clear_on_submit=True):
            title = st.text_input(t("plan.plan_title", "Plan title"), placeholder="For example, first-season planting plan")
            roadmap = []
            for index in range(action_count):
                st.markdown(f"**Action {index + 1}**")
                action_title = st.text_input("Action", key=f"plan_action_title_{index}", placeholder="What needs to happen?")
                detail_cols = st.columns([2, 1])
                with detail_cols[0]:
                    description = st.text_area("Notes", key=f"plan_action_notes_{index}", placeholder="Add relevant instructions or context", height=90)
                with detail_cols[1]:
                    timeframe = st.text_input("When", key=f"plan_action_time_{index}", placeholder="Date or period")
                roadmap.append({"step_number": index + 1, "title": action_title.strip(), "description": description.strip(), "timeframe": timeframe.strip() or None})
            submitted = st.form_submit_button(t("plan.save_plan", "Save plan"), type="primary", width="stretch")

        if submitted:
            if not title.strip() or any(not step["title"] or not step["description"] for step in roadmap):
                st.error("Add a plan title and complete an action title and notes for each step.")
                return
            result = api_client.create_roadmap({
                "zone_id": selected_zone_id,
                "title": title.strip(),
                "roadmap": roadmap,
                "resources": st.session_state.get(f"resource_estimate_{selected_zone_id}") or {},
                "created_by": "frontend",
            })
            if result:
                st.session_state["plan_saved_flash"] = True
                st.session_state.pop(f"resource_estimate_{selected_zone_id}", None)
                api_client.get_zone_plans.clear()
                api_client.get_roadmap.clear()
                st.rerun()
            else:
                st.error("The plan could not be saved. Check the backend connection and try again.")

        with st.expander("Optional resource calculator", expanded=False):
            st.caption("Enter local rates and prices to scale quantities for this area. The calculator does not recommend application rates.")
            zone_area = selected_zone.get("area_cultivated") or selected_zone.get("area_ha")
            with st.form(f"resource_estimate_form_{selected_zone_id}"):
                area = st.number_input(
                    "Cultivated area (ha)", min_value=0.0,
                    value=float(zone_area) if zone_area is not None else None,
                    placeholder="Enter area if it is not recorded",
                    key=f"resource_area_{selected_zone_id}",
                )
                rainfall = st.number_input(
                    "Rainfall (mm, optional)", min_value=0.0, value=None,
                    placeholder="For context only", key=f"resource_rainfall_{selected_zone_id}",
                )
                estimate_inputs = {}
                for input_key, quantity_label, rate_label, price_label in [
                    ("seed", "Seed", "Rate (kg/ha)", "Price (RWF/kg)"),
                    ("dap", "DAP fertilizer", "Rate (kg/ha)", "Price (RWF/kg)"),
                    ("urea", "Urea fertilizer", "Rate (kg/ha)", "Price (RWF/kg)"),
                    ("irrigation", "Irrigation water", "Rate (litres/ha)", "Price (RWF/1,000 litres)"),
                ]:
                    st.markdown(f"**{quantity_label}**")
                    rate_col, price_col = st.columns(2)
                    with rate_col:
                        rate = st.number_input(
                            rate_label, min_value=0.0, value=None,
                            key=f"resource_{input_key}_rate_{selected_zone_id}",
                            placeholder="Optional",
                        )
                    with price_col:
                        price = st.number_input(
                            price_label, min_value=0.0, value=None,
                            key=f"resource_{input_key}_price_{selected_zone_id}",
                            placeholder="Optional",
                        )
                    if rate is not None:
                        rate_name = "irrigation_liters_ha" if input_key == "irrigation" else f"{input_key}_rate_kg_ha"
                        estimate_inputs[rate_name] = rate
                    if price is not None:
                        price_name = "irrigation_price_rwf_1000_liters" if input_key == "irrigation" else f"{input_key}_price_rwf_kg"
                        estimate_inputs[price_name] = price
                estimate = st.form_submit_button("Calculate quantities and cost", type="primary")

            if estimate:
                if area is None or area <= 0:
                    st.error("Enter a cultivated area greater than zero.")
                else:
                    estimate_inputs["area_cultivated"] = area
                    if rainfall is not None:
                        estimate_inputs["rainfall_mm"] = rainfall
                    result = api_client.get_zone_resources(selected_zone_id, **estimate_inputs)
                    if not result:
                        st.error("Resource quantities could not be calculated. Check the zone and backend connection.")
                    else:
                        st.session_state[f"resource_estimate_{selected_zone_id}"] = result
                        quantities = result.get("quantities") or {}
                        costs = result.get("costs_rwf") or {}
                        if quantities:
                            display_rows = [
                                {"Resource": name.replace("_", " ").title(), "Quantity": f"{quantity:,.2f}"}
                                for name, quantity in quantities.items()
                            ]
                            st.dataframe(display_rows, width="stretch", hide_index=True)
                        total = result.get("estimated_cost_rwf")
                        if total is not None:
                            st.metric("Cost of entered resources", f"RWF {total:,.0f}")
                            if costs:
                                st.caption("Costed items: " + ", ".join(costs.keys()))
                        elif result.get("missing_inputs"):
                            st.info("Quantities are shown, but a complete cost needs a price for each entered resource.")
                        st.caption(result.get("basis", "Calculated from the values entered."))
    except requests.exceptions.RequestException as exc:
        logger.exception("Network error in planning view")
        render_error_page("network", str(exc))
    except Exception as exc:
        logger.exception("Unexpected error in planning view")
        render_error_page("system", str(exc))
