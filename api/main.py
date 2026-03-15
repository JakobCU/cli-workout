"""GitFitHub API -- backend for the workout platform."""

import sys
from pathlib import Path
# Ensure project root is on sys.path so both `cd api && uvicorn main:app`
# and `uvicorn api.main:app` work.
_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from api.models import (
    UserProfile, WorkoutSummary, ExerciseInfo, StatsResponse,
    RegisterRequest, LoginRequest, AuthResponse,
    CLITokenCreate, CLITokenResponse, CLITokenListItem,
    ProfileUpdate, PasswordChange, PublicProfile, ActivityDay, SyncRequest,
)
from api.auth import verify_token
from api.database import (
    init_db, create_user, authenticate_user, get_user_by_id, get_user_by_username,
    update_user, update_password, delete_user,
    create_cli_token, list_cli_tokens, revoke_cli_token,
    get_user_stats, get_user_activity, get_user_workouts, sync_user_data,
)
from api.jwt_auth import create_jwt

app = FastAPI(
    title="GitFitHub API",
    description="GitHub for Workouts -- API backend",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Init DB on startup
@app.on_event("startup")
def startup():
    init_db()
    print(f"[startup] GitFitHub API v0.3.0 ready")


# ── Auth dependency ──────────────────────────────────────────────────
async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    token = authorization.replace("Bearer ", "")
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


# ── WebSocket terminal (live demo) ───────────────────────────────────
from fastapi import WebSocket as _WebSocket
from api.terminal import websocket_terminal

@app.websocket("/ws/terminal")
async def ws_terminal(ws: _WebSocket):
    await websocket_terminal(ws)


# ── Public endpoints ─────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"name": "GitFitHub API", "version": "0.2.0", "status": "ok"}


@app.get("/exercises", response_model=list[ExerciseInfo])
async def list_exercises():
    """List all exercises in the catalog."""
    from gitfit.exercise_catalog import EXERCISE_CATALOG
    exercises = []
    for slug, data in EXERCISE_CATALOG.items():
        exercises.append(ExerciseInfo(
            slug=slug,
            name=data["name"],
            description=data.get("description", ""),
            muscle_groups=data.get("muscle_groups", []),
            default_mode=data.get("default_mode", "time"),
            default_value=data.get("default_value", 30),
            variant_count=len(data.get("variants", [])),
        ))
    return exercises


@app.get("/exercises/{slug}", response_model=ExerciseInfo)
async def get_exercise(slug: str):
    """Get exercise details by slug."""
    from gitfit.exercise_catalog import get_exercise as _get_exercise
    data = _get_exercise(slug)
    if not data:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return ExerciseInfo(
        slug=data.get("slug", slug),
        name=data["name"],
        description=data.get("description", ""),
        muscle_groups=data.get("muscle_groups", []),
        default_mode=data.get("default_mode", "time"),
        default_value=data.get("default_value", 30),
        variant_count=len(data.get("variants", [])),
        variants=data.get("variants"),
        tips=data.get("tips"),
    )


@app.get("/workouts")
async def list_workouts():
    """List all library workouts."""
    from gitfit.library import _load_library
    library = _load_library()
    workouts = []
    for slug, data in library.items():
        workouts.append(WorkoutSummary(
            slug=slug,
            name=data.get("name", slug),
            description=data.get("description", ""),
            difficulty=data.get("difficulty", "intermediate"),
            rounds=data.get("rounds", 3),
            exercise_count=len(data.get("exercises", [])),
            tags=data.get("tags", []),
        ))
    return workouts


@app.get("/workouts/{slug}")
async def get_workout(slug: str):
    """Get full workout details by slug."""
    from gitfit.library import _load_library
    library = _load_library()
    if slug not in library:
        slug_full = f"gitfit/{slug}"
        if slug_full in library:
            slug = slug_full
        else:
            raise HTTPException(status_code=404, detail="Workout not found")
    return library[slug]


# ── Auth endpoints ───────────────────────────────────────────────────

@app.post("/auth/register", response_model=AuthResponse)
async def register(req: RegisterRequest):
    """Register a new user."""
    from api.password import hash_password
    if len(req.username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    try:
        password_hash = hash_password(req.password)
        user = create_user(req.username, req.email, password_hash)
        token = create_jwt(user["id"], user["username"])
        return AuthResponse(
            user=UserProfile(
                id=user["id"], username=user["username"], email=user["email"],
                name=user["name"], bio=user["bio"], joined=user["joined"],
                public_profile=bool(user["public_profile"]),
                share_activity=bool(user["share_activity"]),
                ai_provider=user.get("ai_provider", "anthropic"),
            ),
            token=token,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    """Login with username/email + password."""
    from api.password import verify_password
    user = authenticate_user(req.username_or_email, None)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_jwt(user["id"], user["username"])
    return AuthResponse(
        user=UserProfile(
            id=user["id"], username=user["username"], email=user["email"],
            name=user["name"], bio=user["bio"], joined=user["joined"],
            public_profile=bool(user["public_profile"]),
            share_activity=bool(user["share_activity"]),
            ai_provider=user.get("ai_provider", "anthropic"),
        ),
        token=token,
    )


@app.get("/auth/me", response_model=UserProfile)
async def get_me(user=Depends(get_current_user)):
    """Get current user profile."""
    return UserProfile(
        id=user["id"], username=user.get("username"), email=user.get("email"),
        name=user.get("name", "User"), bio=user.get("bio", ""),
        joined=user.get("joined", ""),
        public_profile=bool(user.get("public_profile", True)),
        share_activity=bool(user.get("share_activity", True)),
        ai_provider=user.get("ai_provider", "anthropic"),
    )


@app.patch("/auth/me", response_model=UserProfile)
async def update_me(req: ProfileUpdate, user=Depends(get_current_user)):
    """Update current user's profile."""
    fields = req.model_dump(exclude_none=True)
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    try:
        updated = update_user(user["id"], **fields)
        if not updated:
            raise HTTPException(status_code=404, detail="User not found")
        return UserProfile(
            id=updated["id"], username=updated["username"], email=updated.get("email"),
            name=updated.get("name", "User"), bio=updated.get("bio", ""),
            joined=updated.get("joined", ""),
            public_profile=bool(updated.get("public_profile", True)),
            share_activity=bool(updated.get("share_activity", True)),
            ai_provider=updated.get("ai_provider", "anthropic"),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.patch("/auth/password")
async def change_password(req: PasswordChange, user=Depends(get_current_user)):
    """Change password."""
    from api.password import hash_password, verify_password
    if not verify_password(req.current_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(req.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")
    new_hash = hash_password(req.new_password)
    update_password(user["id"], new_hash)
    return {"ok": True}


@app.delete("/auth/me")
async def delete_me(user=Depends(get_current_user)):
    """Delete current user account."""
    delete_user(user["id"])
    return {"ok": True}


# ── CLI Token endpoints ──────────────────────────────────────────────

@app.post("/auth/cli-tokens", response_model=CLITokenResponse)
async def create_token(req: CLITokenCreate, user=Depends(get_current_user)):
    """Generate a new CLI token."""
    import hashlib
    raw = create_cli_token(user["id"], req.name)
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    return CLITokenResponse(token=raw, token_hash=token_hash)


@app.get("/auth/cli-tokens", response_model=list[CLITokenListItem])
async def list_tokens(user=Depends(get_current_user)):
    """List all CLI tokens."""
    tokens = list_cli_tokens(user["id"])
    return [CLITokenListItem(**t) for t in tokens]


@app.delete("/auth/cli-tokens/{token_hash}")
async def revoke_token(token_hash: str, user=Depends(get_current_user)):
    """Revoke a CLI token."""
    if not revoke_cli_token(user["id"], token_hash):
        raise HTTPException(status_code=404, detail="Token not found")
    return {"ok": True}


# ── Public profile endpoints ─────────────────────────────────────────

@app.get("/users/{username}", response_model=PublicProfile)
async def get_public_profile(username: str):
    """Get a user's public profile."""
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.get("public_profile", True):
        raise HTTPException(status_code=404, detail="User not found")

    stats = get_user_stats(user["id"])
    workouts = get_user_workouts(user["id"], public_only=True)

    return PublicProfile(
        username=user["username"],
        name=user.get("name", "User"),
        bio=user.get("bio", ""),
        joined=user.get("joined", ""),
        level=stats.get("level", 1),
        level_title=stats.get("level_title", "Couch Potato"),
        completed_sessions=stats.get("completed_sessions", 0),
        xp=stats.get("xp", 0),
        current_streak=stats.get("current_streak", 0),
        longest_streak=stats.get("longest_streak", 0),
        public_workouts=workouts,
    )


@app.get("/users/{username}/activity", response_model=list[ActivityDay])
async def get_user_activity_endpoint(username: str):
    """Get user's activity data."""
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.get("share_activity", True):
        return []
    activity = get_user_activity(user["id"])
    return [ActivityDay(**a) for a in activity]


# ── Sync endpoint (CLI push) ────────────────────────────────────────

@app.post("/me/sync")
async def sync_data(req: SyncRequest, user=Depends(get_current_user)):
    """Bulk sync data from CLI (push)."""
    sync_user_data(user["id"], stats=req.stats, history=req.history, workouts=req.workouts)
    return {"ok": True, "synced": True}


# ── Legacy authenticated endpoints ──────────────────────────────────

@app.get("/me", response_model=UserProfile)
async def get_my_profile(user=Depends(get_current_user)):
    """Get current user's profile (legacy)."""
    return UserProfile(
        id=user["id"], username=user.get("username"),
        name=user.get("name", "User"), bio=user.get("bio", ""),
        joined=user.get("joined", ""),
        public_profile=bool(user.get("public_profile", True)),
        share_activity=bool(user.get("share_activity", True)),
        ai_provider=user.get("ai_provider", "anthropic"),
    )


@app.get("/me/stats", response_model=StatsResponse)
async def get_my_stats(user=Depends(get_current_user)):
    """Get current user's workout stats."""
    # Try DB stats first
    if isinstance(user.get("id"), int):
        stats = get_user_stats(user["id"])
        if stats.get("completed_sessions", 0) > 0:
            return StatsResponse(**{k: v for k, v in stats.items() if k != "user_id"})

    # Fall back to local state
    from gitfit.state import load_state
    from gitfit.config import load_config
    state = load_state()
    config = load_config()
    return StatsResponse(
        completed_sessions=state.get("completed_sessions", 0),
        xp=state.get("xp", 0),
        level=state.get("level", 1),
        level_title=state.get("level_title", "Couch Potato"),
        current_streak=state.get("current_streak", 0),
        longest_streak=state.get("longest_streak", 0),
        workout_count=len(config.get("workouts", [])),
        achievement_count=len(state.get("achievements", [])),
    )


@app.get("/me/history")
async def get_my_history(limit: int = 20, user=Depends(get_current_user)):
    """Get current user's workout history."""
    from gitfit.state import load_state
    state = load_state()
    history = state.get("history", [])
    return history[-limit:]


@app.get("/me/workouts")
async def get_my_workouts(user=Depends(get_current_user)):
    """Get current user's configured workouts."""
    from gitfit.config import load_config
    config = load_config()
    return config.get("workouts", [])
