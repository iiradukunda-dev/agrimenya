"""
Admin view: executive operations, governance, zone/plan/alert management, NISR data releases, and community moderation.

Implements an executive Liquid Glass administrative interface for agrimenya.
"""
import logging
from html import escape
from typing import Any

import pandas as pd
import requests
import streamlit as st
from components.errors import error_boundary, render_error_page
from components.icons import render_icon_subheader, render_icon_title
from utils import api_client
from utils.i18n import t

logger = logging.getLogger(__name__)


@st.dialog("System Diagnostics & Raw Telemetry", width="large")
def show_diagnostics_dialog(health: dict) -> None:
    """Popup modal dialog for deep diagnostics without page scrolling."""
    st.markdown("#### Subsystem Telemetry Snapshot")
    st.json(health)
    if st.button("Refresh Telemetry Now", key="btn_refresh_health_dlg", type="primary"):
        st.rerun()


@st.dialog("Plan Inspector & Action Audit Trail", width="large")
def show_plan_inspector_dialog(plan_labels: dict) -> None:
    """Popup modal dialog for plan renaming and audit inspection without vertical scrolling."""
    if not plan_labels:
        st.info("No plans available for inspection.")
        return

    selected_plan_label = st.selectbox("Select Plan to Inspect", list(plan_labels), key="dlg_admin_plan_select")
    plan = plan_labels[selected_plan_label]
    plan_id = str(plan["id"])

    with st.form(f"dlg_admin_plan_rename_form_{plan_id}"):
        plan_title_input = st.text_input("Plan Title", value=str(plan.get("title") or ""))
        update_plan_btn = st.form_submit_button("Update Plan Title", type="primary")

    if update_plan_btn:
        if not plan_title_input.strip():
            st.error("Enter a valid plan title.")
        elif api_client.update_admin_plan(plan_id, {"title": plan_title_input.strip()}):
            st.success("Plan title updated.")
            st.rerun()
        else:
            st.error("Plan update failed. Check admin session permissions.")

    st.write("---")
    st.markdown("#### Action Modification History & Audit Trail")
    plan_history = api_client.get_plan_action_history(plan_id)
    if plan_history:
        st.dataframe(pd.DataFrame(plan_history), width="stretch", hide_index=True)
    else:
        st.caption("No action modifications logged for this plan.")


def _render_admin_session_header() -> None:
    """Render the shared responsive administrator session card."""
    from components.cards import authenticated_session_badge

    identity = st.session_state.get("admin_identity", {})
    display_name = identity.get("display_name") or "Administrator"
    email = identity.get("email") or "admin@agrimenya.gov.rw"
    role = identity.get("role") or "System Administrator"
    if authenticated_session_badge(
        display_name=display_name,
        email=email,
        role=role,
        key_prefix="admin_panel",
    ):
        api_client.admin_sign_out()
        st.rerun()


