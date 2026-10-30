"""Interactive data exploration views built on persisted agricultural metrics."""
from __future__ import annotations

import html
import re

import pandas as pd
import plotly.express as px
import streamlit as st

from components.charts import get_plotly_layout


NUMERIC_COLUMNS = [
    "Yield (kg/ha)",
    "Production (MT)",
    "Cultivated area (ha)",
    "Rainfall (mm)",
    "Household size",
]
CATEGORICAL_COLUMNS = ["District", "Sector", "Cell", "Crop", "Season", "Soil type"]


def crop_key(value: object) -> str:
    """Normalize common plural labels used by the map and metrics APIs."""
    text = str(value).strip().casefold()
    if text.endswith("ies") and len(text) > 3:
        return f"{text[:-3]}y"
    if text.endswith("oes") and len(text) > 3:
        return text[:-2]
    if text.endswith("s") and not text.endswith("ss"):
        return text[:-1]
    return text


def normalize_agri_metrics(rows: list[dict] | None) -> pd.DataFrame:
    """Flatten the existing API response and coerce analytical fields safely."""
    frame = pd.DataFrame(rows or [])
    if frame.empty:
        return pd.DataFrame(columns=["Record ID", "Zone ID", *CATEGORICAL_COLUMNS, *NUMERIC_COLUMNS])

    zones = frame["zones"] if "zones" in frame.columns else pd.Series(index=frame.index, dtype=object)
    frame["District"] = zones.map(lambda item: item.get("district") if isinstance(item, dict) else None)
    frame["Sector"] = zones.map(lambda item: item.get("sector") if isinstance(item, dict) else None)
    frame["Cell"] = zones.map(lambda item: item.get("cell") if isinstance(item, dict) else None)
    frame = frame.drop(columns=["zones"], errors="ignore")
    frame = frame.rename(columns={
        "id": "Record ID",
        "zone_id": "Zone ID",
        "crop": "Crop",
        "season": "Season",
        "yield_actual": "Yield (kg/ha)",
        "production_mt": "Production (MT)",
        "area_cultivated": "Cultivated area (ha)",
        "rainfall_mm": "Rainfall (mm)",
        "soil_type": "Soil type",
        "household_size": "Household size",
        "created_at": "Recorded at",
    })
    for column in NUMERIC_COLUMNS:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
            frame[column] = frame[column].replace([float("inf"), float("-inf")], pd.NA)
    return frame


def filter_dashboard_metrics(
    frame: pd.DataFrame,
    *,
    season: str,
    all_seasons_label: str,
    crops: list[str],
    district: str,
    all_districts_label: str,
    priorities: list[str] | None = None,
) -> pd.DataFrame:
    """Apply the existing operational dashboard selections to metric records."""
    result = frame.copy()
    if result.empty:
        return result
    if season != all_seasons_label and "Season" in result:
        selected_year, selected_part, selected_text = _season_key(season)
        def season_matches(value: object) -> bool:
            year, part, text = _season_key(value)
            if selected_part:
                return part == selected_part and (not selected_year or year == selected_year)
            return text.casefold() == selected_text.casefold()
        result = result[result["Season"].map(season_matches)]
    if crops and "Crop" in result:
        crop_set = {crop_key(item) for item in crops}
        result = result[result["Crop"].map(crop_key).isin(crop_set)]
    if district != all_districts_label and "District" in result:
        result = result[result["District"].astype("string").str.casefold() == district.casefold()]
    if priorities and set(priorities) != {"High", "Medium", "Low"} and "Priority" in result:
        result = result[result["Priority"].isin(priorities)]
    return result


def render_data_workspace(section: str, frame: pd.DataFrame) -> None:
    """Render one of the analytics workspaces with shared session filters."""
    if section == "Settings":
        render_settings(frame)
        return

    filtered = render_filters(frame)
    st.markdown(f"### {section}")
    st.caption(f"Showing {len(filtered):,} of {len(frame):,} records from the live agricultural metrics dataset.")

    if section == "Data Explorer":
        render_data_explorer(filtered)
    elif section == "Visualizations":
        render_visualization_builder(filtered)
    elif section == "Reports":
        render_reports(filtered)


