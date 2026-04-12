"""
Slack Client - Sends messages to Slack via Web API
"""
import os
import httpx
from dotenv import load_dotenv

load_dotenv()
# Default timeout: 10s connect, 30s read — prevents infinite hang on slow Slack mock
DEFAULT_TIMEOUT = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=5.0)

class SlackClient:

    def __init__(self):
        self.base_url = os.getenv("SLACK_BASE_URL", "http://localhost:4003")
        self.token = os.getenv("SLACK_TOKEN")
        self.channel = os.getenv("SLACK_CHANNEL", "qa-reports")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def post_message(self, text: str) -> dict:
        """Send a plain text message to the configured Slack channel."""
        url = f"{self.base_url}/api/chat.postMessage"
        payload = {
            "channel": self.channel,
            "text": text
        }
        response = httpx.post(url, json=payload, headers=self.headers,timeout=DEFAULT_TIMEOUT,)
        response.raise_for_status()
        data = response.json()

        if not data.get("ok"):
            raise Exception(f"Slack API error: {data.get('error')}")

        return data

    def build_summary(self, jira_key: str, jira_summary: str, test_case_count: int, testrail_ids: list) -> str:
        """Format a readable summary message from pipeline results."""
        ids_str = ", ".join(str(i) for i in testrail_ids)
        return (
            f"[QA Agent] Test Cases Generated\n\n"
            f"Jira Story  : {jira_key} — {jira_summary}\n"
            f"Test Cases  : {test_case_count} generated\n"
            f"TestRail    : Case IDs [{ids_str}] pushed to section 1"
        )