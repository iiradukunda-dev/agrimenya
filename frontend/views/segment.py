"""District level agricultural segmentation from saved yield observations."""
import logging
from math import ceil

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from components.errors import render_error_page
from components.icons import render_icon_title
from components.maps import YIELD_SEGMENT_COLORS, render_yield_segmentation_map
from utils import api_client
from utils.i18n import t

logger = logging.getLogger(__name__)

MEASURES = {
    "Yield (kg/ha)": "yield_actual",
    "Production (MT)": "production_mt",
    "Cultivated area (ha)": "area_cultivated",
}
UNASSESSED_LABELS = {"", "none", "nan", "null"}


def _district_name(row: dict) -> str:
    related_zone = row.get("zones") or {}
    if isinstance(related_zone, list):
        related_zone = related_zone[0] if related_zone else {}
    return str(row.get("district") or related_zone.get("district") or "").strip()


def _build_district_segments(metrics: pd.DataFrame, measure: str) -> pd.DataFrame:
    """Aggregate observations by district; use cultivated-area weighting for yield."""
    value_column = MEASURES[measure]
    output = []
    for district, group in metrics.groupby("District", dropna=True):
        group = group.copy()
        values = pd.to_numeric(group[value_column], errors="coerce")
        valid = values.notna()
        if not valid.any():
            continue

        if value_column == "yield_actual":
            areas = pd.to_numeric(group.loc[valid, "area_cultivated"], errors="coerce")
            usable_weights = areas.notna() & (areas > 0)
            if usable_weights.any():
                value = float((values.loc[valid][usable_weights] * areas.loc[usable_weights]).sum() / areas.loc[usable_weights].sum())
            else:
                value = float(values.loc[valid].mean())
        else:
            value = float(values.loc[valid].sum())

        output.append({
            "district": str(district),
            "value": value,
            "record_count": int(valid.sum()),
            "area_ha": float(pd.to_numeric(group["area_cultivated"], errors="coerce").sum(min_count=1))
            if pd.to_numeric(group["area_cultivated"], errors="coerce").notna().any() else None,
            "production_mt": float(pd.to_numeric(group["production_mt"], errors="coerce").sum(min_count=1))
            if pd.to_numeric(group["production_mt"], errors="coerce").notna().any() else None,
        })

    result = pd.DataFrame(output)
    if result.empty:
        return result

    lower, upper = result["value"].quantile([0.25, 0.75]).tolist()

    def segment(value: float) -> str:
        if result["value"].nunique() < 2:
            return "Middle observed range"
        if value < lower:
            return "Lower observed range"
        if value > upper:
            return "Upper observed range"
        return "Middle observed range"

    result["segment"] = result["value"].map(segment)
    result["value_display"] = result["value"].map(lambda value: f"{value:,.1f}")
    return result.sort_values("value", ascending=True).reset_index(drop=True)


def _normalize_observations(rows: list[dict]) -> pd.DataFrame:
    normalized = []
    for row in rows:
        district = _district_name(row)
        crop = str(row.get("crop") or "").strip()
        season = str(row.get("season") or "").strip()
        if not district or not crop or not season:
            continue
        normalized.append({
            **row,
            "District": district,
            "Crop": crop,
            "Season": season,
            "yield_actual": row.get("yield_actual"),
            "production_mt": row.get("production_mt"),
            "area_cultivated": row.get("area_cultivated"),
        })
    frame = pd.DataFrame(normalized)
    for column in ("yield_actual", "production_mt", "area_cultivated"):
        if column in frame:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def _sort_seasons(seasons: list[str]) -> list[str]:
    def season_order(value: str) -> tuple[int, int, str]:
        pieces = value.split()
        year = next((int(piece) for piece in pieces if piece.isdigit()), 0)
        season = next((ord(piece[-1].upper()) - ord("A") for piece in pieces if piece.casefold().startswith("season") and len(piece) > 6), 0)
        return year, season, value.casefold()
    return sorted(seasons, key=season_order, reverse=True)


