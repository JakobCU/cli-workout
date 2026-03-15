"""Workout management: view, add, edit, delete, and AI-pick workouts."""

import copy
import json
import re

from rich.table import Table

from workout_cli.config import (
    console, HAS_ANTHROPIC,
    C_DONE, C_EXERCISE, C_PROGRESS, C_SUBTITLE, C_TITLE,
    load_config, has_api_key, save_config,
)
from workout_cli.state import save_state
from workout_cli.exercises import (
    AVAILABLE_EXERCISES, _estimate_workout_duration,
)
from workout_cli.art import get_evolution_stage
from workout_cli.renderer import display_workout
from workout_cli.animation import prompt_enter
from workout_cli.library import WORKOUT_PRESETS
from workout_cli.meta import get_meta, bump_version


def _workout_submenu(config, state):
    """Workout management submenu."""
    while True:
        config = load_config()  # always fresh
        console.clear()
        console.print(f"[{C_TITLE}]  Workout Manager[/{C_TITLE}]\n")

        # List current workouts
        workouts = config["workouts"]
        if workouts:
            for i, w in enumerate(workouts):
                dur = _estimate_workout_duration(w, config)
                current = " <-- next" if i == state.get("current_workout_index", 0) % len(workouts) else ""
                console.print(
                    f"  [{C_EXERCISE}]{i + 1}.[/{C_EXERCISE}] {w['name']}  "
                    f"[dim]({w['rounds']}R, {len(w['exercises'])}ex, ~{dur}min)[/dim]"
                    f"[{C_DONE}]{current}[/{C_DONE}]")
        else:
            console.print("  [dim]No workouts configured.[/dim]")

        console.print()
        console.print(f"  [{C_PROGRESS}]v)[/{C_PROGRESS}]  View workout details")
        console.print(f"  [{C_PROGRESS}]a)[/{C_PROGRESS}]  Add from presets")
        console.print(f"  [{C_PROGRESS}]c)[/{C_PROGRESS}]  Create custom workout")
        console.print(f"  [{C_PROGRESS}]e)[/{C_PROGRESS}]  Edit a workout")
        console.print(f"  [{C_PROGRESS}]d)[/{C_PROGRESS}]  Delete a workout")
        if HAS_ANTHROPIC and has_api_key(config):
            console.print(f"  [{C_PROGRESS}]ai)[/{C_PROGRESS}] Let AI pick workouts for me")
        console.print(f"  [{C_PROGRESS}]b)[/{C_PROGRESS}]  Back")
        choice = input("\n  Select: ").strip().lower()

        if choice == "v":
            _workout_view(config)
        elif choice == "a":
            _workout_add_preset(config)
        elif choice == "c":
            _workout_create_custom(config)
        elif choice == "e":
            _workout_edit(config)
        elif choice == "d":
            _workout_delete(config, state)
        elif choice == "ai":
            _workout_ai_pick(config, state)
        elif choice == "b":
            break


def _workout_view(config):
    """View details of a specific workout."""
    workouts = config["workouts"]
    if not workouts:
        console.print("  [dim]No workouts.[/dim]")
        prompt_enter()
        return
    console.print()
    idx = input(f"  Which workout? (1-{len(workouts)}): ").strip()
    try:
        i = int(idx) - 1
        if 0 <= i < len(workouts):
            console.print()
            display_workout(workouts[i], config, index=i + 1)
        else:
            console.print("  [red]Invalid number.[/red]")
    except ValueError:
        console.print("  [red]Enter a number.[/red]")
    prompt_enter()


