#!/usr/bin/env python3
"""CLI Workout Tool -- adaptive home training with fancy ASCII animations.

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
import math
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

# ── Paths ────────────────────────────────────────────────────────────
APP_DIR = Path.home() / ".workout_cli"
STATE_FILE = APP_DIR / "state.json"
CONFIG_FILE = APP_DIR / "config.json"

# ── Color theme ──────────────────────────────────────────────────────
C_TITLE = "bold bright_cyan"
C_EXERCISE = "bold bright_yellow"
C_TIMER = "bold bright_green"
C_TIMER_LOW = "bold bright_red"
C_REST = "bold bright_magenta"
C_DONE = "bold bright_green"
C_PROGRESS = "bright_cyan"
C_SUBTITLE = "dim white"
C_BORDER = "bright_blue"
C_FIRE = "bold bright_red"
C_MONSTER = "bold bright_yellow"
C_MONSTER_REST = "bold bright_magenta"
C_MONSTER_SWEAT = "bright_cyan"

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

# ═══════════════════════════════════════════════════════════════════════
# CUTE MONSTER ASCII ART  --  6 frames each for smooth 4fps animation
# "Blobby" the workout monster: round body, tiny horns, stubby limbs
# ═══════════════════════════════════════════════════════════════════════

ASCII_FRAMES = {
    "Push-Ups": [
        # frame 0: arms extended, up position
        r"""
               \  /
            .-''''-.          *
           / @    @ \        /
          |  (~~~~)  |      /
           \ `----' /    __/
        ----`------'----'
       /  /            \  \
      +--+              +--+
     _|  |______________|  |_
    /////              \\\\\ """,
        # frame 1: going down
        r"""
               \  /
            .-''''-.         .
           / @    @ \       /
          |  (~~~~)  |    _/
           \ `----' /  __/
        ----`------'-''
       / /              \ \
      +'+    ________    '+'
     _|  |__|        |__|  |_
    /////              \\\\\ """,
        # frame 2: bottom, face squished
        r"""
               \  /
            .-''''-.        '
           / >    < \      /
          |  (~~~~)  |   _/
           \ `----' /__-'
        ----`------''
       //                \\
      +'  ________________ '+
     _|__|                |__|
    /////              \\\\\ """,
        # frame 3: pushing back up
        r"""
               \  /
            .-''''-.         .
           / @    @ \       /
          |  (~~~~)  |    _/
           \ `----' /  __/
        ----`------'-''
       / /              \ \
      +'+    ________    '+'
     _|  |__|        |__|  |_
    /////              \\\\\ """,
        # frame 4: up, happy
        r"""
              \  /     *
            .-''''-.
           / ^    ^ \    *
          |  (~~~~)  |      *
           \ `----' /    __/
        ----`------'----'
       /  /            \  \
      +--+              +--+
     _|  |______________|  |_
    /////              \\\\\ """,
        # frame 5: up, sweat drop
        r"""
               \  /    ~
            .-''''-.
           / @    @ \        o
          |  (~~~~)  |      /
           \ `----' /    __/
        ----`------'----'
       /  /            \  \
      +--+              +--+
     _|  |______________|  |_
    /////              \\\\\ """,
    ],
    "Squats": [
        # frame 0: standing tall
        r"""
                \  /
             .-''''-.
            / @    @ \
           |  (~~~~)  |
            \ `----' /
             '------'
                ||
               /  \
              /    \
             |      |
            _|_    _|_""",
        # frame 1: slight bend
        r"""
                \  /
             .-''''-.
            / @    @ \
           |  (~~~~)  |
            \ `----' /
             '------'
              / || \
             / /  \ \
            | |    | |
            |_|    |_|""",
        # frame 2: half squat
        r"""
                \  /
             .-''''-.
            / o    o \    '
           |  (~~~~)  |
            \ `----' /
             '------'
            /  /  \  \
           / _/    \_ \
          | /        \ |
          |/          \|""",
        # frame 3: deep squat, struggling face
        r"""
                \  /      ~
             .-''''-.     o
            / >    < \
           |  (~~~~)  |
            \ `----' /
           /-'------'-\
          / /  ____  \ \
         / / /    \ \ \ \
        |  |/      \|  |
        |__|        |__|""",
        # frame 4: half squat coming up
        r"""
                \  /
             .-''''-.
            / o    o \    '
           |  (~~~~)  |
            \ `----' /
             '------'
            /  /  \  \
           / _/    \_ \
          | /        \ |
          |/          \|""",
        # frame 5: standing, relief
        r"""
                \  /      *
             .-''''-.
            / ^    ^ \
           |  (~~~~)  |
            \ `----' /
             '------'
                ||
               /  \
              /    \
             |      |
            _|_    _|_""",
    ],
    "Plank": [
        r"""
            \  /
         .-''''-.___________________________________
        / @    @ \__________________________________\
       |  (~~~~)  |                                  |
        \ `----' /                                   |
         `------+-----------------------------------'
        /  /     \                              \
       +--+      +------------------------------+
      (===)                                (===)""",
        r"""
            \  /
         .-''''-.___________________________________
        / @    @ \__________________________________\
       |  (~~~~)  |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|
        \ `----' /                                   |
         `------+-----------------------------------'
        / /       \                              \
       +'+        +------------------------------+
      (===)                                (===)""",
        r"""
            \  /                              ~
         .-''''-.___________________________________
        / -    - \__________________________________\
       |  (~~~~)  |                                  |
        \ `----' /  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ |
         `------+-----------------------------------'
        /  /     \                              \
       +--+      +------------------------------+
      (===)                                (===)""",
        r"""
            \  /                          ~   o
         .-''''-.___________________________________
        / o    o \__________________________________\
       |  (~~~~)  |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|
        \ `----' /                                   |
         `------+-----------------------------------'
        / /       \                              \
       +'+        +------------------------------+
      (===)                                (===)""",
    ],
    "Reverse Lunges": [
        # standing
        r"""
                \  /
             .-''''-.
            / @    @ \
           |  (~~~~)  |
            \ `----' /
             '------'
                ||
               /  \
              /    \
             |      |
            _|_    _|_""",
        # stepping back
        r"""
                \  /
             .-''''-.
            / @    @ \
           |  (~~~~)  |
            \ `----' /
             '------'
              / |
             /  |
            |   |  \
            |_  |   \
                |    \__""",
        # deep lunge
        r"""
                \  /       ~
             .-''''-.      o
            / >    < \
           |  (~~~~)  |
            \ `----' /
             '------'
              / |
             /  |
            |   |   \
            |   |    \
            |_  |     \___""",
        # stepping back (other side)
        r"""
                \  /
             .-''''-.
            / @    @ \
           |  (~~~~)  |
            \ `----' /
             '------'
                | \
                |  \
              / |   |
             /  |   |
          __/   |  _|""",
        # deep lunge other side
        r"""
             ~  \  /
             o.-''''-.
            / >    < \
           |  (~~~~)  |
            \ `----' /
             '------'
                | \
                |  \
              / |   |
             /  |   |
         ___/   |  _|""",
        # back to standing
        r"""
                \  /       *
             .-''''-.
            / ^    ^ \
           |  (~~~~)  |
            \ `----' /
             '------'
                ||
               /  \
              /    \
             |      |
            _|_    _|_""",
    ],
    "Superman": [
        r"""
                                    *  *
            \  /                  *
         .-''''-._____________  *
        / ^    ^ \_____________>
       |  (~~~~)  |============/
        \ `----' /
         `------'
        /  /  \  \
       +--+    +--+""",
        r"""
                                   *    *
            \  /                 *
         .-''''-.______________*
        / @    @ \______________>
       |  (~~~~)  |=============/
        \ `----' /
         `------'
        /  /  \  \
       +--+    +--+""",
        r"""
                                  *      *
            \  /                *
         .-''''-._____________ *
        / ^    ^ \______________>
       |  (~~~~)  |============/
        \ `----' /
         `------'
        / /    \ \
       +'+      +'+""",
        r"""
                                   *   *
            \  /                  *
         .-''''-.______________  *
        / @    @ \_____________>
       |  (~~~~)  |============/
        \ `----' /
         `------'
        /  /  \  \
       +--+    +--+""",
    ],
    "Side Plank Left": [
        r"""
             \  /
          .-''''-.
         / @    @ \
        |  (~~~~)  |
         \  `--'  /=========================
          `------'
          /  |
         /   |
        +----+""",
        r"""
             \  /                        ~
          .-''''-.
         / @    @ \
        |  (~~~~)  |
         \  `--'  /==========================
          `------'
         /   |
         /   |
        +----+""",
        r"""
             \  /                    ~   o
          .-''''-.
         / o    o \
        |  (~~~~)  |
         \  `--'  /=========================
          `------'
          /  |
         /   |
        +----+""",
    ],
    "Side Plank Right": [
        r"""
                                     \  /
                                  .-''''-.
                                 / @    @ \
                                |  (~~~~)  |
         ========================\  `--'  /
                                  `------'
                                      |  \
                                      |   \
                                      +----+""",
        r"""
          ~                          \  /
                                  .-''''-.
                                 / @    @ \
                                |  (~~~~)  |
         =========================\  `--'  /
                                  `------'
                                      |   \
                                      |   \
                                      +----+""",
        r"""
          ~  o                       \  /
                                  .-''''-.
                                 / o    o \
                                |  (~~~~)  |
         ========================\  `--'  /
                                  `------'
                                      |  \
                                      |   \
                                      +----+""",
    ],
    "Glute Bridge": [
        r"""
            \  /
         .-''''-.
        / @    @ \  __
       |  (~~~~)  |/  \___
        \ `----' /      __\___
         `------+------'      \
        /  /     \             |
       +--+       +===========+""",
        r"""
            \  /
         .-''''-.  _
        / @    @ \/  \___
       |  (~~~~) /      _\___
        \ `----'/            \
         `-----+-------.     |
        /  /    \        \    |
       +--+      +========+==+""",
        r"""
            \  /
         .-''''-.____
        / ^    ^ \   \___
       |  (~~~~)  |     _\___
        \ `----' /           \
         `------+-------.     |
        / /      \       \    |
       +'+        +======+===+""",
        r"""
            \  /
         .-''''-.  _
        / @    @ \/  \___
       |  (~~~~) /      _\___
        \ `----'/            \
         `-----+-------.     |
        /  /    \        \    |
       +--+      +========+==+""",
    ],
    "Bird Dog": [
        r"""
            \  /
         .-''''-.________________________
        / @    @ \_______________________>
       |  (~~~~)  |=====================/
        \ `----' /
         `------'
        /  |  \
       +---+   +---+""",
        r"""
            \  /
         .-''''-._________________________
        / @    @ \________________________>
       |  (~~~~)  |======================/
        \ `----' /
         `------'
        / |    \
       +--+     +---+""",
        r"""
            \  /                          ~
         .-''''-._________________________
        / o    o \_________________________>
       |  (~~~~)  |=======================/
        \ `----' /
         `------'
        /  |  \
       +---+   +---+""",
    ],
    "REST": [
        r"""
              z
                Z
           z      z
            .-''''-.
           / -    - \
          |  (~~~~)  |
           \  .__,  /
            '------'
               ||
              /||\
             / || \
            +--++--+
        ~~~~~~~~~~~~~~~~~~~~""",
        r"""
                 Z
            z         z
              Z
            .-''''-.
           / -    - \
          |  (~~~~)  |
           \  .__,  /
            '------'
               ||
              /||\
             / || \
            +--++--+
        ~~~~~~~~~~~~~~~~~~~~""",
        r"""
           Z     z
                      Z
             z
            .-''''-.
           / -    - \
          |  (~~~~)  |
           \  .__,  /
            '------'
               ||
              /||\
             / || \
            +--++--+
        ~~~~~~~~~~~~~~~~~~~~""",
        r"""
                z   Z
          z               z
                 Z
            .-''''-.
           / -    - \
          |  (~~~~)  |
           \  .__,  /
            '------'
               ||
              /||\
             / || \
            +--++--+
        ~~~~~~~~~~~~~~~~~~~~""",
    ],
    "DONE": [
        r"""
           *  *  *  *  *  *  *  *
         *                        *
        *     \  /                 *
        *  .-''''-.                *
        * / ^    ^ \    \O/  !!!   *
        *|  (~~~~)  |    |  ! ! !  *
        * \ `----' /    / \  !!!   *
        *  '------'                *
         *                        *
           *  *  *  *  *  *  *  *
        === W E L L   D O N E ===""",
    ],
    "COUNTDOWN": [
        r"""
                \  /
             .-''''-.
            / O    O \
           |  (~~~~)  |
            \ `----' /
             '------'
                ||
               /  \
              /    \
             |      |
            _|_    _|_""",
        r"""
                \  /
             .-''''-.
            / O    O \
           |  (~~~~)  |
            \  !!!! /
             '------'
                ||
               /  \
              /    \
             |      |
            _|_    _|_""",
    ],
}

