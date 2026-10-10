"""Cypher for users (ENT-01). Functions take a transaction `tx`.

They never return `embedding`, and only the login query returns `password_hash`.
"""
from typing import Any

_AUTH_FIELDS = "u.user_id AS user_id, u.name AS name, u.email AS email, u.role AS role, u.dept_code AS dept_code"


def get_login_record(tx, email: str) -> dict[str, Any] | None:
    """User by lower-cased email for API-001. The only query that returns `password_hash`."""
    record = tx.run(
        f"MATCH (u:User {{email: $email}}) RETURN {_AUTH_FIELDS}, u.password_hash AS password_hash",
        email=email,
    ).single()
    return record.data() if record else None


def get_by_id(tx, user_id: str) -> dict[str, Any] | None:
    """User by id for every authenticated request. The role comes from here, not from the token."""
    record = tx.run(f"MATCH (u:User {{user_id: $user_id}}) RETURN {_AUTH_FIELDS}", user_id=user_id).single()
    return record.data() if record else None
