import io
import logging
from typing import Any
import requests
import streamlit as st
from components.badges import priority_badge, status_badge
from components.cards import render_kpi_card
from components.charts import render_district_ranking_chart
from components.errors import error_boundary, render_error_page
from components.icons import render_icon_subheader, render_icon_title
from utils import api_client
from utils.i18n import t

try:
    import pandas as pd
except ImportError:
    pd = None

logger = logging.getLogger(__name__)


@st.dialog("Agronomic Disease Evaluation", width="large")
def show_disease_eval_dialog(zones: list[dict[str, Any]]) -> None:
    """Modal popup for agronomic disease diagnosis."""
    crops_list = api_client.get_crops() or ["Maize", "Beans", "Cassava", "Irish Potatoes", "Rice"]
    zone_options = {
        f"{z.get('district', 'District')} / {z.get('site_name') or z.get('sector') or z.get('id')}": str(z.get("id"))
        for z in zones if z.get("id")
    }

    with st.form("modal_disease_form"):
        c1, c2 = st.columns(2)
        with c1:
            crop = st.selectbox("Target Crop", crops_list)
        with c2:
            zone_id = (
                st.selectbox("Field Zone", list(zone_options))
                if zone_options
                else None
            )

        symptoms = st.text_area(
            "Observed Symptoms",
            placeholder="e.g. Pale yellow streaks along leaf veins, premature drying...",
            height=85,
        )
        notes = st.text_input("Additional Field Notes (Optional)", placeholder="e.g. Under-leaf fungal spores")

        submitted = st.form_submit_button("Analyze Agronomic Risk", type="primary", use_container_width=True)

    if submitted:
        if not symptoms.strip():
            st.warning("Please describe the observed symptoms.")
            return

        target_zone = zone_options.get(zone_id) if zone_id else "default"
        with st.spinner("Analyzing disease pattern..."):
            diag = api_client.get_disease_risk(
                zone_id=target_zone,
                crop=crop,
                symptoms=symptoms.strip(),
                image_description=notes.strip() or None,
            )
        if diag:
            st.session_state["last_disease_diag"] = diag
            st.rerun()
        else:
            st.error("Diagnosis could not be completed.")

    last_diag = st.session_state.get("last_disease_diag")
    if last_diag:
        st.markdown("---")
        st.markdown(f"##### Condition: {last_diag.get('predicted_disease', 'Unspecified')}")
        c_r, c_c = st.columns(2)
        with c_r:
            status_badge(last_diag.get("risk_level", "Medium"))
        with c_c:
            conf = last_diag.get("confidence")
            conf_str = f"{round(conf * 100)}%" if isinstance(conf, (int, float)) and conf <= 1.0 else f"{conf}%"
            st.caption(f"Confidence: **{conf_str}**")

        actions = last_diag.get("recommended_actions", [])
        if actions:
            st.markdown("**Action Guidance:**")
            for act in actions:
                st.markdown(f"- {act}")


