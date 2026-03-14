```
 __        __         _               _      ____ _     ___
 \ \      / /__  _ __| | _____  _   _| |_   / ___| |   |_ _|
  \ \ /\ / / _ \| '__| |/ / _ \| | | | __| | |   | |    | |
   \ V  V / (_) | |  |   < (_) | |_| | |_  | |___| |___ | |
    \_/\_/ \___/|_|  |_|\_\___/ \__,_|\__|  \____|_____|___|
```

**Adaptive home training with animated ASCII monsters, XP leveling, achievements, streaks, AI coaching, and full-color terminal UI.**

Built as a CLI-first tool so it can be driven by AI agents (Claude, OpenClaw, etc.) just as easily as by humans.

```
            \  /
         .-''''-.
        / ^    ^ \    <- This is Blobby.
       |  (~~~~)  |      He does your workouts with you.
        \ `----' /       And he levels up when you do.
         '------'
```

---

## Quick Start

```bash
pip install rich pyfiglet
python app.py
```

Config and state are auto-created in `~/.workout_cli/` on first run.

## Features

### Training Engine
- **3 rotating workouts** (A/B/C) with auto-progression every N sessions
- **4fps animated ASCII monster** ("Blobby") doing each exercise alongside you
- **Big block-digit timer** with animated flame borders
- **Full color** via [Rich](https://github.com/Textualize/rich) -- cyan, yellow, green, red urgency cues
- **Flicker-free rendering** using Rich Live display (no `cls` flashing)
- **Adaptive progression** -- exercise durations increase automatically as you get stronger

### Gamification
- **XP system** -- earn XP per session based on duration, exercises, and rounds
- **10 levels** -- from "Couch Potato" to "Transcended"
- **15 achievements** -- milestones for sessions, streaks, XP, levels, endurance
- **Streak tracking** -- consecutive days, with longest-streak record
- **Encouragement** -- Blobby drops motivational lines after each session

### Data & Planning
- **Session notes** -- attach freetext notes to any session
- **Weekly planner** -- see your week at a glance with suggested workout days
- **CSV export** -- pipe history to a file for analysis
- **JSON export** -- full state dump for backups or tooling
- **Webhook support** -- POST session data to a URL on completion (Discord, dashboards, etc.)

### AI Coach (optional)
- **`coach`** -- send your history to Claude for personalized advice
- **`generate`** -- describe a workout in plain English, AI creates the config
- Requires `pip install anthropic` and an API key (env var or config)

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `python app.py` | Interactive menu |
| `python app.py start` | Jump straight into today's workout |
| `python app.py status` | JSON state dump (machine-readable) |
| `python app.py history` | Show workout history table |
| `python app.py stats` | Stats, XP, level, streaks, progression |
| `python app.py achievements` | All achievements (locked + unlocked) |
| `python app.py plan` | Weekly plan with suggested days |
| `python app.py log "note"` | Attach a note to the last session |
| `python app.py export` | Export history as CSV to stdout |
| `python app.py export --json` | Export full config+state as JSON |
| `python app.py coach` | AI coaching advice (needs API key) |
| `python app.py generate "desc"` | AI workout generation (needs API key) |
| `python app.py config` | Show config file paths and editable fields |
| `python app.py skip` | Skip to next workout in rotation |
| `python app.py reset` | Reset all progress (asks confirmation) |
| `python app.py --dev` | Hidden dev menu: preview all evolutions, animations, colors |

## Blobby Evolution

Blobby evolves as you level up, changing form and color:

| Level | Stage | Color | Description |
|-------|-------|-------|-------------|
| 1-2 | Baby Blob | Yellow | Small, round, adorable |
| 3-4 | Blob Warrior | Green | Growing horns, getting tougher |
| 5-6 | Iron Blobby | Cyan | Armored, determined |
| 7-8 | Beast Mode | Red | Spiky, powerful, intense |
| 9-10 | Transcended | White | Celestial aura, glowing |

Use `python app.py --dev` to preview all evolutions and animations.

## For AI Agents

The `status` command outputs structured JSON with everything an agent needs:

```json
{
  "completed_sessions": 12,
  "current_workout_name": "Workout A",
  "xp": 340,
  "level": 4,
  "level_title": "Blob Warrior",
  "current_streak": 5,
  "longest_streak": 8,
  "achievements": [{"id": "first_workout", "name": "First Steps", "unlocked_at": "..."}],
  "achievements_count": "6/15",
  "history_count": 12,
  "last_session": {"date": "2026-03-14 08:30:00", "workout": "Workout C", "duration_min": 18.2},
  "config_path": "~/.workout_cli/config.json",
  "state_path": "~/.workout_cli/state.json"
}
```

Agents can:
- Read `status` to decide if a workout is due
- Run `start` to kick off a session
- Write to `config.json` to adjust workouts
- Use `coach` / `generate` for AI-driven adaptation
- Read `export --json` for full data access

## Configuration

Edit `~/.workout_cli/config.json`:

```jsonc
{
  "profile": {
    "name": "User",
    "target_sessions_per_week": 3
  },
  "settings": {
    "countdown_seconds": 5,
    "rest_between_exercises": 20,
    "rest_between_rounds": 45,
    "progression_every_completed_sessions": 3,
    "progression_seconds_step": 5,
    "webhook_url": null,           // POST here on completion
    "anthropic_api_key": null      // or use ANTHROPIC_API_KEY env var
  },
  "workouts": [
    {
      "name": "Workout A",
      "rounds": 3,
      "exercises": [
        {"name": "Push-Ups", "mode": "time", "value": 30},
        {"name": "Squats",   "mode": "time", "value": 40}
      ]
    }
  ]
}
```

## Leveling System

| Level | Title | XP Required |
|-------|-------|-------------|
| 1 | Couch Potato | 0 |
| 2 | Reluctant Mover | 50 |
| 3 | Warming Up | 150 |
| 4 | Blob Warrior | 300 |
| 5 | Sweat Apprentice | 500 |
| 6 | Iron Blobby | 800 |
| 7 | Beast Mode | 1200 |
| 8 | Legendary Blob | 1800 |
| 9 | Mythic Monster | 2500 |
| 10 | Transcended | 3500 |

**XP formula:** `10 + (duration_min * 2) + (exercises * rounds * 3)`

## File Structure

```
~/.workout_cli/
  config.json    # workouts, settings, profile
  state.json     # history, progression, XP, level, streak, achievements
```

## Dependencies

- Python 3.10+
- [rich](https://pypi.org/project/rich/) -- terminal colors, panels, tables, Live display
- [pyfiglet](https://pypi.org/project/pyfiglet/) -- optional, big countdown digits
- [anthropic](https://pypi.org/project/anthropic/) -- optional, AI coach & workout generation
