"""Current and previous term (ENT-07, assumption A-08): `CURRENT_TERM_ID`, else the term containing today, else the
latest term that has started. With no Term nodes loaded every function returns None."""
from typing import Any

from app.core.clock import today
from app.core.config import get_settings
from app.repos import mentorship_repo


def resolve(tx) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """(current, previous). `previous` is the latest term that ended before the current one starts."""
    ordered = sorted(mentorship_repo.terms(tx), key=lambda t: t["start_date"])
    if not ordered:
        return None, None
    configured = get_settings().current_term_id
    now = today().isoformat()
    current = next((t for t in ordered if t["id"] == configured), None) if configured else None
    if current is None:
        current = next((t for t in ordered if t["start_date"] <= now <= t["end_date"]), None)
    if current is None:
        current = next((t for t in reversed(ordered) if t["start_date"] <= now), ordered[0])
    previous = [t for t in ordered if t["end_date"] < current["start_date"]]
    return current, (previous[-1] if previous else None)


def academic_year(day: str) -> tuple[str, str]:
    """Jul 1 to Jun 30 around `day` (MET-08), as YYYY-MM-DD strings."""
    year, month = int(day[:4]), int(day[5:7])
    start = year if month >= 7 else year - 1
    return f"{start}-07-01", f"{start + 1}-06-30"
