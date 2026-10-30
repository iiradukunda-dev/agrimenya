"""Descriptive district comparisons for observed agricultural metrics."""
from __future__ import annotations

import html
import logging

import pandas as pd
import requests
import streamlit as st

from components.errors import error_boundary
from components.icons import render_icon_title
from components.charts import render_segment_distribution_chart, render_segment_summary_chart
from components.maps import (
    RSA_ORTHOMOSAIC_NOTE,
    render_google_map,
)
from utils import api_client
from utils.i18n import t
from views.data_insights import normalize_agri_metrics

logger = logging.getLogger(__name__)

DISTRICT_BOUNDARIES_URL = (
    "https://gis-server.statistics.gov.rw/server/rest/services/Hosted/"
    "District_Boundary_2022/FeatureServer/0/query"
)
METRIC_OPTIONS = {
    "Yield": ("Yield (kg/ha)", "kg/ha"),
    "Production": ("Production (MT)", "MT"),
    "Cultivated area": ("Cultivated area (ha)", "ha"),
}
RANGE_COLORS = {
    "Lower observed range": "#c66c55",
    "Middle observed range": "#d4a347",
    "Upper observed range": "#458b70",
    "Not comparable": "#94a3b8",
    "No recorded value": "#d1d5db",
}
ALL_DISTRICTS = "All districts"
ALL_SECTORS = "All sectors"
ALL_CELLS = "All cells"


