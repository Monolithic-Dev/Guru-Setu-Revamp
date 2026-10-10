"""Mentoring write side: allotment (REQ-007), session log (REQ-008), confirmation (REQ-009), action items (REQ-010)
and issues (REQ-011, P0 subset). Rules: backend sections 6.5-6.8.

Each write function runs in ONE write transaction: the change, its StatusEvents and its notifications commit or
roll back together.
"""
import uuid
from datetime import date, datetime, timedelta
from typing import Any

from neo4j.exceptions import ConstraintError

from app.core.clock import today, utc_now, utc_now_iso
from app.core.config import get_settings
from app.core.database import run_read, run_write
from app.core.errors import ApiError
from app.repos import mentorship_repo
from app.schemas.auth import CurrentUser
from app.schemas.generated import IssueCreate, IssuePatch, SessionCreate
from app.services.access import assert_mentor_of
from app.services.notify import notify, render_title
from app.services.status_history import history_for, record_status
from app.services.visibility import shape_action_item, shape_issue, shape_session

IDEMPOTENCY_TTL = timedelta(hours=24)


# ============================== allotment (API-022, API-023) ==============================


def _allotment_view(tx, dept_code: str) -> dict[str, Any]:
    warn = get_settings().mentor_load_warn
    mentors = [
        {**m, "overloaded": m["mentee_count"] > warn} for m in mentorship_repo.mentor_loads(tx, dept_code)
    ]
    return {"mentors": mentors, "unallotted": mentorship_repo.unallotted_students(tx, dept_code)}


def allotment_view(user: CurrentUser) -> dict[str, Any]:
    return run_read(lambda tx: _allotment_view(tx, user.dept_code))


def allot(user: CurrentUser, mentor_id: str, student_ids: list[str]) -> dict[str, Any]:
    """Assign students to a mentor. A different active mentor is ended with reason `handover`; the same mentor is a
    no-op (backend 6.8)."""
    unique_ids = list(dict.fromkeys(student_ids))

    def work(tx):
        mentor = mentorship_repo.faculty_in_dept(tx, mentor_id, user.dept_code)
        if mentor is None:
            raise ApiError("NOT_FOUND", 404, "The mentor was not found.")
        students = {s["user_id"]: s for s in mentorship_repo.students_in_dept(tx, unique_ids, user.dept_code)}
        if len(students) != len(unique_ids):
            raise ApiError("NOT_FOUND", 404, "One or more students were not found.")
        current = mentorship_repo.active_assigned_links(tx, unique_ids)
        today_iso = today().isoformat()
        for student_id in unique_ids:
            existing = current.get(student_id)
            if existing and existing["mentor_id"] == mentor_id:
                continue  # already this mentor's mentee: no-op
            if existing:
                mentorship_repo.end_link(tx, existing["link_id"], today_iso, "handover")
                record_status(tx, "mentorship", existing["link_id"], "active", "ended", user, note="handover")
            link_id = str(uuid.uuid4())
            mentorship_repo.create_assigned_link(tx, mentor_id, student_id, link_id, today_iso)
            record_status(tx, "mentorship", link_id, None, "active", user, note="assigned")
            notify(
                tx,
                student_id,
                "allotted",
                render_title("allotted", mentor=mentor["name"]),
                link="/student/mentorship",
            )
        return _allotment_view(tx, user.dept_code)

    return run_write(work)


# ============================== sessions (API-026, API-027, API-028) ==============================


