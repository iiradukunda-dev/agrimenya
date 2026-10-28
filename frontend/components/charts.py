"""
Interactive chart components for agrimenya dashboards and segmentation.

Built on Plotly Express with custom theme tokens, responsive layouts,
and dark/light mode compatibility.
"""
try:
    import plotly.express as px
    import plotly.graph_objects as go
except ImportError:
    px = None
    go = None
try:
    import pandas as pd
except ImportError:
    pd = None
import streamlit as st
from utils.i18n import t
from utils.theme import get_current_theme

# Semantic palette matching design system
PRIORITY_COLORS = {
    "High": "#ef4444",
    "Medium": "#f59e0b",
    "Low": "#10b981",
    "Unassessed": "#94a3b8",
}


def get_plotly_layout() -> dict:
    """Return layout dictionary dynamically configured for current theme mode."""
    is_dark = get_current_theme() == "dark"
    text_color = "#f8fafc" if is_dark else "#1e293b"
    muted_color = "#94a3b8" if is_dark else "#64748b"
    grid_color = "rgba(255, 255, 255, 0.08)" if is_dark else "rgba(15, 23, 42, 0.06)"
    hover_bg = "#0f172a" if is_dark else "#ffffff"

    return dict(
        font=dict(family="Inter, sans-serif", color=text_color, size=12),
        title_font=dict(family="Plus Jakarta Sans, sans-serif", size=15, color=text_color),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11, color=muted_color),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        margin=dict(l=30, r=20, t=45, b=35),
        hoverlabel=dict(
            bgcolor=hover_bg,
            font_size=12,
            font_family="Inter, sans-serif",
            font_color=text_color,
            bordercolor=grid_color,
        ),
    )


def render_yield_chart(df) -> None:
    """
    Renders grouped estimated production by district and priority.
    """
    if px is None:
        st.info("Chart engine is currently initializing.")
        return
    if df.empty:
        st.info(t("seg.empty", default="No data available to plot."))
        return

    # Check required columns
    group_cols = [c for c in ["District", "Priority"] if c in df.columns]
    y_col = "Production_MT" if "Production_MT" in df.columns else ("Yield_MT_ha" if "Yield_MT_ha" in df.columns else None)

    if not group_cols or not y_col:
        st.info("Insufficient columns for yield chart.")
        return

    grouped = df.groupby(group_cols, as_index=False)[y_col].mean()

    fig = px.bar(
        grouped,
        x="District" if "District" in grouped.columns else group_cols[0],
        y=y_col,
        color="Priority" if "Priority" in grouped.columns else None,
        color_discrete_map=PRIORITY_COLORS,
        title=t("seg.chart_title", default="Production by District & Priority"),
        barmode="group",
    )

    layout = get_plotly_layout()
    fig.update_layout(**layout)
    fig.update_xaxes(
        gridcolor="rgba(150, 150, 150, 0.1)",
        linecolor="rgba(150, 150, 150, 0.2)",
        tickangle=-35,
    )
    fig.update_yaxes(
        title="Production (MT)" if y_col == "Production_MT" else "Yield (MT/ha)",
        gridcolor="rgba(150, 150, 150, 0.1)",
        linecolor="rgba(150, 150, 150, 0.2)",
    )
    fig.update_traces(
        marker_cornerradius=4,
        hovertemplate="<b>%{x}</b><br>Production: %{y:.1f} MT<extra></extra>",
    )

    st.plotly_chart(fig, width="stretch")


def render_priority_donut_chart(df) -> None:
    """
    Renders an interactive donut chart showing the percentage breakdown of priority risk levels.
    """
    if px is None:
        st.info("Chart engine is currently initializing.")
        return
    if df.empty or "Priority" not in df.columns:
        st.info("No priority distribution data.")
        return

    counts = df["Priority"].value_counts().reset_index()
    counts.columns = ["Priority", "Count"]

    fig = px.pie(
        counts,
        names="Priority",
        values="Count",
        color="Priority",
        color_discrete_map=PRIORITY_COLORS,
        hole=0.62,
        title="Priority Distribution",
    )

    layout = get_plotly_layout()
    fig.update_layout(**layout)
    fig.update_traces(
        textposition="inside",
        textinfo="percent",
        hovertemplate="<b>%{label} Priority</b><br>Zones: %{value} (%{percent})<extra></extra>",
        marker=dict(line=dict(color="rgba(0,0,0,0)", width=2)),
    )
    # Center metric annotation
    total = len(df)
    is_dark = get_current_theme() == "dark"
    fig.add_annotation(
        text=f"<b>{total}</b><br><span style='font-size:10px;color:#94a3b8;'>ZONES</span>",
        x=0.5,
        y=0.5,
        font=dict(size=18, family="Plus Jakarta Sans, sans-serif", color="#f8fafc" if is_dark else "#0f172a"),
        showarrow=False,
    )

    st.plotly_chart(fig, width="stretch")


