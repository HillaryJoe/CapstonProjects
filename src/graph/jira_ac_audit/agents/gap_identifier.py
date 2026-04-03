"""Identify gap categories for stories needing improvement."""
from src.core import get_logger

logger = get_logger("ac_audit_gap_identifier")

REQUIRED_CATEGORIES = ["happy_path", "error", "boundary", "ui_feedback", "security", "persistence"]
CATEGORY_AC_SUGGESTIONS = {
    "happy_path": "Add a straightforward successful path acceptance criterion describing the expected normal flow and output.",
    "error": "Add an error handling criterion for invalid inputs, service failures, or edge case rejections.",
    "boundary": "Add a boundary/edge-case criterion for minimum, maximum, and limit values.",
    "ui_feedback": "Add a UI feedback criterion specifying user-visible messages, alerts, or confirmations.",
    "security": "Add a security criterion covering auth, permissions, or data protection behavior.",
    "persistence": "Add a persistence criterion describing storage, retrieval, or data consistency behavior."
}


def gap_identifier_agent(state):
    logger.info("🕵️‍♂️ AC Audit: Gap Identifier running...")

    scored = state.get("scored_stories", [])
    gaps = []

    for story in scored:
        categories_present = story.get("categories_present", [])
        categories_missing = story.get("categories_missing", [c for c in REQUIRED_CATEGORIES if c not in categories_present])
        score = story.get("completeness_score", 0)
        skipped = story.get("skipped", False)

        meaningful_gap = (score < 8) #and not skipped
        print(f"Story {story['key']} - score: {score}, meaningful_gap: {meaningful_gap}, skipped: {skipped}")   
        
        category_gap_suggestions = {
            category: CATEGORY_AC_SUGGESTIONS.get(category, "Add a relevant acceptance criterion for this category.")
            for category in categories_missing
        }

        gap_entry = {
            "key": story.get("key"),
            "summary": story.get("summary", ""),
            "acceptance_criteria": story.get("acceptance_criteria", []),
            "completeness_score": score,
            "categories_present": categories_present,
            "categories_missing": categories_missing,
            "needs_improvement": meaningful_gap,
            "meaningful_gap": meaningful_gap,
            "meaningful_gap_categories": categories_missing if meaningful_gap else [],
            "category_gap_suggestions": category_gap_suggestions,
            "skipped": skipped
        }

        gaps.append(gap_entry)

    logger.info(f"✅ Gap analysis done for {len(gaps)} stories")
    print(f"Gap analysis results: {gaps}")
    return {
        "gap_analysis": gaps,
        "steps_completed": state.get("steps_completed", []) + ["gap_identifier"]
    }