# ═══════════════════════════════════════════════════════════════════════
# CUSTOM BIG DIGIT RENDERER  --  blocky 7-line tall digits
# ═══════════════════════════════════════════════════════════════════════

_DIGIT_ART = {
    "0": [
        " ######  ",
        "##    ## ",
        "##    ## ",
        "##    ## ",
        "##    ## ",
        "##    ## ",
        " ######  ",
    ],
    "1": [
        "   ##    ",
        " ####    ",
        "   ##    ",
        "   ##    ",
        "   ##    ",
        "   ##    ",
        " ######  ",
    ],
    "2": [
        " ######  ",
        "##    ## ",
        "      ## ",
        "  ####   ",
        "##       ",
        "##       ",
        "######## ",
    ],
    "3": [
        " ######  ",
        "##    ## ",
        "      ## ",
        "  #####  ",
        "      ## ",
        "##    ## ",
        " ######  ",
    ],
    "4": [
        "##    ## ",
        "##    ## ",
        "##    ## ",
        "######## ",
        "      ## ",
        "      ## ",
        "      ## ",
    ],
    "5": [
        "######## ",
        "##       ",
        "##       ",
        "#######  ",
        "      ## ",
        "##    ## ",
        " ######  ",
    ],
    "6": [
        " ######  ",
        "##       ",
        "##       ",
        "#######  ",
        "##    ## ",
        "##    ## ",
        " ######  ",
    ],
    "7": [
        "######## ",
        "      ## ",
        "     ##  ",
        "    ##   ",
        "   ##    ",
        "   ##    ",
        "   ##    ",
    ],
    "8": [
        " ######  ",
        "##    ## ",
        "##    ## ",
        " ######  ",
        "##    ## ",
        "##    ## ",
        " ######  ",
    ],
    "9": [
        " ######  ",
        "##    ## ",
        "##    ## ",
        " ####### ",
        "      ## ",
        "      ## ",
        " ######  ",
    ],
    ":": [
        "         ",
        "   ##    ",
        "   ##    ",
        "         ",
        "   ##    ",
        "   ##    ",
        "         ",
    ],
}

