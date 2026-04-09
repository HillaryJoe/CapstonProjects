import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.core import get_logger, get_langchain_llm, search_vector_store
from src.prompts.test_case_quality_prompts import IMPROVE_TEST_CASE_SYSTEM_PROMPT
from src.graph.jira_tc_qualityReviewer.agents.completeness_checker import score_test_case

logger = get_logger("tc_quality_improvement_suggester")
llm = get_langchain_llm()
prompt_template = ChatPromptTemplate.from_messages([
    ("system", IMPROVE_TEST_CASE_SYSTEM_PROMPT),
    ("user", "{requirement}")
])
parser = StrOutputParser()
chain = prompt_template | llm | parser


def _clean_response(response: str) -> str:
    if not response:
        return ""
    text = response.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
    return text.strip()


def _build_case_prompt(case: dict, rag_context: str) -> str:
    steps_text = "\n".join([f"{idx+1}. {step}" for idx, step in enumerate(case.get("steps", []))])
    return (
        f"Rewrite the following TestRail test case to meet high quality standards. "
        f"Use a concise title, clear preconditions, numbered specific steps, and a single explicit expected result. "
        f"Do not change the meaning of the test case.\n\n"
        f"RAG quality guidelines:\n{rag_context}\n\n"
        f"Current test case:\n"
        f"Title: {case.get('title', '')}\n"
        f"Preconditions: {case.get('preconditions', '') or 'None'}\n"
        f"Steps:\n{steps_text or 'None'}\n"
        f"Expected Result: {case.get('expected_result', '') or 'None'}\n\n"
        f"Return ONLY a valid JSON object with keys: title, preconditions, steps, expected_result."
    )


def _fallback_improved_case(case: dict) -> dict:
    title = case.get("title", "").strip()
    if len(title) < 20:
        title = f"{title} - improved for clarity" if title else "Perform action and verify expected outcome"

    preconditions = case.get("preconditions") or "User is on the relevant page and ready to perform the test steps."
    steps = case.get("steps") or ["Execute the required steps for the test scenario."]
    expected = case.get("expected_result") or "The application responds with the expected outcome clearly matching the test scenario."

    return {
        "title": title,
        "preconditions": preconditions,
        "steps": steps,
        "expected_result": expected
    }


def improvement_suggester_agent(state):
    logger.info("🔧 Test Case Quality Reviewer: improvement suggester running...")
    cases = state.get("scored_cases", [])
    improved = []

    try:
        results = search_vector_store(
            "Test case quality improvement and writing guidelines", top_k=3
        )
        context_parts = []
        for doc, _ in results:
            source = doc.metadata.get("source", "unknown")
            context_parts.append(f"**[{source}]**\n{doc.page_content}")
        rag_context = "\n\n---\n\n".join(context_parts).strip()
        if not rag_context:
            rag_context = "Use QA best practices for test case quality, including clear test names, explicit preconditions, step-by-step actions, and unambiguous expected results."
    except Exception as e:
        logger.warning(f"RAG search failed: {e}")
        rag_context = "Use QA best practices for test case quality, including clear test names, explicit preconditions, step-by-step actions, and unambiguous expected results."

    for case in cases:
        if case.get("quality_score", 0) >= 7 or case.get("duplicate_of"):
            continue

        prompt = _build_case_prompt(case, rag_context)
        raw_response = ""
        improved_case = None

        try:
            raw_response = chain.invoke({"requirement": prompt})
            parsed = json.loads(_clean_response(raw_response))
            improved_case = {
                "title": parsed.get("title", "").strip(),
                "preconditions": parsed.get("preconditions", "").strip(),
                "steps": [s.strip() for s in parsed.get("steps", []) if isinstance(s, str) and s.strip()],
                "expected_result": parsed.get("expected_result", "").strip()
            }
        except Exception as e:
            logger.warning(f"Improvement suggestion failed for case {case.get('id')}: {e}")
            improved_case = _fallback_improved_case(case)

        if not improved_case["steps"]:
            improved_case["steps"] = case.get("steps") or ["Execute the required test steps."]
        if not improved_case["expected_result"]:
            improved_case["expected_result"] = case.get("expected_result") or "The behavior matches the intended outcome for this scenario."

        predicted_score, _ = score_test_case(improved_case, rag_context)
        improved.append({
            "case_id": case.get("id"),
            "original_score": case.get("quality_score", 0),
            "improved_title": improved_case["title"],
            "improved_preconditions": improved_case["preconditions"],
            "improved_steps": improved_case["steps"],
            "improved_expected_result": improved_case["expected_result"],
            "predicted_score": predicted_score,
            "issues": case.get("issues", []),
            "source_case": case
        })

    logger.info(f"✅ Improvement suggester produced {len(improved)} rewritten test case(s)")
    return {
        "improved_cases": improved,
        "steps_completed": state.get("steps_completed", []) + ["improvement_suggester"]
    }
