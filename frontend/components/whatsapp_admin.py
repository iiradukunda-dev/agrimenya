"""
WhatsApp Administration Component — Agrimenya Executive Command Center.

Provides full lifecycle management for WhatsApp operations:
1. Gateway Status & 7-Day Transmission Insights (Mock Sandbox vs Meta Cloud API)
2. Subscriber Directory & Onboarding (Search, Filter, Register, Role & Crops)
3. Meta Compliance, Consent Governance & Alert Subscriptions
4. Pre-Approved Meta Templates & Interactive Live Smartphone Simulator
5. Broadcast Dispatch Center & Real-Time 5-Stage Delivery Telemetry
"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
try:
    import pandas as pd
except ImportError:
    pd = None
import streamlit as st

from components.icons import render_icon_subheader
from utils import api_client

CAT_TZ = ZoneInfo("Africa/Kigali")

def safe_dialog(title: str, width: str = "large"):
    """Creates a Streamlit @st.dialog with graceful fallback in headless/test environments."""
    def decorator(func):
        try:
            dlg = st.dialog(title, width=width)(func)
            def wrapper(*args, **kwargs):
                try:
                    return dlg(*args, **kwargs)
                except Exception:
                    return func(*args, **kwargs)
            return wrapper
        except Exception:
            return func
    return decorator



def _format_cat_timestamp(iso_str: str | None) -> str:
    """Format an ISO timestamp into Central Africa Time (CAT, UTC+2)."""
    if not iso_str:
        return "Not available"
    try:
        clean_str = str(iso_str).replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        cat_dt = dt.astimezone(CAT_TZ)
        return cat_dt.strftime("%d %b %Y, %H:%M CAT")
    except Exception:
        return str(iso_str)[:19]


def render_whatsapp_admin_panel(key_prefix: str = "wa_mgmt", embedded_mode: bool = False):
    """
    Renders the complete, clear WhatsApp Administration interface.
    
    Args:
        key_prefix: Unique key prefix for Streamlit state widgets.
        embedded_mode: If True, renders compact view without full page headers.
    """
    if not embedded_mode:
        render_icon_subheader("assets/message.svg", "WhatsApp Gateway & Broadcast Command Center")

    # Explanatory Architecture Banner
    st.html(
        """
        <div style="padding:14px 18px; border-radius:12px; background:linear-gradient(135deg, #ffffff 0%, #f0fdf4 100%); border:1.5px solid rgba(16, 185, 129, 0.35); border-top:3px solid #10b981; box-shadow:0 4px 14px rgba(16, 185, 129, 0.08); margin-bottom:1.2rem;">
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:4px;">
                <strong style="color:#065f46; font-size:1.05rem;">Agrimenya WhatsApp Operations & Advisory Dispatch Engine</strong>
            </div>
            <p style="margin:0; font-size:0.9rem; color:#334155; line-height:1.45;">
                Manage verified farmer contacts, record mandatory Meta opt-in consent, simulate template messages, and broadcast localized agricultural alerts with live delivery tracking.
            </p>
        </div>
        """
    )

    # 5 Structured Operational Subtabs
    wa_subtabs = st.tabs([
        "Gateway Health & Telemetry",
        "Subscriber Directory & Onboarding",
        "Consent & Alert Preferences",
        "Meta Templates & Live Simulator",
        "Broadcast Dispatch & Delivery Tracker",
    ])

    # ═════════════════════════════════════════════════════════════
    # SUBTAB 1: Gateway Health & Telemetry
    # ═════════════════════════════════════════════════════════════
    with wa_subtabs[0]:
        _render_gateway_health(key_prefix)

    # ═════════════════════════════════════════════════════════════
    # SUBTAB 2: Subscriber Directory & Onboarding
    # ═════════════════════════════════════════════════════════════
    with wa_subtabs[1]:
        _render_subscribers_directory(key_prefix)

    # ═════════════════════════════════════════════════════════════
    # SUBTAB 3: Consent & Alert Preferences
    # ═════════════════════════════════════════════════════════════
    with wa_subtabs[2]:
        _render_consent_and_preferences(key_prefix)

    # ═════════════════════════════════════════════════════════════
    # SUBTAB 4: Meta Templates & Live Simulator
    # ═════════════════════════════════════════════════════════════
    with wa_subtabs[3]:
        _render_templates_simulator(key_prefix)

    # ═════════════════════════════════════════════════════════════
    # SUBTAB 5: Broadcast Dispatch & Delivery Tracker
    # ═════════════════════════════════════════════════════════════
    with wa_subtabs[4]:
        _render_broadcast_tracker(key_prefix)


# ─────────────────────────────────────────────────────────────
# 1. Gateway Health & Telemetry
# ─────────────────────────────────────────────────────────────
def _render_gateway_health(prefix: str):
    health = api_client.get_whatsapp_health()
    stats = api_client.get_whatsapp_stats()

    if not health:
        st.warning("WhatsApp Gateway status is currently unavailable from the backend API. Please ensure the backend is running.")
        return

    mode = str(health.get("mode", "mock")).lower()
    is_live = mode == "live" or mode == "meta_cloud_api"
    approved_templates = int(health.get("approved_templates") or 0)
    failed_24h = int(health.get("failed_messages_24h") or 0)
    last_webhook = health.get("last_webhook_received_at")

    # Mode Indicator
    mode_color = "#38bdf8" if is_live else "#eab308"
    mode_label = "LIVE META CLOUD API" if is_live else "MOCK SANDBOX MODE (SAFE TESTING)"
    mode_desc = (
        "Connected to official Meta WhatsApp Cloud API. Real messages are sent to registered phone numbers."
        if is_live else
        "Operating in safe mock sandbox. Outbound messages are recorded to the database without incurring WhatsApp messaging charges or requiring live Meta credentials."
    )

    st.markdown(
        f"""
        <div style="padding:10px 16px; border-radius:10px; background:rgba(15, 23, 42, 0.6); border:1px solid {mode_color}55; margin-bottom:1rem;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:700; color:{mode_color}; letter-spacing:0.05em; font-size:0.9rem;">
                    GATEWAY STATUS: {mode_label}
                </span>
                <span style="font-size:0.8rem; color:#94a3b8;">Central Africa Time (CAT UTC+2)</span>
            </div>
            <p style="margin:4px 0 0 0; font-size:0.85rem; color:#334155;">{mode_desc}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 4 Executive Metric Cards
    kpi_cols = st.columns(4)
    with kpi_cols[0]:
        st.metric("Provider Runtime", "Meta Cloud" if is_live else "Mock Local")
    with kpi_cols[1]:
        st.metric("Approved Meta Templates", approved_templates)
    with kpi_cols[2]:
        st.metric("Failed Messages (24h)", failed_24h, delta=f"{failed_24h} failed" if failed_24h else "Normal", delta_color="inverse")
    with kpi_cols[3]:
        st.metric("Last Webhook Heartbeat", "Active" if last_webhook else "Awaiting Ping")

    if last_webhook:
        st.caption(f"Last incoming WhatsApp webhook recorded: {_format_cat_timestamp(last_webhook)}")

    st.write("---")

    # 7-Day Performance Stats
    st.markdown("**7-Day Message Transmission Telemetry**")
    if stats:
        days = stats.get("days", 7)
        by_status = stats.get("by_status") or {}
        by_kind = stats.get("by_kind") or {}
        top_errors = stats.get("top_error_codes") or {}

        # Status distribution cards
        stat_cols = st.columns(5)
        with stat_cols[0]:
            st.metric("Total Queued", by_status.get("queued", 0))
        with stat_cols[1]:
            st.metric("Dispatched (Sent)", by_status.get("sent", 0))
        with stat_cols[2]:
            st.metric("Delivered to Handset", by_status.get("delivered", 0))
        with stat_cols[3]:
            st.metric("Read by Farmers", by_status.get("read", 0))
        with stat_cols[4]:
            st.metric("Transmission Failures", by_status.get("failed", 0))

        # Secondary telemetry breakdown
        col_kind, col_err = st.columns([1, 1], gap="medium")
        with col_kind:
            with st.container(border=True):
                st.markdown("**Messages by Operational Category**")
                if by_kind:
                    kind_rows = [
                        {"Category": k.replace("_", " ").title(), "Count": v}
                        for k, v in by_kind.items()
                    ]
                    st.dataframe(pd.DataFrame(kind_rows) if pd is not None else kind_rows, width="stretch", hide_index=True)
                else:
                    st.caption("No categorised messages in the last 7 days.")

        with col_err:
            with st.container(border=True):
                st.markdown("**Top Provider Error Codes**")
                if top_errors:
                    err_rows = [
                        {"Error Code": str(k), "Occurrences": v, "Description": _explain_wa_error(str(k))}
                        for k, v in top_errors.items()
                    ]
                    st.dataframe(pd.DataFrame(err_rows) if pd is not None else err_rows, width="stretch", hide_index=True)
                else:
                    st.success("Zero delivery error codes recorded in the last 7 days.")
    else:
        st.caption("No telemetry logs accumulated in the 7-day observation window.")


