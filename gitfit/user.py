"""User identity, profile management, auth tokens, and account linking."""

import json
import uuid
import secrets
import hashlib
from datetime import datetime, timezone
from pathlib import Path

from gitfit.config import APP_DIR, console, _load_json, _save_json, C_DONE, C_TITLE, C_EXERCISE, C_PROGRESS, C_BORDER
from gitfit.animation import prompt_enter

USER_FILE = APP_DIR / "user.json"


def _default_user():
    return {
        "id": str(uuid.uuid4()),
        "username": None,
        "name": "User",
        "bio": "",
        "joined": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "auth_token": None,
        "cli_token": None,
        "linked_username": None,
        "public_profile": True,
        "share_activity": True,
    }


def ensure_user():
    """Create user identity if not exists. Returns user dict."""
    APP_DIR.mkdir(parents=True, exist_ok=True)
    if USER_FILE.exists():
        user = _load_json(USER_FILE, _default_user())
        # Ensure all fields exist (migration)
        defaults = _default_user()
        for k, v in defaults.items():
            if k not in user:
                user[k] = v if k != "id" else str(uuid.uuid4())
        return user
    user = _default_user()
    _save_json(USER_FILE, user)
    return user


def get_user():
    """Get current user profile."""
    return ensure_user()


def save_user(user):
    """Persist user data."""
    _save_json(USER_FILE, user)


def generate_token():
    """Generate a new API auth token for the user."""
    user = get_user()
    raw_token = secrets.token_urlsafe(32)
    user["auth_token"] = f"gitfit_{raw_token}"
    save_user(user)
    return user["auth_token"]


def get_token():
    """Get current auth token, or None."""
    user = get_user()
    return user.get("auth_token")


def validate_token(token):
    """Validate a token against the stored user token."""
    user = get_user()
    stored = user.get("auth_token")
    if not stored or not token:
        return False
    return secrets.compare_digest(stored, token)


def cmd_whoami():
    """Display current user identity."""
    user = get_user()
    console.print(f"\n  User ID  : [dim]{user['id']}[/dim]")
    if user.get("username"):
        console.print(f"  Username : [{C_EXERCISE}]{user['username']}[/{C_EXERCISE}]")
    console.print(f"  Name     : [{C_EXERCISE}]{user.get('name', 'User')}[/{C_EXERCISE}]")
    if user.get("bio"):
        console.print(f"  Bio      : {user['bio']}")
    console.print(f"  Joined   : {user.get('joined', '?')}")
    token = user.get("auth_token")
    if token:
        console.print(f"  Token    : [{C_DONE}]{token[:12]}...{token[-4:]}[/{C_DONE}]")
    else:
        console.print(f"  Token    : [dim]not generated[/dim]")
    if user.get("linked_username"):
        console.print(f"  Linked   : [{C_DONE}]{user['linked_username']}[/{C_DONE}]")
    elif user.get("cli_token"):
        console.print(f"  CLI Link : [{C_DONE}]connected[/{C_DONE}]")
    else:
        console.print(f"  CLI Link : [dim]not linked[/dim]")
    console.print(f"  Profile  : [dim]{USER_FILE}[/dim]\n")


def cmd_edit_profile():
    """Interactive profile editor."""
    user = get_user()
    console.print(f"\n[{C_TITLE}]  Edit Profile[/{C_TITLE}]")
    console.print(f"  [dim]Press Enter to keep current value.[/dim]\n")

    new_username = input(f"  Username [{user.get('username') or 'not set'}]: ").strip()
    if new_username:
        user["username"] = new_username

    new_name = input(f"  Display name [{user.get('name', 'User')}]: ").strip()
    if new_name:
        user["name"] = new_name

    new_bio = input(f"  Bio [{user.get('bio') or 'none'}]: ").strip()
    if new_bio:
        user["bio"] = new_bio

    pub = input(f"  Public profile? (y/n) [{'y' if user.get('public_profile', True) else 'n'}]: ").strip().lower()
    if pub in ("y", "n"):
        user["public_profile"] = pub == "y"

    share = input(f"  Share activity? (y/n) [{'y' if user.get('share_activity', True) else 'n'}]: ").strip().lower()
    if share in ("y", "n"):
        user["share_activity"] = share == "y"

    save_user(user)

    # Also sync name to config
    from gitfit.config import load_config, save_config
    config = load_config()
    config["profile"]["name"] = user["name"]
    save_config(config)

    console.print(f"\n  [{C_DONE}]Profile updated![/{C_DONE}]\n")


