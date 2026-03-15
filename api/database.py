"""SQLite database layer for GitFitHub web accounts."""

import hashlib
import json
import os
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "gitfithub.db"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT DEFAULT 'User',
            bio TEXT DEFAULT '',
            joined TEXT NOT NULL,
            public_profile INTEGER DEFAULT 1,
            share_activity INTEGER DEFAULT 1,
            ai_provider TEXT DEFAULT 'anthropic',
            anthropic_api_key TEXT,
            openai_api_key TEXT
        );

        CREATE TABLE IF NOT EXISTS cli_tokens (
            token_hash TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name TEXT DEFAULT 'CLI Token',
            created_at TEXT NOT NULL,
            last_used TEXT,
            token_prefix TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS user_stats (
            user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            completed_sessions INTEGER DEFAULT 0,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            level_title TEXT DEFAULT 'Couch Potato',
            current_streak INTEGER DEFAULT 0,
            longest_streak INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS workout_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            date TEXT NOT NULL,
            workout_name TEXT NOT NULL,
            duration_min REAL DEFAULT 0,
            notes TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS user_workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            slug TEXT NOT NULL,
            workout_json TEXT NOT NULL,
            forked_from TEXT,
            is_public INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            UNIQUE(user_id, slug)
        );
    """)
    conn.close()


def create_user(username: str, email: str, password_hash: str) -> dict:
    """Create a new user. Returns user dict."""
    conn = _get_conn()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        cur = conn.execute(
            "INSERT INTO users (username, email, password_hash, joined) VALUES (?, ?, ?, ?)",
            (username, email.lower(), password_hash, now),
        )
        user_id = cur.lastrowid
        conn.execute(
            "INSERT INTO user_stats (user_id) VALUES (?)", (user_id,)
        )
        conn.commit()
        user = dict(conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone())
        conn.close()
        return user
    except sqlite3.IntegrityError as e:
        conn.close()
        err = str(e).lower()
        if "username" in err:
            raise ValueError("Username already taken")
        if "email" in err:
            raise ValueError("Email already registered")
        raise ValueError("Registration failed")


def authenticate_user(username_or_email: str, password_hash_fn) -> dict | None:
    """Look up user by username or email, verify password. Returns user dict or None.
    password_hash_fn should be a callable(stored_hash, plain_password) -> bool."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM users WHERE username=? OR email=?",
        (username_or_email, username_or_email.lower()),
    ).fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)


