"""
AI Assistant view — conversational AI + crop disease detection.

Implements Page 4 of the frontend handoff: chat + disease detection.
"""
import logging
from contextlib import nullcontext

import requests
import streamlit as st
from components.errors import render_error_page
from components.icons import render_icon_subheader, render_icon_title
from utils import api_client
from utils.assistant_formatting import format_assistant_answer, has_source_citation
from utils.i18n import get_current_language, t

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
            "Ask about local evidence or get a clear explanation of crop symptoms",
        )

        _init_chat_state()

        # ── Layout: Chat + Disease Detection ─────────────────────────
        selected_tool = st.radio(
            "Assistant tool", ["Ask & understand", "Disease Detection"],
            horizontal=True, label_visibility="collapsed", key="assistant_tool",
        )
        # Streamlit tabs render every panel on every rerun. Only mount the
        # selected workflow so inactive forms do not trigger API/data work.
        chat_tab = st.container() if selected_tool == "Ask & understand" else nullcontext()
        disease_tab = st.container() if selected_tool == "Disease Detection" else nullcontext()

        # ═════════════════════════════════════════════════════════════
        # TAB 1: AI Chat
        # ═════════════════════════════════════════════════════════════
        with chat_tab:
            handoff = st.session_state.pop("decision_ai_handoff", None)
            if handoff:
                signature = "|".join(str(handoff.get(key) or "") for key in ("zone_id", "crop", "season"))
                if st.session_state.get("assistant_decision_signature") != signature:
                    st.session_state.ai_messages = []
                    st.session_state["assistant_decision_signature"] = signature
                st.session_state["active_decision_ai_context"] = handoff

            # Optional zone context selector
            zones = api_client.get_zones()
            zone_labels = [
                f"{z.get('district', 'Unknown district')} / {z.get('sector') or z.get('cell') or z.get('id')} · {str(z.get('id') or '')[-8:]}"
                for z in zones
            ]
            zone_by_label = dict(zip(zone_labels, zones))
            active_decision = st.session_state.get("active_decision_ai_context")
            if not active_decision:
                st.caption("Answers use the selected zone as local context. Use Decisions for district crop comparisons.")
            if active_decision:
                target_id = str(active_decision.get("zone_id") or "")
                target_label = next((label for label, zone in zone_by_label.items()
                                     if str(zone.get("id")) == target_id), None)
                if target_label:
                    # Set the widget value before creating the selectbox.
                    st.session_state["ai_zone_ctx"] = target_label
            selected_zone_label = (
                st.selectbox("Zone context", zone_labels, key="ai_zone_ctx")
                if zone_labels else None
            )
            selected_zone = zone_by_label.get(selected_zone_label) if selected_zone_label else None
            selected_zone_id = selected_zone.get("id") if selected_zone else None

            if active_decision and str(selected_zone_id) != str(active_decision.get("zone_id")):
                st.session_state.pop("active_decision_ai_context", None)
                st.session_state.pop("assistant_decision_signature", None)
                active_decision = None
            if active_decision:
                st.info(
                    f"Decision context · {active_decision.get('district')} · {active_decision.get('crop')} · "
                    f"{active_decision.get('season') or 'all available seasons'}"
                )

            # Display conversation history
            for msg in st.session_state.ai_messages:
                with st.chat_message(msg["role"]):
                    st.markdown(format_assistant_answer(msg["content"]))
                    if msg.get("evidence_sources"):
                        st.caption("Evidence: " + " · ".join(msg["evidence_sources"]))
                    elif msg.get("answer_type") == "general_guidance":
                        st.caption("General agricultural guidance · not a local measurement")
                    elif msg.get("answer_type") == "insufficient_evidence" and not has_source_citation(msg.get("content", "")):
                        st.caption("No verified local source was available for this answer")

            # Chat input
            suggested_prompt = st.session_state.pop("assistant_suggested_question", None)
            chat_prompt = st.chat_input("Ask what the records show about a zone or crop...", max_chars=500) if selected_zone_id else None
            prompt = chat_prompt or suggested_prompt
            if not selected_zone_id:
                st.info("Add a zone to use the AI advisor.")
            if prompt:
                # Add user message
                st.session_state.ai_messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                # Get AI response
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        history = [
                            {"role": msg["role"], "content": msg["content"][:500]}
                            for msg in st.session_state.ai_messages[:-1][-8:]
                            if msg.get("role") in {"user", "assistant"}
                        ]
                        response = api_client.chat(
                            prompt, zone_id=selected_zone_id, history=history,
                            crop=active_decision.get("crop") if active_decision else None,
                            season=active_decision.get("season") if active_decision else None,
                        )

                    if response:
                        answer = response.get("answer", "I could not generate a response.")
                        if response.get("source") == "grounded-context":
                            st.warning(
                                "The chat is connected to the backend, but the AI provider did not return a generated answer. "
                                "Showing the zone data available to the assistant. Check the backend LLM key, model access, and provider credits."
                            )
                        st.markdown(format_assistant_answer(answer))
                        evidence_sources = response.get("evidence_sources") or []
                        answer_type = response.get("answer_type", "insufficient_evidence")
                        if evidence_sources and not all(
                            source.casefold() in answer.casefold() for source in evidence_sources
                        ):
                            st.caption("Evidence: " + " · ".join(evidence_sources))
                        elif answer_type == "general_guidance":
                            st.caption("General agricultural guidance · not a local measurement")
                        elif answer_type == "insufficient_evidence" and not has_source_citation(answer):
                            st.caption("No verified local source was available for this answer.")
                        if response.get("evidence_scope") and not active_decision:
                            st.caption(f"Context: {response['evidence_scope']}")
                    else:
                        answer = "The API could not answer this request. Check the backend connection and try again."
                        st.error(answer)

                    st.session_state.ai_messages.append({
                        "role": "assistant", "content": answer,
                        "evidence_sources": (response or {}).get("evidence_sources", []),
                        "answer_type": (response or {}).get("answer_type", "insufficient_evidence"),
                    })

            # Clear chat button
            if st.session_state.ai_messages:
                if st.button("Clear conversation", icon=":material/delete:"):
                    st.session_state.ai_messages = []
                    st.rerun()

        # ═════════════════════════════════════════════════════════════
        # TAB 2: Crop health triage
        # ═════════════════════════════════════════════════════════════
        with disease_tab:
            render_icon_subheader("assets/brain.svg", "Crop health check")
            st.caption("Preliminary photo triage; confirm findings with an agronomist before treatment.")

            zones = api_client.get_zones()
            disease_zone_options = {}
            for zone in zones:
                zone_id = str(zone.get("id") or "")
                if not zone_id:
                    continue
                label = " / ".join(str(value) for value in (
                    zone.get("district") or "Unknown district",
                    zone.get("sector") or zone.get("cell"),
                    zone.get("crop_type") or zone.get("crop"),
                ) if value) + f" · {zone_id[-8:]}"
                disease_zone_options[label] = zone
            if not disease_zone_options:
                st.info("Create or load a zone before running disease detection.")
                return
            crops = api_client.get_crops()

            with st.form("disease_detection_form"):
                top_cols = st.columns(2)

                with top_cols[0]:
                    selected_disease_zone_label = st.selectbox("Zone", list(disease_zone_options), key="disease_zone")
                    disease_zone_id = disease_zone_options[selected_disease_zone_label].get("id")
                with top_cols[1]:
                    zone_crop = str(disease_zone_options[selected_disease_zone_label].get("crop_type") or disease_zone_options[selected_disease_zone_label].get("crop") or "")
                    default_crop_idx = 0
                    if zone_crop:
                        for idx, c in enumerate(crops):
                            if c.casefold() == zone_crop.casefold():
                                default_crop_idx = idx
                                break
                    crop = st.selectbox("Crop", crops, index=default_crop_idx, key="disease_crop") if crops else st.text_input("Crop", value=zone_crop, key="disease_crop_text")
                form_cols = st.columns(2)

                with form_cols[0]:

                    symptoms = st.text_area(
                        "What did you observe? (optional if you upload a photo)",
                        placeholder="For example: lower leaves yellowing over the past week...",
                        height=150,
                        key="disease_symptoms",
                    )

                with form_cols[1]:
                    st.markdown("**Crop photo (optional)**")
                    image_file = st.file_uploader(
                        "Upload crop image",
                        type=["jpg", "jpeg", "png", "webp"],
                        key="disease_image",
                        label_visibility="collapsed",
                    )
                    if image_file:
                        st.image(image_file, caption="Uploaded image", width="stretch")

                submitted = st.form_submit_button("Review crop symptoms", type="primary", width="stretch")

            if submitted and (symptoms.strip() or image_file):
                language = get_current_language()
                with st.spinner("Reviewing the photo and reported symptoms..."):
                    if image_file:
                        result = api_client.disease_detect_upload(crop, symptoms, disease_zone_id, image_file, language=language)
                    else:
                        result = api_client.disease_detect(crop, symptoms, disease_zone_id, language=language)

                if result:
                    st.divider()
                    render_icon_subheader("assets/brain.svg", "What the photo suggests")
                    finding = result.get("predicted_disease") or "Unconfirmed"
                    st.markdown(f"### {finding}")
                    identification = result.get("plant_identification")
                    if identification and identification != "Not confirmed":
                        st.caption(f"Plant visible in photo: {identification}")
                    source = result.get("source") or "unavailable"
                    st.caption("Groq vision model" if source == "groq_vision_triage" else "Groq text model" if source == "groq_symptom_triage" else "Local experimental model" if source.startswith("local_") else "AI analysis unavailable")
                    if result.get("interpretation_note"):
                        st.info(result["interpretation_note"])
                    observation_cols = st.columns([1, 1])
                    with observation_cols[0]:
                        st.markdown("**Visible / reported signs**")
                        observations = result.get("observations") or []
                        if observations:
                            for observation in observations:
                                st.markdown(f"- {observation}")
                        else:
                            st.caption("No specific signs could be confirmed from the submitted information.")
                    with observation_cols[1]:
                        st.markdown("**Possible explanations**")
                        causes = result.get("possible_causes") or []
                        if causes:
                            for cause in causes:
                                st.markdown(f"- {cause}")
                        else:
                            st.caption("More field information is needed.")
                    st.markdown("**Safe next steps**")
                    for action in result.get("recommended_actions") or []:
                        st.markdown(f"- {action}")
                    if st.button("Plan an in-person follow-up", type="primary", icon=":material/edit_calendar:"):
                        zone = disease_zone_options[selected_disease_zone_label]
                        st.session_state["planning_zone_id"] = str(disease_zone_id)
                        st.session_state["plan_decision_context"] = {
                            "zone_id": str(disease_zone_id),
                            "district": zone.get("district"),
                            "crop": crop,
                            "season": zone.get("season"),
                            "priority": None,
                            "assessment": f"Farmer-reported symptoms: {symptoms.strip() or 'Photo submitted for review.'} Preliminary triage: {finding}.",
                            "basis": source,
                        }
                        st.session_state["plan_scenario"] = "field_observation_followup"
                        st.switch_page("pages/8_Planning.py")

                elif submitted:
                    st.warning("AI triage did not complete. The system will not guess a disease when the provider is unavailable.")

            elif submitted:
                st.error("Describe at least one symptom or attach a crop photo.")

    except requests.exceptions.RequestException as e:
        logger.error("Network error in AI assistant: %s", e)
        render_error_page("network", str(e))
    except Exception as e:
        logger.error("Unexpected error in AI assistant: %s", e, exc_info=True)
        render_error_page("system", str(e))
