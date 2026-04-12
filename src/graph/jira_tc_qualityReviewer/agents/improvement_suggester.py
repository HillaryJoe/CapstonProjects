"""
Improvement Suggester Agent
----------------------------
For every test case scoring below 7, asks the LLM to rewrite it with:
  - specific steps, each carrying its own "action" and "expected" result
  - a clear overall expected_result
  - explicit preconditions
Uses RAG context from the knowledge base to ensure rewrites meet quality standards.
"""
import re
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.core import get_logger, get_langchain_llm, search_vector_store
from src.prompts.tc_quality_prompts import IMPROVE_TEST_CASE_SYSTEM_PROMPT
from src.graph.jira_tc_qualityReviewer.agents.completeness_checker import score_test_case

logger = get_logger("tc_quality_improvement_suggester")

# LLM chain
llm = get_langchain_llm()
prompt_template = ChatPromptTemplate.from_messages([
    ("system", IMPROVE_TEST_CASE_SYSTEM_PROMPT),
    ("user", "{testcase}")
])
parser = StrOutputParser()
chain = prompt_template | llm | parser


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean_json_response(response: str) -> str:
    """Strip markdown code fences the LLM sometimes adds around JSON."""
    if not response:
        return ""
    text = response.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.lower().startswith("json"):
            text = text[4:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def _split_embedded_expected(text: str):
    """
    Some LLMs embed the expected result inside the action string like:
      "Step : 1. Navigate to the login page.-- Expected Result: Page loads."
      "Navigate to login page -- Expected Result: Page loads"
      "Navigate to login page. Expected Result: Page loads"

    This helper splits them into (action, expected).
    Returns (original_text, "") if no embedded expected is found.
    """
    # Patterns the LLM uses to embed expected result in the action string
    patterns = [
        r"[-–—]{1,2}\s*[Ee]xpected\s*[Rr]esult\s*[:：]\s*(.+)$",   # "-- Expected Result: ..."
        r"\.\s*[Ee]xpected\s*[Rr]esult\s*[:：]\s*(.+)$",             # ". Expected Result: ..."
        r"\n[Ee]xpected\s*[Rr]esult\s*[:：]\s*(.+)$",                # newline then "Expected Result:"
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            expected = match.group(1).strip()
            action   = text[:match.start()].strip().rstrip(".-– ")
            # Remove leading "Step : N." or "N." numbering prefix from action
            action = re.sub(r"^[Ss]tep\s*[:：]?\s*\d+[.)]\s*", "", action).strip()
            action = re.sub(r"^\d+[.)]\s*", "", action).strip()
            return action, expected

    # No embedded expected — just clean up any leading "Step : N." prefix
    clean = re.sub(r"^[Ss]tep\s*[:：]?\s*\d+[.)]\s*", "", text).strip()
    clean = re.sub(r"^\d+[.)]\s*", "", clean).strip()
    return clean, ""


def _normalise_steps(raw_steps) -> list:
    """
    Guarantee steps is always list[{"action": str, "expected": str}].

    Handles every format the LLM might return:
      1. list[{"action":..,"expected":..}]          <- correct JSON format
      2. list[str] with embedded expected result     <- "Step 1. action-- Expected Result: ..."
      3. list[str] plain                             <- old plain-string format
      4. dict {action: expected}                     <- old dict format
    """
    if not raw_steps:
        return []

    if isinstance(raw_steps, list):
        normalised = []
        for item in raw_steps:
            if isinstance(item, dict):
                # Format 1: correct {"action":..,"expected":..}
                action   = str(item.get("action", item.get("step", ""))).strip()
                expected = str(item.get("expected", "")).strip()
                # Even inside a dict the action might have embedded expected
                if action:
                    action, embedded = _split_embedded_expected(action)
                    if not expected and embedded:
                        expected = embedded
                    normalised.append({"action": action, "expected": expected})

            elif isinstance(item, str) and item.strip():
                # Format 2 / 3: plain string, possibly with embedded expected
                action, expected = _split_embedded_expected(item.strip())
                if action:
                    normalised.append({"action": action, "expected": expected})
        return normalised

    if isinstance(raw_steps, dict):
        # Format 4: {action_text: expected_text}
        return [
            {"action": str(k).strip(), "expected": str(v).strip()}
            for k, v in raw_steps.items() if str(k).strip()
        ]

    return []


def _fill_missing_step_expected(steps: list, overall_expected: str) -> list:
    """
    Ensure no step has an empty 'expected' field.
    Last step gets the overall expected result.
    Intermediate steps get a context-derived default based on the action keyword.
    """
    total  = len(steps)
    filled = []
    for idx, step in enumerate(steps):
        action   = step.get("action", "")
        expected = step.get("expected", "").strip()

        if not expected:
            if idx == total - 1:
                expected = overall_expected or "The action completes successfully with the expected outcome."
            else:
                a = action.lower()
                if any(w in a for w in ["navigate", "open", "go to", "visit", "launch"]):
                    expected = "The page loads successfully and all required elements are visible."
                elif any(w in a for w in ["enter", "type", "input", "fill"]):
                    expected = "The entered value is displayed correctly in the field."
                elif any(w in a for w in ["click", "press", "submit", "tap", "select"]):
                    expected = "The system responds to the action and proceeds to the next state."
                elif any(w in a for w in ["verify", "confirm", "check", "assert"]):
                    expected = "The observed state matches the expected condition."
                else:
                    expected = "The step completes without errors."

        filled.append({"action": action, "expected": expected})
    return filled


def _build_prompt(case: dict, rag_context: str) -> str:
    """Build the user prompt injected into the LLM chain."""
    raw = case.get("steps", [])
    if raw and isinstance(raw[0], dict):
        steps_text = "\n".join(
            f"{i+1}. Action: {s.get('action','')} | Expected: {s.get('expected','')}"
            for i, s in enumerate(raw)
        )
    else:
        steps_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(raw)) or "None"

    return (
        f"Rewrite the following TestRail test case to meet high quality standards.\n\n"
        f"CRITICAL OUTPUT RULES:\n"
        f"  - Return ONLY a valid JSON object.\n"
        f"  - 'steps' MUST be a JSON array of objects.\n"
        f"  - Each step object MUST have exactly two keys: 'action' and 'expected'.\n"
        f"  - 'action' contains ONLY the step instruction — NO expected result text inside it.\n"
        f"  - 'expected' contains ONLY the observable result for that step.\n"
        f"  - Do NOT embed expected result text inside the action string.\n"
        f"  - Do NOT prefix steps with 'Step : N.' or '1.' numbering.\n\n"
        f"WRONG (do not do this):\n"
        f'  {{"action": "Step : 1. Navigate to login page.-- Expected Result: Page loads.", "expected": ""}}\n\n'
        f"CORRECT (do this):\n"
        f'  {{"action": "Navigate to the login page", "expected": "Login page loads and input fields are visible"}}\n\n'
        f"RAG quality guidelines:\n{rag_context}\n\n"
        f"Current test case to rewrite:\n"
        f"Title: {case.get('title', '')}\n"
        f"Preconditions: {case.get('preconditions', '') or 'None'}\n"
        f"Steps:\n{steps_text}\n"
        f"Expected Result: {case.get('expected_result', '') or 'None'}\n"
    )


def _fallback_improved_case(case: dict) -> dict:
    """Minimal improvement when the LLM call fails entirely."""
    title = (case.get("title") or "").strip()
    if not title or len(title) < 15:
        title = (title + " - verify expected behaviour").strip(" -")

    preconditions = (case.get("preconditions") or "").strip()
    if not preconditions:
        preconditions = "User is authenticated and the application is in the correct initial state."

    raw_steps = case.get("steps", [])
    steps = _normalise_steps(raw_steps)
    if not steps:
        steps = [
            {"action": "Navigate to the relevant page.", "expected": "Page loads successfully."},
            {"action": "Perform the required action.",   "expected": "System responds as expected."},
            {"action": "Observe the result.",            "expected": "Result matches the expected outcome."},
        ]

    expected = (case.get("expected_result") or "").strip()
    if not expected:
        expected = "The application responds as defined by the acceptance criteria."

    return {"title": title, "preconditions": preconditions, "steps": steps, "expected_result": expected}


# ---------------------------------------------------------------------------
# Agent entry point
# ---------------------------------------------------------------------------

def improvement_suggester_agent(state):
    """
    For every scored test case with quality_score < 7 (and not a duplicate),
    rewrites it using the LLM + RAG context.

    Each step in improved_steps is {"action": str, "expected": str}
    so testrail_updater maps them directly to custom_steps_separated.
    """
    logger.info("🔧 Test Case Quality Reviewer: improvement suggester running...")
    cases    = state.get("scored_cases", [])
    improved = []

    # Step 1: fetch RAG context once
    rag_context = ""
    try:
        results = search_vector_store(
            "Test case quality improvement writing guidelines clear steps expected result preconditions",
            top_k=3
        )
        context_parts = []
        for doc, _ in results:
            source = doc.metadata.get("source", "unknown")
            context_parts.append(f"[{source}]\n{doc.page_content}")
        rag_context = "\n\n---\n\n".join(context_parts).strip()
        logger.info(f"📚 RAG context loaded ({len(rag_context)} chars)")
    except Exception as e:
        logger.warning(f"RAG search failed, using default guidelines: {e}")

    if not rag_context:
        rag_context = (
            "Quality standards for test cases:\n"
            "- Title: specific, describes the scenario being tested\n"
            "- Preconditions: exact system/user state before test execution\n"
            "- Steps: numbered, one action per step with its own expected result\n"
            "- Expected result: single, measurable, observable outcome per step"
        )

    # Step 2: rewrite each case that needs improvement
    for case in cases:
        case_id       = case.get("id")
        quality_score = case.get("quality_score", 0)
        title_preview = (case.get("title") or "")[:60]

        if quality_score >= 7:
            logger.info(f"Skipping case {case_id} (score {quality_score}/10 - meets threshold)")
            continue
        if case.get("duplicate_of"):
            logger.info(f"Skipping case {case_id} - marked as duplicate of {case.get('duplicate_of')}")
            continue

        logger.info(f"🤖 Rewriting case {case_id} (score {quality_score}/10): {title_preview}...")

        # Step 3: call LLM
        improved_case = None
        try:
            prompt       = _build_prompt(case, rag_context)
            raw_response = chain.invoke({"testcase": prompt})
            logger.debug(f"Raw LLM response for case {case_id}: {raw_response[:400]}")

            if not raw_response or not raw_response.strip():
                raise ValueError("LLM returned an empty response")

            parsed = json.loads(_clean_json_response(raw_response))
            steps  = _normalise_steps(parsed.get("steps"))

            improved_case = {
                "title":           parsed.get("title",           "").strip(),
                "preconditions":   parsed.get("preconditions",   "").strip(),
                "steps":           steps,
                "expected_result": parsed.get("expected_result", "").strip(),
            }
            logger.debug(
                f"Case {case_id} parsed steps: "
                + str([{"action": s["action"][:40], "expected": s["expected"][:40]}
                        for s in steps])
            )

        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse failed for case {case_id}: {e} - using fallback")
            improved_case = _fallback_improved_case(case)
        except Exception as e:
            logger.warning(f"LLM rewrite failed for case {case_id}: {e} - using fallback")
            improved_case = _fallback_improved_case(case)

        # Step 4: fill any empty fields
        if not improved_case["steps"]:
            improved_case["steps"] = _normalise_steps(case.get("steps")) or [
                {"action": "Navigate to the relevant page.", "expected": "Page loads successfully."},
                {"action": "Perform the required action.",   "expected": "System responds as expected."},
                {"action": "Observe the result.",            "expected": "Result matches the expected outcome."},
            ]
        if not improved_case["expected_result"]:
            improved_case["expected_result"] = (
                case.get("expected_result") or "The application responds as expected for this scenario."
            )
        if not improved_case["preconditions"]:
            improved_case["preconditions"] = (
                case.get("preconditions") or
                "User is authenticated and the application is in the correct initial state."
            )
        if not improved_case["title"]:
            improved_case["title"] = case.get("title") or "Rewritten test case"

        # Step 5: ensure every step has a non-empty expected value
        improved_case["steps"] = _fill_missing_step_expected(
            improved_case["steps"], improved_case["expected_result"]
        )

        # Step 6: score the rewritten case (scorer expects plain strings)
        scoreable = {**improved_case, "steps": [s["action"] for s in improved_case["steps"]]}
        predicted_score, _ = score_test_case(scoreable, rag_context)
        logger.info(f"Case {case_id}: original={quality_score}/10 -> predicted={predicted_score}/10")

        improved.append({
            "case_id":                  case_id,
            "original_score":           quality_score,
            "improved_title":           improved_case["title"],
            "improved_preconditions":   improved_case["preconditions"],
            "improved_steps":           improved_case["steps"],   # list[{"action":..,"expected":..}]
            "improved_expected_result": improved_case["expected_result"],
            "predicted_score":          predicted_score,
            "issues":                   case.get("issues", []),
            "source_case":              case,
        })

    logger.info(f"✅ Improvement suggester produced {len(improved)} rewritten test case(s)")
    return {
        "improved_cases":  improved,
        "steps_completed": state.get("steps_completed", []) + ["improvement_suggester"],
    }