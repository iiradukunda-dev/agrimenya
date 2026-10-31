"""Unified centered floating pill navigation tailored to the agrimenya theme."""
from concurrent.futures import Future
import inspect
import streamlit as st
from components.ai_widget import render_floating_ai_widget
from utils.api_client import start_api_warmup
from utils.i18n import render_language_selector, t
from utils.pwa import render_pwa_support


DEFAULT_USER = {
    "name": "Extension Officer",
    "role": "Agronomist",
    "email": "officer@rab.gov.rw",
    "avatar": "EO",
}

PUBLIC_PAGES = {
    "Home.py", "dashboard.py", "3_Dashboard.py", "9_Communication.py",
    "12_Community.py", "1_About.py", "",
}


def init_user_session() -> None:
    """Initialize an anonymous session until a real farmer/admin login succeeds."""
    try:
        if "authenticated" not in st.session_state:
            st.session_state["authenticated"] = False
        if "user_profile" not in st.session_state:
            st.session_state["user_profile"] = {}
        st.session_state["ag_theme_mode"] = "light"
    except Exception:
        pass


def is_authenticated() -> bool:
    """Check if the current session is authenticated."""
    init_user_session()
    try:
        return bool(
            st.session_state.get("authenticated", False)
            or st.session_state.get("community_access_token")
            or st.session_state.get("admin_access_token")
        )
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


def _render_api_warmup() -> None:
    future = st.session_state.get("api_warmup_future")
    if future is not None and not isinstance(future, Future):
        return
    if future is None:
        future = start_api_warmup()
        st.session_state["api_warmup_future"] = future

    if future.done():
        if future.result():
            return
        st.warning(
            "The backend is not responding yet. It may be starting after an idle period."
        )
    else:
        st.info("Connecting to the backend in the background; startup may take a minute.")

    if st.button("Retry backend connection", key="api_warmup_retry") is True:
        st.session_state["api_warmup_future"] = start_api_warmup()
        st.info("Backend connection retry started.")