def render_crop_comparison_bar(df) -> None:
    """
    Renders average production by crop across the selected zones.
    """
    if px is None:
        st.info("Chart engine is currently initializing.")
        return
    if df.empty or "Crop" not in df.columns:
        st.info("No crop comparison data.")
        return

    y_col = "Production_MT" if "Production_MT" in df.columns else ("Yield_MT_ha" if "Yield_MT_ha" in df.columns else None)
    if not y_col:
        return

    crop_agg = df.groupby("Crop", as_index=False)[y_col].mean().sort_values(y_col, ascending=False).head(10)

    fig = px.bar(
        crop_agg,
        x="Crop",
        y=y_col,
        title="Top Crops by Average Production",
        color=y_col,
        color_continuous_scale=["#38bdf8", "#0284c7", "#0369a1"],
    )

    layout = get_plotly_layout()
    fig.update_layout(**layout)
    fig.update_coloraxes(showscale=False)
    fig.update_xaxes(gridcolor="rgba(150, 150, 150, 0.1)")
    fig.update_yaxes(gridcolor="rgba(150, 150, 150, 0.1)")
    fig.update_traces(
        marker_cornerradius=4,
        hovertemplate="<b>%{x}</b><br>Avg Production: %{y:.1f} MT<extra></extra>",
    )

    st.plotly_chart(fig, width="stretch")


