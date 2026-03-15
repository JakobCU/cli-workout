"""Display helpers: timer colors, progress bars, frame builders."""

from rich.panel import Panel
from rich.text import Text

from workout_cli.config import (
    C_BORDER, C_EXERCISE, C_FIRE, C_MONSTER, C_MONSTER_REST,
    C_PROGRESS, C_REST, C_SUBTITLE, C_TITLE, C_TIMER,
)
from workout_cli.art import render_big_time, _DIGIT_ART, _FLAME_FRAMES, _EMBER_FRAMES
from workout_cli.art import EVOLUTION_STAGES
from workout_cli.progression import get_random_encouragement
from workout_cli.exercises import _estimate_workout_duration


def timer_color(remaining, total):
    """Return a Rich style for the timer based on remaining ratio."""
    if remaining <= 3:
        return "bold blink bright_red"
    if remaining <= 5:
        return "bold bright_red"
    ratio = remaining / max(total, 1)
    if ratio > 0.6:
        return "bold bright_green"
    if ratio > 0.3:
        return "bold bright_yellow"
    return "bold bright_red"


def border_color(remaining, total):
    """Return border style based on urgency."""
    if remaining <= 3:
        return "bold bright_red"
    if remaining <= 5:
        return "bright_red"
    ratio = remaining / max(total, 1)
    if ratio > 0.5:
        return C_BORDER
    return "bright_yellow"


def fmt_time(seconds):
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def make_progress_bar_text(current, total, width=44):
    total = max(total, 1)
    pct = current / total
    filled = int(width * pct)
    bar_fill = "\u2588" * filled
    bar_empty = "\u2591" * (width - filled)
    pct_str = f"{int(pct * 100):>3}%"
    return f"  {bar_fill}{bar_empty}  {pct_str}"


def build_exercise_frame(title, frame_art, remaining, total, subtitle="",
                         is_rest=False, tick_count=0, encouragement="",
                         evolution_color=None):
    """Build a Rich renderable for one animation tick."""
    elapsed = total - remaining
    title_style = C_REST if is_rest else C_EXERCISE
    t_color = timer_color(remaining, total)
    b_color = border_color(remaining, total)
    monster_style = C_MONSTER_REST if is_rest else (evolution_color or C_MONSTER)

    # Big block timer
    big_timer = render_big_time(remaining, tick_count)

    output = Text()

    if subtitle:
        output.append(f"  {subtitle}\n\n", style=C_SUBTITLE)

    # ASCII monster art
    output.append(frame_art, style=monster_style)
    output.append("\n\n")

    # Big timer digits with flame/ember lines
    for line in big_timer.splitlines():
        is_deco = any(c in line for c in ")(.*'")
        if is_deco:
            deco_style = "bold bright_red" if remaining <= 10 else C_PROGRESS
            output.append(f"  {line}\n", style=deco_style)
        else:
            output.append(f"  {line}\n", style=t_color)

    output.append("\n")

    # Progress bar
    bar_pct = elapsed / max(total, 1)
    if bar_pct > 0.8:
        bar_style = C_FIRE
    elif bar_pct > 0.5:
        bar_style = "bright_yellow"
    else:
        bar_style = C_PROGRESS
    bar_text = make_progress_bar_text(elapsed, total)
    output.append(f"{bar_text}\n\n", style=bar_style)

    # Status line
    output.append(
        f"  {fmt_time(remaining)} remaining  |  {fmt_time(total)} total  |  "
        f"{fmt_time(elapsed)} elapsed\n",
        style=C_SUBTITLE,
    )

    # Encouragement during rest
    if encouragement:
        output.append(f"\n  \"{encouragement}\"\n", style="italic bright_yellow")

    return Panel(
        output,
        title=f"[{title_style}] {title} [{title_style}]",
        border_style=b_color,
        padding=(0, 2),
    )


def build_countdown_frame(n, tick_count=0, evolution_stage=None):
    """Build a Rich panel for countdown with big number and evolution art."""
    stage = evolution_stage or EVOLUTION_STAGES[0]
    evo_frames = stage["frames"]
    evo_color = stage["color"]
    frame_art = evo_frames[tick_count % len(evo_frames)]

    # Render just the countdown digit big
    n_str = str(n)
    lines_digit = []
    for row in range(7):
        line = ""
        for ch in n_str:
            line += _DIGIT_ART.get(ch, _DIGIT_ART["0"])[row]
        lines_digit.append(line)

    flame = _FLAME_FRAMES[tick_count % len(_FLAME_FRAMES)]
    ember = _EMBER_FRAMES[tick_count % len(_EMBER_FRAMES)]

    output = Text()
    output.append(frame_art, style=evo_color)
    output.append("\n\n")
    output.append(f"  {flame}\n", style=C_FIRE)
    output.append("\n")
    for line in lines_digit:
        output.append(f"              {line}\n", style=C_TIMER)
    output.append("\n")
    output.append(f"  {ember}\n", style=C_FIRE)
    output.append("\n")
    output.append("                  GET READY!\n", style="bold bright_yellow")
    output.append(f"                  {get_random_encouragement()}\n",
                  style="italic bright_cyan")

    return Panel(
        output,
        title=f"[{C_TITLE}] STARTING SOON [{C_TITLE}]",
        subtitle=f"[{evo_color}] {stage['name']} [{evo_color}]",
        border_style=evo_color,
        padding=(0, 2),
    )


def display_workout(workout, config, index=None):
    """Display a single workout as a Rich table."""
    from rich.table import Table
    from workout_cli.config import console

    prefix = f"[{index}] " if index is not None else ""
    dur = _estimate_workout_duration(workout, config)
    table = Table(
        title=f"{prefix}{workout['name']}  ({workout['rounds']} rounds, ~{dur} min)",
        border_style=C_BORDER, header_style="bold bright_cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("Exercise", style="bright_yellow", min_width=20)
    table.add_column("Mode", style="bright_cyan", justify="center")
    table.add_column("Value", style="bright_green", justify="right")
    for i, ex in enumerate(workout["exercises"], 1):
        mode = ex.get("mode", "time")
        val = ex.get("value", 30)
        unit = f"{val}s" if mode == "time" else f"{val} reps"
        table.add_row(str(i), ex["name"], mode, unit)
    console.print(table)
