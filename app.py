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
    python app.py adapt                 # AI adapts existing workouts (needs API key)
    python app.py setup-key             # interactive API key setup
    python app.py config                # show config path & hints
    python app.py status                # JSON dump of current state (agent-friendly)
    python app.py skip                  # skip to next workout in rotation
    python app.py reset                 # reset all progress (asks confirmation)
"""
import copy
import csv
import io
import json
import math
import os
import random
import re
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

# ── .env loading ─────────────────────────────────────────────────────
def _load_dotenv():
    """Load .env file from the script's directory if it exists."""
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value

_load_dotenv()

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


# ═══════════════════════════════════════════════════════════════════════
# BLOBBY EVOLUTION -- 5 stages based on level
# Each stage: list of 3 idle frames for animation, + color style
# ═══════════════════════════════════════════════════════════════════════

EVOLUTION_STAGES = [
    {
        # Stage 1: Baby Blob (Level 1-2)
        "name": "Baby Blob",
        "level_range": (1, 2),
        "color": "bright_yellow",
        "frames": [
            r"""
              \  /
           .-''''-.
          / o    o \
         |  (~~~~)  |
          \ `----' /
           '------'
              ||
             /  \
            /    \
          _|_    _|_""",
            r"""
              \  /
           .-''''-.
          / o    o \
         |  (~~~~)  |
          \  .''.  /
           '------'
              ||
             /  \
            /    \
          _|_    _|_""",
            r"""
              \  /
           .-''''-.
          / -    - \
         |  (~~~~)  |
          \ `----' /
           '------'
              ||
             /||\
            / || \
          _|_    _|_""",
        ],
    },
    {
        # Stage 2: Blob Warrior (Level 3-4)
        "name": "Blob Warrior",
        "level_range": (3, 4),
        "color": "bright_green",
        "frames": [
            r"""
             \\    //
           \.-''''-./
          =/ @    @ \=
         | |  (~~~~)  | |
          \ \ `----' / /
           \'------'/
             | || |
            /| /\ |\
           / |/  \| \
         _|__|    |__|_""",
            r"""
             \\    //
           \.-''''-./
          =/ @    @ \=
         | |  (>~~<)  | |
          \ \ `----' / /
           \'------'/
             | || |
            /|_/\_|\
           / |    | \
         _|__|    |__|_""",
            r"""
             \\    //
           \.-''''-./
          =/ ^    ^ \=
         | |  (~~~~)  | |
          \ \ `----' / /
           \'------'/
             | || |
            /| /\ |\
           / |/  \| \
         _|__|    |__|_""",
        ],
    },
    {
        # Stage 3: Iron Blobby (Level 5-6)
        "name": "Iron Blobby",
        "level_range": (5, 6),
        "color": "bright_cyan",
        "frames": [
            r"""
             \\\\  ////
           \\.-''''-.//
          =|| @    @ ||=
         ||| (~~~~)  |||
          =|| `----' ||=
           |'------'|
           /|  |  |  |\
          /*| /|  |\ |*\
         /**|/ |  | \|**\
        {***||_|  |_||***}""",
            r"""
             \\\\  ////
           \\.-''''-.//
          =|| @    @ ||=
         ||| (>~~<)  |||
          =|| `----' ||=
           |'------'|
           /|  |  |  |\
          /*|  |  |  |*\
         /**|/_|  |_\|**\
        {***||_|  |_||***}""",
            r"""
             \\\\  ////
           \\.-''''-.//
          =|| ^    ^ ||=
         ||| (~~~~)  |||
          =||  !!!! ||=
           |'------'|
           /|  |  |  |\
          /*| /|  |\ |*\
         /**|/ |  | \|**\
        {***||_|  |_||***}""",
        ],
    },
    {
        # Stage 4: Beast Mode (Level 7-8)
        "name": "Beast Mode",
        "level_range": (7, 8),
        "color": "bright_red",
        "frames": [
            r"""
          *  \\\\  ////  *
         * \\.-''''-.//  *
        **=|| O    O ||=**
        *||| (~~~~)  |||*
        **=|| `----' ||=**
         * |'------'| *
         */||  |  |  ||\*
        **/ | /|  |\ | \**
       **/ /|/ |  | \|\ \**
      {**/ /**||  ||**\ \**}""",
            r"""
           * \\\\  //// *
         **\\.-''''-.// **
        **=|| O    O ||=**
        *||| (>~~<)  |||*
        **=|| `----' ||=**
         * |'------'| *
         */||  |  |  ||\*
        **/  | |  | |  \**
       **/  /|| || ||\  \**
      {**/ /**||  ||**\ \**}""",
            r"""
          *  \\\\  ////  *
         * \\.-''''-.//  *
        **=|| ^    ^ ||=**
        *||| (~~~~)  |||*
        **=||  !!!!  ||=**
         * |'------'| *
         */||  |  |  ||\*
        **/ | /|  |\ | \**
       **/ /|/ |  | \|\ \**
      {**/ /**||  ||**\ \**}""",
        ],
    },
    {
        # Stage 5: Transcended (Level 9-10)
        "name": "Transcended",
        "level_range": (9, 10),
        "color": "bold bright_white",
        "frames": [
            r"""
       . * . * . * . * . *
      *    \\\\  ////     *
     .  *\\.-''''-.// *   .
     * **=|| O    O ||=** *
     . *||| (~~~~)  |||*  .
     * **=|| `----' ||=** *
      * * |'------'| * *
      .  /||  |  |  ||\  .
       * / | /|  |\ | \ *
      .  / |/ |  | \|  \ .
       . * . * . * . * . *""",
            r"""
        * . * . * . * . *
      .    \\\\  ////     .
     *  .\\.-''''-.// .   *
     . *.=|| O    O ||=.* .
     * .||| (>~~<)  |||.*  *
     . *.=|| `----' ||=.* .
      . . |'------'| . .
      *  /||  |  |  ||\  *
       . / | /|  |\ | \ .
      *  / |/ |  | \|  \ *
       * . * . * . * . * .""",
            r"""
      . . * . * . * . * . .
       *    \\\\  ////    *
      . .*\\.-''''-.//  *. .
      * .*=|| ^    ^ ||=*. *
      . *||| (~~~~)  |||*  .
      * .*=||  !!!!  ||=*. *
       * . |'------'| . *
       .  /||  |  |  ||\  .
        * / | /|  |\ | \ *
       .  / |/ |  | \|  \ .
      . . * . * . * . * . .""",
        ],
    },
]