def _workout_add_preset(config):
    """Add a workout from the preset library."""
    console.clear()
    console.print(f"[{C_TITLE}]  Workout Presets[/{C_TITLE}]\n")
    preset_names = list(WORKOUT_PRESETS.keys())
    for i, name in enumerate(preset_names, 1):
        w = WORKOUT_PRESETS[name]
        dur = _estimate_workout_duration(w, config)
        console.print(
            f"  [{C_PROGRESS}]{i})[/{C_PROGRESS}]  {name}  "
            f"[dim]({w['rounds']}R, {len(w['exercises'])}ex, ~{dur}min)[/dim]")
    console.print(f"\n  [{C_PROGRESS}]0)[/{C_PROGRESS}]  Cancel")
    choice = input("\n  Select: ").strip()
    try:
        idx = int(choice)
        if idx == 0:
            return
        if 1 <= idx <= len(preset_names):
            preset = copy.deepcopy(WORKOUT_PRESETS[preset_names[idx - 1]])
            # Avoid duplicate names
            existing_names = [w["name"] for w in config["workouts"]]
            if preset["name"] in existing_names:
                n = 2
                while f"{preset['name']} {n}" in existing_names:
                    n += 1
                preset["name"] = f"{preset['name']} {n}"

            console.print()
            display_workout(preset, config)
            confirm = input("\n  Add this workout? (y/N): ").strip().lower()
            if confirm == "y":
                config["workouts"].append(preset)
                save_config(config)
                console.print(f"  [{C_DONE}]Added: {preset['name']}[/{C_DONE}]")
            else:
                console.print("  [dim]Cancelled.[/dim]")
            prompt_enter()
    except ValueError:
        console.print("  [red]Enter a number.[/red]")
        prompt_enter()


def _workout_create_custom(config):
    """Create a workout from scratch."""
    console.clear()
    console.print(f"[{C_TITLE}]  Create Custom Workout[/{C_TITLE}]\n")

    name = input("  Workout name: ").strip()
    if not name:
        console.print("  [dim]Cancelled.[/dim]")
        return

    rounds_str = input("  Rounds (default 3): ").strip()
    rounds = int(rounds_str) if rounds_str.isdigit() else 3

    console.print(f"\n  Available exercises:")
    for i, ex in enumerate(AVAILABLE_EXERCISES, 1):
        console.print(f"    [{C_PROGRESS}]{i})[/{C_PROGRESS}] {ex}")

    console.print(f"\n  Add exercises by number, comma-separated (e.g. 1,2,3,5):")
    ex_input = input("  > ").strip()
    if not ex_input:
        console.print("  [dim]Cancelled.[/dim]")
        return

    exercises = []
    for part in ex_input.split(","):
        part = part.strip()
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < len(AVAILABLE_EXERCISES):
                ex_name = AVAILABLE_EXERCISES[idx]
                # Ask for duration
                dur = input(f"    {ex_name} -- seconds (default 30): ").strip()
                dur = int(dur) if dur.isdigit() else 30
                exercises.append({"name": ex_name, "mode": "time", "value": dur})

    if not exercises:
        console.print("  [red]No exercises added.[/red]")
        prompt_enter()
        return

    workout = {"name": name, "rounds": rounds, "exercises": exercises}
    console.print()
    display_workout(workout, config)
    confirm = input("\n  Save this workout? (y/N): ").strip().lower()
    if confirm == "y":
        config["workouts"].append(workout)
        save_config(config)
        console.print(f"  [{C_DONE}]Created: {name}[/{C_DONE}]")
    else:
        console.print("  [dim]Cancelled.[/dim]")
    prompt_enter()


