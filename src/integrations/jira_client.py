"""
Jira Client - Fetches issue data from Jira REST API v3
"""
import os
import httpx
from dotenv import load_dotenv

load_dotenv()


class JiraClient:

    def __init__(self):
        self.base_url = os.getenv("JIRA_BASE_URL", "http://localhost:4001")
        self.token = os.getenv("JIRA_TOKEN")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def fetch_issue(self, issue_key: str) -> dict:
        """Fetch a Jira issue and return a clean dict with plain-text description."""
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}"       #1. build url
        response = httpx.get(url, headers=self.headers)             #2. call jira api
        response.raise_for_status()                                 #3. raise if error    
        data = response.json()                                      #4. parse json and Convert response to Python dictionary

        fields = data.get("fields", {})
        adf_description = fields.get("description", {})

        return {
            "key": data.get("key"),
            "summary": fields.get("summary", ""),
            "description_text": self._extract_text(adf_description),
            "priority": fields.get("priority", {}).get("name", ""),
            "status": fields.get("status", {}).get("name", "")
        }

    def search_stories(self, jql: str = "issuetype = Story", max_results: int = 50) -> list[dict]:
        """Search for Jira stories by JQL and return list of simplified issue dicts."""
        url = f"{self.base_url}/rest/api/3/search"
        params = {
            "jql": jql,
            "fields": "summary,description",
            "maxResults": max_results
        }

        try:
            response = httpx.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()

            stories = []
            for issue in data.get("issues", []):
                fields = issue.get("fields", {})
                description_text = self._extract_text(fields.get("description", {}))
                stories.append({
                    "key": issue.get("key"),
                    "summary": fields.get("summary", ""),
                    "description_text": description_text
                })

            return stories              # list of all stories

# Fallback Handling
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 422:
                # Some test Jira mocks do not support /search; fallback to explicit key list
                keys = os.getenv("JIRA_STORY_KEYS", "")
                if keys:
                    story_keys = [k.strip() for k in keys.split(",") if k.strip()]
                    return [self.fetch_issue(k) for k in story_keys]

            raise

    def _extract_text(self, node: dict) -> str:             #The method recursively walks through this tree to extract plain text
        """Recursively extract plain text from an ADF (Atlassian Document Format) node."""
        if not node or not isinstance(node, dict):          
            return ""

        # Base case: this node is a text leaf
        if node.get("type") == "text":
            return node.get("text", "")

        # Recursive case: walk all children
        parts = []
        for child in node.get("content", []):
            parts.append(self._extract_text(child))

        return "\n".join(part for part in parts if part)