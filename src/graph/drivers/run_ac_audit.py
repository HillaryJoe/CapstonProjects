"""Driver for Jira AC audit agent pipeline."""
import sys
from pathlib import Path
from src.graph.jira_ac_audit.graph import build_graph
from src.core import get_logger

logger = get_logger("jira_ac_audit_driver")

ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "outputs" / "jira_ac_audit"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    jira_key = sys.argv[1] if len(sys.argv) > 1 else "all"

    logger.info(f"🚀 Starting Jira AC audit pipeline (jira_key={jira_key})")

    app = build_graph()

    init_state = {
        "jira_key": jira_key,
        "next_agent": "",
        "stories": None,
        "parsed_stories": None,
        "scored_stories": None,
        "gap_analysis": None,
        "suggested_ac": None,
        "slack_message_ts": None,
        "summary_report": "",
        "steps_completed": [],
        "errors": []
    }

    logger.info("=" * 70)
    final_state = app.invoke(init_state)
    logger.info("=" * 70)

    if final_state.get("errors"):
        logger.error(f"⚠️ Completed with errors: {final_state['errors']}")
    else:
        logger.info("✅ Pipeline completed successfully!")

    logger.info(f"📊 Agents executed: {', '.join(final_state['steps_completed'])}")

    report_file = OUT_DIR / f"{jira_key}_ac_audit_report.txt"
    report_file.write_text(final_state["summary_report"], encoding="utf-8")
    logger.info(f"📄 Report saved: {report_file.relative_to(ROOT)}")

    print(final_state["summary_report"])


if __name__ == "__main__":
    main()
