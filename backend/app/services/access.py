"""Scope checks (security.md section 4). Each takes a transaction and raises 404 NOT_FOUND when the check fails, so
existence never leaks. They live in the services layer so services can call them inside their own transactions;
`api/deps.py` re-exports them, which is where routes and docs refer to them.
"""
from app.core.errors import ApiError
from app.repos import scope_repo
from app.schemas.auth import CurrentUser


def _not_found() -> ApiError:
    return ApiError("NOT_FOUND", 404, "The resource was not found.")


def assert_mentor_of(tx, faculty_id: str, student_id: str, mentor_type: str | None = None) -> None:
    if not scope_repo.is_mentor_of(tx, faculty_id, student_id, mentor_type):
        raise _not_found()


def assert_owner_of_opening(tx, faculty_id: str, opening_id: str) -> None:
    if not scope_repo.is_owner_of_opening(tx, faculty_id, opening_id):
        raise _not_found()


def assert_applicant_of_own(tx, faculty_id: str, student_id: str, opening_id: str | None = None) -> None:
    if not scope_repo.is_applicant_of_own(tx, faculty_id, student_id, opening_id):
        raise _not_found()


def assert_dept_hod(tx, hod_id: str, student_id: str) -> None:
    if not scope_repo.is_dept_hod_of(tx, hod_id, student_id):
        raise _not_found()


def assert_self_or_scope(tx, user: CurrentUser, student_id: str) -> None:
    """Who may read a student's profile (API-003): self, mentor/guide, faculty the student applied to, the HOD."""
    if user.role == "student":
        if user.user_id == student_id:
            return
    elif user.role == "faculty":
        if scope_repo.is_mentor_of(tx, user.user_id, student_id) or scope_repo.is_applicant_of_own(
            tx, user.user_id, student_id
        ):
            return
    elif user.role == "hod":
        if scope_repo.is_dept_hod_of(tx, user.user_id, student_id):
            return
    raise _not_found()