# Flame deco lines that cycle around the timer
_FLAME_FRAMES = [
    r"  )  ) )  )  ) )  )  ) )  )  ) )  )  ) )  ",
    r" (  ( (  (  ( (  (  ( (  (  ( (  (  ( (  (  ",
    r"  )  ) )  )  ) )  )  ) )  )  ) )  )  ) )  ) ",
    r" (  ( (  (  ( (  (  ( (  (  ( (  (  ( (  (   ",
]

_EMBER_FRAMES = [
    r"  . * . ' . * . ' . * . ' . * . ' . * . '  ",
    r"  ' . * . ' . * . ' . * . ' . * . ' . * .  ",
    r"  * ' . * ' . * ' . * ' . * ' . * ' . * '  ",
    r"  . ' * . ' * . ' * . ' * . ' * . ' * . '  ",
]


def render_big_time(seconds, tick_count=0):
    """Render MM:SS as large block digits with animated flame border."""
    m, s = divmod(int(seconds), 60)
    time_str = f"{m:02d}:{s:02d}"

    # Build the 7 lines by concatenating digit art
    lines = []
    for row in range(7):
        line = ""
        for ch in time_str:
            line += _DIGIT_ART.get(ch, _DIGIT_ART["0"])[row]
        lines.append(line)

    # Add flame decorations
    flame = _FLAME_FRAMES[tick_count % len(_FLAME_FRAMES)]
    ember = _EMBER_FRAMES[tick_count % len(_EMBER_FRAMES)]

    result = []
    result.append(flame)
    result.append("")
    for line in lines:
        result.append(f"    {line}")
    result.append("")
    result.append(ember)
    return "\n".join(result)


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
                         is_rest=False, tick_count=0):
    """Build a Rich renderable for one animation tick."""
    elapsed = total - remaining
    title_style = C_REST if is_rest else C_EXERCISE
    timer_style = C_TIMER_LOW if remaining <= 5 else C_TIMER
    monster_style = C_MONSTER_REST if is_rest else C_MONSTER

    # Big block timer
    big_timer = render_big_time(remaining, tick_count)

    output = Text()

    if subtitle:
        output.append(f"  {subtitle}\n\n", style=C_SUBTITLE)

    # ASCII monster art
    output.append(frame_art, style=monster_style)
    output.append("\n\n")

    # Big timer digits with flame
    for line in big_timer.splitlines():
        # flame lines get fire color, digit lines get timer color
        if ")" in line or "(" in line or "*" in line or "'" in line:
            output.append(f"  {line}\n", style=C_FIRE if remaining <= 10 else C_PROGRESS)
        else:
            output.append(f"  {line}\n", style=timer_style)

    output.append("\n")

    # Progress bar
    bar_pct = elapsed / max(total, 1)
    bar_style = C_FIRE if bar_pct > 0.8 else C_PROGRESS
    bar_text = make_progress_bar_text(elapsed, total)
    output.append(f"{bar_text}\n\n", style=bar_style)
    output.append(
        f"  {fmt_time(remaining)} remaining  |  {fmt_time(total)} total  |  "
        f"{fmt_time(elapsed)} elapsed\n",
        style=C_SUBTITLE,
    )

    return Panel(
        output,
        title=f"[{title_style}] {title} [{title_style}]",
        border_style=C_FIRE if remaining <= 5 else C_BORDER,
        padding=(0, 2),
    )


