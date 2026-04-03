"""Parse acceptance criteria from story description."""
import re
from src.core import get_logger

logger = get_logger("ac_audit_ac_parser")


def _extract_acceptance_criteria(description: str):
    if not description:
        return []

    lower = description.lower()
    ac_section = description

    match = re.search(r"acceptance criteria[:\n]*(.*)$", description, re.IGNORECASE | re.DOTALL)
    if match:
        ac_section = match.group(1).strip()

    lines = ac_section.splitlines()
    items = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if re.match(r"^(\d+[\.)]|[-*+] )", stripped):
            cleaned = re.sub(r"^(\d+[\.)]|[-*+] )", "", stripped).strip()
            if cleaned:
                items.append(cleaned)
        elif len(stripped.split()) > 5 and len(items) == 0:
            # fallback: crawl first large line(s)
            items.append(stripped)

    if not items and description.strip():
        # no clear list, fallback to full text as one AC item
        items = [description.strip()]

    return items


def ac_parser_agent(state):
    logger.info("🧩 AC Audit: AC Parser running...")

    stories = state.get("stories", [])

    parsed = []
    for story in stories:
        ac_list = _extract_acceptance_criteria(story.get("description_text", ""))
        parsed.append({
            "key": story.get("key", "UNKNOWN"),
            "summary": story.get("summary", ""),
            "acceptance_criteria": ac_list
        })

    logger.info(f"✅ Parsed AC data for {len(parsed)} stories")
    logger.info(f"✅ Parsed AC returned to state {parsed}") 

    return {
        "parsed_stories": parsed,
        "steps_completed": state["steps_completed"] + ["ac_parser"]
    }
