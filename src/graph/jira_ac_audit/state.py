from typing import TypedDict, List, Optional


class JiraAcAuditState(TypedDict):
    jira_key: Optional[str]                 # "QA-1" — which story to audit
    next_agent: str                         # supervisor uses this to route

    stories: Optional[list]                 # Agent 1 fills this: raw Jira data
    parsed_stories: Optional[list]          # Agent 2 fills this: extracted AC
    scored_stories: Optional[list]          # Agent 3 fills this: scores 0-10
    gap_analysis: Optional[list]            # Agent 4 fills this: what's missing
    suggested_ac: Optional[list]            # Agent 5 fills this: new GWT AC
    slack_message_ts: Optional[str]         # Agent 6 fills this: Slack timestamp

    summary_report: str                     # Supervisor compiles this at end
    steps_completed: List[str]              # tracks which agents have run
    errors: List[str]                       # any errors collected along the way