def get_evolution_stage(state):
    """Return the evolution stage dict for the current level."""
    level = state.get("level", 1)
    for stage in reversed(EVOLUTION_STAGES):
        if level >= stage["level_range"][0]:
            return stage
    return EVOLUTION_STAGES[0]


def get_evolution_stage_by_index(idx):
    """Return evolution stage by index (0-4). For dev menu."""
    return EVOLUTION_STAGES[min(idx, len(EVOLUTION_STAGES) - 1)]


# ── Timer color gradient ────────────────────────────────────────────
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


# ── Animation engine -- true 4fps ────────────────────────────────────
TICK_DURATION = 0.25   # 4 fps
FRAME_SWITCH_TICKS = 2  # switch monster pose every 0.5s


def show_transition(title, subtitle="", evolution_stage=None, duration=1.0):
    """Show a quick 'NEXT UP' transition screen."""
    stage = evolution_stage or EVOLUTION_STAGES[0]
    evo_color = stage["color"]
    frame = stage["frames"][0]

    output = Text()
    output.append("\n\n")
    output.append(frame, style=evo_color)
    output.append("\n\n")
    output.append(f"         NEXT UP\n\n", style="bold bright_white")
    output.append(f"         {title}\n", style=C_EXERCISE)
    if subtitle:
        output.append(f"\n         {subtitle}\n", style=C_SUBTITLE)
    output.append(f"\n         {get_random_encouragement()}\n", style="italic bright_yellow")

    panel = Panel(output, border_style=evo_color, padding=(1, 4))

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
            out2.append(f"\n         {get_random_encouragement()}\n", style="italic bright_yellow")
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
    """Get Anthropic API key from env (.env loaded at startup) or config."""
    return (os.environ.get("ANTHROPIC_API_KEY")
            or config["settings"].get("anthropic_api_key"))


