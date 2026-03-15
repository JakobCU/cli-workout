```
 _____ _ _   _   _       _
|  ___(_) |_| | | |_   _| |__
| |_  | | __| |_| | | | | '_ \
|  _| | | |_|  _  | |_| | |_) |
|_|   |_|\__|_| |_|\__,_|_.__/
```

**GitHub for your Workouts.** A CLI-first workout tracker with animated ASCII monsters, XP leveling, a workout library you can fork and adapt, and an open format designed for both humans and AI agents.

```
        \  /
     .-''''-.
    / ^    ^ \    <- This is Blobby.
   |  (~~~~)  |      He does your workouts with you.
    \ `----' /       And he evolves as you level up.
     '------'
```

**Homepage:** [fithub on Vercel](https://web-seven-tan-28.vercel.app)

---

## Quick Start

```bash
# Install dependencies
pip install rich pyfiglet

# Optional: AI features (coach, generate, adapt, AI fork)
pip install anthropic

# Run
python app.py
```

Config and state are auto-created in `~/.workout_cli/` on first run.

## First Session

1. Run `python app.py` -- the interactive menu opens
2. Press `1` to start today's workout
3. Blobby guides you through each exercise with animated timers
4. After the session: XP earned, streak updated, achievements checked
5. Run `python app.py profile` to see your FitHub profile with activity grid

## Core Concepts

### Training
- **Workout rotation** -- Cycles through your configured workouts (A -> B -> C -> A...)
- **Animated exercises** -- 4fps ASCII art of Blobby doing each exercise alongside you
- **Auto-progression** -- Every N sessions, exercise durations increase automatically
- **Time & rep modes** -- Exercises can be timed (seconds) or rep-based

### Gamification
- **XP** -- Earned per session: `10 + (duration_min * 2) + (exercises * rounds * 3)`
- **10 levels** -- From "Couch Potato" (0 XP) to "Transcended" (3500 XP)
- **15 achievements** -- Session milestones, streaks, XP targets, endurance
- **Blobby evolution** -- 5 visual stages that change as you level up
- **Streaks** -- Consecutive training days tracked with longest-streak record

### FitHub Library
- **11 curated workouts** -- From "Quick 10min" to "Arnold Golden Era"
- **Browse** -- Explore the library with difficulty ratings and tags
- **Fork** -- Copy any library workout into your config
- **AI Fork** -- Adapt a workout to your needs: `fork "fithub/arnold-golden-era" --adapt "beginner, bodyweight, 15min"`

### openWorkout Format
An open JSON format for sharing workouts between tools, platforms, and AI agents:
```json
{
  "openworkout_version": "1.0",
  "name": "Arnold Golden Era",
  "difficulty": "advanced",
  "tags": ["arnold", "volume", "bodyweight"],
  "rounds": 4,
  "exercises": [
    {"name": "Push-Ups", "mode": "time", "value": 45},
    {"name": "Squats", "mode": "time", "value": 50}
  ]
}
```

### AI Features (optional, needs API key)
- **Coach** -- Personalized advice based on your training history
- **Generate** -- Describe a workout in plain English, AI creates it
- **Adapt** -- AI analyzes your progress and suggests workout modifications
- **AI Fork** -- Take any library workout and adapt it via AI

---

## All Commands

### Training
| Command | Description |
|---------|-------------|
| `python app.py` | Interactive menu |
| `python app.py start` | Start today's workout immediately |
| `python app.py skip` | Skip to next workout in rotation |

### Stats & Profile
| Command | Description |
|---------|-------------|
| `python app.py profile` | FitHub profile: activity grid, muscle volume, stats |
| `python app.py stats` | XP, level, streaks, progression |
| `python app.py history` | Workout history table |
| `python app.py achievements` | All achievements (locked + unlocked) |
| `python app.py plan` | Weekly plan with suggested days |
| `python app.py status` | JSON state dump (machine-readable) |

### Library & Forking
| Command | Description |
|---------|-------------|
| `python app.py browse` | Interactive library browser |
| `python app.py browse --list` | List all library workouts as JSON |
| `python app.py fork "fithub/slug"` | Fork a library workout |
| `python app.py fork "fithub/slug" --adapt "prompt"` | AI-powered fork |

### Data
| Command | Description |
|---------|-------------|
| `python app.py log "note"` | Attach a note to the last session |
| `python app.py export` | Export history as CSV |
| `python app.py export --json` | Export full config + state as JSON |
| `python app.py export-ow N` | Export workout N as openWorkout JSON |
| `python app.py import-ow file.json` | Import an openWorkout file |

### AI (needs `pip install anthropic` + API key)
| Command | Description |
|---------|-------------|
| `python app.py coach` | AI coaching advice |
| `python app.py generate "description"` | AI workout generation |
| `python app.py adapt` | AI adapts existing workouts to your progress |
| `python app.py setup-key` | Interactive API key setup |

### Other
| Command | Description |
|---------|-------------|
| `python app.py config` | Show config file paths |
| `python app.py reset` | Reset all progress (asks confirmation) |
| `python app.py --dev` | Dev menu: preview evolutions, animations |

---

## FitHub Profile

Run `python app.py profile` to see your GitHub-style fitness profile:

```
+--------------------------------- Profile ---------------------------------+
|  Blobby Art   |  Lv.5 Iron Blobby                                         |
|               |  XP: 820  Sessions: 34  Streak: 5d                        |
+---------------+-----------------------------------------------------------+
+-------------------------------- Activity ---------------------------------+
|  Jan  Feb  Mar  Apr  May  Jun  Jul  Aug  Sep  Oct  Nov  Dec               |
|  [52-week activity grid with colored blocks]                              |
|  34 sessions in the last year                                             |
+--------------------------------------------------------------------------+
+------------------------ Volume by Muscle Group ---------------------------+
|  glutes        #########################  115min                          |
|  quads         ##################         85min                           |
|  chest         #######                    35min                           |
+--------------------------------------------------------------------------+
```

## FitHub Library

Browse 11 curated workout programs:

| Workout | Difficulty | Duration | Focus |
|---------|-----------|----------|-------|
| Quick 10min | Beginner | ~5min | Full body |
| Full Body Easy | Beginner | ~6min | Full body |
| Calisthenics Basics | Beginner | ~12min | Strength |
| Upper Body | Intermediate | ~13min | Push |
| Lower Body | Intermediate | ~14min | Legs |
| Core Blast | Intermediate | ~13min | Core |
| Upper/Lower Split A | Intermediate | ~15min | Upper |
| Upper/Lower Split B | Intermediate | ~14min | Lower |
| Full Body Hard | Advanced | ~25min | Endurance |
| Arnold Golden Era | Advanced | ~29min | Volume |
| HIIT Tabata Blaster | Advanced | ~14min | Cardio |

Fork any workout: `python app.py fork "fithub/arnold-golden-era"`

AI-adapt it: `python app.py fork "fithub/arnold-golden-era" --adapt "beginner, bodyweight only, 15min max"`

## Blobby Evolution

| Level | Stage | Color |
|-------|-------|-------|
| 1-2 | Baby Blob | Yellow |
| 3-4 | Blob Warrior | Green |
| 5-6 | Iron Blobby | Cyan |
| 7-8 | Beast Mode | Red |
| 9-10 | Transcended | White |

## Configuration

Edit `~/.workout_cli/config.json`:

```jsonc
{
  "profile": {
    "name": "Your Name",
    "target_sessions_per_week": 3
  },
  "settings": {
    "countdown_seconds": 5,
    "rest_between_exercises": 20,
    "rest_between_rounds": 45,
    "progression_every_completed_sessions": 3,
    "progression_seconds_step": 5,
    "webhook_url": null,
    "anthropic_api_key": null
  },
  "workouts": [...]
}
```

## Project Structure

```
app.py                  # Entry point (thin wrapper)
workout_cli/            # Python package
  config.py             # Paths, console, theme, config I/O
  state.py              # State management
  exercises.py          # Exercise registry, muscle groups
  progression.py        # XP, levels, streaks, achievements
  animation.py          # 4fps ASCII animation engine
  renderer.py           # Rich display builders
  runner.py             # Workout execution loop
  screens.py            # Profile, stats, history screens
  openworkout.py        # openWorkout format handling
  ai.py                 # AI coach, generate, adapt
  library.py            # FitHub workout library
  workout_manager.py    # Workout CRUD menus
  menus.py              # CLI dispatcher + interactive menu
  art/                  # ASCII art assets
    exercise_frames.py  # Per-exercise animation frames
    blobby_evolution.py # 5 Blobby evolution stages
    digits.py           # Timer digit art
workouts/               # Workout data files (openWorkout format)
  _template.workout.json
  fithub--*.workout.json  # 11 library workouts
web/                    # FitHub Homepage (React)
```

## Dependencies

- Python 3.10+
- [rich](https://pypi.org/project/rich/) -- terminal UI
- [pyfiglet](https://pypi.org/project/pyfiglet/) -- big countdown digits
- [anthropic](https://pypi.org/project/anthropic/) -- optional, AI features
