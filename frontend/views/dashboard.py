"""
Dashboard view - high-level operational overview.

Surfaces executive KPIs, multi-dimensional Plotly charts, global
cross-filtering, live weather and climate links, recommendations, and exports.
"""
import io
import logging

try:
    import pandas as pd
except ImportError:
    pd = None
import requests
import streamlit as st

from components.alerts import render_alert
from components.badges import priority_badge, status_badge
from components.cards import (
    render_empty_state,
    render_kpi_card,
    render_weather_forecast_grid,
)
from components.charts import (
    render_dashboard_chart,
)
from components.errors import error_boundary, render_error_page
from components.icons import render_icon_subheader
from components.navbar import render_page_header
from utils import api_client
from utils.i18n import t
from views.data_insights import (
    build_insights,
    crop_key,
    filter_dashboard_metrics,
    normalize_agri_metrics,
    render_data_workspace,
    seasons_match,
)

logger = logging.getLogger(__name__)


def _metric_number(value, suffix: str = "", grouped: bool = False) -> str:
    if value is None:
        return "N/A"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "N/A"
    formatted = f"{number:,.0f}" if grouped else f"{number:.0f}"
    return f"{formatted}{suffix}"


@error_boundary("Dashboard")
def render_dashboard() -> None:
    try:
        priority_df = api_client.get_priority_data()
        if not isinstance(priority_df, pd.DataFrame):
            priority_df = pd.DataFrame()
        metrics_df = normalize_agri_metrics(api_client.get_agri_metrics())
        if not metrics_df.empty and not priority_df.empty and "id" in priority_df and "Priority" in priority_df:
            priority_lookup = priority_df.dropna(subset=["id"]).drop_duplicates("id").set_index("id")["Priority"]
            metrics_df["Priority"] = metrics_df["Zone ID"].map(priority_lookup)

        section = st.sidebar.radio(
            "Analytics workspace",
            ["Dashboard", "Data Explorer", "Visualizations", "Reports", "Settings"],
            key="analytics_workspace_section",
        )
        if section != "Dashboard":
            render_data_workspace(section, metrics_df)
            return

        # ── 1. Page Header with Breadcrumbs & Mission Badge ─────────────
        render_page_header(
            title="Your Data Insights Dashboard",
            subtitle="Explore real agricultural records, compare yields, and see how results change across crops, districts, and seasons.",
            badge="NISR 2026 • OPERATIONAL COMMAND",
            breadcrumbs=[
                ("Agri-Menya", "Home.py"),
                (t("dashboard.title", "Dashboard"), None),
            ],
        )

        # ── 2. Data Fetching ──────────────────────────────────────────
        df = priority_df
        if not df.empty and "District" in df.columns:
            valid_district = df["District"].astype(str).str.strip().str.casefold().ne("")
            valid_district &= df["District"].astype(str).str.strip().str.casefold().ne("unknown")
            df = df[df["District"].notna() & valid_district]

        # ── 3. Global Synchronized Filter Control Bar ──────────────────
        with st.container(border=True):
            st.markdown(
                '<div style="display:flex;align-items:center;gap:8px;margin-bottom:0.4rem;">'
                '<span style="font-size:0.80rem;font-weight:750;letter-spacing:0.04em;text-transform:uppercase;color:var(--ag-primary);">GLOBAL FILTERS</span>'
                ''
                '</div>',
                unsafe_allow_html=True,
            )

            # Available filter options derived from live dataframe
            all_seasons_label = t("common.all_seasons", "All seasons")
            season_options = [all_seasons_label]
            if not metrics_df.empty and "Season" in metrics_df.columns:
                season_options += sorted(str(s) for s in metrics_df["Season"].dropna().unique())
            elif not df.empty and "season" in df.columns:
                season_options += sorted(str(s) for s in df["season"].dropna().unique())

            crop_options = []
            if not metrics_df.empty and "Crop" in metrics_df.columns:
                crop_options = sorted(str(c) for c in metrics_df["Crop"].dropna().unique())

            priority_options = ["High", "Medium", "Low"]

            all_districts_label = t("common.all_districts", "All Districts")
            district_options = [all_districts_label]
            if not metrics_df.empty and "District" in metrics_df.columns:
                district_options += sorted(str(d) for d in metrics_df["District"].dropna().unique())

            f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns([1.1, 1.3, 1.15, 1.15, 1.3])

            with f_col1:
                selected_season = st.selectbox(
                    t("seg.season", "Season"),
                    season_options,
                    index=0,
                    key="dash_filter_season",
                )
            with f_col2:
                selected_crops = st.multiselect(
                    t("seg.crops", "Crops"),
                    crop_options,
                    default=[],
                    key="dash_filter_crops",
                )
            with f_col3:
                selected_priorities = st.multiselect(
                    t("seg.priority_level", "Priority Levels"),
                    priority_options,
                    default=priority_options,
                    key="dash_filter_priority",
                )
            with f_col4:
                selected_district = st.selectbox(
                    t("common.district", "District Focus"),
                    district_options,
                    index=0,
                    key="dash_filter_district",
                )
            with f_col5:
                dashboard_search = st.text_input("Search records", key="dash_filter_search").strip().casefold()

        # Apply global cross-filtering to priority data
        filtered_df = df.copy()
        if not filtered_df.empty:
            if selected_season != all_seasons_label and "season" in filtered_df.columns:
                filtered_df = filtered_df[filtered_df["season"].map(lambda value: seasons_match(value, selected_season))]
            if selected_crops and "Crop" in filtered_df.columns:
                crop_keys = {crop_key(crop) for crop in selected_crops}
                filtered_df = filtered_df[filtered_df["Crop"].map(crop_key).isin(crop_keys)]
            if selected_priorities and "Priority" in filtered_df.columns:
                filtered_df = filtered_df[filtered_df["Priority"].isin(selected_priorities)]
            if selected_district != all_districts_label and "District" in filtered_df.columns:
                filtered_df = filtered_df[filtered_df["District"] == selected_district]

        filtered_metrics_df = filter_dashboard_metrics(
            metrics_df,
            season=selected_season,
            all_seasons_label=all_seasons_label,
            crops=selected_crops,
            district=selected_district,
            all_districts_label=all_districts_label,
            priorities=selected_priorities,
        )
        if dashboard_search:
            for filtered in (filtered_df, filtered_metrics_df):
                if not filtered.empty:
                    searchable = filtered.astype("string").fillna("").apply(lambda column: column.str.casefold())
                    filtered.drop(filtered[~searchable.apply(lambda column: column.str.contains(dashboard_search, regex=False)).any(axis=1)].index, inplace=True)

        # ── 4. Executive KPI Grid with Sparklines ──────────────────────
        kpi_c1, kpi_c2, kpi_c3, kpi_c4, kpi_c5 = st.columns(5)

        total_records = len(filtered_metrics_df)
        total_production = filtered_metrics_df["Production (MT)"].sum(min_count=1) if "Production (MT)" in filtered_metrics_df else None
        average_yield = filtered_metrics_df["Yield (kg/ha)"].mean() if "Yield (kg/ha)" in filtered_metrics_df else None
        crop_count = filtered_metrics_df["Crop"].nunique(dropna=True) if "Crop" in filtered_metrics_df else 0
        district_count = filtered_metrics_df["District"].nunique(dropna=True) if "District" in filtered_metrics_df else 0

        icon_map = """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/><line x1="9" y1="3" x2="9" y2="18"/><line x1="15" y1="6" x2="15" y2="21"/></svg>"""
        icon_records = """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/></svg>"""
        icon_yield = """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21V11M12 14c-4 0-7-2.5-7-6 4 0 7 2 7 6ZM12 11c0-4 3-7 7-7 0 4-3 7-7 7Z"/></svg>"""
        icon_crop = """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22V12M12 16c-4 0-7-2-7-6 4 0 7 2 7 6ZM12 12c0-4 3-7 7-7 0 4-3 7-7 7ZM12 10C8 10 6 7 6 4c4 0 6 2 6 6Z"/></svg>"""
        icon_bank = """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>"""

        render_kpi_card(
            kpi_c1,
            title="Filtered Records",
            value=f"{total_records:,}",
            icon=icon_records,
            badge_color="#0284c7",
        )
        render_kpi_card(
            kpi_c2,
            title="Recorded Production (MT)",
            value=_metric_number(total_production, grouped=True) if pd.notna(total_production) else "N/A",
            icon=icon_bank,
            badge_color="#ef4444",
        )
        render_kpi_card(
            kpi_c3,
            title="Average Yield (kg/ha)",
            value=_metric_number(average_yield, grouped=True) if pd.notna(average_yield) else "N/A",
            icon=icon_yield,
            badge_color="#10b981",
        )
        render_kpi_card(
            kpi_c4,
            title="Crop Types",
            value=f"{crop_count:,}",
            icon=icon_crop,
            badge_color="#0284c7",
        )
        render_kpi_card(
            kpi_c5,
            title="Districts Represented",
            value=f"{district_count:,}",
            icon=icon_map,
            badge_color="#10b981",
        )

        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

        # ── 5. Live District Weather & Climate ─────────────────────────
        with st.container(border=True):
            render_icon_subheader("assets/compass.svg", "Live weather and climate")

            try:
                district_catalog = api_client.get_districts() or []
            except Exception:
                logger.exception("Unable to load canonical districts for the weather view")
                district_catalog = []
            districts = sorted({
                str(item.get("district", "")).strip()
                for item in district_catalog
                if isinstance(item, dict) and item.get("district")
            })
            if not districts:
                try:
                    weather_zones = api_client.get_zones() or []
                except Exception:
                    logger.exception("Unable to load registered weather locations")
                    weather_zones = []
                districts = sorted({
                    str(zone.get("district", "")).strip()
                    for zone in weather_zones
                    if isinstance(zone, dict) and zone.get("district")
                })

            if not districts:
                st.warning("No district locations are available for the weather view.")
            else:
                default_district = (
                    selected_district
                    if selected_district != all_districts_label and selected_district in districts
                    else districts[0]
                )
                w_c1, w_c2 = st.columns([3, 1])
                with w_c1:
                    active_weather_district = st.selectbox(
                        t("dashboard.weather.district_select", "District weather"),
                        districts,
                        index=districts.index(default_district),
                        key="dash_weather_district_select",
                    )
                with w_c2:
                    st.write("")
                    if st.button(t("dashboard.weather.refresh_btn", "Refresh weather"), use_container_width=True):
                        api_client.get_weather.clear()
                        st.rerun()

                try:
                    with st.spinner(f"Loading live weather for {active_weather_district}..."):
                        weather = api_client.get_weather(active_weather_district)
                except Exception:
                    logger.exception("Unable to load weather for %s", active_weather_district)
                    weather = None

                if isinstance(weather, dict) and weather:
                    temp_val = weather.get("temperature_c")
                    hum_val = weather.get("humidity_pct")
                    rain_val = weather.get("rainfall_mm")
                    wind_val = weather.get("wind_kph")

                    temp_str = f"{temp_val:.1f} °C" if isinstance(temp_val, (int, float)) else "Not available °C"
                    hum_str = f"{hum_val:.0f}%" if isinstance(hum_val, (int, float)) else "Not available%"
                    rain_str = f"{rain_val:.1f} mm" if isinstance(rain_val, (int, float)) else "Not available mm"
                    wind_str = f"{wind_val:.1f} km/h" if isinstance(wind_val, (int, float)) else "Not available km/h"

                    w_metric1, w_metric2, w_metric3, w_metric4 = st.columns(4)
                    w_metric1.metric("Temperature", temp_str)
                    w_metric2.metric("Relative Humidity", hum_str)
                    w_metric3.metric("Precipitation", rain_str)
                    w_metric4.metric("Wind Speed", wind_str)
                    forecast_data = weather.get("forecast") or []
                    if forecast_data:
                        render_weather_forecast_grid(forecast_data)
                    st.caption(
                        f"Live conditions: {weather.get('source') or 'source unavailable'} · "
                        f"Updated: {weather.get('updated_at') or 'time not reported'}"
                    )
                else:
                    st.warning("Weather data is temporarily unavailable.")
                st.markdown(
                    "For official national climate notices and reports, visit "
                    "[Meteo Rwanda](https://www.meteorwanda.gov.rw/climate-warning)."
                )

        # One configurable chart replaces the separate dashboard graphs.
        with st.container(border=True):
            render_icon_subheader("assets/brain.svg", t("dashboard.chart.title", "Make the chart your own"))
            st.caption(t("dashboard.chart.subtitle", "Choose what to compare. The chart updates as you adjust the controls."))
            try:
                render_dashboard_chart(filtered_metrics_df)
            except Exception:
                logger.exception("Unable to render dashboard chart")
                st.warning("The chart could not be rendered for this selection. Try changing the filters or chart fields.")

        with st.container(border=True):
            render_icon_subheader("assets/brain.svg", "Insights from selected records")
            insights = build_insights(filtered_metrics_df)
            if not insights:
                st.info("There are not enough complete records in this selection to calculate insights.")
            else:
                for tone, title, text in insights:
                    if tone == "attention":
                        st.warning(f"**{title}.** {text}")
                    elif tone == "positive":
                        st.success(f"**{title}.** {text}")
                    else:
                        st.info(f"**{title}.** {text}")

        # ── 8. Priority Recommendations & Quick Action Hub ─────────────
        act_col, alert_col = st.columns([3, 2], gap="medium")

        with act_col:
            with st.container(border=True):
                render_icon_subheader("assets/brain.svg", t("dashboard.section.top_priority", "Priority Action Interventions"))
                try:
                    recs = api_client.get_recommendations() or []
                except Exception:
                    logger.exception("Unable to load dashboard recommendations")
                    recs = []
                    st.warning("Recommendations are temporarily unavailable.")
                if recs:
                    for i, rec in enumerate(recs[:4]):
                        if not isinstance(rec, dict):
                            logger.warning("Skipping malformed dashboard recommendation: %r", rec)
                            continue
                        with st.container():
                            r_c1, r_c2, r_c3 = st.columns([1.2, 3.2, 1.2])
                            with r_c1:
                                st.markdown(f"**{rec.get('area', 'Unknown')}**")
                                st.caption(f"Crop: {rec.get('crop', 'N/A')}")
                            with r_c2:
                                st.markdown(rec.get("text", ""))
                            with r_c3:
                                priority_badge(rec.get("priority", "Medium"))
                                if st.button("Plan →", key=f"rec_plan_{i}_{rec.get('area')}", use_container_width=True):
                                    st.switch_page("pages/8_Planning.py")
                            st.divider()
                else:
                    render_empty_state("No Priority Flags", "All monitored zones are currently performing within optimal yield baselines.")

        with alert_col:
            with st.container(border=True):
                render_icon_subheader("assets/bell.svg", t("dashboard.section.recent_alerts", "Recent Broadcast Alerts"))
                try:
                    alerts = api_client.get_alerts() or []
                except Exception:
                    logger.exception("Unable to load dashboard alerts")
                    alerts = []
                    st.warning("Broadcast alerts are temporarily unavailable.")
                if alerts:
                    for alert in alerts[:4]:
                        try:
                            render_alert(alert)
                        except Exception:
                            logger.exception("Unable to render dashboard alert")
                else:
                    st.info("No active broadcast alerts.")

            # Quick Action Triggers
            with st.container(border=True):
                render_icon_subheader("assets/compass.svg", t("dashboard.section.quick_actions", "Action Hub"))
                qa1, qa2 = st.columns(2)
                with qa1:
                    if st.button("Predict Yield", use_container_width=True):
                        st.switch_page("pages/4_Zones.py")
                    if st.button("Detect Disease", use_container_width=True):
                        st.switch_page("pages/7_AI_Assistant.py")
                with qa2:
                    if st.button("Create Plan", use_container_width=True):
                        st.switch_page("pages/8_Planning.py")
                    if st.button("Broadcast Alert", use_container_width=True):
                        st.switch_page("pages/9_Communication.py")

        # ── 9. Interactive Record Explorer & CSV Export ────────────────
        with st.container(border=True):
            st.markdown(
                '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:0.5rem;">'
                '<div>'
                '<h3 style="margin:0;font-size:1.15rem;font-weight:750;">Explore agricultural records</h3>'
                ''
                '</div>'
                '</div>',
                unsafe_allow_html=True,
            )

            if not filtered_metrics_df.empty:
                records = filtered_metrics_df.reset_index(drop=True)
                st.caption(
                    f"{len(records):,} records match the dashboard filters. Select a record to inspect its field metrics."
                )
                record_options = list(range(len(records)))

                def _record_label(index: int) -> str:
                    record = records.iloc[index]
                    district = record.get("District")
                    crop_value = record.get("Crop")
                    season_value = record.get("Season")
                    location = str(district) if pd.notna(district) else "Unspecified district"
                    crop = str(crop_value) if pd.notna(crop_value) else "Unspecified crop"
                    season = str(season_value) if pd.notna(season_value) else "Season not recorded"
                    return f"{location} · {crop} · {season} · Record {index + 1}"

                selected_record_index = st.selectbox(
                    "Choose a record",
                    record_options,
                    format_func=_record_label,
                    key="dashboard_record_select",
                )
                selected_record = records.iloc[selected_record_index]
                metric_columns = [
                    ("Yield (kg/ha)", "Yield (kg/ha)", "kg/ha"),
                    ("Production (MT)", "Production", "MT"),
                    ("Cultivated area (ha)", "Cultivated area", "ha"),
                    ("Rainfall (mm)", "Rainfall", "mm"),
                ]
                available_record_metrics = [
                    (column, label, unit)
                    for column, label, unit in metric_columns
                    if column in records.columns
                ]
                if available_record_metrics:
                    metric_cols = st.columns(min(len(available_record_metrics), 4))
                    for metric_col, (column, label, unit) in zip(metric_cols, available_record_metrics):
                        value = pd.to_numeric(pd.Series([selected_record.get(column)]), errors="coerce").iloc[0]
                        metric_col.metric(
                            label,
                            f"{value:,.1f} {unit}" if pd.notna(value) else "Not recorded",
                        )
                location = selected_record.get("District")
                crop_value = selected_record.get("Crop")
                season_value = selected_record.get("Season")
                st.caption(
                    f"Location: {location if pd.notna(location) else 'Not recorded'}"
                    f" · Crop: {crop_value if pd.notna(crop_value) else 'Not recorded'}"
                    f" · Season: {season_value if pd.notna(season_value) else 'Not recorded'}"
                )

                # Export CSV button
                csv_buffer = io.StringIO()
                filtered_metrics_df.to_csv(csv_buffer, index=False)
                st.download_button(
                    label="Export Filtered Records (CSV)",
                    data=csv_buffer.getvalue(),
                    file_name="agrimenya_dashboard_zones.csv",
                    mime="text/csv",
                    use_container_width=False,
                )
            else:
                render_empty_state("No Matching Data", "No crop and yield records match the selected filters.")

    except requests.exceptions.RequestException as e:
        logger.error("Network error in dashboard: %s", e)
        render_error_page("network", str(e))
    except Exception as e:
        logger.error("Unexpected error in dashboard: %s", e, exc_info=True)
        render_error_page("system", str(e))
