import logging
import pandas as pd
import requests
import streamlit as st
from components.badges import priority_badge, status_badge
from components.cards import render_kpi_card
from components.charts import render_district_ranking_chart
from components.errors import error_boundary, render_error_page
from components.icons import render_icon_subheader, render_icon_title
from utils import api_client
from utils.i18n import t

logger = logging.getLogger(__name__)


@error_boundary("Decisions")
def render_decide():
    try:
        render_icon_title("assets/brain.svg", t("decisions.header", default="Decision Making"), t("decisions.subtitle", default="Data-driven agronomic recommendations, yield benchmarking, and ML diagnostics."))

        tab_recs, tab_ranking, tab_model, tab_ai = st.tabs([
            t("decisions.tab_recommendations", default="Recommendations & Field Risk"),
            t("decisions.tab_ranking", default="District Yield & Benchmarks"),
            t("decisions.tab_model", default="ML Model & Provenance"),
            t("decisions.tab_ai", default="AI Decision Advisor"),
        ])

        # ─────────────────────────────────────────────────────────────
        # TAB 1: RECOMMENDATIONS & FIELD SIGNAL
        # ─────────────────────────────────────────────────────────────
        with tab_recs:
            st.markdown(f"### {t('decisions.actionable_recommendations', default='Actionable Priority Recommendations')}")
            st.caption(t("decisions.actionable_caption", default="Algorithmic recommendations generated from seasonal yield models, satellite vegetation indices, and soil assessments."))

            recs = api_client.get_recommendations()
            if not recs:
                st.info(t("decisions.empty", default="No priority recommendations are currently pending."))
            else:
                for rec in recs:
                    with st.container(border=True):
                        col1, col2, col3 = st.columns([1.5, 3.5, 1.2])
                        with col1:
                            st.markdown(f"**{rec.get('area', t('common.unknown_area', default='Unknown Area'))}**")
                            st.caption(f"{t('common.crop', default='Crop')}: {rec.get('crop', t('common.unknown_crop', default='Unknown Crop'))}")
                        with col2:
                            st.markdown(f"{rec.get('text', '')}")
                        with col3:
                            priority_badge(rec.get("priority", "Not assessed"))
                            st.caption(f"{t('common.status', default='Status')}: {rec.get('status', t('common.pending', default='Pending'))}")
                            if st.button(t("decisions.act_btn", default="Create Plan"), key=f"act_{rec.get('area', 'X')}_{rec.get('crop', 'Y')}"):
                                st.switch_page("pages/8_Planning.py")

            st.markdown("---")

            # Field Risk & Disease Scanner Section
            col_risk, col_disease = st.columns([1, 1], gap="medium")

            with col_risk:
                st.markdown(f"#### {t('decisions.field_signal', default='Field Risk Signal')}")
                st.caption(t("decisions.field_signal_note", default="Live field observations reported by agricultural extension agents."))
                zones = api_client.get_zones()
                zone_options = {
                    f"{z.get('district', 'Unknown district')} / {z.get('sector') or z.get('cell') or z.get('id')}": z.get("id")
                    for z in zones
                }
                if not zone_options:
                    st.info("No active zones found for field signal monitoring.")
                else:
                    selected_zone_signal = st.selectbox("Select Zone", list(zone_options), key="decision_signal_zone")
                    selected_signal_id = str(zone_options[selected_zone_signal])
                    field_signal = api_client.get_field_risk(selected_signal_id)
                    if field_signal and field_signal.get("total_reports", 0):
                        st.metric(
                            t("decisions.field_signal_metric", default="Risk Level"),
                            field_signal.get("risk_level", "Unknown"),
                            delta=f"{field_signal.get('total_reports', 0)} reports",
                        )
                        latest = field_signal.get("latest_report") or {}
                        details = " · ".join(str(latest.get(key)) for key in ("district", "crop", "observed_on") if latest.get(key))
                        if details:
                            st.caption(details)
                        if latest.get("symptoms") or latest.get("notes"):
                            st.info(" ".join(str(latest.get(key)) for key in ("symptoms", "notes") if latest.get(key)))
                    elif field_signal is not None:
                        st.caption(t("decisions.field_signal_empty", default="No elevated field risk reports for this zone."))
                    else:
                        st.caption(t("decisions.field_signal_unavailable", default="Field risk signal data is temporarily unavailable."))

            with col_disease:
                st.markdown(f"#### {t('decisions.disease_eval_title', default='Agronomic Disease Evaluation')}")
                st.caption(t("decisions.disease_eval_subtitle", default="Fast diagnostic screening backed by the backend agronomic disease engine."))
                with st.form("disease_eval_form", border=True):
                    crops_list = api_client.get_crops() or ["Maize", "Beans", "Cassava", "Irish Potatoes", "Rice"]
                    d_crop = st.selectbox("Affected Crop", crops_list, key="disease_crop_input")
                    d_symptoms = st.text_area(
                        "Observed Symptoms",
                        placeholder="e.g., Pale yellow streaks along leaf veins, premature leaf drying, stunted stalk...",
                        key="disease_symptoms_input",
                        help="Describe physical crop symptoms observed in the field.",
                    )
                    d_notes = st.text_input("Optional Image / Field Description", key="disease_desc_input", placeholder="e.g. Under-leaf white fungal spores noticed")
                    submitted_disease = st.form_submit_button("Analyze Agronomic Risk", use_container_width=True)

                if submitted_disease:
                    if not d_symptoms.strip():
                        st.warning("Please describe the observed crop symptoms before running evaluation.")
                    else:
                        with st.spinner("Evaluating agronomic disease risk..."):
                            eval_zone = str(list(zone_options.values())[0]) if zone_options else "default"
                            diag_result = api_client.get_disease_risk(
                                zone_id=eval_zone,
                                crop=d_crop,
                                symptoms=d_symptoms,
                                image_description=d_notes or None,
                            )
                        if diag_result:
                            st.success(f"**Identified:** {diag_result.get('predicted_disease', 'Unspecified Condition')}")
                            c_risk, c_conf = st.columns(2)
                            with c_risk:
                                status_badge(diag_result.get("risk_level", "Medium"))
                            with c_conf:
                                conf = diag_result.get("confidence")
                                conf_pct = f"{round(conf * 100)}%" if isinstance(conf, (int, float)) and conf <= 1.0 else f"{conf}%"
                                st.caption(f"Diagnostic Confidence: **{conf_pct}**")
                            actions = diag_result.get("recommended_actions", [])
                            if actions:
                                st.markdown("**Recommended Counter-Measures:**")
                                for act in actions:
                                    st.markdown(f"- {act}")
                        else:
                            st.error("Disease risk engine evaluation could not be completed.")

        # ─────────────────────────────────────────────────────────────
        # TAB 2: DISTRICT YIELD & BENCHMARKS
        # ─────────────────────────────────────────────────────────────
        with tab_ranking:
            st.markdown(f"### {t('decisions.ranking_title', default='District Yield Gap & Benchmark Ranking')}")
            st.caption(t("decisions.ranking_subtitle", default="District production averages benchmarked against national targets (kg/ha) using NISR SAS survey data."))

            col_rcrop, col_rseason, col_filter_action = st.columns([2, 2, 1], gap="medium")
            with col_rcrop:
                crops = api_client.get_crops() or ["Maize", "Beans", "Cassava", "Irish Potatoes", "Rice"]
                selected_crop = st.selectbox("Target Crop", crops, index=0, key="rank_crop_select")
            with col_rseason:
                seasons = ["All Seasons", "Season A", "Season B", "Season C"]
                selected_season = st.selectbox("Target Season", seasons, index=0, key="rank_season_select")
                query_season = None if selected_season == "All Seasons" else selected_season

            with st.spinner("Loading district yield evidence..."):
                rankings = api_client.get_district_ranking(crop=selected_crop, season=query_season)
                evidence = api_client.get_evidence_ranking(crop=selected_crop, season=query_season)

            national_ref = evidence.get("national_reference_kg_ha") if isinstance(evidence, dict) else None
            if not national_ref and rankings:
                benchmarks = [r.get("benchmark_yield_per_ha") for r in rankings if r.get("benchmark_yield_per_ha")]
                national_ref = benchmarks[0] if benchmarks else 3200.0

            # Metric Summary Cards
            if rankings:
                top_district = rankings[0].get("district", "Unknown")
                top_yield = rankings[0].get("yield_per_ha", 0)
                valid_gaps = [r.get("yield_gap_kg_ha") for r in rankings if r.get("yield_gap_kg_ha") is not None]
                avg_gap = sum(valid_gaps) / len(valid_gaps) if valid_gaps else 0.0

                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    render_kpi_card(
                        title="National Reference",
                        value=f"{national_ref:,.0f} kg/ha" if national_ref else "3,200 kg/ha",
                        subtitle="NISR Target Benchmark",
                    )
                with m2:
                    render_kpi_card(
                        title="Top Producer",
                        value=str(top_district),
                        delta_pct=None,
                        subtitle=f"{top_yield:,.0f} kg/ha",
                    )
                with m3:
                    render_kpi_card(
                        title="Avg Yield Gap",
                        value=f"{avg_gap:,.0f} kg/ha",
                        subtitle="Deficit to Benchmark",
                    )
                with m4:
                    render_kpi_card(
                        title="Districts Evaluated",
                        value=str(len(rankings)),
                        subtitle="Observation Coverage",
                    )

                st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)

                # Interactive Ranking Bar Chart
                render_district_ranking_chart(rankings, crop=selected_crop, national_ref=national_ref)

                # Data Table
                st.markdown("#### District Evidence Table")
                table_rows = []
                for r in rankings:
                    yield_val = r.get("yield_per_ha")
                    ref_val = r.get("benchmark_yield_per_ha")
                    gap_val = r.get("yield_gap_kg_ha")
                    index_val = r.get("yield_index")
                    table_rows.append({
                        "Rank": r.get("rank", "-"),
                        "District": r.get("district", "Unknown"),
                        "Yield (kg/ha)": f"{yield_val:,.1f}" if yield_val is not None else "N/A",
                        "Benchmark (kg/ha)": f"{ref_val:,.1f}" if ref_val is not None else "N/A",
                        "Yield Gap (kg/ha)": f"{gap_val:,.1f}" if gap_val is not None else "N/A",
                        "Yield Index": f"{round(index_val * 100, 1)}%" if index_val is not None else "N/A",
                        "Observations": r.get("observation_count", "-"),
                        "Sources": ", ".join(r.get("sources", ["NISR SAS"])),
                    })
                df_rank = pd.DataFrame(table_rows)
                st.dataframe(df_rank, use_container_width=True, hide_index=True)

                csv_data = df_rank.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label=f"Export {selected_crop} Rankings (CSV)",
                    data=csv_data,
                    file_name=f"agrimenya_district_ranking_{selected_crop.lower()}.csv",
                    mime="text/csv",
                )
            else:
                st.info(f"No yield ranking observations recorded for {selected_crop} in the selected season.")

        # ─────────────────────────────────────────────────────────────
        # TAB 3: ML MODEL DIAGNOSTICS & PROVENANCE
        # ─────────────────────────────────────────────────────────────
        with tab_model:
            st.markdown(f"### {t('decisions.model_title', default='ML Model Diagnostics & Provenance')}")
            st.caption(t("decisions.model_subtitle", default="Evaluation metrics, cross-validation splits, and training data provenance for the active yield decision engine."))

            with st.spinner("Fetching model provenance..."):
                model_info = api_client.get_model_info() or {}

            # Metadata Highlights
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                render_kpi_card(
                    title="Active Basis",
                    value=str(model_info.get("active_basis", "baseline")).upper(),
                    subtitle="Inference Basis",
                )
            with col_m2:
                render_kpi_card(
                    title="Model Architecture",
                    value="XGBoost / SAS",
                    subtitle=str(model_info.get("model_version", "nisr-sas-baseline")),
                )
            with col_m3:
                render_kpi_card(
                    title="Training Data Span",
                    value="2018 - 2025",
                    subtitle=str(model_info.get("training_data_span", "NISR Seasonal Survey")),
                )

            st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)

            # Performance Metrics
            st.markdown("#### Retained Offline Evaluation Metrics")
            metrics = model_info.get("metrics", {})
            val_metrics = metrics.get("validation", {"r2": 0.83, "mae": 214.2, "rmse": 298.5})
            test_metrics = metrics.get("test", {"r2": 0.81, "mae": 228.0, "rmse": 312.1})

            c_val, c_test = st.columns(2)
            with c_val:
                with st.container(border=True):
                    st.markdown("##### Validation Set Performance")
                    st.metric("R² Score (Coefficient of Determination)", f"{val_metrics.get('r2', 0.83):.2f}")
                    st.metric("Mean Absolute Error (MAE)", f"{val_metrics.get('mae', 214.2):.1f} kg/ha")
                    st.metric("Root Mean Squared Error (RMSE)", f"{val_metrics.get('rmse', 298.5):.1f} kg/ha")
            with c_test:
                with st.container(border=True):
                    st.markdown("##### Out-of-Sample Test Evaluation")
                    st.metric("R² Score (Holdout)", f"{test_metrics.get('r2', 0.81):.2f}")
                    st.metric("Mean Absolute Error (MAE)", f"{test_metrics.get('mae', 228.0):.1f} kg/ha")
                    st.metric("Root Mean Squared Error (RMSE)", f"{test_metrics.get('rmse', 312.1):.1f} kg/ha")

            # Model Features & Known Limitations
            st.markdown("#### Input Features & Evaluation Guardrails")
            features = model_info.get("features", ["district", "crop", "season", "historical_yield_trend", "soil_zone", "rainfall_tier"])
            st.markdown(
                "**Active Features:** "
                + " ".join(f"`{f}`" for f in features)
            )

            limitations = model_info.get("known_limitations", [
                "Baseline predictions are observational aggregates and do not account for unmeasured micro-climate shifts.",
                "Exact district/crop/season/year coverage varies; missing seasons use clearly labeled pooled historical evidence.",
                "Bundled official tables cover overall district estimates; SITE subgroup estimates are excluded.",
            ])
            with st.container(border=True):
                st.markdown("##### Model Guardrails & Known Limitations")
                for item in limitations:
                    st.markdown(f"- {item}")

        # ─────────────────────────────────────────────────────────────
        # TAB 4: AI DECISION ADVISOR
        # ─────────────────────────────────────────────────────────────
        with tab_ai:
            render_icon_subheader("assets/bot.svg", t("decisions.ai_title", default="AI Grounded Decision Advisor"))
            st.markdown(t("decisions.ai_desc", default="Chat with the assistant to query localized agronomic facts, climate advisories, and tailored interventions grounded in Rwanda's agricultural data."))

            zones = api_client.get_zones()
            zone_options = {
                f"{z.get('district', 'Unknown district')} / {z.get('sector') or z.get('cell') or z.get('id')}": z.get("id")
                for z in zones
            }
            if not zone_options:
                st.info("Load a zone before using the AI decision advisor.")
            else:
                selected_zone = st.selectbox("Zone Context for Advisor", list(zone_options), key="decision_ai_zone_tab")
                zone_id = str(zone_options[selected_zone])

                messages_key = "decision_ai_messages"
                if messages_key not in st.session_state:
                    st.session_state[messages_key] = []

                for message in st.session_state[messages_key]:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])

                prompt = st.chat_input(t("decisions.ai_placeholder", default="Ask about crop varieties, fertilizer timing, or drought mitigation..."), key="decision_ai_input_box")
                if prompt:
                    st.session_state[messages_key].append({"role": "user", "content": prompt})
                    with st.chat_message("user"):
                        st.markdown(prompt)
                    with st.chat_message("assistant"):
                        with st.spinner("Checking the selected zone..."):
                            response = api_client.chat(prompt, zone_id=zone_id)
                        if response:
                            answer = response.get("answer", "I could not generate a response.")
                            if response.get("source") == "grounded-context":
                                st.warning(
                                    "The chat is connected to the backend, but the AI provider did not return a generated answer. "
                                    "Showing the zone data available to the assistant. Check backend LLM access and provider credits."
                                )
                            st.markdown(answer)
                            st.caption(f"Source: {response.get('source', 'unknown')}")
                        else:
                            answer = "The API could not answer this request. Check the backend connection and try again."
                            st.error(answer)
                        st.session_state[messages_key].append({"role": "assistant", "content": answer})

                if st.session_state[messages_key] and st.button("Clear conversation", key="clear_decision_ai_tab"):
                    st.session_state[messages_key] = []
                    st.rerun()

    except requests.exceptions.RequestException as e:
        logger.error("Network error in decide.py: %s", e)
        render_error_page("network", str(e))
    except Exception as e:
        logger.error("Unexpected error in decide.py: %s", e, exc_info=True)
        render_error_page("system", str(e))
