"""Main workout runner -- executes a full workout session."""

from datetime import datetime

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from workout_cli.config import (
    console, C_ACHIEVEMENT, C_BORDER, C_DONE, C_EXERCISE, C_FIRE, C_LEVEL,
    C_PROGRESS, C_REST, C_STREAK, C_SUBTITLE, C_TIMER, C_TITLE, C_XP,
)
from workout_cli.state import save_state
from workout_cli.art import ASCII_FRAMES, get_evolution_stage
from workout_cli.progression import (
    get_progressed_value, maybe_apply_progression, update_streak,
    calculate_session_xp, update_level, check_achievements,
    summarize_workout, get_random_encouragement,
)
from workout_cli.webhook import send_webhook
from workout_cli.animation import (
    show_transition, animate_block, countdown, prompt_enter,
)
from workout_cli.renderer import fmt_time
from workout_cli.screens import show_history, show_stats


def run_workout(config, state, auto_start=False):
    settings = config["settings"]
    workouts = config["workouts"]
    if not workouts:
        console.print("[red]No workouts configured.[/red]")
        return
    idx = int(state.get("current_workout_index", 0)) % len(workouts)
    workout = workouts[idx]

    rounds, lines = summarize_workout(workout, state)

    if not auto_start:
        console.clear()
        table = Table(show_header=True, header_style="bold bright_cyan",
                      border_style=C_BORDER)
        table.add_column("Exercise", style="bright_yellow", min_width=25)
        table.add_column("Duration", style="bright_green", justify="right")
        for name, val in lines:
            table.add_row(name, val)

        session_num = state.get("completed_sessions", 0) + 1
        header_text = Text()
        header_text.append(f"\n  Today's Session: ", style="white")
        header_text.append(f"{workout['name']}\n", style=C_EXERCISE)
        header_text.append(f"  Rounds: ", style="white")
        header_text.append(f"{rounds}\n", style=C_PROGRESS)
        header_text.append(f"  Session #", style="white")
        header_text.append(f"{session_num}\n", style=C_DONE)

        console.print(Panel(header_text,
                            title=f"[{C_TITLE}]HOME WORKOUT CLI[/{C_TITLE}]",
                            border_style=C_BORDER))
        console.print(table)
        console.print()
        console.print("  [bright_cyan][Enter][/] start  |  "
                      "[bright_cyan]h[/] history  |  "
                      "[bright_cyan]s[/] stats  |  "
                      "[bright_cyan]q[/] quit")
        choice = input("  > ").strip().lower()
        if choice == "q":
            return
        if choice == "h":
            show_history(state)
            return
        if choice == "s":
            show_stats(config, state)
            return

    # ── Countdown ────────────────────────────────────────────────
    evo_stage = get_evolution_stage(state)
    countdown(int(settings.get("countdown_seconds", 5)),
              evolution_stage=evo_stage)

    # ── Workout loop ─────────────────────────────────────────────
    total_seconds = 0
    for round_idx in range(1, rounds + 1):
        for ex_idx, ex in enumerate(workout["exercises"], start=1):
            current_value = get_progressed_value(ex, state)
            subtitle = (
                f"{workout['name']}  |  Round {round_idx}/{rounds}"
                f"  |  Exercise {ex_idx}/{len(workout['exercises'])}"
                f"  |  {evo_stage['name']}"
            )
            frames = ASCII_FRAMES.get(ex["name"], ASCII_FRAMES["REST"])

            # Transition screen before each exercise
            show_transition(ex["name"], subtitle, evolution_stage=evo_stage,
                            duration=1.5)

            if ex["mode"] == "time":
                animate_block(ex["name"], current_value, frames,
                              subtitle, is_rest=False,
                              evolution_stage=evo_stage)
                total_seconds += current_value
            else:
                console.clear()
                evo_color = evo_stage["color"]
                console.print(Panel(
                    Text(f"{frames[0]}\n\n  Target reps: {current_value}",
                         style=C_EXERCISE),
                    title=f"[{C_EXERCISE}]{ex['name']}[/{C_EXERCISE}]",
                    subtitle=f"[{C_SUBTITLE}]{subtitle}[/{C_SUBTITLE}]",
                    border_style=evo_color,
                ))
                prompt_enter("  Press Enter when done...")
                total_seconds += current_value * 3

            is_last_exercise = ex_idx == len(workout["exercises"])
            is_last_round = round_idx == rounds

            if not is_last_exercise:
                rest = int(settings.get("rest_between_exercises", 20))
                animate_block("REST", rest, ASCII_FRAMES["REST"],
                              "Catch your breath", is_rest=True,
                              evolution_stage=evo_stage)
                total_seconds += rest
            elif not is_last_round:
                rest = int(settings.get("rest_between_rounds", 45))
                animate_block("ROUND BREAK", rest, ASCII_FRAMES["REST"],
                              "Shake it out!", is_rest=True,
                              evolution_stage=evo_stage)
                total_seconds += rest

    # ── Save results ─────────────────────────────────────────────
    state["completed_sessions"] = int(state.get("completed_sessions", 0)) + 1
    state["current_workout_index"] = (idx + 1) % len(workouts)
    duration_min = round(total_seconds / 60, 1)
    state.setdefault("history", []).append({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "workout": workout["name"],
        "duration_min": duration_min,
    })

    progressed = maybe_apply_progression(config, state)
    streak = update_streak(state)
    xp_earned = calculate_session_xp(
        duration_min, len(workout["exercises"]), rounds)
    state["xp"] = state.get("xp", 0) + xp_earned
    leveled_up = update_level(state)
    newly_unlocked = check_achievements(state, session_duration_min=duration_min)
    save_state(state)

    # ── Webhook ─────────────────────────────────────────────────
    webhook_url = config["settings"].get("webhook_url")
    if webhook_url:
        send_webhook(webhook_url, {
            "event": "workout_completed",
            "workout": workout["name"],
            "duration_min": duration_min,
            "session_number": state["completed_sessions"],
            "xp_earned": xp_earned,
            "level": state.get("level", 1),
            "level_title": state.get("level_title", ""),
            "streak": streak,
            "new_achievements": [a["name"] for a in newly_unlocked],
            "timestamp": datetime.now().isoformat(),
        })

    # ── Done screen ──────────────────────────────────────────────
    from workout_cli.config import STATE_FILE
    evo_stage = get_evolution_stage(state)  # re-fetch in case level changed
    console.clear()
    done_text = Text()
    done_text.append(ASCII_FRAMES["DONE"][0], style=C_DONE)
    done_text.append("\n")
    done_text.append(evo_stage["frames"][0], style=evo_stage["color"])
    done_text.append("\n\n")
    done_text.append(f"  Session  : ", style="white")
    done_text.append(f"{workout['name']}\n", style=C_EXERCISE)
    done_text.append(f"  Duration : ", style="white")
    done_text.append(f"~{duration_min} min\n", style=C_TIMER)
    done_text.append(f"  Total    : ", style="white")
    done_text.append(f"{state['completed_sessions']} sessions\n", style=C_DONE)
    done_text.append(f"  XP       : ", style="white")
    done_text.append(f"+{xp_earned} XP  (total: {state.get('xp', 0)})\n", style=C_XP)
    done_text.append(f"  Level    : ", style="white")
    done_text.append(f"{state.get('level', 1)} - {state.get('level_title', '')}\n", style=C_LEVEL)
    done_text.append(f"  Streak   : ", style="white")
    done_text.append(f"{streak} day{'s' if streak != 1 else ''}\n", style=C_STREAK)

    if progressed:
        step = config["settings"].get("progression_seconds_step", 5)
        done_text.append(
            f"\n  PROGRESSION! +{step}s added to all timed exercises.\n",
            style=C_FIRE,
        )

    if leveled_up:
        done_text.append(
            f"\n  LEVEL UP! You are now: {state['level_title']}!\n",
            style=C_LEVEL,
        )

    if newly_unlocked:
        done_text.append("\n  New achievements unlocked:\n", style=C_ACHIEVEMENT)
        for ach in newly_unlocked:
            done_text.append(f"    {ach['name']} - {ach['desc']}\n", style=C_ACHIEVEMENT)

    done_text.append(f"\n  {get_random_encouragement()}\n", style="bold bright_yellow")
    done_text.append(f"\n  State saved to: {STATE_FILE}\n", style="dim")

    console.print(Panel(done_text,
                        title=f"[{C_DONE}]WORKOUT COMPLETE![/{C_DONE}]",
                        border_style=C_DONE, padding=(1, 2)))
    prompt_enter()
