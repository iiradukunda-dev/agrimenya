"""Creative, animated workflow cards with rich micro-motions for the agrimenya frontend."""
import os
from contextlib import contextmanager
from typing import Any

import requests
import streamlit as st
from utils.api_client import request_api


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
                0%, 100% {{ transform: scale(1); box-shadow: 0 2px 8px rgba(2, 132, 199, 0.12); }}
                50% {{ transform: scale(1.04); box-shadow: 0 0 14px rgba(2, 132, 199, 0.22); }}
            }}
            .ag-workflow-icon-wrap {{
                box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06), inset 0 1px 1px rgba(255, 255, 255, 0.45);
                transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.35s cubic-bezier(0.16, 1, 0.3, 1), background 0.3s ease;
                will-change: transform, box-shadow;
            }}
            [data-testid="stVerticalBlockBorderWrapper"]:hover .ag-workflow-icon-wrap {{
                transform: translateY(-5px) scale(1.12) rotate(-4deg);
                box-shadow: 0 12px 26px rgba(15, 23, 42, 0.12), inset 0 1px 2px rgba(255, 255, 255, 0.7);
                border-color: var(--ag-primary);
            }}
            [data-testid="stVerticalBlockBorderWrapper"]:active .ag-workflow-icon-wrap {{
                transform: translateY(-1px) scale(1.02);
            }}
            .ag-workflow-tag {{
                font-size: 0.7rem;
                font-weight: 750;
                letter-spacing: 0.06em;
                text-transform: uppercase;
                color: var(--ag-primary);
                background: var(--ag-primary-soft);
                padding: 3px 10px;
                border-radius: 9999px;
                border: 1px solid var(--ag-card-border);
                box-shadow: none;
                transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.35s ease, border-color 0.3s ease;
            }}
            [data-testid="stVerticalBlockBorderWrapper"]:hover .ag-workflow-tag {{
                transform: scale(1.05);
                box-shadow: 0 4px 14px rgba(2, 132, 199, 0.14);
                border-color: var(--ag-primary);
                animation: ag-badge-pulse 2s infinite ease-in-out;
            }}
            </style>
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.75rem;">
                <div class="ag-icon-badge ag-workflow-icon-wrap">{icon_markup}</div>
                <span class="ag-workflow-tag">{tag}</span>
            </div>
            <h3 style="margin:0.2rem 0 0.45rem;font-family:'Plus Jakarta Sans',sans-serif;font-size:1.15rem;font-weight:800;color:#0f172a;letter-spacing:-0.02em;text-shadow:none;filter:none;-webkit-text-stroke:0;transition:color 0.25s ease;">{title}</h3>
            <p style="color:#334e5b;font-size:0.88rem;line-height:1.55;min-height:42px;margin:0 0 0.85rem;text-shadow:none;filter:none;opacity:1;">{desc}</p>
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
            <div class="ag-icon-badge ag-login-icon-box">{icon_markup}</div>
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
                border: 1px solid {accent_color}20;
                background: {accent_color}10;
                color: {accent_color};
                box-shadow: none;
            ">
                <span style="
                    width: 7px;
                    height: 7px;
                    border-radius: 50%;
                    background: {accent_color};
                    box-shadow: none;
                "></span>
                {badge_text}
            </span>
        </div>
        <h2 style="
            margin: 0.2rem 0 0.35rem 0 !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            font-size: 1.45rem !important;
            font-weight: 800 !important;
            color: #104b3b !important;
            letter-spacing: -0.025em !important;
            text-shadow: none !important;
        ">{title}</h2>
        <p style="
            color: #60766f !important;
            font-size: 0.88rem !important;
            line-height: 1.55 !important;
            margin: 0 0 0.65rem 0 !important;
            text-shadow: none !important;
        ">{subtitle}</p>
        <div style="
            height: 1px;
            width: 100%;
            background: #e7efeb;
            margin: 0.7rem 0 1rem 0;
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
        border-top: 1px solid #e7efeb;
        color: #70847c;
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
    """Show the matching signed-in card and return True when sign-out is clicked."""
    import html as html_lib

    safe_name = html_lib.escape(str(display_name or "Community member"))
    safe_email = html_lib.escape(str(email or "Authenticated session"))
    safe_role = html_lib.escape(str(role or "Member"))
    initials = html_lib.escape((str(display_name)[:2] if display_name else "AG").upper())
    style_key = f"st-key-{key_prefix}_authenticated_session_card"
    st.markdown(
        f"""
        <style>
        .{style_key} [data-testid="stVerticalBlockBorderWrapper"] {{
            max-width: 460px; margin: 0 auto 1.25rem auto; padding: 1.25rem 1.45rem;
            border: 1px solid #dce9e3; border-radius: 20px; background: #fff;
            box-shadow: 0 12px 32px rgba(17, 73, 55, 0.08);
        }}
        .{style_key} [data-testid="stButton"] button {{
            min-height: 2.8rem; border: 1px solid #cce2d8; border-radius: 11px;
            color: #087a55; background: #f5faf7; font-weight: 700;
        }}
        .{style_key} [data-testid="stButton"] button:hover {{
            border: 2px solid #0875d1; border-radius: 9999px;
            color: #0369a1; background: transparent; box-shadow: none;
            transform: translateY(-2px) scale(1.02);
        }}
        @media (max-width: 600px) {{ .{style_key} [data-testid="stVerticalBlockBorderWrapper"] {{ padding: 1rem; }} }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    with st.container(key=f"{key_prefix}_authenticated_session_card", border=True):
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:1rem;">
              <div style="width:42px;height:42px;display:grid;place-items:center;border-radius:12px;background:#e7f5ed;color:#087a55;font-weight:800;">{initials}</div>
              <span style="display:inline-flex;align-items:center;gap:7px;padding:6px 12px;border-radius:999px;background:#e7f5ed;color:#087a55;font-size:.72rem;font-weight:750;letter-spacing:.04em;text-transform:uppercase;">
                <span style="width:7px;height:7px;border-radius:50%;background:#16a36a;"></span>{safe_role}
              </span>
            </div>
            <h2 style="margin:0 0 .35rem;color:#104b3b;font-size:1.45rem;letter-spacing:-.03em;">You're signed in, {safe_name}</h2>
            <p style="margin:0 0 1rem;color:#60766f;font-size:.9rem;line-height:1.5;">{safe_email} &middot; Your session is active.</p>
            """,
            unsafe_allow_html=True,
        )
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
            border-radius: 20px !important;
            background: #ffffff !important;
            border: 1px solid #dce9e3 !important;
            box-shadow: 0 12px 32px rgba(17, 73, 55, 0.08) !important;
            padding: 1.25rem 1.45rem !important;
        }}
        .st-key-ag_centralized_login_col [data-testid="stTextInput"] input {{
            min-height: 2.8rem;
            border: 1px solid #d9e5e0;
            border-radius: 11px;
            background: #ffffff;
        }}
        .st-key-ag_centralized_login_col [data-testid="stTextInput"] input:focus {{
            border-color: #0b8059;
            box-shadow: 0 0 0 3px rgba(11, 128, 89, 0.11);
        }}
        .st-key-ag_centralized_login_col [data-testid="stFormSubmitButton"] button {{
            min-height: 2.8rem;
            border-radius: 11px;
            background: #087a55;
            border-color: #087a55;
        }}
        .st-key-ag_centralized_login_col [data-testid="stLinkButton"] a {{
            min-height: 2.8rem;
            border-radius: 11px;
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
                accent_color="#087a55",
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
        if portal == "admin":
            return True
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
                accent_color="#087a55",
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
            with st.popover("Forgot password?", use_container_width=True):
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
            try:
                g_status = request_api("GET", "/community/auth/google/status", timeout=2)
                if g_status.status_code == 200 and g_status.json().get("enabled"):
                    st.link_button(
                        "Sign in or register with Google",
                        f"{api_base_url}/community/auth/google",
                        use_container_width=True,
                    )
                    st.caption("New accounts through Google are verified automatically.")
                    st.markdown('<div style="text-align:center;color:#64748b;font-size:0.75rem;margin:0.4rem 0 0.7rem;">— OR —</div>', unsafe_allow_html=True)
            except Exception:
                pass

            tab_signin, tab_create = st.tabs(["Sign In", "Create Account"])
            with tab_signin:
                with st.form(f"{key_prefix}_comm_signin"):
                    comm_email = st.text_input("Email", placeholder="farmer@cooperative.rw", key=f"{key_prefix}_comm_login_email")
                    comm_pw = st.text_input("Password", type="password", placeholder="••••••••••••", key=f"{key_prefix}_comm_login_password")
                    comm_sub = st.form_submit_button("Sign In →", type="primary", use_container_width=True)
                if comm_sub:
                    try:
                        resp = request_api("POST", "/community/login", json={"email": comm_email, "password": comm_pw}, timeout=15)
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
                            resp = request_api(
                                "POST",
                                "/community/register",
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
                accent_color="#087a55",
            )
            tab_admin, tab_comm = st.tabs(["Administrator & Officer", "Farmer Community"])
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
                with st.popover("Forgot password?", use_container_width=True):
                    with st.form(f"{key_prefix}_uni_forgot_form"):
                        forgot_email = st.text_input("Administrator email", placeholder="admin@agrimenya.rw", key=f"{key_prefix}_uni_forgot_email")
                        forgot = st.form_submit_button("Send reset link →", use_container_width=True)
                    if forgot:
                        if api_client.request_admin_password_reset(forgot_email):
                            st.success("If an active account matches that email, reset instructions will be sent.")
                        else:
                            st.error(api_client.get_admin_api_error("/auth/admin/password/forgot") or "Could not request password reset.")
            with tab_comm:
                try:
                    g_status = request_api("GET", "/community/auth/google/status", timeout=2)
                    if g_status.status_code == 200 and g_status.json().get("enabled"):
                        st.link_button(
                            "Sign in or register with Google",
                            f"{api_base_url}/community/auth/google",
                            use_container_width=True,
                        )
                        st.caption("New accounts through Google are verified automatically.")
                        st.markdown('<div style="text-align:center;color:#64748b;font-size:0.75rem;margin:0.4rem 0 0.7rem;">— OR —</div>', unsafe_allow_html=True)
                except Exception:
                    pass

                tab_in, tab_reg = st.tabs(["Sign In", "Create Account"])
                with tab_in:
                    with st.form(f"{key_prefix}_uni_comm_login"):
                        c_email = st.text_input("Email", placeholder="farmer@cooperative.rw", key=f"{key_prefix}_uni_c_email")
                        c_pw = st.text_input("Password", type="password", placeholder="••••••••••••", key=f"{key_prefix}_uni_c_pw")
                        c_sub = st.form_submit_button("Sign In to Community →", type="primary", use_container_width=True)
                    if c_sub:
                        try:
                            resp = request_api("POST", "/community/login", json={"email": c_email, "password": c_pw}, timeout=15)
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
                                resp = request_api(
                                    "POST",
                                    "/community/register",
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





def generate_svg_sparkline(data: list[float], color: str = "#10b981", width: int = 80, height: int = 26) -> str:
    """Generate a lightweight SVG sparkline from a series of numbers."""
    if not data or len(data) < 2:
        return ""
    min_val, max_val = min(data), max(data)
    val_range = max_val - min_val if max_val != min_val else 1.0
    step = width / (len(data) - 1)
    points = []
    for i, val in enumerate(data):
        x = i * step
        y = height - ((val - min_val) / val_range) * (height - 8) - 4
        points.append(f"{x:.1f},{y:.1f}")
    poly_points = " ".join(points)
    fill_polygon = f"0,{height} {poly_points} {width},{height}"

    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none" style="overflow:visible;">
        <polygon points="{fill_polygon}" fill="{color}" fill-opacity="0.12"/>
        <polyline points="{poly_points}" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <circle cx="{points[-1].split(',')[0]}" cy="{points[-1].split(',')[1]}" r="3" fill="{color}"/>
    </svg>"""


def render_kpi_card(
    col=None,
    title: str = "",
    value: str | int | float = "",
    unit: str = "",
    delta: float | str | None = None,
    delta_period: str = "vs baseline",
    sparkline_data: list[float] | None = None,
    icon: str = "",
    badge_color: str = "#0284c7",
    subtitle: str = "",
    delta_pct: float | str | None = None,
) -> None:
    """Render an executive KPI card with live value, delta badge, and inline SVG sparkline."""
    if isinstance(col, str) and not title:
        title = col
        col = None
    if delta_pct is not None and delta is None:
        delta = delta_pct

    sparkline_svg = generate_svg_sparkline(sparkline_data, color=badge_color) if sparkline_data else ""

    delta_markup = ""
    if delta is not None:
        try:
            delta_val = float(str(delta).replace("%", "").replace("+", "").strip())
            is_pos = delta_val >= 0
            cls = "ag-kpi-delta-up" if is_pos else "ag-kpi-delta-down"
            arrow = "↑" if is_pos else "↓"
            delta_markup = f'<div class="ag-kpi-footer"><span class="ag-kpi-delta {cls}">{arrow} {abs(delta_val):.1f}%</span> <span>{subtitle or delta_period}</span></div>'
        except ValueError:
            delta_markup = f'<div class="ag-kpi-footer"><span class="ag-kpi-delta">{delta}</span> <span>{subtitle or delta_period}</span></div>'
    elif subtitle:
        delta_markup = f'<div class="ag-kpi-footer"><span>{subtitle}</span></div>'

    icon_html = f'<div class="ag-icon-badge ag-kpi-icon">{icon}</div>' if icon else ""

    html = f"""
    <div class="ag-kpi-card">
        <div class="ag-kpi-header">
            <span class="ag-kpi-title">{title}</span>
            {icon_html}
        </div>
        <div class="ag-kpi-body">
            <span class="ag-kpi-value">{value}{unit}</span>
            <div class="ag-kpi-sparkline">{sparkline_svg}</div>
        </div>
        {delta_markup}
    </div>
    """
    if col is not None:
        with col:
            st.markdown(html, unsafe_allow_html=True)
    else:
        st.markdown(html, unsafe_allow_html=True)


def render_weather_forecast_grid(forecast_list: list[dict]) -> None:
    """Render a modern horizontal grid of daily weather forecasts."""
    if not forecast_list:
        return
    cards_html = []
    for item in forecast_list[:6]:
        date = str(item.get("date") or item.get("Date") or "")[-5:]
        hi = item.get("temperature_max_c") or item.get("High (C)") or "N/A"
        lo = item.get("temperature_min_c") or item.get("Low (C)") or "N/A"
        rain = item.get("precipitation_probability_pct") or item.get("Rain chance (%)") or 0
        rain_sum = item.get("precipitation_sum_mm") or item.get("Rain (mm)") or 0

        cards_html.append(f"""
        <div class="ag-weather-card">
            <div class="ag-weather-date">{date}</div>
            <div class="ag-weather-temp">{hi}° / {lo}°</div>
            <div class="ag-weather-rain">Rain: {rain}% ({rain_sum}mm)</div>
        </div>
        """)
    grid_html = f'<div class="ag-weather-row">{"".join(cards_html)}</div>'
    st.markdown(grid_html, unsafe_allow_html=True)


def render_empty_state(title: str, message: str, icon_svg: str = "") -> None:
    """Render a clean, modern empty state container."""
    default_icon = """<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/></svg>"""
    icon = icon_svg if icon_svg else default_icon
    html = f"""
    <div class="ag-empty-state">
        <div class="ag-empty-icon">{icon}</div>
        <div class="ag-empty-title">{title}</div>
        <div class="ag-empty-desc">{message}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
