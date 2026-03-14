#!/usr/bin/env python3
"""CLI Workout Tool — adaptive home training with ASCII animations.

Designed for interactive use and for programmatic access by AI agents.

Usage:
    python app.py                  # interactive menu
    python app.py start            # start today's workout
    python app.py history          # show history
    python app.py stats            # show stats
    python app.py config           # show config path & hints
    python app.py status           # JSON dump of current state (agent-friendly)
    python app.py skip             # skip to next workout in rotation
    python app.py reset            # reset all progress (asks confirmation)
"""
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────
APP_DIR = Path.home() / ".workout_cli"
STATE_FILE = APP_DIR / "state.json"
CONFIG_FILE = APP_DIR / "config.json"

# ── Default config ───────────────────────────────────────────────────
DEFAULT_CONFIG = {
    "profile": {
        "name": "User",
        "target_sessions_per_week": 3,
    },
    "settings": {
        "countdown_seconds": 5,
        "rest_between_exercises": 20,
        "rest_between_rounds": 45,
        "progression_every_completed_sessions": 3,
        "progression_seconds_step": 5,
        "enable_clear_screen": True,
    },
    "workouts": [
        {
            "name": "Workout A",
            "rounds": 3,
            "exercises": [
                {"name": "Push-Ups", "mode": "time", "value": 30},
                {"name": "Squats", "mode": "time", "value": 40},
                {"name": "Plank", "mode": "time", "value": 25},
                {"name": "Reverse Lunges", "mode": "time", "value": 35},
                {"name": "Superman", "mode": "time", "value": 25},
            ],
        },
        {
            "name": "Workout B",
            "rounds": 3,
            "exercises": [
                {"name": "Push-Ups", "mode": "time", "value": 30},
                {"name": "Squats", "mode": "time", "value": 45},
                {"name": "Side Plank Left", "mode": "time", "value": 20},
                {"name": "Side Plank Right", "mode": "time", "value": 20},
                {"name": "Glute Bridge", "mode": "time", "value": 35},
            ],
        },
        {
            "name": "Workout C",
            "rounds": 3,
            "exercises": [
                {"name": "Push-Ups", "mode": "time", "value": 35},
                {"name": "Squats", "mode": "time", "value": 45},
                {"name": "Plank", "mode": "time", "value": 30},
                {"name": "Bird Dog", "mode": "time", "value": 35},
                {"name": "Superman", "mode": "time", "value": 25},
            ],
        },
    ],
}

# ── ASCII art frames (2-frame animations) ────────────────────────────
ASCII_FRAMES = {
    "Push-Ups": [
        r"""
           _O
          / |  \
         /\ |
        /  \|
    =================""",
        r"""
          _O/
         /|
        / |  \
       /  |   \
    =================""",
    ],
    "Squats": [
        r"""
          O
         /|\
         / \
         | |
        _| |_""",
        r"""
          O
        --|--
       /     \
      |       |
      |_     _|""",
    ],
    "Plank": [
        r"""
         O_____________
        /|             |
        /\             |
    ============================""",
        r"""
         O_____________
        /|_____________|
        /\
    ============================""",
    ],
    "Reverse Lunges": [
        r"""
          O
         /|\
         / \
        /   |
       /    |""",
        r"""
          O
         /|\
        | |
        | \__
        |""",
    ],
    "Superman": [
        r"""
        ___
       / O \___
      /  |     \___
         /\
""",
        r"""
     \  ___
      \/ O \___
       / |     \___
        /\
""",
    ],
    "Side Plank Left": [
        r"""
          O
         /|=========
        / |
       /""",
        r"""
          O
         /|---------
        / |
       /""",
    ],
    "Side Plank Right": [
        r"""
              O
    =========|\
              | \
                 \
""",
        r"""
              O
    ----------|\
              | \
                 \
""",
    ],
    "Glute Bridge": [
        r"""
           O
          /|\__
        _/ |   \___
    ====/   \=======""",
        r"""
           O
          /|\ __
        _/ |/   \__
    ====/   \=======""",
    ],
    "Bird Dog": [
        r"""
       ___O____
      /  |     \___
         /\
""",
        r"""
    ___O____
       |    \___
      / \
""",
    ],
    "REST": [
        r"""
            z Z z
           (-.-)
           /| |\
            / \
        ~~~~~~~~~~~~~~""",
        r"""
          Z z Z
           (-.-)
           /| |\
            / \
        ~~~~~~~~~~~~~~""",
    ],
    "DONE": [
        r"""
         \O/    * * *
          |    *     *
         / \    * * *
    ===WELL=DONE===""",
    ],
    "COUNTDOWN": [
        r"""
          O
         \|/
          |
         / \
""",
        r"""
          O
         /|\
          |
         / \
""",
    ],
}


