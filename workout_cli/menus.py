"""Main menu: CLI dispatcher and interactive menu loop."""

import sys
import time

from rich.panel import Panel
from rich.text import Text

from workout_cli.config import (
    console, HAS_ANTHROPIC,
    C_DONE, C_EXERCISE, C_LEVEL, C_PROGRESS, C_REST,
    C_STREAK, C_SUBTITLE, C_TITLE, C_XP,
    load_config, has_api_key,
)
from workout_cli.state import load_state, save_state, _default_state
from workout_cli.art import get_evolution_stage
from workout_cli.progression import LEVEL_THRESHOLDS
from workout_cli.animation import prompt_enter
from workout_cli.runner import run_workout
from workout_cli.screens import (
    show_history, show_stats, show_status_json,
    cmd_achievements, cmd_log, cmd_export, cmd_plan,
    cmd_profile, open_config_hint,
    cmd_tree, cmd_diff, cmd_star, cmd_version_history,
    cmd_exercises,
)
from workout_cli.ai import cmd_coach, cmd_generate, cmd_adapt, cmd_setup_key
from workout_cli.library import cmd_browse, cmd_fork, cmd_fork_ai
from workout_cli.openworkout import cmd_export_openworkout, cmd_import_openworkout
from workout_cli.workout_manager import _workout_submenu
from workout_cli.dev import dev_menu

BANNER = r"""
 __        __         _               _      ____ _     ___
 \ \      / /__  _ __| | _____  _   _| |_   / ___| |   |_ _|
  \ \ /\ / / _ \| '__| |/ / _ \| | | | __| | |   | |    | |
   \ V  V / (_) | |  |   < (_) | |_| | |_  | |___| |___ | |
    \_/\_/ \___/|_|  |_|\_\___/ \__,_|\__|  \____|_____|___|
"""

# The module-level docstring for --help
_USAGE = """\
CLI Workout Tool -- adaptive home training with fancy ASCII animations.

Usage:
    python app.py                       # interactive menu
    python app.py start                 # start today's workout
    python app.py history               # show history
    python app.py stats                 # show stats
    python app.py achievements          # show all achievements
    python app.py plan                  # weekly plan view
    python app.py profile               # show profile
    python app.py log "felt great"      # attach note to last session
    python app.py export                # export history as CSV
    python app.py export --json         # export full state as JSON
    python app.py coach                 # AI coaching advice (needs API key)
    python app.py generate "upper body" # AI workout generation (needs API key)
    python app.py adapt                 # AI adapts existing workouts (needs API key)
    python app.py setup-key             # interactive API key setup
    python app.py config                # show config path & hints
    python app.py status                # JSON dump of current state (agent-friendly)
    python app.py exercises             # list all exercises in catalog
    python app.py exercises <slug>      # show exercise details, variants, tips
    python app.py browse                # browse workout library
    python app.py browse --list         # list library as JSON
    python app.py export-ow <n>         # export workout n as openWorkout JSON
    python app.py import-ow <file>      # import openWorkout JSON file
    python app.py fork <slug>           # fork a library workout
    python app.py fork <slug> --adapt "desc"  # fork + AI adapt
    python app.py tree                  # show fork lineage tree
    python app.py diff <n> <m>          # compare two workouts
    python app.py star [slug]           # toggle star / list stars
    python app.py versions <n>          # show version history of workout
    python app.py skip                  # skip to next workout in rotation
    python app.py reset                 # reset all progress (asks confirmation)
"""


def _ai_submenu(config, state):
    """AI features submenu."""
    while True:
        console.clear()
        key_status = (
            f"[{C_DONE}]configured[/{C_DONE}]"
            if has_api_key(config)
            else f"[bold bright_red]not set[/bold bright_red]"
        )
        sdk_status = (
            f"[{C_DONE}]installed[/{C_DONE}]"
            if HAS_ANTHROPIC
            else f"[bold bright_red]not installed[/bold bright_red]"
        )
        console.print(f"[{C_TITLE}]  AI Features[/{C_TITLE}]\n")
        console.print(f"  API Key: {key_status}    SDK: {sdk_status}\n")
        console.print(f"  [{C_PROGRESS}]1)[/{C_PROGRESS}]  Coach -- get personalized advice")
        console.print(f"  [{C_PROGRESS}]2)[/{C_PROGRESS}]  Generate -- create a workout from a description")
        console.print(f"  [{C_PROGRESS}]3)[/{C_PROGRESS}]  Adapt -- AI tweaks your existing workouts")
        console.print(f"  [{C_PROGRESS}]4)[/{C_PROGRESS}]  Setup API key")
        console.print(f"  [{C_PROGRESS}]5)[/{C_PROGRESS}]  Back")
        choice = input("\n  Select: ").strip()

        if choice == "1":
            cmd_coach(config, state)
        elif choice == "2":
            prompt = input("  Describe your workout: ").strip()
            if prompt:
                cmd_generate(config, state, prompt)
                config = load_config()
        elif choice == "3":
            cmd_adapt(config, state)
            config = load_config()  # reload since adapt modifies config
        elif choice == "4":
            cmd_setup_key()
        elif choice == "5":
            break