def _explain_wa_error(code: str) -> str:
    explanations = {
        "131026": "Message undeliverable (phone inactive or unverified)",
        "131047": "24-hour customer service window closed; template required",
        "131051": "Requested template does not exist or is not approved",
        "130429": "Rate limit exceeded (sending too fast)",
        "131000": "Generic WhatsApp Cloud API provider error",
    }
    return explanations.get(code, "Provider status or network code")


# ─────────────────────────────────────────────────────────────
# 2. Subscribers Directory & Onboarding
# ─────────────────────────────────────────────────────────────
@safe_dialog("Onboard WhatsApp Subscriber", width="large")
def _show_onboard_dialog(prefix: str):
    st.html(
        """
        <div style="padding:10px 14px; border-radius:8px; background:rgba(2, 132, 199, 0.08); border:1px solid rgba(2, 132, 199, 0.25); margin-bottom:1rem; font-size:0.88rem; color:#0f172a;">
            <strong>Onboarding Requirement:</strong> Registering creates the subscriber profile. To receive automated broadcasts, the contact must provide explicit opt-in consent (recordable in the 'Consent & Alert Preferences' tab).
        </div>
        """
    )

    with st.form(f"{prefix}_create_subscriber_dlg_form", clear_on_submit=True):
        c_name, c_phone = st.columns(2)
        with c_name:
            display_name = st.text_input("Full Name / Cooperative Name", placeholder="e.g. Habimana Jean Pierre")
        with c_phone:
            phone = st.text_input("Phone Number", placeholder="0788123456 or +250788123456")

        c_bsuid, c_role = st.columns(2)
        with c_bsuid:
            bsuid = st.text_input("WhatsApp BSUID (Optional for bot users)", placeholder="Optional Bot Specific User ID")
        with c_role:
            role = st.selectbox(
                "Role in Agriculture Value Chain",
                ["farmer", "extension_officer", "cooperative_leader", "planner", "other"],
                format_func=lambda r: r.replace("_", " ").title(),
            )

        c_lang, c_crops = st.columns(2)
        with c_lang:
            language = st.selectbox("Preferred Communication Language", ["en", "rw"], format_func=lambda l: "Kinyarwanda (RW)" if l == "rw" else "English (EN)")
        with c_crops:
            crops = st.text_input("Target Crops (Comma-separated)", placeholder="e.g. Maize, Beans, Irish Potatoes")

        # Zone Selection
        zones = api_client.get_zones() or []
        zone_options = {"National / Unassigned": None}
        for z in zones:
            z_id = z.get("id")
            if not z_id:
                continue
            label = f"{z.get('district', 'Unknown')} · {z.get('sector') or z.get('cell') or 'General'} ({z.get('crop') or 'All'})"
            zone_options[label] = str(z_id)

        chosen_zone_label = st.selectbox("Agricultural Zone Assignment", list(zone_options.keys()))
        chosen_zone_id = zone_options.get(chosen_zone_label)

        submit_contact = st.form_submit_button("Register WhatsApp Subscriber", type="primary")

        if submit_contact:
            if not phone.strip() and not bsuid.strip():
                st.error("Please provide at least a Phone Number or WhatsApp BSUID.")
            else:
                crop_list = [c.strip() for c in crops.split(",") if c.strip()]
                payload = {
                    "display_name": display_name.strip() or None,
                    "phone": phone.strip() or None,
                    "bsuid": bsuid.strip() or None,
                    "role": role,
                    "language": language,
                    "zone_id": chosen_zone_id,
                    "crops": crop_list,
                }
                result = api_client.create_whatsapp_contact(payload)
                if result:
                    st.success(f"Successfully registered subscriber '{display_name or phone}'!")
                    st.rerun()
                else:
                    st.error("Failed to register contact. Ensure phone number is valid and not already registered.")