def _workout_edit(config):
    """Edit an existing workout (name, rounds, exercises)."""
    workouts = config["workouts"]
    if not workouts:
        console.print("  [dim]No workouts to edit.[/dim]")
        prompt_enter()
        return
    console.print()
    idx = input(f"  Which workout to edit? (1-{len(workouts)}): ").strip()
    try:
        i = int(idx) - 1
        if not (0 <= i < len(workouts)):
            console.print("  [red]Invalid number.[/red]")
            prompt_enter()
            return
    except ValueError:
        console.print("  [red]Enter a number.[/red]")
        prompt_enter()
        return

    workout = workouts[i]
    console.clear()
    display_workout(workout, config, index=i + 1)

    console.print(f"\n  [{C_SUBTITLE}]Press Enter to keep current value.[/{C_SUBTITLE}]\n")

    new_name = input(f"  Name [{workout['name']}]: ").strip()
    if new_name:
        workout["name"] = new_name

    new_rounds = input(f"  Rounds [{workout['rounds']}]: ").strip()
    if new_rounds.isdigit():
        workout["rounds"] = int(new_rounds)

    console.print(f"\n  Edit exercises? (y/N): ", end="")
    if input().strip().lower() == "y":
        console.print(f"\n  Current exercises:")
        for j, ex in enumerate(workout["exercises"], 1):
            unit = "s" if ex["mode"] == "time" else " reps"
            console.print(f"    {j}. {ex['name']} ({ex['value']}{unit})")

        console.print(f"\n  For each exercise, enter new seconds/reps or Enter to keep:")
        for ex in workout["exercises"]:
            unit = "s" if ex["mode"] == "time" else " reps"
            new_val = input(f"    {ex['name']} [{ex['value']}{unit}]: ").strip()
            if new_val.isdigit():
                ex["value"] = int(new_val)

        console.print(f"\n  Add more exercises? (y/N): ", end="")
        if input().strip().lower() == "y":
            console.print(f"\n  Available:")
            for k, name in enumerate(AVAILABLE_EXERCISES, 1):
                console.print(f"    [{C_PROGRESS}]{k})[/{C_PROGRESS}] {name}")
            add_input = input("  Add by number, comma-separated: ").strip()
            for part in add_input.split(","):
                part = part.strip()
                if part.isdigit():
                    eidx = int(part) - 1
                    if 0 <= eidx < len(AVAILABLE_EXERCISES):
                        ex_name = AVAILABLE_EXERCISES[eidx]
                        dur = input(f"    {ex_name} -- seconds (default 30): ").strip()
                        dur = int(dur) if dur.isdigit() else 30
                        workout["exercises"].append(
                            {"name": ex_name, "mode": "time", "value": dur})

    console.print()
    display_workout(workout, config, index=i + 1)
    confirm = input("\n  Save changes? (y/N): ").strip().lower()
    if confirm == "y":
        # Bump version if workout has fork metadata
        meta = get_meta(workout)
        if meta:
            parts = []
            if new_name:
                parts.append(f"name -> {new_name}")
            if new_rounds and new_rounds.isdigit():
                parts.append(f"rounds -> {new_rounds}")
            parts.append("exercises updated")
            bump_version(meta, "; ".join(parts))
        save_config(config)
        console.print(f"  [{C_DONE}]Saved![/{C_DONE}]")
    else:
        console.print("  [dim]Cancelled -- changes discarded.[/dim]")
    prompt_enter()


def _workout_delete(config, state):
    """Delete a workout."""
    workouts = config["workouts"]
    if not workouts:
        console.print("  [dim]No workouts to delete.[/dim]")
        prompt_enter()
        return
    console.print()
    idx = input(f"  Which workout to delete? (1-{len(workouts)}): ").strip()
    try:
        i = int(idx) - 1
        if not (0 <= i < len(workouts)):
            console.print("  [red]Invalid number.[/red]")
            prompt_enter()
            return
    except ValueError:
        console.print("  [red]Enter a number.[/red]")
        prompt_enter()
        return

    name = workouts[i]["name"]
    confirm = input(f"  Delete '{name}'? (y/N): ").strip().lower()
    if confirm == "y":
        workouts.pop(i)
        # Fix rotation index
        if workouts:
            state["current_workout_index"] = state.get("current_workout_index", 0) % len(workouts)
        else:
            state["current_workout_index"] = 0
        save_config(config)
        save_state(state)
        console.print(f"  [{C_DONE}]Deleted: {name}[/{C_DONE}]")
    else:
        console.print("  [dim]Cancelled.[/dim]")
    prompt_enter()