def _config_submenu(config):
    """Config and setup submenu."""
    while True:
        console.clear()
        console.print(f"[{C_TITLE}]  Config & Setup[/{C_TITLE}]\n")
        console.print(f"  [{C_PROGRESS}]1)[/{C_PROGRESS}]  Config help (file paths & fields)")
        console.print(f"  [{C_PROGRESS}]2)[/{C_PROGRESS}]  Setup API key")
        console.print(f"  [{C_PROGRESS}]3)[/{C_PROGRESS}]  Back")
        choice = input("\n  Select: ").strip()

        if choice == "1":
            open_config_hint()
        elif choice == "2":
            cmd_setup_key()
        elif choice == "3":
            break


def main():
    config = load_config()
    state = load_state()

    # CLI argument mode (agent-friendly)
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "start":
            run_workout(config, state, auto_start=True)
        elif cmd == "history":
            show_history(state)
        elif cmd == "stats":
            show_stats(config, state)
        elif cmd == "achievements":
            cmd_achievements(state)
        elif cmd == "plan":
            cmd_plan(config, state)
        elif cmd == "profile":
            cmd_profile(config, state)
        elif cmd == "log":
            if len(sys.argv) < 3:
                console.print('Usage: python app.py log "your note here"')
            else:
                cmd_log(state, " ".join(sys.argv[2:]))
        elif cmd == "export":
            cmd_export(state, config, as_json="--json" in sys.argv)
        elif cmd == "coach":
            cmd_coach(config, state)
        elif cmd == "generate":
            prompt = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
            cmd_generate(config, state, prompt)
        elif cmd == "adapt":
            cmd_adapt(config, state)
        elif cmd in ("setup-key", "setup_key", "key"):
            cmd_setup_key()
        elif cmd == "config":
            open_config_hint()
        elif cmd == "status":
            show_status_json(config, state)
        elif cmd == "exercises":
            slug = sys.argv[2] if len(sys.argv) > 2 else None
            cmd_exercises(slug)
        elif cmd == "browse":
            cmd_browse(config, list_only="--list" in sys.argv)
        elif cmd == "export-ow":
            idx_str = sys.argv[2] if len(sys.argv) > 2 else None
            cmd_export_openworkout(config, state, idx_str)
        elif cmd == "import-ow":
            if len(sys.argv) < 3:
                console.print("Usage: python app.py import-ow <file.json>")
            else:
                cmd_import_openworkout(config, sys.argv[2])
        elif cmd == "fork":
            if len(sys.argv) < 3:
                console.print("Usage: python app.py fork <slug>")
            elif "--adapt" in sys.argv:
                adapt_idx = sys.argv.index("--adapt")
                adapt_prompt = " ".join(sys.argv[adapt_idx + 1:]) if adapt_idx + 1 < len(sys.argv) else ""
                cmd_fork_ai(config, state, sys.argv[2])
            else:
                cmd_fork(config, sys.argv[2])
        elif cmd == "tree":
            cmd_tree(config)
        elif cmd == "diff":
            if len(sys.argv) < 4:
                console.print("Usage: python app.py diff <n> <m>")
            else:
                cmd_diff(config, sys.argv[2], sys.argv[3])
        elif cmd == "star":
            slug = sys.argv[2] if len(sys.argv) > 2 else None
            cmd_star(state, slug)
        elif cmd == "versions":
            if len(sys.argv) < 3:
                console.print("Usage: python app.py versions <n>")
            else:
                cmd_version_history(config, sys.argv[2])
        elif cmd == "skip":
            workouts = config["workouts"]
            idx = int(state.get("current_workout_index", 0))
            state["current_workout_index"] = (idx + 1) % max(len(workouts), 1)
            save_state(state)
            new_idx = state["current_workout_index"]
            console.print(
                f"[{C_DONE}]Skipped to: {workouts[new_idx]['name']}[/{C_DONE}]")
        elif cmd == "--dev":
            dev_menu(config, state)
        elif cmd == "reset":
            confirm = input("Reset all progress? (y/N): ").strip().lower()
            if confirm == "y":
                save_state(_default_state())
                console.print(f"[{C_DONE}]State reset.[/{C_DONE}]")
            else:
                console.print("[dim]Cancelled.[/dim]")
        else:
            print(_USAGE)
        return

    # Interactive menu
    while True:
        console.clear()
        console.print(f"[{C_TITLE}]{BANNER}[/{C_TITLE}]")

        session_num = state.get("completed_sessions", 0) + 1
        workouts = config["workouts"]
        idx = int(state.get("current_workout_index", 0)) % max(len(workouts), 1)
        next_workout = workouts[idx]["name"] if workouts else "None"
        level = state.get("level", 1)
        level_title = state.get("level_title", "Couch Potato")
        streak = state.get("current_streak", 0)
        xp = state.get("xp", 0)

        # Show Blobby in current evolution
        evo = get_evolution_stage(state)
        evo_frame = evo["frames"][0]

        # XP bar to next level
        next_threshold = None
        current_threshold = 0
        for t_xp, t_level, t_title in LEVEL_THRESHOLDS:
            if t_level == level:
                current_threshold = t_xp
            if t_level == level + 1:
                next_threshold = (t_xp, t_title)
                break

        xp_bar = ""
        if next_threshold:
            xp_in_level = xp - current_threshold
            xp_needed = next_threshold[0] - current_threshold
            filled = int(20 * xp_in_level / max(xp_needed, 1))
            filled = min(filled, 20)
            xp_bar = (
                f"  XP: [{C_XP}]{xp}[/{C_XP}]  "
                f"[{C_PROGRESS}]{'#' * filled}{'.' * (20 - filled)}[/{C_PROGRESS}]"
                f"  [{C_SUBTITLE}]{next_threshold[0] - xp} to {next_threshold[1]}[/{C_SUBTITLE}]"
            )
        else:
            xp_bar = f"  XP: [{C_XP}]{xp}[/{C_XP}]  [{C_DONE}]MAX LEVEL[/{C_DONE}]"

        # Status panel with Blobby
        status = Text()
        status.append(evo_frame, style=evo["color"])
        status.append(f"\n\n  {evo['name']}", style=evo["color"])
        status.append(f"  |  Lv.{level} {level_title}", style=C_LEVEL)
        streak_str = f"  |  Streak: {streak}d" if streak > 0 else ""
        status.append(streak_str, style=C_STREAK)
        console.print(Panel(status, border_style=evo["color"], padding=(0, 2)))

        console.print(xp_bar)
        console.print(
            f"\n  [{C_SUBTITLE}]Next up: [{C_EXERCISE}]{next_workout}"
            f"[/{C_EXERCISE}]  |  Session #{session_num}[/{C_SUBTITLE}]\n")
        console.print(f"  [{C_PROGRESS}]1)[/{C_PROGRESS}]  Start today's workout")
        console.print(f"  [{C_PROGRESS}]2)[/{C_PROGRESS}]  Workouts (view / edit / add)")
        console.print(f"  [{C_PROGRESS}]3)[/{C_PROGRESS}]  Show history")
        console.print(f"  [{C_PROGRESS}]4)[/{C_PROGRESS}]  Show stats")
        console.print(f"  [{C_PROGRESS}]5)[/{C_PROGRESS}]  Achievements")
        console.print(f"  [{C_PROGRESS}]6)[/{C_PROGRESS}]  Weekly plan")
        console.print(f"  [{C_PROGRESS}]7)[/{C_PROGRESS}]  AI Coach / Generate")
        console.print(f"  [{C_PROGRESS}]8)[/{C_PROGRESS}]  Config & API key")
        console.print(f"  [{C_PROGRESS}]9)[/{C_PROGRESS}]  Quit")
        choice = input("\n  Select: ").strip()

        if choice == "1":
            run_workout(config, state)
            config = load_config()
            state = load_state()
        elif choice == "2":
            _workout_submenu(config, state)
            config = load_config()
            state = load_state()
        elif choice == "3":
            show_history(state)
        elif choice == "4":
            show_stats(config, state)
        elif choice == "5":
            cmd_achievements(state)
        elif choice == "6":
            cmd_plan(config, state)
        elif choice == "7":
            _ai_submenu(config, state)
            config = load_config()
        elif choice == "8":
            _config_submenu(config)
        elif choice == "9":
            console.print(
                f"\n  [{C_DONE}]Stay consistent. See you next time![/{C_DONE}]\n")
            break
        else:
            console.print("\n  [red]Invalid choice.[/red]")
            time.sleep(0.8)
