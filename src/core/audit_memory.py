"""Audit history store for per-story AC hashes and scores."""
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
HISTORY_FILE = ROOT / "data" / "audit_history.json"


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


def get_story_history(story_key: str):
    history = load_history()
    return history.get(story_key)

# What audit_history.json looks like:
def set_story_history(story_key: str, ac_hash: str, score: int, categories_present: list, categories_missing: list = None):
    history = load_history()
    history[story_key] = {
        "ac_hash": ac_hash,
        "score": score,
        "categories_present": categories_present,
        "categories_missing": categories_missing or [],
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }
    save_history(history)