@error_boundary("Admin Panel")
def render_admin() -> None:
    try:
        if not api_client.render_admin_login("admin_panel"):
            return

        render_icon_title(
            "assets/compass.svg",
            t("admin.title", "Admin Panel"),
            t("admin.subtitle", "System operations, zone management, and health monitoring"),
        )

        _render_admin_session_header()

        admin_tabs = st.tabs([
            t("admin.tab.health", "System Health"),
            t("admin.tab.zones", "Zone Management"),
            t("admin.tab.plans", "Plan Management"),
            t("admin.tab.alerts", "Alert Management"),
            t("admin.tab.nisr", "NISR Data"),
            t("admin.tab.access", "Access Management"),
            t("admin.tab.moderation", "Community Moderation"),
        ])

        # ═════════════════════════════════════════════════════════════
        # TAB 1: System Health & Telemetry
        # ═════════════════════════════════════════════════════════════
        with admin_tabs[0]:
            render_icon_subheader("assets/compass.svg", "System Health & Channel Telemetry")

            health = api_client.get_health()
            email_health = api_client.get_email_status()
            if email_health:
                if email_health.get("ready"):
                    st.success(f"Transactional email settings are present ({email_health.get('provider', 'unknown')}).")
                else:
                    issue = email_health.get("configuration_issue") or "Email provider settings are incomplete."
                    st.error(f"Transactional email is not ready: {issue}")
                    if email_health.get("gmail_smtp"):
                        st.caption(
                            "For Gmail SMTP, use smtp.gmail.com:587 with STARTTLS, "
                            "SMTP_USER matching EMAIL_FROM, and a Gmail App Password in SMTP_PASSWORD."
                        )
                    if email_health.get("provider") == "smtp":
                        st.warning(
                            "Render Free services block outbound SMTP ports 25, 465, and 587. "
                            "Use Resend over HTTPS with a verified sender domain, or upgrade the backend service."
                        )
            else:
                st.warning("Email delivery status could not be checked.")

            if health:
                status = str(health.get("status", "unknown")).lower()
                is_ok = status == "ok"

                st.markdown(
                    f"""
                    <div style="
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                        padding: 12px 18px;
                        border-radius: 12px;
                        background: {'rgba(16, 185, 129, 0.12)' if is_ok else 'rgba(245, 158, 11, 0.12)'};
                        border: 1px solid {'rgba(16, 185, 129, 0.35)' if is_ok else 'rgba(245, 158, 11, 0.35)'};
                        color: {'#065f46' if is_ok else '#92400e'};
                        font-size: 0.92rem;
                        font-weight: 600;
                        margin-bottom: 1.2rem;
                    ">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span style="width: 10px; height: 10px; border-radius: 50%; background: {'#10b981' if is_ok else '#f59e0b'}; display: inline-block;"></span>
                            <div>
                                <strong>Core Status: {status.upper()}</strong> &mdash; 
                                {'All primary services, database probes, and yield baselines are responding normally.' if is_ok else 'One or more subsystem indicators report degraded performance or missing baselines.'}
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                h_cols = st.columns(5)
                with h_cols[0]:
                    with st.container(border=True):
                        st.caption("API Core Service")
                        st.markdown(f"<h3 style='margin:0;color:#0284c7;'>{status.upper()}</h3>", unsafe_allow_html=True)
                        st.caption("FastAPI &bull; Port 8000")
                with h_cols[1]:
                    with st.container(border=True):
                        db_status = str(health.get("database_status", "unknown")).upper()
                        db_color = "#059669" if db_status == "OK" else "#dc2626"
                        st.caption("Database Connectivity")
                        st.markdown(f"<h3 style='margin:0;color:{db_color};'>{db_status}</h3>", unsafe_allow_html=True)
                        st.caption("Supabase / PostgreSQL")
                with h_cols[2]:
                    with st.container(border=True):
                        env_label = str(health.get("env", "N/A")).upper()
                        st.caption("Active Environment")
                        st.markdown(f"<h3 style='margin:0;color:#0f172a;'>{env_label}</h3>", unsafe_allow_html=True)
                        st.caption("Runtime Profile")
                with h_cols[3]:
                    with st.container(border=True):
                        yield_source = health.get("yield_source") or "Unavailable"
                        if "database" in str(yield_source).casefold():
                            src_label = "DB + SAS Baselines"
                        elif "model" in str(yield_source).casefold():
                            src_label = "Trained Model"
                        else:
                            src_label = "Unavailable"
                        st.caption("Yield Evidence Engine")
                        st.markdown(f"<h3 style='margin:0;color:#0284c7;'>{src_label}</h3>", unsafe_allow_html=True)
                        st.caption("Primary Baseline Basis")
                with h_cols[4]:
                    with st.container(border=True):
                        baselines_present = health.get("baselines_present", False)
                        base_color = "#059669" if baselines_present else "#d97706"
                        st.caption("NISR Yield Baselines")
                        st.markdown(f"<h3 style='margin:0;color:{base_color};'>{'LOADED' if baselines_present else 'OFFLINE'}</h3>", unsafe_allow_html=True)
                        st.caption("30 Districts Active")

                st.write("")
                render_icon_subheader("assets/message.svg", "WhatsApp Channel Telemetry")
                wa_health = api_client.get_whatsapp_health()
                if wa_health:
                    w_cols = st.columns(4)
                    with w_cols[0]:
                        with st.container(border=True):
                            st.caption("Operating Mode")
                            st.markdown(f"<h3 style='margin:0;color:#0284c7;'>{str(wa_health.get('mode', 'sandbox')).upper()}</h3>", unsafe_allow_html=True)
                            st.caption("Cloud API Integration")
                    with w_cols[1]:
                        with st.container(border=True):
                            st.caption("Active Contacts")
                            st.markdown(f"<h3 style='margin:0;color:#0f172a;'>{wa_health.get('active_contacts', 0)}</h3>", unsafe_allow_html=True)
                            st.caption("Opted-in Phone Numbers")
                    with w_cols[2]:
                        with st.container(border=True):
                            st.caption("24h Outbound Messages")
                            st.markdown(f"<h3 style='margin:0;color:#059669;'>{wa_health.get('outbound_24h', 0)}</h3>", unsafe_allow_html=True)
                            st.caption("Broadcast Dispatches")
                    with w_cols[3]:
                        with st.container(border=True):
                            failures = wa_health.get("failed_24h", 0)
                            fail_color = "#059669" if failures == 0 else "#dc2626"
                            st.caption("24h Failures")
                            st.markdown(f"<h3 style='margin:0;color:{fail_color};'>{failures}</h3>", unsafe_allow_html=True)
                            st.caption("Delivery Errors")
                else:
                    st.info("WhatsApp telemetry endpoint not returning data. Check backend WHATSAPP_PHONE_NUMBER_ID.")

                if st.button("View System Diagnostics & Telemetry", key="btn_open_diagnostics_modal", use_container_width=True):
                    show_diagnostics_dialog(health)
            else:
                st.error("Backend is unreachable. Check that the API is running on the expected port.")

        # ═════════════════════════════════════════════════════════════
        # TAB 2: Zone Management
        # ═════════════════════════════════════════════════════════════
        with admin_tabs[1]:
            render_icon_subheader("assets/map.svg", "Agricultural Zone Management")

            admin_zones = api_client.get_admin_zones()
            if admin_zones:
                districts_set = sorted({str(z.get("district")) for z in admin_zones if z.get("district")})
                crops_set = sorted({str(z.get("crop_type")) for z in admin_zones if z.get("crop_type")})

                # Summary Statistics Bar
                stat_cols = st.columns(3)
                with stat_cols[0]:
                    with st.container(border=True):
                        st.caption("Total Zones Registered")
                        st.markdown(f"<h3 style='margin:0;color:#0f172a;'>{len(admin_zones)}</h3>", unsafe_allow_html=True)
                with stat_cols[1]:
                    with st.container(border=True):
                        st.caption("Districts Covered")
                        st.markdown(f"<h3 style='margin:0;color:#0284c7;'>{len(districts_set)} / 30</h3>", unsafe_allow_html=True)
                with stat_cols[2]:
                    with st.container(border=True):
                        st.caption("Crops Mapped")
                        st.markdown(f"<h3 style='margin:0;color:#10b981;'>{len(crops_set)}</h3>", unsafe_allow_html=True)

                # Search and District Filter
                f_col1, f_col2 = st.columns([2, 1])
                with f_col1:
                    search_query = st.text_input("Search zones by district, sector, or crop", key="admin_zone_search", placeholder="e.g. Gasabo, Maize, Season A")
                with f_col2:
                    district_filter = st.selectbox("Filter by District", ["All Districts"] + districts_set, key="admin_zone_filter")

                # Filter zones
                filtered_zones = admin_zones
                if district_filter != "All Districts":
                    filtered_zones = [z for z in filtered_zones if str(z.get("district")) == district_filter]
                if search_query.strip():
                    q = search_query.strip().lower()
                    filtered_zones = [
                        z for z in filtered_zones
                        if q in str(z.get("district", "")).lower()
                        or q in str(z.get("sector", "")).lower()
                        or q in str(z.get("crop_type", "")).lower()
                        or q in str(z.get("season", "")).lower()
                    ]

                # Formatted Zones Table
                table_data = [
                    {
                        "ID": str(z.get("id"))[-8:],
                        "District": z.get("district") or "N/A",
                        "Sector": z.get("sector") or "N/A",
                        "Cell": z.get("cell") or "N/A",
                        "Crop": z.get("crop_type") or "N/A",
                        "Season": z.get("season") or "N/A",
                        "Coordinates": f"{z.get('latitude', '')}, {z.get('longitude', '')}" if z.get("latitude") is not None else "Not Set",
                    }
                    for z in filtered_zones
                ]
                st.dataframe(pd.DataFrame(table_data), width="stretch", hide_index=True)
                st.caption(f"Showing {len(filtered_zones)} of {len(admin_zones)} registered zones.")

                # Management Actions: Register New & Edit
                action_tabs = st.tabs(["Edit Existing Zone", "Register New Zone"])

                with action_tabs[0]:
                    zone_labels = {
                        f"{z.get('district') or 'Unknown district'} / {z.get('sector') or z.get('cell') or 'Area not set'} | {str(z.get('id'))[-8:]}": z
                        for z in admin_zones if z.get("id")
                    }
                    if zone_labels:
                        selected_label = st.selectbox("Select Zone to Edit", list(zone_labels), key="admin_zone_edit_select")
                        zone = zone_labels[selected_label]
                        zone_id = str(zone["id"])

                        with st.form(f"admin_zone_form_{zone_id}"):
                            left, right = st.columns(2)
                            with left:
                                edit_district = st.text_input("District", value=str(zone.get("district") or ""))
                                edit_sector = st.text_input("Sector", value=str(zone.get("sector") or ""))
                                edit_cell = st.text_input("Cell", value=str(zone.get("cell") or ""))
                                edit_crop = st.text_input("Crop Type", value=str(zone.get("crop_type") or ""))
                            with right:
                                edit_season = st.text_input("Season", value=str(zone.get("season") or ""))
                                edit_lat = st.number_input("Latitude", min_value=-90.0, max_value=90.0, value=float(zone["latitude"]) if zone.get("latitude") is not None else None, format="%.6f")
                                edit_lng = st.number_input("Longitude", min_value=-180.0, max_value=180.0, value=float(zone["longitude"]) if zone.get("longitude") is not None else None, format="%.6f")
                            update_btn = st.form_submit_button("Save Zone Updates", type="primary")

                        if update_btn:
                            if not edit_district.strip():
                                st.error("A zone must have a valid district name.")
                            else:
                                payload = {
                                    "district": edit_district.strip(),
                                    "sector": edit_sector.strip() or None,
                                    "cell": edit_cell.strip() or None,
                                    "crop_type": edit_crop.strip() or None,
                                    "season": edit_season.strip() or None,
                                }
                                if edit_lat is not None:
                                    payload["latitude"] = edit_lat
                                if edit_lng is not None:
                                    payload["longitude"] = edit_lng
                                result = api_client.update_admin_zone(zone_id, payload)
                                if result:
                                    st.success("Zone details updated successfully.")
                                    st.rerun()
                                else:
                                    st.error("Zone update failed. Check administrative credentials and values.")
                    else:
                        st.info("No editable zones available.")

                with action_tabs[1]:
                    with st.form("admin_create_zone_form", clear_on_submit=True):
                        c_left, c_right = st.columns(2)
                        with c_left:
                            new_district = st.text_input("District (Required)", placeholder="e.g. Gasabo")
                            new_sector = st.text_input("Sector", placeholder="e.g. Remera")
                            new_cell = st.text_input("Cell", placeholder="e.g. Rukiri I")
                            new_crop = st.text_input("Crop", placeholder="e.g. Maize")
                        with c_right:
                            new_season = st.text_input("Season", placeholder="e.g. 2026 Season A")
                            new_lat = st.number_input("Latitude", min_value=-90.0, max_value=90.0, value=None, format="%.6f")
                            new_lng = st.number_input("Longitude", min_value=-180.0, max_value=180.0, value=None, format="%.6f")
                        create_zone_btn = st.form_submit_button("Register New Zone", type="primary")

                    if create_zone_btn:
                        if not new_district.strip():
                            st.error("Please enter a district name.")
                        else:
                            create_payload = {
                                "district": new_district.strip(),
                                "sector": new_sector.strip() or None,
                                "cell": new_cell.strip() or None,
                                "crop_type": new_crop.strip() or None,
                                "season": new_season.strip() or None,
                            }
                            if new_lat is not None:
                                create_payload["latitude"] = new_lat
                            if new_lng is not None:
                                create_payload["longitude"] = new_lng
                            res = api_client.create_zone(create_payload)
                            if res:
                                st.success(f"Zone for {new_district.strip()} registered successfully.")
                                st.rerun()
                            else:
                                st.error("Failed to register zone. Confirm backend database connectivity.")
            else:
                error = api_client.get_admin_api_error("/admin/zones")
                if error:
                    st.error(f"Zone management could not load: {error}")
                else:
                    st.info("No zones have been registered yet.")

        # ═════════════════════════════════════════════════════════════
        # TAB 3: Plan Management
        # ═════════════════════════════════════════════════════════════
        with admin_tabs[2]:
            render_icon_subheader("assets/calendar.svg", "Seasonal Plan Management")

            admin_plans = api_client.get_admin_plans()
            if admin_plans:
                plan_stat1, plan_stat2 = st.columns(2)
                with plan_stat1:
                    with st.container(border=True):
                        st.caption("Total Seasonal Plans")
                        st.markdown(f"<h3 style='margin:0;color:#0f172a;'>{len(admin_plans)}</h3>", unsafe_allow_html=True)
                with plan_stat2:
                    with st.container(border=True):
                        unique_zones = len({str(p.get("zone_id")) for p in admin_plans if p.get("zone_id")})
                        st.caption("Zones with Plans")
                        st.markdown(f"<h3 style='margin:0;color:#0284c7;'>{unique_zones}</h3>", unsafe_allow_html=True)

                search_plan = st.text_input("Filter plans by title or zone ID", key="admin_plan_search", placeholder="e.g. Maize Planting, Gasabo")
                filtered_plans = admin_plans
                if search_plan.strip():
                    sp = search_plan.strip().lower()
                    filtered_plans = [
                        p for p in filtered_plans
                        if sp in str(p.get("title", "")).lower() or sp in str(p.get("zone_id", "")).lower()
                    ]

                plan_table = [
                    {
                        "ID": str(p.get("id"))[-8:],
                        "Title": p.get("title") or "Untitled Plan",
                        "Zone ID": str(p.get("zone_id"))[-8:] if p.get("zone_id") else "N/A",
                        "Created At": str(p.get("created_at") or "")[:19],
                    }
                    for p in filtered_plans
                ]
                st.dataframe(pd.DataFrame(plan_table), width="stretch", hide_index=True)
                st.caption(f"Showing {len(filtered_plans)} of {len(admin_plans)} seasonal plans.")

                plan_labels = {
                    f"{p.get('title') or 'Untitled plan'} | {str(p.get('id'))[-8:]}": p
                    for p in admin_plans if p.get("id")
                }
                if st.button("Inspect Action Audit Trail & Plans", key="btn_open_plan_inspector_modal", use_container_width=True):
                    show_plan_inspector_dialog(plan_labels)
            else:
                error = api_client.get_admin_api_error("/admin/plans")
                if error:
                    st.error(f"Plan management could not load: {error}")
                else:
                    st.info("No plans found. Plans are initialized through the Planning module.")

        # ═════════════════════════════════════════════════════════════
        # ═════════════════════════════════════════════════════════════
        # TAB 4: WhatsApp Operations & Advisory Dispatch
        # ═════════════════════════════════════════════════════════════
        with admin_tabs[3]:
            render_icon_subheader("assets/message.svg", "WhatsApp Operations & Advisory Dispatch")

            tab4_subtabs = st.tabs([
                "WhatsApp Command Center",
                "Compose System Alert & Email Handoff",
            ])

            # Subtab 1: Full WhatsApp Operational Suite
            with tab4_subtabs[0]:
                from components.whatsapp_admin import render_whatsapp_admin_panel
                render_whatsapp_admin_panel(key_prefix="admin_wa_tab", embedded_mode=True)

            # Subtab 2: Compose Alert & Broadcast Handoff
            with tab4_subtabs[1]:
                zones = api_client.get_admin_zones()
                zone_options = {
                    f"{z.get('district', 'Unknown district')} / {z.get('sector') or z.get('cell') or str(z.get('id', ''))[-8:]}": z.get("id")
                    for z in zones if z.get("id")
                }

                st.markdown(
                    """
                    <div style="padding:10px 16px; border-radius:10px; background:linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border:1px solid rgba(2, 132, 199, 0.25); border-left:4px solid #0284c7; font-size:0.86rem; color:#1e293b; margin-bottom:1rem;">
                        <strong>Dispatch Architecture:</strong> Alerts composed here are published to the public dashboard feed and emailed to active Farmer Community accounts. Outbound WhatsApp delivery requires review and certification in the <strong>WhatsApp Command Center</strong> tab.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if zone_options:
                    with st.form("admin_create_alert_form", clear_on_submit=True):
                        c1, c2 = st.columns(2)
                        with c1:
                            target_zone = st.selectbox("Target Agricultural Area", list(zone_options))
                            alert_severity = st.selectbox("Severity Classification", ["Info", "Warning", "Critical"])
                        with c2:
                            alert_crop = st.text_input("Associated Crop (Optional)", placeholder="e.g. Maize, Beans")
                            alert_action = st.text_input("Recommended Agronomic Action (Optional)", placeholder="e.g. Apply mulch, delay sowing")

                        alert_body = st.text_area("Alert Message / Announcement", max_chars=2000, height=120, placeholder="Describe the weather anomaly, pest outbreak, or field guidance...")
                        dispatch_btn = st.form_submit_button("Broadcast Alert (Feed & Email Handoff)", type="primary")

                    if dispatch_btn:
                        if not alert_body.strip():
                            st.error("Please enter the alert message.")
                        else:
                            res = api_client.send_admin_alert({
                                "zone_id": zone_options[target_zone],
                                "severity": alert_severity,
                                "message": alert_body.strip(),
                                "crop": alert_crop.strip() or None,
                                "action": alert_action.strip() or None,
                            })
                            if res:
                                delivery = res.get("email_delivery") or {}
                                sent_count = int(delivery.get("sent") or 0)
                                if delivery.get("status") == "sent":
                                    st.success(f"Alert published! SMTP accepted delivery for all {sent_count} active farmer accounts.")
                                elif sent_count:
                                    st.warning(f"Alert published; SMTP accepted {sent_count} emails.")
                                elif delivery.get("status") == "no_recipients":
                                    st.info("Alert published to dashboard feed. (No active Farmer Community accounts registered yet).")
                                else:
                                    st.warning("Alert published to feed; email delivery was deferred.")
                                st.rerun()
                            else:
                                st.error(api_client.get_admin_api_error("/communication/alerts") or "Failed to create alert.")
                else:
                    st.error("Please register at least one agricultural zone before creating alerts.")

        # ═════════════════════════════════════════════════════════════
        # TAB 5: NISR Data Releases
        # ═════════════════════════════════════════════════════════════
        with admin_tabs[4]:
            render_icon_subheader("assets/compass.svg", "NISR SAS Dataset Release Imports")

            st.markdown(
                """
                <div style="padding:12px 18px; border-radius:12px; background:linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border:1px solid rgba(2, 132, 199, 0.25); border-left:4px solid #0284c7; color:#0f172a; margin-bottom:1.2rem;">
                    <strong>Seasonal Agricultural Survey (SAS) Workflow:</strong> Upload official NISR district-by-crop yield tables.
                    Required columns: <code>district, crop, season, yield_kg_ha</code>.
                    Optional columns: <code>production_mt, cultivated_area_ha</code>.
                </div>
                """,
                unsafe_allow_html=True,
            )

            example_csv = (
                "district,crop,season,yield_kg_ha,production_mt,cultivated_area_ha\n"
                "Gasabo,Maize,2026 Season C,2200,4.4,2.0\n"
                "Musanze,Irish Potatoes,2026 Season C,4500,9.0,2.0\n"
            )
            st.download_button(
                "Download CSV Format Specification Sample",
                data=example_csv,
                file_name="nisr_yield_import_example.csv",
                mime="text/csv",
                type="secondary",
            )

            with st.container(border=True):
                st.markdown("**Upload New Official NISR Release**")
                with st.form("nisr_release_import_form", clear_on_submit=True):
                    src_release = st.text_input("Release Title or Reference", placeholder="e.g. Seasonal Agricultural Survey: Season C, 2026")
                    src_season = st.text_input("Season Label", placeholder="e.g. 2026 Season C")
                    nisr_csv_file = st.file_uploader("Upload CSV Dataset", type=["csv"], key="nisr_csv_upload_input")
                    import_submit = st.form_submit_button("Validate & Ingest Release", type="primary")

                if import_submit:
                    if not src_release.strip() or not src_season.strip() or nisr_csv_file is None:
                        st.error("Please provide the release reference, season label, and CSV file.")
                    else:
                        result = api_client.upload_nisr_release(
                            nisr_csv_file.name, nisr_csv_file.getvalue(), src_release.strip(), src_season.strip()
                        )
                        if result:
                            st.success(
                                f"Successfully ingested {result.get('rows_imported', 0)} yield observations for "
                                f"{result.get('season')} from '{result.get('source_release')}'."
                            )
                            st.rerun()
                        else:
                            detail = api_client.get_admin_api_error("/admin/nisr/imports")
                            st.error(f"Import failed: {detail or 'The API could not validate the CSV dataset.'}")

            # Historical Imports
            st.write("")
            st.markdown("**Historical NISR Ingested Releases**")
            imports = api_client.get_nisr_imports()
            if imports:
                st.dataframe(
                    [{
                        "Release Reference": item.get("source_release"),
                        "Season": item.get("season"),
                        "Filename": item.get("source_filename"),
                        "Observations": item.get("row_count"),
                        "Status": item.get("status"),
                        "Ingested At": str(item.get("created_at") or "")[:19],
                    } for item in imports],
                    width="stretch",
                    hide_index=True,
                )
            elif api_client.get_admin_api_error("/admin/nisr/imports"):
                st.error(f"Could not load NISR import history: {api_client.get_admin_api_error('/admin/nisr/imports')}")
            else:
                st.caption("No NISR releases have been imported yet.")

        # ═════════════════════════════════════════════════════════════
        # TAB 6: Access Management
        # ═════════════════════════════════════════════════════════════
        with admin_tabs[5]:
            render_icon_subheader("assets/compass.svg", "Administrator Accounts & Access Governance")

            with st.container(border=True):
                st.markdown("**Invite New System Administrator**")
                st.caption("Administrator invitations issue single-use secure tokens that expire automatically after 30 minutes.")
                with st.form("admin_invite_form", clear_on_submit=True):
                    col_inv_name, col_inv_email = st.columns(2)
                    with col_inv_name:
                        inv_name = st.text_input("Administrator Full Name", placeholder="e.g. Marie Claire")
                    with col_inv_email:
                        inv_email = st.text_input("Official Work Email", placeholder="e.g. marie@minagri.gov.rw")
                    send_inv_btn = st.form_submit_button("Dispatch Administrator Invitation", type="primary")

                if send_inv_btn:
                    if not inv_name.strip() or not inv_email.strip():
                        st.error("Please enter both administrator name and work email.")
                    else:
                        inv_res = api_client.invite_admin_account(inv_email.strip(), inv_name.strip())
                        if inv_res:
                            st.success(f"Invitation successfully dispatched to {inv_res.get('email')}.")
                            st.rerun()
                        else:
                            st.error(api_client.get_admin_api_error("/auth/admin/accounts") or "Invitation failed.")

            st.write("")
            st.markdown("**Active Administrator Accounts Directory**")
            accounts = api_client.get_admin_accounts()
            if accounts:
                current_admin_id = str(st.session_state.get("admin_identity", {}).get("id", ""))
                table_admins = [
                    {
                        "Name": a.get("display_name"),
                        "Email": a.get("email"),
                        "Role": (a.get("role") or "admin").upper(),
                        "Status": "ACTIVE" if a.get("is_active") else "DISABLED",
                        "Created": str(a.get("created_at") or "")[:10],
                    }
                    for a in accounts
                ]
                st.dataframe(pd.DataFrame(table_admins), width="stretch", hide_index=True)

                manageable_accounts = [a for a in accounts if str(a.get("id")) != current_admin_id]
                if manageable_accounts:
                    st.write("")
                    st.markdown("**Account Status Controls**")
                    for account in manageable_accounts:
                        label = f"{account.get('display_name')} &bull; {account.get('email')}"
                        is_active = bool(account.get("is_active"))
                        with st.container(border=True):
                            c_info, c_btn = st.columns([4, 1.2])
                            with c_info:
                                st.markdown(f"**{label}** &mdash; Status: `{'ACTIVE' if is_active else 'DISABLED'}`", unsafe_allow_html=True)
                            with c_btn:
                                target_active = not is_active
                                btn_label = "Restore Access" if target_active else "Disable Account"
                                btn_type = "primary" if target_active else "secondary"
                                if st.button(btn_label, key=f"admin_acc_btn_{account.get('id')}", use_container_width=True, type=btn_type):
                                    result = api_client.set_admin_account_active(str(account.get("id")), target_active)
                                    if result:
                                        st.success(result.get("message", "Access privileges updated."))
                                        st.rerun()
                                    else:
                                        path = f"/auth/admin/accounts/{account.get('id')}/status"
                                        st.error(api_client.get_admin_api_error(path) or "Could not update status.")
            elif api_client.get_admin_api_error("/auth/admin/accounts"):
                st.error(f"Administrator accounts could not load: {api_client.get_admin_api_error('/auth/admin/accounts')}")
            else:
                st.info("No administrator accounts found.")

        # ═════════════════════════════════════════════════════════════
        # TAB 7: Community Moderation
        # ═════════════════════════════════════════════════════════════
        with admin_tabs[6]:
            render_icon_subheader("assets/compass.svg", "Community Content Moderation")

            reports = api_client.get_community_moderation_reports()
            field_reports = api_client.get_community_moderation_field_reports()
            all_posts = api_client.get_community_moderation_posts()
            comm_accounts = api_client.get_community_accounts()

            mod_kpis = st.columns(4)
            with mod_kpis[0]:
                with st.container(border=True):
                    rep_color = "#dc2626" if len(reports) > 0 else "#059669"
                    st.caption("Open Reports")
                    st.markdown(f"<h3 style='margin:0;color:{rep_color};'>{len(reports)}</h3>", unsafe_allow_html=True)
            with mod_kpis[1]:
                with st.container(border=True):
                    st.caption("Field Observations")
                    st.markdown(f"<h3 style='margin:0;color:#0f172a;'>{len(field_reports)}</h3>", unsafe_allow_html=True)
            with mod_kpis[2]:
                with st.container(border=True):
                    st.caption("Community Posts")
                    st.markdown(f"<h3 style='margin:0;color:#0284c7;'>{len(all_posts)}</h3>", unsafe_allow_html=True)
            with mod_kpis[3]:
                with st.container(border=True):
                    st.caption("Farmer Accounts")
                    st.markdown(f"<h3 style='margin:0;color:#059669;'>{len(comm_accounts)}</h3>", unsafe_allow_html=True)

            mod_tabs = st.tabs([
                f"Open Reports ({len(reports)})",
                f"Field Observations ({len(field_reports)})",
                f"Discussions ({len(all_posts)})",
                f"Farmer Accounts ({len(comm_accounts)})",
            ])

            # Subtab 1: Open Reports
            with mod_tabs[0]:
                if not reports:
                    st.info("Zero open community reports. All content is clear.")
                for report in reports:
                    target_kind = "comment" if report.get("comment_id") else "post"
                    target = report.get(target_kind) or {}
                    author = target.get("author") or {}
                    with st.container(border=True):
                        st.markdown(f"**Report Reason:** <span style='color:#f87171;'>{escape(str(report.get('reason', '')))}</span>", unsafe_allow_html=True)
                        st.caption(f"{target_kind.title()} by {author.get('display_name', 'Community Member')} &bull; Submitted {report.get('created_at', '')}")
                        if target_kind == "post":
                            st.markdown(f"**{target.get('title', 'Untitled')}**")
                        st.write(target.get("body", ""))

                        action_cols = st.columns([1, 1, 1, 2])
                        actions = [("Hide Content", "hide"), ("Delete Content", "delete"), ("Dismiss Report", "dismiss")]
                        for col, (label, act) in zip(action_cols[:3], actions):
                            if col.button(label, key=f"comm_rep_{report['id']}_{act}"):
                                res = api_client.moderate_community_content({
                                    "target_kind": target_kind,
                                    "target_id": report.get("comment_id") or report.get("post_id"),
                                    "action": act,
                                    "report_id": report["id"],
                                    "report_action": "dismissed" if act == "dismiss" else "resolved",
                                })
                                if res:
                                    st.success(res.get("message", "Moderation executed."))
                                    st.rerun()
                                else:
                                    st.error(api_client.get_admin_api_error("/community/moderation") or "Moderation failed.")

            # Subtab 2: Field Observations
            with mod_tabs[1]:
                if not field_reports:
                    st.caption("No field observations submitted yet.")
                for freport in field_reports:
                    reporter = freport.get("reporter") or {}
                    with st.container(border=True):
                        st.caption(f"{freport.get('district', 'Unknown')} &bull; Crop: {freport.get('crop', 'Unknown')} &bull; Observed: {freport.get('observed_on', '')} &bull; Reporter: {reporter.get('display_name', 'Unknown')}")
                        st.write(freport.get("symptoms") or freport.get("notes") or "No symptoms/notes reported")
                        if freport.get("photo_url"):
                            st.image(freport["photo_url"], width=280)
                        if st.button("Delete Field Observation", key=f"del_freport_{freport.get('id')}", type="secondary"):
                            if api_client.delete_community_field_report(str(freport["id"])):
                                st.success("Observation deleted.")
                                st.rerun()
                            else:
                                st.error("Failed to delete observation.")

            # Subtab 3: Discussions
            with mod_tabs[2]:
                if not all_posts:
                    st.caption("No community discussions yet.")
                for post in all_posts:
                    author = post.get("author") or {}
                    status_val = post.get("status")
                    with st.container(border=True):
                        st.caption(f"{author.get('display_name', 'Member')} &bull; Status: {status_val.upper() if status_val else 'PUBLISHED'} &bull; {post.get('created_at', '')}")
                        st.markdown(f"**{post.get('title', '')}**")
                        st.write(post.get("body", ""))
                        actions = ([("Restore", "restore"), ("Delete", "delete")] if status_val == "hidden" else [("Hide", "hide"), ("Delete", "delete")])
                        p_cols = st.columns(len(actions) + 2)
                        for col, (label, act) in zip(p_cols[:len(actions)], actions):
                            if col.button(label, key=f"post_act_{post.get('id')}_{act}"):
                                res = api_client.moderate_community_content({
                                    "target_kind": "post",
                                    "target_id": post["id"],
                                    "action": act,
                                })
                                if res:
                                    st.success(f"Post {act}d.")
                                    st.rerun()
                                else:
                                    st.error("Action failed.")

            # Subtab 4: Farmer Accounts
            with mod_tabs[3]:
                if not comm_accounts:
                    st.caption("No registered farmer community accounts yet.")
                for c_acc in comm_accounts:
                    with st.container(border=True):
                        c_info, c_action = st.columns([4, 1.2])
                        is_active = bool(c_acc.get("is_active"))
                        with c_info:
                            st.markdown(f"**{c_acc.get('display_name')}** &bull; {c_acc.get('email')} &bull; Role: `{c_acc.get('role', 'farmer')}` &bull; Status: `{'ACTIVE' if is_active else 'DISABLED'}`")
                        with c_action:
                            target_state = not is_active
                            label = "Enable" if target_state else "Disable"
                            if st.button(label, key=f"toggle_comm_acc_{c_acc.get('id')}", use_container_width=True):
                                res = api_client.set_community_account_active(str(c_acc.get("id")), target_state)
                                if res:
                                    st.success(res.get("message", "Status updated."))
                                    st.rerun()
                                else:
                                    st.error("Failed to update account status.")

    except requests.exceptions.RequestException as e:
        logger.error("Network error in admin view: %s", e)
        render_error_page("network", str(e))
    except Exception as e:
        logger.error("Unexpected error in admin view: %s", e, exc_info=True)
        render_error_page("system", str(e))
