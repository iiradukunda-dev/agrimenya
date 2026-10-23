"""Concise landing page message for the Agri-Menya workspace."""
import streamlit as st

from utils import api_client
from utils.i18n import get_current_language


def render_home_hero() -> None:
    rw = get_current_language() == "rw"
    kicker = "UBUHINZI BW'U RWANDA" if rw else "RWANDA AGRICULTURE"
    title = "Ibyemezo bishingiye ku makuru." if rw else "Decisions grounded in data."
    detail = (
        "Hitamo urupapuro muri menu iri ku ruhande kugira ngo utangire."
        if rw else "Choose a workspace from the sidebar to begin."
    )
    st.markdown(
        f"""<section style="background:#163b2a;color:#f6faf6;border-radius:16px;padding:clamp(2rem,5vw,4rem);margin:.5rem 0 1rem">
        <div style="font-size:.75rem;letter-spacing:.12em;font-weight:650;color:#d6e8d9">{kicker}</div>
        <h1 style="color:white!important;font-size:clamp(2rem,5vw,3.4rem)!important;margin:.7rem 0 1rem;letter-spacing:-.04em">{title}</h1>
        <p style="color:#e3eee5;font-size:1rem;margin:0">{detail}</p>
        </section>""",
        unsafe_allow_html=True,
    )

    # A single searchable entry point helps people reach the right workflow
    # without needing to know the page structure first.
    zones = api_client.get_zones()
    crops = api_client.get_crops()
    districts = api_client.get_districts()
    destinations: dict[str, tuple[str, str | None]] = {}
    for title, page in [
        ("Dashboard", "pages/3_Dashboard.py"),
        ("Agricultural zones", "pages/4_Zones.py"),
        ("Segmentation and crop priorities", "pages/5_Segmentation.py"),
        ("Decision making", "pages/6_Decision_Making.py"),
        ("AI assistant", "pages/7_AI_Assistant.py"),
        ("Seasonal planning", "pages/8_Planning.py"),
        ("Communication", "pages/9_Communication.py"),
        ("Farmer community", "pages/12_Community.py"),
        ("Administration", "pages/10_Admin.py"),
        ("Contact and feedback", "pages/11_Contact.py"),
        ("Settings", "pages/13_Settings.py"),
    ]:
        destinations[f"Workspace · {title}"] = ("page", page)
    for crop in sorted({str(c).strip() for c in crops if str(c).strip()}, key=str.casefold):
        destinations[f"Crop · {crop}"] = ("crop", crop)
    for district in districts:
        name = str(district.get("district") or "").strip()
        if name:
            destinations[f"District · {name}"] = ("district", name)
    for zone in zones:
        zone_id = str(zone.get("id") or "")
        if not zone_id:
            continue
        label = " / ".join(str(value) for value in (
            zone.get("district"), zone.get("sector"), zone.get("cell"),
            zone.get("crop_type") or zone.get("crop"),
        ) if value)
        destinations[f"Zone · {label or zone_id[:8]} · {zone_id[-6:]}"] = ("zone", zone_id)

    st.markdown("### Find a service, crop, or zone")
    st.caption("Search by task, crop, district, or saved zone. Choose a result to open it.")
    labels = ["Search Agri-Menya"] + list(destinations)
    with st.form("home_search_form"):
        choice = st.selectbox(
            "Search Agri-Menya",
            labels,
            label_visibility="collapsed",
            key="home_global_search",
            placeholder="Search services, crops, districts, or zones…",
        )
        search_submitted = st.form_submit_button("Open result", type="primary")
    if search_submitted and choice != labels[0]:
        kind, value = destinations[choice]
        if kind == "page":
            st.switch_page(value)
        elif kind == "zone":
            st.session_state["zone_focus_id"] = value
            st.switch_page("pages/4_Zones.py")
        elif kind == "district":
            st.session_state["zones_district_filter"] = [value]
            st.switch_page("pages/4_Zones.py")
        else:
            st.session_state["segment_crop_filter"] = [value]
            st.switch_page("pages/5_Segmentation.py")

    st.markdown("### Choose what you want to do")
    st.caption("Each workspace has one clear purpose. Results depend on the evidence available for the selected area and task.")
    cards = [
        ("Review local areas", "Open saved zones, local records, and field observations.", "pages/4_Zones.py"),
        ("Compare crop priorities", "Explore crop and district evidence by segment.", "pages/5_Segmentation.py"),
        ("Make a decision", "Compare NISR crop evidence and identify follow-up checks.", "pages/6_Decision_Making.py"),
        ("Plan work and resources", "Build a practical plan for a saved zone.", "pages/8_Planning.py"),
        ("Ask about evidence", "Get an explanation grounded in available project data.", "pages/7_AI_Assistant.py"),
        ("Communication", "Read current alerts and review WhatsApp delivery tools.", "pages/9_Communication.py"),
        ("Farmer community", "Share questions, replies, or local field observations.", "pages/12_Community.py"),
        ("Administration", "Manage system operations and review community reports.", "pages/10_Admin.py"),
        ("Contact and feedback", "Send a question, issue, or product suggestion.", "pages/11_Contact.py"),
        ("Settings", "Manage language, active sessions, and this session’s AI conversation.", "pages/13_Settings.py"),
    ]
    for start in range(0, len(cards), 3):
        columns = st.columns(3)
        for column, (title, description, page) in zip(columns, cards[start:start + 3]):
            with column, st.container(border=True):
                st.markdown(f"#### {title}")
                st.caption(description)
                if st.button("Open", key=f"home_open_{page}", width="stretch"):
                    st.switch_page(page)
