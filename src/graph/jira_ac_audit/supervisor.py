"""Supervisor routing and compilation for AC audit pipeline."""
from src.core import get_logger

logger = get_logger("ac_audit_supervisor")


def supervisor_router(state):
    return state


def route_next(state):
    if not state.get("stories"):                                # stories = None? → fetch first
        logger.info("→ Routing to: jira_fetcher")
        return "jira_fetcher"

    if not state.get("parsed_stories"):                          # not parsed yet?  
        logger.info("→ Routing to: ac_parser")
        return "ac_parser"

    if not state.get("scored_stories"):                          # not scored yet?   
        logger.info("→ Routing to: completeness_scorer")
        return "completeness_scorer"

    if not state.get("gap_analysis"):                            # not analyzed for gaps yet?    
        logger.info("→ Routing to: gap_identifier")
        return "gap_identifier"

    if not state.get("suggested_ac"):                           # not suggested improvements yet?   
        logger.info("→ Routing to: improvement_suggester")
        return "improvement_suggester"

    if not state.get("slack_message_ts"):
        logger.info("→ Routing to: slack_reporter")
        return "slack_reporter"

    logger.info("→ All agents complete. Compiling report...")
    return "FINISH"                                             # everything done → compile


def supervisor_compile(state):
    logger.info("Supervisor compiling AC audit final report...")

    stories = state.get("scored_stories", [])
    gaps = {item["key"]: item for item in state.get("gap_analysis", [])}
    suggestions = {item["key"]: item for item in state.get("suggested_ac", [])}

    report_parts = ["=== JIRA ACCEPTANCE CRITERIA AUDIT REPORT ===",
                    "Reference: AC standards (Given/When/Then, scenario coverage, measurable outcomes)",
                    "- Testability criteria: clear trigger, measurable expected outcome, pass/fail clarity, user-visible behavior",
                    "- Complete score 9-10, minor gap 7-8, major gap 5-6, incomplete <5",
                    ""]

    for story in stories:
        key = story.get("key")
        summary = story.get("summary", "")
        score = story.get("completeness_score", 0)

        gap = gaps.get(key, {})
        suggestions_for_story = suggestions.get(key, {}).get("proposed_ac", [])

        if score >= 9:
            status = "Complete — No action needed"
        elif score >= 7:
            status = "Minor gaps — 1-2 scenario types missing"
        elif score >= 5:
            status = "Major gaps — multiple missing types, revise before sprint"
        else:
            status = "Incomplete — critical defects risk, rewrite recommended"

        report_parts.append(f"Story: {key} - {summary}")
        report_parts.append(f"Score: {score}/10")
        report_parts.append(f"Status: {status}")
        report_parts.append(f"Categories present: {', '.join(story.get('categories_present', [])) or 'none'}")
        report_parts.append(f"Categories missing: {', '.join(story.get('categories_missing', [])) or 'none'}")
        report_parts.append(f"Meaningful gap: {'yes' if gap.get('meaningful_gap') else 'no'}")

        if gap.get("category_gap_suggestions"):
            report_parts.append("Category suggestions:")
            for cat, hint in gap.get("category_gap_suggestions", {}).items():
                report_parts.append(f"- {cat}: {hint}")

        if suggestions_for_story:
            report_parts.append("Suggested ACs (Given/When/Then):")
            for ac in suggestions_for_story:
                report_parts.append(f"- {ac}")
        else:
            report_parts.append("Suggested ACs: none generated")

        report_parts.append("-----")

    final_report = "\n".join(report_parts)

    return {
        "summary_report": final_report,
        "steps_completed": state["steps_completed"] + ["supervisor"]
    }
