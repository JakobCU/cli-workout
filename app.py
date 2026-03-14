#!/usr/bin/env python3
"""CLI Workout Tool -- adaptive home training with fancy ASCII animations.

Designed for interactive use and for programmatic access by AI agents.

Usage:
    python app.py                       # interactive menu
    python app.py start                 # start today's workout
    python app.py history               # show history
    python app.py stats                 # show stats
    python app.py achievements          # show all achievements
    python app.py plan                  # weekly plan view
    python app.py log "felt great"      # attach note to last session
    python app.py export                # export history as CSV
    python app.py export --json         # export full state as JSON
    python app.py coach                 # AI coaching advice (needs API key)
    python app.py generate "upper body" # AI workout generation (needs API key)
    python app.py config                # show config path & hints
    python app.py status                # JSON dump of current state (agent-friendly)
    python app.py skip                  # skip to next workout in rotation
    python app.py reset                 # reset all progress (asks confirmation)
"""
import csv
import io
import json
import math
import os
import random
import sys
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

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
C_XP = "bold bright_yellow"
C_LEVEL = "bold bright_cyan"
C_STREAK = "bold bright_red"
C_ACHIEVEMENT = "bold bright_green"
C_LOCKED = "dim"

# ── Encouragement messages ──────────────────────────────────────────
ENCOURAGEMENT_MESSAGES = [
    "Blobby believes in you!",
    "You're doing amazing!",
    "Keep pushing, champion!",
    "One rep closer to greatness!",
    "Sweat is just fat crying!",
    "Blobby is proud of you!",
    "You showed up. That's half the battle!",
    "Stronger than yesterday!",
    "Pain is temporary, gains are forever!",
    "Beast mode: ACTIVATED!",
    "Your future self will thank you!",
    "Consistency beats perfection!",
    "Every rep counts!",
    "You're building something great!",
    "Blobby didn't skip leg day and neither should you!",
    "The only bad workout is the one that didn't happen!",
    "You vs. you. And you're winning!",
    "Discipline is choosing between what you want now and what you want most!",
]


def get_random_encouragement():
    return random.choice(ENCOURAGEMENT_MESSAGES)


# ── Level thresholds ────────────────────────────────────────────────
LEVEL_THRESHOLDS = [
    (0,    1, "Couch Potato"),
    (50,   2, "Reluctant Mover"),
    (150,  3, "Warming Up"),
    (300,  4, "Blob Warrior"),
    (500,  5, "Sweat Apprentice"),
    (800,  6, "Iron Blobby"),
    (1200, 7, "Beast Mode"),
    (1800, 8, "Legendary Blob"),
    (2500, 9, "Mythic Monster"),
    (3500, 10, "Transcended"),
]

# ── Achievement definitions ─────────────────────────────────────────
ACHIEVEMENTS = [
    {"id": "first_workout", "name": "First Steps",
     "desc": "Complete your first workout",
     "check": lambda s, **kw: s.get("completed_sessions", 0) >= 1},
    {"id": "five_sessions", "name": "High Five",
     "desc": "Complete 5 sessions",
     "check": lambda s, **kw: s.get("completed_sessions", 0) >= 5},
    {"id": "ten_sessions", "name": "Getting Serious",
     "desc": "Complete 10 sessions",
     "check": lambda s, **kw: s.get("completed_sessions", 0) >= 10},
    {"id": "twentyfive_sessions", "name": "Quarter Century",
     "desc": "Complete 25 sessions",
     "check": lambda s, **kw: s.get("completed_sessions", 0) >= 25},
    {"id": "fifty_sessions", "name": "Half Century",
     "desc": "Complete 50 sessions",
     "check": lambda s, **kw: s.get("completed_sessions", 0) >= 50},
    {"id": "hundred_sessions", "name": "Centurion",
     "desc": "Complete 100 sessions",
     "check": lambda s, **kw: s.get("completed_sessions", 0) >= 100},
    {"id": "streak_3", "name": "Hat Trick",
     "desc": "3-day streak",
     "check": lambda s, **kw: s.get("current_streak", 0) >= 3},
    {"id": "streak_7", "name": "Week Warrior",
     "desc": "7-day streak",
     "check": lambda s, **kw: s.get("current_streak", 0) >= 7},
    {"id": "streak_14", "name": "Fortnight Fighter",
     "desc": "14-day streak",
     "check": lambda s, **kw: s.get("current_streak", 0) >= 14},
    {"id": "streak_30", "name": "Monthly Monster",
     "desc": "30-day streak",
     "check": lambda s, **kw: s.get("current_streak", 0) >= 30},
    {"id": "long_session", "name": "Endurance Beast",
     "desc": "Complete a 30+ minute session",
     "check": lambda s, **kw: kw.get("duration", 0) >= 30},
    {"id": "xp_500", "name": "XP Hoarder",
     "desc": "Accumulate 500 XP",
     "check": lambda s, **kw: s.get("xp", 0) >= 500},
    {"id": "xp_2000", "name": "XP Titan",
     "desc": "Accumulate 2000 XP",
     "check": lambda s, **kw: s.get("xp", 0) >= 2000},
    {"id": "level_5", "name": "Sweat Apprentice",
     "desc": "Reach level 5",
     "check": lambda s, **kw: s.get("level", 1) >= 5},
    {"id": "level_10", "name": "Transcendence",
     "desc": "Reach level 10",
     "check": lambda s, **kw: s.get("level", 1) >= 10},
]

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
        "webhook_url": None,
        "anthropic_api_key": None,
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
        "current_streak": 0,
        "longest_streak": 0,
        "last_workout_date": None,
        "xp": 0,
        "level": 1,
        "level_title": "Couch Potato",
        "achievements": [],
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


