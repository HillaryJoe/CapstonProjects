import json
import hashlib
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.core import get_logger, get_langchain_llm, search_vector_store
from src.core.test_case_history import get_case_history, set_case_history
from src.prompts.test_case_quality_prompts import TEST_CASE_SCORE_SYSTEM_PROMPT

logger = get_logger("tc_quality_completeness_checker")
llm = get_langchain_llm()
prompt_template = ChatPromptTemplate.from_messages([
    ("system", TEST_CASE_SCORE_SYSTEM_PROMPT),
    ("user", "{testcases}")
])
parser = StrOutputParser()
chain = prompt_template | llm | parser


def _hash_case(case: dict) -> str:
    payload = "\n".join([
        str(case.get("title", "")),
        str(case.get("preconditions", "")),
        "\n".join(case.get("steps", [])),
        str(case.get("expected_result", ""))
    ])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _format_case(case: dict) -> str:
    steps_text = "\n".join([f"{idx-+1}. {step}" for idx, step in enumerate(case.get("steps", []))])
    print(f"Formatted test case {steps_text} ")

    return (
        f"Title: {case.get('title', '')}\n"
        f"Preconditions: {case.get('preconditions', '') or 'None'}\n"
        f"Steps:\n{steps_text or 'None'}\n"
        f"Expected Result: {case.get('expected_result', '') or 'None'}"
    )


def _score_test_case(case: dict, rag_context: str):
    requirement_prompt = f"""Review the following TestRail test case against the quality guidelines below.

**Quality Guidelines:**
{rag_context}

---

**Test Case:**
{_format_case(case)}

---

Return ONLY a JSON object with keys:
{{{{
  "quality_score": <integer 0-10>,
  "issues": [<list of specific issue strings>]
}}}}
"""
    try:
        response = chain.invoke({"testcases": requirement_prompt})
        result = json.loads(response)
        score = int(result.get("quality_score", 0))
        issues = result.get("issues", []) if isinstance(result.get("issues"), list) else []
        logger.info(f"✓ Scored Case {case.get('id')}: {score}/10")
        return score, issues
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse failed for case {case.get('id')}: {e}")
        return _fallback_scoring(case)
    except Exception as e:
        logger.warning(f"LLM scoring failed for case {case.get('id')}: {e}")
        return _fallback_scoring(case)


def _fallback_scoring(case: dict):
    issues = []
    score = 7
    title = (case.get("title") or "").strip()
    preconditions = (case.get("preconditions") or "").strip()
    steps = case.get("steps", [])
    expected = (case.get("expected_result") or "").strip()

    if not title or len(title) < 20:
        issues.append("Title is vague or too short")
        score -= 2
    if not preconditions:
        issues.append("Missing preconditions")
        score -= 2
    if len(steps) < 2:
        issues.append("Too few test steps")
        score -= 2
    else:
        vague_steps = [s for s in steps if any(word in s.lower() for word in ["verify", "check", "ensure", "validate"]) and len(s) < 40]
        if vague_steps:
            issues.append("Some steps are vague or not specific")
            score -= 1
    if not expected:
        issues.append("Expected result is missing or unclear")
        score -= 2
    if score < 0:
        score = 0
    return score, issues


def score_test_case(case: dict, rag_context: str):
    return _score_test_case(case, rag_context)


def completeness_checker_agent(state):
    logger.info("🧾 Test Case Quality Reviewer: completeness checker running...")
    cases = state.get("testrail_cases", [])
    scored = []

    if not cases:
        logger.warning("No TestRail cases found to score")
        return {
            "scored_cases": [],
            "steps_completed": state.get("steps_completed", []) + ["completeness_checker"]
        }

    try:
        results = search_vector_store(
            "Test case quality scoring rubric and improvement guidelines", top_k=3
        )
        context_parts = []
        for doc, _ in results:
            source = doc.metadata.get("source", "unknown")
            context_parts.append(f"**[{source}]**\n{doc.page_content}")
        rag_context = "\n\n---\n\n".join(context_parts).strip()
        if not rag_context:
            rag_context = "Quality guidelines for test case writing, including clear titles, explicit preconditions, specific steps, and measurable expected results."
    except Exception as e:
        logger.warning(f"RAG search failed: {e}")
        rag_context = "Quality guidelines for test case writing, including clear titles, explicit preconditions, specific steps, and measurable expected results."

    for case in cases:
        case_id = str(case.get("id", "unknown"))
        current_hash = _hash_case(case)
        history = get_case_history(case_id)

        if history and history.get("content_hash") == current_hash:
            logger.info(f"ℹ️ Cached score used for case {case_id}")
            scored.append({
                **case,
                "quality_score": history.get("score", 0),
                "issues": history.get("issues", []),
                "skipped": True
            })
            continue

        score, issues = _score_test_case(case, rag_context)
        scored_case = {
            **case,
            "quality_score": score,
            "issues": issues,
            "skipped": False
        }
        scored.append(scored_case)
        set_case_history(case_id, current_hash, score, issues)

    logger.info(f"✅ Scored {len(scored)} test cases")
    return {
        "scored_cases": scored,
        "steps_completed": state.get("steps_completed", []) + ["completeness_checker"]
    }