def has_api_key(config):
    """Check if an API key is configured anywhere."""
    return bool(get_api_key(config))


def cmd_setup_key():
    """Interactive API key setup -- writes to .env file."""
    env_path = Path(__file__).resolve().parent / ".env"
    console.clear()
    console.print(Panel(
        "[bold]AI Coach Setup[/bold]\n\n"
        "Blobby's AI features (coach, generate, adapt) need an Anthropic API key.\n\n"
        "  1. Go to [bright_cyan]console.anthropic.com[/bright_cyan]\n"
        "  2. Create an account and add billing\n"
        "  3. Go to API Keys and create a new key\n"
        "  4. Paste it below\n\n"
        f"The key will be saved to: [dim]{env_path}[/dim]\n"
        "This file is in .gitignore and won't be committed.",
        title=f"[{C_TITLE}]API Key Setup[/{C_TITLE}]",
        border_style=C_BORDER,
        padding=(1, 2),
    ))

    # Show current status
    current = os.environ.get("ANTHROPIC_API_KEY")
    if current:
        masked = current[:12] + "..." + current[-4:]
        console.print(f"\n  Current key: [{C_DONE}]{masked}[/{C_DONE}]")
        console.print("  [dim]Enter a new key to replace, or press Enter to keep it.[/dim]")

    key = input("\n  Paste API key (or Enter to cancel): ").strip()
    if not key:
        console.print("[dim]  Cancelled.[/dim]")
        return

    if not key.startswith("sk-ant-"):
        console.print("[red]  That doesn't look like an Anthropic API key (should start with sk-ant-)[/red]")
        confirm = input("  Save anyway? (y/N): ").strip().lower()
        if confirm != "y":
            console.print("[dim]  Cancelled.[/dim]")
            return

    # Write to .env
    lines = []
    replaced = False
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("ANTHROPIC_API_KEY="):
                lines.append(f"ANTHROPIC_API_KEY={key}")
                replaced = True
            else:
                lines.append(line)
    if not replaced:
        lines.append(f"ANTHROPIC_API_KEY={key}")

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.environ["ANTHROPIC_API_KEY"] = key

    masked = key[:12] + "..." + key[-4:]
    console.print(f"\n  [{C_DONE}]Key saved![/{C_DONE}]  {masked}")
    console.print(f"  [dim]Written to {env_path}[/dim]")


def _require_ai(config):
    """Check anthropic SDK + API key. Returns (client, True) or (None, False)."""
    if not HAS_ANTHROPIC:
        console.print("[red]anthropic package not installed.[/red]")
        console.print("  Run: [bright_cyan]pip install anthropic[/bright_cyan]")
        return None, False
    api_key = get_api_key(config)
    if not api_key:
        console.print("[red]No API key found.[/red]")
        console.print()
        setup = input("  Would you like to set up your API key now? (y/N): ").strip().lower()
        if setup == "y":
            cmd_setup_key()
            api_key = get_api_key(config)
        if not api_key:
            return None, False
    return anthropic.Anthropic(api_key=api_key), True


AI_MODEL = "claude-sonnet-4-20250514"


