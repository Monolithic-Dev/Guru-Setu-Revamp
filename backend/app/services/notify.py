"""Notifications (CMP-11, backend section 6.9). Write inside the same transaction as the change they describe.

Titles come from the catalogue below. Notification text must never contain session notes, issue text, action text or
resolution text (SEC-15): callers pass only names, dates, statuses and titles.
"""
import base64
import uuid
from typing import Any

from app.core.clock import utc_now_iso
from app.core.database import run_read, run_write
from app.core.errors import ApiError
from app.repos import notifications_repo

MAX_TITLE = 120
MAX_BODY = 200

# type -> title template (backend section 6.9)
TITLES: dict[str, str] = {
    "application_received": "{student} applied to {opening}",
    "application_status": "Your application to {opening} is now {status}",
    "certificate_result": "Certificate '{title}' is {status_label}",
    "review_needed": "A certificate from {student} needs review",
    "allotted": "Your mentor is now {mentor}",
    "session_logged": "Please confirm your session on {date}",
    "action_assigned": "New action item due {due_date}",
    "issue_escalated": "Issue escalated by {mentor}",
    "issue_raised_by_mentee": "{student} raised an issue",
    "meeting_request": "{student} requested a meeting",
}


def render_title(notification_type: str, **values: Any) -> str:
    return TITLES[notification_type].format(**values)


def notify(tx, user_id: str, notification_type: str, title: str, link: str, body: str | None = None) -> None:
    """Create a Notification with a NOTIFIES edge to the user."""
    if notification_type not in TITLES:
        raise ValueError(f"Unknown notification type: {notification_type}")
    notifications_repo.create(
        tx,
        user_id,
        {
            "id": str(uuid.uuid4()),
            "type": notification_type,
            "title": title[:MAX_TITLE],
            "body": body[:MAX_BODY] if body else None,
            "link": link,
            "created_at": utc_now_iso(),
        },
    )


# ---- cursor pagination for API-037 -------------------------------------------------------------------------------


def encode_cursor(created_at: str, notification_id: str) -> str:
    return base64.urlsafe_b64encode(f"{created_at}|{notification_id}".encode()).decode("ascii")


def decode_cursor(cursor: str) -> tuple[str, str]:
    try:
        created_at, notification_id = base64.urlsafe_b64decode(cursor.encode("ascii")).decode().split("|", 1)
    except (ValueError, UnicodeError) as exc:
        raise ApiError(
            "VALIDATION_FAILED",
            422,
            "The cursor is not valid.",
            errors=[{"field": "cursor", "message": "Invalid cursor"}],
        ) from exc
    return created_at, notification_id


def list_notifications(user_id: str, limit: int, cursor: str | None) -> dict[str, Any]:
    cursor_ts, cursor_id = decode_cursor(cursor) if cursor else (None, None)

    def read(tx):
        rows = notifications_repo.page(tx, user_id, limit, cursor_ts, cursor_id)
        return rows, notifications_repo.unread_count(tx, user_id)

    rows, unread = run_read(read)
    has_more = len(rows) > limit
    items = rows[:limit]
    next_cursor = encode_cursor(items[-1]["created_at"], items[-1]["id"]) if has_more else None
    return {"items": items, "next_cursor": next_cursor, "unread": unread}


def mark_read(user_id: str, notification_id: str) -> None:
    if not run_write(notifications_repo.mark_read, user_id=user_id, notification_id=notification_id):
        raise ApiError("NOT_FOUND", 404, "The notification was not found.")
