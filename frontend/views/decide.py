import logging

import requests
import streamlit as st
from components.errors import render_error_page
from components.icons import render_icon_title
from utils import api_client
from utils.assistant_formatting import format_assistant_answer, has_source_citation
from utils.i18n import t

logger = logging.getLogger(__name__)


def render_decide():
    """Show a concise crop comparison and the next useful follow-up."""
    try:
        render_icon_title("assets/brain.svg", t("decisions.header"), t("decisions.subtitle"))
        _render_nisr_comparison()

    except requests.exceptions.RequestException as exc:
        logger.error("Network error in Decide: %s", exc)
        render_error_page("network", str(exc))
    except Exception as exc:
        logger.error("Unexpected error in Decide: %s", exc, exc_info=True)
        render_error_page("system", str(exc))


def _render_nisr_comparison():
    """Compact decision workflow with traceable district yield evidence."""
    crops = api_client.get_crops()
    if not crops:
        st.info("No crop yield evidence is currently available from the configured sources.")
        return

    crop_col, season_col = st.columns(2)
    with crop_col:
        crop = st.selectbox("Crop", crops, key="decision_evidence_crop")
    initial = api_client.get_decision_evidence_ranking(crop)
    if not initial:
        st.warning("Could not retrieve crop evidence. Check the API connection and active data release.")
        return
    seasons = initial.get("available_seasons") or []
    season_options = ["All available seasons", *seasons]
    with season_col:
        selected_season = st.selectbox("Season", season_options, key=f"decision_evidence_season_{crop}")
    result = initial if selected_season == "All available seasons" else api_client.get_decision_evidence_ranking(crop, selected_season)
    if not result:
        st.warning("Could not retrieve evidence for this season.")
        return
    rows = result.get("rows") or []
    if not rows:
        st.info("No district observations match this crop and season. Missing districts are left blank.")
        return

    districts = [str(item["district"]) for item in rows]
    district = st.selectbox("Decision area", districts, key=f"decision_district_{crop}_{selected_season}")
    chosen = next(item for item in rows if item.get("district") == district)
    district_yield = float(chosen["yield_kg_ha"])
    reference = result.get("national_reference_kg_ha")
    difference = district_yield - float(reference) if reference is not None else None

    trend_change = chosen.get("trend_change_pct")
    metric_cols = st.columns(3)
    yield_label = ("Pooled district yield" if selected_season == "All available seasons"
                   else f"District yield · {selected_season}")
    yield_help = ("Pooled across the listed seasons. Production is divided by harvested area when reported; otherwise the source-reported yield is used."
                  if selected_season == "All available seasons" else
                  "Observed district yield for this season; the source-reported value is retained when harvested area is unavailable.")
    metric_cols[0].metric(yield_label, f"{district_yield:,.0f} kg/ha", help=yield_help)
    metric_cols[1].metric("Rwanda crop reference", f"{float(reference):,.0f} kg/ha" if reference is not None else "Unavailable")
    metric_cols[2].metric("District rank", f"{chosen['rank']} of {len(rows)}")
    detail_cols = st.columns(2)
    detail_cols[0].metric("District-season records", int(chosen.get("observation_count") or 0))
    trend_code = chosen.get("trend_season_code")
    trend_label = f"Comparable Season {trend_code} change" if trend_code else "Comparable-season change"
    detail_cols[1].metric(trend_label, f"{trend_change:+.1f}%" if trend_change is not None else "Not enough periods")
    sources = chosen.get("sources") or []
    trend_sources = chosen.get("trend_sources") or sources
    evidence_seasons = chosen.get("seasons") or ([selected_season] if selected_season != "All available seasons" else [])
    record_count = int(chosen.get("observation_count") or 0)
    st.caption(
        f"Historical district evidence · {record_count} district-season records"
        if record_count else "Historical district evidence"
    )
    with st.expander("Evidence sources and coverage"):
        st.markdown("**Yield comparison sources**")
        st.write(" · ".join(_friendly_source_name(source) for source in sources) or "Source details unavailable")
        if trend_change is not None:
            st.markdown("**Comparable-season trend sources**")
            st.write(" · ".join(_friendly_source_name(source) for source in trend_sources) or "Source details unavailable")
        st.markdown("**Periods included**")
        st.write(", ".join(evidence_seasons) or "Period details unavailable")
        st.caption("District survey evidence is historical context; it does not describe every farm or establish a cause.")
    if int(chosen.get("observation_count") or 0) < 3:
        st.warning("Few records support this comparison. Treat the district position as provisional.")

    with st.expander("View all districts and source coverage"):
        import pandas as pd
        frame = pd.DataFrame(rows)
        frame["sources"] = frame["sources"].apply(
            lambda value: ", ".join(_friendly_source_name(source) for source in value)
            if isinstance(value, list) else _friendly_source_name(value)
        )
        frame["seasons"] = frame["seasons"].apply(lambda value: ", ".join(value) if isinstance(value, list) else value)
        frame = frame.rename(columns={"rank": "Rank", "district": "District", "yield_kg_ha": "Yield (kg/ha)",
                                      "observation_count": "District-season records", "seasons": "Seasons", "sources": "Source"})
        st.dataframe(frame[["Rank", "District", "Yield (kg/ha)", "District-season records", "Seasons", "Source"]],
                     hide_index=True, use_container_width=True)
        trend_history = chosen.get("trend_history") or []
        if len(trend_history) >= 2:
            history_frame = pd.DataFrame(trend_history).set_index("season")[["yield_kg_ha"]]
            history_frame = history_frame.rename(columns={"yield_kg_ha": "Yield (kg/ha)"})
            st.caption(f"{district}: comparable Season {trend_code or ''} records")
            st.line_chart(history_frame, height=200)

    st.markdown("**Recommended next step**")
    trend_history = chosen.get("trend_history") or []
    trend_period = (f"from {trend_history[0]['season']} to {trend_history[-1]['season']}"
                    if len(trend_history) >= 2 else "")
    trend_evidence = (f" Comparable Season {trend_code} yield changed {trend_change:+.1f}% {trend_period}."
                      if trend_change is not None else " Comparable-season trend is unavailable.")
    if difference is not None and difference < 0 and trend_change is not None and trend_change < 0:
        st.warning(f"The selected district is {abs(difference):,.0f} kg/ha below the crop reference.{trend_evidence} Verify plot outcomes, the season, and local conditions with an extension worker before selecting an intervention.")
    elif difference is not None and difference < 0:
        st.warning(f"The selected district is {abs(difference):,.0f} kg/ha below the crop reference.{trend_evidence} Compare current plot outcomes with the survey period before choosing an intervention.")
    elif trend_change is not None and trend_change < 0:
        st.info(f"The selected district is at or above the crop reference, but comparable-season yield has declined.{trend_evidence} Check the latest field results and monitor the next comparable season.")
    elif difference is not None:
        status = (f"Comparable-season yield changed {trend_change:+.1f}% {trend_period}."
                  if trend_change is not None else "Comparable-season trend is unavailable.")
        st.success(f"The selected district is at or above the crop reference. {status} Keep monitoring; this does not establish current farm performance.")
    else:
        st.info("A crop reference is unavailable. Collect local field evidence before drawing a comparison.")
    district_zones = [zone for zone in api_client.get_zones()
                      if zone.get("id") and str(zone.get("district") or "").casefold() == district.casefold()]
    selected_zone = None
    if district_zones:
        def zone_label(zone):
            locality = zone.get("name") or zone.get("sector") or zone.get("cell")
            suffix = str(zone["id"])[-6:]
            return f"{locality} · {suffix}" if locality else f"Saved zone · {suffix}"

        selected_zone_label = st.selectbox(
            "Follow-up zone", [zone_label(zone) for zone in district_zones],
            key=f"decision_plan_zone_{crop}_{selected_season}_{district}",
        )
        zone = next(item for item in district_zones if zone_label(item) == selected_zone_label)
        selected_zone = zone
        action_cols = st.columns(2)
        with action_cols[0]:
            explain_clicked = st.button(
                "Ask AI to explain this evidence",
                key=f"decision_ask_ai_{crop}_{selected_season}_{district}",
            )
        with action_cols[1]:
            if st.button("Continue to Planning", key=f"decision_open_plan_{crop}_{selected_season}_{district}", type="primary"):
                st.session_state["planning_zone_id"] = str(zone["id"])
                reference_text = f"Rwanda reference {float(reference):,.1f} kg/ha" if reference is not None else "Rwanda reference unavailable"
                difference_text = (
                    f"{abs(difference):,.1f} kg/ha {'below' if difference < 0 else 'above'} reference"
                    if difference is not None else "difference unavailable"
                )
                trend_text = (
                    f"comparable Season {trend_code} changed {trend_change:+.1f}% ({trend_period})"
                    if trend_change is not None else "comparable-season trend unavailable"
                )
                assessment = (
                    f"{district} {crop}: {district_yield:,.1f} kg/ha; {reference_text}; {difference_text}; "
                    f"rank {chosen['rank']} of {len(rows)} districts; {record_count} district-season records; {trend_text}."
                )
                st.session_state["plan_decision_context"] = {
                    "zone_id": str(zone["id"]), "district": district, "crop": crop,
                    "season": None if selected_season == "All available seasons" else selected_season,
                    "assessment": assessment,
                    "basis": sources,
                }
                st.session_state["plan_title"] = f"{crop} · {district} · evidence follow-up"
                st.switch_page("pages/8_Planning.py")
    else:
        st.warning("No saved zone is available for an AI explanation or Planning handoff. You can still review an evidence-only explanation below.")
        explain_clicked = st.button(
            "Ask AI to explain this evidence",
            key=f"decision_ask_ai_{crop}_{selected_season}_{district}",
        )

    explanation_key = f"decision_ai_result_{crop}_{selected_season}_{district}"
    if explain_clicked:
        answer = None
        sources_for_answer = []
        answer_kind = "record_grounded"
        fallback_note = "No saved zone is available to request an AI answer. This summary is assembled directly from the selected NISR evidence."
        if selected_zone:
            response = api_client.chat(
                "Explain this decision clearly and tell me what to check next.",
                zone_id=str(selected_zone["id"]),
                crop=crop,
                season=None if selected_season == "All available seasons" else selected_season,
            )
            if response:
                answer = response.get("answer")
                sources_for_answer = response.get("evidence_sources") or []
                answer_kind = response.get("answer_type") or "insufficient_evidence"
        if not answer:
            if selected_zone:
                fallback_note = "The AI service did not return an answer. This summary is assembled directly from the selected NISR evidence."
            answer = _decision_evidence_explanation(
                district=district, crop=crop, season=selected_season,
                yield_kg_ha=district_yield, reference_kg_ha=reference,
                difference_kg_ha=difference, rank=chosen.get("rank"),
                district_count=len(rows), record_count=record_count,
                trend_change_pct=trend_change, trend_code=trend_code,
                trend_period=trend_period,
                sources=sources,
            )
            answer_kind = "evidence_summary"
        st.session_state[explanation_key] = {
            "answer": answer,
            "sources": sources_for_answer,
            "kind": answer_kind,
            "fallback_note": fallback_note,
        }

    explanation = st.session_state.get(explanation_key)
    if explanation:
        with st.container(border=True):
            st.markdown("### Evidence explanation")
            if explanation.get("kind") == "evidence_summary":
                st.caption(explanation.get("fallback_note"))
            answer = explanation.get("answer") or "No explanation is available."
            st.markdown(format_assistant_answer(answer))
            answer_sources = explanation.get("sources") or []
            if answer_sources and not all(source.casefold() in answer.casefold() for source in answer_sources):
                st.caption("Verified sources: " + " · ".join(_friendly_source_name(source) for source in answer_sources))
            elif explanation.get("kind") == "insufficient_evidence" and not has_source_citation(answer):
                st.caption("No verified source was available for the AI explanation.")


