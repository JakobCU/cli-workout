"""openWorkout format: export/import workouts in a portable JSON schema."""

import json
from pathlib import Path

from gitfit.config import console, C_DONE, C_EXERCISE, C_PROGRESS, save_config
from gitfit.exercises import AVAILABLE_EXERCISES
from gitfit.animation import prompt_enter

OPENWORKOUT_DIFFICULTIES = ["easy", "medium", "hard", "extreme"]


def workout_to_openworkout(workout):
    """Convert an internal workout dict to openWorkout format."""
    exercises = []
    for ex in workout.get("exercises", []):
        ow_ex = {
            "name": ex["name"],
            "mode": ex.get("mode", "time"),
            "value": ex.get("value", 30),
        }
        exercises.append(ow_ex)

    return {
        "format": "openWorkout",
        "version": 1,
        "name": workout.get("name", "Unnamed"),
        "rounds": workout.get("rounds", 3),
        "exercises": exercises,
        "metadata": {
            "source": "fithub",
            "animated_exercises": AVAILABLE_EXERCISES,
        },
    }


def openworkout_to_workout(ow_data):
    """Convert openWorkout format to internal workout dict."""
    return {
        "name": ow_data.get("name", "Imported Workout"),
        "rounds": ow_data.get("rounds", 3),
        "exercises": [
            {
                "name": ex.get("name", "Push-Ups"),
                "mode": ex.get("mode", "time"),
                "value": ex.get("value", 30),
            }
            for ex in ow_data.get("exercises", [])
        ],
    }


def validate_openworkout(data):
    """Validate openWorkout format. Returns (is_valid, errors)."""
    errors = []
    if not isinstance(data, dict):
        return False, ["Data must be a JSON object"]
    if data.get("format") != "openWorkout":
        errors.append("Missing or wrong 'format' field (expected 'openWorkout')")
    if "name" not in data:
        errors.append("Missing 'name' field")
    if "exercises" not in data or not isinstance(data.get("exercises"), list):
        errors.append("Missing or invalid 'exercises' array")
    elif len(data["exercises"]) == 0:
        errors.append("Workout must have at least one exercise")
    else:
        for i, ex in enumerate(data["exercises"]):
            if "name" not in ex:
                errors.append(f"Exercise {i + 1}: missing 'name'")
            if ex.get("mode") not in ("time", "reps", None):
                errors.append(f"Exercise {i + 1}: invalid mode '{ex.get('mode')}'")
    return len(errors) == 0, errors


def cmd_export_openworkout(config, state, index_str):
    """Export a workout in openWorkout format."""
    workouts = config["workouts"]
    if not workouts:
        console.print("[red]No workouts to export.[/red]")
        return

    try:
        idx = int(index_str) - 1
    except (ValueError, TypeError):
        console.print("[red]Usage: python app.py export-ow <number>[/red]")
        console.print(f"  Workouts: 1-{len(workouts)}")
        for i, w in enumerate(workouts, 1):
            console.print(f"    {i}. {w['name']}")
        return

    if not (0 <= idx < len(workouts)):
        console.print(f"[red]Invalid index. Must be 1-{len(workouts)}.[/red]")
        return

    ow = workout_to_openworkout(workouts[idx])
    print(json.dumps(ow, indent=2, ensure_ascii=False))


def cmd_import_openworkout(config, file_path):
    """Import a workout from an openWorkout JSON file."""
    path = Path(file_path)
    if not path.exists():
        console.print(f"[red]File not found: {file_path}[/red]")
        return

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON: {e}[/red]")
        return

    valid, errors = validate_openworkout(data)
    if not valid:
        console.print("[red]Invalid openWorkout format:[/red]")
        for err in errors:
            console.print(f"  - {err}")
        return

    workout = openworkout_to_workout(data)
    console.print(f"\n  [{C_EXERCISE}]{workout['name']}[/{C_EXERCISE}]")
    console.print(f"  Rounds: [{C_PROGRESS}]{workout['rounds']}[/{C_PROGRESS}]")
    for ex in workout["exercises"]:
        unit = f"{ex['value']}s" if ex["mode"] == "time" else f"{ex['value']} reps"
        has_anim = " [animated]" if ex["name"] in AVAILABLE_EXERCISES else ""
        console.print(f"    - {ex['name']}: {unit}{has_anim}")

    confirm = input("\n  Add this workout? (y/N): ").strip().lower()
    if confirm == "y":
        config["workouts"].append(workout)
        save_config(config)
        console.print(f"[{C_DONE}]Imported: {workout['name']}[/{C_DONE}]")
    else:
        console.print("[dim]Cancelled.[/dim]")