def update_streak(state):
    """Update streak based on last workout date. Returns current streak."""
    today = datetime.now().strftime("%Y-%m-%d")
    last = state.get("last_workout_date")

    if last == today:
        return state.get("current_streak", 0)

    if last:
        last_date = datetime.strptime(last, "%Y-%m-%d").date()
        today_date = datetime.now().date()
        delta = (today_date - last_date).days
        if delta == 1:
            state["current_streak"] = state.get("current_streak", 0) + 1
        elif delta > 1:
            state["current_streak"] = 1
    else:
        state["current_streak"] = 1

    state["last_workout_date"] = today
    state["longest_streak"] = max(
        state.get("longest_streak", 0), state.get("current_streak", 0)
    )
    return state["current_streak"]


def calculate_session_xp(duration_min, exercise_count, rounds):
    """Calculate XP earned for a session."""
    return int(10 + duration_min * 2 + exercise_count * rounds * 3)


def update_level(state):
    """Walk level thresholds, update state. Returns True if level changed."""
    xp = state.get("xp", 0)
    old_level = state.get("level", 1)
    new_level = 1
    new_title = "Couch Potato"
    for threshold_xp, level, title in LEVEL_THRESHOLDS:
        if xp >= threshold_xp:
            new_level = level
            new_title = title
    state["level"] = new_level
    state["level_title"] = new_title
    return new_level > old_level