def _build_user_context(config, state):
    """Build a rich text summary of the user's workout data for AI prompts."""
    history = state.get("history", [])
    recent = history[-15:] if history else []

    parts = [
        "=== USER PROFILE ===",
        f"Name: {config['profile'].get('name', 'User')}",
        f"Target sessions/week: {config['profile'].get('target_sessions_per_week', 3)}",
        "",
        "=== PROGRESS ===",
        f"Completed sessions: {state.get('completed_sessions', 0)}",
        f"Level: {state.get('level', 1)} - {state.get('level_title', 'Couch Potato')}",
        f"XP: {state.get('xp', 0)}",
        f"Current streak: {state.get('current_streak', 0)} days",
        f"Longest streak: {state.get('longest_streak', 0)} days",
        f"Achievements unlocked: {len(state.get('achievements', []))}/{len(ACHIEVEMENTS)}",
    ]

    if state.get("exercise_progress"):
        parts.append("")
        parts.append("=== EXERCISE PROGRESSION (bonus seconds added) ===")
        for k, v in sorted(state["exercise_progress"].items()):
            parts.append(f"  {k}: +{v}s")

    parts.append("")
    parts.append("=== CURRENT WORKOUTS ===")
    for w in config["workouts"]:
        parts.append(f"\n  {w['name']} ({w['rounds']} rounds):")
        for ex in w["exercises"]:
            base = ex["value"]
            bonus = state.get("exercise_progress", {}).get(ex["name"], 0)
            actual = base + bonus
            unit = "s" if ex["mode"] == "time" else " reps"
            prog = f" (+{bonus}s)" if bonus else ""
            parts.append(f"    - {ex['name']}: {actual}{unit}{prog}")

    if recent:
        parts.append("")
        parts.append("=== RECENT SESSIONS ===")
        for s in recent:
            line = f"  {s['date']} | {s['workout']} | {s['duration_min']}min"
            if s.get("notes"):
                line += f" | \"{s['notes']}\""
            parts.append(line)

    return "\n".join(parts)


def cmd_coach(config, state):
    """AI coaching: analyze history and give personalized advice."""
    client, ok = _require_ai(config)
    if not ok:
        return

    context = _build_user_context(config, state)
    evo = get_evolution_stage(state)

    console.print()
    console.print(Panel(
        Text(evo["frames"][0], style=evo["color"]),
        title=f"[{evo['color']}]Blobby is thinking...[/{evo['color']}]",
        border_style=evo["color"],
        padding=(0, 2),
    ))
    console.print()

    try:
        with client.messages.stream(
            model=AI_MODEL,
            max_tokens=800,
            system=(
                "You are Blobby, a cute and encouraging workout coach monster. "
                "You have horns, a round body, and you care deeply about your human's fitness.\n\n"
                "Analyze the user's workout data and give personalized coaching advice. "
                "Be specific about what to change and why. Consider:\n"
                "- Are they consistent? (streak, frequency vs target)\n"
                "- Are they progressing? (look at exercise progression bonuses)\n"
                "- Workout balance (muscle groups, variety)\n"
                "- Session duration trends\n"
                "- Their notes/feelings if any\n\n"
                "Structure your response as:\n"
                "1. A brief assessment (2-3 sentences)\n"
                "2. 2-3 specific actionable recommendations\n"
                "3. One motivational closing line in character as Blobby\n\n"
                "Keep it under 250 words. No markdown headers."
            ),
            messages=[{
                "role": "user",
                "content": f"Here's my workout data:\n\n{context}\n\nCoach me, Blobby!"
            }],
        ) as stream:
            for text in stream.text_stream:
                console.print(text, end="")
    except Exception as e:
        console.print(f"\n[red]API error: {e}[/red]")
        return

    console.print("\n")
    prompt_enter()


