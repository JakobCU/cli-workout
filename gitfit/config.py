"""Configuration, paths, console singleton, theme colors, and API key helpers."""

import os
from pathlib import Path

from rich.console import Console

# ── .env loading ─────────────────────────────────────────────────────
def _load_dotenv():
    """Load .env file from the project root (parent of gitfit/)."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
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
    import anthropic  # noqa: F401
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    import openai  # noqa: F401
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

console = Console()

# ── Paths ────────────────────────────────────────────────────────────
APP_DIR = Path.home() / ".gitfit"
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
        "openai_api_key": None,
        "ai_provider": "anthropic",
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


# ── Config / State file helpers ──────────────────────────────────────
import json


def _load_json(path: Path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def _save_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def ensure_files():
    from gitfit.state import _default_state
    APP_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        _save_json(CONFIG_FILE, DEFAULT_CONFIG)
    if not STATE_FILE.exists():
        _save_json(STATE_FILE, _default_state())


def load_config():
    ensure_files()
    return _load_json(CONFIG_FILE, DEFAULT_CONFIG)


def save_config(config):
    _save_json(CONFIG_FILE, config)


# ── API key helpers ──────────────────────────────────────────────────
def get_api_key(config):
    """Get Anthropic API key from env (.env loaded at startup) or config."""
    return (os.environ.get("ANTHROPIC_API_KEY")
            or config["settings"].get("anthropic_api_key"))


def has_api_key(config):
    """Check if an API key is configured anywhere."""
    return bool(get_api_key(config))


def get_openai_key(config):
    """Get OpenAI API key from env or config."""
    return (os.environ.get("OPENAI_API_KEY")
            or config["settings"].get("openai_api_key"))


def has_openai_key(config):
    """Check if an OpenAI key is configured."""
    return bool(get_openai_key(config))