def _field_errors(body: SessionCreate) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    if body.date > today():
        errors.append({"field": "date", "message": "Session date cannot be in the future."})
    ids = [a.student_id for a in body.attendees]
    if len(set(ids)) != len(ids):
        errors.append({"field": "attendees", "message": "Each student can appear only once."})
    if body.kind.value == "individual" and len(body.attendees) != 1:
        errors.append({"field": "attendees", "message": "An individual session needs exactly one attendee."})
    if body.context.value == "guide" and not body.opening_id:
        errors.append({"field": "opening_id", "message": "Choose the opening for a guide session."})
    if body.context.value == "assigned" and body.opening_id:
        errors.append({"field": "opening_id", "message": "An opening applies to guide sessions only."})
    if body.next_followup is not None and body.next_followup <= body.date:
        errors.append({"field": "next_followup", "message": "Follow-up date must be after the session date."})
    attendee_set = set(ids)
    for index, item in enumerate(body.action_items or []):
        if item.student_id not in attendee_set:
            errors.append({"field": f"action_items.{index}.student_id", "message": "Choose one of the attendees."})
        if item.due_date < body.date:
            errors.append(
                {"field": f"action_items.{index}.due_date", "message": "Due date cannot be before the session date."}
            )
    for index, issue in enumerate(body.issues or []):
        if issue.student_id not in attendee_set:
            errors.append({"field": f"issues.{index}.student_id", "message": "Choose one of the attendees."})
    return errors


def _term_error(tx, session_date: date) -> dict[str, str] | None:
    """The session date must fall in the current or the previous term. With no terms loaded the check is skipped."""
    terms = mentorship_repo.terms(tx)
    if not terms:
        return None
    ordered = sorted(terms, key=lambda t: t["start_date"])
    configured = get_settings().current_term_id
    now = today().isoformat()
    current = next((t for t in ordered if t["id"] == configured), None) if configured else None
    if current is None:
        current = next((t for t in ordered if t["start_date"] <= now <= t["end_date"]), None)
    if current is None:
        current = next((t for t in reversed(ordered) if t["start_date"] <= now), ordered[0])
    previous = [t for t in ordered if t["end_date"] < current["start_date"]]
    allowed_from = (previous[-1] if previous else current)["start_date"]
    day = session_date.isoformat()
    if not (allowed_from <= day <= current["end_date"]):
        return {"field": "date", "message": "Session date must be in the current or previous term."}
    return None


def _stored_session_for_key(tx, key: str, user: CurrentUser) -> dict[str, Any] | None:
    found = mentorship_repo.get_idempotency_key(tx, key, user.user_id)
    if not found:
        return None
    created = datetime.fromisoformat(found["created_at"].replace("Z", "+00:00"))
    if utc_now() - created >= IDEMPOTENCY_TTL:
        return None  # expired keys are ignored and overwritten (A-19)
    session = mentorship_repo.get_session(tx, found["ref"])
    return shape_session(user, session) if session else None


