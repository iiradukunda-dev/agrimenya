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
