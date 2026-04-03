"""Score AC completeness with RAG and memory check."""
import json
import hashlib
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.core import get_logger, get_langchain_llm, search_vector_store
from src.core.audit_memory import get_story_history, set_story_history
from src.prompts.ac_audit_prompts import SCORE_SYSTEM_PROMPT

logger = get_logger("ac_audit_completeness_scorer")


# LLM setup for scoring completeness and categorizing scenarios 
llm = get_langchain_llm()
prompt_template = ChatPromptTemplate.from_messages([
    ("system", SCORE_SYSTEM_PROMPT),
    ("user", "{requirement}")
])
parser = StrOutputParser()
chain = prompt_template | llm | parser      # This build an AI pipeline

#This creates a unique fingerprint of your ACs:
def _hash_criteria(ac_list):
    text = "\n".join(ac_list)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _score_and_category(key, ac_list, story_summary, rag_context):
    #This is the main scoring function. 
    """Use LLM to score AC completeness and identify scenario categories.
    
    Args:
        key: Story key for logging
        ac_list: List of acceptance criteria
        story_summary: Story summary/description
        rag_context: Context from RAG vector store
    
    Returns:
        tuple: (score, categories_present_list, categories_missing_list)
    """

    acceptance_criteria_text = "\n".join([f"- {ac}" for ac in ac_list])

#Step 1 — Builds a detailed prompt:    
    requirement_prompt = f"""Review the following acceptance criteria for completeness using the scoring guidelines provided.

**Completeness Guidelines:**
{rag_context}

---

**Story Details:**
Story Key: {key}
Summary: {story_summary}

Acceptance Criteria:
{acceptance_criteria_text}

---

**Scoring Instructions:**
1. Score the acceptance criteria on a scale of 0-10 based on completeness
2. Identify which scenario categories are explicitly covered
3. Identify which scenario categories are missing

**Scenario Categories to Evaluate:**
- happy_path: Successful/normal flow scenarios
- error: Error handling and exception scenarios
- boundary: Boundary and edge case scenarios
- ui_feedback: User feedback (messages, notifications, alerts)
- security: Security, authentication, and authorization concerns
- persistence: Data persistence and storage concerns

Return ONLY a valid JSON object (no markdown, no extra text):
{{
  "completeness_score": <integer 0-10>,
  "categories_present": [<list of category names found>],
  "categories_missing": [<list of category names not found>]
}}"""

#Step 2 — Calls the AI:    
    try:
        # Call the LLM chain
        response = chain.invoke({"Acceptance_criteria": requirement_prompt})

#Step 3 — Parses the JSON response:       
        
        result = json.loads(response)
        
        score = result.get("completeness_score", 0)
        categories_present = result.get("categories_present", [])
        categories_missing = result.get("categories_missing", [])
        
        logger.info(f"✓ {key}: Score={score}, Present={categories_present}")
        
#Step 4 — Returns results:        
        return score, categories_present, categories_missing
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response for {key}: {e}\nResponse: {response}")
        # Fallback to basic keyword matching
        return _fallback_scoring(ac_list, story_summary)
    except Exception as e:
        logger.error(f"Error scoring {key}: {e}")
        return _fallback_scoring(ac_list, story_summary)

#
def _fallback_scoring(ac_list, story_summary):
    """Fallback scoring using keyword matching when LLM fails."""
    joined = "\n".join(ac_list).lower()
    summary_lower = story_summary.lower()
    full_text = joined + " " + summary_lower
    
    categories_present = []
    categories_missing = ["happy_path", "error", "boundary", "ui_feedback", "security", "persistence"]
    
    if any(k in full_text for k in ["happy path", "success", "successful", "completes", "allows"]):
        categories_present.append("happy_path")
        categories_missing.remove("happy_path")
    
    if any(k in full_text for k in ["error", "invalid", "fail", "exception", "incorrect"]):
        categories_present.append("error")
        categories_missing.remove("error")
    
    if any(k in full_text for k in ["boundary", "edge", "minimum", "maximum", "limit"]):
        categories_present.append("boundary")
        categories_missing.remove("boundary")
    
    if any(k in full_text for k in ["message", "alert", "notification", "toast", "feedback", "display"]):
        categories_present.append("ui_feedback")
        categories_missing.remove("ui_feedback")
    
    if any(k in full_text for k in ["auth", "permission", "security", "access", "role"]):
        categories_present.append("security")
        categories_missing.remove("security")
    
    if any(k in full_text for k in ["save", "stored", "database", "persist", "load"]):
        categories_present.append("persistence")
        categories_missing.remove("persistence")
    
    score = min(len(ac_list) * 1.5 + len(categories_present) * 0.5, 10)
    
    return int(score), categories_present, categories_missing


