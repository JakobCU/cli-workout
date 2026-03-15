"""AI features: coaching, workout generation, and adaptation."""

import json
import os
import re
from pathlib import Path

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from gitfit.config import (
    console, CONFIG_FILE, HAS_ANTHROPIC, HAS_OPENAI,
    C_BORDER, C_DONE, C_EXERCISE, C_FIRE, C_PROGRESS, C_SUBTITLE, C_TITLE,
    get_api_key, get_openai_key, save_config,
)
from gitfit.art import get_evolution_stage
from gitfit.progression import ACHIEVEMENTS
from gitfit.animation import prompt_enter
from gitfit.ai_providers import get_provider


def _require_ai(config):
    """Check AI provider availability. Returns (provider, True) or (None, False)."""
    provider, ok = get_provider(config)
    if ok:
        return provider, True

    provider_name = config.get("settings", {}).get("ai_provider", "anthropic")

    if provider_name == "openai":
        if not HAS_OPENAI:
            console.print("[red]openai package not installed.[/red]")
            console.print("  Run: [bright_cyan]pip install openai[/bright_cyan]")
            return None, False
        key = get_openai_key(config)
        if not key:
            console.print("[red]No OpenAI API key found.[/red]")
            console.print()
            setup = input("  Would you like to set up your API key now? (y/N): ").strip().lower()
            if setup == "y":
                cmd_setup_key()
                provider, ok = get_provider(config)
                if ok:
                    return provider, True
            return None, False
    else:
        if not HAS_ANTHROPIC:
            console.print("[red]anthropic package not installed.[/red]")
            console.print("  Run: [bright_cyan]pip install anthropic[/bright_cyan]")
            return None, False
        key = get_api_key(config)
        if not key:
            console.print("[red]No API key found.[/red]")
            console.print()
            setup = input("  Would you like to set up your API key now? (y/N): ").strip().lower()
            if setup == "y":
                cmd_setup_key()
                provider, ok = get_provider(config)
                if ok:
                    return provider, True
            return None, False

    return None, False


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
    provider, ok = _require_ai(config)
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

    system_prompt = (
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
    )
    user_message = f"Here's my workout data:\n\n{context}\n\nCoach me, Blobby!"

    try:
        for text in provider.chat_stream(system_prompt, user_message, max_tokens=800):
            console.print(text, end="")
    except Exception as e:
        console.print(f"\n[red]API error: {e}[/red]")
        return

    console.print("\n")
    prompt_enter()


def cmd_generate(config, state, prompt):
    """AI workout generation: describe what you want, get a workout config."""
    provider, ok = _require_ai(config)
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

    system_prompt = (
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
    )
    user_message = (
        f"User request: {prompt}\n\n"
        f"User context (for scaling difficulty):\n{context}"
    )

    try:
        raw = provider.chat(system_prompt, user_message, max_tokens=1000)
    except Exception as e:
        console.print(f"[red]API error: {e}[/red]")
        return

    raw = raw.strip()

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
        save_config(config)
        console.print(f"[{C_DONE}]Workout '{workout['name']}' added![/{C_DONE}]")
    else:
        console.print("[dim]Cancelled.[/dim]")
    prompt_enter()


def cmd_adapt(config, state):
    """AI-powered adaptation: analyze progress and tweak existing workouts."""
    provider, ok = _require_ai(config)
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

    system_prompt = (
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
    )
    user_message = (
        f"User context:\n{context}\n\n"
        f"Current workout configs:\n{workouts_json}\n\n"
        "Analyze and suggest adaptations."
    )

    try:
        raw = provider.chat(system_prompt, user_message, max_tokens=2000)
    except Exception as e:
        console.print(f"[red]API error: {e}[/red]")
        return

    raw = raw.strip()

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
        save_config(config)
        console.print(f"[{C_DONE}]Workouts adapted![/{C_DONE}]")
    else:
        console.print("[dim]Cancelled.[/dim]")
    prompt_enter()