def log_session(user: CurrentUser, body: SessionCreate, idempotency_key: str | None) -> dict[str, Any]:
    errors = _field_errors(body)
    if errors:
        raise ApiError("VALIDATION_FAILED", 422, "The session could not be saved.", errors=errors)

    def work(tx):
        if idempotency_key:
            replay = _stored_session_for_key(tx, idempotency_key, user)
            if replay is not None:
                return replay
        term_error = _term_error(tx, body.date)
        if term_error:
            raise ApiError("VALIDATION_FAILED", 422, "The session could not be saved.", errors=[term_error])

        attendee_ids = [a.student_id for a in body.attendees]
        mentor_type = "assigned" if body.context.value == "assigned" else "guide"
        linked = mentorship_repo.linked_students(tx, user.user_id, attendee_ids, mentor_type, body.opening_id)
        for student_id in attendee_ids:
            if student_id not in linked:
                name = mentorship_repo.student_names(tx, [student_id]).get(student_id, "This student")
                relation = "mentee" if mentor_type == "assigned" else "guided student"
                raise ApiError("NOT_YOUR_MENTEE", 422, f"{name} is not your {relation}.")

        now = utc_now_iso()
        session_id = str(uuid.uuid4())
        mentorship_repo.create_session(
            tx,
            user.user_id,
            {
                "id": session_id,
                "date": body.date.isoformat(),
                "mode": body.mode.value,
                "kind": body.kind.value,
                "context": body.context.value,
                "opening_id": body.opening_id,
                "topics": [t.value for t in body.topics],
                "notes": body.notes,
                "confidential": bool(body.confidential),
                "next_followup": body.next_followup.isoformat() if body.next_followup else None,
                "now": now,
            },
        )
        attendee_rows = [{"student_id": a.student_id, "present": a.present} for a in body.attendees]
        mentorship_repo.add_attendees(tx, session_id, attendee_rows)

        items = [
            {
                "id": str(uuid.uuid4()),
                "student_id": i.student_id,
                "text": i.text,
                "owner": i.owner.value,
                "due_date": i.due_date.isoformat(),
                "now": now,
            }
            for i in (body.action_items or [])
        ]
        mentorship_repo.add_action_items(tx, session_id, items)
        issues = [
            {
                "id": str(uuid.uuid4()),
                "student_id": i.student_id,
                "category": i.category.value,
                "text": i.text,
                "confidential": bool(i.confidential),
                "raised_by_role": "faculty",
                "now": now,
            }
            for i in (body.issues or [])
        ]
        mentorship_repo.add_issues(tx, session_id, user.user_id, issues)

        for item in items:
            record_status(tx, "action_item", item["id"], None, "open", user)
        for issue in issues:
            record_status(tx, "issue", issue["id"], None, "raised", user)
        for attendee in body.attendees:
            if attendee.present:
                notify(
                    tx,
                    attendee.student_id,
                    "session_logged",
                    render_title("session_logged", date=body.date.isoformat()),
                    link="/student/mentorship",
                )
        for item in items:
            if item["owner"] == "mentee":
                notify(
                    tx,
                    item["student_id"],
                    "action_assigned",
                    render_title("action_assigned", due_date=item["due_date"]),
                    link="/student/mentorship",
                )
        if idempotency_key:
            mentorship_repo.put_idempotency_key(tx, idempotency_key, user.user_id, session_id, now)
        return shape_session(user, mentorship_repo.get_session(tx, session_id))

    try:
        return run_write(work)
    except ConstraintError:
        # A concurrent request with the same Idempotency-Key won the race: return its stored result.
        stored = run_read(lambda tx: _stored_session_for_key(tx, idempotency_key or "", user))
        if stored is None:
            raise
        return stored


def get_session(user: CurrentUser, session_id: str) -> dict[str, Any]:
    """API-027. Role first (done by the route), then scope: the author, or an attendee. Others get 404."""

    def read(tx):
        session = mentorship_repo.get_session(tx, session_id)
        if session is None:
            raise ApiError("NOT_FOUND", 404, "The session was not found.")
        if user.role == "faculty":
            allowed = session["author_id"] == user.user_id
        else:
            allowed = any(a["student_id"] == user.user_id for a in session["attendees"])
        if not allowed:
            raise ApiError("NOT_FOUND", 404, "The session was not found.")
        return shape_session(user, session)

    return run_read(read)


def confirm_session(user: CurrentUser, session_id: str) -> dict[str, Any]:
    """API-028. An attendee confirms they were there (404 if not an attendee, 409 if marked absent). Idempotent."""

    def work(tx):
        session = mentorship_repo.get_session(tx, session_id)
        row = next((a for a in (session["attendees"] if session else []) if a["student_id"] == user.user_id), None)
        if row is None:
            raise ApiError("NOT_FOUND", 404, "The session was not found.")
        if not row["present"]:
            raise ApiError("NOT_PRESENT", 409, "You were marked absent for this session.")
        mentorship_repo.confirm_attendance(tx, session_id, user.user_id, utc_now_iso())
        return shape_session(user, mentorship_repo.get_session(tx, session_id))

    return run_write(work)


# ============================== action items (API-030) ==============================

# new status -> (allowed current statuses) for the mentor who logged the session (backend 6.6)
_MENTOR_TRANSITIONS: dict[str, set[str]] = {
    "verified": {"done"},
    "dropped": {"open", "done"},
    "open": {"done"},  # reopen
}


