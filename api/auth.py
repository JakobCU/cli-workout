"""Auth helpers for the GitFitHub API -- unified token detection."""

import sys
from pathlib import Path
_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

from api.database import validate_cli_token, get_user_by_id
from api.jwt_auth import decode_jwt


def verify_token(token: str) -> dict | None:
    """Verify a bearer token. Supports both CLI tokens (gitfit_*) and JWTs.
    Returns user dict or None."""
    if not token:
        return None

    # CLI token: starts with gitfit_
    if token.startswith("gitfit_"):
        user = validate_cli_token(token)
        if user:
            return dict(user)
        return None

    # JWT token
    payload = decode_jwt(token)
    if payload:
        user_id = int(payload["sub"])
        user = get_user_by_id(user_id)
        if user:
            return dict(user)

    # Legacy: fall back to local CLI token validation
    try:
        from gitfit.user import get_user, validate_token as local_validate
        if local_validate(token):
            return get_user()
    except Exception:
        pass

    return None
