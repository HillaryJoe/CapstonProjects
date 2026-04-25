"""
Supervisor for TC Quality Review pipeline.

Key routing rule — use `is None` not `not` for all list fields:
  - `not state.get("field")` is True for BOTH None AND []
  - `state.get("field") is None` is True ONLY for None

This matters because agents return [] (empty list) when they run
but find nothing (e.g. no duplicates, no cases to improve).
Using `not` treats [] the same as None and re-routes endlessly.
"""
from src.core import get_logger

logger = get_logger("tc_quality_supervisor")


def supervisor_router(state):
    return state


def route_next(state):
    errors = state.get("errors", [])

    # Agent 1: testrail_fetcher
    # Use `is None` — fetcher returns [] if TestRail has zero cases,
    # which is a valid result and should NOT trigger a re-fetch.
    if state.get("testrail_cases") is None:
        if errors:
            logger.error(f"Aborting: fetch already failed. Errors: {errors[-1]}")
            return "FINISH"
        logger.info("-> Routing to: testrail_fetcher")
        return "testrail_fetcher"

    # Agent 2: completeness_checker
    # Use `is None` — checker returns [] when there are no cases to score.
    if state.get("scored_cases") is None:
        logger.info("-> Routing to: completeness_checker")
        return "completeness_checker"

    # Agent 3: duplicate_detector
    if state.get("duplicate_pairs") is None:
        logger.info("-> Routing to: duplicate_detector")
        return "duplicate_detector"

    # Agent 4: improvement_suggester
    if state.get("improved_cases") is None:
        logger.info("-> Routing to: improvement_suggester")
        return "improvement_suggester"

    # Agent 5: testrail_updater
    if state.get("updated_cases") is None:
        logger.info("-> Routing to: testrail_updater")
        return "testrail_updater"

    # Agent 6: slack_reporter
    # slack_message_ts is a string. On timeout the reporter returns "" (falsy).
    # Stop retrying after 2 recorded Slack errors.
    slack_ts     = state.get("slack_message_ts")
    slack_errors = [e for e in errors if "slack_reporter" in e]

    if slack_ts is None or slack_ts == "":
        if len(slack_errors) >= 2:
            logger.warning(
                f"Slack reporter failed {len(slack_errors)} time(s) - "
                "skipping further retries and compiling report"
            )
            return "FINISH"
        logger.info("-> Routing to: slack_reporter")
        return "slack_reporter"

    logger.info("-> All agents complete. Compiling final report...")
    return "FINISH"


def supervisor_compile(state):
    logger.info("Supervisor compiling Test Case Quality Review final report...")

    scored        = state.get("scored_cases",      []) or []
    duplicate_ids = set(state.get("duplicate_case_ids") or [])
    updated       = state.get("updated_cases",     []) or []

    total        = len(scored)
    improved     = sum(1 for item in updated if item.get("updated"))
    duplicates   = len(duplicate_ids)
    high_quality = sum(
        1 for case in scored
        if case.get("quality_score", 0) >= 7 and case.get("id") not in duplicate_ids
    )

    before_scores = [case.get("quality_score", 0) for case in scored]
    after_scores  = []
    for case in scored:
        after_score = case.get("quality_score", 0)
        for item in state.get("improved_cases", []) or []:
            if item.get("case_id") == case.get("id") and item.get("predicted_score") is not None:
                after_score = item.get("predicted_score")
                break
        after_scores.append(after_score)

    average_before = round(sum(before_scores) / total, 2) if total else 0.0
    average_after  = round(sum(after_scores)  / total, 2) if total else 0.0

    all_issues = []
    for case in scored:
        all_issues.extend(case.get("issues", []))
    unique_issues = sorted(set(all_issues))

    report_lines = [
        "=== TEST CASE QUALITY REVIEW REPORT ===",
        f"Total reviewed:             {total}",
        f"Improved cases updated:     {improved}",
        f"Duplicates flagged:         {duplicates}",
        f"High quality cases:         {high_quality}",
        f"Average quality before:     {average_before}/10",
        f"Average quality after:      {average_after}/10",
        "",
        "Most common issues found:",
    ]

    if unique_issues:
        for issue in unique_issues:
            report_lines.append(f"  - {issue}")
    else:
        report_lines.append("  - None detected")

    report_lines.append("")
    report_lines.append("Detailed case results:")
    for case in scored:
        cid   = case.get("id")
        score = case.get("quality_score", 0)
        if cid in duplicate_ids:
            status = "Duplicate flagged"
        elif score >= 7:
            status = "High quality"
        else:
            status = "Needs improvement"
        report_lines.append(
            f"  Case {cid}: {case.get('title', '')} - Score {score}/10 - {status}"
        )

    errors = state.get("errors", [])
    if errors:
        report_lines.append("")
        report_lines.append("Pipeline warnings:")
        for err in errors:
            report_lines.append(f"  {err}")

    return {
        "summary_report":  "\n".join(report_lines),
        "steps_completed": state.get("steps_completed", []) + ["supervisor"],
    }