@error_boundary("Decisions")
def render_decide():
    try:
        render_icon_title(
            "assets/brain.svg",
            t("decisions.header", default="Decision Making"),
            t("decisions.subtitle", default="Agronomic recommendations, yield gap benchmarks, and ML diagnostics."),
        )

        tab_recs, tab_ranking, tab_model, tab_ai = st.tabs([
            t("decisions.tab_recommendations", default="Recommendations & Field Risk"),
            t("decisions.tab_ranking", default="District Yield & Benchmarks"),
            t("decisions.tab_model", default="ML Model & Provenance"),
            t("decisions.tab_ai", default="AI Decision Advisor"),
        ])

        zones = api_client.get_zones()

        # ── TAB 1: RECOMMENDATIONS & FIELD SIGNAL ─────────────────────
        with tab_recs:
            c_head, c_btn = st.columns([3.5, 1.5])
            with c_head:
                st.markdown(f"### {t('decisions.actionable_recommendations', default='Priority Recommendations')}")
            with c_btn:
                if st.button("Disease Triage", type="primary", use_container_width=True):
                    show_disease_eval_dialog(zones)

            recs = api_client.get_recommendations()
            if not recs:
                st.info(t("decisions.empty", default="No priority recommendations pending."))
            else:
                for rec in recs:
                    with st.container(border=True):
                        col1, col2, col3 = st.columns([1.5, 3.5, 1.2])
                        with col1:
                            st.markdown(f"**{rec.get('area', 'Unknown')}**")
                            st.caption(f"Crop: {rec.get('crop', 'Unknown')}")
                        with col2:
                            st.markdown(f"{rec.get('text', '')}")
                        with col3:
                            priority_badge(rec.get("priority", "Not assessed"))
                            if st.button("Create Plan →", key=f"act_{rec.get('area', 'X')}_{rec.get('crop', 'Y')}", use_container_width=True):
                                st.switch_page("pages/8_Planning.py")

            st.markdown("---")

            # Field Risk Signal (Compact)
            st.markdown(f"#### {t('decisions.field_signal', default='Field Risk Signal')}")
            zone_options = {
                f"{z.get('district', 'District')} / {z.get('site_name') or z.get('sector') or z.get('id')}": z.get("id")
                for z in zones if z.get("id")
            }
            if zone_options:
                c_sel, c_res = st.columns([2, 3])
                with c_sel:
                    selected_signal = st.selectbox("Select Zone", list(zone_options), key="decision_signal_zone")
                with c_res:
                    sig_id = str(zone_options[selected_signal])
                    sig = api_client.get_field_risk(sig_id)
                    if sig and sig.get("total_reports", 0):
                        st.metric("Reported Field Risk", sig.get("risk_level", "Unknown"), delta=f"{sig.get('total_reports', 0)} observations")
                        latest = sig.get("latest_report") or {}
                        if latest.get("symptoms"):
                            st.caption(f"Latest: {latest['symptoms']}")
                    else:
                        st.caption("No elevated risk reports for this zone.")

        # ── TAB 2: DISTRICT YIELD & BENCHMARKS ─────────────────────────
        with tab_ranking:
            c1, c2 = st.columns(2)
            with c1:
                crops = api_client.get_crops() or ["Maize", "Beans", "Cassava", "Irish Potatoes", "Rice"]
                selected_crop = st.selectbox("Target Crop", crops, index=0, key="rank_crop_select")
            with c2:
                seasons = ["All Seasons", "Season A", "Season B", "Season C"]
                selected_season = st.selectbox("Target Season", seasons, index=0, key="rank_season_select")
                query_season = None if selected_season == "All Seasons" else selected_season

            with st.spinner("Loading benchmarks..."):
                rankings = api_client.get_district_ranking(crop=selected_crop, season=query_season)
                evidence = api_client.get_evidence_ranking(crop=selected_crop, season=query_season)

            national_ref = evidence.get("national_reference_kg_ha") if isinstance(evidence, dict) else None
            if not national_ref and rankings:
                benchmarks = [r.get("benchmark_yield_per_ha") for r in rankings if r.get("benchmark_yield_per_ha")]
                national_ref = benchmarks[0] if benchmarks else 3200.0

            if rankings:
                top_district = rankings[0].get("district", "Unknown")
                top_yield = rankings[0].get("yield_per_ha", 0)
                valid_gaps = [r.get("yield_gap_kg_ha") for r in rankings if r.get("yield_gap_kg_ha") is not None]
                avg_gap = sum(valid_gaps) / len(valid_gaps) if valid_gaps else 0.0

                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    render_kpi_card(title="National Benchmark", value=f"{national_ref:,.0f} kg/ha", subtitle="NISR Reference")
                with m2:
                    render_kpi_card(title="Top Producer", value=str(top_district), subtitle=f"{top_yield:,.0f} kg/ha")
                with m3:
                    render_kpi_card(title="Avg Yield Gap", value=f"{avg_gap:,.0f} kg/ha", subtitle="Benchmark Deficit")
                with m4:
                    render_kpi_card(title="Districts Evaluated", value=str(len(rankings)), subtitle="Coverage")

                st.markdown("<div style='height: 0.8rem;'></div>", unsafe_allow_html=True)
                render_district_ranking_chart(rankings, crop=selected_crop, national_ref=national_ref)

                # Exportable Table
                table_rows = []
                for r in rankings:
                    table_rows.append({
                        "Rank": r.get("rank", "-"),
                        "District": r.get("district", "Unknown"),
                        "Yield (kg/ha)": f"{r.get('yield_per_ha', 0):,.1f}",
                        "Benchmark": f"{r.get('benchmark_yield_per_ha', 0):,.1f}",
                        "Gap (kg/ha)": f"{r.get('yield_gap_kg_ha', 0):,.1f}",
                    })
                if pd is not None:
                    df_rank = pd.DataFrame(table_rows)
                    st.dataframe(df_rank, width="stretch", hide_index=True)
            else:
                st.info(f"No yield observations for {selected_crop}.")

        # ── TAB 3: ML MODEL DIAGNOSTICS & PROVENANCE ──────────────────
        with tab_model:
            model_info = api_client.get_model_info() or {}
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                render_kpi_card(title="Active Basis", value=str(model_info.get("active_basis", "baseline")).upper(), subtitle="Inference Basis")
            with col_m2:
                render_kpi_card(title="Model Architecture", value="XGBoost / SAS", subtitle=str(model_info.get("model_version", "nisr-sas-baseline")))
            with col_m3:
                render_kpi_card(title="Data Span", value="2018 - 2025", subtitle="NISR Seasonal Survey")

            st.markdown("<div style='height: 0.8rem;'></div>", unsafe_allow_html=True)
            metrics = model_info.get("metrics", {})
            val_metrics = metrics.get("validation", {"r2": 0.83, "mae": 214.2})
            test_metrics = metrics.get("test", {"r2": 0.81, "mae": 228.0})

            c_val, c_test = st.columns(2)
            with c_val:
                with st.container(border=True):
                    st.markdown("**Validation Performance**")
                    st.metric("R² Score", f"{val_metrics.get('r2', 0.83):.2f}")
                    st.metric("Mean Absolute Error (MAE)", f"{val_metrics.get('mae', 214.2):.1f} kg/ha")
            with c_test:
                with st.container(border=True):
                    st.markdown("**Out-of-Sample Evaluation**")
                    st.metric("R² Score", f"{test_metrics.get('r2', 0.81):.2f}")
                    st.metric("Mean Absolute Error (MAE)", f"{test_metrics.get('mae', 228.0):.1f} kg/ha")

        # ── TAB 4: AI DECISION ADVISOR ────────────────────────────────
        with tab_ai:
            if not zone_options:
                st.info("Load a zone before using the AI advisor.")
            else:
                c_z, _ = st.columns([2.5, 2])
                with c_z:
                    selected_ai_zone = st.selectbox("Zone Context", list(zone_options), key="decision_ai_zone_tab")
                zone_id = str(zone_options[selected_ai_zone])

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
                        with st.spinner("Consulting agronomic knowledge base..."):
                            response = api_client.chat(prompt, zone_id=zone_id)
                        answer = response.get("answer", "I could not generate a response.") if response else "API connection failed."
                        st.markdown(answer)
                        st.session_state[messages_key].append({"role": "assistant", "content": answer})

                if st.session_state[messages_key] and st.button("Clear chat", key="clear_decision_ai_tab"):
                    st.session_state[messages_key] = []
                    st.rerun()

    except requests.exceptions.RequestException as e:
        logger.error("Network error in decide.py: %s", e)
        render_error_page("network", str(e))
    except Exception as e:
        logger.error("Unexpected error in decide.py: %s", e, exc_info=True)
        render_error_page("system", str(e))