def render_filters(frame: pd.DataFrame) -> pd.DataFrame:
    """Sidebar filters shared by the Explorer, Visualizations, and Reports views."""
    st.sidebar.markdown("### Filter dataset")
    if frame.empty:
        st.sidebar.info("The metrics API returned no records.")
        return frame.copy()

    search = st.sidebar.text_input("Search records or insights", key="insights_search").strip().casefold()
    selected_seasons = st.sidebar.multiselect(
        "Season",
        sorted(frame["Season"].dropna().astype(str).unique()) if "Season" in frame else [],
        key="insights_seasons",
        help="This dataset is organized by season; it does not include daily observation dates.",
    )
    selected_districts = st.sidebar.multiselect(
        "District",
        sorted(frame["District"].dropna().astype(str).unique()) if "District" in frame else [],
        key="insights_districts",
    )
    selected_sectors = st.sidebar.multiselect(
        "Sector",
        sorted(frame["Sector"].dropna().astype(str).unique()) if "Sector" in frame else [],
        key="insights_sectors",
    )
    selected_cells = st.sidebar.multiselect(
        "Cell",
        sorted(frame["Cell"].dropna().astype(str).unique()) if "Cell" in frame else [],
        key="insights_cells",
    )
    selected_crops = st.sidebar.multiselect(
        "Crop",
        sorted(frame["Crop"].dropna().astype(str).unique()) if "Crop" in frame else [],
        key="insights_crops",
    )
    selected_soils = st.sidebar.multiselect(
        "Soil type",
        sorted(frame["Soil type"].dropna().astype(str).unique()) if "Soil type" in frame else [],
        key="insights_soils",
    )

    result = frame.copy()
    if selected_seasons:
        result = result[result["Season"].isin(selected_seasons)]
    if selected_districts:
        result = result[result["District"].isin(selected_districts)]
    if selected_sectors:
        result = result[result["Sector"].isin(selected_sectors)]
    if selected_cells:
        result = result[result["Cell"].isin(selected_cells)]
    if selected_crops:
        result = result[result["Crop"].isin(selected_crops)]
    if selected_soils:
        result = result[result["Soil type"].isin(selected_soils)]

    numeric = [column for column in NUMERIC_COLUMNS if column in result and result[column].notna().any()]
    if numeric:
        measure = st.sidebar.selectbox("Numeric range", numeric, key="insights_range_column")
        values = result[measure].dropna()
        low, high = float(values.min()), float(values.max())
        if low < high:
            selected_range = st.sidebar.slider(
                f"{measure} range",
                min_value=low,
                max_value=high,
                value=(low, high),
                key=f"insights_range_{measure}",
            )
            result = result[result[measure].between(*selected_range) | result[measure].isna()]

    if search:
        searchable = result.astype("string").fillna("").apply(lambda column: column.str.casefold())
        result = result[searchable.apply(lambda column: column.str.contains(re.escape(search), regex=True)).any(axis=1)]
    return result


