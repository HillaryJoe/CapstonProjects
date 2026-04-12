"""
TestRail Updater Agent
-----------------------
For each improved test case produced by improvement_suggester,
calls the TestRail update_case API to replace the original content
with the improved version — including per-step expected results.

improved_steps format from improvement_suggester:
  [{"action": "Navigate to page", "expected": "Page loads"},
   {"action": "Click Login",      "expected": "Error message shown"}, ...]
"""
from src.core import get_logger
from src.integrations import TestRailClient
from src.core.test_case_history import set_case_history
from src.graph.jira_tc_qualityReviewer.agents.completeness_checker import _hash_case

logger = get_logger("tc_quality_testrail_updater")
client = TestRailClient()


def _steps_to_strings(steps) -> list:
    """
    Convert improved_steps (list of {"action":..,"expected":..} dicts)
    to a plain list of strings for _hash_case, which calls "\n".join(steps)
    and therefore requires list[str] not list[dict].
    """
    if not steps:
        return []
    result = []
    for s in steps:
        if isinstance(s, dict):
            result.append(str(s.get("action", s.get("step", ""))).strip())
        elif isinstance(s, str):
            result.append(s.strip())
    return [r for r in result if r]


def testrail_updater_agent(state):
    """
    Iterates over state["improved_cases"] and pushes each one to TestRail.

    Produces state["updated_cases"]: list of dicts each containing:
      case_id, updated (bool), predicted_score, result or error
    """
    logger.info("🛠️ Test Case Quality Reviewer: TestRail updater running...")

    improved_cases = state.get("improved_cases", [])

    if not improved_cases:
        logger.info("No improved cases to update — skipping TestRail update")
        return {
            "updated_cases":   [],
            "steps_completed": state.get("steps_completed", []) + ["testrail_updater"],
        }

    logger.info(f"📤 Updating {len(improved_cases)} case(s) in TestRail...")
    updated = []

    for item in improved_cases:
        case_id           = item.get("case_id")
        improved_title    = item.get("improved_title",         "")
        improved_preconds = item.get("improved_preconditions", "")
        improved_steps    = item.get("improved_steps",         [])
        improved_expected = item.get("improved_expected_result","")
        predicted_score   = item.get("predicted_score",        0)
        original_score    = item.get("original_score",         0)

        if not case_id:
            logger.warning("Skipping item with missing case_id")
            continue

        logger.info(
            f"  → Case {case_id}: "
            f"score {original_score}/10 → {predicted_score}/10 | "
            f"{len(improved_steps)} step(s)"
        )

        try:
            # testrail_client._build_steps_payload handles list[dict] correctly
            result = client.update_case(
                case_id=case_id,
                title=improved_title,
                preconditions=improved_preconds,
                steps=improved_steps,
                expected=improved_expected,
            )

            logger.info(f"  ✅ Case {case_id} updated successfully in TestRail")
            updated.append({
                "case_id":         case_id,
                "updated":         True,
                "predicted_score": predicted_score,
                "result":          result,
            })

            # _hash_case does "\n".join(steps) — must be list[str], not list[dict]
            new_hash = _hash_case({
                "title":           improved_title,
                "preconditions":   improved_preconds,
                "steps":           _steps_to_strings(improved_steps),
                "expected_result": improved_expected,
            })
            set_case_history(
                str(case_id),
                new_hash,
                int(predicted_score),
                item.get("issues", []),
                updated=True,
            )

        except Exception as e:
            logger.error(f"  ❌ Failed to update TestRail case {case_id}: {e}")
            updated.append({
                "case_id": case_id,
                "updated": False,
                "error":   str(e),
            })

    success_count = sum(1 for i in updated if i.get("updated"))
    fail_count    = len(updated) - success_count
    logger.info(f"✅ TestRail update complete — {success_count} succeeded, {fail_count} failed")

    return {
        "updated_cases":   updated,
        "steps_completed": state.get("steps_completed", []) + ["testrail_updater"],
    }