def _render_subscribers_directory(prefix: str):
    st.markdown("### WhatsApp Farmer & Extension Directory")
    st.caption("Centralised registry of verified farmers, cooperative leaders, and agronomists receiving Agri-Menya advisory messages.")

    contacts = api_client.get_whatsapp_contacts()
    active_contacts = [c for c in contacts if not c.get("deleted_at")] if contacts else []

    c_sub_hdr, c_sub_act = st.columns([3, 1.4])
    with c_sub_hdr:
        st.markdown("#### Subscriber Directory")
    with c_sub_act:
        if st.button("Onboard New Subscriber", key=f"{prefix}_open_onboard_btn", type="primary", use_container_width=True):
            _show_onboard_dialog(prefix)

    st.write("")

    # Search & Filter Controls
    f_col1, f_col2, f_col3 = st.columns([2, 1, 1])
    with f_col1:
        search_query = st.text_input("Search subscribers by Name, Phone, or Crops", key=f"{prefix}_search_input", placeholder="Filter contacts...")
    with f_col2:
        consent_filter = st.selectbox("Consent Filter", ["All Contacts", "Opted In (Active)", "Consent Pending"], key=f"{prefix}_consent_filter")
    with f_col3:
        role_filter = st.selectbox("Role Filter", ["All Roles", "Farmer", "Extension Officer", "Cooperative Leader", "Planner"], key=f"{prefix}_role_filter")

    # Filter contacts
    filtered = list(active_contacts)
    if isinstance(search_query, str) and search_query.strip():
        q = search_query.lower()
        filtered = [
            c for c in filtered
            if q in str(c.get("display_name", "")).lower()
            or q in str(c.get("phone_masked", "")).lower()
            or any(q in str(crop).lower() for crop in (c.get("crops") or []))
        ]

    if isinstance(consent_filter, str):
        if consent_filter == "Opted In (Active)":
            filtered = [c for c in filtered if c.get("whatsapp_opt_in")]
        elif consent_filter == "Consent Pending":
            filtered = [c for c in filtered if not c.get("whatsapp_opt_in")]

    if isinstance(role_filter, str) and role_filter != "All Roles":
        target_role = role_filter.lower().replace(" ", "_")
        filtered = [c for c in filtered if c.get("role") == target_role]

    st.caption(f"Displaying {len(filtered)} of {len(active_contacts)} total active subscribers.")

    if filtered:
        rows = []
        for c in filtered:
            opt_in = c.get("whatsapp_opt_in", False)
            rows.append({
                "ID": str(c.get("id"))[-8:],
                "Name": c.get("display_name") or "Unnamed Farmer",
                "Role": (c.get("role") or "farmer").replace("_", " ").title(),
                "Phone": c.get("phone_masked") or (f"BSUID: {c.get('bsuid')}" if c.get('bsuid') else "No phone"),
                "Language": "Kinyarwanda" if c.get("language") == "rw" else "English",
                "Crops": ", ".join(c.get("crops") or []) or "All",
                "Consent Status": "OPTED IN" if opt_in else "PENDING",
                "Opt-In Date": _format_cat_timestamp(c.get("opt_in_at")) if opt_in else "Not Recorded",
            })
        st.dataframe(pd.DataFrame(rows) if pd is not None else rows, width="stretch", hide_index=True)
    else:
        st.info("No subscribers match your search filter criteria.")