def _render_observation_register(crop: str, season: str, districts: list[str]) -> None:
    st.subheader("Yield observation register")

    def reset_filters() -> None:
        st.session_state["seg_register_district"] = "All districts"
        st.session_state["seg_register_crop"] = "All crops"
        st.session_state["seg_register_search"] = ""
        st.session_state["seg_register_page"] = 0

    controls = st.columns([1.2, 1.2, 0.9, 2.2, 1])
    if st.session_state.get("seg_register_district") not in ["All districts", *districts]:
        st.session_state.pop("seg_register_district", None)
    if st.session_state.get("seg_register_crop") not in ["All crops", crop]:
        st.session_state.pop("seg_register_crop", None)
    with controls[0]:
        selected_district = st.selectbox("District", ["All districts", *districts], key="seg_register_district")
    with controls[1]:
        selected_crop = st.selectbox("Crop", ["All crops", crop], index=1, key="seg_register_crop")
    with controls[2]:
        selected_size = st.selectbox("Rows", [25, 50, 100], key="seg_register_size")
    with controls[3]:
        search = st.text_input("Search crop or season", key="seg_register_search", placeholder="Search records")
    with controls[4]:
        st.write("")
        st.write("")
        st.button("Reset filters", key="seg_register_reset", on_click=reset_filters)

    district_arg = None if selected_district == "All districts" else selected_district
    crop_arg = None if selected_crop == "All crops" else selected_crop
    signature = (selected_district, selected_crop, season, search.strip(), selected_size)
    if st.session_state.get("seg_register_signature") != signature:
        st.session_state["seg_register_signature"] = signature
        st.session_state["seg_register_page"] = 0
    page_index = int(st.session_state.get("seg_register_page", 0))
    page = api_client.get_agri_metrics_page(
        district=district_arg,
        crop=crop_arg,
        season=season,
        search=search.strip() or None,
        limit=selected_size,
        offset=page_index * selected_size,
    )
    items = _normalize_observations(page.get("items") or [])
    total = int(page.get("total", 0) or 0)
    page_count = max(1, ceil(total / selected_size))
    if page_index >= page_count:
        page_index = page_count - 1
        st.session_state["seg_register_page"] = page_index
        st.rerun()

    if items.empty:
        st.info("No yield records match these filters.")
        return

    display = items[["District", "Crop", "Season", "yield_actual", "production_mt", "area_cultivated"]].rename(columns={
        "District": "District", "Crop": "Crop", "Season": "Season",
        "yield_actual": "Observed yield (kg/ha)",
        "production_mt": "Observed production (MT)",
        "area_cultivated": "Cultivated area (ha)",
    })
    st.caption(f"Showing {page_index * selected_size + 1}–{min((page_index + 1) * selected_size, total)} of {total:,} observations")
    st.dataframe(display, width="stretch", hide_index=True)
    if page_count > 1:
        pager = st.columns([1, 1, 8])
        with pager[0]:
            if st.button("Previous", key="seg_register_previous", disabled=page_index <= 0):
                st.session_state["seg_register_page"] = page_index - 1
                st.rerun()
        with pager[1]:
            if st.button("Next", key="seg_register_next", disabled=page_index >= page_count - 1):
                st.session_state["seg_register_page"] = page_index + 1
                st.rerun()
        with pager[2]:
            st.caption(f"Page {page_index + 1} of {page_count}")