def completeness_scorer_agent(state):
    """Score acceptance criteria completeness using LLM and RAG context.
    
    For each story's AC list:
    1. Query RAG for completeness rubric
    2. Ask LLM to score ACs out of 10
    3. Identify which scenario categories are present vs missing
    
    Args:
        state: Graph state containing parsed_stories
        
    Returns:
        Updated state with scored_stories list
    """
    logger.info("🧾 AC Audit: Completeness Scorer running...")
    parsed_stories = state.get("parsed_stories", [])

    scored = []

    if not parsed_stories:
        logger.warning("No parsed stories found")
        return {
            "scored_stories": [],
            "steps_completed": state.get("steps_completed", []) + ["completeness_scorer"]
        }
    
    # Query RAG once for rubric (used for all stories)
    logger.info("📚 Fetching acceptance criteria completeness guidelines from RAG...")
    try:
        results = search_vector_store(
            "Acceptance criteria completeness scoring rubric and scenario categories for user stories", 
            top_k=3
        )
        context_parts = []
        for doc, score in results:
            source = doc.metadata.get("source", "unknown")
            content = doc.page_content
            context_parts.append(f"**[{source}]**\n{content}")
        
        rag_context = "\n\n---\n\n".join(context_parts)
        if not rag_context.strip():
            logger.warning("⚠️ No RAG context found, using LLM knowledge")
            rag_context = "Standard QA completeness framework including happy path, error handling, boundary conditions, UI feedback, security, and persistence."
    except Exception as e:
        logger.warning(f"⚠️ RAG search failed: {e}, using default context")
        rag_context = "Standard QA completeness framework including happy path, error handling, boundary conditions, UI feedback, security, and persistence."

    # Score each story
    for story in parsed_stories:
        key = story.get("key")
        summary = story.get("summary", "")
        ac_list = story.get("acceptance_criteria", [])
        
        if not ac_list:
            logger.warning(f"⚠️ Story {key} has no acceptance criteria")
            scored.append({
                "key": key,
                "summary": summary,
                "acceptance_criteria": ac_list,
                "completeness_score": 0,
                "categories_present": [],
                "categories_missing": ["happy_path", "error", "boundary", "ui_feedback", "security", "persistence"],
                "skipped": True,
                "reason": "No acceptance criteria provided"
            })
            continue

        # Check memory to avoid re-scoring unchanged ACs
        current_hash = _hash_criteria(ac_list)
        history = get_story_history(key)
        
        if history and history.get("ac_hash") == current_hash:
            logger.info(f"ℹ️ No AC change for {key}, using previous score")
            scored.append({
                "key": key,
                "summary": summary,
                "acceptance_criteria": ac_list,
                "completeness_score": history.get("score", 0),
                "categories_present": history.get("categories_present", []),
                "categories_missing": history.get("categories_missing", []),
                "skipped": True,
                "reason": "Using cached result"
            })
            continue

        # Use LLM to score and categorize
        logger.info(f"🤖 Scoring {key}: {summary[:50]}...")
        score, categories_present, categories_missing = _score_and_category(
            key, ac_list, summary, rag_context
        )

        scored.append({
            "key": key,
            "summary": summary,
            "acceptance_criteria": ac_list,
            "completeness_score": score,
            "categories_present": categories_present,
            "categories_missing": categories_missing,
            "skipped": False
        })

        # Save to memory for future reference
        set_story_history(key, current_hash, score, categories_present, categories_missing)

    logger.info(f"✅ Scored {len(scored)} stories")
    print(f"Scoring results: {scored}")
    return {
        "scored_stories": scored,
        "steps_completed": state.get("steps_completed", []) + ["completeness_scorer"]
    }
