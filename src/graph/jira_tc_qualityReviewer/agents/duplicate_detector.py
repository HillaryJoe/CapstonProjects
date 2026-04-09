import difflib
import re
from src.core import get_logger

logger = get_logger("tc_quality_duplicate_detector")


def _normalize_text(text: str) -> str:
    text = text or ""
    normalized = re.sub(r"[^0-9a-zA-Z]+", " ", text).strip().lower()
    return normalized


def _similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def duplicate_detector_agent(state):
    logger.info("🔎 Test Case Quality Reviewer: duplicate detector running...")
    cases = state.get("scored_cases", [])
    duplicate_pairs = []
    duplicate_ids = set()

    for i, case_a in enumerate(cases):
        for case_b in cases[i + 1:]:
            if case_a.get("id") == case_b.get("id"):
                continue

            title_a = _normalize_text(case_a.get("title", ""))
            title_b = _normalize_text(case_b.get("title", ""))
            steps_a = _normalize_text(" ".join(case_a.get("steps", [])))
            steps_b = _normalize_text(" ".join(case_b.get("steps", [])))

            title_similarity = _similarity(title_a, title_b)
            steps_similarity = _similarity(steps_a, steps_b)

            if title_similarity >= 0.75 or (steps_similarity >= 0.65 and title_similarity >= 0.45):
                primary, duplicate = (case_a, case_b) if case_a.get("quality_score", 0) >= case_b.get("quality_score", 0) else (case_b, case_a)
                if primary.get("quality_score", 0) == duplicate.get("quality_score", 0) and primary.get("id") and duplicate.get("id"):
                    if str(primary.get("id")) > str(duplicate.get("id")):
                        primary, duplicate = duplicate, primary

                duplicate_entry = {
                    "duplicate_case_id": duplicate.get("id"),
                    "original_case_id": primary.get("id"),
                    "title_similarity": round(title_similarity, 2),
                    "steps_similarity": round(steps_similarity, 2),
                    "duplicate_of": primary.get("id"),
                    "duplicate_title": duplicate.get("title"),
                    "original_title": primary.get("title")
                }
                duplicate_pairs.append(duplicate_entry)
                duplicate_ids.add(duplicate.get("id"))
                duplicate["duplicate_of"] = primary.get("id")
                duplicate["is_duplicate"] = True
                duplicate["duplicate_confidence"] = max(title_similarity, steps_similarity)

    logger.info(f"✅ Detected {len(duplicate_pairs)} duplicate pair(s)")
    return {
        "duplicate_pairs": duplicate_pairs,
        "duplicate_case_ids": list(duplicate_ids),
        "scored_cases": cases,
        "steps_completed": state.get("steps_completed", []) + ["duplicate_detector"]
    }