def render_segment() -> None:
    """Explore district yield segments from observed agricultural records."""
    try:
        render_icon_title(
            "assets/map.svg",
            t("seg.header"),
            t("seg.subtitle"),
        )

        observations = _normalize_observations(api_client.get_agri_metrics())
        if observations.empty:
            st.info("No yield observations are available from the data service.")
            return

        crop_options = sorted(observations["Crop"].dropna().unique(), key=str.casefold)
        season_options = _sort_seasons(observations["Season"].dropna().unique().tolist())
        district_options = sorted(observations["District"].dropna().unique(), key=str.casefold)
        if not crop_options or not season_options:
            st.info("The yield register has no crop and season combinations to compare.")
            return

        for key, options, default in (
            ("segmentation_crop", crop_options, crop_options[0]),
            ("segmentation_season", season_options, season_options[0]),
            ("segmentation_measure", list(MEASURES), list(MEASURES)[0]),
            ("segmentation_district_focus", ["All districts", *district_options], "All districts"),
        ):
            if st.session_state.get(key) not in options:
                st.session_state[key] = default

        with st.container(border=True):
            st.subheader("Segmentation filters")
            filters = st.columns([1.25, 1.25, 1.35, 1.3])
            with filters[0]:
                crop = st.selectbox("Crop", crop_options, key="segmentation_crop")
            with filters[1]:
                season = st.selectbox("Season", season_options, key="segmentation_season")
            with filters[2]:
                measure = st.selectbox("Segment by", list(MEASURES), key="segmentation_measure")
            with filters[3]:
                district_focus = st.selectbox("Inspect district", ["All districts", *district_options], key="segmentation_district_focus")

        selected = observations[(observations["Crop"] == crop) & (observations["Season"] == season)].copy()
        district_segments = _build_district_segments(selected, measure)
        if district_segments.empty:
            st.info("No valid observations exist for this crop and season.")
            return

        value_column = MEASURES[measure]
        record_count = int(pd.to_numeric(selected[value_column], errors="coerce").notna().sum())
        median_value = float(district_segments["value"].median())
        display_unit = {"Yield (kg/ha)": "kg/ha", "Production (MT)": "MT", "Cultivated area (ha)": "ha"}[measure]
        summary = st.columns(3)
        summary[0].metric("Districts with observations", f"{len(district_segments)} / 30")
        summary[1].metric(f"Median {measure.lower()}", f"{median_value:,.1f} {display_unit}")
        summary[2].metric("Matching observations", f"{record_count:,}")

        with st.expander("How the segments are calculated", expanded=False):
            st.write(
                "The selected measure is aggregated by district for this crop and season. Yield is weighted by "
                "cultivated area where area values are present; otherwise the district mean is used. Districts are "
                "then grouped into lower, middle, and upper quartiles of the observed values. These are relative "
                "segments of this dataset, not farm-level ratings, risk scores, or causal explanations."
            )

        st.subheader(f"{crop} · {season} district map")
        render_yield_segmentation_map(district_segments.to_dict("records"), metric_label=f"{measure} · {display_unit}")

        chart, detail = st.columns([1.5, 1])
        with chart:
            st.subheader("District comparison")
            plot = district_segments.sort_values("value", ascending=True)
            fig = px.bar(
                plot,
                x="value",
                y="district",
                orientation="h",
                color="segment",
                color_discrete_map=YIELD_SEGMENT_COLORS,
                hover_data={"record_count": True, "segment": True, "value": ":,.1f"},
                labels={"value": f"{measure} · {display_unit}", "district": "District", "segment": "Relative segment", "record_count": "Observations"},
            )
            fig.update_layout(
                font=dict(family="Inter, sans-serif", color="#374151"),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=15, t=15, b=30),
                legend_title_text="Observed range",
            )
            fig.update_xaxes(showgrid=True, gridcolor="rgba(209,213,219,.35)")
            fig.update_yaxes(title=None, categoryorder="array", categoryarray=plot["district"].tolist())
            st.plotly_chart(fig, width="stretch")

        with detail:
            st.subheader("District summary")
            if district_focus == "All districts":
                st.caption("Select a district above to inspect its recorded values.")
            else:
                selected_segment = district_segments[district_segments["district"] == district_focus]
                if selected_segment.empty:
                    st.info(f"No {crop} observations are recorded for {district_focus} in {season}.")
                else:
                    district_row = selected_segment.iloc[0]
                    st.metric(measure, f"{district_row['value']:,.1f} {display_unit}")
                    st.caption(f"Relative segment: {district_row['segment']} · {int(district_row['record_count'])} observation(s)")
                    if pd.notna(district_row["area_ha"]):
                        st.metric("Cultivated area recorded", f"{district_row['area_ha']:,.1f} ha")
                    if pd.notna(district_row["production_mt"]):
                        st.metric("Production recorded", f"{district_row['production_mt']:,.1f} MT")

        st.divider()
        _render_observation_register(crop, season, district_options)
        st.caption(
            "The segmentation view uses saved yield observations. The project’s seeded observation file matches the "
            "Rwanda SAS 2026 extraction; per-row source metadata is not stored in the database. District polygons "
            "are the NISR 2022 administrative boundary snapshot, not field boundaries."
        )

    except requests.exceptions.RequestException as exc:
        logger.error("Network error in Segmentation: %s", exc)
        render_error_page("network", str(exc))
    except Exception as exc:
        logger.error("Unexpected error in Segmentation: %s", exc, exc_info=True)
        render_error_page("system", str(exc))
