# FitHub CLI -- Agent Integration Guide

This document describes how AI agents (LLMs, coding assistants, automation tools) can interact with the FitHub CLI workout tracker. The tool is designed CLI-first and machine-readable-first.

## Quick Reference

```bash
# Read current state (JSON)
python app.py status

# Start a workout
python app.py start

# List library workouts (JSON)
python app.py browse --list

# Fork a workout
python app.py fork "fithub/arnold-golden-era"

# AI-fork (adapt via Claude)
python app.py fork "fithub/arnold-golden-era" --adapt "beginner, bodyweight, 15min"

# Export workout as openWorkout JSON
python app.py export-ow 1

# Import openWorkout JSON
python app.py import-ow workout.json

# Full state export
python app.py export --json
```

## Data Locations

| File | Path | Purpose |
|------|------|---------|
| Config | `~/.gitfit/config.json` | Workouts, settings, profile |
| State | `~/.gitfit/state.json` | History, XP, level, streak, achievements |
| Library | `workouts/fithub--*.workout.json` | Curated workout plans |
| Template | `workouts/_template.workout.json` | openWorkout format template |

## Machine-Readable Commands

### `python app.py status` -> JSON

Returns complete state as JSON to stdout:

```json
{
  "completed_sessions": 12,
  "current_workout_index": 0,
  "current_workout_name": "Workout A",
  "exercise_progress": {"Push-Ups": 5, "Squats": 10},
  "xp": 340,
  "level": 4,
  "level_title": "Blob Warrior",
  "current_streak": 5,
  "longest_streak": 8,
  "last_workout_date": "2026-03-14",
  "achievements": [{"id": "first_workout", "name": "First Steps", "unlocked_at": "..."}],
  "achievements_count": "6/15",
  "history_count": 12,
  "last_session": {"date": "2026-03-14 08:30:00", "workout": "Workout C", "duration_min": 18.2},
  "config_path": "~/.gitfit/config.json",
  "state_path": "~/.gitfit/state.json"
}
```

### `python app.py browse --list` -> JSON

Returns all library workouts as JSON array:

```json
[
  {"slug": "fithub/arnold-golden-era", "name": "Arnold Golden Era", "rounds": 4, "exercises": 7},
  {"slug": "fithub/quick-10min", "name": "Quick 10min", "rounds": 2, "exercises": 3}
]
```

### `python app.py export --json` -> JSON

Returns full `{config: {...}, state: {...}}` dump to stdout.

### `python app.py export-ow N` -> JSON

Exports workout at index N (1-based) in openWorkout format to stdout.

### `python app.py export` -> CSV

Exports history as CSV to stdout: `date,workout,duration_min,notes`

## openWorkout Format v1.0

The standard format for creating, sharing, and importing workouts.

### Schema

```json
{
  "openworkout_version": "1.0",
  "id": "uuid-v4",
  "name": "Workout Name",
  "description": "What this workout targets.",
  "author": {"name": "author-name"},
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601",
  "forked_from": "parent-id-or-null",
  "tags": ["bodyweight", "beginner"],
  "difficulty": "beginner|intermediate|advanced|expert",
  "estimated_duration_min": 20,
  "equipment": ["none"],
  "muscle_groups": ["chest", "quads", "core"],
  "rounds": 3,
  "rest_between_exercises_sec": 20,
  "rest_between_rounds_sec": 45,
  "exercises": [
    {
      "name": "Push-Ups",
      "mode": "time",
      "value": 30,
      "muscle_groups": ["chest", "shoulders", "triceps"]
    }
  ]
}
```

### Exercise Rules

- `mode`: `"time"` (value = seconds, range 15-60) or `"reps"` (value = rep count, range 5-25)
- `value`: positive integer
- 4-7 exercises per workout is typical
- 2-4 rounds is typical

### Exercises with Built-in Animations

These exercise names have ASCII art animations in the CLI. **Prefer these names** when creating workouts:

```
Push-Ups, Squats, Plank, Reverse Lunges, Superman,
Side Plank Left, Side Plank Right, Glute Bridge, Bird Dog
```

Any other exercise name will work but uses a fallback animation.

### Muscle Group Vocabulary

Use these muscle group names for consistency:

```
chest, shoulders, triceps, quads, glutes, hamstrings,
core, obliques, lower back
```

Exercises not in the built-in mapping default to `["general"]`.

## Modifying Workouts Directly

Agents can read and write `~/.gitfit/config.json` directly.

### Adding a Workout

Append to the `workouts` array in config.json:

```json
{
  "name": "My New Workout",
  "rounds": 3,
  "exercises": [
    {"name": "Push-Ups", "mode": "time", "value": 30},
    {"name": "Squats", "mode": "time", "value": 40},
    {"name": "Plank", "mode": "time", "value": 25}
  ]
}
```

Optional `_meta` field for tracking provenance:

```json
{
  "name": "...",
  "rounds": 3,
  "exercises": [...],
  "_meta": {
    "openworkout_id": "uuid",
    "forked_from": "fithub/arnold-golden-era",
    "author": "agent-name",
    "tags": ["bodyweight"],
    "difficulty": "beginner"
  }
}
```