def cmd_generate(config, state, prompt):
    """AI workout generation: describe what you want, get a workout config."""
    client, ok = _require_ai(config)
    if not ok:
        return
    if not prompt:
        console.print("[red]Usage: python app.py generate \"upper body 20 min\"[/red]")
        console.print()
        console.print("  Examples:")
        console.print('    python app.py generate "leg day, 15 minutes, bodyweight only"')
        console.print('    python app.py generate "easy recovery session"')
        console.print('    python app.py generate "hardcore full body 30 min"')
        return

    context = _build_user_context(config, state)
    existing = [w["name"] for w in config["workouts"]]

    evo = get_evolution_stage(state)
    console.print(f"\n  [{evo['color']}]Blobby is designing your workout...[/{evo['color']}]\n")

    try:
        response = client.messages.create(
            model=AI_MODEL,
            max_tokens=1000,
            system=(
                "Generate a workout config as JSON. Output ONLY valid JSON, no markdown, "
                "no explanation, no code fences.\n\n"
                "Format:\n"
                '{"name": "Workout Name", "rounds": N, "exercises": [\n'
                '  {"name": "Exercise Name", "mode": "time", "value": SECONDS},\n'
                '  {"name": "Exercise Name", "mode": "reps", "value": COUNT}\n'
                "]}\n\n"
                "Rules:\n"
                "- Use mode 'time' for timed exercises (value = seconds, typically 20-60)\n"
                "- Use mode 'reps' for rep-based exercises (value = rep count, typically 8-20)\n"
                "- Include 4-7 exercises per workout\n"
                "- 2-4 rounds is typical\n"
                "- Scale difficulty to the user's level and progression\n"
                f"- Existing workout names to avoid: {existing}\n"
                "- Pick a creative unique name\n"
            ),
            messages=[{
                "role": "user",
                "content": (
                    f"User request: {prompt}\n\n"
                    f"User context (for scaling difficulty):\n{context}"
                ),
            }],
        )
    except Exception as e:
        console.print(f"[red]API error: {e}[/red]")
        return

    raw = response.content[0].text.strip()

    # Parse JSON -- try direct first, then extract from response
    workout = None
    for attempt in [raw, (re.search(r'\{.*\}', raw, re.DOTALL) or type('', (), {'group': lambda s: ''})()).group()]:
        if not attempt:
            continue
        try:
            workout = json.loads(attempt)
            break
        except (json.JSONDecodeError, AttributeError):
            continue

    if not workout:
        console.print(f"[red]Could not parse response as JSON:[/red]\n{raw}")
        return

    # Validate structure
    if not all(k in workout for k in ("name", "rounds", "exercises")):
        console.print("[red]Invalid workout structure -- missing required fields.[/red]")
        return
    if not isinstance(workout["exercises"], list) or not workout["exercises"]:
        console.print("[red]Invalid workout -- no exercises.[/red]")
        return

    # Display the generated workout
    console.print()
    table = Table(title=f"Generated: {workout['name']}",
                  border_style=evo["color"], header_style="bold bright_cyan")
    table.add_column("Exercise", style="bright_yellow", min_width=25)
    table.add_column("Mode", style="bright_cyan", justify="center")
    table.add_column("Value", style="bright_green", justify="right")
    for ex in workout["exercises"]:
        mode = ex.get("mode", "time")
        val = ex.get("value", 30)
        unit = f"{val}s" if mode == "time" else f"{val} reps"
        table.add_row(ex.get("name", "?"), mode, unit)
    console.print(table)
    console.print(f"  Rounds: [{C_PROGRESS}]{workout['rounds']}[/{C_PROGRESS}]")

    # Estimate duration
    total_est = 0
    rest_ex = config["settings"].get("rest_between_exercises", 20)
    rest_rd = config["settings"].get("rest_between_rounds", 45)
    for ex in workout["exercises"]:
        if ex.get("mode") == "time":
            total_est += ex.get("value", 30)
        else:
            total_est += ex.get("value", 10) * 3
    total_est = (total_est + rest_ex * (len(workout["exercises"]) - 1)) * workout["rounds"]
    total_est += rest_rd * (workout["rounds"] - 1)
    console.print(f"  Estimated duration: [{C_PROGRESS}]~{round(total_est / 60)} min[/{C_PROGRESS}]")

    confirm = input("\n  Add this workout to your config? (y/N): ").strip().lower()
    if confirm == "y":
        config["workouts"].append(workout)
        save_json(CONFIG_FILE, config)
        console.print(f"[{C_DONE}]Workout '{workout['name']}' added![/{C_DONE}]")
    else:
        console.print("[dim]Cancelled.[/dim]")
    prompt_enter()


