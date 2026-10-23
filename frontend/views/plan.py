import logging
from datetime import date, timedelta
from json import dumps

import requests
import streamlit as st
from components.errors import render_error_page
from components.icons import render_icon_title
from utils import api_client
from utils.i18n import t

logger = logging.getLogger(__name__)


def render_plan() -> None:
    try:
        render_icon_title("assets/calendar.svg", "Planning", "Assign owners, due dates, and resources for agreed field work.")
        if st.session_state.pop("plan_saved_flash", False):
            st.success("Plan saved.")
        zones = api_client.get_zones()
        zone_options: dict[str, str] = {}
        zone_by_id: dict[str, dict] = {}
        for zone in zones:
            if not zone.get("id"):
                continue
            zone_id = str(zone["id"])
            label_parts = [zone.get("district") or "Unknown district", zone.get("sector") or zone.get("cell"), zone.get("crop_type") or zone.get("crop")]
            label = " / ".join(str(part) for part in label_parts if part)
            label = f"{label or 'Saved zone'} · {zone_id[-6:]}"
            zone_options[zone_id] = label
            zone_by_id[zone_id] = zone
        if not zone_options:
            st.info("Add or load a zone before creating a plan.")
            return

        selected_zone_id = st.selectbox(
            t("plan.select_zone"),
            options=list(zone_options),
            format_func=lambda zone_id: zone_options[zone_id],
            key="planning_zone_id",
        )
        selected_zone = zone_by_id[selected_zone_id]
        decision_context = st.session_state.get("plan_decision_context") or {}
        has_decision_context = str(decision_context.get("zone_id")) == selected_zone_id
        handoff_title = st.session_state.get("plan_title") if has_decision_context else None
        previous_plan_zone = st.session_state.get("_plan_form_zone_id")
        if previous_plan_zone and previous_plan_zone != selected_zone_id:
            draft_keys = {
                "plan_title", "plan_planned_season_context", "plan_scenario", "plan_action_count",
            }
            draft_prefixes = (
                "plan_action_title_", "plan_action_notes_", "plan_action_time_",
                "plan_action_owner_", "plan_action_due_",
            )
            for key in list(st.session_state):
                if key in draft_keys or key.startswith(draft_prefixes):
                    st.session_state.pop(key, None)
            if handoff_title:
                st.session_state["plan_title"] = handoff_title
            st.session_state["plan_scenario"] = "priority_followup"
        if previous_plan_zone != selected_zone_id:
            # Historical survey periods are evidence, not the season this team plans to work in.
            st.session_state["plan_planned_season_context"] = ""
        if decision_context and not has_decision_context:
            st.session_state.pop("plan_decision_context", None)
        st.session_state["_plan_form_zone_id"] = selected_zone_id
        context = [
            ("Crop", selected_zone.get("crop_type") or selected_zone.get("crop")),
            ("Season on zone record", selected_zone.get("season")),
            ("Cultivated area", f"{selected_zone['area_cultivated']} ha" if selected_zone.get("area_cultivated") is not None else None),
        ]
        with st.container(border=True):
            st.markdown(f"### {zone_options[selected_zone_id]}")
            if selected_zone.get("area_cultivated") is not None:
                st.caption("Cultivated area is from the saved zone record. Confirm it before using it for procurement or budgeting.")
            st.caption(" · ".join(f"{label}: {value}" for label, value in context if value not in (None, "")) or "Zone details have not been recorded yet.")

        if has_decision_context:
            with st.container(border=True):
                st.caption("Decision context")
                context_season = decision_context.get("season") or "All available seasons"
                context_summary = " · ".join(str(value) for value in (
                    decision_context.get("crop"), context_season
                ) if value)
                if context_summary:
                    st.markdown(f"**{context_summary}**")
                st.write(decision_context.get("assessment") or "No assessment details were attached.")
                raw_provenance = decision_context.get("basis")
                provenance_items = raw_provenance if isinstance(raw_provenance, list) else [raw_provenance]
                provenance = " · ".join(_friendly_source_name(item) for item in provenance_items if item)
                st.caption(
                    f"Evidence: {provenance}. Confirm current field conditions with the responsible local team before acting."
                    if provenance else "Planning context only. Confirm current field conditions with the responsible local team before acting."
                )

        st.subheader("Saved plans for this area")
        plans = api_client.get_zone_plans(selected_zone_id)
        plan_groups: dict[str, list[dict]] = {}
        for plan in plans:
            resources = plan.get("resources_json") or {}
            plan_context = resources.get("plan_context") or {}
            signature = _plan_signature(
                plan.get("title"), plan.get("roadmap_json") or [], plan_context, resources,
            )
            plan_groups.setdefault(signature, []).append(plan)

        dated_actions = []
        open_actions = []
        open_actions_without_dates = 0
        for plan_item in plans:
            for step in plan_item.get("roadmap_json") or []:
                if step.get("status", "planned") != "completed":
                    open_actions.append(step)
                due_text = step.get("due_date")
                if not due_text or step.get("status", "planned") == "completed":
                    if not due_text and step.get("status", "planned") != "completed":
                        open_actions_without_dates += 1
                    continue
                try:
                    due = date.fromisoformat(str(due_text))
                except ValueError:
                    continue
                dated_actions.append((due, plan_item.get("title") or "Untitled plan", step))
        today = date.today()
        overdue = [item for item in dated_actions if item[0] < today]
        upcoming = [item for item in dated_actions if today <= item[0] <= today + timedelta(days=7)]
        summary_cols = st.columns(4)
        summary_cols[0].metric("Saved plans", len(plans))
        summary_cols[1].metric("Open actions", len(open_actions))
        summary_cols[2].metric("Overdue", len(overdue))
        summary_cols[3].metric("Due in 7 days", len(upcoming))
        if open_actions_without_dates:
            st.caption(f"{open_actions_without_dates} open action(s) have no due date set.")
        if overdue or upcoming:
            for due, plan_title, step in sorted(overdue + upcoming, key=lambda item: item[0])[:6]:
                is_overdue = due < today
                st.warning(f"Overdue · {step.get('title', 'Activity')} · {plan_title} · due {due.isoformat()}" if is_overdue else f"Due soon · {step.get('title', 'Activity')} · {plan_title} · due {due.isoformat()}")
        else:
            st.caption("No overdue actions or actions due in the next 7 days.")
        if not plans:
            st.info("No action plans have been saved for this area yet.")
        else:
            for group in plan_groups.values():
                plan = group[0]
                title = plan.get("title") or "Untitled plan"
                steps = plan.get("roadmap_json") or []
                resources = plan.get("resources_json") or {}
                label = f"{title} · {len(steps)} actions"
                if len(group) > 1:
                    label += f" · {len(group)} identical saves"
                else:
                    saved_at = str(plan.get("created_at") or "save time unknown")
                    short_id = str(plan.get("id") or "")[-6:]
                    label += f" · {saved_at}"
                    if short_id:
                        label += f" · {short_id}"
                with st.expander(label, expanded=False):
                    if len(group) > 1:
                        saved_copies = [
                            f"{item.get('created_at') or 'creation time unavailable'} · ID {str(item.get('id') or '')[-6:]}"
                            for item in group
                        ]
                        st.caption("Exact duplicate saves are grouped here; each database record is retained.")
                        st.caption("Saved copies: " + " | ".join(saved_copies))
                    plan_context = resources.get("plan_context") or {}
                    context_line = " · ".join(str(value) for value in (
                        plan_context.get("scenario"), plan_context.get("crop"), plan_context.get("season")
                    ) if value)
                    if context_line:
                        st.caption(context_line.replace("_", " ").title())
                    saved_decision = plan_context.get("decision_context") or {}
                    if saved_decision:
                        st.markdown("**Decision evidence at plan creation**")
                        st.write(saved_decision.get("assessment") or "Assessment summary unavailable.")
                        saved_sources = saved_decision.get("sources") or []
                        if saved_sources:
                            st.caption("Evidence: " + " · ".join(
                                _friendly_source_name(source) for source in saved_sources
                            ))
                        st.caption(
                            f"Scope: {saved_decision.get('season_scope') or 'Not recorded'}. "
                            "Historical district evidence; verify current field conditions before acting."
                        )
                    counts = {name: sum(1 for step in steps if step.get("status", "planned") == name)
                              for name in ("planned", "in_progress", "completed", "blocked")}
                    st.caption("Activity status · " + " · ".join(f"{name.replace('_', ' ').title()}: {count}" for name, count in counts.items()))
                    for step in steps:
                        timing = step.get("timeframe") or "Timing not set"
                        owner = step.get("owner")
                        owner_label = f" · Responsible: {owner}" if owner else " · Owner not assigned"
                        status = str(step.get("status") or "planned").replace("_", " ").title()
                        due_date = step.get("due_date")
                        st.markdown(f"**{step.get('step_number', '')}. {step.get('title') or 'Untitled action'}** · {status} · {timing}{owner_label}")
                        if due_date:
                            st.caption(f"Due: {due_date}")
                        if step.get("description"):
                            st.write(step["description"])
                    saved_quantities = resources.get("quantities") or {}
                    if not saved_quantities:
                        saved_quantities = {
                            key: resources[key] for key in
                            ("seeds_kg", "dap_kg", "urea_kg", "irrigation_liters")
                            if resources.get(key) is not None
                        }
                    saved_costs = resources.get("costs_rwf") or {}
                    if saved_quantities or saved_costs or resources.get("estimated_cost_rwf") is not None:
                        st.markdown("**Resource estimate saved with this plan**")
                        if saved_quantities:
                            st.caption("Quantities: " + " · ".join(
                                f"{name.replace('_', ' ').title()}: {value:,.2f}"
                                for name, value in saved_quantities.items() if name != "fertilizer_kg"
                            ))
                        if resources.get("estimated_cost_rwf") is not None:
                            st.caption(
                                f"Entered-item estimate: RWF {resources['estimated_cost_rwf']:,.0f}. "
                                "This is not a complete farm budget or a supplier quote."
                            )
                        elif saved_costs:
                            st.caption("Some resource prices were not entered, so there is no complete entered-item total.")
                        if resources.get("rate_source") or resources.get("price_source") or resources.get("prices_checked_on"):
                            st.caption(
                                f"Rate source: {resources.get('rate_source') or 'not recorded'} · "
                                f"Price source: {resources.get('price_source') or 'not recorded'} · "
                                f"Prices checked: {resources.get('prices_checked_on') or 'date not recorded'}"
                            )
                    missing = resources.get("missing_inputs") or []
                    if missing:
                        st.caption("Resource estimate incomplete; missing inputs: " + ", ".join(str(item) for item in missing))

        with st.expander("Optional resource calculator", expanded=False):
            st.caption("Estimates use only values entered here. This app supplies no agronomic rates or market prices. Record the source and date so unverified entries are not mistaken for confirmed local data.")
            zone_area = selected_zone.get("area_cultivated") or selected_zone.get("area_ha")
            with st.form(f"resource_estimate_form_{selected_zone_id}"):
                area = st.number_input(
                    "Cultivated area (ha)", min_value=0.0,
                    value=float(zone_area) if zone_area is not None else None,
                    placeholder="Enter area if it is not recorded",
                    key=f"resource_area_{selected_zone_id}",
                )
                estimate_inputs = {}
                st.markdown("**Seed and crop inputs**")
                for input_key, quantity_label, unit, price_label, price_unit in [
                    ("seed", "Seed", "kg/ha", "Price", "RWF/kg"),
                    ("dap", "DAP fertilizer", "kg/ha", "Price", "RWF/kg"),
                    ("urea", "Urea fertilizer", "kg/ha", "Price", "RWF/kg"),
                    ("irrigation", "Irrigation water", "litres/ha", "Price", "RWF/1,000 litres"),
                ]:
                    rate_col, price_col = st.columns(2)
                    with rate_col:
                        rate = st.number_input(
                            f"{quantity_label} rate ({unit})", min_value=0.0, value=None,
                            key=f"resource_{input_key}_rate_{selected_zone_id}", placeholder="Optional",
                        )
                    with price_col:
                        price = st.number_input(
                            f"{quantity_label} {price_label.lower()} ({price_unit})", min_value=0.0, value=None,
                            key=f"resource_{input_key}_price_{selected_zone_id}", placeholder="Optional",
                        )
                    if rate is not None:
                        estimate_inputs["irrigation_liters_ha" if input_key == "irrigation" else f"{input_key}_rate_kg_ha"] = rate
                    if price is not None:
                        estimate_inputs["irrigation_price_rwf_1000_liters" if input_key == "irrigation" else f"{input_key}_price_rwf_kg"] = price

                st.markdown("**Work, logistics and other costs**")
                labor_cols = st.columns(2)
                with labor_cols[0]:
                    labor_days = st.number_input("Labor (days/ha)", min_value=0.0, value=None,
                                                 key=f"resource_labor_days_{selected_zone_id}", placeholder="Optional")
                with labor_cols[1]:
                    labor_price = st.number_input("Labor cost (RWF/day)", min_value=0.0, value=None,
                                                  key=f"resource_labor_price_{selected_zone_id}", placeholder="Optional")
                if labor_days is not None:
                    estimate_inputs["labor_days_ha"] = labor_days
                if labor_price is not None:
                    estimate_inputs["labor_price_rwf_day"] = labor_price

                cost_labels = [
                    ("land_preparation_cost_rwf_ha", "Land preparation (RWF/ha)"),
                    ("crop_protection_cost_rwf_ha", "Crop protection (RWF/ha)"),
                    ("equipment_hire_cost_rwf_ha", "Equipment hire (RWF/ha)"),
                    ("transport_cost_rwf_ha", "Transport and delivery (RWF/ha)"),
                    ("postharvest_cost_rwf_ha", "Harvest and post-harvest handling (RWF/ha)"),
                    ("storage_packaging_cost_rwf_ha", "Storage and packaging (RWF/ha)"),
                    ("other_cost_rwf_ha", "Other agreed costs (RWF/ha)"),
                ]
                cost_columns = st.columns(2)
                for index, (input_key, label) in enumerate(cost_labels):
                    with cost_columns[index % 2]:
                        value = st.number_input(label, min_value=0.0, value=None,
                                                key=f"resource_{input_key}_{selected_zone_id}", placeholder="Optional")
                    if value is not None:
                        estimate_inputs[input_key] = value
                contingency = st.number_input("Contingency (% of entered costs)", min_value=0.0, max_value=100.0,
                                              value=None, key=f"resource_contingency_{selected_zone_id}", placeholder="Optional")
                if contingency is not None:
                    estimate_inputs["contingency_pct"] = contingency
                provenance_cols = st.columns(2)
                with provenance_cols[0]:
                    rate_source = st.text_input(
                        "Rate source (optional)", max_chars=200,
                        key=f"resource_rate_source_{selected_zone_id}",
                        placeholder="Extension advice or other source",
                    )
                with provenance_cols[1]:
                    price_source = st.text_input(
                        "Price source/vendor (optional)", max_chars=200,
                        key=f"resource_price_source_{selected_zone_id}",
                        placeholder="Supplier, cooperative, or market quote",
                    )
                prices_checked_on = st.date_input(
                    "Prices checked on (optional)", value=None,
                    key=f"resource_prices_date_{selected_zone_id}",
                )
                estimate = st.form_submit_button("Calculate quantities and cost", type="primary")

            if estimate:
                if area is None or area <= 0:
                    st.error("Enter a cultivated area greater than zero.")
                else:
                    estimate_inputs["area_cultivated"] = area
                    estimate_inputs["area_source"] = "saved_zone_record" if zone_area is not None else "entered_for_estimate"
                    estimate_inputs["rate_source"] = rate_source.strip() or None
                    estimate_inputs["price_source"] = price_source.strip() or None
                    estimate_inputs["prices_checked_on"] = prices_checked_on.isoformat() if prices_checked_on else None
                    result = api_client.get_zone_resources(selected_zone_id, **estimate_inputs)
                    if not result:
                        st.error("Resource quantities could not be calculated. Check the zone and backend connection.")
                    else:
                        st.session_state[f"resource_estimate_{selected_zone_id}"] = result
            result = st.session_state.get(f"resource_estimate_{selected_zone_id}")
            if result:
                quantities = result.get("quantities") or {}
                costs = result.get("costs_rwf") or {}
                if quantities:
                    quantity_labels = {
                        "seeds_kg": "Seed", "dap_kg": "DAP fertilizer", "urea_kg": "Urea",
                        "fertilizer_kg": "Total fertilizer entered", "irrigation_liters": "Irrigation water",
                        "labor_days": "Labor days",
                    }
                    quantity_units = {"seeds_kg": "kg", "dap_kg": "kg", "urea_kg": "kg",
                                      "fertilizer_kg": "kg", "irrigation_liters": "litres", "labor_days": "days"}
                    display_rows = [
                        {"Resource": quantity_labels.get(name, name.replace("_", " ").title()),
                         "Estimated quantity": f"{quantity:,.2f} {quantity_units.get(name, '')}".strip()}
                        for name, quantity in quantities.items() if name != "fertilizer_kg"
                    ]
                    st.dataframe(display_rows, width="stretch", hide_index=True)
                if costs:
                    cost_labels = {
                        "seeds": "Seed", "dap": "DAP fertilizer", "urea": "Urea",
                        "irrigation": "Irrigation water", "labor": "Labor",
                        "land_preparation": "Land preparation", "crop_protection": "Crop protection",
                        "equipment_hire": "Equipment hire", "transport": "Transport and delivery",
                        "postharvest_handling": "Harvest and post-harvest", "storage_packaging": "Storage and packaging",
                        "other_costs": "Other agreed costs", "contingency": "Contingency",
                    }
                    st.dataframe([{"Cost item": cost_labels.get(name, name.replace("_", " ").title()),
                                   "Estimate": f"RWF {amount:,.0f}"}
                                  for name, amount in costs.items()], width="stretch", hide_index=True)
                total = result.get("estimated_cost_rwf")
                if total is not None:
                    st.metric("Estimated cost of entered items", f"RWF {total:,.0f}")
                elif result.get("missing_inputs"):
                    st.info("Quantities are estimated. Add the missing prices to total these entered items: " +
                            ", ".join(item.replace("_", " ") for item in result["missing_inputs"]))
                st.caption(result.get("basis", "Calculated from the values entered."))
                area_source_label = "saved zone record" if result.get("area_source") == "saved_zone_record" else "entered by planner"
                st.caption(f"Area source: {area_source_label}. Rate source: {result.get('rate_source') or 'not recorded'}. Price source: {result.get('price_source') or 'not recorded'}. Price date: {result.get('prices_checked_on') or 'not recorded'}.")
                st.caption("This is a user-entered estimate, not verified supplier pricing or a complete farm budget. Confirm the area, rates, prices, source and availability locally.")

        st.subheader("Build an action plan")
        st.caption("Write actions your team has agreed on. Each action can include a timeframe and a responsible person or team.")
        scenario_labels = {
            "season_start": "Prepare for a planting season",
            "priority_followup": "Follow up a priority zone",
            "field_observation_followup": "Verify a farmer field report",
            "cooperative_input_readiness": "Coordinate cooperative input needs",
            "custom": "Other agreed work",
        }
        scenario = st.selectbox("What work is this plan for?", list(scenario_labels), format_func=lambda key: scenario_labels[key], key="plan_scenario")
        crop_catalog = {
            str(crop).strip().casefold(): str(crop).strip()
            for crop in api_client.get_crops()
            if str(crop).strip()
        }
        zone_crop = str(selected_zone.get("crop_type") or selected_zone.get("crop") or "").strip()
        decision_crop = str(decision_context.get("crop") or "").strip() if has_decision_context else ""
        if decision_crop:
            crop_catalog.setdefault(decision_crop.casefold(), decision_crop)
        if zone_crop:
            crop_catalog.setdefault(zone_crop.casefold(), zone_crop)
        crop_options = sorted(crop_catalog.values(), key=str.casefold)
        no_crop = "Not specified"
        other_crop = "Other / not listed"
        if st.session_state.get("_plan_crop_zone_id") != selected_zone_id:
            # Zone and historical evidence crops are context only; require an explicit planning choice.
            st.session_state["plan_planned_crop_selector"] = no_crop
            st.session_state["_plan_crop_zone_id"] = selected_zone_id
        # Ask for an intended season; do not turn historical decision evidence into a plan date.
        season_default = ""
        context_cols = st.columns(2)
        with context_cols[0]:
            crop_choice = st.selectbox(
                "Crop",
                [no_crop, *crop_options, other_crop],
                key="plan_planned_crop_selector",
                help="Search the full crop list. Choose ‘Other / not listed’ to enter another crop.",
            )
            if crop_choice == other_crop:
                plan_crop = st.text_input(
                    "Enter crop", value="",
                    max_chars=50, key=f"plan_crop_custom_{selected_zone_id}",
                )
            else:
                plan_crop = "" if crop_choice == no_crop else crop_choice
        with context_cols[1]:
            plan_season = st.text_input(
                "Planned season (confirmed by your team)", value=season_default, max_chars=80,
                key="plan_planned_season_context",
                help="Historical NISR periods are shown separately as evidence. Enter the season this plan is actually for.",
            )
        st.caption("Select the crop and season agreed for upcoming work. Saved-zone details and NISR assessment periods provide context, not a verified future plan.")
        action_count = st.number_input("Number of actions", min_value=1, max_value=8, value=1, step=1, key="plan_action_count")
        with st.form("save_plan_form", clear_on_submit=True):
            title = st.text_input("Plan title", placeholder="Name the agreed work", key="plan_title")
            roadmap = []
            for index in range(int(action_count)):
                st.markdown(f"**Action {index + 1}**")
                action_title = st.text_input("Action", key=f"plan_action_title_{index}", placeholder="What needs to happen?")
                detail_cols = st.columns([2, 1, 1.1])
                with detail_cols[0]:
                    description = st.text_area("Notes", key=f"plan_action_notes_{index}", placeholder="Add relevant instructions or context", height=90)
                with detail_cols[1]:
                    timeframe = st.text_input("When", key=f"plan_action_time_{index}", placeholder="Date or period")
                with detail_cols[2]:
                    owner = st.text_input("Responsible person/team", key=f"plan_action_owner_{index}", placeholder="Optional")
                due_date = st.date_input("Due date (optional)", value=None, key=f"plan_action_due_{index}")
                roadmap.append({
                    "step_number": index + 1,
                    "title": action_title.strip(),
                    "description": description.strip(),
                    "timeframe": timeframe.strip() or None,
                    "owner": owner.strip() or None,
                    "due_date": due_date.isoformat() if due_date else None,
                    "status": "planned",
                })
            submitted = st.form_submit_button("Save plan", type="primary", width="stretch")

        if submitted:
            if scenario in {"season_start", "cooperative_input_readiness"} and (not plan_crop.strip() or not plan_season.strip()):
                st.error("For seasonal preparation or input coordination, select the crop and enter the confirmed planned season before saving.")
                return
            if not title.strip() or any(not step["title"] or not step["description"] for step in roadmap):
                st.error("Add a plan title and complete an action title and notes for each step.")
                return
            decision_for_plan = ({
                "district": decision_context.get("district"),
                "assessment": decision_context.get("assessment"),
                "sources": decision_context.get("basis") or [],
                "season_scope": decision_context.get("season") or "All available seasons",
            } if has_decision_context else None)
            resource_payload = st.session_state.get(f"resource_estimate_{selected_zone_id}") or {}
            plan_context_payload = {
                "scenario": scenario,
                "crop": plan_crop.strip() or None,
                "season": plan_season.strip() or None,
                "decision_context": decision_for_plan,
            }
            candidate_signature = _plan_signature(
                title.strip(), roadmap, plan_context_payload,
                {**resource_payload, "plan_context": plan_context_payload},
            )
            if any(
                _plan_signature(
                    existing.get("title"), existing.get("roadmap_json") or [],
                    (existing.get("resources_json") or {}).get("plan_context") or {},
                    existing.get("resources_json") or {},
                ) == candidate_signature
                for existing in plans
            ):
                st.warning("This plan matches a saved plan with the same actions and resource estimate. Update its title, actions, season or estimate to save a distinct plan.")
                return
            result = api_client.create_roadmap({
                "zone_id": selected_zone_id,
                "title": title.strip(),
                "roadmap": roadmap,
                "resources": resource_payload,
                "scenario": scenario,
                "crop": plan_crop.strip() or None,
                "season": plan_season.strip() or None,
                "decision_context": decision_for_plan,
                "created_by": "frontend",
            })
            if result:
                st.session_state["plan_saved_flash"] = True
                st.session_state.pop("plan_decision_context", None)
                st.session_state.pop(f"resource_estimate_{selected_zone_id}", None)
                api_client.get_zone_plans.clear()
                api_client.get_roadmap.clear()
                st.rerun()
            else:
                st.error("The plan could not be saved. Check the backend connection and try again.")

    except requests.exceptions.RequestException as exc:
        logger.exception("Network error in planning view")
        render_error_page("network", str(exc))
    except Exception as exc:
        logger.exception("Unexpected error in planning view")
        render_error_page("system", str(exc))


