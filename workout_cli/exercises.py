"""Available exercises, muscle groups, and duration estimation.

Derives from the exercise catalog (exercises/*.exercise.json) when available,
falls back to hardcoded defaults for backward compatibility.
"""

from workout_cli.exercise_catalog import (
    EXERCISE_CATALOG, catalog_names, catalog_muscle_groups,
)

# Available exercise names (ones that have ASCII art animations)
# Pulled from catalog if available, otherwise hardcoded fallback
_FALLBACK_EXERCISES = [
    "Push-Ups", "Squats", "Plank", "Reverse Lunges", "Superman",
    "Side Plank Left", "Side Plank Right", "Glute Bridge", "Bird Dog",
]

AVAILABLE_EXERCISES = catalog_names() if EXERCISE_CATALOG else _FALLBACK_EXERCISES

# Muscle groups for each exercise (for analysis / screens)
_FALLBACK_MUSCLE_GROUPS = {
    "Push-Ups":         ["Chest", "Triceps", "Shoulders"],
    "Squats":           ["Quads", "Glutes", "Hamstrings"],
    "Plank":            ["Core", "Shoulders"],
    "Reverse Lunges":   ["Quads", "Glutes", "Hamstrings"],
    "Superman":         ["Lower Back", "Glutes"],
    "Side Plank Left":  ["Obliques", "Core"],
    "Side Plank Right": ["Obliques", "Core"],
    "Glute Bridge":     ["Glutes", "Hamstrings"],
    "Bird Dog":         ["Core", "Lower Back"],
}

MUSCLE_GROUPS = catalog_muscle_groups() if EXERCISE_CATALOG else _FALLBACK_MUSCLE_GROUPS


def _estimate_workout_duration(workout, config):
    """Estimate total duration in minutes including rests."""
    rest_ex = config["settings"].get("rest_between_exercises", 20)
    rest_rd = config["settings"].get("rest_between_rounds", 45)
    ex_total = 0
    for ex in workout["exercises"]:
        if ex.get("mode") == "time":
            ex_total += ex.get("value", 30)
        else:
            ex_total += ex.get("value", 10) * 3
    per_round = ex_total + rest_ex * max(len(workout["exercises"]) - 1, 0)
    total = per_round * workout["rounds"] + rest_rd * max(workout["rounds"] - 1, 0)
    return round(total / 60, 1)