def render_navbar(show_sidebar: bool = False) -> None:
    """Render the unified centered floating pill navigation styled with agrimenya theme tokens."""
    _render_api_warmup()
    style = """
      <style>
      @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
      [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

      /* =========================================================
         AGRIMENYA TOP STICKY FLOATING NAVBAR
         ========================================================= */
      /* Suppress native Streamlit header and remove top padding */
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
        padding-top: 0.35rem !important;
        margin-top: 0 !important;
      }

      /* Outer Container: Pinned to the top of the viewport */
      .st-key-ag_navbar {
        position: sticky !important;
        top: 0.35rem !important;
        z-index: 999990 !important;
        display: flex !important;
        flex-direction: row !important;
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 auto 0.45rem auto !important;
        padding: 0 !important;
        background: transparent !important;
      }
      .st-key-ag_navbar > div {
        display: flex !important;
        flex-direction: row !important;
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
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
          position: sticky !important;
          top: 0.25rem !important;
          z-index: 999990 !important;
          width: 100% !important;
          margin: 0 auto 0.45rem !important;
          padding: 0 0.25rem !important;
        }
        .st-key-ag_mobile_navbar [data-testid="stHorizontalBlock"] {
          display: flex !important;
          flex-wrap: nowrap !important;
          align-items: center !important;
          justify-content: space-between !important;
          width: 100% !important;
          max-width: 100% !important;
          margin: 0 !important;
          padding: 6px 12px !important;
          gap: 8px !important;
          background: transparent !important;
          border: none !important;
          border-radius: 0 !important;
          box-shadow: none !important;
          backdrop-filter: none !important;
          -webkit-backdrop-filter: none !important;
        }
        .st-key-ag_mobile_navbar [data-testid="column"],
        .st-key-ag_mobile_navbar [data-testid="stColumn"] {
          display: flex !important;
          flex: 0 0 auto !important;
          width: auto !important;
          min-width: 0 !important;
          max-width: none !important;
          margin: 0 !important;
          padding: 0 !important;
          align-items: center !important;
          justify-content: center !important;
        }
        .st-key-ag_mobile_navbar [data-testid="stPopover"] button {
          display: inline-flex !important;
          align-items: center !important;
          justify-content: flex-start !important;
          position: relative !important;
          width: auto !important;
          min-width: 5.4rem !important;
          height: 2.5rem !important;
          min-height: 2.5rem !important;
          padding: 0 0.75rem 0 2.55rem !important;
          border: 0 !important;
          border-radius: 9999px !important;
          background: rgba(2, 132, 199, 0.09) !important;
          color: #0284c7 !important;
          font-size: 1.45rem !important;
          line-height: 1 !important;
          box-shadow: none !important;
        }
        .st-key-ag_mobile_navbar [data-testid="stPopover"] button:hover {
          background: #0284c7 !important;
          color: #ffffff !important;
        }
        .st-key-ag_mobile_navbar [data-testid="stPopover"] button p {
          font-size: 0 !important;
          line-height: 0 !important;
          width: 0 !important;
          height: 0 !important;
          margin: 0 !important;
          overflow: hidden !important;
        }
        .st-key-ag_mobile_navbar [data-testid="stPopover"] button::before {
          content: "" !important;
          position: absolute !important;
          left: 0.85rem !important;
          top: 50% !important;
          display: block !important;
          width: 18px !important;
          height: 2px !important;
          transform: translateY(-50%) !important;
          border-radius: 999px !important;
          background: currentColor !important;
          box-shadow: 0 6px 0 currentColor, 0 -6px 0 currentColor !important;
        }
        .st-key-ag_mobile_navbar [data-testid="stPopover"] button::after {
          content: "More" !important;
          display: inline-block !important;
          color: currentColor !important;
          font-family: 'Plus Jakarta Sans', sans-serif !important;
          font-size: 0.9rem !important;
          font-weight: 650 !important;
          line-height: 1 !important;
          pointer-events: none !important;
        }
        .st-key-ag_mobile_navbar [data-testid="stIconMaterial"],
        .st-key-ag_mobile_navbar [data-testid="stPopover"] button svg {
          display: none !important;
        }
        .st-key-ag_mobile_navbar [data-testid="stPopoverButton"] > div > div[aria-hidden="true"] {
          display: none !important;
        }
        .st-key-ag_mobile_navbar [data-testid="stPopoverBody"],
        body:has(.st-key-ag_mobile_navbar [data-testid="stPopover"] button[aria-expanded="true"]) [data-testid="stPopoverBody"] {
          width: min(16rem, calc(100vw - 2rem)) !important;
          min-width: 0 !important;
          max-width: min(16rem, calc(100vw - 2rem)) !important;
          max-height: calc(100dvh - 7rem) !important;
          box-sizing: border-box !important;
          overflow-y: auto !important;
        }
        .st-key-ag_mobile_navbar [data-testid="stPopoverBody"] [data-testid="stPageLink"],
        .st-key-ag_mobile_navbar [data-testid="stPopoverBody"] [data-testid="stPageLink-NavLink"],
        body:has(.st-key-ag_mobile_navbar [data-testid="stPopover"] button[aria-expanded="true"]) [data-testid="stPopoverBody"] [data-testid="stPageLink"],
        body:has(.st-key-ag_mobile_navbar [data-testid="stPopover"] button[aria-expanded="true"]) [data-testid="stPopoverBody"] [data-testid="stPageLink-NavLink"] {
          min-height: 2.75rem !important;
          padding: 0.65rem 0.85rem !important;
          background: transparent !important;
          background-color: transparent !important;
          border: none !important;
          border-radius: 0 !important;
          box-shadow: none !important;
        }
        .st-key-ag_mobile_navbar [data-testid="stPopoverBody"] [data-testid="stPageLink"]:hover,
        .st-key-ag_mobile_navbar [data-testid="stPopoverBody"] [data-testid="stPageLink-NavLink"]:hover,
        body:has(.st-key-ag_mobile_navbar [data-testid="stPopover"] button[aria-expanded="true"]) [data-testid="stPopoverBody"] [data-testid="stPageLink"]:hover,
        body:has(.st-key-ag_mobile_navbar [data-testid="stPopover"] button[aria-expanded="true"]) [data-testid="stPopoverBody"] [data-testid="stPageLink-NavLink"]:hover,
        .st-key-ag_mobile_navbar [data-testid="stPopoverBody"] [data-testid="stPageLink"][aria-current="page"],
        .st-key-ag_mobile_navbar [data-testid="stPopoverBody"] [data-testid="stPageLink-NavLink"][aria-current="page"],
        body:has(.st-key-ag_mobile_navbar [data-testid="stPopover"] button[aria-expanded="true"]) [data-testid="stPopoverBody"] [data-testid="stPageLink"][aria-current="page"],
        body:has(.st-key-ag_mobile_navbar [data-testid="stPopover"] button[aria-expanded="true"]) [data-testid="stPopoverBody"] [data-testid="stPageLink-NavLink"][aria-current="page"] {
          background: transparent !important;
          background-color: transparent !important;
          border: none !important;
          box-shadow: none !important;
        }
      }

      /* The Unified Floating Pill Capsule */
      .st-key-ag_navbar [data-testid="stHorizontalBlock"],
      [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) {
        display: inline-flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        justify-content: center !important;
        width: auto !important;
        max-width: fit-content !important;
        margin: 0 auto !important;
        padding: 6px 16px !important;
        background: rgba(255, 255, 255, 0.96) !important;
        backdrop-filter: blur(14px) !important;
        -webkit-backdrop-filter: blur(14px) !important;
        border-radius: 9999px !important;
        border: none !important;
        box-shadow: 0 8px 30px rgba(2, 132, 199, 0.14), 0 2px 8px rgba(0, 0, 0, 0.04) !important;
        gap: 6px !important;
      }
      @media (max-width: 840px) {
        .st-key-ag_navbar {
          padding: 0 0.25rem !important;
        }
        .st-key-ag_navbar [data-testid="stHorizontalBlock"],
        [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) {
          width: calc(100% - 0.5rem) !important;
          max-width: 100% !important;
          padding: 6px 10px !important;
          justify-content: space-between !important;
          gap: 4px !important;
          overflow-x: auto !important;
          scrollbar-width: none !important;
          -ms-overflow-style: none !important;
        }
        .st-key-ag_navbar [data-testid="stHorizontalBlock"]::-webkit-scrollbar,
        [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn)::-webkit-scrollbar {
          display: none !important;
        }
        .st-key-ag_navbar [data-testid="stHorizontalBlock"] > [data-testid="column"],
        .st-key-ag_navbar [data-testid="stHorizontalBlock"] > [data-testid="stColumn"],
        [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) > [data-testid="column"],
        [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) > [data-testid="stColumn"] {
          flex: 0 0 auto !important;
        }
      }

      /* Ensure each sub-column shrinks to content width and aligns center */
      .st-key-ag_navbar [data-testid="stHorizontalBlock"] > [data-testid="column"],
      .st-key-ag_navbar [data-testid="stHorizontalBlock"] > [data-testid="stColumn"],
      [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) > [data-testid="column"],
      [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) > [data-testid="stColumn"] {
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

      /* Base nav links inside the pill (Overview, Zones, Decisions) */
      .st-key-ag_navbar [data-testid="stPageLink"]:not([aria-current="page"]):not(.ag-nav-active),
      .st-key-ag_navbar a[data-testid="stPageLink"]:not([aria-current="page"]):not(.ag-nav-active),
      .st-key-ag_navbar [data-testid="stPageLink-NavLink"]:not([aria-current="page"]):not(.ag-nav-active),
      .st-key-ag_navbar a[data-testid="stPageLink-NavLink"]:not([aria-current="page"]):not(.ag-nav-active),
      [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) [data-testid="stPageLink-NavLink"]:not([aria-current="page"]):not(.ag-nav-active) {
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
      .st-key-ag_navbar [data-testid="stPageLink"]:not([aria-current="page"]):not(.ag-nav-active) p,
      .st-key-ag_navbar a[data-testid="stPageLink"]:not([aria-current="page"]):not(.ag-nav-active) p,
      .st-key-ag_navbar [data-testid="stPageLink-NavLink"]:not([aria-current="page"]):not(.ag-nav-active) p,
      .st-key-ag_navbar a[data-testid="stPageLink-NavLink"]:not([aria-current="page"]):not(.ag-nav-active) p,
      [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) [data-testid="stPageLink-NavLink"]:not([aria-current="page"]):not(.ag-nav-active) p {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        color: #0a1f26 !important;
        letter-spacing: -0.01em !important;
        margin: 0 !important;
        line-height: 1 !important;
        transition: color 0.2s ease !important;
      }
      .st-key-ag_navbar [data-testid="stPageLink"]:not([aria-current="page"]):not(.ag-nav-active):hover,
      .st-key-ag_navbar a[data-testid="stPageLink"]:not([aria-current="page"]):not(.ag-nav-active):hover,
      .st-key-ag_navbar [data-testid="stPageLink-NavLink"]:not([aria-current="page"]):not(.ag-nav-active):hover,
      .st-key-ag_navbar a[data-testid="stPageLink-NavLink"]:not([aria-current="page"]):not(.ag-nav-active):hover,
      [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) [data-testid="stPageLink-NavLink"]:not([aria-current="page"]):not(.ag-nav-active):hover {
        background: transparent !important;
        background-color: transparent !important;
        transform: none !important;
      }
      .st-key-ag_navbar [data-testid="stPageLink"]:not([aria-current="page"]):not(.ag-nav-active):hover p,
      .st-key-ag_navbar a[data-testid="stPageLink"]:not([aria-current="page"]):not(.ag-nav-active):hover p,
      .st-key-ag_navbar [data-testid="stPageLink-NavLink"]:not([aria-current="page"]):not(.ag-nav-active):hover p,
      .st-key-ag_navbar a[data-testid="stPageLink-NavLink"]:not([aria-current="page"]):not(.ag-nav-active):hover p,
      [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) [data-testid="stPageLink-NavLink"]:not([aria-current="page"]):not(.ag-nav-active):hover p {
        color: #0284c7 !important;
      }

      /* ACTIVE / SELECTED TAB: transparent capsule with a blue outline */
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
        transition: all 0.2s ease !important;
      }
      /* Keep the Streamlit page-link wrapper plain so only the link is outlined. */
      .st-key-ag_navbar [data-testid="stPageLink"].ag-nav-active,
      .st-key-ag_navbar [data-testid="stPageLink"][aria-current="page"] {
        border: none !important;
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
      }
      .st-key-ag_navbar [data-testid="stHorizontalBlock"] a[aria-current="page"] p,
      .st-key-ag_navbar [data-testid="stHorizontalBlock"] [data-testid="stPageLink"][aria-current="page"] p,
      .st-key-ag_navbar [data-testid="stHorizontalBlock"] [data-testid="stPageLink-NavLink"][aria-current="page"] p,
      .st-key-ag_navbar [data-testid="stHorizontalBlock"] a.ag-nav-active p,
      .st-key-ag_navbar [data-testid="stHorizontalBlock"] [data-testid="stPageLink"].ag-nav-active p,
      .st-key-ag_navbar a[aria-current="page"] p,
      .st-key-ag_navbar [data-testid="stPageLink"][aria-current="page"] p,
      .st-key-ag_navbar [data-testid="stPageLink-NavLink"][aria-current="page"] p,
      .st-key-ag_navbar a.ag-nav-active p,
      .st-key-ag_navbar [data-testid="stPageLink"].ag-nav-active p {
        color: #0369a1 !important;
        font-weight: 700 !important;
        text-shadow: none !important;
      }
      .st-key-ag_navbar [data-testid="stHorizontalBlock"] a[aria-current="page"]:hover,
      .st-key-ag_navbar [data-testid="stHorizontalBlock"] a.ag-nav-active:hover,
      .st-key-ag_navbar a[aria-current="page"]:hover,
      .st-key-ag_navbar a.ag-nav-active:hover {
        background: transparent !important;
        background-color: transparent !important;
        transform: none !important;
      }

      /* More Popover Button inside the Pill: Pure transparent, pixel-aligned */
      .st-key-ag_navbar div[data-testid="stPopover"],
      .st-key-ag_navbar .stPopover,
      .st-key-ag_navbar [data-testid="stPopover"] {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 0 !important;
        padding: 0 !important;
        height: 100% !important;
      }
      .st-key-ag_navbar [data-testid="stHorizontalBlock"] [data-testid="stPopover"] button,
      .st-key-ag_navbar [data-testid="stHorizontalBlock"] .stPopover button,
      .st-key-ag_navbar [data-testid="stHorizontalBlock"] .stPopover > button,
      .st-key-ag_navbar div[data-testid="stPopover"] button,
      .st-key-ag_navbar div[data-testid="stPopover"] button:hover,
      .st-key-ag_navbar .stPopover > button,
      .st-key-ag_navbar .stPopover > button:hover,
      .st-key-ag_navbar div[data-testid="stPopover"] [data-testid="stBaseButton-secondary"],
      .st-key-ag_navbar div[data-testid="stPopover"] [data-testid="baseButton-secondary"],
      [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) [data-testid="stPopover"] button,
      [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) .stPopover button,
      [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) .stPopover > button,
      [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) button:not([data-testid="stPopoverButton"]):not(.ag-nav-active):not(#ag-nav-install-btn):not([aria-current="page"]),
      [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) [data-testid="stBaseButton-secondary"]:not(#ag-nav-install-btn) {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        border-radius: 9999px !important;
        height: 2.35rem !important;
        min-height: 2.35rem !important;
        padding: 0.45rem 1.15rem !important;
        box-shadow: none !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 0 !important;
        line-height: 1 !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
      }
      .st-key-ag_navbar [data-testid="stPopover"] button::before,
      .st-key-ag_navbar [data-testid="stPopover"] button::after {
        content: "" !important;
        display: block !important;
        position: relative !important;
        width: 18px !important;
        height: 2px !important;
        border-radius: 999px !important;
        background: #0284c7 !important;
        box-shadow: 0 6px 0 #0284c7, 0 -6px 0 #0284c7 !important;
      }
      .st-key-ag_navbar [data-testid="stPopover"] button:hover::before,
      .st-key-ag_navbar [data-testid="stPopover"] button:hover::after {
        background: #ffffff !important;
        box-shadow: 0 6px 0 #ffffff, 0 -6px 0 #ffffff !important;
      }
      @media (max-width: 840px) {
        .st-key-ag_navbar [data-testid="stHorizontalBlock"] [data-testid="stPopover"] button,
        .st-key-ag_navbar [data-testid="stHorizontalBlock"] .stPopover button,
        .st-key-ag_navbar [data-testid="stHorizontalBlock"] .stPopover > button,
        .st-key-ag_navbar div[data-testid="stPopover"] button,
        .st-key-ag_navbar .stPopover > button,
        .st-key-ag_navbar div[data-testid="stPopover"] [data-testid="stBaseButton-secondary"],
        [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) [data-testid="stPopover"] button,
        [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) .stPopover button,
        [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) .stPopover > button,
        [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) button:not(.ag-nav-active):not(#ag-nav-install-btn):not([aria-current="page"]) {
          padding: 0.4rem 0.8rem !important;
          min-height: 2rem !important;
          height: 2rem !important;
        }
        .st-key-ag_navbar [data-testid="stPopover"] button::before,
        .st-key-ag_navbar [data-testid="stPopover"] button::after {
          width: 16px !important;
          box-shadow: 0 5px 0 #0284c7, 0 -5px 0 #0284c7 !important;
        }
      }
      .st-key-ag_navbar div[data-testid="stPopover"] button::before,
      .st-key-ag_navbar div[data-testid="stPopover"] button::after,
      .st-key-ag_navbar [data-testid="stHorizontalBlock"] [data-testid="stPopover"] button::before,
      .st-key-ag_navbar [data-testid="stHorizontalBlock"] [data-testid="stPopover"] button::after {
        display: none !important;
        content: none !important;
      }
      .st-key-ag_navbar [data-testid="stHorizontalBlock"] [data-testid="stPopover"] button p,
      .st-key-ag_navbar [data-testid="stHorizontalBlock"] [data-testid="stPopover"] button span,
      .st-key-ag_navbar [data-testid="stHorizontalBlock"] [data-testid="stPopover"] button *,
      .st-key-ag_navbar div[data-testid="stPopover"] button p,
      .st-key-ag_navbar div[data-testid="stPopover"] button span,
      .st-key-ag_navbar div[data-testid="stPopover"] button * {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        color: #0a1f26 !important;
        letter-spacing: -0.01em !important;
        margin: 0 !important;
        line-height: 1 !important;
        visibility: visible !important;
        opacity: 1 !important;
        display: inline-block !important;
        text-shadow: none !important;
        transition: color 0.2s ease !important;
      }
      .st-key-ag_navbar [data-testid="stHorizontalBlock"] [data-testid="stPopover"] button:hover,
      .st-key-ag_navbar div[data-testid="stPopover"] button:hover {
        background: transparent !important;
        background-color: transparent !important;
        border: 2px solid #0875d1 !important;
        border-radius: 9999px !important;
        box-shadow: none !important;
        transform: translateY(-2px) scale(1.02) !important;
      }
      .st-key-ag_navbar [data-testid="stHorizontalBlock"] [data-testid="stPopover"] button:hover p,
      .st-key-ag_navbar [data-testid="stHorizontalBlock"] [data-testid="stPopover"] button:hover span,
      .st-key-ag_navbar [data-testid="stHorizontalBlock"] [data-testid="stPopover"] button:hover *,
      .st-key-ag_navbar div[data-testid="stPopover"] button:hover p,
      .st-key-ag_navbar div[data-testid="stPopover"] button:hover span,
      .st-key-ag_navbar div[data-testid="stPopover"] button:hover * {
        color: #0284c7 !important;
      }
      .st-key-ag_desktop_navbar [data-testid="stPopoverButton"] > div > div[aria-hidden="true"] {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        flex: 0 0 1rem !important;
        width: 1rem !important;
        height: 1rem !important;
      }

      .st-key-ag_desktop_navbar .st-key-lang_cycle_btn button,
      .st-key-ag_desktop_navbar .st-key-lang_cycle_btn button::before {
        color: #0284c7 !important;
      }

      /* Popover Dropdown Styling */
      div[data-testid="stPopoverBody"] {
        max-height: 520px !important;
        border-radius: 16px !important;
        border: none !important;
        background: #ffffff !important;
        box-shadow: 0 16px 40px rgba(4, 31, 38, 0.14), 0 4px 12px rgba(2, 132, 199, 0.08) !important;
        padding: 0.75rem 0.65rem !important;
      }
      div[data-testid="stPopoverBody"] [data-testid="stPageLink"],
      div[data-testid="stPopoverBody"] [data-testid="stPageLink-NavLink"] {
        min-height: 2.2rem !important;
        padding: 0.4rem 0.85rem !important;
        margin: 0.15rem 0 !important;
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        justify-content: flex-start !important;
      }
      div[data-testid="stPopoverBody"] [data-testid="stPageLink"] p,
      div[data-testid="stPopoverBody"] [data-testid="stPageLink-NavLink"] p {
        font-size: 0.86rem !important;
        font-weight: 600 !important;
        color: #0a1f26 !important;
      }
      div[data-testid="stPopoverBody"] [data-testid="stPageLink"]:hover,
      div[data-testid="stPopoverBody"] [data-testid="stPageLink-NavLink"]:hover {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        transform: none !important;
      }
      div[data-testid="stPopoverBody"] [data-testid="stPageLink"]:hover p,
      div[data-testid="stPopoverBody"] [data-testid="stPageLink-NavLink"]:hover p {
        color: #0284c7 !important;
      }
      div[data-testid="stPopoverBody"] [data-testid="stCaptionContainer"] p {
        color: #0284c7 !important;
        font-weight: 700 !important;
        font-size: 0.72rem !important;
        letter-spacing: 0.06em !important;
      }

      /* Hide any unwanted nested icons in links */
      [data-testid="stPageLink-NavLink"] span[data-testid="stIconMaterial"],
      [data-testid="stPageLink-NavLink"] svg:not([class*="custom"]),
      [data-testid="stPageLink-NavLink"] i {
        display: none !important;
      }

      /* =========================================================
         Sign In Capsule Button inside the Pill
         ========================================================= */
      .st-key-ag_navbar [data-testid="stPageLink"]:has(a[href*="Admin"]),
      .st-key-ag_navbar [data-testid="stPageLink-NavLink"]:has(a[href*="Admin"]),
      .st-key-ag_navbar a[href*="Admin"] {
        background: rgba(2, 132, 199, 0.08) !important;
        background-color: rgba(2, 132, 199, 0.08) !important;
        border: none !important;
        border-radius: 9999px !important;
        height: 2.35rem !important;
        min-height: 2.35rem !important;
        padding: 0.4rem 1.15rem !important;
        box-shadow: none !important;
        justify-content: center !important;
        text-align: center !important;
        display: inline-flex !important;
        align-items: center !important;
        text-decoration: none !important;
        line-height: 1 !important;
        margin: 0 !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
      }
      .st-key-ag_navbar [data-testid="stPageLink"]:has(a[href*="Admin"]) p,
      .st-key-ag_navbar [data-testid="stPageLink-NavLink"]:has(a[href*="Admin"]) p,
      .st-key-ag_navbar a[href*="Admin"] p {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 0.86rem !important;
        font-weight: 700 !important;
        color: #0284c7 !important;
        letter-spacing: -0.01em !important;
        margin: 0 !important;
        line-height: 1 !important;
        transition: color 0.2s ease !important;
      }
      .st-key-ag_navbar [data-testid="stPageLink"]:has(a[href*="Admin"]):hover,
      .st-key-ag_navbar [data-testid="stPageLink-NavLink"]:has(a[href*="Admin"]):hover,
      .st-key-ag_navbar a[href*="Admin"]:hover {
        border: none !important;
        background: #0284c7 !important;
        background-color: #0284c7 !important;
        box-shadow: 0 4px 14px rgba(2, 132, 199, 0.35) !important;
        transform: translateY(-1px) !important;
      }
      .st-key-ag_navbar [data-testid="stPageLink"]:has(a[href*="Admin"]):hover p,
      .st-key-ag_navbar [data-testid="stPageLink-NavLink"]:has(a[href*="Admin"]):hover p,
      .st-key-ag_navbar a[href*="Admin"]:hover p {
        color: #ffffff !important;
      }

      /* =========================================================
         Language Selector Button inside the Pill (Single Globe)
         ========================================================= */
      .st-key-ag_navbar .st-key-lang_cycle_btn,
      .st-key-ag_navbar .st-key-lang_cycle_btn > div {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 0 !important;
        padding: 0 !important;
      }
      .st-key-ag_navbar [data-testid="column"]:has(.st-key-lang_cycle_btn),
      .st-key-ag_mobile_navbar [data-testid="column"]:has(.st-key-lang_cycle_mobile_btn) {
        align-self: center !important;
        align-items: center !important;
        justify-content: center !important;
      }
      .st-key-ag_mobile_navbar .st-key-lang_cycle_mobile_btn,
      .st-key-ag_mobile_navbar .st-key-lang_cycle_mobile_btn > div {
        display: inline-flex !important;
        align-self: center !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 0 !important;
        padding: 0 !important;
      }
      .st-key-lang_cycle_btn button,
      .st-key-lang_cycle_mobile_btn button,
      .st-key-lang_cycle_btn button:hover,
      .st-key-lang_cycle_mobile_btn button:hover,
      .st-key-ag_navbar .st-key-lang_cycle_btn button,
      .st-key-ag_navbar .st-key-lang_cycle_btn button:hover,
      .st-key-ag_navbar [data-testid="stHorizontalBlock"] .st-key-lang_cycle_btn button,
      .st-key-ag_navbar [data-testid="stHorizontalBlock"] [data-testid="column"]:last-child button,
      .st-key-ag_navbar [data-testid="stHorizontalBlock"] [data-testid="stColumn"]:last-child button {
        background: rgba(2, 132, 199, 0.08) !important;
        background-color: rgba(2, 132, 199, 0.08) !important;
        border: none !important;
        border-radius: 50% !important;
        height: 2.35rem !important;
        min-height: 2.35rem !important;
        width: 2.35rem !important;
        box-shadow: none !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0 !important;
        margin: 0 !important;
        position: relative !important;
        align-self: center !important;
        vertical-align: middle !important;
      }
      .st-key-lang_cycle_btn button:hover,
      .st-key-lang_cycle_mobile_btn button:hover,
      .st-key-ag_navbar .st-key-lang_cycle_btn button:hover {
        background: #0284c7 !important;
        background-color: #0284c7 !important;
        border: none !important;
        box-shadow: 0 4px 14px rgba(2, 132, 199, 0.35) !important;
        transform: translateY(-1px) scale(1.05) !important;
      }
      .st-key-lang_cycle_btn button *,
      .st-key-lang_cycle_mobile_btn button * {
        font-size: 0 !important;
        color: transparent !important;
        line-height: 0 !important;
        max-width: 0 !important;
        max-height: 0 !important;
        overflow: hidden !important;
        visibility: hidden !important;
      }
      .st-key-lang_cycle_btn button::before,
      .st-key-lang_cycle_mobile_btn button::before {
        content: '' !important;
        display: block !important;
        width: 16px !important;
        height: 16px !important;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='%230284c7' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'%3E%3C/circle%3E%3Cline x1='2' y1='12' x2='22' y2='12'%3E%3C/line%3E%3Cpath d='M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z'%3E%3C/path%3E%3C/svg%3E") !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        background-size: contain !important;
        pointer-events: none !important;
        transition: all 0.25s ease !important;
      }
      .st-key-lang_cycle_btn button:hover::before,
      .st-key-lang_cycle_mobile_btn button:hover::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='%23ffffff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'%3E%3C/circle%3E%3Cline x1='2' y1='12' x2='22' y2='12'%3E%3C/line%3E%3Cpath d='M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z'%3E%3C/path%3E%3C/svg%3E") !important;
        transform: rotate(18deg) scale(1.1) !important;
      }

      /* Subtle theme divider */
      .ag-nav-rule {
        border: 0;
        height: 1px;
        background: transparent;
        margin: 0.1rem 0 0.5rem;
      }

      /* Clean Light Styling for Streamlit Tabs across all views */
      [data-testid="stTabs"], .stTabs { background: transparent !important; }
      [data-testid="stTabs"] [data-baseweb="tab-list"],
      .stTabs [data-baseweb="tab-list"],
      [data-testid="stTabs"] div[role="tablist"],
      .stTabs div[role="tablist"] {
        background: rgba(255, 255, 255, 0.85) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border-radius: 14px !important;
        padding: 4px 8px !important;
        border: 1px solid rgba(2, 132, 199, 0.20) !important;
        box-shadow: 0 4px 14px rgba(4, 31, 38, 0.05) !important;
        gap: 6px !important;
      }
      [data-testid="stTabs"] button[role="tab"],
      [data-testid="stTabs"] [data-baseweb="tab"],
      [data-testid="stTabs"] button,
      .stTabs button[role="tab"],
      .stTabs [data-baseweb="tab"],
      .stTabs button,
      [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stTabs"] button,
      [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stTabs"] [role="tab"],
      [data-testid="stVerticalBlockBorderWrapper"] [data-baseweb="tab"] {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 8px 18px !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 0.90rem !important;
        font-weight: 600 !important;
        color: #334155 !important;
        box-shadow: none !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
      }
      [data-testid="stTabs"] button[role="tab"] p,
      [data-testid="stTabs"] [data-baseweb="tab"] p,
      [data-testid="stTabs"] button p,
      .stTabs button[role="tab"] p,
      .stTabs [data-baseweb="tab"] p {
        color: #334155 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 600 !important;
      }
      [data-testid="stTabs"] button[role="tab"]:hover,
      [data-testid="stTabs"] [data-baseweb="tab"]:hover,
      [data-testid="stTabs"] button:hover,
      .stTabs button[role="tab"]:hover,
      .stTabs [data-baseweb="tab"]:hover {
        background: rgba(2, 132, 199, 0.08) !important;
        background-color: rgba(2, 132, 199, 0.08) !important;
        color: #0284c7 !important;
        box-shadow: none !important;
        transform: none !important;
      }
      [data-testid="stTabs"] button[role="tab"][aria-selected="true"],
      [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"],
      [data-testid="stTabs"] button[aria-selected="true"],
      .stTabs button[role="tab"][aria-selected="true"],
      .stTabs [data-baseweb="tab"][aria-selected="true"],
      [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stTabs"] button[aria-selected="true"] {
        background: #ffffff !important;
        background-color: #ffffff !important;
        color: #0284c7 !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 8px rgba(2, 132, 199, 0.15), 0 1px 3px rgba(0, 0, 0, 0.06) !important;
        border-bottom: 2.5px solid #0284c7 !important;
      }
      [data-testid="stTabs"] button[role="tab"][aria-selected="true"] p,
      [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] p {
        color: #0284c7 !important;
        font-weight: 700 !important;
      }

      @media(max-width:950px) {
        .st-key-ag_navbar [data-testid="stHorizontalBlock"],
        [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) {
          flex-wrap: wrap !important;
          border-radius: 20px !important;
          gap: 0.5rem !important;
        }
      }
      @media(max-width:768px) {
        .block-container,
        [data-testid="stMainBlockContainer"],
        [data-testid="stAppViewBlockContainer"],
        .main .block-container {
          padding-top: 0.2rem !important;
          padding-left: 1rem !important;
          padding-right: 1rem !important;
        }
        .st-key-ag_navbar {
          top: 0.2rem !important;
          margin-bottom: 0.4rem !important;
          padding: 0 !important;
        }
        .st-key-ag_navbar [data-testid="stHorizontalBlock"] {
          flex-wrap: wrap !important;
          justify-content: center !important;
          gap: 0.15rem 0.4rem !important;
          padding: 0.35rem 0.45rem !important;
          border-radius: 16px !important;
        }
        .st-key-ag_navbar [data-testid="column"] {
          flex: 0 1 auto !important;
          width: auto !important;
          min-width: max-content !important;
        }
        .st-key-ag_navbar [data-testid="stPageLink"] a,
        .st-key-ag_navbar [data-testid="stPopover"] > button,
        .st-key-ag_navbar [data-testid="stPopover"] button {
          min-height: 42px !important;
          padding: 0.4rem 0.7rem !important;
          font-size: 0.84rem !important;
        }
      }

      /* Borderless navbar with a lively, soft hover treatment */
      .st-key-ag_navbar [data-testid="stHorizontalBlock"],
      [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) {
        border: none !important;
      }
      .st-key-ag_navbar [data-testid="stPageLink"],
      .st-key-ag_navbar [data-testid="stPageLink-NavLink"],
      .st-key-ag_navbar [data-testid="stPageLink"] a,
      .st-key-ag_navbar [data-testid="stPageLink-NavLink"] a,
      .st-key-ag_navbar [data-testid="stPopover"] > button,
      .st-key-ag_navbar [data-testid="stPopover"] button {
        border: none !important;
        transition: transform 180ms cubic-bezier(0.2, 0.8, 0.2, 1),
                    background 180ms ease, color 180ms ease, box-shadow 180ms ease !important;
      }
      .st-key-ag_navbar [data-testid="stPageLink"]:hover,
      .st-key-ag_navbar [data-testid="stPageLink-NavLink"]:hover,
      .st-key-ag_navbar [data-testid="stPageLink"] a:hover,
      .st-key-ag_navbar [data-testid="stPageLink-NavLink"] a:hover,
      .st-key-ag_navbar [data-testid="stPopover"] > button:hover,
      .st-key-ag_navbar [data-testid="stPopover"] button:hover {
        border: none !important;
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
        transform: translateY(-2px) scale(1.035) !important;
      }
      .st-key-ag_navbar [data-testid="stPageLink"][aria-current="page"],
      .st-key-ag_navbar [data-testid="stPageLink-NavLink"][aria-current="page"],
      .st-key-ag_navbar a[aria-current="page"],
      .st-key-ag_navbar [data-testid="stPageLink"].ag-nav-active,
      .st-key-ag_navbar [data-testid="stPageLink-NavLink"].ag-nav-active,
      .st-key-ag_navbar a.ag-nav-active {
        box-sizing: border-box !important;
        border: none !important;
        border-radius: 9999px !important;
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
      }
      .st-key-ag_navbar a[aria-current="page"],
      .st-key-ag_navbar a.ag-nav-active {
        box-sizing: border-box !important;
        border: 2px solid #0875d1 !important;
        border-radius: 9999px !important;
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
      }
      .st-key-ag_navbar [data-testid="stPageLink"][aria-current="page"]:hover,
      .st-key-ag_navbar [data-testid="stPageLink-NavLink"][aria-current="page"]:hover,
      .st-key-ag_navbar a[aria-current="page"]:hover,
      .st-key-ag_navbar [data-testid="stPageLink"].ag-nav-active:hover,
      .st-key-ag_navbar [data-testid="stPageLink-NavLink"].ag-nav-active:hover,
      .st-key-ag_navbar a.ag-nav-active:hover {
        border: none !important;
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
        transform: none !important;
      }
      .st-key-ag_navbar a[aria-current="page"]:hover,
      .st-key-ag_navbar a.ag-nav-active:hover {
        border: 2px solid #0875d1 !important;
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
        transform: none !important;
      }
      .st-key-ag_navbar [data-testid="stPageLink"] a:hover,
      .st-key-ag_navbar [data-testid="stPageLink-NavLink"] a:hover,
      .st-key-ag_navbar a[data-testid="stPageLink-NavLink"]:hover {
        box-sizing: border-box !important;
        border: 2px solid #0875d1 !important;
        border-radius: 9999px !important;
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
      }
      div[data-testid="stPopoverBody"],
      div[data-testid="stPopoverBody"] [data-testid="stPageLink"],
      div[data-testid="stPopoverBody"] [data-testid="stPageLink-NavLink"],
      .st-key-ag_navbar [data-testid="stPageLink"]:has(a[href*="Admin"]),
      .st-key-ag_navbar [data-testid="stPageLink-NavLink"]:has(a[href*="Admin"]),
      .st-key-ag_navbar a[href*="Admin"],
      .st-key-ag_navbar .stButton > button,
      #ag-nav-install-btn,
      div[data-testid="stPopoverBody"] a[href*="offline.html"],
      .st-key-ag_navbar .st-key-lang_cycle_btn button {
        border: none !important;
      }
      div[data-testid="stPopoverBody"] [data-testid="stPageLink"]:hover,
      div[data-testid="stPopoverBody"] [data-testid="stPageLink-NavLink"]:hover {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        transform: none !important;
      }
      .st-key-ag_navbar .stButton > button:hover {
        border: 2px solid #0875d1 !important;
        border-radius: 9999px !important;
        background: transparent !important;
        color: #0369a1 !important;
        box-shadow: none !important;
        transform: translateY(-2px) scale(1.02) !important;
      }
      /* A Streamlit page link has a wrapper and a clickable anchor; outline only the anchor. */
      div[data-testid="stPopoverBody"] [data-testid="stPageLink"]:hover {
        border: none !important;
        border-radius: 0 !important;
        background: transparent !important;
        box-shadow: none !important;
        transform: none !important;
      }
      div[data-testid="stPopoverBody"] [data-testid="stPageLink-NavLink"]:hover {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        transform: none !important;
      }
      .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stPopoverButton"] [data-testid="stIconMaterial"] {
        color: #0284c7 !important;
      }
      .st-key-ag_desktop_navbar .st-key-ag_navbar .st-key-lang_cycle_btn button:not(#ag-nav-install-btn):hover {
        background: rgba(2, 132, 199, 0.08) !important;
        background-color: rgba(2, 132, 199, 0.08) !important;
        color: #0284c7 !important;
      }
      .st-key-ag_desktop_navbar .st-key-ag_navbar .st-key-lang_cycle_btn button:not(#ag-nav-install-btn):hover::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='%230284c7' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'%3E%3C/circle%3E%3Cline x1='2' y1='12' x2='22' y2='12'%3E%3C/line%3E%3Cpath d='M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z'%3E%3C/path%3E%3C/svg%3E") !important;
      }
      .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stPopover"] button {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 2.35rem !important;
        min-width: 2.35rem !important;
        max-width: 2.35rem !important;
        min-height: 2.35rem !important;
        padding: 0 !important;
        flex: 0 0 2.35rem !important;
        border: 1px solid rgba(2, 132, 199, 0.24) !important;
        border-radius: 9999px !important;
        background: rgba(2, 132, 199, 0.08) !important;
        color: #0a1f26 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 6px rgba(2, 132, 199, 0.08) !important;
        opacity: 1 !important;
        visibility: visible !important;
      }
      html body [data-testid="stAppViewContainer"] .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stHorizontalBlock"] [data-testid="stPopover"] button {
        background: rgba(2, 132, 199, 0.1) !important;
        background-color: rgba(2, 132, 199, 0.1) !important;
        border: 1px solid rgba(2, 132, 199, 0.28) !important;
        color: #0a1f26 !important;
      }
      html body [data-testid="stAppViewContainer"] .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stHorizontalBlock"] [data-testid="stPopover"] button:hover {
        background: #0284c7 !important;
        background-color: #0284c7 !important;
        border-color: #0284c7 !important;
        color: #ffffff !important;
      }
      .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stPopover"] button:hover {
        border-color: #0284c7 !important;
        background: #0284c7 !important;
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.24) !important;
      }
      .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stPopover"] button > div,
      .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stPopover"] button > div > div {
        display: inline-flex !important;
        align-items: center !important;
        width: auto !important;
        min-width: max-content !important;
        max-width: none !important;
        height: auto !important;
        max-height: none !important;
        overflow: visible !important;
      }
      .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stPopover"] button p {
        display: none !important;
      }
      .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stPopover"] button:hover p,
      .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stPopover"] button:hover [data-testid="stIconMaterial"] {
        color: #ffffff !important;
      }
      .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stPopover"] button > div > div:first-child,
      .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stPopover"] button > div > div:first-child span,
      .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stPopover"] button [data-testid="stMarkdownContainer"] {
        width: auto !important;
        min-width: max-content !important;
        height: auto !important;
        max-height: none !important;
        max-width: none !important;
        overflow: visible !important;
      }
      .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stPopover"] button [data-testid="stIconMaterial"] {
        display: none !important;
      }
      .st-key-ag_desktop_navbar .st-key-ag_navbar .st-key-lang_cycle_btn button {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 2.35rem !important;
        min-width: 2.35rem !important;
        max-width: 2.35rem !important;
        height: 2.35rem !important;
        min-height: 2.35rem !important;
        padding: 0 !important;
        flex: 0 0 2.35rem !important;
        position: relative !important;
      }
      .st-key-ag_desktop_navbar .st-key-ag_navbar .st-key-lang_cycle_btn button::before {
        content: "" !important;
        display: block !important;
        position: absolute !important;
        left: 50% !important;
        top: 50% !important;
        width: 18px !important;
        min-width: 18px !important;
        height: 18px !important;
        transform: translate(-50%, -50%) !important;
        background: no-repeat center / contain url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%230284c7' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'/%3E%3Cpath d='M2 12h20M12 2a15 15 0 0 1 0 20M12 2a15 15 0 0 0 0 20'/%3E%3C/svg%3E") !important;
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: none !important;
      }
      @media (max-width: 840px) {
        .st-key-ag_mobile_navbar .st-key-lang_cycle_mobile_btn button {
          width: 42px !important;
          min-width: 42px !important;
          height: 42px !important;
          min-height: 42px !important;
          align-self: center !important;
        }
      }
      .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stHorizontalBlock"] {
        box-sizing: border-box !important;
        width: min(100%, 820px) !important;
        max-width: 820px !important;
        flex-wrap: nowrap !important;
        gap: 0.35rem !important;
        padding: 0.7rem 1rem !important;
        border: 1px solid #e8eef5 !important;
        border-radius: 9999px !important;
        background: #ffffff !important;
        box-shadow: 0 8px 24px rgba(44, 112, 190, 0.12) !important;
      }
      .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stPageLink"] a,
      .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stPageLink-NavLink"] {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        min-height: 3rem !important;
        padding: 0.65rem 1.35rem !important;
        border: 0 !important;
        border-radius: 9999px !important;
        background: transparent !important;
        color: #536174 !important;
        font-size: 0.98rem !important;
        font-weight: 500 !important;
        text-decoration: none !important;
        white-space: nowrap !important;
        box-shadow: none !important;
        transform: none !important;
      }
      .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stPageLink"] a p,
      .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stPageLink-NavLink"] p {
        color: inherit !important;
        font-size: inherit !important;
        font-weight: inherit !important;
      }
      .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stPageLink"] a[aria-current="page"],
      .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stPageLink-NavLink"][aria-current="page"] {
        background: #328ff0 !important;
        color: #ffffff !important;
        box-shadow: 0 4px 10px rgba(50, 143, 240, 0.24) !important;
      }
      .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stPageLink"] a[aria-current="page"] p,
      .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stPageLink-NavLink"][aria-current="page"] p {
        color: #ffffff !important;
      }
      .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stPageLink"] a:hover:not([aria-current="page"]),
      .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stPageLink-NavLink"]:hover:not([aria-current="page"]) {
        background: #f3f7fc !important;
        color: #287bc9 !important;
      }
      .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stPopover"] button {
        width: 3.2rem !important;
        min-width: 3.2rem !important;
        max-width: 3.2rem !important;
        height: 3.2rem !important;
        min-height: 3.2rem !important;
        flex-basis: 3.2rem !important;
        border: 1px solid #e0e5ec !important;
        border-radius: 50% !important;
        background: #eef0f3 !important;
        box-shadow: none !important;
      }
      .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stPopover"] button::before {
        content: "" !important;
        display: block !important;
        width: 1.45rem !important;
        height: 1.45rem !important;
        background: no-repeat center / contain url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%236b7280'%3E%3Cpath d='M12 12a5 5 0 1 0 0-10 5 5 0 0 0 0 10Zm0 2c-4.42 0-8 2.24-8 5v2h16v-2c0-2.76-3.58-5-8-5Z'/%3E%3C/svg%3E") !important;
        box-shadow: none !important;
      }
      .st-key-ag_desktop_navbar .st-key-ag_navbar .st-key-lang_cycle_btn button {
        width: 3.2rem !important;
        min-width: 3.2rem !important;
        max-width: 3.2rem !important;
        height: 3.2rem !important;
        min-height: 3.2rem !important;
        flex-basis: 3.2rem !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 50% !important;
        background: #ffffff !important;
        box-shadow: none !important;
      }
      .st-key-ag_desktop_navbar .st-key-ag_navbar .st-key-lang_cycle_btn button::before {
        width: 1.55rem !important;
        height: 1.55rem !important;
        background-size: contain !important;
      }
      .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stPageLink"] a[aria-current="page"],
      .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stPageLink-NavLink"][aria-current="page"] {
        border: 2px solid #0875d1 !important;
        background: #ffffff !important;
        color: #0875d1 !important;
        box-shadow: none !important;
      }
      .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stPageLink"] a[aria-current="page"] p,
      .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stPageLink-NavLink"][aria-current="page"] p {
        color: #0875d1 !important;
      }
      html body [data-testid="stAppViewContainer"] .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stHorizontalBlock"] [data-testid="stPopover"] button {
        border: 0 !important;
        border-radius: 0 !important;
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
      }
      html body [data-testid="stAppViewContainer"] .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stHorizontalBlock"] [data-testid="stPopover"] button:hover {
        border: 0 !important;
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
        color: inherit !important;
        filter: none !important;
        transform: none !important;
      }
      html body [data-testid="stAppViewContainer"] .st-key-ag_desktop_navbar .st-key-ag_navbar [data-testid="stHorizontalBlock"] [data-testid="stPopover"] button:hover::before {
        background: no-repeat center / contain url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%236b7280'%3E%3Cpath d='M12 12a5 5 0 1 0 0-10 5 5 0 0 0 0 10Zm0 2c-4.42 0-8 2.24-8 5v2h16v-2c0-2.76-3.58-5-8-5Z'/%3E%3C/svg%3E") !important;
        background-color: transparent !important;
        transform: none !important;
        filter: none !important;
        transition: none !important;
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
                st.page_link("pages/dashboard.py", label=t("nav.overview", "Overview"))

            if auth:
                with c_zones:
                    st.page_link("pages/4_Zones.py", label=t("nav.zones", "Zones"))
                with c_decide:
                    st.page_link("pages/6_Decision_Making.py", label=t("nav.decisions", "Decisions"))
                with c_more:
                    with st.popover(
                        " ",
                        help=t("nav.more", "More"),
                        width="stretch",
                    ):
                        st.divider()
                        st.caption(t("nav.operations_tools", "OPERATIONS & TOOLS"))
                        st.page_link("pages/8_Planning.py", label=t("nav.planning_short", "season-plan"))
                        st.page_link("pages/9_Communication.py", label=t("nav.comms_short", "field-alerts"))
                        st.page_link("pages/5_Segmentation.py", label=t("nav.segmentation_short", "zone-seg"))
                        st.page_link("pages/7_AI_Assistant.py", label=t("nav.ai_assistant_short", "AI-assist"))
                        st.divider()
                        st.caption(t("nav.platform_community", "PLATFORM & COMMUNITY"))
                        st.page_link("pages/10_Admin.py", label=t("nav.admin_short", "admin"))
                        st.page_link("pages/99_Showcase.py", label=t("nav.data_guide_short", "data-guide"))
                        st.page_link("pages/12_Community.py", label=t("nav.community_short", "community"))
                        st.page_link("pages/1_About.py", label=t("nav.about_short", "about"))
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
                    st.page_link("pages/12_Community.py", label=t("nav.farmer_login", "Farmer login"))
                with c_sep:
                    st.empty()

            with c_lang:
                render_language_selector(sidebar=False)

    with st.container(key="ag_mobile_navbar"):
        mobile_menu_col, mobile_language_col = st.columns([1, 1], vertical_alignment="center")
        with mobile_menu_col:
            with st.popover("☰", help="Open navigation menu", width="content"):
                st.page_link("Home.py", label=t("nav.home", "Home"))
                st.page_link("pages/dashboard.py", label=t("nav.overview", "Overview"))
                if auth:
                    st.page_link("pages/4_Zones.py", label=t("nav.zones", "Zones"))
                    st.page_link("pages/6_Decision_Making.py", label=t("nav.decisions", "Decisions"))
                    st.divider()
                    st.page_link("pages/8_Planning.py", label=t("nav.planning_short", "season-plan"))
                    st.page_link("pages/9_Communication.py", label=t("nav.comms_short", "field-alerts"))
                    st.page_link("pages/5_Segmentation.py", label=t("nav.segmentation_short", "zone-seg"))
                    st.page_link("pages/7_AI_Assistant.py", label=t("nav.ai_assistant_short", "AI-assist"))
                    st.page_link("pages/10_Admin.py", label=t("nav.admin_short", "admin"))
                    st.page_link("pages/99_Showcase.py", label=t("nav.data_guide_short", "data-guide"))
                    st.page_link("pages/12_Community.py", label=t("nav.community_short", "community"))
                    st.page_link("pages/1_About.py", label=t("nav.about_short", "about"))
                    if st.button(t("nav.sign_out", "Sign out"), key="mobile_nav_signout_btn", use_container_width=True):
                        st.session_state["authenticated"] = False
                        st.rerun()
                else:
                    st.page_link("pages/9_Communication.py", label=t("nav.updates", "Updates"))
                    st.page_link("pages/1_About.py", label=t("nav.about", "About"))
                    st.page_link("pages/12_Community.py", label=t("nav.farmer_login", "Farmer login"))
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
