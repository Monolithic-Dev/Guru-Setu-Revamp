"""Scope predicates (security.md section 4) as single Cypher EXISTS queries. Each returns a bool.

`api/deps.py` turns a False into 404 NOT_FOUND so that existence never leaks.
"""


def is_mentor_of(tx, faculty_id: str, student_id: str, mentor_type: str | None = None) -> bool:
    """mentor_of / assigned_mentor_of: an active MENTORS link, optionally of one type ('assigned' or 'guide')."""
    return bool(
        tx.run(
            """
            RETURN EXISTS {
              MATCH (:Faculty {user_id: $f})-[m:MENTORS {status: 'active'}]->(:Student {user_id: $s})
              WHERE $type IS NULL OR m.type = $type
            } AS ok
            """,
            f=faculty_id, s=student_id, type=mentor_type,
        ).single()["ok"]
    )


def is_owner_of_opening(tx, faculty_id: str, opening_id: str) -> bool:
    return bool(
        tx.run(
            "RETURN EXISTS { MATCH (:Faculty {user_id: $f})-[:POSTED]->(:Opening {id: $o}) } AS ok",
            f=faculty_id, o=opening_id,
        ).single()["ok"]
    )


def is_applicant_of_own(tx, faculty_id: str, student_id: str, opening_id: str | None = None) -> bool:
    """The student applied to an opening this faculty posted (optionally to one specific opening)."""
    return bool(
        tx.run(
            """
            RETURN EXISTS {
              MATCH (:Faculty {user_id: $f})-[:POSTED]->(o:Opening)<-[:APPLIED_TO]-(:Student {user_id: $s})
              WHERE $o IS NULL OR o.id = $o
            } AS ok
            """,
            f=faculty_id, s=student_id, o=opening_id,
        ).single()["ok"]
    )


def is_dept_hod_of(tx, hod_id: str, student_id: str) -> bool:
    """dept_of: the HOD and the student share a department."""
    return bool(
        tx.run(
            """
            RETURN EXISTS {
              MATCH (h:Staff {user_id: $h, role: 'hod'}), (s:Student {user_id: $s})
              WHERE h.dept_code = s.dept_code
            } AS ok
            """,
            h=hod_id, s=student_id,
        ).single()["ok"]
    )
