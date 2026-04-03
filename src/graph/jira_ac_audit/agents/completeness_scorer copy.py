"""Score AC completeness with RAG and memory check."""
import json
import hashlib
from src.core import get_logger, get_langchain_llm, search_vector_store
from src.core.audit_memory import get_story_history, set_story_history
from src.prompts.ac_audit_prompts import SCORE_SYSTEM_PROMPT

logger = get_logger("ac_audit_completeness_scorer")


# Module-level initialization — same pattern as testcase_memory
llm = get_langchain_llm()
prompt_template = ChatPromptTemplate.from_messages([
    ("system", SCORE_SYSTEM_PROMPT),
    ("user", "Requirements:\n\n{requirement}")
])
parser = StrOutputParser()
chain = prompt_template | llm | parser


def _hash_criteria(ac_list):
    text = "\n".join(ac_list)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _check_category(text, keywords):
    t = text.lower()
    return any(k in t for k in keywords)


def _score_and_category(ac_list, story_summary, rag_context):
    categories = {
        "happy_path": False,
        "error": False,
        "boundary": False,
        "ui_feedback": False,
        "security": False,
        "persistence": False
    }

    joined = "\n".join(ac_list)

    categories["happy_path"] = _check_category(joined, ["happy path", "success", "successful", "completed"])
    categories["error"] = _check_category(joined, ["error", "invalid", "fail", "exception", "invalid input"])
    categories["boundary"] = _check_category(joined, ["boundary", "edge", "minimum", "maximum", "limit"])
    categories["ui_feedback"] = _check_category(joined, ["message", "alert", "notification", "toast", "error message"])
    categories["security"] = _check_category(joined, ["auth", "permission", "security", "xss", "csrf", "access denied"])
    categories["persistence"] = _check_category(joined, ["save", "stored", "database", "persist", "load"])

    score = 0
    score += min(len(ac_list), 4)
    score += sum(1 for v in categories.values() if v)
    score = min(score, 10)

    return score, categories


def completeness_scorer_agent(state):
    logger.info("🧾 AC Audit: Completeness Scorer running...")
    parsed_stories = state.get("parsed_stories", [])

    scored = []

    if not parsed_stories:
        logger.warning("No parsed stories found")
        return {
            "scored_stories": [],
            "steps_completed": state["steps_completed"] + ["completeness_scorer"]
        }
    
   # formated_stories = []
    for story in parsed_stories:
        key = story.get("key")
        summary = story.get("summary", "")
        ac_list = story.get("acceptance_criteria", [])
        current_hash = _hash_criteria(ac_list)
        formated_stories.append({key: key, "summary": summary, "ac_list": current_hash})

        history = get_story_history(key)
        print(f"jira stories details:{key, summary, current_hash}")

        if history and history.get("ac_hash") == current_hash:
            logger.info(f"ℹ️ No AC change for {key}, using previous score")
            scored.append({
                "key": key,
                "summary": summary,
                "acceptance_criteria": ac_list,
                "completeness_score": history.get("score", 0),
                "categories_present": history.get("categories", []),
                "categories_missing": [],
                "skipped": True
            })
            continue

        results = search_vector_store(f"Acceptance criteria completeness scoring rubric and score interpretation for user stories", top_k=3)
        context_parts = []
        for doc, score in results:
            source = doc.metadata.get("source", "unknown")
            context_parts.append(f"[Source: {source}] {doc.page_content}")
        rag_context = "\n---\n".join(context_parts)

        score, category_map = _score_and_category(ac_list, summary, rag_context)

        categories_present = [k for k, v in category_map.items() if v]
        categories_missing = [k for k, v in category_map.items() if not v]
        scored.append({
            "key": key,
            "summary": summary,
            "acceptance_criteria": ac_list,
            "completeness_score": score,
            "categories_present": categories_present,
            "categories_missing": categories_missing,
            "skipped": False
        })

        set_story_history(key, current_hash, score, categories_present)

         user_message = f"""

Acceptance criteria scoring guidelines:
{rag_context}

---



    logger.info(f"✅ Scored {len(scored)} stories")

    return {
        "scored_stories": scored,
        "steps_completed": state["steps_completed"] + ["completeness_scorer"]
    }
