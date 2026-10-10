"""Field visibility (security.md section 4, REQ-015, REQ-036). Private fields are OMITTED from the dict, never set to
None: the routes serialise with `response_model_exclude_unset`, so an omitted key does not appear in the JSON at all.
"""
from typing import Any

from app.core.clock import today
from app.schemas.auth import CurrentUser


def can_read_issue_text(viewer: CurrentUser, issue: dict[str, Any]) -> bool:
    """Issue text and resolution: the student it is about (unless the mentor marked it confidential), the mentor who
    raised it, other mentors of the student (unless confidential), and the HOD only when it is escalated and not
    confidential. IQAC never."""
    confidential = bool(issue.get("confidential"))
    if viewer.role == "student":
        return issue["student_id"] == viewer.user_id and not confidential
    if viewer.role == "faculty":
        return issue.get("raised_by") == viewer.user_id or not confidential
    if viewer.role == "hod":
        return bool(issue.get("escalated")) and not confidential
    return False


def shape_issue(
    viewer: CurrentUser, issue: dict[str, Any], history: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "id": issue["id"],
        "student_id": issue["student_id"],
        "category": issue["category"],
        "status": issue["status"],
        "escalated": bool(issue.get("escalated")),
        "confidential": bool(issue.get("confidential")),
        "raised_by_role": issue["raised_by_role"],
        "raised_at": issue["raised_at"],
        "resolved_at": issue.get("resolved_at"),
    }
    if can_read_issue_text(viewer, issue):
        out["text"] = issue.get("text")
        out["resolution"] = issue.get("resolution")
    if history is not None:
        out["history"] = history
    return out


def is_overdue(item: dict[str, Any]) -> bool:
    """open and due before today (backend 6.6)."""
    return item["status"] == "open" and str(item["due_date"]) < today().isoformat()


def shape_action_item(item: dict[str, Any], history: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    out = {
        "id": item["id"],
        "student_id": item["student_id"],
        "text": item["text"],
        "owner": item["owner"],
        "due_date": item["due_date"],
        "status": item["status"],
        "overdue": is_overdue(item),
        "session_id": item["session_id"],
        "created_at": item["created_at"],
        "updated_at": item["updated_at"],
    }
    if history is not None:
        out["history"] = history
    return out


def shape_session(viewer: CurrentUser, session: dict[str, Any]) -> dict[str, Any]:
    """SessionDetail for the author (everything) or an attendee (own rows only, never the notes)."""
    is_author = viewer.role == "faculty" and session["author_id"] == viewer.user_id
    own = viewer.user_id
    attendees = [a for a in session["attendees"] if is_author or a["student_id"] == own]
    items = [i for i in session["action_items"] if is_author or i["student_id"] == own]
    issues = [i for i in session["issues"] if is_author or i["student_id"] == own]
    out: dict[str, Any] = {
        "id": session["id"],
        "date": session["date"],
        "mode": session["mode"],
        "kind": session["kind"],
        "context": session["context"],
        "opening_id": session.get("opening_id"),
        "topics": session["topics"],
        "confidential": bool(session.get("confidential")),
        "next_followup": session.get("next_followup"),
        "logged_by": {"user_id": session["author_id"], "name": session["author_name"]},
        "attendees": [
            {"student_id": a["student_id"], "name": a["name"], "present": bool(a["present"]),
             "confirmed_at": a.get("confirmed_at")}
            for a in attendees
        ],
        "action_items": [
            {**shape_action_item({**i, "session_id": session["id"]})} for i in items
        ],
        "issues": [shape_issue(viewer, i) for i in issues],
        "created_at": session["created_at"],
    }
    if is_author:
        out["notes"] = session.get("notes")  # REQ-015: only the author ever receives the notes
    return out