def render_data_explorer(frame: pd.DataFrame) -> None:
    st.markdown("#### Dataset overview")
    total_missing = int(frame.isna().sum().sum()) if not frame.empty else 0
    columns = st.columns(4)
    columns[0].metric("Records", f"{len(frame):,}")
    columns[1].metric("Fields", f"{len(frame.columns):,}")
    columns[2].metric("Missing values", f"{total_missing:,}")
    columns[3].metric("Districts", f"{frame['District'].nunique(dropna=True):,}" if "District" in frame else "N/A")

    if frame.empty:
        st.info("No records match the selected filters. Adjust the filters to continue exploring.")
        return

    with st.expander("Column details and descriptive statistics", expanded=False):
        details = pd.DataFrame({
            "Column": frame.columns,
            "Data type": [str(frame[column].dtype) for column in frame.columns],
            "Missing": [int(frame[column].isna().sum()) for column in frame.columns],
            "Unique values": [int(frame[column].nunique(dropna=True)) for column in frame.columns],
        })
        st.dataframe(details, width="stretch", hide_index=True)
        numeric = frame.select_dtypes(include="number")
        if not numeric.empty:
            st.dataframe(numeric.describe().T.rename_axis("Measure").reset_index(), width="stretch", hide_index=True)

    page_size = st.selectbox("Rows per page", [25, 50, 100], index=0, key="insights_page_size")
    page_count = max(1, (len(frame) + page_size - 1) // page_size)
    page_number = st.number_input("Page", min_value=1, max_value=page_count, value=1, step=1, key="insights_page_number")
    start = (int(page_number) - 1) * page_size
    st.dataframe(frame.iloc[start:start + page_size], width="stretch", hide_index=True)
    st.caption(f"Rows {start + 1:,}–{min(start + page_size, len(frame)):,} of {len(frame):,}. Select a column header to sort.")


def render_visualization_builder(frame: pd.DataFrame) -> None:
    st.markdown("#### Build a chart from the filtered records")
    if frame.empty:
        st.info("No data matches these filters. Update the filters to build a chart.")
        return

    chart_type = st.selectbox("Chart type", ["Bar", "Line", "Area", "Pie", "Donut", "Scatter", "Histogram"], key="insights_chart_type")
    dimensions = [column for column in CATEGORICAL_COLUMNS if column in frame and frame[column].nunique(dropna=True) > 1]
    measures = [column for column in NUMERIC_COLUMNS if column in frame and frame[column].notna().any()]

    if chart_type == "Histogram":
        if not measures:
            st.info("The filtered records have no numeric values to plot.")
            return
        measure = st.selectbox("Measure", measures, key="insights_histogram_measure")
        fig = px.histogram(frame.dropna(subset=[measure]), x=measure, nbins=30, color_discrete_sequence=["#1682bb"])
    elif chart_type == "Scatter":
        if len(measures) < 2:
            st.info("A scatter plot needs two numeric measures with values in the filtered data.")
            return
        controls = st.columns(3)
        x_measure = controls[0].selectbox("X-axis", measures, index=0, key="insights_scatter_x")
        y_options = [column for column in measures if column != x_measure]
        y_measure = controls[1].selectbox("Y-axis", y_options, key="insights_scatter_y")
        color = controls[2].selectbox("Group", ["None", *dimensions], key="insights_scatter_color")
        fig = px.scatter(frame.dropna(subset=[x_measure, y_measure]), x=x_measure, y=y_measure,
                         color=None if color == "None" else color, hover_data=[column for column in ("District", "Crop", "Season") if column in frame])
    else:
        if not dimensions:
            st.info("Choose a category with at least two values to compare.")
            return
        controls = st.columns(3)
        category = controls[0].selectbox("Category (X-axis)", dimensions, key="insights_chart_category")
        measure = controls[1].selectbox("Measure", ["Record count", *measures], key="insights_chart_measure")
        group = controls[2].selectbox("Compare groups", ["None", *[column for column in dimensions if column != category]], key="insights_chart_group")
        group_column = None if group == "None" else group
        group_columns = [category] + ([group_column] if group_column else [])
        selected = frame.dropna(subset=[category]).copy()
        if measure == "Record count":
            grouped = selected.groupby(group_columns, dropna=False).size().rename("Value").reset_index()
            measure_label = "Records"
        else:
            selected[measure] = pd.to_numeric(selected[measure], errors="coerce")
            selected = selected.dropna(subset=[measure])
            grouped = selected.groupby(group_columns, dropna=False)[measure].mean().rename("Value").reset_index()
            measure_label = f"Average {measure}"
        if grouped.empty:
            st.info("There are no compatible values for this chart and filter selection.")
            return
        if chart_type in {"Pie", "Donut"} and group_column:
            st.info("Remove the group breakdown to keep this chart readable.")
            return
        if chart_type == "Bar":
            fig = px.bar(grouped, x=category, y="Value", color=group_column, barmode="group", labels={"Value": measure_label}, color_discrete_sequence=px.colors.qualitative.Safe)
        elif chart_type == "Line":
            fig = px.line(grouped, x=category, y="Value", color=group_column, markers=True, labels={"Value": measure_label}, color_discrete_sequence=px.colors.qualitative.Safe)
        elif chart_type == "Area":
            fig = px.area(grouped, x=category, y="Value", color=group_column, markers=True, labels={"Value": measure_label}, color_discrete_sequence=px.colors.qualitative.Safe)
        else:
            fig = px.pie(grouped, names=category, values="Value", hole=0.48 if chart_type == "Donut" else 0,
                         color_discrete_sequence=px.colors.qualitative.Safe)

    fig.update_layout(**get_plotly_layout(), height=420, transition_duration=250)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": True, "scrollZoom": False}, key="insights_custom_chart")
    st.download_button("Download filtered chart data (CSV)", frame.to_csv(index=False).encode("utf-8"),
                       "agrimenya_filtered_chart_data.csv", "text/csv", key="download_chart_data")


def _season_key(value: object) -> tuple[int, int, str]:
    text = str(value or "")
    year_match = re.search(r"\b(20\d{2})\b", text)
    part_match = re.search(r"\b([AB])\b", text, re.IGNORECASE)
    return (int(year_match.group(1)) if year_match else 0,
            1 if part_match and part_match.group(1).upper() == "A" else 2 if part_match else 0,
            text)


def seasons_match(value: object, selected: object) -> bool:
    value_year, value_part, value_text = _season_key(value)
    selected_year, selected_part, selected_text = _season_key(selected)
    if value_part and selected_part:
        return value_part == selected_part and (not value_year or not selected_year or value_year == selected_year)
    return value_text.casefold() == selected_text.casefold()


def build_insights(frame: pd.DataFrame) -> list[tuple[str, str, str]]:
    """Create observations only when the filtered data supports them."""
    insights: list[tuple[str, str, str]] = []
    if frame.empty:
        return insights
    if "Crop" in frame and "Yield (kg/ha)" in frame:
        crop_yield = frame.dropna(subset=["Crop", "Yield (kg/ha)"]).groupby("Crop")["Yield (kg/ha)"].mean().sort_values(ascending=False)
        if not crop_yield.empty:
            crop, value = crop_yield.index[0], float(crop_yield.iloc[0])
            insights.append(("positive", "Highest average crop yield", f"{crop} averages {value:,.0f} kg/ha across the filtered records."))
            if len(crop_yield) > 1:
                low_crop, low_value = crop_yield.index[-1], float(crop_yield.iloc[-1])
                insights.append(("attention", "Lowest average crop yield", f"{low_crop} averages {low_value:,.0f} kg/ha in this selection."))
    if "District" in frame and "Yield (kg/ha)" in frame:
        district_yield = frame.dropna(subset=["District", "Yield (kg/ha)"]).groupby("District")["Yield (kg/ha)"].mean().sort_values(ascending=False)
        if not district_yield.empty:
            district, value = district_yield.index[0], float(district_yield.iloc[0])
            insights.append(("info", "Leading district by average yield", f"{district} has the highest mean yield at {value:,.0f} kg/ha."))
    if "Season" in frame and "Yield (kg/ha)" in frame:
        season_means = frame.dropna(subset=["Season", "Yield (kg/ha)"]).groupby("Season")["Yield (kg/ha)"].mean()
        if len(season_means) > 1:
            ordered = sorted(season_means.items(), key=lambda item: _season_key(item[0]))
            previous, current = ordered[-2], ordered[-1]
            if previous[1] != 0:
                change = (float(current[1]) - float(previous[1])) / abs(float(previous[1])) * 100
                direction = "positive" if change > 0 else "attention" if change < 0 else "info"
                insights.append((direction, "Season-over-season yield comparison",
                                 f"Mean yield changed {change:+.1f}% from {previous[0]} to {current[0]} (unadjusted for crop mix)."))
    if "Crop" in frame and "Production (MT)" in frame:
        production = frame.dropna(subset=["Crop", "Production (MT)"]).groupby("Crop")["Production (MT)"].sum().sort_values(ascending=False)
        total = float(production.sum()) if not production.empty else 0
        if total > 0:
            crop = production.index[0]
            share = float(production.iloc[0]) / total * 100
            insights.append(("info", "Largest production share", f"{crop} accounts for {share:.1f}% of recorded production in this selection."))
    if "Yield (kg/ha)" in frame and "Production (MT)" in frame:
        pair = frame[["Yield (kg/ha)", "Production (MT)"]].dropna()
        if len(pair) >= 4:
            correlation = float(pair.corr().iloc[0, 1])
            if pd.notna(correlation) and abs(correlation) >= 0.5:
                insights.append(("info", "Yield and production move together", f"Their Pearson correlation is {correlation:.2f}; this is association, not evidence of cause."))
    if "Yield (kg/ha)" in frame:
        values = frame["Yield (kg/ha)"].dropna()
        if len(values) >= 8:
            q1, q3 = values.quantile([0.25, 0.75])
            spread = q3 - q1
            if spread > 0:
                outlier_count = int(((values < q1 - 1.5 * spread) | (values > q3 + 1.5 * spread)).sum())
                if outlier_count:
                    insights.append(("attention", "Unusually distant yield values", f"{outlier_count} records fall outside the 1.5× IQR range; review them before drawing conclusions."))
    return insights


def render_reports(frame: pd.DataFrame) -> None:
    if frame.empty:
        st.info("No filtered records are available to include in a report.")
        return
    yield_values = frame["Yield (kg/ha)"].dropna() if "Yield (kg/ha)" in frame else pd.Series(dtype=float)
    production_values = frame["Production (MT)"].dropna() if "Production (MT)" in frame else pd.Series(dtype=float)
    summary = {
        "Records included": len(frame),
        "Districts represented": int(frame["District"].nunique(dropna=True)) if "District" in frame else 0,
        "Crops represented": int(frame["Crop"].nunique(dropna=True)) if "Crop" in frame else 0,
        "Average yield (kg/ha)": float(yield_values.mean()) if not yield_values.empty else None,
        "Median yield (kg/ha)": float(yield_values.median()) if not yield_values.empty else None,
        "Recorded production (MT)": float(production_values.sum()) if not production_values.empty else None,
    }
    st.markdown("#### Filtered dataset summary")
    st.dataframe(pd.DataFrame([{"Metric": key, "Value": value} for key, value in summary.items()]), width="stretch", hide_index=True)
    insights = build_insights(frame)
    if insights:
        st.markdown("#### Evidence-based observations")
        for _, title, text in insights:
            st.markdown(f"- **{title}:** {text}")
    st.download_button("Download filtered records (CSV)", frame.to_csv(index=False).encode("utf-8"),
                       "agrimenya_filtered_report.csv", "text/csv", key="download_report_csv")
    report_lines = ["# Agri-Menya data summary", "", "Generated from the currently filtered agricultural metrics records.", ""]
    report_lines.extend(f"- **{html.escape(key)}:** {value if value is not None else 'Not available'}" for key, value in summary.items())
    report_lines += ["", "## Data observations", ""]
    report_lines.extend(f"- **{html.escape(title)}:** {html.escape(text)}" for _, title, text in insights)
    st.download_button("Download summary report (Markdown)", "\n".join(report_lines).encode("utf-8"),
                       "agrimenya_data_summary.md", "text/markdown", key="download_report_markdown")


def render_settings(frame: pd.DataFrame) -> None:
    st.markdown("### Data workspace settings")
    st.caption("The analytics views use the persisted agricultural metrics returned by the Agri-Menya API.")
    left, right = st.columns(2)
    left.metric("Records available", f"{len(frame):,}")
    left.metric("Fields available", f"{len(frame.columns):,}")
    right.write("**Source**")
    right.code("GET /segmentation/agri-metrics", language="text")
    right.write("Created-at timestamps mark ingestion, not field observation dates; season labels are the valid time unit for comparisons.")
    with st.expander("Dataset fields", expanded=True):
        if frame.empty:
            st.info("The API has not returned any metric records.")
        else:
            dictionary = pd.DataFrame({
                "Field": frame.columns,
                "Type": [str(frame[column].dtype) for column in frame.columns],
                "Missing": [int(frame[column].isna().sum()) for column in frame.columns],
            })
            st.dataframe(dictionary, width="stretch", hide_index=True)