def cmd_adapt(config, state):
    """AI-powered adaptation: analyze progress and tweak existing workouts."""
    client, ok = _require_ai(config)
    if not ok:
        return

    if state.get("completed_sessions", 0) < 3:
        console.print(
            "[red]Need at least 3 completed sessions for meaningful adaptation.[/red]")
        return

    context = _build_user_context(config, state)
    evo = get_evolution_stage(state)

    console.print(f"\n  [{evo['color']}]Blobby is analyzing your progress...[/{evo['color']}]\n")

    # Send the full workout config + state for analysis
    workouts_json = json.dumps(config["workouts"], indent=2)

    try:
        response = client.messages.create(
            model=AI_MODEL,
            max_tokens=2000,
            system=(
                "You are an AI workout optimizer. Analyze the user's workout history, "
                "progression, and current workout configs. Suggest specific modifications "
                "to their existing workout configs to better suit their progress.\n\n"
                "Output a JSON object with this exact format:\n"
                '{"changes": [\n'
                '  {"workout_index": 0, "description": "what changed and why",\n'
                '   "workout": {full updated workout object}}\n'
                "]}\n\n"
                "Rules:\n"
                "- Only modify workouts that need changes\n"
                "- Keep the same exercise names when possible (they map to animations)\n"
                "- Available exercise names with animations: Push-Ups, Squats, Plank, "
                "Reverse Lunges, Superman, Side Plank Left, Side Plank Right, "
                "Glute Bridge, Bird Dog\n"
                "- You can add new exercises but prefer the ones above\n"
                "- Adjust values (duration/reps), rounds, or swap exercises\n"
                "- Scale based on their level, progression, and session notes\n"
                "- Output ONLY valid JSON, no markdown\n"
            ),
            messages=[{
                "role": "user",
                "content": (
                    f"User context:\n{context}\n\n"
                    f"Current workout configs:\n{workouts_json}\n\n"
                    "Analyze and suggest adaptations."
                ),
            }],
        )
    except Exception as e:
        console.print(f"[red]API error: {e}[/red]")
        return

    raw = response.content[0].text.strip()

    # Parse response
    result = None
    for attempt in [raw, (re.search(r'\{.*\}', raw, re.DOTALL) or type('', (), {'group': lambda s: ''})()).group()]:
        if not attempt:
            continue
        try:
            result = json.loads(attempt)
            break
        except (json.JSONDecodeError, AttributeError):
            continue

    if not result or "changes" not in result:
        console.print(f"[red]Could not parse adaptation suggestions.[/red]")
        console.print(f"[dim]{raw[:500]}[/dim]")
        return

    changes = result["changes"]
    if not changes:
        console.print(f"[{C_DONE}]No changes recommended -- your workouts look good![/{C_DONE}]")
        return

    # Display proposed changes
    console.print(f"\n  [{C_EXERCISE}]Proposed adaptations:[/{C_EXERCISE}]\n")
    for change in changes:
        idx = change.get("workout_index", 0)
        desc = change.get("description", "No description")
        workout = change.get("workout", {})

        old_name = config["workouts"][idx]["name"] if idx < len(config["workouts"]) else "?"
        new_name = workout.get("name", old_name)

        console.print(f"  [{C_EXERCISE}]{old_name}[/{C_EXERCISE}] -> [{C_DONE}]{new_name}[/{C_DONE}]")
        console.print(f"  [dim]{desc}[/dim]")

        if workout.get("exercises"):
            table = Table(border_style="dim", show_header=True,
                          header_style="bold dim")
            table.add_column("Exercise", min_width=20)
            table.add_column("Mode", justify="center")
            table.add_column("Value", justify="right")
            for ex in workout["exercises"]:
                mode = ex.get("mode", "time")
                val = ex.get("value", 30)
                unit = f"{val}s" if mode == "time" else f"{val} reps"
                table.add_row(ex.get("name", "?"), mode, unit)
            console.print(table)
        console.print()

    confirm = input("  Apply these adaptations? (y/N): ").strip().lower()
    if confirm == "y":
        for change in changes:
            idx = change.get("workout_index", 0)
            workout = change.get("workout", {})
            if idx < len(config["workouts"]) and workout:
                config["workouts"][idx] = workout
        save_json(CONFIG_FILE, config)
        console.print(f"[{C_DONE}]Workouts adapted![/{C_DONE}]")
    else:
        console.print("[dim]Cancelled.[/dim]")
    prompt_enter()


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


