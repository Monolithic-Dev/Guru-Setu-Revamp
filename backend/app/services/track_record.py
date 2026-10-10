"""Faculty track record (API-044, REQ-035): facts, never ratings."""
from datetime import datetime
from statistics import median
from typing import Any

from app.core.database import run_read
from app.core.errors import ApiError
from app.repos import tracking_repo


def _days(applied_at: str, decided: str) -> float:
    fmt = datetime.fromisoformat
    return (fmt(decided.replace("Z", "+00:00")) - fmt(applied_at.replace("Z", "+00:00"))).total_seconds() / 86400


def track_record(faculty_id: str) -> dict[str, Any]:
    row = run_read(lambda tx: tracking_repo.track_record(tx, faculty_id))
    if row is None:
        raise ApiError("NOT_FOUND", 404, "The faculty member was not found.")
    days = [_days(d["applied_at"], d["decided"]) for d in row["decisions"]]
    return {
        "faculty_id": row["faculty_id"],
        "name": row["name"],
        "openings_posted": row["openings_posted"],
        "guide_links_accepted": row["guide_links_accepted"],
        "guide_links_completed": row["guide_links_completed"],
        "median_days_to_first_decision": round(median(days), 1) if days else None,
    }
