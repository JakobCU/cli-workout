"""JWT creation and validation for GitFitHub web auth."""

import os
import secrets
from datetime import datetime, timezone, timedelta
from pathlib import Path

from jose import jwt, JWTError

# Auto-generate JWT secret on first run
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

def _ensure_jwt_secret() -> str:
    """Get or create JWT_SECRET from .env."""
    secret = os.environ.get("JWT_SECRET")
    if secret:
        return secret

    # Generate and persist
    secret = secrets.token_urlsafe(48)
    lines = []
    if _ENV_PATH.exists():
        lines = _ENV_PATH.read_text(encoding="utf-8").splitlines()
    lines.append(f"JWT_SECRET={secret}")
    _ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.environ["JWT_SECRET"] = secret
    return secret


JWT_SECRET = _ensure_jwt_secret()
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 7


def create_jwt(user_id: int, username: str) -> str:
    """Create a JWT token with 7-day expiry."""
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRY_DAYS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str) -> dict | None:
    """Decode and validate a JWT. Returns payload dict or None."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None
