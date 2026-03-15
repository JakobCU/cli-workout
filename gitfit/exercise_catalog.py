"""Exercise catalog: loads exercise definitions from exercises/*.exercise.gitfit."""

import json
from pathlib import Path


def _load_catalog():
    """Load all exercise definitions from exercises/ folder."""
    exercises_dir = Path(__file__).resolve().parent.parent / "exercises"
    catalog = {}
    if not exercises_dir.is_dir():
        return catalog
    for f in sorted(exercises_dir.glob("*.exercise.gitfit")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            slug = data.get("slug", f.stem.replace(".exercise", ""))
            catalog[slug] = data
        except (json.JSONDecodeError, OSError):
            pass
    return catalog


EXERCISE_CATALOG = _load_catalog()


def get_exercise(name_or_slug):
    """Look up an exercise by name or slug. Returns catalog entry or None."""
    # Try slug first
    if name_or_slug in EXERCISE_CATALOG:
        return EXERCISE_CATALOG[name_or_slug]
    # Try by name (case-sensitive)
    for entry in EXERCISE_CATALOG.values():
        if entry.get("name") == name_or_slug:
            return entry
    return None


def get_exercise_description(name):
    """Get description for an exercise, or empty string."""
    entry = get_exercise(name)
    return entry.get("description", "") if entry else ""


def get_exercise_tips(name):
    """Get tips for an exercise, or empty list."""
    entry = get_exercise(name)
    return entry.get("tips", []) if entry else []


def get_exercise_variants(name):
    """Get variants for an exercise, or empty list."""
    entry = get_exercise(name)
    return entry.get("variants", []) if entry else []


def get_animation_key(name):
    """Get the animation key for an exercise. Falls back to the name itself.
    Also registers inline animation_frames if present."""
    entry = get_exercise(name)
    if not entry:
        return name

    # If exercise has inline animation_frames, register them in the art system
    if entry.get("animation_frames"):
        from gitfit.art import EXERCISE_FRAMES
        if name not in EXERCISE_FRAMES:
            EXERCISE_FRAMES[name] = entry["animation_frames"]
        return name

    return entry.get("animation_key", name)


def catalog_names():
    """Return list of all exercise names from the catalog."""
    return [e["name"] for e in EXERCISE_CATALOG.values()]


def catalog_muscle_groups():
    """Return dict mapping exercise name -> muscle_groups from catalog."""
    return {
        e["name"]: e.get("muscle_groups", [])
        for e in EXERCISE_CATALOG.values()
    }


def reload_catalog():
    """Reload the catalog from disk (e.g. after AI generates a new exercise)."""
    global EXERCISE_CATALOG
    EXERCISE_CATALOG = _load_catalog()
