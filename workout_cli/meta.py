"""Fork metadata: lineage tracking, versioning, and history."""

import uuid
from datetime import datetime, timezone


def create_fork_meta(source_slug, source_name, adapted_with=None):
    """Create _meta dict for a newly forked workout."""
    now = datetime.now(timezone.utc)
    changes = f"Initial fork from {source_name}"
    if adapted_with:
        changes += f' (AI: "{adapted_with}")'

    return {
        "id": str(uuid.uuid4()),
        "forked_from": source_slug,
        "forked_at": now.isoformat(timespec="seconds"),
        "adapted_with": adapted_with,
        "author": "user",
        "version": 1,
        "history": [
            {"version": 1, "date": now.strftime("%Y-%m-%d"), "changes": changes}
        ],
    }


def bump_version(meta, change_description):
    """Increment version and append a history entry."""
    meta["version"] = meta.get("version", 1) + 1
    meta.setdefault("history", []).append({
        "version": meta["version"],
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "changes": change_description,
    })


def get_meta(workout):
    """Safe access to _meta, returns None if absent."""
    return workout.get("_meta")


def has_fork_lineage(workout):
    """Check if workout has fork tracking metadata."""
    meta = get_meta(workout)
    return meta is not None and "forked_from" in meta
