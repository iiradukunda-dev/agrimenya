"""Creative, animated workflow cards with rich micro-motions for the agrimenya frontend."""
import os
from contextlib import contextmanager
from typing import Any

import requests
import streamlit as st


def pillar_card(
    col,
    title: str,
    desc: str,
    btn_text: str,
    page_route: str,
    icon: str = "",
    tag: str = "WORKFLOW",
    accent_color: str = "#10b981",
) -> None:
    """Render an interactive, animated workflow card with fluid micro-motions."""
    with col:
        with st.container(border=True):
            icon_markup = (
                icon
                if icon
                else f"""<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{accent_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 14 14"></polyline></svg>"""
            )
            html_block = f"""
            <style>
            @keyframes ag-badge-pulse {{
                0%, 100% {{ transform: scale(1); box-shadow: 0 2px 8px {accent_color}25; }}
                50% {{ transform: scale(1.06); box-shadow: 0 0 16px {accent_color}55; }}
            }}
            .ag-workflow-icon-wrap {{
                width: 44px;
                height: 44px;
                border-radius: 12px;
                background: linear-gradient(135deg, {accent_color}25 0%, {accent_color}10 100%);
                border: 1.5px solid {accent_color}55;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 4px 14px {accent_color}30, inset 0 1px 1px rgba(255, 255, 255, 0.45);
                transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.35s cubic-bezier(0.16, 1, 0.3, 1), background 0.3s ease;
                will-change: transform, box-shadow;
            }}
            [data-testid="stVerticalBlockBorderWrapper"]:hover .ag-workflow-icon-wrap {{
                transform: translateY(-5px) scale(1.12) rotate(-4deg);
                box-shadow: 0 12px 26px {accent_color}55, inset 0 1px 2px rgba(255, 255, 255, 0.7);
                border-color: {accent_color}90;
            }}
            [data-testid="stVerticalBlockBorderWrapper"]:active .ag-workflow-icon-wrap {{
                transform: translateY(-1px) scale(1.02);
            }}
            .ag-workflow-tag {{
                font-size: 0.7rem;
                font-weight: 750;
                letter-spacing: 0.06em;
                text-transform: uppercase;
                color: {accent_color};
                background: {accent_color}22;
                padding: 3px 10px;
                border-radius: 9999px;
                border: 1px solid {accent_color}50;
                box-shadow: 0 2px 8px {accent_color}20;
                transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.35s ease, border-color 0.3s ease;
            }}
            [data-testid="stVerticalBlockBorderWrapper"]:hover .ag-workflow-tag {{
                transform: scale(1.05);
                box-shadow: 0 4px 14px {accent_color}45;
                border-color: {accent_color}90;
                animation: ag-badge-pulse 2s infinite ease-in-out;
            }}
            </style>
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.75rem;">
                <div class="ag-workflow-icon-wrap">{icon_markup}</div>
                <span class="ag-workflow-tag">{tag}</span>
            </div>
            <h3 style="margin:0.2rem 0 0.45rem;font-family:'Plus Jakarta Sans',sans-serif;font-size:1.15rem;font-weight:750;color:#ffffff;letter-spacing:-0.02em;text-shadow:0 2px 8px rgba(0,0,0,0.7);transition:color 0.25s ease;">{title}</h3>
            <p style="color:#e0f2fe;font-size:0.88rem;line-height:1.55;min-height:42px;margin:0 0 0.85rem;text-shadow:0 1px 6px rgba(0,0,0,0.7);">{desc}</p>
            """
            st.markdown(html_block, unsafe_allow_html=True)
            if st.button(f"{btn_text} →", key=f"btn_{page_route}", width="stretch"):
                st.switch_page(page_route)


