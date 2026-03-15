"""Pydantic models for the GitFitHub API."""

from pydantic import BaseModel


class UserProfile(BaseModel):
    id: int | str
    username: str | None = None
    email: str | None = None
    name: str = "User"
    bio: str = ""
    joined: str = ""
    public_profile: bool = True
    share_activity: bool = True
    ai_provider: str = "anthropic"


class WorkoutSummary(BaseModel):
    slug: str
    name: str
    description: str = ""
    difficulty: str = "intermediate"
    rounds: int = 3
    exercise_count: int = 0
    tags: list[str] = []


class ExerciseInfo(BaseModel):
    slug: str
    name: str
    description: str = ""
    muscle_groups: list[str] = []
    default_mode: str = "time"
    default_value: int = 30
    variant_count: int = 0
    variants: list | None = None
    tips: list[str] | None = None


class StatsResponse(BaseModel):
    completed_sessions: int = 0
    xp: int = 0
    level: int = 1
    level_title: str = "Couch Potato"
    current_streak: int = 0
    longest_streak: int = 0
    workout_count: int = 0
    achievement_count: int = 0


# ── Auth models ──────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username_or_email: str
    password: str


class AuthResponse(BaseModel):
    user: UserProfile
    token: str


class CLITokenCreate(BaseModel):
    name: str = "CLI Token"


class CLITokenResponse(BaseModel):
    token: str
    token_hash: str


class CLITokenListItem(BaseModel):
    token_hash: str
    name: str
    created_at: str
    last_used: str | None = None
    token_prefix: str


class ProfileUpdate(BaseModel):
    name: str | None = None
    bio: str | None = None
    email: str | None = None
    public_profile: bool | None = None
    share_activity: bool | None = None
    ai_provider: str | None = None
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class PublicProfile(BaseModel):
    username: str
    name: str
    bio: str
    joined: str
    level: int
    level_title: str
    completed_sessions: int
    xp: int
    current_streak: int
    longest_streak: int
    public_workouts: list = []


class ActivityDay(BaseModel):
    date: str
    count: int


class SyncRequest(BaseModel):
    stats: dict | None = None
    history: list | None = None
    workouts: list | None = None
