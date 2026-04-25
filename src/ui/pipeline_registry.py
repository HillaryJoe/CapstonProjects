"""
Pipeline registry — defines which pipelines are available in the UI.
Add a new PipelineConfig entry to PIPELINE_REGISTRY to expose a pipeline.
"""
from dataclasses import dataclass
from typing import Callable
from src.graph.jira_ac_audit.graph import build_graph as build_jira_ac_audit_graph
from src.graph.jira_tc_qualityReviewer.graph import build_graph as build_testrail_quality_graph


@dataclass
class PipelineConfig:
    name: str               #name of the pipeline to show in the UI
    input_type: str         # "log" | "jira_key"
    description: str        #short description to show in the UI what each agent does
    run_fn: Callable

# streamlit calling driver is not the best place for this logic, but for simplicity we'll keep it here for now. In a more complex app, you'd want to separate the UI from the orchestration logic.

def run_jira_ac_audit(jira_key: str) -> dict:       # this function will be called by the UI when the user clicks "Run Pipeline". It should invoke the LangGraph and return the final result to display.
    graph = build_jira_ac_audit_graph()
    return graph.invoke({
        "jira_key": jira_key,
        "next_agent": "",
        "jira_summary": None,
        "jira_description": None,
        "ac_audit_report": "",
        "steps_completed": [],
        "errors": [],
    })


def run_test_case_quality_review(log_data: str | None = None) -> dict:
    graph = build_testrail_quality_graph()
    return graph.invoke({
        "next_agent": "",
        "testrail_cases": None,
        "scored_cases": None,
        "duplicate_pairs": None,
        "duplicate_case_ids": None,
        "improved_cases": None,
        "updated_cases": None,
        "slack_message_ts": None,
        "summary_report": "",
        "steps_completed": [],
        "errors": [],
    })



PIPELINE_REGISTRY: list[PipelineConfig] = [
    PipelineConfig(
        name="Fetch Jira AC → Audit",
        input_type="jira_key",
        description="Analyze Acceptance Criteria and generate story completion report.",
        run_fn=run_jira_ac_audit
    ),
    PipelineConfig(
        name="TestRail Test Case Quality Review",
        input_type="log",
        description="Review TestRail cases for quality, rewrite low-quality cases, and post a Slack summary.",
        run_fn=run_test_case_quality_review
    ),

]

if __name__ == "__main__":
    import streamlit as st

    st.title("Pipeline Registry")

    # Select a pipeline
    pipeline_names = [config.name for config in PIPELINE_REGISTRY]
    selected_pipeline_name = st.selectbox("Select a Pipeline", pipeline_names)

    # Find the selected config
    selected_config = next(config for config in PIPELINE_REGISTRY if config.name == selected_pipeline_name)

    st.write(f"**Description:** {selected_config.description}")
    st.write(f"**Input Type:** {selected_config.input_type}")

    # Input based on type
    if selected_config.input_type == "jira_key":
        user_input = st.text_input("Enter Jira Key")
    elif selected_config.input_type == "log":
        user_input = st.text_area("Enter Log Data")
    else:
        user_input = None

    if st.button("Run Pipeline"):
        if user_input or selected_config.input_type == "log":
            try:
                if selected_config.input_type == "jira_key":
                    result = selected_config.run_fn(user_input)
                else:
                    result = selected_config.run_fn()
                st.json(result)
            except Exception as e:
                st.error(f"Error running pipeline: {str(e)}")
        else:
            st.error("Please provide the required input.")