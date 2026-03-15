"""State management: default state, load, and save."""

from workout_cli.config import STATE_FILE, ensure_files, _load_json, _save_json


def _default_state():
    return {
        "current_workout_index": 0,
        "history": [],
        "exercise_progress": {},
        "completed_sessions": 0,
        "current_streak": 0,
        "longest_streak": 0,
        "last_workout_date": None,
        "xp": 0,
        "level": 1,
        "level_title": "Couch Potato",
        "achievements": [],
    }


def load_state():
    ensure_files()
    return _load_json(STATE_FILE, _default_state())


def save_state(state):
    _save_json(STATE_FILE, state)