def build_countdown_frame(n, tick_count=0):
    """Build a Rich panel for countdown with big number."""
    frames = ASCII_FRAMES["COUNTDOWN"]
    frame_art = frames[tick_count % len(frames)]

    big_n = render_big_time(n, tick_count)  # shows as 00:0N

    # Actually render just the single digit big
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
    output.append(frame_art, style=C_MONSTER)
    output.append("\n\n")
    output.append(f"  {flame}\n", style=C_FIRE)
    output.append("\n")
    for line in lines_digit:
        output.append(f"              {line}\n", style=C_TIMER)
    output.append("\n")
    output.append(f"  {ember}\n", style=C_FIRE)
    output.append("\n")
    output.append("                  GET READY!\n", style="bold bright_yellow")

    return Panel(
        output,
        title=f"[{C_TITLE}] STARTING SOON [{C_TITLE}]",
        border_style=C_BORDER,
        padding=(0, 2),
    )


# ── Animation engine -- true 4fps ────────────────────────────────────
TICK_DURATION = 0.25   # 4 fps
FRAME_SWITCH_TICKS = 2  # switch monster pose every 0.5s


def animate_block(title, seconds, frames, subtitle="", is_rest=False):
    """Flicker-free 4fps animation using Rich Live."""
    total = max(int(seconds), 1)
    total_ticks = total * 4  # 4 ticks per second
    tick = 0

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
            )
            live.update(panel)
            time.sleep(TICK_DURATION)


