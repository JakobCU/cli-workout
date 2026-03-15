"""Workout library: browsable preset workouts loaded from disk + fork support."""

import copy
import json
import re
from pathlib import Path

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from gitfit.config import (
    console, HAS_ANTHROPIC,
    C_BORDER, C_DONE, C_EXERCISE, C_PROGRESS, C_SUBTITLE, C_TITLE,
    has_api_key, save_config,
)
from gitfit.exercises import _estimate_workout_duration, AVAILABLE_EXERCISES
from gitfit.renderer import display_workout
from gitfit.animation import prompt_enter
from gitfit.meta import create_fork_meta

# ── Inline presets (used by workout manager add-from-presets) ────────
WORKOUT_PRESETS = {
    "Upper Body": {
        "name": "Upper Body",
        "rounds": 3,
        "exercises": [
            {"name": "Push-Ups", "mode": "time", "value": 30},
            {"name": "Plank", "mode": "time", "value": 30},
            {"name": "Superman", "mode": "time", "value": 25},
            {"name": "Bird Dog", "mode": "time", "value": 30},
            {"name": "Push-Ups", "mode": "time", "value": 25},
        ],
    },
    "Lower Body": {
        "name": "Lower Body",
        "rounds": 3,
        "exercises": [
            {"name": "Squats", "mode": "time", "value": 40},
            {"name": "Reverse Lunges", "mode": "time", "value": 35},
            {"name": "Glute Bridge", "mode": "time", "value": 35},
            {"name": "Squats", "mode": "time", "value": 35},
            {"name": "Reverse Lunges", "mode": "time", "value": 30},
        ],
    },
    "Core Blast": {
        "name": "Core Blast",
        "rounds": 3,
        "exercises": [
            {"name": "Plank", "mode": "time", "value": 35},
            {"name": "Side Plank Left", "mode": "time", "value": 25},
            {"name": "Side Plank Right", "mode": "time", "value": 25},
            {"name": "Superman", "mode": "time", "value": 30},
            {"name": "Bird Dog", "mode": "time", "value": 30},
        ],
    },
    "Full Body Easy": {
        "name": "Full Body Easy",
        "rounds": 2,
        "exercises": [
            {"name": "Push-Ups", "mode": "time", "value": 20},
            {"name": "Squats", "mode": "time", "value": 25},
            {"name": "Plank", "mode": "time", "value": 20},
            {"name": "Glute Bridge", "mode": "time", "value": 20},
        ],
    },
    "Full Body Hard": {
        "name": "Full Body Hard",
        "rounds": 4,
        "exercises": [
            {"name": "Push-Ups", "mode": "time", "value": 40},
            {"name": "Squats", "mode": "time", "value": 50},
            {"name": "Plank", "mode": "time", "value": 40},
            {"name": "Reverse Lunges", "mode": "time", "value": 40},
            {"name": "Superman", "mode": "time", "value": 35},
            {"name": "Glute Bridge", "mode": "time", "value": 35},
        ],
    },
    "Quick 10min": {
        "name": "Quick 10min",
        "rounds": 2,
        "exercises": [
            {"name": "Push-Ups", "mode": "time", "value": 25},
            {"name": "Squats", "mode": "time", "value": 30},
            {"name": "Plank", "mode": "time", "value": 20},
        ],
    },
}


