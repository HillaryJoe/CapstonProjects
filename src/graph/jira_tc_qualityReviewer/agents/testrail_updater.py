from src.core import get_logger
from src.integrations import TestRailClient
from src.core.test_case_history import set_case_history
from src.graph.jira_tc_qualityReviewer.agents.completeness_checker import _hash_case

logger = get_logger("tc_quality_testrail_updater")
client = TestRailClient()


def testrail_updater_agent(state):
    logger.info("🛠️ Test Case Quality Reviewer: TestRail updater running...")
    improved_cases = state.get("improved_cases", [])
    updated = []

    if not improved_cases:
        logger.info("No improved cases to update in TestRail")
        return {
            "updated_cases": [],
            "steps_completed": state.get("steps_completed", []) + ["testrail_updater"]
        }

    for item in improved_cases:
        case_id = item.get("case_id")
        if not case_id:
            continue

        try:
            result = client.update_case(
                case_id=case_id,
                title=item.get("improved_title"),
                preconditions=item.get("improved_preconditions"),
                steps=item.get("improved_steps"),
                expected=item.get("improved_expected_result")
            )
            updated.append({
                "case_id": case_id,
                "updated": True,
                "result": result,
                "predicted_score": item.get("predicted_score")
            })

            new_history_hash = _hash_case({
                "title": item.get("improved_title"),
                "preconditions": item.get("improved_preconditions"),
                "steps": item.get("improved_steps", []),
                "expected_result": item.get("improved_expected_result")
            })
            set_case_history(str(case_id), new_history_hash, int(item.get("predicted_score", 0)), item.get("issues", []), updated=True)
        except Exception as e:
            logger.error(f"Failed to update TestRail case {case_id}: {e}")
            updated.append({
                "case_id": case_id,
                "updated": False,
                "error": str(e)
            })

    logger.info(f"✅ Updated {sum(1 for item in updated if item.get('updated'))} TestRail case(s)")
    return {
        "updated_cases": updated,
        "steps_completed": state.get("steps_completed", []) + ["testrail_updater"]
    }