def login_card_header(
    title: str,
    subtitle: str,
    badge_text: str = "SECURITY PROTOCOL",
    icon: str = "",
    accent_color: str = "#0284c7",
) -> None:
    """Render an executive header for authentication and login cards."""
    default_icon = f"""<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="{accent_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
        <rect x="9" y="9" width="6" height="5" rx="1"/>
        <path d="M10 9V7a2 2 0 0 1 4 0v2"/>
    </svg>"""
    icon_markup = icon if icon else default_icon

    html = f"""
    <div style="text-align: left; margin-bottom: 0.5rem;">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.85rem;">
            <div class="ag-login-icon-box" style="
                width: 48px;
                height: 48px;
                border-radius: 13px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(135deg, {accent_color}28 0%, {accent_color}12 100%);
                border: 1.5px solid {accent_color}60;
                box-shadow: 0 6px 18px {accent_color}35, inset 0 1px 1px rgba(255, 255, 255, 0.45);
            ">{icon_markup}</div>
            <span style="
                display: inline-flex;
                align-items: center;
                gap: 6px;
                font-family: 'Plus Jakarta Sans', sans-serif;
                font-size: 0.72rem;
                font-weight: 750;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                padding: 4px 12px;
                border-radius: 9999px;
                border: 1px solid {accent_color}55;
                background: {accent_color}18;
                color: {accent_color};
                box-shadow: 0 2px 10px {accent_color}22;
            ">
                <span style="
                    width: 7px;
                    height: 7px;
                    border-radius: 50%;
                    background: {accent_color};
                    box-shadow: 0 0 8px {accent_color};
                "></span>
                {badge_text}
            </span>
        </div>
        <h2 style="
            margin: 0.2rem 0 0.35rem 0 !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            font-size: 1.45rem !important;
            font-weight: 800 !important;
            color: #ffffff !important;
            letter-spacing: -0.025em !important;
            text-shadow: 0 2px 10px rgba(0, 0, 0, 0.7) !important;
        ">{title}</h2>
        <p style="
            color: #cbe5f5 !important;
            font-size: 0.88rem !important;
            line-height: 1.55 !important;
            margin: 0 0 0.65rem 0 !important;
            text-shadow: 0 1px 4px rgba(0, 0, 0, 0.6) !important;
        ">{subtitle}</p>
        <div style="
            height: 1px;
            width: 100%;
            background: linear-gradient(90deg, transparent 0%, {accent_color}66 50%, transparent 100%);
            margin: 0.7rem 0 1.15rem 0;
        "></div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def security_trust_footer(
    message: str = "256-bit TLS encrypted",
    session_info: str = "Role-based access control",
) -> None:
    """Render a reassuring trust badge at the bottom of an authentication card."""
    html = f"""
    <div style="
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        margin-top: 1.1rem;
        padding-top: 0.85rem;
        border-top: 1px solid rgba(56, 189, 248, 0.18);
        color: #94a3b8;
        font-size: 0.76rem;
        font-weight: 550;
        letter-spacing: 0.01em;
        text-align: center;
    ">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
        </svg>
        <span style="color: #cbd5e1;">{message}</span>
        <span style="color: rgba(56, 189, 248, 0.45);">•</span>
        <span style="color: #94a3b8;">{session_info}</span>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def authenticated_session_badge(
    display_name: str,
    email: str = "",
    role: str = "Administrator",
    key_prefix: str = "auth",
) -> bool:
    """Render an executive authenticated session card with user identity and sign-out action.
    Returns True if sign-out was clicked."""
    initials = (display_name[:2] if len(display_name) >= 2 else "AD").upper()
    html = f"""
    <div style="
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.95rem 1.25rem;
        margin-bottom: 1.2rem;
        border-radius: 14px;
        background: linear-gradient(135deg, rgba(8, 26, 38, 0.95) 0%, rgba(12, 36, 53, 0.95) 100%);
        border: 1px solid rgba(56, 189, 248, 0.35);
        border-top: 1.5px solid rgba(56, 189, 248, 0.6);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
    ">
        <div style="display: flex; align-items: center; gap: 14px;">
            <div style="
                width: 44px;
                height: 44px;
                border-radius: 12px;
                background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                color: #ffffff;
                font-family: 'Plus Jakarta Sans', sans-serif;
                font-weight: 800;
                font-size: 1rem;
                box-shadow: 0 4px 12px rgba(14, 165, 233, 0.35);
                letter-spacing: 0.04em;
            ">{initials}</div>
            <div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="
                        font-family: 'Plus Jakarta Sans', sans-serif;
                        font-weight: 750;
                        font-size: 0.98rem;
                        color: #ffffff;
                    ">{display_name}</span>
                    <span style="
                        display: inline-flex;
                        align-items: center;
                        gap: 4px;
                        font-size: 0.68rem;
                        font-weight: 750;
                        text-transform: uppercase;
                        letter-spacing: 0.05em;
                        color: #4ade80;
                        background: rgba(74, 222, 128, 0.15);
                        border: 1px solid rgba(74, 222, 128, 0.35);
                        padding: 2px 8px;
                        border-radius: 9999px;
                    ">
                        <span style="width: 5px; height: 5px; border-radius: 50%; background: #4ade80; box-shadow: 0 0 6px #4ade80;"></span>
                        {role}
                    </span>
                </div>
                <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 2px;">
                    {email if email else 'Authenticated session'} <span style="color: rgba(56, 189, 248, 0.4);">•</span> <span style="color: #38bdf8;">Active (30m refresh)</span>
                </div>
            </div>
        </div>
    </div>
    """
    col_info, col_btn = st.columns([4, 1.2])
    with col_info:
        st.markdown(html, unsafe_allow_html=True)
    with col_btn:
        st.write("")
        st.write("")
        return st.button("Sign out", key=f"{key_prefix}_signout_btn", width="stretch")


