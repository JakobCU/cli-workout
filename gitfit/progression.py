"""Progression logic: XP, levels, streaks, achievements, encouragement."""

import random
from datetime import datetime

# ── Encouragement messages ──────────────────────────────────────────
ENCOURAGEMENT_MESSAGES = [
    "Blobby believes in you!",
    "You're doing amazing!",
    "Keep pushing, champion!",
    "One rep closer to greatness!",
    "Sweat is just fat crying!",
    "Blobby is proud of you!",
    "You showed up. That's half the battle!",
    "Stronger than yesterday!",
    "Pain is temporary, gains are forever!",
    "Beast mode: ACTIVATED!",
    "Your future self will thank you!",
    "Consistency beats perfection!",
    "Every rep counts!",
    "You're building something great!",
    "Blobby didn't skip leg day and neither should you!",
    "The only bad workout is the one that didn't happen!",
    "You vs. you. And you're winning!",
    "Discipline is choosing between what you want now and what you want most!",
]


def get_random_encouragement():
    return random.choice(ENCOURAGEMENT_MESSAGES)


# ── Level thresholds ────────────────────────────────────────────────
LEVEL_THRESHOLDS = [
    (0,    1, "Couch Potato"),
    (50,   2, "Reluctant Mover"),
    (150,  3, "Warming Up"),
    (300,  4, "Blob Warrior"),
    (500,  5, "Sweat Apprentice"),
    (800,  6, "Iron Blobby"),
    (1200, 7, "Beast Mode"),
    (1800, 8, "Legendary Blob"),
    (2500, 9, "Mythic Monster"),
    (3500, 10, "Transcended"),
]

# ── Achievement definitions ─────────────────────────────────────────
ACHIEVEMENTS = [
    {"id": "first_workout", "name": "First Steps",
     "desc": "Complete your first workout",
     "check": lambda s, **kw: s.get("completed_sessions", 0) >= 1},
    {"id": "five_sessions", "name": "High Five",
     "desc": "Complete 5 sessions",
     "check": lambda s, **kw: s.get("completed_sessions", 0) >= 5},
    {"id": "ten_sessions", "name": "Getting Serious",
     "desc": "Complete 10 sessions",
     "check": lambda s, **kw: s.get("completed_sessions", 0) >= 10},
    {"id": "twentyfive_sessions", "name": "Quarter Century",
     "desc": "Complete 25 sessions",
     "check": lambda s, **kw: s.get("completed_sessions", 0) >= 25},
    {"id": "fifty_sessions", "name": "Half Century",
     "desc": "Complete 50 sessions",
     "check": lambda s, **kw: s.get("completed_sessions", 0) >= 50},
    {"id": "hundred_sessions", "name": "Centurion",
     "desc": "Complete 100 sessions",
     "check": lambda s, **kw: s.get("completed_sessions", 0) >= 100},
    {"id": "streak_3", "name": "Hat Trick",
     "desc": "3-day streak",
     "check": lambda s, **kw: s.get("current_streak", 0) >= 3},
    {"id": "streak_7", "name": "Week Warrior",
     "desc": "7-day streak",
     "check": lambda s, **kw: s.get("current_streak", 0) >= 7},
    {"id": "streak_14", "name": "Fortnight Fighter",
     "desc": "14-day streak",
     "check": lambda s, **kw: s.get("current_streak", 0) >= 14},
    {"id": "streak_30", "name": "Monthly Monster",
     "desc": "30-day streak",
     "check": lambda s, **kw: s.get("current_streak", 0) >= 30},
    {"id": "long_session", "name": "Endurance Beast",
     "desc": "Complete a 30+ minute session",
     "check": lambda s, **kw: kw.get("duration", 0) >= 30},
    {"id": "xp_500", "name": "XP Hoarder",
     "desc": "Accumulate 500 XP",
     "check": lambda s, **kw: s.get("xp", 0) >= 500},
    {"id": "xp_2000", "name": "XP Titan",
     "desc": "Accumulate 2000 XP",
     "check": lambda s, **kw: s.get("xp", 0) >= 2000},
    {"id": "level_5", "name": "Sweat Apprentice",
     "desc": "Reach level 5",
     "check": lambda s, **kw: s.get("level", 1) >= 5},
    {"id": "level_10", "name": "Transcendence",
     "desc": "Reach level 10",
     "check": lambda s, **kw: s.get("level", 1) >= 10},
]


# ── Progression functions ────────────────────────────────────────────

def get_progressed_value(ex, state):
    base = int(ex["value"])
    bonus = int(state.get("exercise_progress", {}).get(ex["name"], 0))
    return base + bonus


def maybe_apply_progression(config, state):
    settings = config["settings"]
    every = int(settings.get("progression_every_completed_sessions", 3))
    step = int(settings.get("progression_seconds_step", 5))
    completed = int(state.get("completed_sessions", 0))

    if completed > 0 and completed % every == 0:
        progress_map = state.setdefault("exercise_progress", {})
        seen = set()
        for workout in config["workouts"]:
            for ex in workout["exercises"]:
                if ex["mode"] == "time" and ex["name"] not in seen:
                    progress_map[ex["name"]] = int(progress_map.get(ex["name"], 0)) + step
                    seen.add(ex["name"])
        return True
    return False


def update_streak(state):
    """Update streak based on last workout date. Returns current streak."""
    today = datetime.now().strftime("%Y-%m-%d")
    last = state.get("last_workout_date")

    if last == today:
        return state.get("current_streak", 0)

    if last:
        last_date = datetime.strptime(last, "%Y-%m-%d").date()
        today_date = datetime.now().date()
        delta = (today_date - last_date).days
        if delta == 1:
            state["current_streak"] = state.get("current_streak", 0) + 1
        elif delta > 1:
            state["current_streak"] = 1
    else:
        state["current_streak"] = 1

    state["last_workout_date"] = today
    state["longest_streak"] = max(
        state.get("longest_streak", 0), state.get("current_streak", 0)
    )
    return state["current_streak"]


def calculate_session_xp(duration_min, exercise_count, rounds):
    """Calculate XP earned for a session."""
    return int(10 + duration_min * 2 + exercise_count * rounds * 3)


def update_level(state):
    """Walk level thresholds, update state. Returns True if level changed."""
    xp = state.get("xp", 0)
    old_level = state.get("level", 1)
    new_level = 1
    new_title = "Couch Potato"
    for threshold_xp, level, title in LEVEL_THRESHOLDS:
        if xp >= threshold_xp:
            new_level = level
            new_title = title
    state["level"] = new_level
    state["level_title"] = new_title
    return new_level > old_level


def check_achievements(state, session_duration_min=0):
    """Check all achievements, return list of newly unlocked ones."""
    unlocked_ids = {a["id"] for a in state.get("achievements", [])}
    newly_unlocked = []
    for ach in ACHIEVEMENTS:
        if ach["id"] not in unlocked_ids:
            if ach["check"](state, duration=session_duration_min):
                entry = {
                    "id": ach["id"],
                    "name": ach["name"],
                    "desc": ach["desc"],
                    "unlocked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                state.setdefault("achievements", []).append(entry)
                newly_unlocked.append(entry)
    return newly_unlocked


def summarize_workout(workout, state):
    rounds = workout["rounds"]
    lines = []
    for ex in workout["exercises"]:
        val = get_progressed_value(ex, state)
        unit = "s" if ex["mode"] == "time" else " reps"
        lines.append((ex["name"], f"{val}{unit}"))
    return rounds, lines