def patch_action_item(user: CurrentUser, item_id: str, new_status: str) -> dict[str, Any]:
    def work(tx):
        item = mentorship_repo.get_action_item(tx, item_id)
        if item is None:
            raise ApiError("NOT_FOUND", 404, "The action item was not found.")
        current = item["status"]
        if user.role == "student":
            if item["student_id"] != user.user_id:
                raise ApiError("NOT_FOUND", 404, "The action item was not found.")
            if new_status != "done":  # the mentee may only mark their own item done
                raise ApiError("FORBIDDEN", 403, "Only your mentor can set this status.")
            if current != "open":
                raise ApiError("INVALID_TRANSITION", 409, f"Cannot move action item from {current} to {new_status}.")
        else:  # faculty
            if item["author_id"] != user.user_id:
                raise ApiError("NOT_FOUND", 404, "The action item was not found.")
            if new_status == "done":  # marking done belongs to the mentee
                raise ApiError("FORBIDDEN", 403, "Only the mentee can mark an action item done.")
            if current not in _MENTOR_TRANSITIONS.get(new_status, set()):
                raise ApiError("INVALID_TRANSITION", 409, f"Cannot move action item from {current} to {new_status}.")
        mentorship_repo.set_action_status(tx, item_id, new_status, utc_now_iso())
        record_status(tx, "action_item", item_id, current, new_status, user)
        updated = mentorship_repo.get_action_item(tx, item_id)
        return shape_action_item(updated, history_for(tx, [item_id])[item_id])

    return run_write(work)


# ============================== issues (API-031, API-032) ==============================


def create_issue(user: CurrentUser, body: IssueCreate) -> dict[str, Any]:
    def work(tx):
        assert_mentor_of(tx, user.user_id, body.student_id)  # 404 unless an active mentor or guide
        session_id = body.session_id
        if session_id and not mentorship_repo.session_logged_by(tx, session_id, user.user_id):
            raise ApiError("NOT_FOUND", 404, "The session was not found.")
        issue = {
            "id": str(uuid.uuid4()),
            "student_id": body.student_id,
            "category": body.category.value,
            "text": body.text,
            "confidential": bool(body.confidential),
            "raised_by_role": "faculty",
            "now": utc_now_iso(),
        }
        mentorship_repo.add_issues(tx, session_id, user.user_id, [issue])
        record_status(tx, "issue", issue["id"], None, "raised", user)
        stored = mentorship_repo.get_issue(tx, issue["id"])
        return shape_issue(user, stored, history_for(tx, [issue["id"]])[issue["id"]])

    return run_write(work)


def patch_issue(user: CurrentUser, issue_id: str, body: IssuePatch) -> dict[str, Any]:
    """P0 subset: `raised -> resolved` with a resolution note. The wider lifecycle, escalation and the confidential
    toggle arrive with add-on A4 and return 409 until then."""

    def work(tx):
        issue = mentorship_repo.get_issue(tx, issue_id)
        if issue is None:
            raise ApiError("NOT_FOUND", 404, "The issue was not found.")
        if user.role == "faculty":
            assert_mentor_of(tx, user.user_id, issue["student_id"])
            if issue["confidential"] and issue.get("raised_by") != user.user_id:
                raise ApiError("NOT_FOUND", 404, "The issue was not found.")
        elif not (issue["escalated"] and not issue["confidential"]):  # HOD: escalated issues only
            raise ApiError("NOT_FOUND", 404, "The issue was not found.")

        requested = body.model_fields_set
        not_yet = body.status is not None and body.status.value != "resolved"
        if body.escalated or "confidential" in requested or not_yet:
            raise ApiError("INVALID_TRANSITION", 409, "This issue action is not available yet.")
        if body.status is None or body.status.value != "resolved":
            raise ApiError(
                "VALIDATION_FAILED",
                422,
                "Nothing to update.",
                errors=[{"field": "status", "message": "Set status to resolved."}],
            )
        if not body.resolution:
            raise ApiError(
                "VALIDATION_FAILED",
                422,
                "A resolution note is required.",
                errors=[{"field": "resolution", "message": "Write what was done to resolve this issue."}],
            )
        if issue["status"] == "resolved":
            raise ApiError("INVALID_TRANSITION", 409, "Cannot move issue from resolved to resolved.")
        previous = issue["status"]
        mentorship_repo.resolve_issue(tx, issue_id, body.resolution, utc_now_iso())
        record_status(tx, "issue", issue_id, previous, "resolved", user)
        updated = mentorship_repo.get_issue(tx, issue_id)
        return shape_issue(user, updated, history_for(tx, [issue_id])[issue_id])

    return run_write(work)
