"""
Dashboard view — high-level operational overview.

Surfaces KPIs, priority map, alerts, and quick actions in a single pane.
"""
import logging

import requests
import streamlit as st
from components.alerts import render_alert
from components.badges import priority_badge
from components.charts import render_yield_chart
from components.errors import render_error_page
from components.icons import render_icon_subheader
from components.maps import render_priority_map
from utils import api_client
from utils.i18n import t

logger = logging.getLogger(__name__)


def render_dashboard() -> None:
    try:
        st.markdown(
            '<h1 style="font-family: \'Space Grotesk\', sans-serif; '
            'background: linear-gradient(135deg, #2D6A4F, #52B788); '
            '-webkit-background-clip: text; -webkit-text-fill-color: transparent; '
            'margin-bottom: 0.25rem;">Dashboard</h1>'
            '<p style="color: #6B7280; margin-top: 0;">Operational overview of agricultural zones across Rwanda</p>',
            unsafe_allow_html=True,
        )

        # ── KPI summary cards ────────────────────────────────────────
        dashboard_data = api_client.get_alignment_dashboard()
        kpi_cols = st.columns(5)

        kpi_items = [
            ("Total Zones", dashboard_data.get("total_zones", 0), None),
            ("High Priority", dashboard_data.get("high_priority_zones", 0), None),
            ("Credit Readiness", f"{dashboard_data.get('avg_credit_readiness', 0):.0f}%", None),
            ("Export Ready", dashboard_data.get("export_ready_zones", 0), None),
            ("Jobs Supported", f"{dashboard_data.get('estimated_jobs', 0):,}", None),
        ]

        for col, (label, value, delta) in zip(kpi_cols, kpi_items):
            with col:
                st.metric(label, value, delta)

        st.divider()

        # ── Map + Priority Breakdown ─────────────────────────────────
        map_col, chart_col = st.columns([3, 2])

        df = api_client.get_priority_data()

        with map_col:
            render_icon_subheader("assets/map.svg", "Zone Priority Map")
            render_priority_map(df)

        with chart_col:
            render_icon_subheader("assets/brain.svg", "Yield by District")
            render_yield_chart(df)

        st.divider()

        # ── Alerts + Quick Actions ───────────────────────────────────
        alerts_col, actions_col = st.columns([3, 2])

        with alerts_col:
            render_icon_subheader("assets/bell.svg", "Recent Alerts")
            alerts = api_client.get_alerts()
            if not alerts:
                st.info("No active alerts.")
            else:
                for alert in alerts[:5]:
                    render_alert(alert)

        with actions_col:
            render_icon_subheader("assets/compass.svg", "Quick Actions")
            st.markdown('<div style="display: flex; flex-direction: column; gap: 8px;">', unsafe_allow_html=True)

            if st.button("Predict Zone Yield", icon=":material/query_stats:", use_container_width=True):
                st.switch_page("pages/4_Zones.py")
            if st.button("Create New Plan", icon=":material/edit_calendar:", use_container_width=True):
                st.switch_page("pages/6_Planning.py")
            if st.button("Detect Crop Disease", icon=":material/biotech:", use_container_width=True):
                st.switch_page("pages/5_AI_Assistant.py")
            if st.button("Send Alert", icon=":material/campaign:", use_container_width=True):
                st.switch_page("pages/7_Communication.py")

            st.markdown("</div>", unsafe_allow_html=True)

        st.divider()

        # ── Priority Ranking Table ───────────────────────────────────
        render_icon_subheader("assets/brain.svg", "Top Priority Zones")
        recs = api_client.get_recommendations()
        if recs:
            for rec in recs[:5]:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([1, 4, 1])
                    with c1:
                        st.markdown(f"**{rec.get('area', 'Unknown')}**")
                        st.caption(f"Crop: {rec.get('crop', 'N/A')}")
                    with c2:
                        st.markdown(rec.get("text", ""))
                    with c3:
                        priority_badge(rec.get("priority", "Low"))

    except requests.exceptions.RequestException as e:
        logger.error("Network error in dashboard: %s", e)
        render_error_page("network", str(e))
    except Exception as e:
        logger.error("Unexpected error in dashboard: %s", e, exc_info=True)
        render_error_page("system", str(e))
