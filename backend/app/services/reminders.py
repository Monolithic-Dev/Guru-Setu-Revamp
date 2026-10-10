"""Reminders computed on read (API-039, REQ-023, backend 6.10). Nothing is stored and no job runs (ADR-05).
Messages carry names and dates only, never note, issue or action text."""
from datetime import date, timedelta
from typing import Any

from app.core.clock import today
from app.core.config import get_settings
from app.core.database import run_read
from app.repos import tracking_repo
from app.schemas.auth import CurrentUser
from app.services import terms, tracking

MAX_REMINDERS = 200


def _meetings_due(row: dict[str, Any], term_end: str, days_left: int) -> dict[str, Any]:
    return {
        "kind": "meetings_due", "student_id": row["student_id"], "student_name": row["name"],
        "ref_id": row["student_id"], "due_date": term_end,
        "message": f"{row['name']} has {row['meetings_this_term']} of {row['meetings_required']} meetings this term; "
                   f"the term ends in {days_left} days.",
    }


def _mentor(tx, user: CurrentUser) -> list[dict[str, Any]]:
    cfg, now = get_settings(), today()
    day = now.isoformat()
    stale_cut = (now - timedelta(days=cfg.issue_stale_days)).isoformat()
    term = terms.resolve(tx)[0]
    rows = [r for r in tracking.link_rows(tx, [user.user_id]) if r["mentorship_type"] == "assigned"]
    names = {r["student_id"]: r["name"] for r in tracking.link_rows(tx, [user.user_id])}
    out: list[dict[str, Any]] = []

    if term:
        days_left = (date.fromisoformat(term["end_date"]) - now).days
        if 0 <= days_left <= cfg.reminder_term_end_days:
            out += [
                _meetings_due(r, term["end_date"], days_left)
                for r in rows if r["meetings_this_term"] < r["meetings_required"]
            ]

    student_ids = list(names)
    for item in tracking_repo.action_items_of_mentors(tx, [user.user_id], student_ids):
        if item["status"] == "open" and str(item["due_date"]) < day:
            out.append({
                "kind": "action_overdue", "student_id": item["student_id"], "student_name": names[item["student_id"]],
                "ref_id": item["id"], "due_date": item["due_date"],
                "message": f"An action item for {names[item['student_id']]} was due on {item['due_date']}.",
            })
    for issue in tracking_repo.issues_about(tx, student_ids):
        visible = not issue["confidential"] or issue["raised_by"] == user.user_id  # same rule as 6.4 stale_issue
        if visible and issue["status"] != "resolved" and issue["raised_at"][:10] < stale_cut:
            out.append({
                "kind": "issue_stale", "student_id": issue["student_id"], "student_name": names[issue["student_id"]],
                "ref_id": issue["id"], "due_date": None,
                "message": f"An issue about {names[issue['student_id']]} has been open since "
                           f"{issue['raised_at'][:10]}.",
            })
    return out


def _student(tx, user: CurrentUser) -> list[dict[str, Any]]:
    cfg, now = get_settings(), today()
    day = now.isoformat()
    confirm_cut = (now - timedelta(days=cfg.session_confirm_days)).isoformat()
    term = terms.resolve(tx)[0]
    sessions = tracking_repo.sessions_of_student(tx, user.user_id)
    out: list[dict[str, Any]] = []

    if term:
        days_left = (date.fromisoformat(term["end_date"]) - now).days
        held = sum(1 for s in sessions if s["context"] == "assigned" and s["present"]
                   and term["start_date"] <= s["date"] <= term["end_date"])
        if 0 <= days_left <= cfg.reminder_term_end_days and held < cfg.min_meetings_per_term:
            out.append({
                "kind": "meetings_due", "ref_id": term["id"], "due_date": term["end_date"],
                "message": f"You have {held} of {cfg.min_meetings_per_term} mentor meetings this term; "
                           f"the term ends in {days_left} days.",
            })
    for item in tracking_repo.action_items_of_student(tx, user.user_id):
        if item["status"] == "open" and str(item["due_date"]) < day:
            out.append({
                "kind": "action_overdue", "ref_id": item["id"], "due_date": item["due_date"],
                "message": f"An action item was due on {item['due_date']}.",
            })
    for s in sessions:
        if s["present"] and s["confirmed_at"] is None and s["date"] < confirm_cut:
            out.append({
                "kind": "session_unconfirmed", "ref_id": s["id"], "due_date": s["date"],
                "message": f"Please confirm that you attended the session on {s['date']}.",
            })
    return out


def list_reminders(user: CurrentUser) -> list[dict[str, Any]]:
    """Student: own meetings, overdue actions, unconfirmed sessions. Faculty: per mentee, meetings due, overdue
    actions and stale issues. Soonest due date first (those without one last), at most 200."""
    out = run_read(lambda tx: _student(tx, user) if user.role == "student" else _mentor(tx, user))
    out.sort(key=lambda r: (r["due_date"] is None, r["due_date"] or "", r["ref_id"]))
    return out[:MAX_REMINDERS]