### Modifying Settings

Editable fields in `config.json.settings`:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `countdown_seconds` | int | 5 | Pre-exercise countdown |
| `rest_between_exercises` | int | 20 | Rest seconds between exercises |
| `rest_between_rounds` | int | 45 | Rest seconds between rounds |
| `progression_every_completed_sessions` | int | 3 | Sessions before auto-progression |
| `progression_seconds_step` | int | 5 | Seconds added per progression |
| `webhook_url` | string/null | null | POST JSON here on workout completion |
| `anthropic_api_key` | string/null | null | API key for AI features |

## Webhook Payload

On workout completion, if `webhook_url` is set, the tool POSTs:

```json
{
  "event": "workout_completed",
  "workout": "Workout A",
  "duration_min": 18.2,
  "session_number": 12,
  "xp_earned": 85,
  "level": 4,
  "level_title": "Blob Warrior",
  "streak": 5,
  "new_achievements": ["Dedicated"],
  "timestamp": "2026-03-14T08:30:00"
}
```

## Gamification System

### XP Formula

```
xp = 10 + (duration_min * 2) + (exercise_count * rounds * 3)
```

### Level Thresholds

| XP | Level | Title |
|----|-------|-------|
| 0 | 1 | Couch Potato |
| 50 | 2 | Reluctant Mover |
| 150 | 3 | Warming Up |
| 300 | 4 | Blob Warrior |
| 500 | 5 | Sweat Apprentice |
| 800 | 6 | Iron Blobby |
| 1200 | 7 | Beast Mode |
| 1800 | 8 | Legendary Blob |
| 2500 | 9 | Mythic Monster |
| 3500 | 10 | Transcended |

### Achievements (15 total)

| ID | Trigger |
|----|---------|
| `first_workout` | 1 session |
| `five_sessions` | 5 sessions |
| `ten_sessions` | 10 sessions |
| `twentyfive_sessions` | 25 sessions |
| `fifty_sessions` | 50 sessions |
| `hundred_sessions` | 100 sessions |
| `streak_3` | 3-day streak |
| `streak_7` | 7-day streak |
| `streak_14` | 14-day streak |
| `streak_30` | 30-day streak |
| `long_session` | 30+ minute session |
| `xp_500` | 500 XP total |
| `xp_2000` | 2000 XP total |
| `level_5` | Reach level 5 |
| `level_10` | Reach level 10 |

### Progression

Every `progression_every_completed_sessions` sessions (default: 3), all time-based exercises gain `progression_seconds_step` seconds (default: 5). The bonus is tracked in `state.json.exercise_progress` as `{"Push-Ups": 10}` (meaning +10s added to base value).

## State Schema (state.json)

```json
{
  "current_workout_index": 0,
  "history": [
    {
      "date": "2026-03-14 08:30:00",
      "workout": "Workout A",
      "duration_min": 18.2,
      "notes": "optional note",
      "volume": {
        "exercises_completed": 15,
        "rounds_completed": 3,
        "exercises": [
          {"name": "Push-Ups", "mode": "time", "actual_value": 35}
        ]
      }
    }
  ],
  "exercise_progress": {"Push-Ups": 5, "Squats": 10},
  "completed_sessions": 12,
  "current_streak": 5,
  "longest_streak": 8,
  "last_workout_date": "2026-03-14",
  "xp": 340,
  "level": 4,
  "level_title": "Blob Warrior",
  "achievements": [
    {"id": "first_workout", "name": "First Steps", "desc": "...", "unlocked_at": "..."}
  ]
}
```

## Agent Workflows

### Check if user should work out today

```bash
python app.py status
# Parse JSON: check last_workout_date vs today
# Check current_streak to encourage consistency
# Suggest the current_workout_name
```

### Create a personalized workout

```bash
# Option 1: AI generation (needs API key)
python app.py generate "upper body, 20 minutes, intermediate"

# Option 2: AI fork from library
python app.py fork "fithub/arnold-golden-era" --adapt "beginner, no equipment, 15min"

# Option 3: Write directly to config.json
# Read config, append workout to workouts array, save
```

### Analyze training patterns

```bash
python app.py export --json
# Parse full state: look at history for patterns
# Check volume data for muscle group balance
# Identify gaps in training
```

### Import a workout from external source

```bash
# Write openWorkout JSON to a file, then:
python app.py import-ow custom-workout.workout.json
```

## Project Structure

```
app.py                          # Entry point
gitfit/                    # Python package (21 modules)
  config.py                     # Core config, paths, console
  state.py                      # State management
  exercises.py                  # Exercise registry + muscle groups
  progression.py                # XP, levels, streaks, achievements
  animation.py                  # ASCII animation engine
  renderer.py                   # Rich display builders
  runner.py                     # Workout execution
  screens.py                    # Profile, stats, history
  openworkout.py                # openWorkout format
  ai.py                         # AI features (Claude)
  library.py                    # FitHub library + fork
  workout_manager.py            # Workout CRUD
  menus.py                      # CLI dispatcher
  art/                          # ASCII art data
workouts/                       # .workout.json files
  _template.workout.json        # Format template
  fithub--*.workout.json        # 11 library workouts
```
