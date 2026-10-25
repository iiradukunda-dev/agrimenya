"""Creative, animated workflow cards with rich micro-motions for the agrimenya frontend."""
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
            background: linear-gradient(90deg, transparent 0%, {accent_color}60 30%, rgba(74, 222, 128, 0.45) 70%, transparent 100%);
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
                background: linear-gradient(135deg, #0284c7 0%, #059669 100%);
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