# ── Disk-based workout library ──────────────────────────────────────
def _load_library():
    """Load workout library from workouts/*.gitfit files."""
    workouts_dir = Path(__file__).resolve().parent.parent / "workouts"
    library = {}
    if not workouts_dir.is_dir():
        return library
    for f in sorted(workouts_dir.glob("gitfit--*.gitfit")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            slug = f.stem.replace(".workout", "").replace("gitfit--", "gitfit/")
            library[slug] = data
        except (json.JSONDecodeError, OSError):
            pass
    return library


WORKOUT_LIBRARY = _load_library()


def cmd_browse(config, list_only=False, state=None):
    """Browse the workout library."""
    from gitfit.state import load_state
    if state is None:
        state = load_state()
    stars = set(state.get("stars", []))

    library = _load_library()  # reload fresh
    if not library:
        console.print("[dim]No workouts in library. Add .gitfit files to workouts/[/dim]")
        return

    if list_only:
        # --list flag: just dump JSON
        items = []
        for slug, data in library.items():
            items.append({
                "slug": slug,
                "name": data.get("name", slug),
                "rounds": data.get("rounds", 3),
                "exercises": len(data.get("exercises", [])),
            })
        print(json.dumps(items, indent=2))
        return

    console.clear()
    console.print(f"[{C_TITLE}]  Workout Library[/{C_TITLE}]\n")

    slugs = list(library.keys())
    for i, slug in enumerate(slugs, 1):
        data = library[slug]
        dur = _estimate_workout_duration(data, config)
        star = " [bright_yellow]*[/bright_yellow]" if slug in stars else ""
        console.print(
            f"  [{C_PROGRESS}]{i})[/{C_PROGRESS}]  {data.get('name', slug)}  "
            f"[dim]({data.get('rounds', 3)}R, {len(data.get('exercises', []))}ex, ~{dur}min)[/dim]"
            f"{star}"
        )

    console.print(f"\n  [{C_PROGRESS}]0)[/{C_PROGRESS}]  Back")
    choice = input("\n  View details (number) or 0 to go back: ").strip()
    try:
        idx = int(choice)
        if idx == 0:
            return
        if 1 <= idx <= len(slugs):
            _library_detail(config, slugs[idx - 1], library[slugs[idx - 1]])
    except ValueError:
        pass


def _library_detail(config, slug, data):
    """Show details of a library workout and offer to add it."""
    console.clear()
    console.print(f"[{C_TITLE}]  {data.get('name', slug)}[/{C_TITLE}]")
    console.print(f"  [dim]slug: {slug}[/dim]\n")

    if data.get("description"):
        console.print(f"  {data['description']}\n")

    display_workout(data, config)

    confirm = input("\n  Add to your workouts? (y/N): ").strip().lower()
    if confirm == "y":
        workout = copy.deepcopy(data)
        # Remove library metadata
        workout.pop("description", None)
        workout.pop("tags", None)
        workout.pop("difficulty", None)
        workout["_meta"] = create_fork_meta(slug, data.get("name", slug))
        config["workouts"].append(workout)
        save_config(config)
        console.print(f"  [{C_DONE}]Added: {workout['name']}[/{C_DONE}]")
    else:
        console.print("  [dim]Cancelled.[/dim]")
    prompt_enter()


def cmd_fork(config, slug):
    """Fork a library workout into your config (CLI command)."""
    library = _load_library()
    if slug not in library:
        # Try adding fithub/ prefix
        if f"gitfit/{slug}" in library:
            slug = f"gitfit/{slug}"
        else:
            console.print(f"[red]Workout '{slug}' not found in library.[/red]")
            console.print("  Available:")
            for s in sorted(library.keys()):
                console.print(f"    {s}")
            return

    workout = copy.deepcopy(library[slug])
    source_name = workout.get("name", slug)
    workout.pop("description", None)
    workout.pop("tags", None)
    workout.pop("difficulty", None)
    workout["_meta"] = create_fork_meta(slug, source_name)
    config["workouts"].append(workout)
    save_config(config)
    console.print(f"[{C_DONE}]Forked '{workout['name']}' into your workouts.[/{C_DONE}]")


def cmd_fork_ai(config, state, slug, adapt_prompt=None):
    """Fork a library workout and let AI customize it."""
    from gitfit.ai import _require_ai, _build_user_context

    library = _load_library()
    if slug not in library and f"gitfit/{slug}" in library:
        slug = f"gitfit/{slug}"
    if slug not in library:
        console.print(f"[red]Workout '{slug}' not found in library.[/red]")
        return

    client, ok = _require_ai(config)
    if not ok:
        return

    workout = library[slug]
    context = _build_user_context(config, state)

    adapt_label = f' with "{adapt_prompt}"' if adapt_prompt else " for your level"
    console.print(f"\n  Customizing [{C_EXERCISE}]{workout['name']}[/{C_EXERCISE}]{adapt_label}...\n")

    adapt_instruction = ""
    if adapt_prompt:
        adapt_instruction = f"\nUser's adaptation request: {adapt_prompt}\n"

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=(
                "Customize this workout for the user's level. Output ONLY valid JSON.\n"
                "Keep the same structure but adjust values (duration/reps) based on their level.\n"
                + adapt_instruction +
                "Available animated exercises: " + ", ".join(AVAILABLE_EXERCISES) + "\n"
            ),
            messages=[{
                "role": "user",
                "content": (
                    f"Workout to customize:\n{json.dumps(workout, indent=2)}\n\n"
                    f"User context:\n{context}"
                ),
            }],
        )
    except Exception as e:
        console.print(f"[red]API error: {e}[/red]")
        return

    raw = response.content[0].text.strip()
    try:
        customized = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            try:
                customized = json.loads(match.group())
            except json.JSONDecodeError:
                console.print("[red]Could not parse AI response.[/red]")
                return
        else:
            console.print("[red]Could not parse AI response.[/red]")
            return

    display_workout(customized, config)
    confirm = input("\n  Add this customized workout? (y/N): ").strip().lower()
    if confirm == "y":
        customized["_meta"] = create_fork_meta(
            slug, workout.get("name", slug),
            adapted_with=adapt_prompt or "AI-customized")
        config["workouts"].append(customized)
        save_config(config)
        console.print(f"[{C_DONE}]Added: {customized.get('name', 'Custom')}[/{C_DONE}]")
    else:
        console.print("[dim]Cancelled.[/dim]")
    prompt_enter()