def check_achievements(state, session_duration_min=0):
    """Check all achievements, return list of newly unlocked ones."""
    unlocked_ids = {a["id"] for a in state.get("achievements", [])}
    newly_unlocked = []
    for ach in ACHIEVEMENTS:
        if ach["id"] not in unlocked_ids:
            if ach["check"](state, duration=session_duration_min):
                entry = {
                    "id": ach["id"],
                    "name": ach["name"],
                    "desc": ach["desc"],
                    "unlocked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                state.setdefault("achievements", []).append(entry)
                newly_unlocked.append(entry)
    return newly_unlocked


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
        table.add_column("Notes", style="dim", max_width=30)
        for item in history[-15:]:
            table.add_row(item["date"], item["workout"],
                          f"{item['duration_min']:.1f} min",
                          item.get("notes", ""))
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
    output.append(f"{len(config['workouts'])}\n", style=C_PROGRESS)
    output.append(f"  XP                       : ", style="white")
    output.append(f"{state.get('xp', 0)}\n", style=C_XP)
    output.append(f"  Level                    : ", style="white")
    output.append(f"{state.get('level', 1)} - {state.get('level_title', 'Couch Potato')}\n", style=C_LEVEL)
    output.append(f"  Current streak           : ", style="white")
    output.append(f"{state.get('current_streak', 0)} days\n", style=C_STREAK)
    output.append(f"  Longest streak           : ", style="white")
    output.append(f"{state.get('longest_streak', 0)} days\n\n", style=C_STREAK)

    # XP to next level
    xp = state.get("xp", 0)
    current_level = state.get("level", 1)
    next_threshold = None
    for threshold_xp, level, title in LEVEL_THRESHOLDS:
        if level == current_level + 1:
            next_threshold = (threshold_xp, title)
            break
    if next_threshold:
        remaining = next_threshold[0] - xp
        output.append(f"  Next level ({next_threshold[1]}): ", style="white")
        output.append(f"{remaining} XP to go\n\n", style=C_XP)

    progress = state.get("exercise_progress", {})
    if progress:
        output.append("  Exercise Progression:\n", style="bold white")
        for k, v in sorted(progress.items()):
            if v:
                output.append(f"    {k}: ", style="white")
                output.append(f"+{v}s\n", style=C_FIRE)
    else:
        output.append("  No progression yet.\n", style="dim")

    # Achievements summary
    achievements = state.get("achievements", [])
    output.append(f"\n  Achievements: ", style="bold white")
    output.append(f"{len(achievements)}/{len(ACHIEVEMENTS)} unlocked\n", style=C_ACHIEVEMENT)

    history = state.get("history", [])
    if history:
        output.append("\n  Recent Sessions:\n", style="bold white")
        for item in history[-5:]:
            output.append(f"    {item['date']}  ", style="dim")
            output.append(f"{item['workout']}", style=C_EXERCISE)
            if item.get("notes"):
                output.append(f"  -- {item['notes']}", style="dim")
            output.append("\n")

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
        "xp": state.get("xp", 0),
        "level": state.get("level", 1),
        "level_title": state.get("level_title", "Couch Potato"),
        "current_streak": state.get("current_streak", 0),
        "longest_streak": state.get("longest_streak", 0),
        "last_workout_date": state.get("last_workout_date"),
        "achievements": state.get("achievements", []),
        "achievements_count": f"{len(state.get('achievements', []))}/{len(ACHIEVEMENTS)}",
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
    console.clear()
    done_text = Text()
    done_text.append(ASCII_FRAMES["DONE"][0], style=C_DONE)
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


def cmd_achievements(state):
    """Display all achievements."""
    console.clear()
    unlocked_ids = {a["id"] for a in state.get("achievements", [])}
    unlocked_map = {a["id"]: a for a in state.get("achievements", [])}

    table = Table(title="Achievements", border_style=C_BORDER,
                  header_style="bold bright_cyan")
    table.add_column("", style="white", width=3)
    table.add_column("Name", min_width=20)
    table.add_column("Description", min_width=30)
    table.add_column("Unlocked", min_width=20)

    for ach in ACHIEVEMENTS:
        if ach["id"] in unlocked_ids:
            entry = unlocked_map[ach["id"]]
            table.add_row(
                "[bright_green][+][/]",
                f"[{C_ACHIEVEMENT}]{ach['name']}[/{C_ACHIEVEMENT}]",
                ach["desc"],
                f"[dim]{entry['unlocked_at']}[/dim]",
            )
        else:
            table.add_row(
                f"[{C_LOCKED}][ ][/{C_LOCKED}]",
                f"[{C_LOCKED}]{ach['name']}[/{C_LOCKED}]",
                f"[{C_LOCKED}]{ach['desc']}[/{C_LOCKED}]",
                "",
            )

    console.print(table)
    console.print(
        f"\n  [{C_ACHIEVEMENT}]{len(unlocked_ids)}/{len(ACHIEVEMENTS)}"
        f" unlocked[/{C_ACHIEVEMENT}]")
    prompt_enter()


def cmd_log(state, note_text):
    """Attach a note to the most recent session."""
    history = state.get("history", [])
    if not history:
        console.print("[red]No sessions logged yet.[/red]")
        return
    history[-1]["notes"] = note_text
    save_state(state)
    console.print(f"[{C_DONE}]Note added to session: {history[-1]['date']}[/{C_DONE}]")


def cmd_export(state, config, as_json=False):
    """Export history to CSV or full state as JSON."""
    if as_json:
        print(json.dumps({"config": config, "state": state}, indent=2,
                          ensure_ascii=False))
    else:
        history = state.get("history", [])
        if not history:
            console.print("[red]No history to export.[/red]")
            return
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["date", "workout", "duration_min", "notes"])
        for item in history:
            writer.writerow([
                item.get("date", ""),
                item.get("workout", ""),
                item.get("duration_min", ""),
                item.get("notes", ""),
            ])
        print(output.getvalue(), end="")


