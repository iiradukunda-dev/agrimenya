"""
AI Assistant view: conversational AI + crop disease detection.

Implements Page 4 of the frontend handoff: chat + disease detection.
"""
import logging

import requests
import streamlit as st
from components.badges import priority_badge
from components.errors import error_boundary, render_error_page
from components.icons import render_icon_subheader, render_icon_title
from utils import api_client
from utils.i18n import t
from utils.mock_data import CROPS

logger = logging.getLogger(__name__)


def _init_chat_state() -> None:
    """Initialize session state for chat history."""
    if "ai_messages" not in st.session_state:
        st.session_state.ai_messages = []


@error_boundary("AI Assistant")
def render_ai_assistant() -> None:
    try:
        render_icon_title(
            "assets/bot.svg",
            t("ai.title", "AI Assistant"),
            t("ai.subtitle", "Ask questions about zones, get recommendations, and detect crop diseases"),
        )

        _init_chat_state()

        # ── Layout: Chat + Disease Detection ─────────────────────────
        chat_tab, disease_tab = st.tabs([t("ai.tab.advisor", "AI Advisor"), t("ai.tab.disease", "Disease Detection")])

        # ═════════════════════════════════════════════════════════════
        # TAB 1: AI Chat
        # ═════════════════════════════════════════════════════════════
        with chat_tab:
            # Optional zone context selector
            zones = api_client.get_zones()
            zone_labels = [
                f"{z.get('district', 'Unknown district')} / {z.get('sector') or z.get('cell') or z.get('id')}"
                for z in zones
            ]
            zone_by_label = dict(zip(zone_labels, zones))
            selected_zone_label = st.selectbox(t("ai.zone_ctx", "Zone context"), zone_labels, key="ai_zone_ctx") if zone_labels else None
            selected_zone = zone_by_label.get(selected_zone_label) if selected_zone_label else None
            selected_zone_id = selected_zone.get("id") if selected_zone else None

            # Display conversation history
            for msg in st.session_state.ai_messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            # Chat input
            prompt = st.chat_input(t("ai.placeholder", "Ask about a zone, crop, or recommendation...")) if selected_zone_id else None
            if not selected_zone_id:
                st.info("Select or create an agricultural zone to start asking questions with grounded soil and yield data.")
            if prompt:
                # Add user message
                st.session_state.ai_messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                # Get AI response
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        response = api_client.chat(prompt, zone_id=selected_zone_id)

                    if response:
                        answer = response.get("answer", "I could not generate a response.")
                        if response.get("source") == "grounded-context":
                            st.warning(
                                "The chat is connected to the backend, but the AI provider did not return a generated answer. "
                                "Showing the zone data available to the assistant. Check the backend LLM key, model access, and provider credits."
                            )
                        st.markdown(answer)
                        st.caption(f"Source: {response.get('source', 'unknown')}")
                    else:
                        answer = "The API could not answer this request. Check the backend connection and try again."
                        st.error(answer)

                    st.session_state.ai_messages.append({"role": "assistant", "content": answer})

            # Clear chat button
            if st.session_state.ai_messages:
                if st.button(t("ai.clear_chat", "Clear conversation"), icon=":material/delete:"):
                    st.session_state.ai_messages = []
                    st.rerun()

        # ═════════════════════════════════════════════════════════════
        # TAB 2: Disease Detection
        # ═════════════════════════════════════════════════════════════
        with disease_tab:
            render_icon_subheader("assets/brain.svg", t("ai.disease_title", "Crop Disease Detection"))
            st.markdown(t("ai.disease_desc", "Describe symptoms and optionally upload a photo to identify potential crop diseases."))

            zones = api_client.get_zones()
            disease_zone_options = {
                f"{z.get('district', 'Unknown district')} / {z.get('sector') or z.get('cell') or z.get('id')}": z
                for z in zones
            }
            if not disease_zone_options:
                st.info("Create or load a zone before running disease detection.")
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
                        type=["jpg", "jpeg", "png"],
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

            if submitted and symptoms:
                with st.spinner("Analyzing symptoms..."):
                    if image_file:
                        result = api_client.disease_detect_upload(crop, symptoms, disease_zone_id, image_file)
                    else:
                        result = api_client.disease_detect(crop, symptoms, disease_zone_id)

                if result:
                    st.divider()
                    render_icon_subheader("assets/brain.svg", t("ai.detection_result", "Detection Result"))
                    if image_file and result.get("source") != "vision-cnn":
                        st.warning(
                            "The image model is not trained yet. This result is based on the symptoms you entered, not visual image analysis."
                        )
                    else:
                        st.caption(f"Analysis source: {result.get('source', 'symptom-model')}")

                    result_cols = st.columns(2, gap="medium")
                    with result_cols[0]:
                        with st.container(border=True):
                            st.markdown(f"**{t('ai.probable_disease', 'Probable Disease')}**")
                            st.markdown(f"### {result.get('predicted_disease', 'Unknown')}")
                            confidence = result.get("confidence", 0)
                            conf_str = f"{confidence:.0%}" if isinstance(confidence, float) else f"{confidence}"
                            st.caption(f"Model Confidence: **{conf_str}**")

                    with result_cols[1]:
                        with st.container(border=True):
                            st.markdown(f"**{t('ai.risk_assess', 'Risk Assessment')}**")
                            risk = result.get("risk_level", "Unknown")
                            priority_badge(risk if risk in ("High", "Medium", "Low") else "Not assessed")
                            st.caption(f"Diagnostic Engine: {result.get('source', 'symptom-model')}")

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

            elif submitted and not symptoms:
                st.error("Please describe the symptoms before submitting.")

    except requests.exceptions.RequestException as e:
        logger.error("Network error in AI assistant: %s", e)
        render_error_page("network", str(e))
    except Exception as e:
        logger.error("Unexpected error in AI assistant: %s", e, exc_info=True)
        render_error_page("system", str(e))