def _friendly_source_name(source: str) -> str:
    """Avoid showing internal release labels while retaining useful provenance."""
    label = str(source or "").strip()
    normalized = label.casefold()
    if "database" in normalized or "release" in normalized:
        return "NISR database records"
    if "sas" in normalized or "historical" in normalized:
        return "Official NISR historical tables"
    return label or "Source details unavailable"


def _decision_evidence_explanation(
    *, district: str, crop: str, season: str, yield_kg_ha: float,
    reference_kg_ha: float | None, difference_kg_ha: float | None,
    rank: int | None, district_count: int, record_count: int,
    trend_change_pct: float | None, trend_code: str | None,
    trend_period: str, sources: list[str],
) -> str:
    """Provide a transparent evidence-only explanation if the AI API is unavailable."""
    period_label = "all available seasons" if season == "All available seasons" else season
    reference_text = (
        f"The Rwanda crop reference is {reference_kg_ha:,.1f} kg/ha; the district is "
        f"{abs(difference_kg_ha):,.1f} kg/ha {'below' if difference_kg_ha < 0 else 'above'} it."
        if reference_kg_ha is not None and difference_kg_ha is not None
        else "A Rwanda crop reference is unavailable for this comparison."
    )
    rank_text = (
        f"The district ranks {rank} of {district_count} districts with records, "
        f"using {record_count} district-season records."
        if rank is not None else f"The comparison uses {record_count} district-season records."
    )
    trend_text = (
        f"Comparable Season {trend_code or ''} yield changed {trend_change_pct:+.1f}% {trend_period}."
        if trend_change_pct is not None else "A comparable-season trend is unavailable."
    )
    source_text = ", ".join(_friendly_source_name(source) for source in sources) or "Source details unavailable"
    return (
        f"### What the records show\n\n{district}'s recorded {crop} yield for {period_label} is "
        f"{yield_kg_ha:,.1f} kg/ha. {reference_text} {rank_text} {trend_text}\n\n"
        "### What it means\n\nThis is a district-level historical comparison. It does not describe every farm or establish why yield changed.\n\n"
        "### What to check next\n\nConfirm the crop and season with local records, compare recent plot harvests, and verify current field conditions with an extension worker before changing a plan.\n\n"
        f"### Evidence limits\n\nHistorical district data is not a farm forecast or proof of cause.\n\n### Evidence\n\n{source_text}."
    )
