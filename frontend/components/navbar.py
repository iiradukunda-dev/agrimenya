"""Unified centered floating pill navigation tailored to the agrimenya theme."""
import inspect
import streamlit as st
from components.ai_widget import render_floating_ai_widget
from utils.i18n import render_language_selector, t
from utils.pwa import render_pwa_support


DEFAULT_USER = {
    "name": "Extension Officer",
    "role": "Agronomist",
    "email": "officer@rab.gov.rw",
    "avatar": "EO",
}

PUBLIC_PAGES = {"Home.py", "3_Dashboard.py", "9_Communication.py", "1_About.py", ""}


def init_user_session() -> None:
    """Initialize session state so the app always defaults to signed in and White & Sky Blue theme."""
    try:
        if "authenticated" not in st.session_state:
            st.session_state["authenticated"] = True
        if "user_profile" not in st.session_state:
            st.session_state["user_profile"] = dict(DEFAULT_USER)
        st.session_state["ag_theme_mode"] = "light"
    except Exception:
        pass


def is_authenticated() -> bool:
    """Check if the current session is authenticated."""
    init_user_session()
    try:
        return bool(st.session_state.get("authenticated", True))
    except Exception:
        return True


def get_current_page_file() -> str:
    """Detect current running Streamlit page filename from call stack."""
    try:
        for frame in inspect.stack():
            filename = frame.filename.replace("\\", "/")
            if "Home.py" in filename:
                return "Home.py"
            if "/pages/" in filename or filename.startswith("pages/"):
                return filename.split("/")[-1]
    except Exception:
        pass
    return ""