def get_user_by_id(user_id: int) -> dict | None:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_username(username: str) -> dict | None:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_user(user_id: int, **fields) -> dict | None:
    """Update user fields. Returns updated user."""
    allowed = {"name", "bio", "public_profile", "share_activity", "ai_provider",
               "anthropic_api_key", "openai_api_key", "email"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return get_user_by_id(user_id)
    conn = _get_conn()
    set_clause = ", ".join(f"{k}=?" for k in updates)
    values = list(updates.values()) + [user_id]
    try:
        conn.execute(f"UPDATE users SET {set_clause} WHERE id=?", values)
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        conn.close()
        return dict(row) if row else None
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError("Email already in use")


def update_password(user_id: int, new_password_hash: str):
    conn = _get_conn()
    conn.execute("UPDATE users SET password_hash=? WHERE id=?", (new_password_hash, user_id))
    conn.commit()
    conn.close()


def delete_user(user_id: int):
    conn = _get_conn()
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()


# ── CLI Tokens ──────────────────────────────────────────────────────

def create_cli_token(user_id: int, name: str = "CLI Token") -> str:
    """Generate a new CLI token. Returns the raw token (shown once)."""
    raw = f"gitfit_{secrets.token_urlsafe(32)}"
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    prefix = raw[:12]
    now = datetime.now(timezone.utc).isoformat()
    conn = _get_conn()
    conn.execute(
        "INSERT INTO cli_tokens (token_hash, user_id, name, created_at, token_prefix) VALUES (?,?,?,?,?)",
        (token_hash, user_id, name, now, prefix),
    )
    conn.commit()
    conn.close()
    return raw


def validate_cli_token(raw_token: str) -> dict | None:
    """Validate a CLI token. Returns user dict or None."""
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    conn = _get_conn()
    row = conn.execute(
        "SELECT u.* FROM cli_tokens ct JOIN users u ON ct.user_id=u.id WHERE ct.token_hash=?",
        (token_hash,),
    ).fetchone()
    if row:
        conn.execute(
            "UPDATE cli_tokens SET last_used=? WHERE token_hash=?",
            (datetime.now(timezone.utc).isoformat(), token_hash),
        )
        conn.commit()
    conn.close()
    return dict(row) if row else None


def list_cli_tokens(user_id: int) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT token_hash, name, created_at, last_used, token_prefix FROM cli_tokens WHERE user_id=? ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def revoke_cli_token(user_id: int, token_hash: str) -> bool:
    conn = _get_conn()
    cur = conn.execute(
        "DELETE FROM cli_tokens WHERE token_hash=? AND user_id=?",
        (token_hash, user_id),
    )
    conn.commit()
    conn.close()
    return cur.rowcount > 0


# ── Stats & History ────────────────────────────────────────────────

def get_user_stats(user_id: int) -> dict:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM user_stats WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    if row:
        return dict(row)
    return {"user_id": user_id, "completed_sessions": 0, "xp": 0, "level": 1,
            "level_title": "Couch Potato", "current_streak": 0, "longest_streak": 0}


def get_user_activity(user_id: int, days: int = 365) -> list[dict]:
    """Get activity data for the last N days."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT date, COUNT(*) as count FROM workout_history WHERE user_id=? "
        "AND date >= date('now', ? || ' days') GROUP BY date ORDER BY date",
        (user_id, f"-{days}"),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_workout_history(user_id: int, limit: int = 50) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM workout_history WHERE user_id=? ORDER BY date DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_user_workouts(user_id: int, public_only: bool = False) -> list[dict]:
    conn = _get_conn()
    query = "SELECT * FROM user_workouts WHERE user_id=?"
    if public_only:
        query += " AND is_public=1"
    rows = conn.execute(query + " ORDER BY created_at DESC", (user_id,)).fetchall()
    conn.close()
    results = []
    for r in rows:
        d = dict(r)
        d["workout_json"] = json.loads(d["workout_json"])
        results.append(d)
    return results


def sync_user_data(user_id: int, stats: dict = None, history: list = None, workouts: list = None):
    """Bulk upsert from CLI push."""
    conn = _get_conn()
    if stats:
        conn.execute("""
            INSERT INTO user_stats (user_id, completed_sessions, xp, level, level_title, current_streak, longest_streak)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                completed_sessions=excluded.completed_sessions,
                xp=excluded.xp,
                level=excluded.level,
                level_title=excluded.level_title,
                current_streak=excluded.current_streak,
                longest_streak=excluded.longest_streak
        """, (user_id, stats.get("completed_sessions", 0), stats.get("xp", 0),
              stats.get("level", 1), stats.get("level_title", "Couch Potato"),
              stats.get("current_streak", 0), stats.get("longest_streak", 0)))

    if history:
        for h in history:
            conn.execute("""
                INSERT OR IGNORE INTO workout_history (user_id, date, workout_name, duration_min, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, h.get("date", ""), h.get("workout", ""),
                  h.get("duration_min", 0), h.get("notes", "")))

    if workouts:
        now = datetime.now(timezone.utc).isoformat()
        for w in workouts:
            slug = w.get("slug", w.get("name", "").lower().replace(" ", "-"))
            conn.execute("""
                INSERT INTO user_workouts (user_id, slug, workout_json, forked_from, is_public, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, slug) DO UPDATE SET
                    workout_json=excluded.workout_json,
                    forked_from=excluded.forked_from,
                    is_public=excluded.is_public
            """, (user_id, slug, json.dumps(w.get("workout", w)),
                  w.get("forked_from"), 1, now))

    conn.commit()
    conn.close()