@contextmanager
def centralized_login_container(max_width: int = 460):
    """Render a responsive, horizontally centered Liquid Glass container
    tailored for authentication cards across all screen resolutions."""
    st.markdown(
        f"""
        <style>
        .st-key-ag_centralized_login_col {{
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            width: 100% !important;
            margin: 0.75rem auto 2.2rem auto !important;
        }}
        .st-key-ag_centralized_login_col [data-testid="stVerticalBlockBorderWrapper"] {{
            max-width: {max_width}px !important;
            width: 100% !important;
            margin: 0 auto !important;
            border-radius: 18px !important;
            background: linear-gradient(135deg, rgba(8, 26, 38, 0.94) 0%, rgba(5, 18, 27, 0.96) 100%) !important;
            border: 1px solid rgba(56, 189, 248, 0.28) !important;
            border-top: 1.5px solid rgba(56, 189, 248, 0.6) !important;
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.45), 0 0 1px rgba(255, 255, 255, 0.12) !important;
            backdrop-filter: blur(18px) !important;
            -webkit-backdrop-filter: blur(18px) !important;
            padding: 1.25rem 1.45rem !important;
        }}
        @media (max-width: 768px) {{
            .st-key-ag_centralized_login_col [data-testid="stVerticalBlockBorderWrapper"] {{
                max-width: 100% !important;
                padding: 1rem 1rem !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    col_l, col_center, col_r = st.columns([1, 1.35, 1])
    with col_center:
        with st.container(key="ag_centralized_login_col"):
            with st.container(border=True):
                yield


def render_centralized_login_card(
    portal: str = "unified",
    key_prefix: str = "auth",
    title: str | None = None,
    subtitle: str | None = None,
) -> bool:
    """Render a unified, executive centralized login card for agrimenya.

    Parameters:
      portal: 'admin' (Administrator login), 'community' (Grower network login),
              or 'unified' (Interactive dual-role switcher).
      key_prefix: Unique widget prefix to avoid state collisions.
      title: Optional custom header title.
      subtitle: Optional custom header subtitle.

    Returns:
      True if an active authenticated session exists, False otherwise.
    """
    from utils import api_client

    api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")

    # 1. Handle query parameter reset token (administrator password recovery)
    reset_token = st.query_params.get("reset_token")
    if reset_token:
        with centralized_login_container():
            login_card_header(
                title="Reset Password",
                subtitle="Set a new secure password for your administrator account.",
                badge_text="SECURITY RECOVERY",
                accent_color="#0284c7",
            )
            with st.form(f"{key_prefix}_reset_form"):
                password = st.text_input(
                    "New password (12 characters minimum)",
                    type="password",
                    placeholder="Min. 12 characters",
                    key=f"{key_prefix}_new_password",
                )
                confirmation = st.text_input(
                    "Confirm new password",
                    type="password",
                    placeholder="Re-enter password",
                    key=f"{key_prefix}_confirm_password",
                )
                submit = st.form_submit_button("Update Password →", type="primary", use_container_width=True)
            if submit:
                if len(password) < 12:
                    st.error("Use at least 12 characters for your password.")
                elif password != confirmation:
                    st.error("The passwords do not match.")
                else:
                    result = api_client.reset_admin_password(reset_token, password)
                    if result:
                        st.success("Password updated. Sign in with your new password.")
                        st.query_params.clear()
                        st.rerun()
                    else:
                        st.error(api_client.get_admin_api_error("/auth/admin/password/reset") or "This reset link is invalid or expired.")
            security_trust_footer()
        return False

    # 2. Check for active authenticated admin session
    if portal in ("admin", "unified") and api_client.admin_session_authenticated():
        identity = st.session_state.get("admin_identity", {})
        display_name = str(identity.get("display_name") or identity.get("email") or "Administrator")
        email = str(identity.get("email") or "")
        if authenticated_session_badge(display_name=display_name, email=email, role="System Administrator", key_prefix=f"{key_prefix}_admin"):
            st.session_state.pop("admin_session_expires_at", None)
            st.session_state.pop("admin_access_token", None)
            st.session_state.pop("admin_identity", None)
            st.rerun()
        if portal == "admin":
            return True

    # 3. Check for active authenticated community session
    if portal in ("community", "unified") and st.session_state.get("community_access_token"):
        account = st.session_state.get("community_account", {})
        display_name = str(account.get("display_name") or "Community Member")
        email = str(account.get("email") or "")
        if authenticated_session_badge(display_name=display_name, email=email, role="Grower Network", key_prefix=f"{key_prefix}_comm"):
            st.session_state.pop("community_access_token", None)
            st.session_state.pop("community_account", None)
            st.rerun()
        if portal == "community":
            return True

    if portal == "unified" and (api_client.admin_session_authenticated() or st.session_state.get("community_access_token")):
        return True

    # 4. Render Centralized Login Card
    with centralized_login_container():
        if portal == "admin":
            default_title = "Administrator Portal"
            default_subtitle = "Sign in with authorized credentials to access zone management, NISR data ingestion, and system controls."
            login_card_header(
                title=title or default_title,
                subtitle=subtitle or default_subtitle,
                badge_text="SECURITY PROTOCOL",
                accent_color="#0284c7",
            )
            login_error = st.session_state.pop("admin_login_error", None)
            if login_error:
                st.error(login_error)
            widget_key = f"{key_prefix}_password"
            with st.form(f"{key_prefix}_admin_login_form"):
                st.text_input(
                    "Administrator email",
                    placeholder="admin@agrimenya.rw",
                    key=f"{key_prefix}_email",
                )
                st.text_input(
                    "Password",
                    type="password",
                    placeholder="••••••••••••",
                    key=widget_key,
                )
                st.form_submit_button(
                    "Authenticate Session →",
                    type="primary",
                    use_container_width=True,
                    on_click=api_client._authenticate_admin_session,
                    args=(widget_key,),
                )
            with st.expander("Forgot your administrator password?"):
                with st.form(f"{key_prefix}_forgot_form"):
                    forgot_email = st.text_input(
                        "Administrator email",
                        placeholder="admin@agrimenya.rw",
                        key=f"{key_prefix}_forgot_email",
                    )
                    forgot = st.form_submit_button("Send reset link →", use_container_width=True)
                if forgot:
                    if api_client.request_admin_password_reset(forgot_email):
                        st.success("If an active account matches that email, reset instructions will be sent.")
                    else:
                        st.error(api_client.get_admin_api_error("/auth/admin/password/forgot") or "Could not request password reset.")
            st.markdown(
                '<div style="text-align:center;margin-top:0.75rem;font-size:0.82rem;color:#94a3b8;">Farmer or cooperative member? <a href="/Community" style="color:#34d399;font-weight:700;text-decoration:none;">Go to Community Portal →</a></div>',
                unsafe_allow_html=True,
            )
            security_trust_footer(
                message="256-bit TLS encrypted session",
                session_info="30-minute auto-expiry timeout",
            )
            return api_client.admin_session_authenticated()

        elif portal == "community":
            sprout_icon = """<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#34d399" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M7 20h10"/>
                <path d="M10 20c0-4 1-6 2-10"/>
                <path d="M12 10a4 4 0 0 1 7-3 4 4 0 0 1-3 7 4 4 0 0 1-4-4z"/>
                <path d="M12 14a4 4 0 0 0-7-3 4 4 0 0 0 3 7 4 4 0 0 0 4-4z"/>
            </svg>"""
            login_card_header(
                title=title or "Grower Network",
                subtitle=subtitle or "Connect with peer farmers, report field pest sightings, and share localized knowledge.",
                badge_text="COMMUNITY NETWORK",
                icon=sprout_icon,
                accent_color="#10b981",
            )
            tab_signin, tab_create = st.tabs(["Sign In", "Create Account"])
            with tab_signin:
                with st.form(f"{key_prefix}_comm_signin"):
                    comm_email = st.text_input("Email", placeholder="farmer@cooperative.rw", key=f"{key_prefix}_comm_login_email")
                    comm_pw = st.text_input("Password", type="password", placeholder="••••••••••••", key=f"{key_prefix}_comm_login_password")
                    comm_sub = st.form_submit_button("Sign In →", type="primary", use_container_width=True)
                if comm_sub:
                    try:
                        resp = requests.post(f"{api_base_url}/community/login", json={"email": comm_email, "password": comm_pw}, timeout=15)
                        resp.raise_for_status()
                        res_data = resp.json()
                        st.session_state["community_access_token"] = res_data["access_token"]
                        st.session_state["community_account"] = res_data.get("account", {})
                        st.rerun()
                    except requests.RequestException:
                        st.error("Sign-in failed. Please verify your email and password.")
            with tab_create:
                with st.form(f"{key_prefix}_comm_register"):
                    reg_name = st.text_input("Full Name or Handle", placeholder="e.g. Jean_Gasabo", max_chars=80)
                    reg_email = st.text_input("Email", placeholder="farmer@cooperative.rw", key=f"{key_prefix}_comm_reg_email")
                    reg_pw = st.text_input("Password (min. 12 characters)", type="password", placeholder="Min. 12 characters", key=f"{key_prefix}_comm_reg_pw")
                    reg_sub = st.form_submit_button("Create Grower Account →", type="primary", use_container_width=True)
                if reg_sub:
                    if len(reg_pw) < 12:
                        st.error("Password must contain at least 12 characters.")
                    else:
                        try:
                            resp = requests.post(
                                f"{api_base_url}/community/register",
                                json={"display_name": reg_name.strip(), "email": reg_email.strip(), "password": reg_pw},
                                timeout=15,
                            )
                            resp.raise_for_status()
                            res_data = resp.json()
                            st.session_state["community_access_token"] = res_data["access_token"]
                            st.session_state["community_account"] = res_data.get("account", {})
                            st.rerun()
                        except requests.RequestException:
                            st.error("Account creation failed. Please check that this email is not already registered.")
            st.markdown(
                '<div style="text-align:center;margin-top:0.75rem;font-size:0.82rem;color:#94a3b8;">Administrator or agronomist? <a href="/Admin" style="color:#38bdf8;font-weight:700;text-decoration:none;">Go to Administrator Portal →</a></div>',
                unsafe_allow_html=True,
            )
            security_trust_footer(message="Privacy Protected", session_info="Verified Grower Network")
            return bool(st.session_state.get("community_access_token"))

        else:
            # Unified mode: Dual-role switcher tab
            login_card_header(
                title=title or "agrimenya Portal Access",
                subtitle=subtitle or "Sign in with your credentials to access spatial intelligence, decisions, or the community grower network.",
                badge_text="SECURE ACCESS",
                accent_color="#0284c7",
            )
            tab_admin, tab_comm = st.tabs(["🛡️ Administrator & Officer", "🌾 Farmer Community"])
            with tab_admin:
                admin_error = st.session_state.pop("admin_login_error", None)
                if admin_error:
                    st.error(admin_error)
                widget_key = f"{key_prefix}_uni_admin_password"
                with st.form(f"{key_prefix}_uni_admin_form"):
                    st.text_input("Administrator email", placeholder="admin@agrimenya.rw", key=f"{key_prefix}_uni_admin_email")
                    st.text_input("Password", type="password", placeholder="••••••••••••", key=widget_key)
                    st.form_submit_button(
                        "Authenticate Admin Session →",
                        type="primary",
                        use_container_width=True,
                        on_click=api_client._authenticate_admin_session,
                        args=(widget_key,),
                    )
                with st.expander("Forgot your administrator password?"):
                    with st.form(f"{key_prefix}_uni_forgot_form"):
                        forgot_email = st.text_input("Administrator email", placeholder="admin@agrimenya.rw", key=f"{key_prefix}_uni_forgot_email")
                        forgot = st.form_submit_button("Send reset link →", use_container_width=True)
                    if forgot:
                        if api_client.request_admin_password_reset(forgot_email):
                            st.success("If an active account matches that email, reset instructions will be sent.")
                        else:
                            st.error(api_client.get_admin_api_error("/auth/admin/password/forgot") or "Could not request password reset.")
            with tab_comm:
                tab_in, tab_reg = st.tabs(["Sign In", "Create Account"])
                with tab_in:
                    with st.form(f"{key_prefix}_uni_comm_login"):
                        c_email = st.text_input("Email", placeholder="farmer@cooperative.rw", key=f"{key_prefix}_uni_c_email")
                        c_pw = st.text_input("Password", type="password", placeholder="••••••••••••", key=f"{key_prefix}_uni_c_pw")
                        c_sub = st.form_submit_button("Sign In to Community →", type="primary", use_container_width=True)
                    if c_sub:
                        try:
                            resp = requests.post(f"{api_base_url}/community/login", json={"email": c_email, "password": c_pw}, timeout=15)
                            resp.raise_for_status()
                            res_data = resp.json()
                            st.session_state["community_access_token"] = res_data["access_token"]
                            st.session_state["community_account"] = res_data.get("account", {})
                            st.rerun()
                        except requests.RequestException:
                            st.error("Sign-in failed. Please verify your email and password.")
                with tab_reg:
                    with st.form(f"{key_prefix}_uni_comm_reg"):
                        r_name = st.text_input("Full Name or Handle", placeholder="e.g. Jean_Gasabo", max_chars=80)
                        r_email = st.text_input("Email", placeholder="farmer@cooperative.rw", key=f"{key_prefix}_uni_r_email")
                        r_pw = st.text_input("Password (min. 12 characters)", type="password", placeholder="Min. 12 characters", key=f"{key_prefix}_uni_r_pw")
                        r_sub = st.form_submit_button("Create Account →", type="primary", use_container_width=True)
                    if r_sub:
                        if len(r_pw) < 12:
                            st.error("Password must contain at least 12 characters.")
                        else:
                            try:
                                resp = requests.post(
                                    f"{api_base_url}/community/register",
                                    json={"display_name": r_name.strip(), "email": r_email.strip(), "password": r_pw},
                                    timeout=15,
                                )
                                resp.raise_for_status()
                                res_data = resp.json()
                                st.session_state["community_access_token"] = res_data["access_token"]
                                st.session_state["community_account"] = res_data.get("account", {})
                                st.rerun()
                            except requests.RequestException:
                                st.error("Account creation failed. Please check that this email is not already registered.")
            security_trust_footer(message="256-bit TLS encrypted session", session_info="Unified Role-based Access Control")
            return api_client.admin_session_authenticated() or bool(st.session_state.get("community_access_token"))


