"""Animation engine: countdown, transitions, and exercise blocks."""

import time

from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from workout_cli.config import console, C_EXERCISE, C_SUBTITLE
from workout_cli.art import EVOLUTION_STAGES
from workout_cli.progression import get_random_encouragement
from workout_cli.renderer import build_exercise_frame, build_countdown_frame

# ── Animation constants ──────────────────────────────────────────────
TICK_DURATION = 0.25   # 4 fps
FRAME_SWITCH_TICKS = 2  # switch monster pose every 0.5s


def show_transition(title, subtitle="", evolution_stage=None, duration=1.0):
    """Show a quick 'NEXT UP' transition screen."""
    stage = evolution_stage or EVOLUTION_STAGES[0]
    evo_color = stage["color"]

    with Live(console=console, refresh_per_second=4, screen=True) as live:
        ticks = int(duration * 4)
        for t in range(ticks):
            # Cycle through frames for movement
            f = stage["frames"][t % len(stage["frames"])]
            out2 = Text()
            out2.append("\n\n")
            out2.append(f, style=evo_color)
            out2.append("\n\n")
            out2.append(f"         NEXT UP\n\n", style="bold bright_white")
            out2.append(f"         {title}\n", style=C_EXERCISE)
            if subtitle:
                out2.append(f"\n         {subtitle}\n", style=C_SUBTITLE)
            out2.append(f"\n         {get_random_encouragement()}\n",
                        style="italic bright_yellow")
            panel2 = Panel(out2, border_style=evo_color, padding=(1, 4))
            live.update(panel2)
            time.sleep(TICK_DURATION)


def animate_block(title, seconds, frames, subtitle="", is_rest=False,
                  evolution_stage=None):
    """Flicker-free 4fps animation using Rich Live."""
    total = max(int(seconds), 1)
    total_ticks = total * 4  # 4 ticks per second
    evo_color = (evolution_stage or EVOLUTION_STAGES[0])["color"] if evolution_stage else None
    encouragement = get_random_encouragement() if is_rest else ""

    with Live(console=console, refresh_per_second=8, screen=True) as live:
        for t in range(total_ticks):
            remaining = total - (t // 4)
            if remaining <= 0:
                remaining = 1
            frame_idx = (t // FRAME_SWITCH_TICKS) % len(frames)
            frame_art = frames[frame_idx]
            panel = build_exercise_frame(
                title, frame_art, remaining, total,
                subtitle=subtitle, is_rest=is_rest, tick_count=t,
                encouragement=encouragement if is_rest else "",
                evolution_color=evo_color,
            )
            live.update(panel)
            time.sleep(TICK_DURATION)


def countdown(seconds, evolution_stage=None):
    """Flicker-free countdown with 4fps animation using evolution art."""
    stage = evolution_stage or EVOLUTION_STAGES[0]
    total_ticks = seconds * 4
    with Live(console=console, refresh_per_second=8, screen=True) as live:
        for t in range(total_ticks):
            n = seconds - (t // 4)
            if n <= 0:
                n = 1
            panel = build_countdown_frame(n, tick_count=t,
                                          evolution_stage=stage)
            live.update(panel)
            time.sleep(TICK_DURATION)


def prompt_enter(message="Press Enter to continue..."):
    input(f"\n{message}")