def countdown(seconds):
    """Flicker-free countdown with 4fps animation."""
    total_ticks = seconds * 4
    with Live(console=console, refresh_per_second=8, screen=True) as live:
        for t in range(total_ticks):
            n = seconds - (t // 4)
            if n <= 0:
                n = 1
            panel = build_countdown_frame(n, tick_count=t)
            live.update(panel)
            time.sleep(TICK_DURATION)


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
        lines.append((ex["name"], f"{val}{unit}"))
    return rounds, lines


# ── Screens ──────────────────────────────────────────────────────────
def show_history(state):
    console.clear()
    history = state.get("history", [])
    if not history:
        console.print(Panel("No workouts logged yet.",
                            title="[bold]History[/bold]", border_style=C_BORDER))
    else:
        table = Table(title="Workout History", border_style=C_BORDER,
                      header_style="bold bright_cyan")
        table.add_column("Date", style="white", min_width=20)
        table.add_column("Workout", style="bright_yellow")
        table.add_column("Duration", style="bright_green", justify="right")
        for item in history[-15:]:
            table.add_row(item["date"], item["workout"],
                          f"{item['duration_min']:.1f} min")
        console.print(table)
    prompt_enter()


def show_stats(config, state):
    console.clear()
    target = config["profile"].get("target_sessions_per_week", 3)
    completed = state.get("completed_sessions", 0)

    output = Text()
    output.append(f"  Total sessions completed : ", style="white")
    output.append(f"{completed}\n", style=C_DONE)
    output.append(f"  Target per week          : ", style="white")
    output.append(f"{target}\n", style=C_PROGRESS)
    output.append(f"  Configured workouts      : ", style="white")
    output.append(f"{len(config['workouts'])}\n\n", style=C_PROGRESS)

    progress = state.get("exercise_progress", {})
    if progress:
        output.append("  Exercise Progression:\n", style="bold white")
        for k, v in sorted(progress.items()):
            if v:
                output.append(f"    {k}: ", style="white")
                output.append(f"+{v}s\n", style=C_FIRE)
    else:
        output.append("  No progression yet.\n", style="dim")

    history = state.get("history", [])
    if history:
        output.append("\n  Recent Sessions:\n", style="bold white")
        for item in history[-5:]:
            output.append(f"    {item['date']}  ", style="dim")
            output.append(f"{item['workout']}\n", style=C_EXERCISE)

    console.print(Panel(output, title=f"[{C_TITLE}]Stats[/{C_TITLE}]",
                        border_style=C_BORDER, padding=(1, 2)))
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
        "last_session": (state.get("history", [])[-1]
                         if state.get("history") else None),
        "config_path": str(CONFIG_FILE),
        "state_path": str(STATE_FILE),
    }
    print(json.dumps(out, indent=2))