def render_dashboard_chart(df) -> None:
    """Render one user-configurable chart for the dashboard's filtered data."""
    if px is None or pd is None:
        st.info(t("dashboard.chart.unavailable", "The chart is unavailable right now."))
        return
    if df is None or df.empty:
        st.info(t("dashboard.chart.empty", "There is no data for these filters yet."))
        return

    dimensions = [
        column for column in ("District", "Crop", "Priority", "Season", "season", "Province")
        if column in df.columns and df[column].nunique(dropna=True) > 1
    ]
    if not dimensions:
        st.info(t("dashboard.chart.no_dimensions", "There are not enough categories to build a chart."))
        return

    excluded_numeric = {"id", "zone_id", "lat", "lon", "latitude", "longitude"}
    numeric_columns = [
        column for column in df.select_dtypes(include="number").columns
        if column.lower() not in excluded_numeric and df[column].notna().any()
    ]
    preferred_metrics = [column for column in ("Production (MT)", "Yield (kg/ha)", "Production_MT", "Yield_MT_ha") if column in numeric_columns]
    metric_columns = preferred_metrics + [column for column in numeric_columns if column not in preferred_metrics]

    dimension_labels = {
        "District": t("common.district", "District"),
        "Crop": t("common.crop", "Crop"),
        "Priority": t("dashboard.chart.priority", "Priority"),
        "season": t("common.season", "Season"),
        "Season": t("common.season", "Season"),
        "Province": t("common.province", "Province"),
    }
    metric_labels = {
        "Production_MT": t("dashboard.chart.production", "Production (MT)"),
        "Yield_MT_ha": t("dashboard.chart.yield", "Yield (MT/ha)"),
        "Production (MT)": "Production (MT)",
        "Yield (kg/ha)": "Yield (kg/ha)",
    }
    for column in metric_columns:
        metric_labels.setdefault(column, column.replace("_", " "))

    controls = st.columns([1.15, 1.35, 1.0, 1.0, 1.25], gap="small")
    with controls[0]:
        x_column = st.selectbox(
            t("dashboard.chart.group_by", "Group by"),
            dimensions,
            format_func=lambda value: dimension_labels.get(value, value),
            key="dashboard_chart_group_by",
        )
    with controls[1]:
        record_count_label = "Records"
        measure_options = [record_count_label] + metric_columns
        measure = st.selectbox(
            t("dashboard.chart.measure", "Measure"),
            measure_options,
            format_func=lambda value: (
                value if value == measure_options[0] else metric_labels.get(value, value)
            ),
            key="dashboard_chart_measure",
        )
    with controls[2]:
        summary = st.selectbox(
            t("dashboard.chart.summary", "Summary"),
            [t("dashboard.chart.average", "Average"), t("dashboard.chart.total", "Total")],
            key="dashboard_chart_summary",
            disabled=measure == record_count_label,
        )
    with controls[3]:
        chart_type = st.selectbox(
            t("dashboard.chart.style", "Chart style"),
            ["Bar", "Line", "Scatter"],
            format_func=lambda value: t(f"dashboard.chart.style.{value.lower()}", value),
            key="dashboard_chart_style",
        )
    with controls[4]:
        no_breakdown = t("dashboard.chart.none", "No breakdown")
        series_options = [""] + [column for column in dimensions if column != x_column]
        selected_series = st.selectbox(
            t("dashboard.chart.breakdown", "Break down by"),
            series_options,
            format_func=lambda value: (
                no_breakdown if not value else dimension_labels.get(value, value)
            ),
            key="dashboard_chart_breakdown",
        )
        series_column = selected_series or None

    group_columns = [x_column] + ([series_column] if series_column else [])
    if measure == record_count_label:
        chart_data = df.groupby(group_columns, dropna=False).size().rename("value").reset_index()
        metric_title = record_count_label
    else:
        numeric_values = df[group_columns + [measure]].copy()
        numeric_values[measure] = pd.to_numeric(numeric_values[measure], errors="coerce")
        numeric_values = numeric_values.dropna(subset=[measure])
        if numeric_values.empty:
            st.info(t("dashboard.chart.no_values", "There are no values for this measure in the current selection."))
            return
        reducer = "mean" if summary == t("dashboard.chart.average", "Average") else "sum"
        chart_data = numeric_values.groupby(group_columns, dropna=False)[measure].agg(reducer).rename("value").reset_index()
        metric_title = f"{summary} {metric_labels.get(measure, measure)}"

    if chart_data.empty:
        st.info(t("dashboard.chart.empty", "There is no data for these filters yet."))
        return
    if chart_type == "Bar":
        fig = px.bar(chart_data, x=x_column, y="value", color=series_column, barmode="group")
    elif chart_type == "Line":
        fig = px.line(chart_data, x=x_column, y="value", color=series_column, markers=True)
    else:
        fig = px.scatter(chart_data, x=x_column, y="value", color=series_column)

    fig.update_layout(**get_plotly_layout(), height=420, xaxis_title=dimension_labels.get(x_column, x_column), yaxis_title=metric_title)
    fig.update_xaxes(gridcolor="rgba(150, 150, 150, 0.1)", linecolor="rgba(150, 150, 150, 0.2)")
    fig.update_yaxes(gridcolor="rgba(150, 150, 150, 0.1)", linecolor="rgba(150, 150, 150, 0.2)", rangemode="tozero")
    fig.update_traces(hovertemplate=f"<b>%{{x}}</b><br>{metric_title}: %{{y:,.2f}}<extra></extra>")
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False}, key="dashboard_explorer_chart")



def render_district_ranking_chart(rankings: list[dict], crop: str, national_ref: float | None = None) -> None:
    """Renders a comparative bar chart of district yields against the national reference benchmark."""
    if px is None:
        st.info("Chart engine is currently initializing.")
        return
    if not rankings:
        st.info("No district ranking data available.")
        return

    sorted_rankings = sorted(rankings, key=lambda r: float(r.get("yield_per_ha") or 0), reverse=True)
    districts = [str(r.get("district", "Unknown")) for r in sorted_rankings]
    yields = [float(r.get("yield_per_ha") or 0) for r in sorted_rankings]

    fig = px.bar(
        x=districts,
        y=yields,
        title=f"District Yield Ranking — {crop} (kg/ha)",
        color=yields,
        color_continuous_scale="Viridis",
    )

    layout = get_plotly_layout()
    fig.update_layout(**layout)
    fig.update_coloraxes(showscale=False)
    fig.update_xaxes(tickangle=-40, title="District", gridcolor="rgba(150, 150, 150, 0.1)")
    fig.update_yaxes(title="Yield (kg/ha)", gridcolor="rgba(150, 150, 150, 0.1)")

    if national_ref:
        fig.add_hline(
            y=national_ref,
            line_dash="dash",
            line_color="#ef4444",
            annotation_text=f"National Ref: {national_ref:,.0f} kg/ha",
            annotation_position="top right",
        )

    fig.update_traces(
        marker_cornerradius=4,
        hovertemplate="<b>%{x}</b><br>Yield: %{y:,.1f} kg/ha<extra></extra>",
    )

    st.plotly_chart(fig, width="stretch")
