"""Presentation helpers for grounded AI advisor responses."""
from typing import Any

import streamlit as st


def render_advisor_response(response: dict[str, Any]) -> None:
    """Render an advisor answer with its evidence type, scope, and sources."""
    answer_type = response.get("answer_type")
    if answer_type == "general_guidance":
        st.info("General farming guidance; this is not a conclusion from your zone's records.")
    elif answer_type == "insufficient_evidence":
        st.warning("The available records do not support a specific conclusion for this question.")

    if response.get("source") == "grounded-context":
        st.warning(
            "The AI provider did not return a generated answer. This response uses the "
            "backend's available zone context; check provider configuration if you expect AI-generated advice."
        )

    answer = str(response.get("answer") or "").strip()
    if answer:
        st.markdown(answer)
    else:
        st.error("The advisor returned no answer. Please try again.")

    details = response.get("evidence_source_details")
    sources = response.get("evidence_sources")
    scope = response.get("evidence_scope")
    if scope or details or sources:
        with st.expander("Evidence and scope"):
            if scope:
                st.caption(f"Scope: {scope}")
            if isinstance(details, list) and details:
                for detail in details:
                    if not isinstance(detail, dict):
                        continue
                    title = str(detail.get("title") or detail.get("publisher") or "Source")
                    url = str(detail.get("url") or "")
                    publisher = str(detail.get("publisher") or "")
                    if url.startswith(("https://", "http://")):
                        st.markdown(f"- [{title}]({url})" + (f" — {publisher}" if publisher else ""))
                    else:
                        st.markdown(f"- {title}" + (f" — {publisher}" if publisher else ""))
                    if detail.get("coverage"):
                        st.caption(f"Coverage: {detail['coverage']}")
                    if detail.get("limitations"):
                        st.caption(f"Limitation: {detail['limitations']}")
            elif isinstance(sources, list):
                for source in sources:
                    st.markdown(f"- {source}")
