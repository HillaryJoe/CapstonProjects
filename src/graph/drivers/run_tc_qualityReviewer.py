"""Driver for Test Case Quality Reviewer agent pipeline."""
import sys
from pathlib import Path
from src.graph.jira_tc_qualityReviewer.graph import build_graph
from src.core import get_logger

logger = get_logger("test_case_quality_reviewer_driver")

ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "outputs" / "test_case_quality_review"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    """Main entry point for the Test Case Quality Reviewer pipeline."""
    
    logger.info("🚀 Starting Test Case Quality Reviewer pipeline")

    app = build_graph()

    init_state = {
        "next_agent": "",
        "testrail_cases": None,
        "scored_cases": None,
        "duplicate_pairs": None,
        "duplicate_case_ids": None,
        "improved_cases": None,
        "updated_cases": None,
        "slack_message_ts": None,
        "summary_report": "",
        "steps_completed": [],
        "errors": []
    }

    logger.info("=" * 70)
    logger.info("Executing Test Case Quality Review Workflow")
    logger.info("=" * 70)
    
    final_state = app.invoke(init_state)
    
    logger.info("=" * 70)

    if final_state.get("errors"):
        logger.error(f"⚠️ Completed with errors: {final_state['errors']}")
    else:
        logger.info("✅ Pipeline completed successfully!")

    logger.info(f"📊 Agents executed: {', '.join(final_state['steps_completed'])}")

    # Statistics from the review
    if final_state.get("scored_cases"):
        logger.info(f"📈 Total test cases reviewed: {len(final_state['scored_cases'])}")
    
    if final_state.get("improved_cases"):
        logger.info(f"✨ Test cases improved: {len(final_state['improved_cases'])}")
    
    if final_state.get("duplicate_pairs"):
        logger.info(f"🔄 Duplicate pairs found: {len(final_state['duplicate_pairs'])}")

    # Save the summary report
    report_file = OUT_DIR / "test_case_quality_review_report.txt"
    report_file.write_text(final_state["summary_report"], encoding="utf-8")
    logger.info(f"📄 Report saved: {report_file.relative_to(ROOT)}")

    # Print the summary to console
    if final_state["summary_report"]:
        print("\n" + "=" * 70)
        print(final_state["summary_report"])
        print("=" * 70)


if __name__ == "__main__":
    main()
