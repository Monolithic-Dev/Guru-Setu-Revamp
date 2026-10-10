"""Applications (REQ-006): apply, decide, list. State machine and side effects per backend section 6.3.

Every transition writes a StatusEvent and a notification in the same transaction as the change.
"""
import uuid
from typing import Any

from app.core.clock import today, utc_now_iso
from app.core.database import run_read, run_write
from app.core.errors import ApiError
from app.repos import applications_repo, openings_repo
from app.schemas.auth import CurrentUser
from app.services import eligibility
from app.services.notify import notify, render_title
from app.services.status_history import history_for, record_status

# From -> allowed targets (backend 6.3). `rejected` and `completed` are terminal.
ALLOWED: dict[str, set[str]] = {
    "pending": {"shortlisted", "rejected"},
    "shortlisted": {"accepted", "rejected"},
    "accepted": {"completed"},
}


def _shape(row: dict[str, Any], history: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "opening_id": row["opening_id"],
        "opening_title": row["opening_title"],
        "student_id": row["student_id"],
        "status": row["status"],
        "applied_at": row["applied_at"],
        "updated_at": row["updated_at"],
        "history": history,
    }


def _enforce_eligibility(tx, user: CurrentUser, opening_id: str) -> None:
    """Availability rules (deadline, capacity, faculty capacity) always block; suitability rules (year, department,
    CGPA) block only a `strict` opening and otherwise just warn. CGPA decides eligibility, never the fit score."""
    row = openings_repo.get(tx, opening_id)
    ctx = eligibility.student_ctx(tx, user.user_id)
    if row is None or ctx is None:
        return
    result = eligibility.evaluate(row, ctx, today())
    unavailable, unsuitable = eligibility.blocking(result)
    if unavailable:
        raise ApiError("OPENING_CLOSED", 409, unavailable[0]["detail"])
    if unsuitable and row["eligibility_mode"] == "strict":
        raise ApiError(
            "NOT_ELIGIBLE", 409, "You do not meet this opening's requirements.",
            errors=[{"field": c["rule"], "message": c["detail"]} for c in unsuitable],
        )


def apply(user: CurrentUser, opening_id: str) -> dict[str, Any]:
    """API-017. Checks in order: opening exists (404), is open (409 OPENING_CLOSED), not applied yet (409)."""

    def work(tx):
        opening = applications_repo.get_opening(tx, opening_id)
        if opening is None:
            raise ApiError("NOT_FOUND", 404, "The opening was not found.")
        if opening["status"] != "open":
            raise ApiError("OPENING_CLOSED", 409, "This opening is closed.")
        if openings_repo.has_applied(tx, user.user_id, opening_id):
            raise ApiError("ALREADY_APPLIED", 409, "You have already applied to this opening.")
        _enforce_eligibility(tx, user, opening_id)
        application_id = str(uuid.uuid4())
        if not applications_repo.create_application(tx, user.user_id, opening_id, application_id, utc_now_iso()):
            raise ApiError("ALREADY_APPLIED", 409, "You have already applied to this opening.")
        record_status(tx, "application", application_id, None, "pending", user)
        if opening["owner_id"]:
            notify(
                tx,
                opening["owner_id"],
                "application_received",
                render_title("application_received", student=user.name, opening=opening["title"]),
                link=f"/faculty/openings/{opening_id}",
            )
        row = applications_repo.get_application(tx, application_id)
        return _shape(row, history_for(tx, [application_id])[application_id])

    return run_write(work)


def decide(user: CurrentUser, application_id: str, new_status: str) -> dict[str, Any]:
    """API-018. Only the faculty member who posted the opening may change the status (others get 404)."""

    def work(tx):
        row = applications_repo.get_application(tx, application_id)
        if row is None or row["owner_id"] != user.user_id:
            raise ApiError("NOT_FOUND", 404, "The application was not found.")
        current = row["status"]
        if new_status not in ALLOWED.get(current, set()):
            raise ApiError("INVALID_TRANSITION", 409, f"Cannot move application from {current} to {new_status}.")
        if new_status == "accepted":
            opening = openings_repo.get(tx, row["opening_id"])
            if opening and opening["accepted_count"] >= opening["positions"]:
                raise ApiError("OPENING_CLOSED", 409, "All positions for this opening are filled.")
        now = utc_now_iso()
        applications_repo.set_status(tx, application_id, new_status, now)
        record_status(tx, "application", application_id, current, new_status, user)
        if new_status == "accepted":
            link_id = applications_repo.ensure_guide_link(
                tx, user.user_id, row["student_id"], row["opening_id"], str(uuid.uuid4()), today().isoformat()
            )
            record_status(tx, "mentorship", link_id, None, "active", user, note="guide")
            after = openings_repo.get(tx, row["opening_id"])
            if after and after["status"] == "open" and after["accepted_count"] >= after["positions"]:
                openings_repo.close(tx, row["opening_id"])  # the last position is taken: close in the same transaction
                record_status(tx, "opening", row["opening_id"], "open", "closed", user, note="positions filled")
        elif new_status == "completed":
            link_id = applications_repo.end_guide_link(
                tx, user.user_id, row["student_id"], row["opening_id"], today().isoformat()
            )
            if link_id:
                record_status(tx, "mentorship", link_id, "active", "ended", user, note="completed")
        notify(
            tx,
            row["student_id"],
            "application_status",
            render_title("application_status", opening=row["opening_title"], status=new_status),
            link="/student/mentorship",
        )
        updated = applications_repo.get_application(tx, application_id)
        return _shape(updated, history_for(tx, [application_id])[application_id])

    return run_write(work)


def list_mine(user: CurrentUser) -> list[dict[str, Any]]:
    """API-019."""

    def read(tx):
        rows = applications_repo.list_for_student(tx, user.user_id)
        histories = history_for(tx, [r["id"] for r in rows]) if rows else {}
        return [_shape(r, histories[r["id"]]) for r in rows]

    return run_read(read)