# ── Main workout runner ──────────────────────────────────────────────
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
    countdown(int(settings.get("countdown_seconds", 5)))

    # ── Workout loop ─────────────────────────────────────────────
    total_seconds = 0
    for round_idx in range(1, rounds + 1):
        for ex_idx, ex in enumerate(workout["exercises"], start=1):
            current_value = get_progressed_value(ex, state)
            subtitle = (
                f"{workout['name']}  \u2502  Round {round_idx}/{rounds}"
                f"  \u2502  Exercise {ex_idx}/{len(workout['exercises'])}"
            )
            frames = ASCII_FRAMES.get(ex["name"], ASCII_FRAMES["REST"])

            if ex["mode"] == "time":
                animate_block(ex["name"], current_value, frames,
                              subtitle, is_rest=False)
                total_seconds += current_value
            else:
                console.clear()
                console.print(Panel(
                    Text(f"{frames[0]}\n\n  Target reps: {current_value}",
                         style=C_EXERCISE),
                    title=f"[{C_EXERCISE}]{ex['name']}[/{C_EXERCISE}]",
                    subtitle=f"[{C_SUBTITLE}]{subtitle}[/{C_SUBTITLE}]",
                    border_style=C_BORDER,
                ))
                prompt_enter("  Press Enter when done...")
                total_seconds += current_value * 3

            is_last_exercise = ex_idx == len(workout["exercises"])
            is_last_round = round_idx == rounds

            if not is_last_exercise:
                rest = int(settings.get("rest_between_exercises", 20))
                animate_block("REST", rest, ASCII_FRAMES["REST"],
                              "Catch your breath", is_rest=True)
                total_seconds += rest
            elif not is_last_round:
                rest = int(settings.get("rest_between_rounds", 45))
                animate_block("ROUND BREAK", rest, ASCII_FRAMES["REST"],
                              "Shake it out!", is_rest=True)
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
    console.clear()
    done_text = Text()
    done_text.append(ASCII_FRAMES["DONE"][0], style=C_DONE)
    done_text.append("\n\n")
    done_text.append(f"  Session  : ", style="white")
    done_text.append(f"{workout['name']}\n", style=C_EXERCISE)
    done_text.append(f"  Duration : ", style="white")
    done_text.append(f"~{round(total_seconds / 60, 1)} min\n", style=C_TIMER)
    done_text.append(f"  Total    : ", style="white")
    done_text.append(f"{state['completed_sessions']} sessions\n", style=C_DONE)

    if progressed:
        step = config["settings"].get("progression_seconds_step", 5)
        done_text.append(
            f"\n  LEVEL UP! +{step}s added to all timed exercises.\n",
            style=C_FIRE,
        )

    done_text.append(f"\n  State saved to: {STATE_FILE}\n", style="dim")

    # Big "DONE" in block digits
    done_digits = ""
    for row in range(7):
        line = ""
        for ch in "0:00":
            line += _DIGIT_ART.get(ch, _DIGIT_ART["0"])[row]
        done_digits += f"  {line}\n"

    console.print(Panel(done_text,
                        title=f"[{C_DONE}]WORKOUT COMPLETE![/{C_DONE}]",
                        border_style=C_DONE, padding=(1, 2)))
    prompt_enter()


