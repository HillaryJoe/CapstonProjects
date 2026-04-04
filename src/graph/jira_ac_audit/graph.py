"""Jira AC audit graph wiring."""
from langgraph.graph import StateGraph, END
from .state import JiraAcAuditState
from .supervisor import supervisor_router, route_next, supervisor_compile
from .agents import (
    jira_fetcher_agent,
    ac_parser_agent,
    completeness_scorer_agent,
    gap_identifier_agent,
    improvement_suggester_agent,
    slack_reporter_agent
)
from src.core import get_logger

logger = get_logger("jira_ac_audit_graph")


def build_graph():
    logger.info("Building Jira AC Audit graph...")

    workflow = StateGraph(JiraAcAuditState)

    # Register all nodes (agents + supervisor pieces)
    workflow.add_node("router", supervisor_router)
    workflow.add_node("jira_fetcher", jira_fetcher_agent)
    workflow.add_node("ac_parser", ac_parser_agent)
    workflow.add_node("completeness_scorer", completeness_scorer_agent)
    workflow.add_node("gap_identifier", gap_identifier_agent)
    workflow.add_node("improvement_suggester", improvement_suggester_agent)
    workflow.add_node("slack_reporter", slack_reporter_agent)
    workflow.add_node("compile_report", supervisor_compile)

    # Always start at the router
    workflow.set_entry_point("router")

    # Router uses conditional edges — it decides where to go next based on the state
    workflow.add_conditional_edges(
        "router",
        route_next,
        {
            "jira_fetcher": "jira_fetcher",
            "ac_parser": "ac_parser",
            "completeness_scorer": "completeness_scorer",
            "gap_identifier": "gap_identifier",
            "improvement_suggester": "improvement_suggester",
            "slack_reporter": "slack_reporter",
            "FINISH": "compile_report"
        }
    )

    # Every agent returns to the router after finishing
    for step in ["jira_fetcher", "ac_parser", "completeness_scorer", "gap_identifier", "improvement_suggester", "slack_reporter"]:
    #for step in ["jira_fetcher", "ac_parser", "completeness_scorer"]:
        workflow.add_edge(step, "router")

    workflow.add_edge("compile_report", END)

    logger.info("✅ Jira AC Audit graph built")
    return workflow.compile()
