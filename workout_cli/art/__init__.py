"""ASCII art subpackage -- re-exports merged frames dict."""

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