def open_config_hint():
    console.clear()
    output = Text()
    output.append(f"  Config file: ", style="white")
    output.append(f"{CONFIG_FILE}\n", style=C_PROGRESS)
    output.append(f"  State file:  ", style="white")
    output.append(f"{STATE_FILE}\n\n", style=C_PROGRESS)
    output.append("  Editable fields:\n", style="bold white")
    output.append('    "rounds"              ', style=C_EXERCISE)
    output.append("- rounds per workout\n", style="dim")
    output.append('    "mode": "time"|"reps" ', style=C_EXERCISE)
    output.append("- exercise timing mode\n", style="dim")
    output.append('    "value"               ', style=C_EXERCISE)
    output.append("- seconds or rep count\n", style="dim")
    output.append('    "rest_between_*"      ', style=C_EXERCISE)
    output.append("- rest durations\n", style="dim")
    output.append('    "progression_*"       ', style=C_EXERCISE)
    output.append("- auto progression settings\n", style="dim")
    console.print(Panel(output, title=f"[{C_TITLE}]Configuration[/{C_TITLE}]",
                        border_style=C_BORDER, padding=(1, 2)))
    prompt_enter()


# ── CLI entry point ──────────────────────────────────────────────────
BANNER = r"""
 __        __         _               _      ____ _     ___
 \ \      / /__  _ __| | _____  _   _| |_   / ___| |   |_ _|
  \ \ /\ / / _ \| '__| |/ / _ \| | | | __| | |   | |    | |
   \ V  V / (_) | |  |   < (_) | |_| | |_  | |___| |___ | |
    \_/\_/ \___/|_|  |_|\_\___/ \__,_|\__|  \____|_____|___|
"""


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
        elif cmd == "config":
            open_config_hint()
        elif cmd == "status":
            show_status_json(config, state)
        elif cmd == "skip":
            workouts = config["workouts"]
            idx = int(state.get("current_workout_index", 0))
            state["current_workout_index"] = (idx + 1) % max(len(workouts), 1)
            save_state(state)
            new_idx = state["current_workout_index"]
            console.print(
                f"[{C_DONE}]Skipped to: {workouts[new_idx]['name']}[/{C_DONE}]")
        elif cmd == "reset":
            confirm = input("Reset all progress? (y/N): ").strip().lower()
            if confirm == "y":
                save_state(_default_state())
                console.print(f"[{C_DONE}]State reset.[/{C_DONE}]")
            else:
                console.print("[dim]Cancelled.[/dim]")
        else:
            print(__doc__)
        return

    # Interactive menu
    while True:
        console.clear()
        console.print(f"[{C_TITLE}]{BANNER}[/{C_TITLE}]")

        session_num = state.get("completed_sessions", 0) + 1
        workouts = config["workouts"]
        idx = int(state.get("current_workout_index", 0)) % max(len(workouts), 1)
        next_workout = workouts[idx]["name"] if workouts else "None"

        console.print(
            f"  [{C_SUBTITLE}]Next up: [{C_EXERCISE}]{next_workout}"
            f"[/{C_EXERCISE}]  |  Session #{session_num}[/{C_SUBTITLE}]\n")
        console.print(f"  [{C_PROGRESS}]1)[/{C_PROGRESS}]  Start today's workout")
        console.print(f"  [{C_PROGRESS}]2)[/{C_PROGRESS}]  Show history")
        console.print(f"  [{C_PROGRESS}]3)[/{C_PROGRESS}]  Show stats")
        console.print(f"  [{C_PROGRESS}]4)[/{C_PROGRESS}]  Config help")
        console.print(f"  [{C_PROGRESS}]5)[/{C_PROGRESS}]  Quit")
        choice = input("\n  Select: ").strip()

        if choice == "1":
            run_workout(config, state)
            config = load_config()
            state = load_state()
        elif choice == "2":
            show_history(state)
        elif choice == "3":
            show_stats(config, state)
        elif choice == "4":
            open_config_hint()
        elif choice == "5":
            console.print(
                f"\n  [{C_DONE}]Stay consistent. See you next time![/{C_DONE}]\n")
            break
        else:
            console.print("\n  [red]Invalid choice.[/red]")
            time.sleep(0.8)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print(
            f"\n\n  [{C_REST}]Stopped. Progress saved up to last "
            f"completed session.[/{C_REST}]\n")
