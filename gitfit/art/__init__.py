"""ASCII art subpackage -- re-exports merged frames dict."""

import json
from pathlib import Path

from .exercise_frames import EXERCISE_FRAMES
from .special_frames import SPECIAL_FRAMES
from .blobby_evolution import (
    EVOLUTION_STAGES,
    get_evolution_stage,
    get_evolution_stage_by_index,
)
from .digits import (
    _DIGIT_ART,
    _FLAME_FRAMES,
    _EMBER_FRAMES,
    render_big_time,
)

# Load custom AI-generated frames
_custom_dir = Path(__file__).parent / "custom"
if _custom_dir.is_dir():
    for f in _custom_dir.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            name = data.get("name")
            frames = data.get("frames", [])
            if name and frames:
                EXERCISE_FRAMES[name] = frames
        except (json.JSONDecodeError, OSError):
            pass

ASCII_FRAMES = {**EXERCISE_FRAMES, **SPECIAL_FRAMES}

__all__ = [
    "ASCII_FRAMES",
    "EXERCISE_FRAMES",
    "SPECIAL_FRAMES",
    "EVOLUTION_STAGES",
    "get_evolution_stage",
    "get_evolution_stage_by_index",
    "_DIGIT_ART",
    "_FLAME_FRAMES",
    "_EMBER_FRAMES",
    "render_big_time",
]