def cmd_generate_exercise(config, state, prompt):
    """AI exercise generation: describe an exercise, get a full .exercise.gitfit."""
    provider, ok = _require_ai(config)
    if not ok:
        return
    if not prompt:
        console.print("[red]Usage: python app.py generate-exercise \"burpees\"[/red]")
        console.print()
        console.print("  Examples:")
        console.print('    python app.py generate-exercise "burpees with jump"')
        console.print('    python app.py generate-exercise "mountain climbers"')
        console.print('    python app.py generate-exercise "tricep dips using a chair"')
        return

    from gitfit.exercise_catalog import EXERCISE_CATALOG, reload_catalog

    existing = [e["name"] for e in EXERCISE_CATALOG.values()]
    evo = get_evolution_stage(state)
    console.print(f"\n  [{evo['color']}]Blobby is designing your exercise...[/{evo['color']}]\n")

    system_prompt = (
        "Generate an exercise definition as JSON. Output ONLY valid JSON, "
        "no markdown, no code fences, no explanation.\n\n"
        "Format:\n"
        "{\n"
        '  "name": "Exercise Name",\n'
        '  "slug": "exercise-name",\n'
        '  "description": "1-2 sentence description of the movement and what it targets.",\n'
        '  "muscle_groups": ["primary", "secondary"],\n'
        '  "default_mode": "time",\n'
        '  "default_value": 30,\n'
        '  "animation_key": "closest existing exercise or null",\n'
        '  "tips": ["tip 1", "tip 2", "tip 3"],\n'
        '  "variants": [\n'
        '    {"name": "Variant Name", "slug": "variant-slug", '
        '"description": "...", "muscle_groups": ["..."], "default_value": 25}\n'
        "  ]\n"
        "}\n\n"
        "Rules:\n"
        '- slug must be lowercase with hyphens, no spaces\n'
        '- default_mode is "time" (seconds) or "reps" (count)\n'
        '- default_value: 15-60 for time, 8-20 for reps\n'
        '- muscle_groups: use lowercase (chest, shoulders, triceps, quads, '
        'glutes, hamstrings, core, obliques, lower back, calves, hip flexors, adductors, lats)\n'
        '- animation_key: pick the closest match from these existing animations: '
        'Push-Ups, Squats, Plank, Reverse Lunges, Superman, '
        'Side Plank Left, Side Plank Right, Glute Bridge, Bird Dog. '
        'Use null if none fits.\n'
        '- Include 1-3 variants (creative variations of the exercise)\n'
        '- 3 practical form tips\n'
        f'- Existing exercises to avoid duplicating: {existing}\n'
    )
    user_message = f"Create an exercise definition for: {prompt}"

    try:
        raw = provider.chat(system_prompt, user_message, max_tokens=1500)
    except Exception as e:
        console.print(f"[red]API error: {e}[/red]")
        return

    raw = raw.strip()

    # Parse JSON
    exercise = None
    for attempt in [raw, (re.search(r'\{.*\}', raw, re.DOTALL) or type('', (), {'group': lambda s: ''})()).group()]:
        if not attempt:
            continue
        try:
            exercise = json.loads(attempt)
            break
        except (json.JSONDecodeError, AttributeError):
            continue

    if not exercise:
        console.print(f"[red]Could not parse response as JSON:[/red]\n{raw[:500]}")
        return

    # Validate required fields
    required = ("name", "slug", "description", "muscle_groups")
    if not all(k in exercise for k in required):
        console.print("[red]Invalid exercise -- missing required fields.[/red]")
        return

    # Display
    console.print(f"  [{C_EXERCISE}]{exercise['name']}[/{C_EXERCISE}]")
    console.print(f"  [dim]{exercise.get('slug', '')}[/dim]\n")
    console.print(f"  {exercise.get('description', '')}\n")
    console.print(f"  Muscles: [{C_PROGRESS}]{', '.join(exercise.get('muscle_groups', []))}[/{C_PROGRESS}]")
    mode = exercise.get("default_mode", "time")
    val = exercise.get("default_value", 30)
    console.print(f"  Default: {val}{'s' if mode == 'time' else ' reps'}")

    anim = exercise.get("animation_key")
    if anim:
        console.print(f"  Animation: [{C_DONE}]{anim}[/{C_DONE}]")
    else:
        console.print(f"  Animation: [dim]none (will use REST fallback)[/dim]")

    tips = exercise.get("tips", [])
    if tips:
        console.print(f"\n  Tips:")
        for tip in tips:
            console.print(f"    - {tip}")

    variants = exercise.get("variants", [])
    if variants:
        console.print(f"\n  Variants:")
        for v in variants:
            console.print(f"    [{C_EXERCISE}]{v['name']}[/{C_EXERCISE}] -- {v.get('description', '')}")

    # Confirm save
    confirm = input(f"\n  Save to exercises/{exercise['slug']}.exercise.gitfit? (y/N): ").strip().lower()
    if confirm == "y":
        exercises_dir = Path(__file__).resolve().parent.parent / "exercises"
        exercises_dir.mkdir(exist_ok=True)
        out_path = exercises_dir / f"{exercise['slug']}.exercise.gitfit"

        if out_path.exists():
            overwrite = input(f"  File already exists. Overwrite? (y/N): ").strip().lower()
            if overwrite != "y":
                console.print("[dim]Cancelled.[/dim]")
                return

        out_path.write_text(
            json.dumps(exercise, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        reload_catalog()
        console.print(f"\n  [{C_DONE}]Exercise saved![/{C_DONE}]")
        console.print(f"  [dim]{out_path}[/dim]")
        console.print(f"  Use in workouts as: [bright_cyan]{exercise['name']}[/bright_cyan]")
    else:
        console.print("[dim]Cancelled.[/dim]")
    prompt_enter()


def cmd_setup_key():
    """Interactive API key setup -- writes to .env file."""
    from gitfit.config import load_config, save_config as _save_config
    config = load_config()
    current_provider = config.get("settings", {}).get("ai_provider", "anthropic")

    env_path = Path(__file__).resolve().parent.parent / ".env"
    console.clear()
    console.print(Panel(
        "[bold]AI Provider Setup[/bold]\n\n"
        "Blobby's AI features (coach, generate, adapt) need an API key.\n\n"
        f"  Current provider: [{C_DONE}]{current_provider}[/{C_DONE}]\n\n"
        "  [bright_cyan]1)[/bright_cyan]  Anthropic (Claude) -- recommended\n"
        "  [bright_cyan]2)[/bright_cyan]  OpenAI (GPT-4o)\n\n"
        f"Keys are saved to: [dim]{env_path}[/dim]\n"
        "This file is in .gitignore and won't be committed.",
        title=f"[{C_TITLE}]AI Setup[/{C_TITLE}]",
        border_style=C_BORDER,
        padding=(1, 2),
    ))

    choice = input("\n  Select provider (1/2) or Enter to keep current: ").strip()
    if choice == "1":
        provider = "anthropic"
    elif choice == "2":
        provider = "openai"
    else:
        provider = current_provider

    # Update provider in config
    config["settings"]["ai_provider"] = provider
    _save_config(config)

    if provider == "anthropic":
        env_var = "ANTHROPIC_API_KEY"
        prefix = "sk-ant-"
        current = os.environ.get("ANTHROPIC_API_KEY")
        console.print(f"\n  Provider: [{C_DONE}]Anthropic (Claude)[/{C_DONE}]")
        console.print("  Get a key at [bright_cyan]console.anthropic.com[/bright_cyan]")
    else:
        env_var = "OPENAI_API_KEY"
        prefix = "sk-"
        current = os.environ.get("OPENAI_API_KEY")
        console.print(f"\n  Provider: [{C_DONE}]OpenAI (GPT-4o)[/{C_DONE}]")
        console.print("  Get a key at [bright_cyan]platform.openai.com[/bright_cyan]")

    if current:
        masked = current[:12] + "..." + current[-4:]
        console.print(f"\n  Current key: [{C_DONE}]{masked}[/{C_DONE}]")
        console.print("  [dim]Enter a new key to replace, or press Enter to keep it.[/dim]")

    key = input("\n  Paste API key (or Enter to cancel): ").strip()
    if not key:
        console.print("[dim]  Cancelled.[/dim]")
        return

    if provider == "anthropic" and not key.startswith("sk-ant-"):
        console.print("[red]  That doesn't look like an Anthropic API key (should start with sk-ant-)[/red]")
        confirm = input("  Save anyway? (y/N): ").strip().lower()
        if confirm != "y":
            console.print("[dim]  Cancelled.[/dim]")
            return
    elif provider == "openai" and not key.startswith("sk-"):
        console.print("[red]  That doesn't look like an OpenAI API key (should start with sk-)[/red]")
        confirm = input("  Save anyway? (y/N): ").strip().lower()
        if confirm != "y":
            console.print("[dim]  Cancelled.[/dim]")
            return

    # Write to .env
    lines = []
    replaced = False
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith(f"{env_var}="):
                lines.append(f"{env_var}={key}")
                replaced = True
            else:
                lines.append(line)
    if not replaced:
        lines.append(f"{env_var}={key}")

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.environ[env_var] = key

    masked = key[:12] + "..." + key[-4:]
    console.print(f"\n  [{C_DONE}]Key saved![/{C_DONE}]  {masked}")
    console.print(f"  [dim]Written to {env_path}[/dim]")


def cmd_ai_provider(config, provider_arg=None):
    """Switch or show active AI provider."""
    current = config.get("settings", {}).get("ai_provider", "anthropic")

    if not provider_arg:
        console.print(f"\n  Active AI provider: [{C_DONE}]{current}[/{C_DONE}]")
        console.print(f"  [dim]Use: python app.py ai-provider [anthropic|openai][/dim]\n")
        return

    provider_arg = provider_arg.lower()
    if provider_arg not in ("anthropic", "openai"):
        console.print(f"[red]Unknown provider: {provider_arg}[/red]")
        console.print("  Valid options: anthropic, openai")
        return

    config["settings"]["ai_provider"] = provider_arg
    save_config(config)
    console.print(f"  [{C_DONE}]AI provider set to: {provider_arg}[/{C_DONE}]")
