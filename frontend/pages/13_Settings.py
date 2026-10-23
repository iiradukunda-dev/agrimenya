"""User-facing preferences and current-session controls."""
import os
import time

import streamlit as st
from components.navbar import render_navbar
from utils.api_client import admin_session_authenticated
from utils.i18n import get_current_language
from utils.theme import load_theme
from utils.timezone import setup_system_timezone

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "logo.jpg")

st.set_page_config(page_title="Settings - Agri-Menya", page_icon=LOGO_PATH, layout="wide")
setup_system_timezone()
load_theme()
render_navbar()

rw = get_current_language() == "rw"
st.title("Igenamiterere" if rw else "Settings")
st.caption(
    "Hitamo ururimi, urebe amasomo yawe y'igihe gito kandi usibe ibiganiro by'umufasha wa AI."
    if rw else "Manage language, review active sign-in sessions, and clear this session’s AI conversation."
)

st.subheader("Ibyo ukunda" if rw else "Preferences")
left, right = st.columns(2)
with left, st.container(border=True):
    st.markdown("**Ururimi / Language**")
    st.write("Ikinyarwanda" if rw else "English")
    st.caption(
        "Hindura ururimi ukoresheje akamenyetso ko guhitamo ururimi kari hejuru y'urupapuro."
        if rw else "Change the language with the selector in the page header. Your choice applies across the app session."
    )
with right, st.container(border=True):
    st.markdown("**Akarere k'isaha / Time zone**")
    st.write("Africa/Kigali · CAT (UTC+2)")
    st.caption("The application currently uses Rwanda time for displayed dates and schedules.")

st.subheader("Amasomo yinjiyemo" if rw else "Sign-in sessions")
community_token = st.session_state.get("community_access_token")
community_expiry = st.session_state.get("community_access_token_expires_at")
if community_token and (community_expiry is None or time.time() >= community_expiry):
    st.session_state.pop("community_access_token", None)
    st.session_state.pop("community_access_token_expires_at", None)
    st.session_state.pop("community_account", None)
    community_token = None

community_col, admin_col = st.columns(2)
with community_col, st.container(border=True):
    st.markdown("**Farmer Community**")
    if community_token:
        account = st.session_state.get("community_account") or {}
        remaining = max(0, int(community_expiry - time.time()))
        st.success(f"Signed in as {account.get('display_name') or 'community member'}")
        st.caption(f"This session expires in about {max(1, remaining // 60)} minutes.")
        if st.button("Sign out of Community", key="settings_community_signout"):
            for key in ("community_access_token", "community_access_token_expires_at", "community_account"):
                st.session_state.pop(key, None)
            st.rerun()
    else:
        st.info("No active Community sign-in session." if not rw else "Nta konti y'umuryango yinjiye.")

with admin_col, st.container(border=True):
    st.markdown("**Administrator**")
    if admin_session_authenticated():
        identity = st.session_state.get("admin_identity") or {}
        remaining = max(0, int(st.session_state.get("admin_session_expires_at", time.monotonic()) - time.monotonic()))
        st.success(f"Signed in as {identity.get('display_name') or identity.get('email') or 'administrator'}")
        st.caption(f"This session expires in about {max(1, remaining // 60)} minutes.")
        if st.button("Sign out of Admin", key="settings_admin_signout"):
            for key in ("admin_session_expires_at", "admin_access_token", "admin_identity"):
                st.session_state.pop(key, None)
            st.rerun()
    else:
        st.info("No active administrator session." if not rw else "Nta muyobozi winjiye.")

st.subheader("Ikiganiro cya AI" if rw else "AI Assistant")
st.caption(
    "Ibiganiro bibitswe mu gihe cy'iyi session ya Streamlit gusa; ntibibikwa muri konti yawe."
    if rw else "The current AI conversation is held in this Streamlit session; it is not saved as an account history."
)
if st.button("Siba ikiganiro" if rw else "Clear AI conversation", key="settings_clear_ai"):
    for key in ("ai_messages", "active_decision_ai_context", "assistant_decision_signature", "assistant_suggested_question"):
        st.session_state.pop(key, None)
    st.success("Ikiganiro cyasibwe." if rw else "AI conversation cleared from this session.")

with st.expander("About sign-in and privacy" if not rw else "Ibyerekeye kwinjira n'ibanga"):
    st.write(
        "Community and administrator sign-ins are held in Streamlit's server-side session state and expire automatically. "
        "The app does not use persistent browser login cookies, so a browser refresh or lost session may require signing in again."
        if not rw else
        "Konti z'abahinzi n'abayobozi zibikwa mu gihe cya Streamlit kandi zirangira. "
        "Porogaramu ntikoresha cookies zo kuguma winjiye; ushobora kongera kwinjira nyuma yo kongera gufungura urubuga."
    )
