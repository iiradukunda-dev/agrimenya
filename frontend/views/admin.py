"""
Admin view — operations, governance, and system health.

Implements Page 7 of the frontend handoff: zone/plan/alert management + health.
"""
import logging

import pandas as pd
import requests
import streamlit as st
from components.errors import render_error_page
from components.icons import render_icon_subheader, render_icon_title
from utils import api_client

logger = logging.getLogger(__name__)


def render_admin() -> None:
    try:
        render_icon_title(
            "assets/compass.svg",
            "Admin Panel",
            "System operations, zone management, and health monitoring",
        )

        admin_tabs = st.tabs(["System Health", "Zone Management", "Plan Management", "Alert Management"])

        # ═════════════════════════════════════════════════════════════
        # TAB 1: System Health
        # ═════════════════════════════════════════════════════════════
        with admin_tabs[0]:
            render_icon_subheader("assets/compass.svg", "System Health")

            health = api_client.get_health()
            if health:
                status = health.get("status", "unknown")
                status_color = "#059669" if status == "ok" else "#DC2626"

                h_cols = st.columns(4)
                with h_cols[0]:
                    st.metric("Status", status.upper())
                    st.html(
                        f'<div style="width:12px;height:12px;border-radius:50%;'
                        f'background:{status_color};display:inline-block;'
                        f'box-shadow:0 0 8px {status_color};"></div>'
                    )
                with h_cols[1]:
                    st.metric("Environment", health.get("env", "N/A"))
                with h_cols[2]:
                    model_present = health.get("model_present", False)
                    st.metric("ML Model", "Loaded" if model_present else "Missing")
                with h_cols[3]:
                    baselines_present = health.get("baselines_present", False)
                    st.metric("Baselines", "Loaded" if baselines_present else "Missing")

                with st.expander("Detailed Health Info"):
                    st.json(health)
            else:
                st.error("Backend is unreachable. Check that the API is running on the expected port.")

        # ═════════════════════════════════════════════════════════════
        # TAB 2: Zone Management
        # ═════════════════════════════════════════════════════════════
        with admin_tabs[1]:
            render_icon_subheader("assets/map.svg", "Zone Management")

            admin_zones = api_client.get_admin_zones()
            if admin_zones:
                df = pd.DataFrame(admin_zones)
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.caption(f"{len(admin_zones)} zones registered.")
            else:
                # Fall back to segmentation zones
                zones = api_client.get_zones()
                if zones:
                    df = pd.DataFrame(zones)
                    display_cols = [c for c in ["id", "name", "district", "crop", "priority", "predicted_yield", "area_ha"] if c in df.columns]
                    st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
                    st.caption(f"{len(zones)} zones from segmentation data.")
                else:
                    st.info("No zone data available.")

        # ═════════════════════════════════════════════════════════════
        # TAB 3: Plan Management
        # ═════════════════════════════════════════════════════════════
        with admin_tabs[2]:
            render_icon_subheader("assets/calendar.svg", "Plan Management")

            admin_plans = api_client.get_admin_plans()
            if admin_plans:
                df = pd.DataFrame(admin_plans)
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.caption(f"{len(admin_plans)} plans found.")
            else:
                st.info("No plans available from the admin endpoint. Plans are created through the Planning page.")

        # ═════════════════════════════════════════════════════════════
        # TAB 4: Alert Management
        # ═════════════════════════════════════════════════════════════
        with admin_tabs[3]:
            render_icon_subheader("assets/bell.svg", "Alert Management")

            admin_alerts = api_client.get_admin_alerts()
            if admin_alerts:
                df = pd.DataFrame(admin_alerts)
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.caption(f"{len(admin_alerts)} alerts found.")
            else:
                # Fall back to communication alerts
                alerts = api_client.get_alerts()
                if alerts:
                    df = pd.DataFrame(alerts)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    st.caption(f"{len(alerts)} alerts from communication feed.")
                else:
                    st.info("No alerts available.")

    except requests.exceptions.RequestException as e:
        logger.error("Network error in admin view: %s", e)
        render_error_page("network", str(e))
    except Exception as e:
        logger.error("Unexpected error in admin view: %s", e, exc_info=True)
        render_error_page("system", str(e))
