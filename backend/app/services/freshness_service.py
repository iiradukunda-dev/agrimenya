from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def data_freshness_score(last_updated: str | None, max_age_hours: int = 48) -> dict[str, Any]:
    updated = _parse_timestamp(last_updated)
    if updated is None:
        return {"freshness_score": 0.0, "status": "stale", "age_hours": None}

    age_hours = (datetime.now(timezone.utc) - updated).total_seconds() / 3600.0
    score = max(0.0, min(1.0, 1.0 - (age_hours / max_age_hours)))
    status = "fresh" if score >= 0.7 else "warning" if score >= 0.35 else "stale"
    return {
        "freshness_score": round(score, 3),
        "status": status,
        "age_hours": round(age_hours, 2),
    }
