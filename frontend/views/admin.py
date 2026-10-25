"""
Admin view: operations, governance, and system health.

Implements Page 7 of the frontend handoff: zone/plan/alert management + health.
"""
import logging

import pandas as pd
import requests
import streamlit as st
from components.errors import render_error_page
from components.icons import render_icon_subheader, render_icon_title
from utils import api_client
from utils.i18n import t

logger = logging.getLogger(__name__)


def render_admin() -> None:
    try:
        if not api_client.render_admin_login("admin_panel"):
            return
        render_icon_title(
            "assets/compass.svg",
            t("admin.title", "Admin Panel"),
            t("admin.subtitle", "System operations, zone management, and health monitoring"),
        )

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
        # TAB 1: System Health
        # ═════════════════════════════════════════════════════════════
        with admin_tabs[0]:
            render_icon_subheader("assets/compass.svg", "System Health")

            health = api_client.get_health()
            if health:
                status = health.get("status", "unknown")

                h_cols = st.columns(5)
                with h_cols[0]:
                    st.metric("API service", status.upper())
                with h_cols[1]:
                    st.metric("Database", str(health.get("database_status", "unknown")).upper())
                model_present = health.get("model_present", False)
                with h_cols[2]:
                    st.metric("Environment", health.get("env", "N/A"))
                with h_cols[3]:
                    yield_source = health.get("yield_source") or ("Trained model" if model_present else "Unavailable")
                    if "database" in str(yield_source).casefold():
                        source_label = "Database"
                    elif "model" in str(yield_source).casefold():
                        source_label = "Model"
                    else:
                        source_label = "Unavailable"
                    st.metric("Yield source", source_label)
                    st.caption(str(yield_source))
                with h_cols[4]:
                    baselines_present = health.get("baselines_present", False)
                    st.metric("Yield baselines", "Loaded" if baselines_present else "Unavailable")

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
                st.dataframe(df, width="stretch", hide_index=True)
                st.caption(f"{len(admin_zones)} zones registered.")
                zone_labels = {
                    f"{z.get('district') or 'Unknown district'} / {z.get('sector') or z.get('cell') or 'Area not set'} | {str(z.get('id'))[-8:]}": z
                    for z in admin_zones if z.get("id")
                }
                with st.expander("Edit zone details"):
                    if zone_labels:
                        label = st.selectbox("Zone", list(zone_labels), key="admin_zone_edit")
                        zone = zone_labels[label]
                        zone_id = str(zone["id"])
                        with st.form(f"admin_zone_form_{zone_id}"):
                            left, right = st.columns(2)
                            with left:
                                district = st.text_input("District", value=str(zone.get("district") or ""))
                                sector = st.text_input("Sector", value=str(zone.get("sector") or ""))
                                cell = st.text_input("Cell", value=str(zone.get("cell") or ""))
                                crop = st.text_input("Crop", value=str(zone.get("crop_type") or ""))
                            with right:
                                season = st.text_input("Season", value=str(zone.get("season") or ""))
                                latitude = st.number_input("Latitude", min_value=-90.0, max_value=90.0, value=float(zone["latitude"]) if zone.get("latitude") is not None else None, format="%.6f")
                                longitude = st.number_input("Longitude", min_value=-180.0, max_value=180.0, value=float(zone["longitude"]) if zone.get("longitude") is not None else None, format="%.6f")
                            update_zone = st.form_submit_button("Save zone details", type="primary")
                        if update_zone:
                            if not district.strip():
                                st.error("A zone must have a district.")
                            else:
                                payload = {
                                    "district": district.strip(), "sector": sector.strip() or None,
                                    "cell": cell.strip() or None, "crop_type": crop.strip() or None,
                                    "season": season.strip() or None,
                                }
                                if latitude is not None:
                                    payload["latitude"] = latitude
                                if longitude is not None:
                                    payload["longitude"] = longitude
                                result = api_client.update_admin_zone(zone_id, payload)
                                if result:
                                    st.success("Zone updated.")
                                    st.rerun()
                                else:
                                    st.error("Zone update failed. Check admin access and the entered values.")
                    else:
                        st.info("No editable zones are available.")
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
            render_icon_subheader("assets/calendar.svg", "Plan Management")

            admin_plans = api_client.get_admin_plans()
            if admin_plans:
                df = pd.DataFrame(admin_plans)
                st.dataframe(df, width="stretch", hide_index=True)
                st.caption(f"{len(admin_plans)} plans found.")
                plan_labels = {
                    f"{p.get('title') or 'Untitled plan'} | {str(p.get('id'))[-8:]}": p
                    for p in admin_plans if p.get("id")
                }
                with st.expander("Rename a plan"):
                    if plan_labels:
                        label = st.selectbox("Plan", list(plan_labels), key="admin_plan_edit")
                        plan = plan_labels[label]
                        plan_id = str(plan["id"])
                        with st.form(f"admin_plan_form_{plan_id}"):
                            title = st.text_input("Plan title", value=str(plan.get("title") or ""))
                            update_plan = st.form_submit_button("Save plan title", type="primary")
                        if update_plan:
                            if not title.strip():
                                st.error("Enter a plan title.")
                            elif api_client.update_admin_plan(plan_id, {"title": title.strip()}):
                                st.success("Plan title updated.")
                                st.rerun()
                            else:
                                st.error("Plan update failed. Check admin access.")
            else:
                error = api_client.get_admin_api_error("/admin/plans")
                if error:
                    st.error(f"Plan management could not load: {error}")
                else:
                    st.info("No plans available. Plans are created through the Planning page.")

        # ═════════════════════════════════════════════════════════════
        # TAB 4: Alert Management
        # ═════════════════════════════════════════════════════════════
        with admin_tabs[3]:
            render_icon_subheader("assets/bell.svg", "Alert Management")

            zones = api_client.get_admin_zones()
            zone_options = {
                f"{z.get('district', 'Unknown district')} / {z.get('sector') or z.get('cell') or str(z.get('id', ''))[-8:]}": z.get("id")
                for z in zones if z.get("id")
            }
            st.caption("A sent alert is emailed to every active Farmer Community account. No recipient selection is needed. SMTP acceptance confirms handoff, not inbox delivery. WhatsApp delivery is a separate, consent-based admin action.")
            if zone_options:
                with st.form("admin_community_alert_create", clear_on_submit=True):
                    selected_zone = st.selectbox("Alert area", list(zone_options))
                    severity = st.selectbox("Severity", ["Info", "Warning", "Critical"])
                    message = st.text_area("Alert message", max_chars=2000, height=130)
                    crop = st.text_input("Crop (optional)", max_chars=80)
                    action = st.text_input("Recommended action (optional)", max_chars=500)
                    create_alert = st.form_submit_button("Send alert to all farmer accounts", type="primary")
                if create_alert:
                    if not message.strip():
                        st.error("Enter the alert message.")
                    else:
                        result = api_client.send_admin_alert({
                            "zone_id": zone_options[selected_zone], "severity": severity,
                            "message": message.strip(), "crop": crop.strip() or None,
                            "action": action.strip() or None,
                        })
                        if result:
                            delivery = result.get("email_delivery") or {}
                            sent = int(delivery.get("sent") or 0)
                            total = int(delivery.get("recipients") or 0)
                            failed = int(delivery.get("failed") or 0)
                            if delivery.get("status") == "sent":
                                st.success(f"Alert created; SMTP accepted delivery for all {sent} active farmer accounts.")
                            elif sent:
                                st.warning(f"Alert created; SMTP accepted delivery for {sent} of {total} accounts, with {failed} failures.")
                            elif delivery.get("status") == "no_recipients":
                                st.warning("Alert created, but there are no active Farmer Community email accounts yet.")
                            else:
                                st.warning(f"Alert created, but no emails were delivered ({failed} failed). {delivery.get('reason', 'Check SMTP settings and backend logs.')}")
                        else:
                            st.error(api_client.get_admin_api_error("/communication/alerts") or "Alert could not be created.")
            else:
                zone_error = api_client.get_admin_api_error("/admin/zones")
                st.error(zone_error or "Add a zone before creating an alert.")

            admin_alerts = api_client.get_admin_alerts()
            if admin_alerts:
                df = pd.DataFrame(admin_alerts)
                st.dataframe(df, width="stretch", hide_index=True)
                st.caption(f"{len(admin_alerts)} alerts found.")
                alert_labels = {
                    f"{a.get('severity') or 'Info'} / {str(a.get('message') or '')[:70]} | {str(a.get('id'))[-8:]}": a
                    for a in admin_alerts if a.get("id")
                }
                with st.expander("Edit an alert"):
                    if alert_labels:
                        label = st.selectbox("Alert", list(alert_labels), key="admin_alert_edit")
                        alert = alert_labels[label]
                        alert_id = str(alert["id"])
                        with st.form(f"admin_alert_form_{alert_id}"):
                            message = st.text_area("Message", value=str(alert.get("message") or ""), max_chars=2000)
                            severity = st.selectbox("Severity", ["Info", "Warning", "Critical"], index=["Info", "Warning", "Critical"].index(alert.get("severity", "Info")) if alert.get("severity", "Info") in ["Info", "Warning", "Critical"] else 0)
                            update_alert = st.form_submit_button("Save alert", type="primary")
                        st.caption("Saving changes resets approval. The edited alert must be reviewed again before WhatsApp dispatch.")
                        if update_alert:
                            if not message.strip():
                                st.error("Enter an alert message.")
                            elif api_client.update_admin_alert(alert_id, {"message": message.strip(), "severity": severity}):
                                st.success("Alert updated and returned to draft review.")
                                st.rerun()
                            else:
                                st.error("Alert update failed. Check admin access and message validation.")
            else:
                error = api_client.get_admin_api_error("/admin/alerts")
                if error:
                    st.error(f"Alert management could not load: {error}")
                else:
                    st.info("No alerts are available for management.")

        with admin_tabs[4]:
            render_icon_subheader("assets/compass.svg", "NISR Dataset Imports")
            st.markdown(
                "Upload one released NISR district-by-crop yield table at a time. "
                "Imports are validated, tied to their release and season, and recorded in the database."
            )
            example_csv = (
                "district,crop,season,yield_kg_ha,production_mt,cultivated_area_ha\n"
                "Gasabo,Maize,2026 Season C,2200,4.4,2.0\n"
            )
            st.download_button(
                "Download CSV format example",
                data=example_csv,
                file_name="nisr_yield_import_example.csv",
                mime="text/csv",
            )
            st.caption(
                "Required columns: district, crop, season, yield_kg_ha. "
                "production_mt and cultivated_area_ha are optional. Use the exact season label on every row, "
                "for example ‘2026 Season C’. Accepted districts are Rwanda’s 30 districts."
            )
            with st.form("nisr_release_import", clear_on_submit=True):
                source_release = st.text_input("NISR release title or reference", placeholder="Seasonal Agricultural Survey: Season C, 2026")
                season_label = st.text_input("Release season", placeholder="2026 Season C")
                nisr_file = st.file_uploader("NISR CSV", type=["csv"], key="nisr_csv_upload")
                import_clicked = st.form_submit_button("Validate and import release", type="primary")
            if import_clicked:
                if not source_release.strip() or not season_label.strip() or nisr_file is None:
                    st.error("Provide the release title, season, and CSV file.")
                else:
                    result = api_client.upload_nisr_release(
                        nisr_file.name, nisr_file.getvalue(), source_release.strip(), season_label.strip()
                    )
                    if result:
                        st.success(
                            f"Imported {result.get('rows_imported', 0)} observations for "
                            f"{result.get('season')} from {result.get('source_release')}."
                        )
                        st.rerun()
                    else:
                        detail = api_client.get_admin_api_error("/admin/nisr/imports")
                        st.error(f"NISR import failed: {detail or 'the API did not return an explanation.'}")

            imports = api_client.get_nisr_imports()
            if imports:
                st.markdown("**Import history**")
                st.dataframe(
                    [{
                        "Release": item.get("source_release"),
                        "Season": item.get("season"),
                        "File": item.get("source_filename"),
                        "Rows": item.get("row_count"),
                        "Status": item.get("status"),
                        "Imported": item.get("created_at"),
                    } for item in imports],
                    width="stretch",
                    hide_index=True,
                )
            elif api_client.get_admin_api_error("/admin/nisr/imports"):
                st.error(f"NISR import history could not load: {api_client.get_admin_api_error('/admin/nisr/imports')}")
            else:
                st.caption("No NISR releases have been imported through this panel yet.")

        with admin_tabs[5]:
            render_icon_subheader("assets/compass.svg", "Administrator Accounts")
            st.caption("Invite named administrators by email. Each invite link expires after 30 minutes and can be used once.")
            with st.form("admin_account_invite", clear_on_submit=True):
                invite_name = st.text_input("Administrator name")
                invite_email = st.text_input("Work email")
                invite_clicked = st.form_submit_button("Send administrator invitation", type="primary")
            if invite_clicked:
                if not invite_name.strip() or not invite_email.strip():
                    st.error("Enter the administrator’s name and email.")
                else:
                    invitation = api_client.invite_admin_account(invite_email.strip(), invite_name.strip())
                    if invitation:
                        st.success(f"Invitation sent to {invitation.get('email')}.")
                        st.rerun()
                    else:
                        st.error(api_client.get_admin_api_error("/auth/admin/accounts") or "Invitation failed.")

            accounts = api_client.get_admin_accounts()
            if accounts:
                st.dataframe(accounts, width="stretch", hide_index=True)
                current_admin_id = str(st.session_state.get("admin_identity", {}).get("id", ""))
                manageable_accounts = [a for a in accounts if str(a.get("id")) != current_admin_id]
                for account in manageable_accounts:
                    label = f"{account.get('display_name')} · {account.get('email')}"
                    with st.container(border=True):
                        status_col, action_col = st.columns([3, 1])
                        status_col.write(f"{label}: {'Active' if account.get('is_active') else 'Disabled'}")
                        target_active = not bool(account.get("is_active"))
                        action = "Restore access" if target_active else "Disable account"
                        if action_col.button(action, key=f"admin_account_{account.get('id')}"):
                            result = api_client.set_admin_account_active(str(account.get("id")), target_active)
                            if result:
                                st.success(result.get("message", "Administrator access updated."))
                                st.rerun()
                            else:
                                path = f"/auth/admin/accounts/{account.get('id')}/status"
                                st.error(api_client.get_admin_api_error(path) or "Could not update administrator access.")
            elif api_client.get_admin_api_error("/auth/admin/accounts"):
                st.error(f"Administrator accounts could not load: {api_client.get_admin_api_error('/auth/admin/accounts')}")
            else:
                st.info("No administrator accounts are available.")

        with admin_tabs[6]:
            render_icon_subheader("assets/compass.svg", "Community Moderation")
            st.caption("Review reported posts and comments. Hidden content is removed from the public feed.")
            accounts = api_client.get_community_accounts()
            with st.expander(f"Community accounts ({len(accounts)})"):
                for account in accounts:
                    access_col, toggle_col = st.columns([4, 1])
                    access_col.text(
                        f"{account.get('display_name')} · {account.get('email')} · "
                        f"{account.get('role')} · {'Active' if account.get('is_active') else 'Disabled'}"
                    )
                    next_active = not bool(account.get("is_active"))
                    if toggle_col.button(
                        "Enable" if next_active else "Disable",
                        key=f"community_account_{account.get('id')}",
                    ):
                        result = api_client.set_community_account_active(str(account.get("id")), next_active)
                        if result:
                            st.success(result.get("message", "Account status updated."))
                            st.rerun()
                        else:
                            path = f"/community/moderation/accounts/{account.get('id')}/status"
                            st.error(api_client.get_admin_api_error(path) or "Account status could not be updated.")
            all_posts = api_client.get_community_moderation_posts()
            post_load_error = api_client.get_admin_api_error("/community/moderation/posts")
            if post_load_error:
                st.error(post_load_error)
            with st.expander(f"Community posts ({len(all_posts)})"):
                for post in all_posts:
                    author = post.get("author") or {}
                    with st.container(border=True):
                        st.caption(f"{author.get('display_name', 'unknown member')} · {post.get('status')} · {post.get('created_at', '')}")
                        st.write(post.get("title", ""))
                        st.write(post.get("body", ""))
                        actions = ([('Restore', 'restore'), ('Delete', 'delete')] if post.get("status") == "hidden"
                                   else [('Hide', 'hide'), ('Delete', 'delete')])
                        action_cols = st.columns(len(actions))
                        for col, (label, action) in zip(action_cols, actions):
                            if col.button(label, key=f"community_post_{post.get('id')}_{action}"):
                                result = api_client.moderate_community_content({
                                    "target_kind": "post", "target_id": post["id"], "action": action,
                                })
                                if result:
                                    success_message = {"hide": "Post hidden.", "restore": "Post restored.", "delete": "Post deleted."}[action]
                                    st.success(success_message)
                                    st.rerun()
                                else:
                                    st.error(api_client.get_admin_api_error("/community/moderation") or f"Post could not be {action}d.")
            field_reports = api_client.get_community_moderation_field_reports()
            field_report_error = api_client.get_admin_api_error("/community/moderation/field-reports")
            if field_report_error:
                st.error(field_report_error)
            with st.expander(f"Farmer field observations ({len(field_reports)})"):
                for report in field_reports:
                    reporter = report.get("reporter") or {}
                    with st.container(border=True):
                        st.caption(f"{report.get('crop', '')} · {report.get('district', '')} · {report.get('observed_on', '')} · {reporter.get('display_name', 'unknown member')}")
                        st.write(report.get("symptoms") or report.get("notes") or "No note provided")
                        if report.get("photo_url"):
                            st.image(report["photo_url"], width=320)
                        if st.button("Delete field observation", key=f"community_report_delete_{report.get('id')}"):
                            result = api_client.delete_community_field_report(str(report["id"]))
                            if result:
                                st.success("Field observation deleted.")
                                st.rerun()
                            else:
                                st.error(api_client.get_admin_api_error(f"/community/moderation/field-reports/{report.get('id')}") or "Field observation could not be deleted.")
            reports = api_client.get_community_moderation_reports()
            if not reports:
                error = api_client.get_admin_api_error("/community/moderation/reports")
                st.error(error) if error else st.info("There are no open community reports.")
            for report in reports:
                target_kind = "comment" if report.get("comment_id") else "post"
                target = report.get(target_kind) or {}
                author = target.get("author") or {}
                with st.container(border=True):
                    st.text(f"Report: {report.get('reason', '')}")
                    st.text(f"{target_kind.title()} by {author.get('display_name', 'unknown member')} · {report.get('created_at', '')}")
                    if target_kind == "post":
                        st.text(target.get("title", "Post"))
                    st.text(target.get("body", ""))
                    buttons = st.columns([1, 1, 1, 2])
                    actions = [("Hide content", "hide"), ("Delete content", "delete"), ("Dismiss report", "dismiss")]
                    for column, (label, action) in zip(buttons[:3], actions):
                        if column.button(label, key=f"community_mod_{report['id']}_{action}"):
                            payload = {
                                "target_kind": target_kind,
                                "target_id": report.get("comment_id") or report.get("post_id"),
                                "action": action,
                                "report_id": report["id"],
                                "report_action": "dismissed" if action == "dismiss" else "resolved",
                            }
                            result = api_client.moderate_community_content(payload)
                            if result:
                                st.success(result.get("message", "Moderation saved."))
                                st.rerun()
                            else:
                                st.error(api_client.get_admin_api_error("/community/moderation") or "Moderation could not be saved.")

    except requests.exceptions.RequestException as e:
        logger.error("Network error in admin view: %s", e)
        render_error_page("network", str(e))
    except Exception as e:
        logger.error("Unexpected error in admin view: %s", e, exc_info=True)
        render_error_page("system", str(e))