def _workout_ai_pick(config, state):
    """Let AI configure workouts based on user preferences."""
    from workout_cli.ai import _require_ai, _build_user_context

    client, ok = _require_ai(config)
    if not ok:
        return

    console.clear()
    console.print(f"[{C_TITLE}]  AI Workout Setup[/{C_TITLE}]\n")
    console.print("  Tell Blobby what kind of training you want.\n")
    console.print("  Examples:")
    console.print('    "3 balanced full body workouts, 20 min each"')
    console.print('    "push pull legs split, intermediate level"')
    console.print('    "I only have 15 min, bodyweight only, focus on core"')
    console.print('    "beginner friendly, 3x per week"')
    console.print()
    prompt_text = input("  What do you want? ").strip()
    if not prompt_text:
        return

    replace = False
    if config["workouts"]:
        console.print(f"\n  You have {len(config['workouts'])} existing workouts.")
        r = input("  Replace all with AI picks? (y/N, N = add alongside): ").strip().lower()
        replace = r == "y"

    context = _build_user_context(config, state)
    evo = get_evolution_stage(state)
    console.print(f"\n  [{evo['color']}]Blobby is building your program...[/{evo['color']}]\n")

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=3000,
            system=(
                "Generate a workout program as a JSON array of workout objects. "
                "Output ONLY valid JSON, no markdown, no explanation.\n\n"
                "Format: [{\"name\": \"...\", \"rounds\": N, \"exercises\": [\n"
                "  {\"name\": \"...\", \"mode\": \"time\", \"value\": SECONDS}\n"
                "]}, ...]\n\n"
                "Rules:\n"
                "- Generate 2-4 workouts as requested\n"
                "- Use mode 'time' (value = seconds 15-60) or 'reps' (value = 8-20)\n"
                "- 4-6 exercises per workout, 2-4 rounds\n"
                "- Prefer these exercise names (they have animations): "
                "Push-Ups, Squats, Plank, Reverse Lunges, Superman, "
                "Side Plank Left, Side Plank Right, Glute Bridge, Bird Dog\n"
                "- You can use other exercise names too if needed\n"
                "- Scale to user's level and preferences\n"
                "- Give each workout a creative name\n"
            ),
            messages=[{
                "role": "user",
                "content": (
                    f"Request: {prompt_text}\n\n"
                    f"User context:\n{context}"
                ),
            }],
        )
    except Exception as e:
        console.print(f"  [red]API error: {e}[/red]")
        prompt_enter()
        return

    raw = response.content[0].text.strip()

    # Parse -- could be array or wrapped in an object
    program = None
    try:
        program = json.loads(raw)
        if isinstance(program, dict) and "workouts" in program:
            program = program["workouts"]
    except json.JSONDecodeError:
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            try:
                program = json.loads(match.group())
            except json.JSONDecodeError:
                pass

    if not program or not isinstance(program, list):
        console.print(f"  [red]Could not parse AI response.[/red]")
        console.print(f"  [dim]{raw[:300]}...[/dim]")
        prompt_enter()
        return

    # Validate each workout
    valid = []
    for w in program:
        if isinstance(w, dict) and "name" in w and "exercises" in w:
            w.setdefault("rounds", 3)
            valid.append(w)

    if not valid:
        console.print("  [red]No valid workouts in AI response.[/red]")
        prompt_enter()
        return

    # Display all generated workouts
    for w in valid:
        console.print()
        display_workout(w, config)

    console.print(f"\n  [{C_DONE}]{len(valid)} workouts generated.[/{C_DONE}]")
    action = "Replace existing workouts" if replace else "Add to existing workouts"
    confirm = input(f"\n  {action}? (y/N): ").strip().lower()
    if confirm == "y":
        if replace:
            config["workouts"] = valid
            state["current_workout_index"] = 0
            save_state(state)
        else:
            config["workouts"].extend(valid)
        save_config(config)
        console.print(f"  [{C_DONE}]Done! {len(valid)} workouts saved.[/{C_DONE}]")
    else:
        console.print("  [dim]Cancelled.[/dim]")
    prompt_enter()
