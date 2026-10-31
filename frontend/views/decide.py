import logging
import math
from typing import Any
import requests
import streamlit as st
from components.ai_response import render_advisor_response
from components.badges import priority_badge, status_badge
from components.charts import render_district_ranking_chart
from components.errors import error_boundary, render_error_page
from components.icons import render_icon_title
from utils import api_client
from utils.i18n import t

logger = logging.getLogger(__name__)


def _available_ranking_seasons(evidence: dict[str, Any] | None) -> list[str]:
    seasons = evidence.get("available_seasons", []) if isinstance(evidence, dict) else []
    if not isinstance(seasons, list):
        seasons = []
    return [
        "All available seasons",
        *sorted(
            {str(season).strip() for season in seasons if str(season).strip()},
            reverse=True,
        ),
    ]


def _format_yield(value: object, unit: str = "kg/ha") -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "Not available"
    if not math.isfinite(number):
        return "Not available"
    return f"{number:,.1f} {unit}"


def _zone_options(zones: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    options = {}
    for zone in zones:
        if not isinstance(zone, dict):
            continue
        zone_id = zone.get("id")
        if not zone_id:
            continue
        location = " / ".join(
            str(value).strip()
            for value in (zone.get("district"), zone.get("sector"), zone.get("cell"))
            if value and str(value).strip()
        ) or str(zone.get("site_name") or zone_id)
        label = f"{location} · {str(zone_id)[:6]}"
        if label in options:
            label = f"{location} · {zone_id}"
        options[label] = zone
    return options


def _render_assessment_result(
    result: dict[str, Any],
    recommendations: dict[str, Any] | None,
) -> None:
    st.markdown("#### Assessment result")
    metrics = st.columns(3)
    metrics[0].metric("Estimated yield", _format_yield(result.get("yield_per_ha")))
    total = result.get("predicted_yield")
    metrics[1].metric(
        "Estimated total output",
        _format_yield(total, "kg") if total is not None else "Enter cultivated area to estimate total output",
    )
    with metrics[2]:
        st.markdown("**Priority**")
        priority_badge(result.get("priority_level") or "Unknown")

    low = result.get("predicted_yield_low")
    high = result.get("predicted_yield_high")
    if low is not None and high is not None:
        level = result.get("interval_level")
        interval_label = f"{float(level) * 100:.0f}% interval" if isinstance(level, (int, float)) else "Estimated interval"
        unit = "kg" if total is not None else "kg/ha"
        st.caption(f"{interval_label}: {_format_yield(low, unit)}–{_format_yield(high, unit)}")

    warning = result.get("warning")
    if warning:
        st.warning(str(warning))
    if result.get("yield_data_status") == "no_data":
        st.warning("The backend has no matching yield observations. Treat the yield estimate as unavailable.")

    observation_count = result.get("district_observations")
    if isinstance(observation_count, int):
        st.caption(f"Matching district observations: {observation_count}")

    reasons = result.get("priority_reasons") or []
    if reasons:
        st.markdown("**Why this priority?**")
        for reason in reasons:
            st.markdown(f"- {reason}")

    interpretation = result.get("interpretation_note")
    if interpretation:
        st.caption(str(interpretation))

    actions = recommendations.get("recommendations", []) if isinstance(recommendations, dict) else []
    if actions:
        st.markdown("**Suggested next steps**")
        for action in actions:
            st.markdown(f"- {action}")
    elif recommendations is None:
        st.info("The assessment succeeded, but additional action guidance could not be loaded.")


@st.dialog("Agronomic Disease Evaluation", width="large")
def show_disease_eval_dialog(zones: list[dict[str, Any]]) -> None:
    """Modal popup for agronomic disease diagnosis."""
    crops_list = api_client.get_crops()
    zone_options = {
        f"{z.get('district', 'District')} / {z.get('site_name') or z.get('sector') or z.get('id')}": str(z.get("id"))
        for z in zones if z.get("id")
    }
    if not crops_list:
        st.error("Crop choices could not be loaded from the backend.")
        return
    if not zone_options:
        st.info("Register a field zone before requesting disease triage.")
        return

    with st.form("modal_disease_form"):
        c1, c2 = st.columns(2)
        with c1:
            crop = st.selectbox("Target Crop", crops_list)
        with c2:
            selected_zone = st.selectbox("Field Zone", list(zone_options))

        symptoms = st.text_area(
            "Observed Symptoms",
            placeholder="e.g. Pale yellow streaks along leaf veins, premature drying...",
            height=85,
        )
        notes = st.text_input("Additional Field Notes (Optional)", placeholder="e.g. Under-leaf fungal spores")

        submitted = st.form_submit_button("Analyze Agronomic Risk", type="primary", use_container_width=True)

    if submitted:
        if not symptoms.strip():
            st.warning("Please describe the observed symptoms.")
            return

        target_zone = zone_options[selected_zone]
        with st.spinner("Analyzing disease pattern..."):
            diag = api_client.get_disease_risk(
                zone_id=target_zone,
                crop=crop,
                symptoms=symptoms.strip(),
                image_description=notes.strip() or None,
            )
        if diag:
            st.session_state["last_disease_diag"] = diag
            st.rerun()
        else:
            st.error("Diagnosis could not be completed.")

    last_diag = st.session_state.get("last_disease_diag")
    if last_diag:
        st.markdown("---")
        st.markdown(f"##### Condition: {last_diag.get('predicted_disease', 'Unconfirmed')}")
        st.warning("Preliminary triage only—not a confirmed diagnosis. Verify with an RAB or district agronomist before treatment.")
        c_r, c_c = st.columns(2)
        with c_r:
            risk_level = last_diag.get("risk_level")
            status_badge(risk_level if risk_level in {"High", "Medium", "Low"} else "Unknown")
        with c_c:
            conf = last_diag.get("confidence")
            if isinstance(conf, (int, float)) and math.isfinite(float(conf)):
                conf_str = f"{round(conf * 100)}%" if conf <= 1.0 else f"{conf}%"
                st.caption(f"Backend-reported confidence: **{conf_str}**")
            else:
                st.caption("Confidence was not reported.")

        if last_diag.get("plant_identification"):
            st.caption(f"Crop identification: {last_diag['plant_identification']}")
        if last_diag.get("urgency"):
            st.caption(f"Urgency: {str(last_diag['urgency']).replace('_', ' ').title()}")
        observations = last_diag.get("observations") or []
        if observations:
            st.markdown("**Reported or observed signs:**")
            for observation in observations:
                st.markdown(f"- {observation}")
        possible_causes = last_diag.get("possible_causes") or []
        if possible_causes:
            st.markdown("**Other possible causes to check:**")
            for cause in possible_causes:
                st.markdown(f"- {cause}")
        actions = last_diag.get("recommended_actions", [])
        if actions:
            st.markdown("**Action Guidance:**")
            for act in actions:
                st.markdown(f"- {act}")
        if last_diag.get("interpretation_note"):
            st.caption(str(last_diag["interpretation_note"]))
        if last_diag.get("source"):
            st.caption(f"Analysis source: {last_diag['source']}")


@error_boundary("Decisions")
def render_decide():
    try:
        render_icon_title(
            "assets/brain.svg",
            t("decisions.header", default="Decision Making"),
            t(
                "decisions.subtitle",
                default="Assess a field, compare historical district evidence, and review practical next steps.",
            ),
        )

        tab_assess, tab_evidence, tab_actions, tab_ai = st.tabs([
            "Field assessment",
            "District evidence",
            "Recommendations & field risk",
            "AI advisor",
        ])

        zones = api_client.get_zones()
        crops = api_client.get_crops()
        zone_options = _zone_options(zones)

        # ── TAB 1: BACKEND FIELD ASSESSMENT ────────────────────────────
        with tab_assess:
            st.markdown("### Estimate yield and priority for a registered field")
            st.caption(
                "The backend uses available historical crop and district observations. "
                "A result is an estimate, not a guaranteed farm outcome."
            )
            if not zone_options:
                st.info("No registered field zones are available. Add a zone before running an assessment.")
            elif not crops:
                st.error("Crop choices could not be loaded from the backend.")
            else:
                zone_labels = list(zone_options)
                selected_zone_label = st.selectbox(
                    "Field zone",
                    zone_labels,
                    key="decision_assessment_zone",
                )
                selected_zone = zone_options[selected_zone_label]
                selected_crop = st.selectbox(
                    "Crop",
                    crops,
                    key="decision_assessment_crop",
                )
                evidence_for_crop = api_client.get_evidence_ranking(selected_crop)
                available_seasons = (
                    evidence_for_crop.get("available_seasons", [])
                    if isinstance(evidence_for_crop, dict)
                    else []
                )
                seasons = sorted(
                    {str(season).strip() for season in available_seasons if str(season).strip()},
                    reverse=True,
                )
                if evidence_for_crop is None:
                    st.error("Crop seasons could not be loaded from the backend. Please try again later.")
                elif not seasons:
                    st.info("The backend has no recorded seasons for this crop, so an assessment cannot be run yet.")
                else:
                    season_key = "decision_assessment_season"
                    if st.session_state.get(season_key) not in seasons:
                        st.session_state.pop(season_key, None)
                    selected_season = st.selectbox(
                        "Season",
                        seasons,
                        key=season_key,
                    )

                    known_area = selected_zone.get("area_cultivated") or selected_zone.get("area_ha")
                    try:
                        area_default = float(known_area) if known_area is not None else 1.0
                    except (TypeError, ValueError):
                        area_default = 1.0
                    if not math.isfinite(area_default) or area_default <= 0:
                        known_area = None
                        area_default = 1.0
                    assessment_key = "decision_last_assessment"
                    with st.form("decision_assessment_form"):
                        include_area = st.checkbox(
                            "Estimate total output for a cultivated area",
                            value=known_area is not None,
                            help="Leave unchecked to get yield per hectare only. Total output is calculated only when you provide an area.",
                        )
                        area = (
                            st.number_input(
                                "Cultivated area (ha)",
                                min_value=0.01,
                                max_value=100000.0,
                                value=area_default,
                                step=0.1,
                            )
                            if include_area
                            else None
                        )
                        submitted = st.form_submit_button(
                            "Run field assessment",
                            type="primary",
                            use_container_width=True,
                        )

                    if submitted:
                        payload = {
                            "zone_id": str(selected_zone["id"]),
                            "crop": selected_crop,
                            "season": selected_season,
                        }
                        if area is not None:
                            payload["area_cultivated"] = area
                        with st.spinner("Requesting an assessment from the backend..."):
                            result = api_client.predict_yield(payload)
                        if isinstance(result, dict):
                            with st.spinner("Loading action guidance..."):
                                actions = api_client.get_zone_recommendations(str(selected_zone["id"]))
                            st.session_state[assessment_key] = {
                                "zone_id": str(selected_zone["id"]),
                                "crop": selected_crop,
                                "season": selected_season,
                                "result": result,
                                "recommendations": actions,
                            }
                        else:
                            st.error(
                                "The backend could not complete this assessment. "
                                "Check the selected field, crop, season, and API connection."
                            )

                    last_assessment = st.session_state.get(assessment_key)
                    if (
                        isinstance(last_assessment, dict)
                        and last_assessment.get("zone_id") == str(selected_zone["id"])
                        and last_assessment.get("crop") == selected_crop
                        and last_assessment.get("season") == selected_season
                    ):
                        st.markdown("---")
                        _render_assessment_result(
                            last_assessment["result"],
                            last_assessment.get("recommendations"),
                        )

        # ── TAB 2: OBSERVED DISTRICT EVIDENCE ──────────────────────────
        with tab_evidence:
            if not crops:
                st.error("Crop choices could not be loaded from the backend.")
            else:
                c1, c2 = st.columns(2)
                with c1:
                    selected_crop = st.selectbox(
                        "Crop",
                        crops,
                        key="rank_crop_select",
                    )
                all_evidence = api_client.get_evidence_ranking(crop=selected_crop)
                seasons = _available_ranking_seasons(all_evidence)
                if isinstance(all_evidence, dict) and all_evidence.get("offline_fallback"):
                    st.warning(
                        "The live API is unavailable. Showing bundled historical NISR SAS data; "
                        "field-specific assessments and saved actions need the live service."
                    )
                season_key = "rank_season_select"
                if st.session_state.get(season_key) not in seasons:
                    st.session_state.pop(season_key, None)
                with c2:
                    selected_season = st.selectbox(
                        "Season",
                        seasons,
                        key=season_key,
                    )
                query_season = None if selected_season == "All available seasons" else selected_season
                if all_evidence is None:
                    st.error("Historical district evidence could not be loaded from the backend.")
                else:
                    with st.spinner("Loading district comparisons..."):
                        rankings = api_client.get_district_ranking(crop=selected_crop, season=query_season)
                        evidence = (
                            all_evidence if query_season is None
                            else api_client.get_evidence_ranking(crop=selected_crop, season=query_season)
                        )

                    valid_rankings = []
                    for record in rankings:
                        try:
                            yield_value = float(record.get("yield_per_ha"))
                        except (TypeError, ValueError):
                            continue
                        if record.get("district") and math.isfinite(yield_value):
                            valid_rankings.append(record)

                    national_ref = evidence.get("national_reference_kg_ha") if isinstance(evidence, dict) else None
                    if valid_rankings:
                        top_record = max(valid_rankings, key=lambda record: float(record["yield_per_ha"]))
                        valid_gaps = []
                        for record in valid_rankings:
                            try:
                                gap = float(record.get("yield_gap_kg_ha"))
                            except (TypeError, ValueError):
                                continue
                            if math.isfinite(gap):
                                valid_gaps.append(gap)
                        avg_gap = sum(valid_gaps) / len(valid_gaps) if valid_gaps else None

                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("National reference", _format_yield(national_ref))
                        m2.metric(
                            "Highest observed district",
                            str(top_record["district"]),
                            delta=_format_yield(top_record["yield_per_ha"]),
                        )
                        m3.metric("Average reported gap", _format_yield(avg_gap))
                        m4.metric("Districts with evidence", str(len(valid_rankings)))
                        st.caption(
                            evidence.get("interpretation")
                            or "District comparisons describe recorded historical observations; they do not predict a farm outcome or explain causes."
                        )
                        render_district_ranking_chart(
                            valid_rankings,
                            crop=selected_crop,
                            national_ref=national_ref,
                        )

                        district_options = {
                            str(record["district"]): record for record in valid_rankings
                        }
                        selected_district = st.selectbox(
                            "District details",
                            list(district_options),
                            key="rank_district_inspector",
                        )
                        selected_record = district_options[selected_district]
                        detail_metrics = st.columns(3)
                        detail_metrics[0].metric(
                            "Observed yield",
                            _format_yield(selected_record.get("yield_per_ha")),
                        )
                        detail_metrics[1].metric(
                            "National reference",
                            _format_yield(selected_record.get("benchmark_yield_per_ha")),
                        )
                        detail_metrics[2].metric(
                            "Reported yield gap",
                            _format_yield(selected_record.get("yield_gap_kg_ha")),
                        )
                        st.caption(
                            f"Rank {selected_record.get('rank', 'not available')} · "
                            f"{selected_record.get('observation_count', 0)} matching observations · "
                            f"{selected_crop} · {selected_season}"
                        )
                    else:
                        st.info(f"No district yield observations are available for {selected_crop} and this season.")

        # ── TAB 3: ACTIONS AND COMMUNITY FIELD SIGNALS ─────────────────
        with tab_actions:
            head_col, button_col = st.columns([3.5, 1.5])
            with head_col:
                st.markdown("### Recommendations from saved field assessments")
            with button_col:
                if st.button(
                    "Disease triage",
                    type="primary",
                    use_container_width=True,
                    key="disease_triage_button",
                ):
                    show_disease_eval_dialog(zones)

            recs = api_client.get_recommendations()
            if not recs:
                st.info("No saved field assessments with recommendations are available yet.")
            else:
                for index, rec in enumerate(recs):
                    with st.container(border=True):
                        col1, col2, col3 = st.columns([1.5, 3.5, 1.2])
                        with col1:
                            st.markdown(f"**{rec.get('area', 'Unknown district')}**")
                            st.caption(
                                f"{rec.get('crop', 'Unknown crop')} · "
                                f"{rec.get('season') or 'Season not recorded'}"
                            )
                        with col2:
                            st.markdown(rec.get("text") or "No additional action guidance returned.")
                        with col3:
                            priority_badge(rec.get("priority") or "Unknown")
                            if st.button(
                                "Create plan",
                                key=f"act_{rec.get('zone_id') or index}",
                                use_container_width=True,
                                disabled=not rec.get("zone_id"),
                            ):
                                st.session_state["planning_pending_zone_id"] = str(rec["zone_id"])
                                st.switch_page("pages/8_Planning.py")

            st.markdown("---")
            st.markdown("#### Recent farmer field reports")
            if not zone_options:
                st.info("Register a field zone to review community field reports.")
            else:
                selected_signal_label = st.selectbox(
                    "Field zone",
                    list(zone_options),
                    key="decision_signal_zone",
                )
                selected_signal_zone = zone_options[selected_signal_label]
                with st.spinner("Loading recent field reports..."):
                    signal = api_client.get_field_risk(str(selected_signal_zone["id"]))
                if signal is None:
                    st.warning("Field reports could not be loaded from the backend.")
                elif signal.get("total_reports", 0):
                    st.metric(
                        "Reported field risk",
                        signal.get("risk_level") or "Unknown",
                        delta=f"{signal.get('total_reports', 0)} reports",
                    )
                    latest = signal.get("latest_report") or {}
                    if latest.get("symptoms"):
                        st.caption(f"Latest report: {latest['symptoms']}")
                else:
                    st.info("No recent farmer field reports are recorded for this zone.")

        # ── TAB 4: ZONE-CONTEXT AI ADVISOR ────────────────────────────
        with tab_ai:
            if not zone_options:
                st.info("Register a field zone before using the AI advisor.")
            else:
                selected_ai_zone = st.selectbox(
                    "Zone context",
                    list(zone_options),
                    key="decision_ai_zone_tab",
                )
                zone_id = str(zone_options[selected_ai_zone]["id"])
                ai_crop = st.selectbox(
                    "Crop context",
                    ["No specific crop", *crops],
                    key="decision_ai_crop",
                )
                ai_crop = None if ai_crop == "No specific crop" else ai_crop
                ai_season = None
                if ai_crop:
                    ai_evidence = api_client.get_evidence_ranking(ai_crop)
                    ai_seasons = (
                        ai_evidence.get("available_seasons", [])
                        if isinstance(ai_evidence, dict)
                        else []
                    )
                    ai_seasons = sorted(
                        {str(season).strip() for season in ai_seasons if str(season).strip()},
                        reverse=True,
                    )
                    if ai_seasons:
                        ai_season = st.selectbox(
                            "Season context",
                            ["All available seasons", *ai_seasons],
                            key="decision_ai_season",
                        )
                        if ai_season == "All available seasons":
                            ai_season = None
                messages_key = f"decision_ai_messages_{zone_id}"
                if messages_key not in st.session_state:
                    st.session_state[messages_key] = []

                for message in st.session_state[messages_key]:
                    with st.chat_message(message["role"]):
                        if message["role"] == "assistant" and isinstance(message.get("response"), dict):
                            render_advisor_response(message["response"])
                        else:
                            st.markdown(message["content"])

                prompt = st.chat_input(
                    t(
                        "decisions.ai_placeholder",
                        default="Ask about crop varieties, fertilizer timing, or drought mitigation...",
                    ),
                    key=f"decision_ai_input_box_{zone_id}",
                )
                if prompt:
                    if len(prompt) > 500:
                        st.warning("Please keep each question to 500 characters or fewer.")
                    else:
                        prior_history = [
                            {
                                "role": message["role"],
                                "content": str(message["content"])[:500],
                            }
                            for message in st.session_state[messages_key][-8:]
                            if message.get("role") in {"user", "assistant"}
                        ]
                        st.session_state[messages_key].append({"role": "user", "content": prompt})
                        with st.chat_message("user"):
                            st.markdown(prompt)
                        with st.chat_message("assistant"):
                            with st.spinner("Sending your question to the backend advisor..."):
                                response = api_client.chat(
                                    prompt,
                                    zone_id=zone_id,
                                    history=prior_history,
                                    crop=ai_crop,
                                    season=ai_season,
                                )
                            if response and response.get("answer"):
                                answer = str(response["answer"])
                                render_advisor_response(response)
                                st.session_state[messages_key].append({
                                    "role": "assistant",
                                    "content": answer,
                                    "response": response,
                                })
                            else:
                                st.error("The advisor could not respond. Please check the backend connection and try again.")

                if st.session_state[messages_key] and st.button("Clear chat", key="clear_decision_ai_tab"):
                    st.session_state[messages_key] = []
                    st.rerun()

    except requests.exceptions.RequestException as e:
        logger.error("Network error in decide.py: %s", e)
        render_error_page("network", str(e))
    except Exception as e:
        logger.error("Unexpected error in decide.py: %s", e, exc_info=True)
        render_error_page("system", str(e))
