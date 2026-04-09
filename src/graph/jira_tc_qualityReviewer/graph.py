from langgraph.graph import StateGraph, END
from .state import JiraTCQualityState
from .supervisor import supervisor_router, route_next, supervisor_compile
from .agents import (
    testrail_fetcher_agent,
    completeness_checker_agent,
    duplicate_detector_agent,
    improvement_suggester_agent,
    testrail_updater_agent,
    slack_reporter_agent
)
from src.core import get_logger

logger = get_logger("jira_tc_quality_reviewer_graph")


def build_graph():
    logger.info("Building Jira Test Case Quality Reviewer graph...")
    workflow = StateGraph(JiraTCQualityState)

    workflow.add_node("router", supervisor_router)
    workflow.add_node("testrail_fetcher", testrail_fetcher_agent)
    workflow.add_node("completeness_checker", completeness_checker_agent)
    workflow.add_node("duplicate_detector", duplicate_detector_agent)
    workflow.add_node("improvement_suggester", improvement_suggester_agent)
    workflow.add_node("testrail_updater", testrail_updater_agent)
    workflow.add_node("slack_reporter", slack_reporter_agent)
    workflow.add_node("compile_report", supervisor_compile)

    workflow.set_entry_point("router")
    workflow.add_conditional_edges(
        "router",
        route_next,
        {
            "testrail_fetcher": "testrail_fetcher",
            "completeness_checker": "completeness_checker",
            "duplicate_detector": "duplicate_detector",
            "improvement_suggester": "improvement_suggester",
            "testrail_updater": "testrail_updater",
            "slack_reporter": "slack_reporter",
            "FINISH": "compile_report"
        }
    )

    for node in [
        "testrail_fetcher",
        "completeness_checker",
        "duplicate_detector",
        "improvement_suggester",
        "testrail_updater",
        "slack_reporter"
    ]:
        workflow.add_edge(node, "router")

    workflow.add_edge("compile_report", END)
    logger.info("✅ Jira Test Case Quality Reviewer graph built")
    return workflow.compile()
