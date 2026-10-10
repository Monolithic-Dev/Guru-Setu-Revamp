"""Authentication, role checks and scope checks (CMP-03; security.md sections 2-4).

Order on every protected route: token (401) -> role (403, `require_role`) -> scope (404, the `assert_*` helpers).
The user is re-read from Neo4j by `sub` and the role comes from the database, never from the token (SEC-03/04).
"""
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Depends, Request

from app.core.database import run_read
from app.core.errors import ApiError
from app.core.security import decode_token
from app.repos import scope_repo, users_repo


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    name: str
    email: str
    role: str  # student | faculty | hod | iqac
    dept_code: str


def _bearer_token(request: Request) -> str:
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise ApiError("UNAUTHENTICATED", 401, "Missing or invalid token.")
    return token.strip()


def current_user(request: Request) -> CurrentUser:
    claims = decode_token(_bearer_token(request))
    row = run_read(users_repo.get_by_id, user_id=str(claims["sub"]))
    if row is None:  # token for a user that no longer exists
        raise ApiError("UNAUTHENTICATED", 401, "Missing or invalid token.")
    request.state.user_id = row["user_id"]  # for the access log
    return CurrentUser(**row)


def require_role(*roles: str) -> Callable[[CurrentUser], CurrentUser]:
    """Dependency factory: 403 FORBIDDEN unless the caller's role is listed."""

    def dependency(user: CurrentUser = Depends(current_user)) -> CurrentUser:
        if user.role not in roles:
            raise ApiError("FORBIDDEN", 403, "You don't have access to this.")
        return user

    return dependency


# ---- scope helpers: each takes a transaction, raises 404 NOT_FOUND when the check fails -----------------------

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
