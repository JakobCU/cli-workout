```
 __        __         _               _      ____ _     ___
 \ \      / /__  _ __| | _____  _   _| |_   / ___| |   |_ _|
  \ \ /\ / / _ \| '__| |/ / _ \| | | | __| | |   | |    | |
   \ V  V / (_) | |  |   < (_) | |_| | |_  | |___| |___ | |
    \_/\_/ \___/|_|  |_|\_\___/ \__,_|\__|  \____|_____|___|
```

**Adaptive home training with animated ASCII monsters, big block timers, and full-color terminal UI.**

Built as a CLI-first tool so it can be driven by AI agents (Claude, OpenClaw, etc.) just as easily as by humans.

```
            \  /
         .-''''-.
        / ^    ^ \    <- This is Blobby.
       |  (~~~~)  |      He does your workouts with you.
        \ `----' /
         '------'
```

---

## Quick Start

```bash
pip install rich pyfiglet
python app.py
```

That's it. Config and state are auto-created in `~/.workout_cli/` on first run.

## Features

### What's in the box

- **3 rotating workouts** (A/B/C) with auto-progression every N sessions
- **4fps animated ASCII monster** ("Blobby") doing each exercise alongside you
- **Big block-digit timer** with animated flame borders
- **Full color** via [Rich](https://github.com/Textualize/rich) -- cyan, yellow, green, red urgency cues
- **Flicker-free rendering** using Rich Live display (no `cls` flashing)
- **Adaptive progression** -- exercise durations increase automatically as you get stronger
- **Persistent state** -- history, progression, and workout rotation saved to JSON

### CLI Commands (agent-friendly)

| Command | Description |
|---------|-------------|
| `python app.py` | Interactive menu |
| `python app.py start` | Jump straight into today's workout |
| `python app.py status` | JSON dump of current state (machine-readable) |
| `python app.py history` | Show workout history |
| `python app.py stats` | Show stats and progression |
| `python app.py skip` | Skip to next workout in rotation |
| `python app.py reset` | Reset all progress |
| `python app.py config` | Show config file location and editable fields |

### For AI Agents

The `status` command outputs structured JSON:

```json
{
  "completed_sessions": 12,
  "current_workout_index": 0,
  "current_workout_name": "Workout A",
  "exercise_progress": {"Push-Ups": 10, "Squats": 10},
  "history_count": 12,
  "last_session": {"date": "2026-03-14 08:30:00", "workout": "Workout C", "duration_min": 18.2},
  "config_path": "~/.workout_cli/config.json",
  "state_path": "~/.workout_cli/state.json"
}
```

Agents can read/write `config.json` directly to adjust workouts, or use `start` to kick off a session.

## Configuration

Edit `~/.workout_cli/config.json` to customize:

```jsonc
{
  "settings": {
    "countdown_seconds": 5,          // pre-workout countdown
    "rest_between_exercises": 20,    // seconds
    "rest_between_rounds": 45,       // seconds
    "progression_every_completed_sessions": 3,  // level up every N sessions
    "progression_seconds_step": 5    // add N seconds per progression
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

## File Structure

```
~/.workout_cli/
  config.json    # workouts, settings, profile
  state.json     # history, progression, current rotation index
```

## Dependencies

- Python 3.10+
- [rich](https://pypi.org/project/rich/) -- terminal colors, panels, tables, Live display
- [pyfiglet](https://pypi.org/project/pyfiglet/) -- optional, used for countdown digits if available
