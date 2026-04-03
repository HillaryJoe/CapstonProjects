"""Post the AC audit report to Slack."""
from src.core import get_logger
from src.integrations import SlackClient

logger = get_logger("ac_audit_slack_reporter")
client = SlackClient()


def slack_reporter_agent(state):
    logger.info("💬 AC Audit: Slack Reporter running...")

    gap_analysis = state.get("gap_analysis", [])
    suggestions = {item["key"]: item for item in state.get("suggested_ac", [])}

    lines = ["[QA AC Audit] audit results for current run:\n"]

    for story in gap_analysis:
        key = story["key"]
        score = story.get("completeness_score", 0)
        status = "✅ No action needed" if score >= 9 else "⚠️ Action needed"

        lines.append(f"*{key}* - {story.get('summary', '')}")
        lines.append(f"Score: {score}/10")
        lines.append(f"Status: {status}")
        lines.append(f"Categories present: {', '.join(story.get('categories_present', [])) or 'none'}")
        lines.append(f"Categories missing: {', '.join(story.get('categories_missing', [])) or 'none'}")
        lines.append(f"Meaningful gap: {'yes' if story.get('meaningful_gap', False) else 'no'}")

        if story.get("skipped"):
            lines.append("__No change detected since last audit; using cached score and categories.__")

        if story.get('completeness_score', 0) < 9:
            sa = suggestions.get(key, {})
            proposed = sa.get("proposed_ac", [])
            if proposed:
                lines.append("Suggested ACs in Given/When/Then format:")
                for ac in proposed:
                    lines.append(f"- {ac}")
            else:
                lines.append("No specific Generated ACs; use RAG docs to craft Given/When/Then criteria.")

            gap_hints = story.get("category_gap_suggestions", {})
            if gap_hints:
                lines.append("Recommended improvements by category:")
                for cat, hint in gap_hints.items():
                    lines.append(f"- {cat}: {hint}")

        lines.append("---")


    message = "\n".join(lines)

    try:
        result = client.post_message(message)
        ts = result.get("ts", "")
        logger.info(f"✅ Slack report sent (ts: {ts})")

        return {
            "slack_message_ts": ts,
            "steps_completed": state["steps_completed"] + ["slack_reporter"]
        }

    except Exception as e:
        logger.error(f"❌ Slack report failed: {e}")
        return {
            "slack_message_ts": "",
            "steps_completed": state["steps_completed"] + ["slack_reporter"],
            "errors": state["errors"] + [f"slack_reporter: {e}"]
        }