def cmd_auth():
    """Auth token management."""
    user = get_user()
    token = user.get("auth_token")

    console.print(f"\n[{C_TITLE}]  Auth Token[/{C_TITLE}]\n")

    if token:
        console.print(f"  Current token: [{C_DONE}]{token[:12]}...{token[-4:]}[/{C_DONE}]")
        console.print(f"  [dim]Use this token to authenticate with the GitFitHub API.[/dim]\n")
        regen = input("  Regenerate token? (y/N): ").strip().lower()
        if regen == "y":
            new_token = generate_token()
            console.print(f"\n  [{C_DONE}]New token generated![/{C_DONE}]")
            console.print(f"  Token: [{C_EXERCISE}]{new_token}[/{C_EXERCISE}]")
            console.print(f"  [red]Save this token -- it won't be shown in full again.[/red]\n")
    else:
        console.print(f"  [dim]No auth token generated yet.[/dim]\n")
        gen = input("  Generate a token? (y/N): ").strip().lower()
        if gen == "y":
            new_token = generate_token()
            console.print(f"\n  [{C_DONE}]Token generated![/{C_DONE}]")
            console.print(f"  Token: [{C_EXERCISE}]{new_token}[/{C_EXERCISE}]")
            console.print(f"  [red]Save this token -- it won't be shown in full again.[/red]\n")


def cmd_link(token):
    """Link this CLI to a GitFitHub web account using a CLI token."""
    if not token:
        console.print("[red]Usage: python app.py link <token>[/red]")
        console.print("  Generate a CLI token at your GitFitHub Settings page.")
        return

    if not token.startswith("gitfit_"):
        console.print("[red]Invalid token format. CLI tokens start with 'gitfit_'[/red]")
        return

    # Validate the token against the API
    import os
    api_url = os.environ.get("GITFIT_API_URL", "http://localhost:8000")

    console.print(f"\n  Validating token against {api_url}...")

    try:
        import urllib.request
        import urllib.error
        req = urllib.request.Request(
            f"{api_url}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            username = data.get("username", "unknown")
    except Exception as e:
        console.print(f"[red]  Could not validate token: {e}[/red]")
        console.print("  [dim]Make sure the GitFitHub API is running.[/dim]")
        save_anyway = input("  Save token locally anyway? (y/N): ").strip().lower()
        if save_anyway != "y":
            return
        username = None

    # Store the CLI token
    user = get_user()
    user["cli_token"] = token
    if username:
        user["linked_username"] = username
    save_user(user)

    if username:
        console.print(f"\n  [{C_DONE}]Linked to @{username}![/{C_DONE}]")
    else:
        console.print(f"\n  [{C_DONE}]Token saved locally.[/{C_DONE}]")
    console.print(f"  Use [bright_cyan]python app.py push[/bright_cyan] to sync your data.\n")


def cmd_push():
    """Push local workout data to the GitFitHub web account."""
    user = get_user()
    cli_token = user.get("cli_token")

    if not cli_token:
        console.print("[red]Not linked to a GitFitHub account.[/red]")
        console.print("  Use [bright_cyan]python app.py link <token>[/bright_cyan] first.")
        return

    import os
    api_url = os.environ.get("GITFIT_API_URL", "http://localhost:8000")

    from gitfit.state import load_state
    from gitfit.config import load_config

    state = load_state()
    config = load_config()

    # Build sync payload
    stats = {
        "completed_sessions": state.get("completed_sessions", 0),
        "xp": state.get("xp", 0),
        "level": state.get("level", 1),
        "level_title": state.get("level_title", "Couch Potato"),
        "current_streak": state.get("current_streak", 0),
        "longest_streak": state.get("longest_streak", 0),
    }

    history = state.get("history", [])

    workouts = []
    for w in config.get("workouts", []):
        entry = {
            "slug": w.get("name", "").lower().replace(" ", "-"),
            "workout": w,
            "forked_from": w.get("_meta", {}).get("forked_from"),
        }
        workouts.append(entry)

    payload = json.dumps({
        "stats": stats,
        "history": history,
        "workouts": workouts,
    }).encode()

    console.print(f"\n  Syncing to {api_url}...")
    console.print(f"  Stats: {stats['completed_sessions']} sessions, {stats['xp']} XP, Lv.{stats['level']}")
    console.print(f"  History: {len(history)} entries")
    console.print(f"  Workouts: {len(workouts)} configs")

    try:
        import urllib.request
        import urllib.error
        req = urllib.request.Request(
            f"{api_url}/me/sync",
            data=payload,
            headers={
                "Authorization": f"Bearer {cli_token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            if result.get("ok"):
                console.print(f"\n  [{C_DONE}]Push complete![/{C_DONE}]")
                linked = user.get("linked_username")
                if linked:
                    console.print(f"  View your profile at: [bright_cyan]/user/{linked}[/bright_cyan]\n")
            else:
                console.print(f"[red]  Sync returned unexpected response.[/red]")
    except urllib.error.HTTPError as e:
        console.print(f"[red]  Push failed: {e.code} {e.reason}[/red]")
        if e.code == 401:
            console.print("  [dim]Token may be expired. Generate a new one at Settings.[/dim]")
    except Exception as e:
        console.print(f"[red]  Push failed: {e}[/red]")
