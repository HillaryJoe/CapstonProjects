from typing import TypedDict, List, Optional


class JiraAcAuditState(TypedDict):
    jira_key: Optional[str]
    next_agent: str

    stories: Optional[list]                 #list[dict]
    parsed_stories: Optional[list]          #list[dict]
    scored_stories: Optional[list]          #list[dict]
    gap_analysis: Optional[list]
    suggested_ac: Optional[list]
    slack_message_ts: Optional[str]

    summary_report: str
    steps_completed: List[str]
    errors: List[str]