def check_page_access() -> bool:
    """
    Enforce page access rules.
    Unauthenticated users are allowed only on the public landing/navigation pages:
    Home, Overview, Updates (Communication), and About.
    """
    if is_authenticated():
        return True

    current_page = get_current_page_file()
    if not current_page or current_page in PUBLIC_PAGES or "test" in current_page:
        return True

    # User is unauthenticated and attempting to view a restricted page
    st.markdown("""
    <div style="
        max-width: 580px;
        margin: 2.5rem auto 1.5rem;
        padding: 2.25rem 2rem;
        background: #ffffff;
        border-radius: 20px;
        border: 1.5px solid rgba(2, 132, 199, 0.25);
        border-top: 4px solid #0284c7;
        box-shadow: 0 16px 40px rgba(2, 132, 199, 0.12), 0 2px 8px rgba(0, 0, 0, 0.04);
        text-align: center;
        font-family: 'Plus Jakarta Sans', sans-serif;
    ">
        <div style="
            width: 60px;
            height: 60px;
            margin: 0 auto 1.2rem;
            border-radius: 50%;
            background: #e0f2fe;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #0284c7;
        ">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
        </div>
        <h2 style="color: #0f172a; font-size: 1.45rem; font-weight: 800; margin-bottom: 0.4rem;">Access Restricted</h2>
        <p style="color: #475569; font-size: 0.92rem; line-height: 1.6; margin-bottom: 1.5rem;">
            This page is reserved for authenticated agricultural officers. Unauthenticated access is limited to <strong>Home</strong>, <strong>Overview</strong>, <strong>Updates</strong>, and <strong>About</strong>.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Sign In as Extension Officer", key="auth_restricted_gate_btn", type="primary", use_container_width=True):
        st.session_state["authenticated"] = True
        st.session_state["user_profile"] = dict(DEFAULT_USER)
        st.rerun()
    st.page_link("Home.py", label="Return to Home", use_container_width=True)

    st.stop()
    return False


def render_navbar(show_sidebar: bool = False) -> None:
    """Render the unified centered floating pill navigation styled with agrimenya theme tokens."""
    style = """
      <style>
      @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
      [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

      /* =========================================================
         AGRIMENYA TOP STICKY FLOATING NAVBAR
         ========================================================= */
      header[data-testid="stHeader"],
      .stApp > header,
      [data-testid="stHeader"] {
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        visibility: hidden !important;
      }

      .block-container,
      [data-testid="stMainBlockContainer"],
      [data-testid="stAppViewBlockContainer"],
      .main .block-container {
        padding-top: 4.25rem !important;
        margin-top: 0 !important;
      }

      .st-key-ag_desktop_navbar {
        position: fixed !important;
        top: 0.25rem !important;
        left: 0 !important;
        right: 0 !important;
        z-index: 999990 !important;
        display: flex !important;
        justify-content: center !important;
        pointer-events: none !important;
      }

      /* Outer Floating Container */
      .st-key-ag_navbar {
        z-index: 999990 !important;
        display: flex !important;
        flex-direction: row !important;
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 auto 0.45rem auto !important;
        padding: 0 0.5rem !important;
        background: transparent !important;
        box-sizing: border-box !important;
        pointer-events: auto !important;
      }
      .st-key-ag_navbar > div {
        display: flex !important;
        flex-direction: row !important;
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 auto !important;
        padding: 0 !important;
      }
      .st-key-ag_mobile_navbar {
        display: none !important;
      }

      @media (max-width: 840px) {
        .st-key-ag_desktop_navbar {
          display: none !important;
        }
        .st-key-ag_mobile_navbar {
          display: block !important;
          position: fixed !important;
          top: 0.25rem !important;
          left: 0 !important;
          right: 0 !important;
          z-index: 999990 !important;
          width: 100% !important;
          margin: 0 auto 0.45rem !important;
          padding: 0 0.5rem !important;
        }
        .st-key-ag_mobile_navbar [data-testid="stHorizontalBlock"] {
          display: flex !important;
          flex-wrap: nowrap !important;
          align-items: center !important;
          justify-content: space-between !important;
          width: 100% !important;
          max-width: 100% !important;
          margin: 0 !important;
          padding: 6px 14px !important;
          gap: 8px !important;
          background: rgba(255, 255, 255, 0.98) !important;
          border-radius: 9999px !important;
          box-shadow: 0 6px 24px rgba(2, 132, 199, 0.12) !important;
          border: 1px solid rgba(2, 132, 199, 0.18) !important;
        }
        .st-key-ag_mobile_navbar [data-testid="column"],
        .st-key-ag_mobile_navbar [data-testid="stColumn"] {
          display: flex !important;
          flex: 0 0 auto !important;
          width: auto !important;
          margin: 0 !important;
          padding: 0 !important;
          align-items: center !important;
        }
        .st-key-ag_mobile_navbar [data-testid="stPopover"] button {
          width: auto !important;
          height: 2.35rem !important;
          min-width: 4.5rem !important;
          border-radius: 9999px !important;
          background: #e0f2fe !important;
          color: #075985 !important;
          border: 1px solid #7dd3fc !important;
          padding: 0.4rem 0.9rem !important;
          font-size: 0.9rem !important;
          font-weight: 700 !important;
        }
        .st-key-ag_mobile_navbar [data-testid="stPopover"] button p {
          color: #075985 !important;
          font-size: 0.9rem !important;
          font-weight: 700 !important;
          margin: 0 !important;
          white-space: nowrap !important;
        }
        .st-key-ag_mobile_navbar [data-testid="stPopoverBody"] {
          width: min(20rem, calc(100vw - 2rem)) !important;
          max-height: calc(100dvh - 6rem) !important;
          overflow-y: auto !important;
        }
      }

      /* Unified Floating Pill Capsule */
      .st-key-ag_navbar [data-testid="stHorizontalBlock"] {
        display: inline-flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        justify-content: center !important;
        width: auto !important;
        max-width: 100% !important;
        margin: 0 auto !important;
        padding: 5px 14px !important;
        background: rgba(255, 255, 255, 0.98) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border-radius: 9999px !important;
        border: 1px solid rgba(2, 132, 199, 0.18) !important;
        box-shadow: 0 8px 30px rgba(2, 132, 199, 0.14), 0 2px 8px rgba(0, 0, 0, 0.04) !important;
        gap: 4px !important;
        box-sizing: border-box !important;
      }

      .st-key-ag_navbar [data-testid="stHorizontalBlock"] > [data-testid="column"],
      .st-key-ag_navbar [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        display: inline-flex !important;
        flex: 0 0 auto !important;
        width: auto !important;
        min-width: unset !important;
        max-width: unset !important;
        margin: 0 !important;
        padding: 0 !important;
        align-items: center !important;
        justify-content: center !important;
      }

      /* Base nav links */
      .st-key-ag_navbar [data-testid="stPageLink"],
      .st-key-ag_navbar [data-testid="stPageLink-NavLink"] {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        border-radius: 9999px !important;
        height: 2.35rem !important;
        min-height: 2.35rem !important;
        padding: 0.45rem 1.15rem !important;
        box-shadow: none !important;
        justify-content: center !important;
        align-items: center !important;
        text-align: center !important;
        display: inline-flex !important;
        text-decoration: none !important;
        line-height: 1 !important;
        margin: 0 !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
      }
      .st-key-ag_navbar [data-testid="stPageLink"] p,
      .st-key-ag_navbar [data-testid="stPageLink-NavLink"] p {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        color: #0a1f26 !important;
        letter-spacing: -0.01em !important;
        margin: 0 !important;
        line-height: 1 !important;
        transition: color 0.2s ease !important;
      }
      .st-key-ag_navbar [data-testid="stPageLink"]:hover p,
      .st-key-ag_navbar [data-testid="stPageLink-NavLink"]:hover p {
        color: #0284c7 !important;
      }

      /* ACTIVE / SELECTED TAB */
      .st-key-ag_navbar [data-testid="stHorizontalBlock"] a[aria-current="page"],
      .st-key-ag_navbar [data-testid="stHorizontalBlock"] a.ag-nav-active,
      .st-key-ag_navbar a[aria-current="page"],
      .st-key-ag_navbar a.ag-nav-active {
        background: transparent !important;
        background-color: transparent !important;
        box-sizing: border-box !important;
        border: 2px solid #0875d1 !important;
        border-radius: 9999px !important;
        height: 2.35rem !important;
        min-height: 2.35rem !important;
        padding: 0.45rem 1.35rem !important;
        box-shadow: none !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-decoration: none !important;
      }
      .st-key-ag_navbar a[aria-current="page"] p,
      .st-key-ag_navbar a.ag-nav-active p {
        color: #0369a1 !important;
        font-weight: 700 !important;
      }

      /* More popover button */
      .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stPopoverButton"] {
        min-width: 4.25rem !important;
        height: 2.25rem !important;
        padding: 0.4rem 0.85rem !important;
        border: 1px solid #7dd3fc !important;
        border-radius: 9999px !important;
        background: #e0f2fe !important;
        color: #075985 !important;
        box-shadow: none !important;
      }
      .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stPopoverButton"] p,
      .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stPopoverButton"] span {
        color: #075985 !important;
        font-weight: 700 !important;
        visibility: visible !important;
        opacity: 1 !important;
      }
      .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stPopoverButton"]:hover {
        border-color: #0284c7 !important;
        background: #bae6fd !important;
      }

      .st-key-ag_desktop_navbar .st-key-ag_navbar .st-key-lang_cycle_btn button,
      .st-key-lang_cycle_btn button {
        border: 1px solid #7dd3fc !important;
        border-radius: 9999px !important;
        background: #e0f2fe !important;
        color: #075985 !important;
      }
      .st-key-ag_desktop_navbar .st-key-ag_navbar .st-key-lang_cycle_btn button:hover,
      .st-key-lang_cycle_btn button:hover {
        border-color: #0284c7 !important;
        background: #0284c7 !important;
        color: #ffffff !important;
      }

      /* Dropdown Body */
      div[data-testid="stPopoverBody"] {
        max-height: 520px !important;
        border-radius: 16px !important;
        border: 1px solid rgba(2, 132, 199, 0.15) !important;
        background: #ffffff !important;
        box-shadow: 0 16px 40px rgba(4, 31, 38, 0.14) !important;
        padding: 0.75rem 0.65rem !important;
      }

      /* Tabs styling */
      [data-testid="stTabs"] {
        margin-top: 0.5rem !important;
      }
      [data-testid="stTabs"] [data-baseweb="tab-list"] {
        background: #f1f5f9 !important;
        padding: 4px !important;
        border-radius: 12px !important;
        gap: 4px !important;
      }
      [data-testid="stTabs"] button[role="tab"] {
        background: transparent !important;
        border-radius: 8px !important;
        color: #334155 !important;
        border: none !important;
      }
      [data-testid="stTabs"] button[role="tab"] p {
        color: #334155 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 600 !important;
      }
      [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        background: #ffffff !important;
        background-color: #ffffff !important;
        color: #0284c7 !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 8px rgba(2, 132, 199, 0.15) !important;
        border-bottom: 2.5px solid #0284c7 !important;
      }
      [data-testid="stTabs"] button[role="tab"][aria-selected="true"] p {
        color: #0284c7 !important;
        font-weight: 700 !important;
      }

      hr.ag-nav-rule {
        border: none !important;
        border-top: 1px solid rgba(2, 132, 199, 0.12) !important;
        margin: 0.25rem 0 0.75rem 0 !important;
      }
      </style>
    """
    if show_sidebar:
        style = style.replace(
            '      [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }',
            "",
        )
    st.markdown(style, unsafe_allow_html=True)

    init_user_session()
    auth = is_authenticated()

    # Enforce page-level access control for the public unauthenticated menu.
    check_page_access()

    with st.container(key="ag_desktop_navbar"):
        with st.container(key="ag_navbar"):
            if auth:
                c_home, c_overview, c_zones, c_decide, c_more, c_sep, c_lang = st.columns(
                    [1.15, 1.1, 0.95, 1.15, 1.05, 0.02, 0.45], vertical_alignment="center"
                )
            else:
                c_home, c_overview, c_updates, c_about, c_more, c_sep, c_lang = st.columns(
                    [1.15, 1.1, 1.2, 1.0, 0.25, 0.02, 0.45], vertical_alignment="center"
                )

            with c_home:
                st.page_link("Home.py", label=t("nav.home", "Home"))
            with c_overview:
                st.page_link("pages/3_Dashboard.py", label=t("nav.overview", "Overview"))

            if auth:
                with c_zones:
                    st.page_link("pages/4_Zones.py", label=t("nav.zones", "Zones"))
                with c_decide:
                    st.page_link("pages/6_Decision_Making.py", label=t("nav.decisions", "Decisions"))
                with c_more:
                    with st.popover(t("nav.more", "More"), width="stretch"):
                        st.divider()
                        st.caption(t("nav.operations_tools", "OPERATIONS & TOOLS"))
                        st.page_link("pages/8_Planning.py", label=t("nav.planning", "Seasonal planning"))
                        st.page_link("pages/9_Communication.py", label=t("nav.comms", "Field alerts & comms"))
                        st.page_link("pages/5_Segmentation.py", label=t("nav.segmentation", "Zone segmentation"))
                        st.page_link("pages/7_AI_Assistant.py", label=t("nav.ai_assistant", "AI assistant"))
                        st.divider()
                        st.caption(t("nav.platform_community", "PLATFORM & COMMUNITY"))
                        st.page_link("pages/10_Admin.py", label=t("nav.admin", "Administration"))
                        st.page_link("pages/99_Showcase.py", label=t("nav.data_guide", "Data guide"))
                        st.page_link("pages/12_Community.py", label=t("nav.community", "Farmer community"))
                        st.page_link("pages/1_About.py", label=t("nav.about", "About agrimenya"))
                        st.markdown(
                            f'<a href="/app/static/offline.html" target="_self" style="text-decoration:none;display:flex;align-items:center;gap:0.4rem;padding:0.4rem 0.75rem;border-radius:8px;font-size:0.85rem;font-weight:600;color:#0284c7;background:rgba(2,132,199,0.08);border:1px solid rgba(2,132,199,0.22);margin-top:0.3rem;"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"></path></svg> {t("nav.offline_hub", "Offline Field Hub")}</a>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f'<button id="ag-nav-install-btn" onclick="if(window.parent&&window.parent.__agrimenya_trigger_install){{window.parent.__agrimenya_trigger_install();}}else{{const b=window.parent.document.getElementById(\'ag-pwa-install-badge\');if(b){{b.click();}}}}" style="width:100%;text-align:left;border:none;background:linear-gradient(135deg,#031d28 0%,#063143 100%);color:#ffffff;border:1.5px solid rgba(56,189,248,0.55);border-radius:8px;padding:0.45rem 0.75rem;margin-top:0.35rem;display:flex;align-items:center;gap:0.5rem;cursor:pointer;font-family:\'Plus Jakarta Sans\',sans-serif;font-size:0.85rem;font-weight:700;box-shadow:0 4px 14px rgba(0,0,0,0.35);transition:all 0.2s;"><img src="/app/static/ai_assistant_bulb.png" alt="logo" style="width:18px;height:18px;object-fit:contain;filter:drop-shadow(0 0 6px rgba(56,189,248,0.9));"> <span style="color:#ffffff;">{t("nav.install_app", "Install agrimenya App")}</span></button>',
                            unsafe_allow_html=True,
                        )
                        st.divider()
                        if st.button(t("nav.sign_out", "Sign out"), key="navbar_signout_action_btn", use_container_width=True):
                            st.session_state["authenticated"] = False
                            st.rerun()

                with c_sep:
                    st.empty()
            else:
                with c_updates:
                    st.page_link("pages/9_Communication.py", label=t("nav.updates", "Updates"))
                with c_about:
                    st.page_link("pages/1_About.py", label=t("nav.about", "About"))
                with c_more:
                    st.empty()
                with c_sep:
                    st.empty()

            with c_lang:
                render_language_selector(sidebar=False)

    with st.container(key="ag_mobile_navbar"):
        mobile_menu_col, mobile_language_col = st.columns([1, 1], vertical_alignment="center")
        with mobile_menu_col:
            with st.popover("Menu", help="Open navigation menu", width="content"):
                st.page_link("Home.py", label=t("nav.home", "Home"))
                st.page_link("pages/3_Dashboard.py", label=t("nav.overview", "Overview"))
                if auth:
                    st.page_link("pages/4_Zones.py", label=t("nav.zones", "Zones"))
                    st.page_link("pages/6_Decision_Making.py", label=t("nav.decisions", "Decisions"))
                    st.divider()
                    st.page_link("pages/8_Planning.py", label=t("nav.planning", "Seasonal planning"))
                    st.page_link("pages/9_Communication.py", label=t("nav.comms", "Field alerts & comms"))
                    st.page_link("pages/5_Segmentation.py", label=t("nav.segmentation", "Zone segmentation"))
                    st.page_link("pages/7_AI_Assistant.py", label=t("nav.ai_assistant", "AI assistant"))
                    st.page_link("pages/10_Admin.py", label=t("nav.admin", "Administration"))
                    st.page_link("pages/99_Showcase.py", label=t("nav.data_guide", "Data guide"))
                    st.page_link("pages/12_Community.py", label=t("nav.community", "Farmer community"))
                    st.page_link("pages/1_About.py", label=t("nav.about", "About agrimenya"))
                    if st.button(t("nav.sign_out", "Sign out"), key="mobile_nav_signout_btn", use_container_width=True):
                        st.session_state["authenticated"] = False
                        st.rerun()
                else:
                    st.page_link("pages/9_Communication.py", label=t("nav.updates", "Updates"))
                    st.page_link("pages/1_About.py", label=t("nav.about", "About"))
        with mobile_language_col:
            render_language_selector(sidebar=False, button_key="lang_cycle_mobile_btn")


    st.markdown('<hr class="ag-nav-rule">', unsafe_allow_html=True)
    render_floating_ai_widget()
    render_pwa_support()


def render_page_header(
    title: str,
    subtitle: str = "",
    badge: str | None = None,
    breadcrumbs: list[tuple[str, str | None]] | None = None,
) -> None:
    """Render a consistent, modern executive page header with breadcrumbs and badge."""
    breadcrumb_html = ""
    if breadcrumbs:
        crumbs = []
        for name, link in breadcrumbs:
            if link:
                crumbs.append(f'<a href="{link}" style="color:var(--ag-text-muted);text-decoration:none;">{name}</a>')
            else:
                crumbs.append(f'<span style="color:var(--ag-primary);font-weight:600;">{name}</span>')
        breadcrumb_html = f'<div style="font-size:0.78rem;margin-bottom:0.35rem;display:flex;align-items:center;gap:6px;">{" › ".join(crumbs)}</div>'

    badge_html = f'<span style="font-size:0.72rem;font-weight:750;letter-spacing:0.06em;text-transform:uppercase;color:var(--ag-primary);background:var(--ag-primary-soft);padding:3px 10px;border-radius:9999px;border:1px solid rgba(2,132,199,0.25);margin-bottom:0.4rem;display:inline-block;">{badge}</span>' if badge else ""
    sub_html = f'<p style="color:var(--ag-text-muted);font-size:0.95rem;margin:0.25rem 0 0.75rem;">{subtitle}</p>' if subtitle else ""

    html = f"""
    <div style="margin: 0.5rem 0 1.25rem;">
        {breadcrumb_html}
        {badge_html}
        <h1 style="margin:0;padding:0;font-family:var(--ag-font-display);font-size:1.85rem;font-weight:800;letter-spacing:-0.03em;color:var(--ag-text-main);">{title}</h1>
        {sub_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
