"""
AI Assistant view: conversational AI + crop disease detection.

Implements Page 4 of the frontend handoff: chat + disease detection.
"""
import logging

import requests
import streamlit as st
from components.ai_response import render_advisor_response
from components.badges import priority_badge
from components.errors import error_boundary, render_error_page
from components.icons import render_icon_subheader, render_icon_title
from utils import api_client
from utils.i18n import t
from utils.mock_data import CROPS

logger = logging.getLogger(__name__)


def _init_chat_state() -> None:
    """Initialize session state for zone-scoped chat history."""
    if "ai_messages_by_zone" not in st.session_state:
        st.session_state.ai_messages_by_zone = {}


@error_boundary("AI Assistant")
def render_ai_assistant() -> None:
    try:
        render_icon_title(
            "assets/bot.svg",
            t("ai.title", "AI Assistant"),
            t("ai.subtitle", "Ask questions about zones, get recommendations, and detect crop diseases"),
        )

        _init_chat_state()

        with st.spinner("Checking for live zone data..."):
            zones = api_client.get_zones(
                timeout=3,
                retry_on_transient=False,
                include_map=False,
            )

        # ── Layout: Chat + Disease Detection ─────────────────────────
        chat_tab, disease_tab = st.tabs([t("ai.tab.advisor", "AI Advisor"), t("ai.tab.disease", "Disease Detection")])

        # ═════════════════════════════════════════════════════════════
        # TAB 1: AI Chat
        # ═════════════════════════════════════════════════════════════
        with chat_tab:
            crop_options = api_client.get_offline_nisr_crops() or CROPS
            selected_zone = None
            selected_zone_id = None
            offline_district = None

            if zones:
                zone_labels = [
                    f"{z.get('district', 'Unknown district')} / {z.get('sector') or z.get('cell') or z.get('id')}"
                    for z in zones
                ]
                zone_by_label = dict(zip(zone_labels, zones))
                selected_zone_label = st.selectbox(
                    t("ai.zone_ctx", "Zone context"), zone_labels, key="ai_zone_ctx"
                )
                selected_zone = zone_by_label.get(selected_zone_label)
                selected_zone_id = selected_zone.get("id") if selected_zone else None
                crop_selection = st.selectbox(
                    "Crop context",
                    ["No specific crop", *crop_options],
                    key="ai_crop_ctx",
                )
                selected_crop = None if crop_selection == "No specific crop" else crop_selection
            else:
                fallback_notice = (
                    "The live API is unavailable."
                    if st.session_state.get("zones_api_unavailable")
                    else "No saved live zone is available."
                )
                st.info(
                    f"{fallback_notice} You can still ask about historical NISR "
                    "crop yields; zone-specific actions and AI-generated answers need the API."
                )
                selected_crop = st.selectbox(
                    "NISR crop", crop_options, key="ai_crop_ctx_offline"
                ) if crop_options else None
                offline_district_options = (
                    ["All districts", *api_client.get_offline_nisr_districts(selected_crop)]
                    if selected_crop else ["All districts"]
                )
                district_selection = st.selectbox(
                    "NISR district",
                    offline_district_options,
                    key=f"ai_district_ctx_offline_{selected_crop}",
                )
                offline_district = (
                    None if district_selection == "All districts" else district_selection
                )

            selected_season = None
            if selected_crop:
                seasons = api_client.get_offline_nisr_seasons(selected_crop)
                if seasons:
                    season_options = ["All available seasons", *seasons]
                    selected_season = st.selectbox(
                        "Season context",
                        season_options,
                        key=(
                            f"ai_season_ctx_zone_{selected_crop}"
                            if selected_zone_id
                            else f"ai_season_ctx_offline_{selected_crop}"
                        ),
                    )
                    if selected_season == "All available seasons":
                        selected_season = None

            conversation_key = "|".join(
                (
                    str(selected_zone_id or offline_district or "nisr"),
                    str(selected_crop or ""),
                    str(selected_season or ""),
                )
            )
            messages = st.session_state.ai_messages_by_zone.setdefault(conversation_key, [])
            for msg in messages:
                with st.chat_message(msg["role"]):
                    if msg["role"] == "assistant" and isinstance(msg.get("response"), dict):
                        render_advisor_response(msg["response"])
                    else:
                        st.markdown(msg["content"])

            # Chat input
            prompt = st.chat_input(
                t("ai.placeholder", "Ask about a zone, crop, or recommendation...")
            )
            if prompt:
                if len(prompt) > 500:
                    st.warning("Please keep each question to 500 characters or fewer.")
                else:
                    history = [
                        {"role": msg["role"], "content": str(msg["content"])[:500]}
                        for msg in messages[-8:]
                        if msg.get("role") in {"user", "assistant"}
                    ]
                    messages.append({"role": "user", "content": prompt})
                    with st.chat_message("user"):
                        st.markdown(prompt)

                    with st.chat_message("assistant"):
                        response = None
                        if selected_zone_id:
                            if api_client.is_api_available():
                                with st.spinner("Thinking..."):
                                    response = api_client.chat(
                                        prompt,
                                        zone_id=selected_zone_id,
                                        history=history,
                                        crop=selected_crop,
                                        season=selected_season,
                                    )
                        if not (isinstance(response, dict) and response.get("answer")):
                            fallback_crop = selected_crop or (
                                selected_zone.get("crop") if selected_zone else None
                            )
                            if fallback_crop:
                                response = api_client.get_offline_nisr_advisor_response(
                                    prompt,
                                    fallback_crop,
                                    district=(
                                        offline_district
                                        or (selected_zone.get("district") if selected_zone else None)
                                    ),
                                    season=selected_season,
                                )

                        if isinstance(response, dict) and response.get("answer"):
                            render_advisor_response(response)
                            messages.append({
                                "role": "assistant",
                                "content": str(response["answer"]),
                                "response": response,
                            })
                        else:
                            st.warning(
                                "No NISR historical yield records are available for this crop "
                                "selection. Choose a crop with bundled NISR data or reconnect "
                                "to the API for live AI advice."
                            )

            # Clear chat button
            if messages:
                if st.button(t("ai.clear_chat", "Clear conversation"), icon=":material/delete:"):
                    st.session_state.ai_messages_by_zone[conversation_key] = []
                    st.rerun()

        # ═════════════════════════════════════════════════════════════
        # TAB 2: Disease Detection
        # ═════════════════════════════════════════════════════════════
        with disease_tab:
            render_icon_subheader("assets/brain.svg", t("ai.disease_title", "Crop Disease Detection"))
            st.markdown(t("ai.disease_desc", "Describe symptoms and optionally upload a photo to identify potential crop diseases."))

            disease_zone_options = {
                f"{z.get('district', 'Unknown district')} / {z.get('sector') or z.get('cell') or z.get('id')}": z
                for z in zones
            }
            if not disease_zone_options:
                st.info(
                    "Disease detection requires the live API and a saved zone. "
                    "NISR yield history cannot diagnose crop diseases."
                )
                return

            with st.form("disease_detection_form"):
                form_cols = st.columns(2)

                selected_disease_zone_label = st.selectbox("Zone", list(disease_zone_options), key="disease_zone")
                disease_zone_id = disease_zone_options[selected_disease_zone_label].get("id")

                with form_cols[0]:
                    crops = api_client.get_crops() or CROPS
                    crop = st.selectbox("Crop", crops, key="disease_crop")
                    symptoms = st.text_area(
                        t("ai.describe_symptoms", "Describe symptoms"),
                        placeholder="e.g. Yellowing leaves with brown spots, wilting stems...",
                        height=150,
                        key="disease_symptoms",
                    )

                with form_cols[1]:
                    st.markdown(f"**{t('ai.upload_photo', 'Upload a photo (optional)')}**")
                    image_file = st.file_uploader(
                        "Upload crop image",
                        type=["jpg", "jpeg", "png", "webp"],
                        key="disease_image",
                        label_visibility="collapsed",
                    )
                    if image_file:
                        st.image(image_file, caption="Uploaded image", width="stretch")

                submitted = st.form_submit_button(
                    t("ai.detect_btn", "Detect Disease"),
                    type="primary",
                    width="stretch",
                    key="detect_disease_submit",
                )

            if submitted and (symptoms.strip() or image_file):
                with st.spinner("Analyzing symptoms..."):
                    if image_file:
                        result = api_client.disease_detect_upload(crop, symptoms, disease_zone_id, image_file)
                    else:
                        result = api_client.disease_detect(crop, symptoms, disease_zone_id)

                if result:
                    st.divider()
                    render_icon_subheader("assets/brain.svg", t("ai.detection_result", "Detection Result"))
                    st.warning(
                        "Preliminary triage only—not a confirmed diagnosis. Verify the signs with an RAB or district agronomist before treatment."
                    )
                    st.caption(f"Analysis source: {result.get('source', 'unavailable')}")

                    result_cols = st.columns(2, gap="medium")
                    with result_cols[0]:
                        with st.container(border=True):
                            st.markdown("**Possible issue (preliminary)**")
                            st.markdown(f"### {result.get('predicted_disease', 'Unknown')}")
                            st.caption(f"Crop identification: {result.get('plant_identification', 'Not confirmed')}")

                    with result_cols[1]:
                        with st.container(border=True):
                            st.markdown("**Urgency and risk**")
                            risk = result.get("risk_level", "Unknown")
                            if risk in ("High", "Medium", "Low"):
                                priority_badge(risk)
                            else:
                                st.caption(f"Risk level: {risk or 'Unknown'}")
                            st.caption(f"Urgency: {str(result.get('urgency') or 'unclear').replace('_', ' ').title()}")

                    observations = result.get("observations", [])
                    if observations:
                        st.markdown("**Reported or observed signs**")
                        for item in observations:
                            st.markdown(f"- {item}")

                    causes = result.get("possible_causes", [])
                    if causes:
                        st.markdown("**Other possible causes to check**")
                        for item in causes:
                            st.markdown(f"- {item}")
                    if result.get("interpretation_note"):
                        st.caption(str(result["interpretation_note"]))

                    # Recommended actions
                    actions = result.get("recommended_actions", result.get("actions", []))
                    if actions:
                        st.markdown(f"**{t('ai.rec_actions', 'Recommended Actions:')}**")
                        for i, action in enumerate(actions, 1):
                            st.markdown(f"{i}. {action}")

                    # Option to create a disease plan
                    if st.button(t("ai.create_disease_plan", "Create Disease Action Plan"), type="primary", icon=":material/edit_calendar:"):
                        plan_result = api_client.create_disease_plan({
                            "zone_id": disease_zone_id,
                            "crop": crop,
                            "symptoms": symptoms,
                        })
                        if plan_result:
                            st.success("Disease action plan created successfully.")
                        else:
                            st.warning("Could not create plan. Backend may be unavailable.")

                elif submitted:
                    st.warning("Could not detect disease. Please check backend connectivity.")

            elif submitted and not symptoms.strip() and not image_file:
                st.error("Describe the symptoms or upload a crop photo before submitting.")

    except requests.exceptions.RequestException as e:
        logger.error("Network error in AI assistant: %s", e)
        render_error_page("network", str(e))
    except Exception as e:
        logger.error("Unexpected error in AI assistant: %s", e, exc_info=True)
        render_error_page("system", str(e))
