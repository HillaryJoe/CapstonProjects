from typing import TypedDict, List, Optional


class JiraTCQualityState(TypedDict):
    next_agent: str

    testrail_cases: Optional[list]
    scored_cases: Optional[list]
    duplicate_pairs: Optional[list]
    duplicate_case_ids: Optional[list]
    improved_cases: Optional[list]
    updated_cases: Optional[list]
    slack_message_ts: Optional[str]

    summary_report: str
    steps_completed: List[str]
    errors: List[str]