# ── File helpers ─────────────────────────────────────────────────────
def ensure_files():
    APP_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        save_json(CONFIG_FILE, DEFAULT_CONFIG)
    if not STATE_FILE.exists():
        save_json(STATE_FILE, _default_state())


def _default_state():
    return {
        "current_workout_index": 0,
        "history": [],
        "exercise_progress": {},
        "completed_sessions": 0,
    }


def load_json(path: Path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def save_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_config():
    ensure_files()
    return load_json(CONFIG_FILE, DEFAULT_CONFIG)


def load_state():
    ensure_files()
    return load_json(STATE_FILE, _default_state())


def save_state(state):
    save_json(STATE_FILE, state)


# ── Display helpers ──────────────────────────────────────────────────
def clear_screen(enabled=True):
    if enabled:
        os.system("cls" if os.name == "nt" else "clear")


def fmt_time(seconds):
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def progress_bar(current, total, width=30):
    total = max(total, 1)
    filled = int(width * current / total)
    bar_fill = "\u2588" * filled
    bar_empty = "\u2591" * (width - filled)
    pct = int(100 * current / total)
    return f"|{bar_fill}{bar_empty}| {pct}%"


def print_header(title, subtitle="", clear=True, clear_enabled=True):
    if clear:
        clear_screen(clear_enabled)
    w = 60
    print("\u2554" + "\u2550" * w + "\u2557")
    print("\u2551" + title.center(w) + "\u2551")
    print("\u2560" + "\u2550" * w + "\u2563")
    if subtitle:
        print("\u2551" + subtitle.center(w) + "\u2551")
        print("\u255a" + "\u2550" * w + "\u255d")
    else:
        print("\u255a" + "\u2550" * w + "\u255d")


# ── Animation / timer ────────────────────────────────────────────────
def animate_block(title, seconds, frames, subtitle="", clear_enabled=True):
    total = max(int(seconds), 1)
    for remaining in range(total, 0, -1):
        elapsed = total - remaining + 1
        frame = frames[(elapsed // 2) % len(frames)]  # switch every 2s
        print_header(title, subtitle, clear=True, clear_enabled=clear_enabled)
        print(frame)
        print()
        print(f"  Time left: {fmt_time(remaining)}  /  {fmt_time(total)}")
        print(f"  {progress_bar(elapsed, total)}")
        sys.stdout.flush()
        time.sleep(1)


def countdown(seconds, clear_enabled=True):
    frames = ASCII_FRAMES["COUNTDOWN"]
    for n in range(seconds, 0, -1):
        print_header("GET READY", clear_enabled=clear_enabled)
        print(frames[n % len(frames)])
        print()
        big = str(n)
        print(f"      >>> {big} <<<")
        print()
        sys.stdout.flush()
        time.sleep(1)


def prompt_enter(message="Press Enter to continue..."):
    input(f"\n{message}")


# ── Progression logic ────────────────────────────────────────────────
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


def summarize_workout(workout, state):
    rounds = workout["rounds"]
    lines = []
    for ex in workout["exercises"]:
        val = get_progressed_value(ex, state)
        unit = "s" if ex["mode"] == "time" else " reps"
        lines.append(f"  {ex['name']:.<30} {val}{unit}")
    return rounds, lines


# ── Screens ──────────────────────────────────────────────────────────
def show_history(state, clear_enabled=True):
    print_header("WORKOUT HISTORY", clear_enabled=clear_enabled)
    history = state.get("history", [])
    if not history:
        print("  No workouts logged yet.")
    else:
        print(f"  {'Date':>19}  {'Workout':<14}  {'Duration':>8}")
        print("  " + "-" * 46)
        for item in history[-15:]:
            print(f"  {item['date']:>19}  {item['workout']:<14}  {item['duration_min']:>6.1f} m")
    prompt_enter()


def show_stats(config, state, clear_enabled=True):
    target = config["profile"].get("target_sessions_per_week", 3)
    completed = state.get("completed_sessions", 0)
    print_header("STATS", clear_enabled=clear_enabled)
    print(f"  Total sessions completed : {completed}")
    print(f"  Target per week          : {target}")
    print(f"  Configured workouts      : {len(config['workouts'])}")
    print()
    progress = state.get("exercise_progress", {})
    if progress:
        print("  Exercise progression:")
        for k, v in sorted(progress.items()):
            if v:
                print(f"    {k}: +{v}s")
    else:
        print("  No progression yet.")
    print()
    history = state.get("history", [])
    if history:
        print("  Recent sessions:")
        for item in history[-5:]:
            print(f"    {item['date']} | {item['workout']}")
    prompt_enter()


def show_status_json(config, state):
    """Machine-readable status dump for AI agents."""
    workouts = config["workouts"]
    idx = int(state.get("current_workout_index", 0)) % max(len(workouts), 1)
    workout = workouts[idx] if workouts else None
    out = {
        "completed_sessions": state.get("completed_sessions", 0),
        "current_workout_index": idx,
        "current_workout_name": workout["name"] if workout else None,
        "exercise_progress": state.get("exercise_progress", {}),
        "history_count": len(state.get("history", [])),
        "last_session": state.get("history", [])[-1] if state.get("history") else None,
        "config_path": str(CONFIG_FILE),
        "state_path": str(STATE_FILE),
    }
    print(json.dumps(out, indent=2))


# ── Main workout runner ──────────────────────────────────────────────
def run_workout(config, state, auto_start=False):
    settings = config["settings"]
    clear_enabled = bool(settings.get("enable_clear_screen", True))
    workouts = config["workouts"]
    if not workouts:
        print("No workouts configured. Edit config to add some.")
        return
    idx = int(state.get("current_workout_index", 0)) % len(workouts)
    workout = workouts[idx]

    rounds, lines = summarize_workout(workout, state)

    if not auto_start:
        print_header("HOME WORKOUT CLI", f"Session #{state.get('completed_sessions', 0) + 1}", clear_enabled=clear_enabled)
        print(f"\n  Today's session: {workout['name']}")
        print(f"  Rounds: {rounds}\n")
        print("  Exercises:")
        for line in lines:
            print(line)
        print()
        print("  [Enter] start  |  h history  |  s stats  |  q quit")
        choice = input("  > ").strip().lower()
        if choice == "q":
            return
        if choice == "h":
            show_history(state, clear_enabled=clear_enabled)
            return
        if choice == "s":
            show_stats(config, state, clear_enabled=clear_enabled)
            return

    # ── Countdown ────────────────────────────────────────────────
    countdown(int(settings.get("countdown_seconds", 5)), clear_enabled=clear_enabled)

    # ── Workout loop ─────────────────────────────────────────────
    total_seconds = 0
    for round_idx in range(1, rounds + 1):
        for ex_idx, ex in enumerate(workout["exercises"], start=1):
            current_value = get_progressed_value(ex, state)
            subtitle = (
                f"{workout['name']}  |  Round {round_idx}/{rounds}"
                f"  |  Exercise {ex_idx}/{len(workout['exercises'])}"
            )
            frames = ASCII_FRAMES.get(ex["name"], ASCII_FRAMES["REST"])

            if ex["mode"] == "time":
                animate_block(ex["name"], current_value, frames, subtitle, clear_enabled)
                total_seconds += current_value
            else:
                print_header(ex["name"], subtitle, clear=True, clear_enabled=clear_enabled)
                print(frames[0])
                print(f"\n  Target reps: {current_value}")
                prompt_enter("  Press Enter when done...")
                total_seconds += current_value * 3

            is_last_exercise = ex_idx == len(workout["exercises"])
            is_last_round = round_idx == rounds

            if not is_last_exercise:
                rest = int(settings.get("rest_between_exercises", 20))
                animate_block("REST", rest, ASCII_FRAMES["REST"], "Catch your breath", clear_enabled)
                total_seconds += rest
            elif not is_last_round:
                rest = int(settings.get("rest_between_rounds", 45))
                animate_block("ROUND BREAK", rest, ASCII_FRAMES["REST"], "Shake it out!", clear_enabled)
                total_seconds += rest

    # ── Save results ─────────────────────────────────────────────
    state["completed_sessions"] = int(state.get("completed_sessions", 0)) + 1
    state["current_workout_index"] = (idx + 1) % len(workouts)
    state.setdefault("history", []).append({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "workout": workout["name"],
        "duration_min": round(total_seconds / 60, 1),
    })

    progressed = maybe_apply_progression(config, state)
    save_state(state)

    # ── Done screen ──────────────────────────────────────────────
    print_header("WORKOUT COMPLETE!", clear_enabled=clear_enabled)
    print(ASCII_FRAMES["DONE"][0])
    print(f"  Session  : {workout['name']}")
    print(f"  Duration : ~{round(total_seconds / 60, 1)} min")
    print(f"  Total    : {state['completed_sessions']} sessions")
    if progressed:
        step = config["settings"].get("progression_seconds_step", 5)
        print(f"\n  Level up! +{step}s added to all timed exercises.")
    print(f"\n  State saved to: {STATE_FILE}")
    prompt_enter()


def open_config_hint(clear_enabled=True):
    print_header("CONFIG", clear_enabled=clear_enabled)
    print(f"  Config file: {CONFIG_FILE}")
    print(f"  State file:  {STATE_FILE}")
    print()
    print("  Editable fields:")
    print('    "rounds"              - rounds per workout')
    print('    "mode": "time"|"reps" - exercise timing mode')
    print('    "value"               - seconds or rep count')
    print('    "rest_between_*"      - rest durations')
    print('    "progression_*"       - auto progression settings')
    prompt_enter()


# ── CLI entry point ──────────────────────────────────────────────────
def main():
    config = load_config()
    state = load_state()
    clear_enabled = bool(config["settings"].get("enable_clear_screen", True))

    # CLI argument mode (agent-friendly)
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "start":
            run_workout(config, state, auto_start=True)
        elif cmd == "history":
            show_history(state, clear_enabled=clear_enabled)
        elif cmd == "stats":
            show_stats(config, state, clear_enabled=clear_enabled)
        elif cmd == "config":
            open_config_hint(clear_enabled=clear_enabled)
        elif cmd == "status":
            show_status_json(config, state)
        elif cmd == "skip":
            workouts = config["workouts"]
            idx = int(state.get("current_workout_index", 0))
            state["current_workout_index"] = (idx + 1) % max(len(workouts), 1)
            save_state(state)
            new_idx = state["current_workout_index"]
            print(f"Skipped to workout: {workouts[new_idx]['name']}")
        elif cmd == "reset":
            confirm = input("Reset all progress? (y/N): ").strip().lower()
            if confirm == "y":
                save_state(_default_state())
                print("State reset.")
            else:
                print("Cancelled.")
        else:
            print(__doc__)
        return

    # Interactive menu
    while True:
        print_header("WORKOUT CLI", "Adaptive home training", clear=True, clear_enabled=clear_enabled)
        print()
        print("  1)  Start today's workout")
        print("  2)  Show history")
        print("  3)  Show stats")
        print("  4)  Config help")
        print("  5)  Quit")
        choice = input("\n  Select: ").strip()

        if choice == "1":
            run_workout(config, state)
            config = load_config()
            state = load_state()
            clear_enabled = bool(config["settings"].get("enable_clear_screen", True))
        elif choice == "2":
            show_history(state, clear_enabled=clear_enabled)
        elif choice == "3":
            show_stats(config, state, clear_enabled=clear_enabled)
        elif choice == "4":
            open_config_hint(clear_enabled=clear_enabled)
        elif choice == "5":
            print("\n  Stay consistent. See you next time!\n")
            break
        else:
            print("\n  Invalid choice.")
            time.sleep(0.8)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Stopped. Progress saved up to last completed session.\n")
