"""Mentee 360 (API-025, REQ-013) and the student's My mentorship page (API-029, REQ-014).

Private fields are OMITTED here (never set to None): the routes serialise with `response_model_exclude_unset`.
"""
from typing import Any

from app.core.clock import today
from app.core.database import run_read
from app.core.errors import ApiError
from app.repos import applications_repo, certificates_repo, scope_repo, students_repo, tracking_repo
from app.schemas.auth import CurrentUser
from app.services import terms, tracking
from app.services.access import assert_dept_hod, assert_mentor_of
from app.services.status_history import history_for
from app.services.visibility import shape_action_item, shape_issue


def _user_ref(user_id: str, name: str) -> dict[str, str]:
    return {"user_id": user_id, "name": name}


def _mentorship(row: dict[str, Any]) -> dict[str, Any]:
    out = {
        "id": row["id"], "type": row["type"], "status": row["status"], "since": row["since"],
        "until": row["until"], "end_reason": row["end_reason"],
        "mentor": _user_ref(row["mentor_id"], row["mentor_name"]),
    }
    if row["type"] == "guide":
        out["opening_id"], out["opening_title"] = row["opening_id"], row["opening_title"]
    return out


def _session_summary(viewer: CurrentUser, row: dict[str, Any]) -> dict[str, Any]:
    """SessionSummary for the student `row` describes. Notes only for the author (REQ-015)."""
    out = {
        "id": row["id"], "date": row["date"], "mode": row["mode"], "kind": row["kind"], "context": row["context"],
        "topics": row["topics"], "logged_by": _user_ref(row["author_id"], row["author_name"]),
        "present": bool(row["present"]), "confirmed_at": row["confirmed_at"], "confidential": row["confidential"],
    }
    if viewer.role == "faculty" and row["author_id"] == viewer.user_id:
        out["notes"] = row["notes"]
    return out


def _application(row: dict[str, Any], history: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "id": row["id"], "opening_id": row["opening_id"], "opening_title": row["opening_title"],
        "student_id": row["student_id"], "status": row["status"], "applied_at": row["applied_at"],
        "updated_at": row["updated_at"], "history": history,
    }


def _certificate(row: dict[str, Any]) -> dict[str, Any]:
    return dict(row)


def _term_summary(tx, sessions, actions, issues, certificates) -> dict[str, int] | None:
    """REQ-032: computed counts for the current term, no LLM."""
    term = terms.resolve(tx)[0]
    if term is None:
        return None
    start, end = term["start_date"], term["end_date"]

    def within(stamp: str | None) -> bool:
        return bool(stamp) and start <= stamp[:10] <= end

    mine = [a for a in actions if within(a["created_at"])]
    return {
        "sessions_attended": sum(1 for s in sessions if s["present"] and start <= s["date"] <= end),
        "actions_done": sum(1 for a in mine if a["status"] in ("done", "verified")),
        "actions_total": len(mine),
        "issues_raised": sum(1 for i in issues if within(i["raised_at"])),
        "issues_resolved": sum(1 for i in issues if within(i["resolved_at"])),
        "certificates_certified": sum(
            1 for c in certificates if c["status"] == "certified" and within(c["updated_at"])
        ),
    }


