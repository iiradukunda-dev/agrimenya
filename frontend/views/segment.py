"""Descriptive district comparisons for observed agricultural metrics."""
from __future__ import annotations

import html
import logging

import pandas as pd
import requests
import streamlit as st

try:
    import folium
    from streamlit_folium import st_folium
except ImportError:  # Keep the table usable if optional map packages are missing.
    folium = None
    st_folium = None

from components.errors import error_boundary
from components.charts import render_segment_distribution_chart, render_segment_summary_chart
from components.maps import add_map_layer_control, create_rwanda_map
from utils import api_client
from utils.i18n import t
from views.data_insights import normalize_agri_metrics

logger = logging.getLogger(__name__)

DISTRICT_BOUNDARIES_URL = (
    "https://gis-server.statistics.gov.rw/server/rest/services/Hosted/"
    "District_Boundary_2022/FeatureServer/0/query"
)
CELL_BOUNDARIES_URL = (
    "https://gis-server.statistics.gov.rw/server/rest/services/Hosted/"
    "Cell_Boundary_2022__Open_Data_/FeatureServer/2/query"
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
def _load_administrative_locations() -> pd.DataFrame:
    """Load NISR's complete 2022 district-sector-cell directory without geometries."""
    locations = []
    offset = 0
    for _ in range(10):
        response = requests.get(
            CELL_BOUNDARIES_URL,
            params={
                "where": "1=1",
                "outFields": "district,sector,cell",
                "returnGeometry": "false",
                "orderByFields": "objectid",
                "resultOffset": offset,
                "resultRecordCount": 2000,
                "f": "json",
            },
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or payload.get("error"):
            raise ValueError("NISR returned an invalid administrative-location response")
        features = payload.get("features") or []
        locations.extend(
            feature.get("attributes") or {}
            for feature in features
            if isinstance(feature, dict)
        )
        if not payload.get("exceededTransferLimit") or not features:
            break
        offset += len(features)
    else:
        raise ValueError("NISR administrative-location response exceeded the pagination limit")

    frame = pd.DataFrame(locations).rename(columns={
        "district": "District",
        "sector": "Sector",
        "cell": "Cell",
    })
    required = ["District", "Sector", "Cell"]
    if frame.empty or not all(column in frame.columns for column in required):
        raise ValueError("NISR returned no district-sector-cell records")
    for column in required:
        frame[column] = frame[column].astype("string").str.strip()
    return frame.dropna(subset=required).drop_duplicates(required).sort_values(required).reset_index(drop=True)


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
    if folium is None or st_folium is None:
        st.info("The map is unavailable because its optional map components could not be loaded.")
        return

    map_view = create_rwanda_map(satellite_default=satellite_default)

    value_by_district = {
        _clean_value(row["District"]).casefold(): row
        for _, row in summary.iterrows()
    }

    try:
        boundaries = _load_district_boundaries()
    except (requests.RequestException, ValueError) as exc:
        logger.warning("Unable to load official district boundaries: %s", exc)
        boundaries = None

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
            features.append(enriched_feature)
        enriched_boundaries = {**boundaries, "features": features}

        def style_feature(feature: dict) -> dict:
            properties = feature.get("properties") or {}
            district = _clean_value(properties.get("district")).casefold()
            record = value_by_district.get(district)
            range_label = record["Range"] if record is not None else "No recorded value"
            return {
                "fillColor": RANGE_COLORS.get(range_label, RANGE_COLORS["No recorded value"]),
                "color": "#ffffff",
                "weight": 1.6,
                "fillOpacity": 0.72 if record is not None else 0.22,
            }

        folium.GeoJson(
            enriched_boundaries,
            name="District comparison",
            style_function=style_feature,
            highlight_function=lambda _: {"weight": 3, "color": "#0f172a", "fillOpacity": 0.86},
            tooltip=folium.GeoJsonTooltip(
                fields=["district", "province", "metric_value", "observed_range", "record_count"],
                aliases=["District", "Province", metric_label, "Observed range", "Records"],
                sticky=True,
            ),
            popup=folium.GeoJsonPopup(
                fields=["district", "metric_value", "observed_range", "record_count"],
                aliases=["District", metric_label, "Observed range", "Records"],
                labels=True,
            ),
        ).add_to(map_view)
    else:
        st.warning(
            "District boundary service is unavailable, so the map is showing observation locations where coordinates exist."
        )
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
                    folium.CircleMarker(
                        location=[float(coords["Lat"]), float(coords["Lon"])],
                        radius=10,
                        color=RANGE_COLORS.get(range_label, RANGE_COLORS["Not comparable"]),
                        fill=True,
                        fill_color=RANGE_COLORS.get(range_label, RANGE_COLORS["Not comparable"]),
                        fill_opacity=0.8,
                        tooltip=(
                            f"{html.escape(str(record['District']))}: "
                            f"{record['Value']:,.1f} {html.escape(unit)} · {html.escape(range_label)}"
                        ),
                    ).add_to(map_view)
        except Exception:
            logger.exception("Unable to render fallback district observation markers")

    add_map_layer_control(map_view)
    st_folium(map_view, key=key, height=540, width="stretch", returned_objects=[])

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
    st.markdown(
        """
        <style>
        .segmentation-hero {
            margin: 0.4rem 0 1.25rem;
            padding: clamp(1.25rem, 3vw, 2rem);
            border: 1px solid rgba(2, 132, 199, 0.16);
            border-radius: 20px;
            background: linear-gradient(118deg, #eff8ff 0%, #ffffff 58%, #effaf4 100%);
            box-shadow: 0 10px 28px rgba(15, 23, 42, 0.055);
        }
        .segmentation-hero__top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 0.65rem;
            margin-bottom: 0.8rem;
        }
        .segmentation-hero__eyebrow {
            color: #0b7657;
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.11em;
            text-transform: uppercase;
        }
        .segmentation-hero__badge {
            padding: 0.3rem 0.65rem;
            border: 1px solid rgba(11, 118, 87, 0.18);
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.78);
            color: #0b7657;
            font-size: 0.72rem;
            font-weight: 700;
        }
        .segmentation-hero h1 {
            margin: 0;
            color: #102a36;
            font-size: clamp(1.7rem, 3vw, 2.35rem);
            font-weight: 800;
            letter-spacing: -0.04em;
            line-height: 1.15;
        }
        .segmentation-hero__description {
            max-width: 760px;
            margin: 0.65rem 0 0;
            color: #47616b;
            font-size: 1rem;
            line-height: 1.65;
        }
        .segmentation-hero__note {
            margin-top: 1rem;
            padding-top: 0.8rem;
            border-top: 1px solid rgba(15, 54, 64, 0.1);
            color: #536b72;
            font-size: 0.84rem;
        }
        </style>
        <section class="segmentation-hero">
            <div class="segmentation-hero__top">
                <span class="segmentation-hero__eyebrow">Rwanda · District insights</span>
                <span class="segmentation-hero__badge">Observed data</span>
            </div>
            <h1>District comparison</h1>
            <p class="segmentation-hero__description">
                Explore recorded yield, production, and cultivated area across crops, seasons, and districts.
                Yield is area-weighted when cultivated-area data is available.
            </p>
            <div class="segmentation-hero__note">
                Descriptive summaries only — not forecasts or individual-farm rankings.
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    try:
        official_rows = api_client.get_official_yields()
    except Exception:
        logger.exception("Unable to load bundled NISR observations for segmentation")
        official_rows = []
    official_data_available = bool(official_rows)
    if official_data_available:
        records = normalize_agri_metrics(official_rows)
        st.caption("NISR district-level observations · all seasons available in the bundled 2022–2026 evidence.")
    else:
        try:
            records = normalize_agri_metrics(api_client.get_agri_metrics())
        except Exception:
            logger.exception("Unable to load agricultural observations for segmentation")
            records = normalize_agri_metrics([])
            st.error("Agricultural observations could not be loaded. Please check the data connection and try again.")
        if not records.empty:
            st.warning("The historical NISR dataset is unavailable. Showing only operational records returned by the backend.")

    try:
        locations = _load_administrative_locations()
    except (requests.RequestException, ValueError):
        logger.exception("Unable to load the NISR 2022 administrative-location directory")
        locations = pd.DataFrame(columns=["District", "Sector", "Cell"])
        st.warning(
            "The complete NISR location directory is temporarily unavailable. "
            "Location choices are limited to places present in the available records."
        )
    if locations.empty and not records.empty:
        locations = records[["District", "Sector", "Cell"]].dropna(how="all").drop_duplicates()
    try:
        zone_locations = api_client.get_zones() or []
    except Exception:
        logger.exception("Unable to load registered zone locations")
        zone_locations = []
    if zone_locations:
        registered_locations = pd.DataFrame([{
            "District": zone.get("district"),
            "Sector": zone.get("sector"),
            "Cell": zone.get("cell"),
        } for zone in zone_locations if isinstance(zone, dict)])
        if not registered_locations.empty:
            locations = pd.concat([locations, registered_locations], ignore_index=True)
            locations = locations.dropna(subset=["District"], how="any").drop_duplicates()

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
    if not crops:
        st.info("No crop labels are available in the current observations.")
        return

    with st.container(border=True):
        st.subheader("Choose what to compare")
        filter_row_one = st.columns([1.15, 1.15, 1.1])
        with filter_row_one[0]:
            selected_metric_label = st.selectbox("Measure", [item[0] for item in available_metrics], key="seg_measure")
        with filter_row_one[1]:
            selected_crop = st.selectbox("Crop", crops, key="seg_crop")

        crop_records = records[records["Crop"].astype(str).eq(selected_crop)]
        seasons = sorted(
            (value for value in crop_records["Season"].dropna().astype(str).str.strip().unique() if value),
            reverse=True,
        )
        if not seasons:
            st.info(f"No observed seasons are available for {selected_crop}.")
            return
        with filter_row_one[2]:
            selected_season = st.selectbox("Season", seasons, key="seg_season")

        crop_season_records = crop_records[crop_records["Season"].astype(str).eq(selected_season)]
        if locations.empty or "District" not in locations.columns:
            districts = sorted(
                value for value in crop_season_records["District"].dropna().astype(str).unique() if value
            )
        else:
            districts = sorted(
                value for value in locations["District"].dropna().astype(str).str.strip().unique() if value
            )
        filter_row_two = st.columns(3)
        with filter_row_two[0]:
            selected_district = st.selectbox("District", [ALL_DISTRICTS, *districts], key="seg_district")

        district_locations = locations
        if selected_district != ALL_DISTRICTS and "District" in district_locations.columns:
            district_locations = district_locations[
                district_locations["District"].astype(str).str.casefold().eq(selected_district.casefold())
            ]
        sector_records = district_locations[["District", "Sector"]].dropna().drop_duplicates()
        sector_labels = {
            (str(row["Sector"]) if selected_district != ALL_DISTRICTS
             else f"{row['District']} · {row['Sector']}"): (str(row["District"]), str(row["Sector"]))
            for _, row in sector_records.iterrows()
        }
        with filter_row_two[1]:
            selected_sector = st.selectbox("Sector", [ALL_SECTORS, *sector_labels], key="seg_sector")

        selected_sector_location = sector_labels.get(selected_sector)
        cell_records = district_locations[["District", "Sector", "Cell"]].dropna().drop_duplicates()
        if selected_sector_location:
            cell_records = cell_records[
                cell_records["District"].astype(str).str.casefold().eq(selected_sector_location[0].casefold())
                & cell_records["Sector"].astype(str).str.casefold().eq(selected_sector_location[1].casefold())
            ]
        cell_labels = {
            (str(row["Cell"]) if selected_district != ALL_DISTRICTS and selected_sector_location
             else f"{row['District']} · {row['Sector']} · {row['Cell']}"):
                (str(row["District"]), str(row["Sector"]), str(row["Cell"]))
            for _, row in cell_records.iterrows()
        }
        with filter_row_two[2]:
            selected_cell = st.selectbox("Cell", [ALL_CELLS, *cell_labels], key="seg_cell")

    selected_cell_location = cell_labels.get(selected_cell)
    effective_district = (
        selected_district if selected_district != ALL_DISTRICTS
        else selected_cell_location[0] if selected_cell_location
        else selected_sector_location[0] if selected_sector_location
        else None
    )
    filtered = crop_season_records.copy()
    if effective_district:
        filtered = filtered[
            filtered["District"].astype(str).str.casefold().eq(effective_district.casefold())
        ]
    if not official_data_available and selected_sector_location and "Sector" in filtered.columns:
        filtered = filtered[
            filtered["Sector"].astype(str).str.casefold().eq(selected_sector_location[1].casefold())
        ]
    if not official_data_available and selected_cell_location and "Cell" in filtered.columns:
        filtered = filtered[
            filtered["Cell"].astype(str).str.casefold().eq(selected_cell_location[2].casefold())
        ]

    if official_data_available and (selected_sector_location or selected_cell_location):
        st.info(
            "The location directory includes all NISR 2022 sectors and cells. "
            "The available crop observations are district-level, so the results below show the selected location's district "
            "and do not estimate yield or production for an individual sector or cell."
        )

    metric_column, metric_unit = METRIC_OPTIONS[selected_metric_label]
    summary = _summarize_districts(filtered, metric_column)
    observed_record_count = int(
        pd.to_numeric(filtered[metric_column], errors="coerce")
        .replace([float("inf"), float("-inf")], float("nan"))
        .notna()
        .sum()
    )

    coverage_columns = st.columns(3, gap="medium")
    coverage_metrics = (
        ("Matching records", f"{len(filtered):,}", "Records matching the current crop, season, and location filters."),
        ("Records with this measure", f"{observed_record_count:,}", f"Matching records with a recorded {selected_metric_label.casefold()} value."),
        ("Districts represented", f"{len(summary):,}", "Districts with at least one usable value for the selected measure."),
    )
    for column, (label, value, help_text) in zip(coverage_columns, coverage_metrics):
        with column:
            with st.container(border=True):
                st.metric(label, value, help=help_text)

    map_col, summary_col = st.columns([1.55, 1], gap="large")
    with map_col:
        st.subheader("Observed values by district")
        st.caption("Switch between street and satellite imagery using the map layers control at the upper right.")
        _render_comparison_map(
            summary,
            selected_metric_label,
            metric_unit,
            key="segmentation_observation_map",
            satellite_default=False,
        )

    with summary_col:
        st.subheader(f"{selected_metric_label} summary")
        if summary.empty:
            st.info("No matching observations include a value for this measure.")
        else:
            finite_values = summary["Value"].replace([float("inf"), float("-inf")], pd.NA).dropna()
            if not finite_values.empty:
                top = summary.loc[summary["Value"].idxmax()]
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
