"""Display screens: history, stats, profile, achievements, plan, export, etc."""

import csv
import io
import json
from datetime import datetime, timedelta

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from gitfit.config import (
    console, CONFIG_FILE, STATE_FILE,
    C_ACHIEVEMENT, C_BORDER, C_DONE, C_EXERCISE, C_FIRE, C_LEVEL,
    C_LOCKED, C_PROGRESS, C_REST, C_STREAK, C_SUBTITLE, C_TITLE, C_XP,
)
from gitfit.state import load_state, save_state
from gitfit.progression import (
    ACHIEVEMENTS, LEVEL_THRESHOLDS, get_random_encouragement,
)
from gitfit.animation import prompt_enter
from gitfit.meta import get_meta, has_fork_lineage


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


def cmd_profile(config, state):
    """Display user profile summary."""
    console.clear()
    from gitfit.art import get_evolution_stage

    evo = get_evolution_stage(state)
    output = Text()
    output.append(evo["frames"][0], style=evo["color"])
    output.append("\n\n")
    output.append(f"  Name   : ", style="white")
    output.append(f"{config['profile'].get('name', 'User')}\n", style=C_EXERCISE)
    output.append(f"  Level  : ", style="white")
    output.append(f"{state.get('level', 1)} - {state.get('level_title', 'Couch Potato')}\n", style=C_LEVEL)
    output.append(f"  XP     : ", style="white")
    output.append(f"{state.get('xp', 0)}\n", style=C_XP)
    output.append(f"  Streak : ", style="white")
    output.append(f"{state.get('current_streak', 0)} days\n", style=C_STREAK)
    output.append(f"  Sessions: ", style="white")
    output.append(f"{state.get('completed_sessions', 0)}\n", style=C_DONE)
    # User identity
    from gitfit.user import get_user
    user = get_user()
    if user.get("username"):
        output.append(f"  User   : ", style="white")
        output.append(f"@{user['username']}\n", style=C_PROGRESS)
    output.append(f"  ID     : ", style="white")
    output.append(f"{user['id'][:8]}...\n", style="dim")
    output.append(f"  Stage  : ", style="white")
    output.append(f"{evo['name']}\n", style=evo["color"])

    console.print(Panel(output, title=f"[{C_TITLE}]Profile[/{C_TITLE}]",
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


# ── Fork Tree ────────────────────────────────────────────────────────
def cmd_tree(config):
    """Show fork tree: library sources and their user forks."""
    from gitfit.library import _load_library
    from gitfit.exercises import _estimate_workout_duration

    library = _load_library()
    workouts = config["workouts"]

    # Group user workouts by forked_from source
    tree = {}  # source_slug -> list of (workout, meta)
    orphans = []

    for w in workouts:
        meta = get_meta(w)
        if meta and meta.get("forked_from"):
            source = meta["forked_from"]
            tree.setdefault(source, []).append((w, meta))
        else:
            orphans.append(w)

    console.print(f"\n[{C_TITLE}]  Fork Tree[/{C_TITLE}]\n")

    for source_slug, forks in tree.items():
        # Show source from library if available
        source_data = library.get(source_slug)
        if source_data:
            dur = _estimate_workout_duration(source_data, config)
            console.print(
                f"  [{C_EXERCISE}]{source_slug}[/{C_EXERCISE}]  "
                f"[dim]({source_data.get('rounds', '?')}R, "
                f"{len(source_data.get('exercises', []))}ex, ~{dur}min)[/dim]"
            )
        else:
            console.print(f"  [{C_EXERCISE}]{source_slug}[/{C_EXERCISE}]  [dim](source not in library)[/dim]")

        for w, meta in forks:
            dur = _estimate_workout_duration(w, config)
            forked_date = meta.get("forked_at", "")[:10]
            ai_label = ""
            if meta.get("adapted_with"):
                ai_label = f', AI: "{meta["adapted_with"]}"'
            console.print(
                f"    |_ [{C_DONE}]{w['name']}[/{C_DONE}]  "
                f"[dim]({w.get('rounds', '?')}R, {len(w.get('exercises', []))}ex, ~{dur}min)[/dim]  "
                f"[dim][forked {forked_date}{ai_label}][/dim]"
            )
        console.print()

    if orphans:
        for w in orphans:
            dur = _estimate_workout_duration(w, config)
            console.print(
                f"  [{C_EXERCISE}]{w['name']}[/{C_EXERCISE}]  "
                f"[dim]({w.get('rounds', '?')}R, {len(w.get('exercises', []))}ex, ~{dur}min)[/dim]  "
                f"[dim](original, no fork history)[/dim]"
            )
        console.print()


# ── Diff ─────────────────────────────────────────────────────────────
def cmd_diff(config, idx_a, idx_b):
    """Compare two user workouts side-by-side."""
    workouts = config["workouts"]
    try:
        a_idx = int(idx_a) - 1
        b_idx = int(idx_b) - 1
    except (ValueError, TypeError):
        console.print("[red]Usage: python app.py diff <n> <m>[/red]")
        return

    if not (0 <= a_idx < len(workouts) and 0 <= b_idx < len(workouts)):
        console.print(f"[red]Invalid workout index. You have {len(workouts)} workouts.[/red]")
        return

    wa, wb = workouts[a_idx], workouts[b_idx]

    console.print(f"\n[{C_TITLE}]  Comparing:[/{C_TITLE}] "
                  f"[{C_EXERCISE}]{wa['name']}[/{C_EXERCISE}] vs "
                  f"[{C_EXERCISE}]{wb['name']}[/{C_EXERCISE}]\n")

    # Rounds diff
    ra, rb = wa.get("rounds", 3), wb.get("rounds", 3)
    if ra != rb:
        console.print(f"  Rounds: [{C_REST}]{ra}[/{C_REST}] -> [{C_DONE}]{rb}[/{C_DONE}]")
    else:
        console.print(f"  Rounds: {ra}")

    console.print(f"\n  Exercises:")

    exa = wa.get("exercises", [])
    exb = wb.get("exercises", [])

    # Build name-based matching, handling duplicates positionally
    name_counts_a = {}
    indexed_a = []
    for ex in exa:
        n = ex["name"]
        occ = name_counts_a.get(n, 0)
        name_counts_a[n] = occ + 1
        indexed_a.append((n, occ, ex))

    name_counts_b = {}
    indexed_b = []
    for ex in exb:
        n = ex["name"]
        occ = name_counts_b.get(n, 0)
        name_counts_b[n] = occ + 1
        indexed_b.append((n, occ, ex))

    matched_b = set()
    # Match exercises from A to B
    for name, occ, ex_a in indexed_a:
        match = None
        for j, (nb, ob, ex_b) in enumerate(indexed_b):
            if j not in matched_b and nb == name and ob == occ:
                match = (j, ex_b)
                break
        if match:
            j, ex_b = match
            matched_b.add(j)
            val_a = ex_a.get("value", 0)
            val_b = ex_b.get("value", 0)
            unit = "s" if ex_a.get("mode") == "time" else ""
            if val_a != val_b:
                diff = val_b - val_a
                sign = f"+{diff}" if diff > 0 else str(diff)
                color = C_DONE if diff > 0 else C_REST
                console.print(
                    f"    = {name:<20} {val_a}{unit} -> {val_b}{unit}  "
                    f"[{color}]({sign}{unit})[/{color}]")
            else:
                console.print(f"    = {name:<20} {val_a}{unit}")
        else:
            val_a = ex_a.get("value", 0)
            unit = "s" if ex_a.get("mode") == "time" else ""
            console.print(f"    [red]- {name:<20} {val_a}{unit} (removed)[/red]")

    # Show exercises only in B (added)
    for j, (nb, ob, ex_b) in enumerate(indexed_b):
        if j not in matched_b:
            val_b = ex_b.get("value", 0)
            unit = "s" if ex_b.get("mode") == "time" else ""
            console.print(f"    [{C_DONE}]+ {nb:<20} {val_b}{unit} (added)[/{C_DONE}]")

    console.print()


# ── Stars ────────────────────────────────────────────────────────────
def cmd_star(state, slug=None):
    """Toggle star on a library workout, or list all stars."""
    from gitfit.library import _load_library

    stars = state.get("stars", [])

    if slug is None:
        # List all stars
        if not stars:
            console.print("\n  [dim]No starred workouts. Use: python app.py star <slug>[/dim]")
            return
        library = _load_library()
        console.print(f"\n[{C_TITLE}]  Starred Workouts[/{C_TITLE}]\n")
        for s in stars:
            name = library.get(s, {}).get("name", s)
            console.print(f"  [bright_yellow]*[/bright_yellow] {name}  [dim]({s})[/dim]")
        console.print()
        return

    # Normalize slug
    library = _load_library()
    if slug not in library and f"gitfit/{slug}" in library:
        slug = f"gitfit/{slug}"
    if slug not in library:
        console.print(f"[red]Workout '{slug}' not found in library.[/red]")
        return

    if slug in stars:
        stars.remove(slug)
        state["stars"] = stars
        save_state(state)
        console.print(f"[{C_REST}]Unstarred: {library[slug].get('name', slug)}[/{C_REST}]")
    else:
        stars.append(slug)
        state["stars"] = stars
        save_state(state)
        console.print(f"[bright_yellow]Starred: {library[slug].get('name', slug)}[/bright_yellow]")


# ── Version History ──────────────────────────────────────────────────
def cmd_version_history(config, idx_str):
    """Show version history of a user workout."""
    workouts = config["workouts"]
    try:
        i = int(idx_str) - 1
    except (ValueError, TypeError):
        console.print("[red]Usage: python app.py versions <n>[/red]")
        return

    if not (0 <= i < len(workouts)):
        console.print(f"[red]Invalid workout index. You have {len(workouts)} workouts.[/red]")
        return

    workout = workouts[i]
    meta = get_meta(workout)

    if not meta:
        console.print(f"\n  [dim]{workout['name']} -- no version history (not a fork)[/dim]\n")
        return

    console.print(f"\n[{C_TITLE}]  Version History: {workout['name']}[/{C_TITLE}]")
    console.print(f"  Forked from: [{C_EXERCISE}]{meta.get('forked_from', '?')}[/{C_EXERCISE}]")
    console.print(f"  Current version: [{C_DONE}]{meta.get('version', 1)}[/{C_DONE}]\n")

    history = meta.get("history", [])
    for entry in history:
        v = entry.get("version", "?")
        date = entry.get("date", "?")
        changes = entry.get("changes", "")
        console.print(f"  [dim]v{v}[/dim]  {date}  {changes}")
    console.print()


# ── Exercise Catalog ─────────────────────────────────────────────────
def cmd_exercises(slug=None):
    """List all exercises or show details for one."""
    from gitfit.exercise_catalog import EXERCISE_CATALOG, get_exercise
    from gitfit.art import ASCII_FRAMES

    if slug:
        entry = get_exercise(slug)
        if not entry:
            console.print(f"[red]Exercise '{slug}' not found.[/red]")
            return

        console.print(f"\n[{C_TITLE}]  {entry['name']}[/{C_TITLE}]")
        console.print(f"  [dim]{entry.get('slug', '')}[/dim]\n")
        console.print(f"  {entry.get('description', '')}\n")

        # Show animation frame 0
        anim_key = entry.get("animation_key", entry["name"])
        frames = ASCII_FRAMES.get(anim_key)
        if frames:
            console.print(f"[{C_DONE}]{frames[0]}[/{C_DONE}]\n")

        # Muscle groups
        mgs = entry.get("muscle_groups", [])
        if mgs:
            console.print(f"  Muscle groups: [{C_EXERCISE}]{', '.join(mgs)}[/{C_EXERCISE}]")

        # Defaults
        console.print(f"  Default: {entry.get('default_value', 30)}"
                      f"{'s' if entry.get('default_mode') == 'time' else ' reps'}")

        # Tips
        tips = entry.get("tips", [])
        if tips:
            console.print(f"\n  [{C_PROGRESS}]Tips:[/{C_PROGRESS}]")
            for tip in tips:
                console.print(f"    - {tip}")

        # Variants
        variants = entry.get("variants", [])
        if variants:
            console.print(f"\n  [{C_PROGRESS}]Variants:[/{C_PROGRESS}]")
            for v in variants:
                console.print(
                    f"    [{C_EXERCISE}]{v['name']}[/{C_EXERCISE}]  "
                    f"[dim]{v.get('description', '')}[/dim]")
                vms = v.get("muscle_groups", [])
                if vms:
                    console.print(f"      Muscles: {', '.join(vms)}  "
                                  f"Default: {v.get('default_value', 30)}s")
        console.print()
        return

    # List all exercises
    if not EXERCISE_CATALOG:
        console.print("[dim]No exercises in catalog.[/dim]")
        return

    console.print(f"\n[{C_TITLE}]  Exercise Catalog[/{C_TITLE}]\n")
    for slug_key, entry in EXERCISE_CATALOG.items():
        mgs = entry.get("muscle_groups", [])
        variants = entry.get("variants", [])
        variant_label = f"  ({len(variants)} variants)" if variants else ""
        console.print(
            f"  [{C_EXERCISE}]{entry['name']}[/{C_EXERCISE}]  "
            f"[dim]{', '.join(mgs)}{variant_label}[/dim]"
        )
    console.print(f"\n  [dim]Use: python app.py exercises <slug> for details[/dim]\n")
