from src.core import get_logger

logger = get_logger("tc_quality_supervisor")


def supervisor_router(state):
    return state


def route_next(state):
    errors = state.get("errors", [])
    
    if not state.get("testrail_cases"):
        if errors:
            logger.error(f"❌ Aborting: TestRail fetch failed. Errors: {errors[-1]}")
            return "FINISH"
        logger.info("→ Routing to: testrail_fetcher")
        return "testrail_fetcher"

    if not state.get("scored_cases"):
        logger.info("→ Routing to: completeness_checker")
        return "completeness_checker"

    if state.get("duplicate_pairs") is None:
        logger.info("→ Routing to: duplicate_detector")
        return "duplicate_detector"

    if state.get("improved_cases") is None:
        logger.info("→ Routing to: improvement_suggester")
        return "improvement_suggester"

    if state.get("updated_cases") is None:
        logger.info("→ Routing to: testrail_updater")
        return "testrail_updater"

    if not state.get("slack_message_ts"):
        logger.info("→ Routing to: slack_reporter")
        return "slack_reporter"

    logger.info("→ All agents complete. Compiling final report...")
    return "FINISH"


def supervisor_compile(state):
    logger.info("Supervisor compiling Test Case Quality Review final report...")

    scored = state.get("scored_cases", []) or []
    duplicate_ids = set(state.get("duplicate_case_ids") or [])
    updated = state.get("updated_cases", []) or []

    total = len(scored)
    improved = sum(1 for item in updated if item.get("updated"))
    duplicates = len(duplicate_ids)
    high_quality = sum(1 for case in scored if case.get("quality_score", 0) >= 7 and case.get("id") not in duplicate_ids)
    before_scores = [case.get("quality_score", 0) for case in scored]
    after_scores = []
    for case in scored:
        after_score = case.get("quality_score", 0)
        for item in state.get("improved_cases", []):
            if item.get("case_id") == case.get("id") and item.get("predicted_score") is not None:
                after_score = item.get("predicted_score")
                break
        after_scores.append(after_score)

    average_before = round(sum(before_scores) / total, 2) if total else 0.0
    average_after = round(sum(after_scores) / total, 2) if total else 0.0

    issues = []
    for case in scored:
        issues.extend(case.get("issues", []))
    unique_issues = sorted(set(issues))

    report_lines = [
        "=== TEST CASE QUALITY REVIEW REPORT ===",
        f"Total reviewed: {total}",
        f"Improved cases updated: {improved}",
        f"Duplicates flagged: {duplicates}",
        f"High quality cases: {high_quality}",
        f"Average quality before: {average_before}/10",
        f"Average quality after: {average_after}/10",
        "",
        "Most common issues found:",
    ]

    if unique_issues:
        for issue in unique_issues:
            report_lines.append(f"- {issue}")
    else:
        report_lines.append("- None detected")

    report_lines.append("")
    report_lines.append("Detailed case results:")
    for case in scored:
        status = "High quality" if case.get("quality_score", 0) >= 7 else "Needs improvement"
        if case.get("id") in duplicate_ids:
            status = "Duplicate flagged"
        report_lines.append(f"Case {case.get('id')}: {case.get('title', '')} — Score {case.get('quality_score', 0)}/10 — {status}")

    return {
        "summary_report": "\n".join(report_lines),
        "steps_completed": state.get("steps_completed", []) + ["supervisor"]
    }
