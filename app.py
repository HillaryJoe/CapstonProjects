"""
Agentic AI Course — Multi-Pipeline Streamlit App
"""
import streamlit as st
from src.ui.pipeline_registry import PIPELINE_REGISTRY
from src.ui.components import render_report_output

st.set_page_config(
    page_title="Agentic AI Pipelines",
    page_icon="🤖",
    layout="wide",
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🤖 Agentic AI")
    st.caption("Multi-Pipeline Runner")
    st.divider()

    if PIPELINE_REGISTRY:
        selected_name = st.selectbox(
            "Select Pipeline",
            [p.name for p in PIPELINE_REGISTRY],
        )
        selected = next(p for p in PIPELINE_REGISTRY if p.name == selected_name)
    else:
        st.info("No pipelines configured yet.")
        selected = None

    st.divider()
    st.caption("Built with LangGraph + Streamlit")

# ── Main area ─────────────────────────────────────────────────────────────────
if not selected:
    st.title("Agentic AI Pipelines")
    st.info("No pipelines available yet. Pipelines will appear here as they are registered.")
else:
    st.title(f"Pipeline: {selected.name}")
    st.caption(selected.description)

    user_input = None

    if selected.input_type == 'log':
        uploaded = st.file_uploader("Upload Log File", type=["txt", "log"])
        if uploaded:
            user_input = uploaded.read().decode("utf-8")
        else:
            user_input = st.text_area("Or paste log content here", height=200)

    elif selected.input_type == "jira_key":
        user_input = st.text_input("Jira Issue Key", placeholder="QA-1")

    if st.button("Run Pipeline", disabled=not user_input):
        with st.spinner("Running pipeline..."):
            st.session_state["result"] = selected.run_fn(user_input)

    if "result" in st.session_state:
        render_report_output(st.session_state["result"])