"""Time helpers (architecture section 5). Calendar dates are Asia/Kolkata; timestamps are UTC with a Z suffix.

India has no daylight saving time, so a fixed +05:30 offset is exact and needs no tz database.
"""
from datetime import UTC, date, datetime, timedelta, timezone

from app.core.config import get_settings

IST = timezone(timedelta(hours=5, minutes=30), name="Asia/Kolkata")


def today() -> date:
    """Today in Asia/Kolkata. TODAY_OVERRIDE (tests and rehearsal only) wins."""
    override = get_settings().today_override
    if override is not None:
        return override
    return datetime.now(IST).date()


def utc_now() -> datetime:
    return datetime.now(UTC)


def utc_now_iso() -> str:
    """UTC ISO-8601 with a Z suffix and millisecond precision, e.g. 2026-10-10T08:15:30.123Z."""
    return utc_now().isoformat(timespec="milliseconds").replace("+00:00", "Z")
