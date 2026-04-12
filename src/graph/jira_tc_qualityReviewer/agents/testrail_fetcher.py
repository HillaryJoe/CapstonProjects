import os
import re
from src.core import get_logger
from src.integrations import TestRailClient
from dotenv import load_dotenv

load_dotenv()
logger = get_logger("tc_quality_testrail_fetcher")
client = TestRailClient()


def _normalize_case(raw: dict) -> dict:
    case_id = raw.get("id") or raw.get("case_id") or raw.get("caseId")
    title = (raw.get("title") or raw.get("name") or "").strip()
    preconditions = (raw.get("custom_preconds") or raw.get("custom_preconditions") or raw.get("custom_precondition") or "").strip()
    expected_result = (raw.get("custom_expected") or raw.get("expected") or raw.get("custom_expected_result") or "").strip()
    steps = []

    for item in raw.get("custom_steps_separated", []) or []:
        if not isinstance(item, dict):
            continue
        step_text = item.get("step") or item.get("content") or item.get("action") or ""
        expected_step = item.get("expected") or item.get("expected_result") or ""
        if step_text:
            steps.append(f"Step : {step_text.strip()}-- Expected Result: {expected_step.strip()}" if expected_step else step_text.strip())
        if expected_step and not expected_result:
            expected_result = expected_step.strip()
           

    if not steps and raw.get("custom_steps"):
        raw_steps = raw.get("custom_steps")
        if isinstance(raw_steps, str):
            lines = [line.strip() for line in raw_steps.splitlines() if line.strip()]
            steps.extend(lines)

    if not title and raw.get("refs"):
        title = raw.get("refs").strip()

    return {
        "id": case_id,
        "title": title,
        "preconditions": preconditions,
        "steps": steps,
        "expected_result": expected_result,
        "raw": raw
    }


def testrail_fetcher_agent(state):
    logger.info("🔍 Test Case Quality Reviewer: TestRail fetcher running...")

    project_id = os.getenv("TESTRAIL_PROJECT_ID")
    suite_id = os.getenv("TESTRAIL_SUITE_ID")
    section_id = os.getenv("TESTRAIL_SECTION_ID")

    if not project_id:
        error_message = "Missing TESTRAIL_PROJECT_ID environment variable for TestRail case fetching"
        logger.error(error_message)
        return {
            "testrail_cases": [],
            "steps_completed": state.get("steps_completed", []) + ["testrail_fetcher"],
            "errors": state.get("errors", []) + [error_message]
        }

    try:
        raw_response = client.get_cases(
            project_id=int(project_id),
            suite_id=int(suite_id) if suite_id else None,
            section_id=int(section_id) if section_id else None
        )
        raw_cases = raw_response.get('cases', []) if isinstance(raw_response, dict) else raw_response
        cases = [_normalize_case(raw) for raw in raw_cases]
        logger.info(f"✅ TestRail fetcher returned {len(cases)} cases")
      #  logger.info(f"✅ TestRail cases returned state {cases}")
        
        return {
            "testrail_cases": cases,
            "steps_completed": state.get("steps_completed", []) + ["testrail_fetcher"]
        }

    except Exception as e:
        logger.error(f"❌ TestRail fetcher failed: {e}")
        return {
            "testrail_cases": [],
            "steps_completed": state.get("steps_completed", []) + ["testrail_fetcher"],
            "errors": state.get("errors", []) + [f"testrail_fetcher: {e}"]
        }
