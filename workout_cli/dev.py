"""Developer menu for previewing visual elements."""

import time

from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from workout_cli.config import console, C_DONE
from workout_cli.art import (
    ASCII_FRAMES, EVOLUTION_STAGES,
)
from workout_cli.renderer import (
    timer_color, border_color, fmt_time, make_progress_bar_text,
)
from workout_cli.animation import (
    TICK_DURATION, FRAME_SWITCH_TICKS,
    animate_block, countdown, prompt_enter,
)


def dev_menu(config, state):
    """Hidden developer menu for previewing all visual elements."""
    while True:
        console.clear()
        console.print("[bold bright_magenta]--- DEV MENU ---[/]\n")
        console.print("  [bright_cyan]1)[/]  Browse all Blobby evolutions")
        console.print("  [bright_cyan]2)[/]  Preview exercise animations (5s each)")
        console.print("  [bright_cyan]3)[/]  Preview countdown")
        console.print("  [bright_cyan]4)[/]  Preview transition screen")
        console.print("  [bright_cyan]5)[/]  Preview done screen")
        console.print("  [bright_cyan]6)[/]  Timer color gradient test")
        console.print("  [bright_cyan]7)[/]  Back / quit")
        choice = input("\n  Select: ").strip()

        if choice == "1":
            dev_browse_evolutions()
        elif choice == "2":
            dev_preview_exercises()
        elif choice == "3":
            dev_preview_countdown()
        elif choice == "4":
            dev_preview_transitions()
        elif choice == "5":
            dev_preview_done(state)
        elif choice == "6":
            dev_timer_gradient()
        elif choice == "7":
            break


def dev_browse_evolutions():
    """Show all 5 evolution stages with animated frames."""
    for si, stage in enumerate(EVOLUTION_STAGES):
        console.clear()
        console.print(
            f"[bold bright_magenta]Evolution {si + 1}/5: "
            f"{stage['name']} (Level {stage['level_range'][0]}-{stage['level_range'][1]})[/]\n")

        for fi, frame in enumerate(stage["frames"]):
            console.print(f"  [dim]Frame {fi + 1}/{len(stage['frames'])}:[/dim]")
            console.print(f"[{stage['color']}]{frame}[/{stage['color']}]")
            console.print()

        # Also show animated for 3 seconds
        console.print("[dim]Animating for 3 seconds...[/dim]")
        time.sleep(0.5)
        with Live(console=console, refresh_per_second=8, screen=True) as live:
            for t in range(12):  # 3 seconds at 4fps
                fidx = (t // FRAME_SWITCH_TICKS) % len(stage["frames"])
                output = Text()
                output.append(
                    f"\n  Evolution {si + 1}/5: {stage['name']}"
                    f" (Level {stage['level_range'][0]}-{stage['level_range'][1]})\n\n",
                    style="bold bright_magenta",
                )
                output.append(stage["frames"][fidx], style=stage["color"])
                output.append(f"\n\n  Frame {fidx + 1}/{len(stage['frames'])}\n",
                              style="dim")
                panel = Panel(output, border_style=stage["color"],
                              title=f"[{stage['color']}]{stage['name']}[/{stage['color']}]")
                live.update(panel)
                time.sleep(TICK_DURATION)

        if si < len(EVOLUTION_STAGES) - 1:
            prompt_enter(f"  Enter for next evolution ({EVOLUTION_STAGES[si + 1]['name']})...")
        else:
            prompt_enter("  That's all evolutions!")


def dev_preview_exercises():
    """Preview each exercise animation for 5 seconds."""
    from workout_cli.animation import show_transition
    exercises = [k for k in ASCII_FRAMES.keys()
                 if k not in ("REST", "DONE", "COUNTDOWN")]
    for name in exercises:
        frames = ASCII_FRAMES[name]
        stage = EVOLUTION_STAGES[2]  # Use Iron Blobby for preview
        animate_block(name, 5, frames,
                      subtitle=f"DEV PREVIEW  |  {len(frames)} frames",
                      is_rest=False, evolution_stage=stage)

    # Also show REST
    animate_block("REST", 5, ASCII_FRAMES["REST"],
                  subtitle="DEV PREVIEW  |  Rest animation",
                  is_rest=True, evolution_stage=EVOLUTION_STAGES[0])


def dev_preview_countdown():
    """Preview countdown with each evolution stage."""
    for si, stage in enumerate(EVOLUTION_STAGES):
        console.clear()
        console.print(
            f"[bold bright_magenta]Countdown with: {stage['name']}[/]")
        time.sleep(0.5)
        countdown(3, evolution_stage=stage)
    prompt_enter("  All countdowns done!")


def dev_preview_transitions():
    """Preview transition screens for each evolution."""
    from workout_cli.animation import show_transition
    exercises = ["Push-Ups", "Squats", "Plank", "Superman"]
    for si, stage in enumerate(EVOLUTION_STAGES):
        ex = exercises[si % len(exercises)]
        show_transition(ex, f"Round 1/3  |  {stage['name']}",
                        evolution_stage=stage, duration=2.0)
    prompt_enter("  All transitions done!")


def dev_preview_done(state):
    """Preview done screen."""
    console.clear()
    done_text = Text()
    done_text.append(ASCII_FRAMES["DONE"][0], style=C_DONE)
    for si, stage in enumerate(EVOLUTION_STAGES):
        done_text.append(f"\n\n  --- {stage['name']} ---\n", style="bold bright_magenta")
        done_text.append(stage["frames"][0], style=stage["color"])
    console.print(Panel(done_text,
                        title=f"[{C_DONE}]ALL EVOLUTION FORMS[/{C_DONE}]",
                        border_style=C_DONE, padding=(1, 2)))
    prompt_enter()


def dev_timer_gradient():
    """Show timer at different remaining values to preview color gradient."""
    console.clear()
    console.print("[bold bright_magenta]Timer Color Gradient Test[/]\n")
    test_values = [60, 45, 30, 20, 15, 10, 7, 5, 4, 3, 2, 1]
    total = 60
    for remaining in test_values:
        tc = timer_color(remaining, total)
        bc = border_color(remaining, total)
        bar = make_progress_bar_text(total - remaining, total, width=20)
        console.print(
            f"  [{tc}]{fmt_time(remaining):>6}[/{tc}]  "
            f"[{bc}]border[/{bc}]  "
            f"{bar}",
        )
    prompt_enter()
