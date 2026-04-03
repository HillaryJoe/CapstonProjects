"""Generate actionable Given/When/Then AC suggestions for gaps."""
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.core import get_logger, get_langchain_llm, search_vector_store
from src.prompts.ac_audit_prompts import IMPROVEMENT_SYSTEM_PROMPT

logger = get_logger("ac_audit_improvement_suggester")
llm = get_langchain_llm()
prompt_template = ChatPromptTemplate.from_messages([
    ("system", IMPROVEMENT_SYSTEM_PROMPT),
    ("user", "{requirement}")
])
parser = StrOutputParser()
chain = prompt_template | llm | parser 

def improvement_suggester_agent(state):
    logger.info("💡 AC Audit: Improvement Suggester running...")

    gap_analysis = state.get("gap_analysis", [])
    print(f"These are the stories with identified gaps: {gap_analysis}")
    suggestions = []

    for story in gap_analysis:
        if not story.get("meaningful_gap"):
            suggestions.append({
                "key": story["key"],
                "proposed_ac": [],
                "note": "No action needed (score 9-10 or not meaningful gap)"
            })
            continue

        missing_categories = story.get("meaningful_gap_categories", story.get("categories_missing", []))

        # RAG context for suggestions
        rag_parts = []
        rag_items = search_vector_store(f"AC writing standards for: {story['summary']}", top_k=2)
        for doc, score in rag_items:
            rag_parts.append(doc.page_content)

        prompt = (
            f"Generate specific acceptance criteria suggestions for each missing category in the story below. "
            f"For each missing category, provide 1-2 concrete Given/When/Then examples that address that specific gap.\n"
            f"Story: {story['key']} - {story['summary']}\n"
            f"Missing categories: {', '.join(missing_categories) if missing_categories else 'none'}\n"
            f"Existing criteria: {story.get('acceptance_criteria', [])}\n"
            f"RAG guidance:\n{chr(10).join(rag_parts)}\n"
            "Respond ONLY with a JSON array of the generated criteria strings."
        )

        suggestions_raw = []
        try:
            response = chain.invoke({"requirement": prompt})
            logger.debug(f"LLM raw response for {story['key']}: {response[:200] if response else 'EMPTY'}")
            
            if not response or not response.strip():
                logger.warning(f"LLM returned empty response for {story['key']}")
                raise ValueError("LLM returned empty response")
            
            response_clean = response.strip()
            if response_clean.startswith("```"):
                response_clean = response_clean.split("```")[1]
                if response_clean.startswith("json"):
                    response_clean = response_clean[4:]
                response_clean = response_clean.strip()
            
            suggestions_raw = json.loads(response_clean)
            if not isinstance(suggestions_raw, list):
                raise ValueError(f"Expected list output, got {type(suggestions_raw)}")
            
            logger.debug(f"Parsed {len(suggestions_raw)} ACs for {story['key']}")

        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse failed for {story['key']}: {e} | Response: {response_clean[:100] if response_clean else 'EMPTY'}")
            suggestions_raw = []
        except Exception as e:
            logger.warning(f"LLM improvement suggestion failed for {story['key']}: {e}")
            suggestions_raw = []
        
        if not suggestions_raw:
            for category in missing_categories:
                suggestions_raw.append(
                    f"Given {story['summary']}, when {category} scenario happens, then verify expected behavior is correct."
                )

        safelist = [s.strip() for s in suggestions_raw if isinstance(s, str) and s.strip()]

        suggestions.append({
            "key": story['key'],
            "proposed_ac": safelist[:10],  # Allow up to 10 suggestions
            "note": "Generated AC suggestions"
        })

    logger.info(f"✅ Generated improvement suggestions for {len(suggestions)} stories")

    return {
        "suggested_ac": suggestions,
        "steps_completed": state.get('steps_completed', []) + ['improvement_suggester']
    }