@st.cache_data(ttl=86400, show_spinner=False)
def _load_district_boundaries() -> dict | None:
    """Load the 2022 Rwanda district boundaries published by NISR."""
    response = requests.get(
        DISTRICT_BOUNDARIES_URL,
        params={
            "where": "1=1",
            "outFields": "district,province",
            "returnGeometry": "true",
            "outSR": "4326",
            "f": "geojson",
        },
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    return payload if isinstance(payload, dict) and payload.get("type") == "FeatureCollection" else None


def _clean_value(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def _summarize_districts(frame: pd.DataFrame, metric_column: str) -> pd.DataFrame:
    """Aggregate observed rows by district without mixing in predictions."""
    columns = ["District", "Value", "Record count", "Range"]
    if frame.empty or metric_column not in frame.columns or "District" not in frame:
        return pd.DataFrame(columns=columns)

    results = []
    for district, district_rows in frame.groupby("District", dropna=True):
        observed = district_rows[metric_column].dropna()
        if observed.empty:
            continue

        if metric_column == "Yield (kg/ha)":
            if "Cultivated area (ha)" in district_rows.columns:
                area = district_rows["Cultivated area (ha)"]
                weighted_rows = district_rows[metric_column].notna() & area.notna() & area.gt(0)
                valid_area = area[weighted_rows]
                if not valid_area.empty and valid_area.sum() > 0:
                    value = float(
                        (district_rows.loc[weighted_rows, metric_column] * valid_area).sum()
                        / valid_area.sum()
                    )
                else:
                    value = float(observed.mean())
            else:
                value = float(observed.mean())
        elif metric_column in {"Production (MT)", "Cultivated area (ha)"}:
            value = float(observed.sum())
        else:
            value = float(observed.mean())

        results.append({
            "District": str(district),
            "Value": value,
            "Record count": int(observed.count()),
            "Range": "Not comparable",
        })

    summary = pd.DataFrame(results, columns=columns)
    if summary.empty:
        return summary

    # Use thirds of the observed district values, recalculated for the current selection.
    if len(summary) == 1:
        summary.loc[:, "Range"] = "Not comparable"
        return summary

    lower_cut, upper_cut = summary["Value"].quantile([1 / 3, 2 / 3]).tolist()
    summary["Range"] = summary["Value"].map(
        lambda value: (
            "Lower observed range" if value <= lower_cut else
            "Middle observed range" if value <= upper_cut else
            "Upper observed range"
        )
    )
    return summary


def _render_comparison_map(
    summary: pd.DataFrame,
    metric_label: str,
    unit: str,
    *,
    key: str,
    satellite_default: bool,
) -> None:
    value_by_district = {
        _clean_value(row["District"]).casefold(): row
        for _, row in summary.iterrows()
    }

    try:
        boundaries = _load_district_boundaries()
    except (requests.RequestException, ValueError) as exc:
        logger.warning("Unable to load official district boundaries: %s", exc)
        boundaries = None

    enriched_boundaries = None
    if boundaries:
        features = []
        for feature in boundaries.get("features", []):
            enriched_feature = {**feature, "properties": dict(feature.get("properties") or {})}
            district = _clean_value(enriched_feature["properties"].get("district")).casefold()
            record = value_by_district.get(district)
            enriched_feature["properties"]["metric_value"] = (
                f"{record['Value']:,.1f} {unit}" if record is not None else "No matching observations"
            )
            enriched_feature["properties"]["observed_range"] = (
                record["Range"] if record is not None else "No recorded value"
            )
            enriched_feature["properties"]["record_count"] = (
                f"{record['Record count']:,}" if record is not None else "0"
            )
            enriched_feature["properties"]["has_observations"] = record is not None
            range_label = record["Range"] if record is not None else "No recorded value"
            enriched_feature["properties"]["style_color"] = RANGE_COLORS.get(
                range_label,
                RANGE_COLORS["No recorded value"],
            )
            features.append(enriched_feature)
        enriched_boundaries = {**boundaries, "features": features}
    else:
        st.warning(
            "District boundary service is unavailable, so the map is showing observation locations where coordinates exist."
        )
        fallback_markers = []
        try:
            map_points = api_client.get_priority_data()
            if isinstance(map_points, pd.DataFrame) and not map_points.empty:
                district_coords = map_points.dropna(subset=["Lat", "Lon"]).groupby("District")[
                    ["Lat", "Lon"]
                ].mean()
                for _, record in summary.iterrows():
                    coords = district_coords.loc[record["District"]] if record["District"] in district_coords.index else None
                    if coords is None:
                        continue
                    range_label = record["Range"]
                    district = str(record["District"])
                    fallback_markers.append({
                        "lat": float(coords["Lat"]),
                        "lng": float(coords["Lon"]),
                        "title": f"{district}: {record['Value']:,.1f} {unit}",
                        "color": RANGE_COLORS.get(range_label, RANGE_COLORS["Not comparable"]),
                        "details": [
                            {"label": "District", "value": district},
                            {"label": metric_label, "value": f"{record['Value']:,.1f} {unit}"},
                            {"label": "Observed range", "value": range_label},
                        ],
                    })
        except Exception:
            logger.exception("Unable to render fallback district observation markers")

    render_google_map(
        key=key,
        satellite_default=satellite_default,
        markers=fallback_markers if not enriched_boundaries else None,
        geojson=enriched_boundaries,
        fit_bounds=bool(enriched_boundaries),
    )

    legend_items = "".join(
        f"<span style='display:inline-flex;align-items:center;gap:6px;margin:0 14px 6px 0;'>"
        f"<i style='display:inline-block;width:12px;height:12px;border-radius:50%;background:{color};'></i>"
        f"{html.escape(label)}</span>"
        for label, color in RANGE_COLORS.items()
    )
    st.markdown(
        f"<div style='font-size:.82rem;margin-top:.35rem;'>{legend_items}</div>",
        unsafe_allow_html=True,
    )
    st.caption(
        "District boundaries: National Institute of Statistics of Rwanda (NISR), updated with 2022 census mapping. "
        "Observed-value ranges are recalculated for the current crop, season, and location filters."
    )


@error_boundary("Segmentation")
def render_segment() -> None:
    render_icon_title(
        "assets/map.svg",
        "District comparison",
        "Explore recorded agricultural outcomes across Rwanda for a selected crop and season.",
    )
    st.markdown(
        "Compare observed yield, production, or cultivated area. Districts are grouped into lower, middle, "
        "and upper ranges from the records currently in view. Yield uses an area-weighted average where "
        "cultivated-area data is available."
    )
    st.caption(
        "This is a descriptive view of recorded data. It is not a forecast and does not rank individual farmers."
    )

    try:
        records = normalize_agri_metrics(api_client.get_agri_metrics())
    except Exception:
        logger.exception("Unable to load agricultural observations for segmentation")
        records = normalize_agri_metrics([])
        st.error("Agricultural observations could not be loaded. Please check the data connection and try again.")

    available_metrics = [
        (label, column, unit)
        for label, (column, unit) in METRIC_OPTIONS.items()
        if column in records.columns and records[column].notna().any()
    ]

    if records.empty or "Crop" not in records.columns or "Season" not in records.columns:
        st.info("No agricultural observation records are available for this view yet.")
        return
    if not available_metrics:
        st.info("The available records do not contain yield, production, or cultivated-area values to compare.")
        return

    crops = sorted(value for value in records["Crop"].dropna().astype(str).str.strip().unique() if value)
    seasons = sorted(value for value in records["Season"].dropna().astype(str).str.strip().unique() if value)

    with st.container(border=True):
        st.subheader("Choose what to compare")
        filter_row_one = st.columns([1.15, 1.15, 1.1])
        with filter_row_one[0]:
            selected_metric_label = st.selectbox("Measure", [item[0] for item in available_metrics], key="seg_measure")
        with filter_row_one[1]:
            selected_crop = st.selectbox("Crop", crops, key="seg_crop")
        with filter_row_one[2]:
            selected_season = st.selectbox("Season", seasons, key="seg_season")

        crop_season_records = records[
            records["Crop"].astype(str).eq(selected_crop)
            & records["Season"].astype(str).eq(selected_season)
        ]
        districts = sorted(value for value in crop_season_records["District"].dropna().astype(str).unique() if value)
        filter_row_two = st.columns(3)
        with filter_row_two[0]:
            selected_district = st.selectbox("District", [ALL_DISTRICTS, *districts], key="seg_district")

        geography_records = crop_season_records
        if selected_district != ALL_DISTRICTS:
            geography_records = geography_records[geography_records["District"].astype(str).eq(selected_district)]

        sectors = sorted(value for value in geography_records["Sector"].dropna().astype(str).unique() if value)
        with filter_row_two[1]:
            selected_sector = st.selectbox("Sector", [ALL_SECTORS, *sectors], key="seg_sector")

        if selected_sector != ALL_SECTORS:
            geography_records = geography_records[geography_records["Sector"].astype(str).eq(selected_sector)]
        cells = sorted(value for value in geography_records["Cell"].dropna().astype(str).unique() if value)
        with filter_row_two[2]:
            selected_cell = st.selectbox("Cell", [ALL_CELLS, *cells], key="seg_cell")

    filtered = crop_season_records.copy()
    if selected_district != ALL_DISTRICTS:
        filtered = filtered[filtered["District"].astype(str).eq(selected_district)]
    if selected_sector != ALL_SECTORS:
        filtered = filtered[filtered["Sector"].astype(str).eq(selected_sector)]
    if selected_cell != ALL_CELLS:
        filtered = filtered[filtered["Cell"].astype(str).eq(selected_cell)]

    metric_column, metric_unit = METRIC_OPTIONS[selected_metric_label]
    summary = _summarize_districts(filtered, metric_column)

    map_col, summary_col = st.columns([1.55, 1], gap="large")
    with map_col:
        st.subheader("Observed values by district")
        st.caption(
            "Use the map controls to switch between road and Google satellite imagery, or toggle the RSA overlay. "
            "Zoom in to explore districts, sectors, cells, and villages. "
            f"{RSA_ORTHOMOSAIC_NOTE}"
        )
        _render_comparison_map(
            summary,
            selected_metric_label,
            metric_unit,
            key="segmentation_observation_map",
            satellite_default=True,
        )

    with summary_col:
        st.subheader(f"{selected_metric_label} summary")
        if summary.empty:
            st.info("No matching observations include a value for this measure.")
        else:
            finite_values = summary["Value"].replace([float("inf"), float("-inf")], pd.NA).dropna()
            if not finite_values.empty:
                top = summary.loc[summary["Value"].idxmax()]
                st.metric("Districts with observations", f"{len(summary):,}")
                st.metric(
                    f"Highest observed {selected_metric_label.casefold()}",
                    f"{top['Value']:,.1f} {metric_unit}",
                    help="This describes the selected records; it is not a forecast or farmer ranking.",
                )
                st.caption(f"{top['District']} has the highest observed district value in this selection.")

            render_segment_summary_chart(summary, selected_metric_label, metric_unit)

    st.divider()
    st.subheader("Explore matching observations")
    st.caption("Search within the current crop, season, district, sector, and cell selection.")
    search_term = st.text_input("Search records", key="seg_records_search", placeholder="Search a district, sector, cell, or crop")
    searchable_columns = [
        column for column in ["District", "Sector", "Cell", "Crop", "Season", "Soil type"]
        if column in filtered.columns
    ]
    visible_records = filtered
    if search_term.strip() and searchable_columns:
        query = search_term.strip().casefold()
        matches = filtered[searchable_columns].astype("string").fillna("").apply(
            lambda column: column.str.casefold().str.contains(query, regex=False)
        ).any(axis=1)
        visible_records = filtered[matches]

    st.caption(f"Showing {len(visible_records):,} of {len(filtered):,} matching records.")
    if visible_records.empty:
        st.info("No records match the current filters and search.")
    else:
        render_segment_distribution_chart(
            visible_records,
            metric_column,
            selected_metric_label,
            metric_unit,
        )
        records_for_inspection = visible_records.reset_index(drop=True)

        def _observation_label(index: int) -> str:
            record = records_for_inspection.iloc[index]
            location = " / ".join(
                str(record.get(column)).strip()
                for column in ("District", "Sector", "Cell")
                if record.get(column) is not None and not pd.isna(record.get(column)) and str(record.get(column)).strip()
            )
            value = record.get(metric_column)
            crop_value = record.get("Crop")
            value_label = f"{float(value):,.1f} {metric_unit}" if pd.notna(value) else "Value not recorded"
            crop_label = str(crop_value) if pd.notna(crop_value) else selected_crop
            return f"{location or 'Location not recorded'} · {crop_label} · {value_label}"

        selected_record_index = st.selectbox(
            "Inspect an observation",
            list(range(len(records_for_inspection))),
            format_func=_observation_label,
            key="seg_observation_select",
        )
        selected_record = records_for_inspection.iloc[selected_record_index]
        observation_metrics = [
            ("Yield (kg/ha)", "Yield", "kg/ha"),
            ("Production (MT)", "Production", "MT"),
            ("Cultivated area (ha)", "Cultivated area", "ha"),
            ("Rainfall (mm)", "Rainfall", "mm"),
        ]
        available_observation_metrics = [
            (column, label, unit)
            for column, label, unit in observation_metrics
            if column in records_for_inspection.columns
        ]
        if available_observation_metrics:
            metric_cols = st.columns(min(len(available_observation_metrics), 4))
            for metric_col, (column, label, unit) in zip(metric_cols, available_observation_metrics):
                value = pd.to_numeric(pd.Series([selected_record.get(column)]), errors="coerce").iloc[0]
                metric_col.metric(
                    label,
                    f"{value:,.1f} {unit}" if pd.notna(value) else "Not recorded",
                )
        def _location_value(column: str) -> str:
            value = selected_record.get(column)
            return str(value) if pd.notna(value) else "Not recorded"

        st.caption(
            f"District: {_location_value('District')}"
            f" · Sector: {_location_value('Sector')}"
            f" · Cell: {_location_value('Cell')}"
            f" · Soil: {_location_value('Soil type')}"
        )
