"""Authentication, role checks and scope checks (CMP-03; security.md sections 2-4).

Order on every protected route: token (401) -> role (403, `require_role`) -> scope (404, the `assert_*` helpers).
The user is re-read from Neo4j by `sub` and the role comes from the database, never from the token (SEC-03/04).
The scope helpers are implemented in `app/services/access.py` and re-exported here.
"""
from collections.abc import Callable

from fastapi import Depends, Request

from app.core.database import run_read
from app.core.errors import ApiError
from app.core.security import decode_token
from app.repos import users_repo
from app.schemas.auth import CurrentUser
from app.services.access import (
    assert_applicant_of_own,
    assert_dept_hod,
    assert_mentor_of,
    assert_owner_of_opening,
    assert_self_or_scope,
)

__all__ = [
    "CurrentUser",
    "assert_applicant_of_own",
    "assert_dept_hod",
    "assert_mentor_of",
    "assert_owner_of_opening",
    "assert_self_or_scope",
    "current_user",
    "require_role",
]


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
