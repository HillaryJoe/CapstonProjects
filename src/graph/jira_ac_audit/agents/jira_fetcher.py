"""Jira Fetcher for AC audit pipeline."""
import os
from src.core import get_logger
from src.integrations import JiraClient

logger = get_logger("ac_audit_jira_fetcher")
client = JiraClient()


def jira_fetcher_agent(state):
    logger.info("🔍 AC Audit: Jira Fetcher running...")

    jira_key = state.get("jira_key")

    try:
        if jira_key and jira_key.strip().lower() not in ["all", "*"]:
            story = client.fetch_issue(jira_key)
            stories = [story]
            logger.info(f"✅ Fetched issue {jira_key}")
        else:
            raw_keys = os.getenv("JIRA_STORY_KEYS", "")
            normalized = raw_keys.strip().strip('"').strip("'")
            env_keys = [k.strip() for k in normalized.split(",") if k.strip()]

            logger.info(f"🔧 JIRA_STORY_KEYS resolved: {env_keys}")

            if env_keys:
                stories = [client.fetch_issue(k) for k in env_keys]
                logger.info(f"✅ Fetched {len(stories)} stories from JIRA_STORY_KEYS")
            else:
                stories = client.search_stories(jql="issuetype = Story", max_results=200)
                logger.info(f"✅ Fetched {len(stories)} stories (issuetype=Story)")
                
# return stories and steps_completed to state
        return {
            "stories": stories,
            "steps_completed": state["steps_completed"] + ["jira_fetcher"]
        }

    except Exception as e:
        logger.error(f"❌ AC Audit Jira Fetcher failed: {e}")
        return {
            "stories": [],
            "steps_completed": state["steps_completed"] + ["jira_fetcher"],
            "errors": state["errors"] + [f"jira_fetcher: {e}"]
        }
