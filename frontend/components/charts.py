"""
Chart components for the Segmentation pillar.

Uses Plotly Express with the agrimenya color palette.
"""
import plotly.express as px
import streamlit as st
from utils.i18n import t

# Shared Plotly layout settings matching the agrimenya design system
AG_PLOTLY_LAYOUT = dict(
    font=dict(family="Inter, sans-serif", color="#374151"),
    title_font=dict(family="Space Grotesk, sans-serif", size=16, color="#1B3A2D"),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    legend=dict(
        bgcolor="rgba(255,255,255,0.5)",
        bordercolor="rgba(209,213,219,0.4)",
        borderwidth=1,
        font=dict(size=11),
    ),
    margin=dict(l=40, r=20, t=50, b=40),
    hoverlabel=dict(
        bgcolor="white",
        font_size=12,
        font_family="Inter, sans-serif",
    ),
)


def render_yield_chart(df) -> None:
    """
    Renders a grouped bar chart of average crop yield by district and priority.
    Uses the agrimenya semantic color palette for priority levels.
    """
    if df.empty:
        st.info(t("seg.empty"))
        return

    priority_colors = {
        "High":   "#DC2626",
        "Medium": "#D97706",
        "Low":    "#059669",
    }

    grouped = (
        df.groupby(["District", "Priority"])["Yield_MT_ha"]
        .mean()
        .reset_index()
    )

    fig = px.bar(
        grouped,
        x="District",
        y="Yield_MT_ha",
        color="Priority",
        color_discrete_map=priority_colors,
        title=t("seg.chart_title"),
        barmode="group",
    )

    fig.update_layout(**AG_PLOTLY_LAYOUT)
    fig.update_xaxes(
        title=t("seg.axis_district"),
        gridcolor="rgba(209,213,219,0.3)",
        linecolor="rgba(209,213,219,0.5)",
    )
    fig.update_yaxes(
        title=t("seg.axis_yield"),
        gridcolor="rgba(209,213,219,0.3)",
        linecolor="rgba(209,213,219,0.5)",
    )
    fig.update_traces(
        marker_line_width=0,
        marker_cornerradius=6,
    )

    st.plotly_chart(fig, use_container_width=True)