# ─────────────────────────────────────────────────────────────
# 3. Consent & Alert Preferences
# ─────────────────────────────────────────────────────────────
def _render_consent_and_preferences(prefix: str):
    st.markdown("### Meta Compliance, Opt-In Consent & Subscription Routing")

    st.markdown(
        """
        <div style="padding:12px 18px; border-radius:12px; background:linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border:1px solid rgba(2, 132, 199, 0.25); margin-bottom:1.2rem; color:#0f172a;">
            <strong>Meta Business Messaging Rule:</strong>
            To protect users from unsolicited messages, automated WhatsApp broadcasts can ONLY be dispatched to contacts with documented, verifiable opt-in consent.
            Subscribers can also specify which agricultural zones and crop severity levels they want to be notified about.
        </div>
        """,
        unsafe_allow_html=True,
    )

    contacts = api_client.get_whatsapp_contacts()
    active_contacts = [c for c in contacts if not c.get("deleted_at")] if contacts else []

    if not active_contacts:
        st.info("No subscribers registered yet. Please register subscribers in the 'Subscriber Directory & Onboarding' tab first.")
        return

    # Select Subscriber
    contact_labels = {
        f"{c.get('display_name') or 'Unnamed'} | {c.get('phone_masked') or 'BSUID'} | {'Opted In' if c.get('whatsapp_opt_in') else 'Pending Consent'} | ID: {str(c.get('id'))[-6:]}": c
        for c in active_contacts
    }

    selected_label = st.selectbox("Select Subscriber to Manage", list(contact_labels.keys()), key=f"{prefix}_subscriber_choice")
    chosen_contact = contact_labels.get(selected_label) or (next(iter(contact_labels.values())) if contact_labels else {})
    contact_id = str(chosen_contact.get("id", ""))
    has_opt_in = bool(chosen_contact.get("whatsapp_opt_in"))

    col_consent, col_prefs = st.columns([1, 1], gap="medium")

    # --- Left: Opt-In Consent Governance ---
    with col_consent:
        with st.container(border=True):
            st.markdown("#### 1. Meta Opt-In Consent Status")

            if has_opt_in:
                st.markdown(
                    f"""
                    <div style="padding:12px 16px; border-radius:8px; background:#f0fdf4; border:1px solid #16a34a; margin-bottom:1rem;">
                        <div style="display:flex; align-items:center; gap:8px;">
                            <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:#16a34a;"></span>
                            <strong style="color:#166534;">Active Opt-In Consent on File</strong>
                        </div>
                        <p style="margin:6px 0 0 0; font-size:0.85rem; color:#1e293b;">
                            Source: <strong>{chosen_contact.get('opt_in_source') or 'Verified In-Person'}</strong><br/>
                            Version: <code>{chosen_contact.get('opt_in_text_version') or 'v1.0'}</code><br/>
                            Recorded: {_format_cat_timestamp(chosen_contact.get('opt_in_at'))}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.caption("This subscriber is legally cleared to receive outbound WhatsApp weather advisories and agricultural alerts.")
            else:
                st.markdown(
                    """
                    <div style="padding:12px 16px; border-radius:8px; background:#fffbeb; border:1px solid #d97706; margin-bottom:1rem;">
                        <div style="display:flex; align-items:center; gap:8px;">
                            <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:#d97706;"></span>
                            <strong style="color:#92400e;">Consent Pending (Broadcasts Blocked)</strong>
                        </div>
                        <p style="margin:6px 0 0 0; font-size:0.85rem; color:#1e293b;">
                            This contact has not yet confirmed formal opt-in consent. Meta policies prohibit dispatching automated notifications until consent is certified.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.markdown("**Record Formal Opt-In Verification**")
                with st.form(f"{prefix}_record_consent_form_{contact_id}"):
                    consent_source = st.selectbox(
                        "Opt-In Verification Source",
                        [
                            "In-Person Cooperative Registration",
                            "Paper Consent Form (Signed)",
                            "Inbound WhatsApp Command (START)",
                            "SMS Text Request",
                            "Agricultural Extension Outreach",
                        ]
                    )
                    consent_version = st.text_input("Consent Policy Version", value="agrimenya-opt-in-v1.0")
                    submit_optin = st.form_submit_button("Record Legal Consent & Activate", type="primary")

                if submit_optin:
                    res = api_client.opt_in_whatsapp_contact(contact_id, consent_source.strip(), consent_version.strip())
                    if res:
                        st.success(f"Consent successfully recorded for {chosen_contact.get('display_name') or 'contact'}. Subscriber is now active!")
                        st.rerun()
                    else:
                        st.error("Failed to record consent. Please check administrative permissions.")

    # --- Right: Alert Routing Preferences ---
    with col_prefs:
        with st.container(border=True):
            st.markdown("#### 2. Alert Routing & Preferences")
            st.caption("Configure which advisories this subscriber receives based on geographic zone, crop interest, and hazard severity.")

            zones = api_client.get_zones() or []
            zone_options = {"All National Zones (Broadcast All)": None}
            for z in zones:
                z_id = z.get("id")
                if not z_id:
                    continue
                label = f"{z.get('district', 'Unknown')} · {z.get('sector') or z.get('cell') or 'General'} ({z.get('crop') or 'All'})"
                zone_options[label] = str(z_id)

            with st.form(f"{prefix}_save_sub_prefs_{contact_id}"):
                sub_zone_label = st.selectbox("Subscribed Agricultural Zone", list(zone_options.keys()))
                sub_crop = st.text_input("Specific Crop Filter (Leave empty for all crops)", value=", ".join(chosen_contact.get("crops") or []))
                sub_min_sev = st.selectbox("Minimum Alert Severity Threshold", ["info", "warning", "critical"], index=1, format_func=lambda s: s.upper())
                save_prefs_btn = st.form_submit_button("Save Subscription Routing", type="primary")

            if save_prefs_btn:
                chosen_zone_uuid = zone_options.get(sub_zone_label)
                sub_payload = {
                    "zone_id": chosen_zone_uuid,
                    "crop": sub_crop.strip() or None,
                    "min_severity": sub_min_sev,
                }
                sub_res = api_client.subscribe_whatsapp_contact(contact_id, sub_payload)
                if sub_res:
                    st.success("Alert preferences saved successfully!")
                else:
                    st.error("Could not save preferences. Check administrative permissions.")

    # Danger Zone: Remove Contact
    st.write("")
    with st.popover("Remove Subscriber"):
        st.warning(f"Deactivating '{chosen_contact.get('display_name') or 'this subscriber'}' will permanently stop all future WhatsApp advisories.")
        if st.button("Permanently Deactivate Subscriber", key=f"{prefix}_del_btn_{contact_id}", type="secondary"):
            if api_client.remove_whatsapp_contact(contact_id):
                st.success("Subscriber deactivated.")
                st.rerun()
            else:
                st.error("Failed to deactivate subscriber.")


# ─────────────────────────────────────────────────────────────
# 4. Meta Templates & Live Simulator
# ─────────────────────────────────────────────────────────────
def _render_templates_simulator(prefix: str):
    st.markdown("### Pre-Approved Meta WhatsApp Templates & Interactive Live Simulator")
    st.caption("Meta requires all business-initiated messages outside the 24-hour service window to use pre-approved templates.")

    templates = api_client.get_whatsapp_templates()

    if not templates:
        st.warning("No pre-approved WhatsApp templates retrieved from the backend. Ensure Meta Cloud templates are configured.")
        return

    # Templates Catalog
    st.markdown("**Official Approved Message Templates**")
    tmpl_rows = [
        {
            "Template Name": t.get("name"),
            "Language": "Kinyarwanda (RW)" if t.get("language") == "rw" else "English (EN)",
            "Category": str(t.get("category", "UTILITY")).upper(),
            "Required Parameters": t.get("param_count", 0),
            "Status": "APPROVED" if t.get("status") == "APPROVED" or not t.get("status") else str(t.get("status")).upper(),
        }
        for t in templates
    ]
    st.dataframe(pd.DataFrame(tmpl_rows) if pd is not None else tmpl_rows, width="stretch", hide_index=True)

    st.write("---")

    # Live Simulator Section
    st.markdown("#### Interactive WhatsApp Smartphone Simulator")
    st.caption("Test how dynamic alert parameters render inside real WhatsApp chat bubbles before initiating a national broadcast.")

    template_options = {
        f"{t.get('name')} ({'Kinyarwanda' if t.get('language') == 'rw' else 'English'})": t
        for t in templates
    }
    selected_t_label = st.selectbox("Select Template to Simulate", list(template_options.keys()), key=f"{prefix}_sim_template_choice")
    selected_template = template_options.get(selected_t_label) or (next(iter(template_options.values())) if template_options else {})
    t_name = str(selected_template.get("name", ""))
    t_lang = str(selected_template.get("language", "en"))
    param_count = int(selected_template.get("param_count") or 0)

    sim_col_inputs, sim_col_phone = st.columns([1, 1], gap="large")

    param_values = []
    with sim_col_inputs:
        with st.container(border=True):
            st.markdown(f"**Template Parameters ({param_count} required)**")

            # Contextual parameter helper labels
            param_labels = [
                "{{1}} Alert Headline / Title (e.g. Heavy Rain Advisory)",
                "{{2}} Hazard Severity Level (e.g. WARNING)",
                "{{3}} District / Target Region (e.g. Musanze District)",
                "{{4}} Recommended Action for Farmers (e.g. Clear drainage trenches)",
                "{{5}} Secondary Recommendation / Date",
                "{{6}} Contact Hotline / Extension Office",
            ]

            defaults = [
                "Imvura Nyamwinshi n'Umuyaga",
                "INTEGUZA IKOMEYE",
                "Akarere ka Musanze",
                "Hutira gusibura imiferege y'amazi no kurinda imyaka",
                "Kigali Weather Advisory",
                "MINAGRI Extension Hotline 114",
            ]

            for i in range(param_count):
                lbl = param_labels[i] if i < len(param_labels) else f"Parameter {{{{{i+1}}}}}"
                d_val = defaults[i] if i < len(defaults) else f"Value {i+1}"
                val = st.text_input(lbl, value=d_val, key=f"{prefix}_param_{t_name}_{t_lang}_{i}")
                param_values.append(val.strip())

            preview_clicked = st.button("Render WhatsApp Mobile Preview", type="primary", key=f"{prefix}_render_btn")

    with sim_col_phone:
        # Call live preview API
        rendered_text = None
        if preview_clicked or True:
            preview_res = api_client.preview_whatsapp_template(t_name, t_lang, param_values)
            if preview_res:
                rendered_text = preview_res.get("body_preview")

        if not rendered_text:
            rendered_text = "Select parameters on the left and click 'Render WhatsApp Mobile Preview' to inspect the simulated bubble."

        # WhatsApp Bubble
        current_time_str = datetime.now(CAT_TZ).strftime("%H:%M")
        bubble_html = rendered_text.replace("\n", "<br/>")

        st.html(
            f"""
            <div style="max-width:380px; margin:0 auto; border-radius:28px; background:#0B141A; border:4px solid #1F2C34; box-shadow:0 12px 36px rgba(0,0,0,0.4); overflow:hidden; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
                <!-- WhatsApp Top Bar -->
                <div style="background:#1F2C34; padding:12px 16px; display:flex; align-items:center; gap:12px; border-bottom:1px solid rgba(255,255,255,0.08);">
                    <div style="width:38px; height:38px; border-radius:50%; background:#25D366; display:flex; align-items:center; justify-content:center; font-size:1.1rem; color:#fff; font-weight:700;">
                        AM
                    </div>
                    <div>
                        <div style="color:#E9EDEF; font-weight:600; font-size:0.95rem; display:flex; align-items:center; gap:4px;">
                            Agri-Menya Verified
                        </div>
                        <div style="color:#8696A0; font-size:0.75rem;">Official Ministry Alert System</div>
                    </div>
                </div>
                <!-- Chat Area -->
                <div style="background:#0B141A; min-height:280px; padding:16px; background-image:radial-gradient(rgba(255,255,255,0.03) 1px, transparent 1px); background-size:16px 16px;">
                    <div style="background:#005C4B; color:#E9EDEF; padding:10px 14px; border-radius:8px 8px 8px 0; max-width:88%; font-size:0.88rem; line-height:1.4; box-shadow:0 2px 4px rgba(0,0,0,0.3); margin-top:10px;">
                        <div>{bubble_html}</div>
                        <div style="display:flex; justify-content:flex-end; align-items:center; gap:4px; margin-top:6px; font-size:0.7rem; color:#8696A0;">
                            <span>{current_time_str}</span>
                        </div>
                    </div>
                </div>
            </div>
            """
        )


# ─────────────────────────────────────────────────────────────
# 5. Broadcast Dispatch & Delivery Tracker
# ─────────────────────────────────────────────────────────────
def _render_broadcast_tracker(prefix: str):
    st.markdown("### WhatsApp Advisory Broadcast & Real-Time Delivery Tracker")
    st.caption("Review draft agricultural alerts, certify them for WhatsApp delivery, and monitor transmission status across farmer devices.")

    admin_alerts = api_client.get_admin_alerts()

    if not admin_alerts:
        st.info("No active alerts found in the system. Compose a new alert in the 'Alert Management' tab to begin.")
        return

    alert_options = {
        f"[{str(a.get('severity', 'Info')).upper()}] {str(a.get('message', ''))[:60]}... (ID: {str(a.get('id'))[-6:]})": a
        for a in admin_alerts if a.get("id")
    }

    selected_alert_title = st.selectbox("Select Alert for WhatsApp Broadcast & Telemetry", list(alert_options.keys()), key=f"{prefix}_alert_choice")
    alert = alert_options.get(selected_alert_title) or (next(iter(alert_options.values())) if alert_options else {})
    alert_id = str(alert.get("id", ""))
    alert_status = str(alert.get("status", "draft")).lower()
    is_approved = alert_status == "approved"

    # Executive Alert Card
    with st.container(border=True):
        st.markdown(f"**Full Alert Message:**\n> {alert.get('message', '')}")
        m_c1, m_c2, m_c3, m_c4 = st.columns(4)
        with m_c1:
            st.caption("Hazard Severity")
            sev = alert.get("severity", "Info")
            sev_color = "#ef4444" if sev.lower() == "critical" else ("#f59e0b" if sev.lower() == "warning" else "#38bdf8")
            st.markdown(f"<strong style='color:{sev_color};'>{sev.upper()}</strong>", unsafe_allow_html=True)
        with m_c2:
            st.caption("Crop Target")
            st.write(alert.get("crop") or "National (All Crops)")
        with m_c3:
            st.caption("WhatsApp Approval Status")
            st.markdown("**APPROVED**" if is_approved else "**DRAFT (REQUIRES APPROVAL)**")
        with m_c4:
            st.caption("Certified By")
            st.write(alert.get("approved_by") or "Pending Review")

        st.write("---")

        # Two-Step Operational Workflow
        st.markdown("#### 1. Dispatch Operations")
        if not is_approved:
            st.info("Step 1: Review the alert text above. When verified, click 'Certify & Approve Alert for WhatsApp' to unlock delivery.")
            if st.button("Certify & Approve Alert for WhatsApp Broadcast", key=f"{prefix}_approve_btn_{alert_id}", type="primary", use_container_width=True):
                res = api_client.approve_whatsapp_alert(alert_id)
                if res:
                    st.success("Alert certified and approved for WhatsApp dispatch!")
                    st.rerun()
                else:
                    st.error(api_client.get_admin_api_error(f"/communication/alerts/{alert_id}/approve") or "Approval failed.")
        else:
            st.success(f"Approved for WhatsApp broadcast on {_format_cat_timestamp(alert.get('approved_at'))}")

            b_c1, b_c2 = st.columns([2, 1])
            with b_c1:
                st.markdown(
                    """
                    <div style="font-size:0.88rem; color:#334155; margin-bottom:8px;">
                        Clicking broadcast will match all registered subscribers with active opt-in consent whose zone, crop, and severity settings align with this alert.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with b_c2:
                dispatch_clicked = st.button("Dispatch WhatsApp Broadcast", key=f"{prefix}_dispatch_btn_{alert_id}", type="primary", use_container_width=True)

            if dispatch_clicked:
                summary = api_client.dispatch_whatsapp_alert(alert_id)
                if summary is not None:
                    queued = summary.get("queued", 0)
                    failed = summary.get("failed", 0)
                    no_consent = summary.get("skipped_no_consent", 0)
                    daily_cap = summary.get("skipped_daily_cap", 0)
                    no_tmpl = summary.get("skipped_no_template", 0)

                    if queued > 0:
                        st.success(f"Broadcast Dispatched! {queued} message(s) successfully queued for transmission.")
                    if no_consent > 0 or daily_cap > 0:
                        st.info(f"Broadcast filters applied: {no_consent} contact(s) skipped without consent, {daily_cap} contact(s) reached daily rate cap.")
                    if no_tmpl > 0:
                        st.warning(f"{no_tmpl} contact(s) skipped because no approved Meta template matched the recipient language.")
                    if failed > 0:
                        st.error(f"{failed} message(s) encountered provider transmission errors.")
                    st.rerun()
                else:
                    st.error(api_client.get_admin_api_error(f"/communication/alerts/{alert_id}/dispatch/whatsapp") or "Dispatch request failed.")

    # Real-Time 5-Stage Delivery Telemetry
    st.write("")
    st.markdown("#### 2. Real-Time 5-Stage Delivery Telemetry")
    delivery_data = api_client.get_whatsapp_delivery(alert_id)

    if delivery_data and "counts" in delivery_data:
        counts = delivery_data.get("counts", {})
        q_count = int(counts.get("queued") or 0)
        s_count = int(counts.get("sent") or 0)
        d_count = int(counts.get("delivered") or 0)
        r_count = int(counts.get("read") or 0)
        f_count = int(counts.get("failed") or 0)

        total_dispatched = q_count + s_count + d_count + r_count + f_count

        # 5-Stage Telemetry KPI Row
        d_cols = st.columns(5)
        with d_cols[0]:
            st.metric("1. Queued in Gateway", q_count)
        with d_cols[1]:
            st.metric("2. Dispatched (Sent)", s_count)
        with d_cols[2]:
            st.metric("3. Handset Delivered", d_count)
        with d_cols[3]:
            st.metric("4. Read by Farmers", r_count)
        with d_cols[4]:
            st.metric("5. Failed Deliveries", f_count, delta=f"{f_count} failed" if f_count else None, delta_color="inverse")

        # Visual Delivery Funnel Progress
        if total_dispatched > 0:
            success_rate = ((d_count + r_count) / total_dispatched) * 100
            st.progress(min(1.0, (d_count + r_count) / total_dispatched), text=f"Handset Delivery & Read Rate: {success_rate:.1f}% ({d_count + r_count}/{total_dispatched} recipients)")
        else:
            st.caption("No deliveries dispatched yet for this alert. Click 'Dispatch WhatsApp Broadcast' above to initiate broadcast.")
    else:
        st.caption("Delivery telemetry is currently not recorded for this alert.")
