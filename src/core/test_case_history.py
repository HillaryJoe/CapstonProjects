"""Persistent review history for TestRail test cases."""
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
HISTORY_FILE = ROOT / "data" / "test_case_quality_history.json"


def load_history():
    if not HISTORY_FILE.exists():
        return {}
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_history(history: dict):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(history, indent=2), encoding="utf-8")


def get_case_history(case_id: str):
    history = load_history()
    return history.get(case_id)


def set_case_history(case_id: str, content_hash: str, score: int, issues: list, updated: bool = False):
    history = load_history()
    history[case_id] = {
        "content_hash": content_hash,
        "score": score,
        "issues": issues,
        "updated": updated,
        "last_reviewed_at": datetime.utcnow().isoformat() + "Z"
    }
    save_history(history)