def _friendly_source_name(source: object) -> str:
    label = str(source or "").strip()
    normalized = label.casefold()
    if "database" in normalized or "release" in normalized:
        return "NISR database records"
    if "sas" in normalized or "historical" in normalized:
        return "Official NISR historical tables"
    return label or "Source details unavailable"


def _plan_signature(title: object, roadmap: list[dict], context: dict, resources: dict) -> str:
    """Stable content signature used to group and prevent exact accidental resaves."""
    step_fields = ("step_number", "title", "description", "timeframe", "owner", "due_date", "status")
    resource_fields = (
        "area_ha", "user_inputs", "quantities", "costs_rwf", "estimated_cost_rwf",
        "area_source", "rate_source", "price_source", "prices_checked_on",
    )
    normalized_steps = [
        {field: step.get(field, "planned" if field == "status" else None) for field in step_fields}
        for step in roadmap
    ]
    resource_values = {
        field: resources.get(field) for field in resource_fields
        if resources.get(field) not in (None, {}, [], "")
    }
    payload = {
        "title": str(title or "").strip().casefold(),
        "roadmap": normalized_steps,
        "context": {
            "scenario": context.get("scenario"),
            "crop": str(context.get("crop") or "").strip().casefold() or None,
            "season": str(context.get("season") or "").strip().casefold() or None,
            "decision_context": context.get("decision_context"),
        },
        "resources": resource_values,
    }
    return dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