def mentee_overview(user: CurrentUser, student_id: str) -> dict[str, Any]:
    """API-025. Scope: any mentor of the student, or the HOD of the department; otherwise 404."""

    def read(tx):
        if user.role == "hod":
            assert_dept_hod(tx, user.user_id, student_id)
        else:
            assert_mentor_of(tx, user.user_id, student_id)
        profile = students_repo.get_profile(tx, student_id)
        if profile is None:
            raise ApiError("NOT_FOUND", 404, "The student was not found.")

        sessions = tracking_repo.sessions_of_student(tx, student_id)
        # A confidential session written by another mentor is not shown at all (REQ-036).
        sessions = [s for s in sessions if not s["confidential"] or s["author_id"] == user.user_id]
        actions = tracking_repo.action_items_of_student(tx, student_id)
        issues = tracking_repo.issues_of_student(tx, student_id)
        applications = applications_repo.list_for_student(tx, student_id)
        history = history_for(
            tx, [a["id"] for a in actions] + [i["id"] for i in issues] + [a["id"] for a in applications]
        )
        # Not-yet-certified certificates are for the assigned mentor and the HOD; a guide sees certified ones only.
        full_certs = user.role == "hod" or scope_repo.is_mentor_of(tx, user.user_id, student_id, "assigned")
        certificates = [
            _certificate(c) for c in certificates_repo.list_for_student(tx, student_id)
            if full_certs or c["status"] == "certified"
        ]
        rows = tracking.link_rows(tx, [user.user_id]) if user.role == "faculty" else []
        mine = next((r for r in rows if r["student_id"] == student_id), None)
        out = {
            "student": profile,
            "mentorships": [_mentorship(m) for m in tracking_repo.mentorships_of(tx, student_id)],
            "academics": [
                {k: a[k] for k in ("term_id", "cgpa", "attendance_pct", "backlogs")}
                for a in tracking_repo.academics(tx, [student_id])
            ],
            "sessions": [_session_summary(user, s) for s in sessions],
            "action_items": [shape_action_item(a, history.get(a["id"], [])) for a in actions],
            "issues": [shape_issue(user, i, history.get(i["id"], [])) for i in issues],
            "applications": [_application(a, history.get(a["id"], [])) for a in applications],
            "certificates": certificates,
            "attention_reasons": mine["attention_reasons"] if mine else [],
            "term_summary": _term_summary(tx, sessions, actions, issues, certificates),
        }
        if mine and mine["attention_details"]:
            out["attention_details"] = mine["attention_details"]
        # REQ-029, REQ-033: the level is for the assigned mentor and the HOD; the note and the at-risk mark are the
        # assigned mentor's alone. They are omitted (never null) for everyone else.
        flags = tracking_repo.student_flags(tx, student_id)
        if user.role == "hod" or (full_certs and user.role == "faculty"):
            out["learner_level"] = flags.get("learner_level")
        if user.role == "faculty" and full_certs:
            out["learner_note"] = flags.get("learner_note")
            out["marked_at_risk"] = flags.get("marked_at_risk", False)
        return out

    return run_read(read)


def my_mentorship(user: CurrentUser) -> dict[str, Any]:
    """API-029: everything the student sees on one page."""

    def read(tx):
        sid, day = user.user_id, today().isoformat()
        links = tracking_repo.mentorships_of(tx, sid)
        active = [m for m in links if m["status"] == "active"]
        assigned = next((m for m in active if m["type"] == "assigned"), None)
        sessions = tracking_repo.sessions_of_student(tx, sid)
        # The student sees their own attendee row only; notes are never theirs (REQ-015).
        summaries = [_session_summary(user, s) for s in sessions]
        actions = tracking_repo.action_items_of_student(tx, sid)
        issues = tracking_repo.issues_of_student(tx, sid)
        applications = applications_repo.list_for_student(tx, sid)
        history = history_for(
            tx, [a["id"] for a in actions] + [i["id"] for i in issues] + [a["id"] for a in applications]
        )
        return {
            "assigned_mentor": (
                {"user_id": assigned["mentor_id"], "name": assigned["mentor_name"],
                 "designation": assigned["designation"], "email": assigned["email"]}
                if assigned else None
            ),
            "guides": [_mentorship(m) for m in active if m["type"] == "guide"],
            "next_followup": min(
                (s["next_followup"] for s in sessions if s["next_followup"] and s["next_followup"] > day), default=None
            ),
            "sessions_to_confirm": [s for s in summaries if s["present"] and s["confirmed_at"] is None],
            "recent_sessions": summaries[:20],
            "action_items": [shape_action_item(a, history.get(a["id"], [])) for a in actions],
            "issues": [shape_issue(user, i, history.get(i["id"], [])) for i in issues],
            "applications": [_application(a, history.get(a["id"], [])) for a in applications],
        }

    return run_read(read)
