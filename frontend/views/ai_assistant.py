"""
AI Assistant view — conversational AI + crop disease detection.

Implements Page 4 of the frontend handoff: chat + disease detection.
"""
import logging

import requests
import streamlit as st
from components.badges import priority_badge
from components.errors import render_error_page
from components.icons import render_icon_subheader, render_icon_title
from utils import api_client
from utils.i18n import t
from utils.mock_data import CROPS

logger = logging.getLogger(__name__)


def _init_chat_state() -> None:
    """Initialize session state for chat history."""
    if "ai_messages" not in st.session_state:
        st.session_state.ai_messages = []


def render_ai_assistant() -> None:
    try:
        render_icon_title(
            "assets/bot.svg",
            "AI Assistant",
            "Ask questions about zones, get recommendations, and detect crop diseases",
        )

        _init_chat_state()

        # ── Layout: Chat + Disease Detection ─────────────────────────
        chat_tab, disease_tab = st.tabs(["AI Advisor", "Disease Detection"])

        # ═════════════════════════════════════════════════════════════
        # TAB 1: AI Chat
        # ═════════════════════════════════════════════════════════════
        with chat_tab:
            # Optional zone context selector
            zones = api_client.get_zones()
            zone_names = ["(No specific zone)"] + [z.get("name", f"Zone {z.get('id')}") for z in zones]
            selected_zone_name = st.selectbox("Zone context (optional)", zone_names, key="ai_zone_ctx")

            selected_zone_id = None
            if selected_zone_name != "(No specific zone)":
                selected_zone = next((z for z in zones if z.get("name") == selected_zone_name), None)
                if selected_zone:
                    selected_zone_id = selected_zone.get("id")

            # Display conversation history
            for msg in st.session_state.ai_messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            # Chat input
            prompt = st.chat_input("Ask about a zone, crop, or recommendation...")
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
                        answer = response.get("response", response.get("message", "I could not generate a response."))
                        st.markdown(answer)

                        # Show source context if available
                        sources = response.get("sources", [])
                        if sources:
                            with st.expander("Source context"):
                                for src in sources:
                                    st.caption(f"- {src}")
                    else:
                        answer = (
                            f"Based on my agricultural knowledge, here is guidance for your query: '{prompt}'. "
                            "For the most accurate data-driven response, ensure the backend is running."
                        )
                        st.markdown(answer)

                    st.session_state.ai_messages.append({"role": "assistant", "content": answer})

            # Clear chat button
            if st.session_state.ai_messages:
                if st.button("Clear conversation", icon=":material/delete:"):
                    st.session_state.ai_messages = []
                    st.rerun()

        # ═════════════════════════════════════════════════════════════
        # TAB 2: Disease Detection
        # ═════════════════════════════════════════════════════════════
        with disease_tab:
            render_icon_subheader("assets/brain.svg", "Crop Disease Detection")
            st.markdown("Describe symptoms and optionally upload a photo to identify potential crop diseases.")

            with st.form("disease_detection_form"):
                form_cols = st.columns(2)

                with form_cols[0]:
                    crop = st.selectbox("Crop", CROPS, key="disease_crop")
                    symptoms = st.text_area(
                        "Describe symptoms",
                        placeholder="e.g. Yellowing leaves with brown spots, wilting stems...",
                        height=150,
                        key="disease_symptoms",
                    )

                with form_cols[1]:
                    st.markdown("**Upload a photo (optional)**")
                    image_file = st.file_uploader(
                        "Upload crop image",
                        type=["jpg", "jpeg", "png"],
                        key="disease_image",
                        label_visibility="collapsed",
                    )
                    if image_file:
                        st.image(image_file, caption="Uploaded image", use_container_width=True)

                submitted = st.form_submit_button("Detect Disease", type="primary", use_container_width=True)

            if submitted and symptoms:
                with st.spinner("Analyzing symptoms..."):
                    if image_file:
                        result = api_client.disease_detect_upload(crop, symptoms, image_file)
                    else:
                        result = api_client.disease_detect(crop, symptoms)

                if result:
                    st.divider()
                    render_icon_subheader("assets/brain.svg", "Detection Result")

                    result_cols = st.columns(3)
                    with result_cols[0]:
                        with st.container(border=True):
                            st.markdown("**Probable Disease**")
                            st.markdown(f"### {result.get('disease', 'Unknown')}")

                    with result_cols[1]:
                        with st.container(border=True):
                            st.markdown("**Confidence**")
                            confidence = result.get("confidence", 0)
                            st.markdown(f"### {confidence:.0%}" if isinstance(confidence, float) else f"### {confidence}")

                    with result_cols[2]:
                        with st.container(border=True):
                            st.markdown("**Risk Level**")
                            risk = result.get("risk_level", "Unknown")
                            priority_badge(risk if risk in ("High", "Medium", "Low") else "Medium")

                    # Recommended actions
                    actions = result.get("recommended_actions", result.get("actions", []))
                    if actions:
                        st.markdown("**Recommended Actions:**")
                        for i, action in enumerate(actions, 1):
                            st.markdown(f"{i}. {action}")

                    # Option to create a disease plan
                    if st.button("Create Disease Action Plan", type="primary", icon=":material/edit_calendar:"):
                        plan_result = api_client.create_disease_plan({
                            "crop": crop,
                            "disease": result.get("disease", "Unknown"),
                            "symptoms": symptoms,
                            "actions": actions,
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