# ── Dev menu ─────────────────────────────────────────────────────────
def _ai_submenu(config, state):
    """AI features submenu."""
    while True:
        console.clear()
        key_status = (
            f"[{C_DONE}]configured[/{C_DONE}]"
            if has_api_key(config)
            else f"[{C_FIRE}]not set[/{C_FIRE}]"
        )
        sdk_status = (
            f"[{C_DONE}]installed[/{C_DONE}]"
            if HAS_ANTHROPIC
            else f"[{C_FIRE}]not installed[/{C_FIRE}]"
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


# ── Workout preset library ──────────────────────────────────────────
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

# Available exercise names (ones that have ASCII art)
AVAILABLE_EXERCISES = [
    "Push-Ups", "Squats", "Plank", "Reverse Lunges", "Superman",
    "Side Plank Left", "Side Plank Right", "Glute Bridge", "Bird Dog",
]


def _estimate_workout_duration(workout, config):
    """Estimate total duration in minutes including rests."""
    rest_ex = config["settings"].get("rest_between_exercises", 20)
    rest_rd = config["settings"].get("rest_between_rounds", 45)
    ex_total = 0
    for ex in workout["exercises"]:
        if ex.get("mode") == "time":
            ex_total += ex.get("value", 30)
        else:
            ex_total += ex.get("value", 10) * 3
    per_round = ex_total + rest_ex * max(len(workout["exercises"]) - 1, 0)
    total = per_round * workout["rounds"] + rest_rd * max(workout["rounds"] - 1, 0)
    return round(total / 60, 1)


def _display_workout(workout, config, index=None):
    """Display a single workout as a Rich table."""
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
            _display_workout(workouts[i], config, index=i + 1)
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
            _display_workout(preset, config)
            confirm = input("\n  Add this workout? (y/N): ").strip().lower()
            if confirm == "y":
                config["workouts"].append(preset)
                save_json(CONFIG_FILE, config)
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
    _display_workout(workout, config)
    confirm = input("\n  Save this workout? (y/N): ").strip().lower()
    if confirm == "y":
        config["workouts"].append(workout)
        save_json(CONFIG_FILE, config)
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
    _display_workout(workout, config, index=i + 1)

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
    _display_workout(workout, config, index=i + 1)
    confirm = input("\n  Save changes? (y/N): ").strip().lower()
    if confirm == "y":
        save_json(CONFIG_FILE, config)
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
        save_json(CONFIG_FILE, config)
        save_state(state)
        console.print(f"  [{C_DONE}]Deleted: {name}[/{C_DONE}]")
    else:
        console.print("  [dim]Cancelled.[/dim]")
    prompt_enter()


def _workout_ai_pick(config, state):
    """Let AI configure workouts based on user preferences."""
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
            model=AI_MODEL,
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
    # Try as array first
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
        _display_workout(w, config)

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
        save_json(CONFIG_FILE, config)
        console.print(f"  [{C_DONE}]Done! {len(valid)} workouts saved.[/{C_DONE}]")
    else:
        console.print("  [dim]Cancelled.[/dim]")
    prompt_enter()


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
        elif cmd == "adapt":
            cmd_adapt(config, state)
        elif cmd in ("setup-key", "setup_key", "key"):
            cmd_setup_key()
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


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print(
            f"\n\n  [{C_REST}]Stopped. Progress saved up to last "
            f"completed session.[/{C_REST}]\n")
