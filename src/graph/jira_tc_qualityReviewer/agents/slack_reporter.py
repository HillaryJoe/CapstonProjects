from collections import Counter
from src.core import get_logger
from src.integrations import SlackClient

logger = get_logger("tc_quality_slack_reporter")
client = SlackClient()


def _format_average(scores):
    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 2)


def _top_issues(scored_cases):
    counter = Counter()
    for case in scored_cases:
        for issue in case.get("issues", []):
            counter[issue] += 1
    return counter.most_common(5)


def slack_reporter_agent(state):
    logger.info("💬 Test Case Quality Reviewer: Slack reporter running...")
    scored_cases = state.get("scored_cases", [])
    duplicate_ids = set(state.get("duplicate_case_ids", []))
    improved = state.get("improved_cases", [])
    updated = state.get("updated_cases", [])

    before_scores = [case.get("quality_score", 0) for case in scored_cases]
    after_scores = []
    for case in scored_cases:
        after_score = case.get("quality_score", 0)
        for improvement in improved:
            if improvement.get("case_id") == case.get("id") and improvement.get("predicted_score") is not None:
                after_score = improvement.get("predicted_score")
                break
        after_scores.append(after_score)

    total_reviewed = len(scored_cases)
    improved_count = sum(1 for item in updated if item.get("updated"))
    duplicate_count = len(duplicate_ids)
    high_quality_count = sum(1 for case in scored_cases if case.get("quality_score", 0) >= 7 and case.get("id") not in duplicate_ids)
    average_before = _format_average(before_scores)
    average_after = _format_average(after_scores)
    common_issues = _top_issues(scored_cases)

    lines = [
        "*Test Case Quality Review Summary*",
        f"Total test cases reviewed: {total_reviewed}",
        f"Number improved: {improved_count}",
        f"Number flagged as duplicates: {duplicate_count}",
        f"Number already high quality: {high_quality_count}",
        f"Average quality score before: {average_before}/10",
        f"Average quality score after: {average_after}/10",
        ""
    ]

    if common_issues:
        lines.append("Most common quality issues found:")
        for issue, count in common_issues:
            lines.append(f"- {issue}: {count}")
    else:
        lines.append("No common issues detected.")

    lines.append("")
    if improved_count:
        lines.append("Updated cases:")
        for item in updated:
            if item.get("updated"):
                lines.append(f"- Case {item.get('case_id')} updated successfully")

    message = "\n".join(lines)

    try:
        result = client.post_message(message)
        ts = result.get("ts", "")
        logger.info(f"✅ Slack report posted (ts={ts})")
        return {
            "slack_message_ts": ts,
            "steps_completed": state.get("steps_completed", []) + ["slack_reporter"]
        }
    except Exception as e:
        logger.error(f"❌ Slack report failed: {e}")
        return {
            "slack_message_ts": "",
            "steps_completed": state.get("steps_completed", []) + ["slack_reporter"],
            "errors": state.get("errors", []) + [f"slack_reporter: {e}"]
        }