def cmd_plan(config, state):
    """Show weekly plan based on target and history."""
    console.clear()
    target = config["profile"].get("target_sessions_per_week", 3)
    today = datetime.now().date()
    # Monday of this week
    monday = today - timedelta(days=today.weekday())
    days = [(monday + timedelta(days=i)) for i in range(7)]
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    # Find which days have sessions this week
    history = state.get("history", [])
    done_dates = set()
    for item in history:
        try:
            d = datetime.strptime(item["date"], "%Y-%m-%d %H:%M:%S").date()
            if monday <= d <= days[-1]:
                done_dates.add(d)
        except (ValueError, KeyError):
            pass

    sessions_done = len(done_dates)
    remaining = max(0, target - sessions_done)

    # Suggest remaining days (spread evenly across remaining days, skip past)
    future_days = [d for d in days if d >= today and d not in done_dates]
    suggested = set()
    if remaining > 0 and future_days:
        step = max(1, len(future_days) // remaining)
        for i in range(0, len(future_days), step):
            if len(suggested) < remaining:
                suggested.add(future_days[i])

    table = Table(title="This Week's Plan", border_style=C_BORDER,
                  header_style="bold bright_cyan")
    for name in day_names:
        table.add_column(name, justify="center", min_width=8)

    row = []
    for i, d in enumerate(days):
        cell = d.strftime("%d")
        if d in done_dates:
            cell = f"[{C_DONE}]{cell} OK[/{C_DONE}]"
        elif d in suggested:
            cell = f"[{C_XP}]{cell} *[/{C_XP}]"
        elif d == today:
            cell = f"[bold white]{cell}[/bold white]"
        else:
            cell = f"[dim]{cell}[/dim]"
        row.append(cell)
    table.add_row(*row)

    console.print(table)
    console.print(f"\n  Sessions this week: [{C_DONE}]{sessions_done}[/{C_DONE}]/{target}")
    if remaining > 0:
        console.print(f"  Remaining: [{C_XP}]{remaining} sessions[/{C_XP}]  (* = suggested)")
    else:
        console.print(f"  [{C_DONE}]Target reached this week![/{C_DONE}]")
    prompt_enter()


def get_api_key(config):
    """Get Anthropic API key from env or config."""
    return (os.environ.get("ANTHROPIC_API_KEY")
            or config["settings"].get("anthropic_api_key"))


def cmd_coach(config, state):
    """Send history + state to Claude for personalized advice."""
    if not HAS_ANTHROPIC:
        console.print("[red]anthropic package not installed.[/red]")
        console.print("Run: pip install anthropic")
        return
    api_key = get_api_key(config)
    if not api_key:
        console.print("[red]No API key found.[/red]")
        console.print("Set ANTHROPIC_API_KEY env var or add to config.")
        return

    # Build context from state
    history = state.get("history", [])
    recent = history[-10:] if history else []
    context_parts = [
        f"Completed sessions: {state.get('completed_sessions', 0)}",
        f"Level: {state.get('level', 1)} ({state.get('level_title', 'Couch Potato')})",
        f"XP: {state.get('xp', 0)}",
        f"Current streak: {state.get('current_streak', 0)} days",
        f"Longest streak: {state.get('longest_streak', 0)} days",
        f"Achievements: {len(state.get('achievements', []))}/{len(ACHIEVEMENTS)}",
    ]
    if state.get("exercise_progress"):
        context_parts.append("Exercise progression: " + ", ".join(
            f"{k}: +{v}s" for k, v in state["exercise_progress"].items()))
    if recent:
        context_parts.append("\nRecent sessions:")
        for s in recent:
            line = f"  {s['date']} | {s['workout']} | {s['duration_min']}min"
            if s.get("notes"):
                line += f" | notes: {s['notes']}"
            context_parts.append(line)

    context = "\n".join(context_parts)

    console.print(f"[{C_PROGRESS}]Asking Blobby's coach brain...[/{C_PROGRESS}]\n")

    client = anthropic.Anthropic(api_key=api_key)
    with client.messages.stream(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        system=(
            "You are Blobby, a cute and encouraging workout coach monster. "
            "Analyze the user's workout data and give brief, actionable advice. "
            "Be motivational but specific. Keep it under 200 words. "
            "Use simple formatting."
        ),
        messages=[{"role": "user", "content": f"Here's my workout data:\n\n{context}\n\nGive me coaching advice."}],
    ) as stream:
        for text in stream.text_stream:
            console.print(text, end="")
    console.print()
    prompt_enter()


def cmd_generate(config, state, prompt):
    """Use Claude to generate a workout config."""
    if not HAS_ANTHROPIC:
        console.print("[red]anthropic package not installed.[/red]")
        console.print("Run: pip install anthropic")
        return
    api_key = get_api_key(config)
    if not api_key:
        console.print("[red]No API key found.[/red]")
        console.print("Set ANTHROPIC_API_KEY env var or add to config.")
        return
    if not prompt:
        console.print("[red]Usage: python app.py generate \"upper body 20 min\"[/red]")
        return

    # Show existing workout names for context
    existing = [w["name"] for w in config["workouts"]]

    console.print(f"[{C_PROGRESS}]Generating workout...[/{C_PROGRESS}]\n")

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=(
            "Generate a workout config as JSON. Output ONLY valid JSON, no markdown. "
            "Format: {\"name\": \"...\", \"rounds\": N, \"exercises\": "
            "[{\"name\": \"...\", \"mode\": \"time\", \"value\": SECONDS}, ...]}. "
            "Use mode \"time\" for timed exercises (value in seconds) or "
            "\"reps\" for rep-based (value is rep count). "
            f"Existing workouts: {existing}. Pick a unique name."
        ),
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    # Try to extract JSON
    try:
        workout = json.loads(raw)
    except json.JSONDecodeError:
        # Try to find JSON in the response
        import re
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            try:
                workout = json.loads(match.group())
            except json.JSONDecodeError:
                console.print(f"[red]Could not parse response as JSON:[/red]\n{raw}")
                return
        else:
            console.print(f"[red]Could not parse response as JSON:[/red]\n{raw}")
            return

    # Validate structure
    if not all(k in workout for k in ("name", "rounds", "exercises")):
        console.print("[red]Invalid workout structure.[/red]")
        return

    console.print(f"[{C_EXERCISE}]Generated: {workout['name']}[/{C_EXERCISE}]")
    console.print(f"  Rounds: {workout['rounds']}")
    for ex in workout["exercises"]:
        unit = "s" if ex.get("mode") == "time" else " reps"
        console.print(f"  - {ex['name']}: {ex['value']}{unit}")

    confirm = input("\nAdd this workout to your config? (y/N): ").strip().lower()
    if confirm == "y":
        config["workouts"].append(workout)
        save_json(CONFIG_FILE, config)
        console.print(f"[{C_DONE}]Workout added![/{C_DONE}]")
    else:
        console.print("[dim]Cancelled.[/dim]")


def send_webhook(url, payload):
    """POST JSON to a webhook URL. Failures are silently caught."""
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass  # webhook failure should never crash the app


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
    output.append('    "webhook_url"         ', style=C_EXERCISE)
    output.append("- POST to URL on completion\n", style="dim")
    output.append('    "anthropic_api_key"   ', style=C_EXERCISE)
    output.append("- for AI coach (or use env var)\n", style="dim")
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
        elif cmd == "achievements":
            cmd_achievements(state)
        elif cmd == "plan":
            cmd_plan(config, state)
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
        level_title = state.get("level_title", "Couch Potato")
        streak = state.get("current_streak", 0)

        console.print(
            f"  [{C_SUBTITLE}]Next up: [{C_EXERCISE}]{next_workout}"
            f"[/{C_EXERCISE}]  |  Session #{session_num}"
            f"  |  Lv.{state.get('level', 1)} {level_title}"
            f"  |  Streak: {streak}d[/{C_SUBTITLE}]\n")
        console.print(f"  [{C_PROGRESS}]1)[/{C_PROGRESS}]  Start today's workout")
        console.print(f"  [{C_PROGRESS}]2)[/{C_PROGRESS}]  Show history")
        console.print(f"  [{C_PROGRESS}]3)[/{C_PROGRESS}]  Show stats")
        console.print(f"  [{C_PROGRESS}]4)[/{C_PROGRESS}]  Achievements")
        console.print(f"  [{C_PROGRESS}]5)[/{C_PROGRESS}]  Weekly plan")
        console.print(f"  [{C_PROGRESS}]6)[/{C_PROGRESS}]  Config help")
        console.print(f"  [{C_PROGRESS}]7)[/{C_PROGRESS}]  Quit")
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
            cmd_achievements(state)
        elif choice == "5":
            cmd_plan(config, state)
        elif choice == "6":
            open_config_hint()
        elif choice == "7":
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
