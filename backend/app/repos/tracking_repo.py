"""Cypher for the read side of mentoring: mentor home rows (API-024), Mentee 360 (API-025), My mentorship (API-029).

Every function takes a transaction. Rows carry the raw facts; the rules (backend 6.4) are evaluated in
`services/tracking.py` with the configured thresholds. Nothing here returns `password_hash` or `embedding`.
"""
from typing import Any

_ISSUE_FIELDS = """
    i.id AS id, st.user_id AS student_id, i.category AS category, i.text AS text, i.status AS status,
    coalesce(i.escalated, false) AS escalated, coalesce(i.confidential, false) AS confidential,
    i.raised_by AS raised_by, i.raised_by_role AS raised_by_role, i.raised_at AS raised_at,
    i.resolved_at AS resolved_at, i.resolution AS resolution
"""


def _rows(result) -> list[dict[str, Any]]:
    return [record.data() for record in result]


# ---- mentor home / needs-attention (REQ-012, REQ-029) -----------------------------------------------------------


def active_links(tx, mentor_ids: list[str]) -> list[dict[str, Any]]:
    return _rows(
        tx.run(
            """
            MATCH (f:Faculty)-[m:MENTORS {status: 'active'}]->(s:Student) WHERE f.user_id IN $mentors
            RETURN f.user_id AS mentor_id, f.name AS mentor_name, m.id AS link_id, m.type AS type, m.since AS since,
                   m.opening_id AS opening_id, s.user_id AS student_id, s.name AS name, s.roll_no AS roll_no
            ORDER BY s.name
            """,
            mentors=mentor_ids,
        )
    )


def sessions_of_mentors(tx, mentor_ids: list[str], student_ids: list[str]) -> list[dict[str, Any]]:
    return _rows(
        tx.run(
            """
            MATCH (f:Faculty)-[:LOGGED]->(x:Session)-[r:ATTENDED_BY]->(s:Student)
            WHERE f.user_id IN $mentors AND s.user_id IN $students
            RETURN f.user_id AS mentor_id, s.user_id AS student_id, x.id AS id, x.date AS date,
                   x.context AS context, x.opening_id AS opening_id, r.present AS present,
                   r.confirmed_at AS confirmed_at
            """,
            mentors=mentor_ids,
            students=student_ids,
        )
    )


def action_items_of_mentors(tx, mentor_ids: list[str], student_ids: list[str]) -> list[dict[str, Any]]:
    """Action items created in the mentors' own sessions (backend 6.4 `overdue_action`)."""
    return _rows(
        tx.run(
            """
            MATCH (f:Faculty)-[:LOGGED]->(x:Session)-[:CREATED]->(a:ActionItem)-[:FOR]->(s:Student)
            WHERE f.user_id IN $mentors AND s.user_id IN $students
            RETURN f.user_id AS mentor_id, s.user_id AS student_id, a.id AS id, a.status AS status,
                   a.due_date AS due_date, x.context AS context, x.opening_id AS opening_id
            """,
            mentors=mentor_ids,
            students=student_ids,
        )
    )


def issues_about(tx, student_ids: list[str]) -> list[dict[str, Any]]:
    return _rows(
        tx.run(
            f"MATCH (i:Issue)-[:ABOUT]->(st:Student) WHERE st.user_id IN $students RETURN {_ISSUE_FIELDS}",
            students=student_ids,
        )
    )


def academics(tx, student_ids: list[str]) -> list[dict[str, Any]]:
    return _rows(
        tx.run(
            """
            MATCH (s:Student)-[:HAS_RECORD]->(r:AcademicRecord) WHERE s.user_id IN $students
            RETURN s.user_id AS student_id, r.term_id AS term_id, r.cgpa AS cgpa,
                   r.attendance_pct AS attendance_pct, r.backlogs AS backlogs
            ORDER BY r.term_id
            """,
            students=student_ids,
        )
    )


# ---- Mentee 360 and My mentorship (REQ-013, REQ-014) ------------------------------------------------------------


def mentorships_of(tx, student_id: str) -> list[dict[str, Any]]:
    return _rows(
        tx.run(
            """
            MATCH (f:Faculty)-[m:MENTORS]->(:Student {user_id: $sid})
            OPTIONAL MATCH (o:Opening {id: m.opening_id})
            RETURN m.id AS id, m.type AS type, m.status AS status, m.since AS since, m.until AS until,
                   m.end_reason AS end_reason, f.user_id AS mentor_id, f.name AS mentor_name,
                   m.opening_id AS opening_id, o.title AS opening_title,
                   f.designation AS designation, f.email AS email
            ORDER BY m.since DESC, m.id
            """,
            sid=student_id,
        )
    )


def sessions_of_student(tx, student_id: str) -> list[dict[str, Any]]:
    """Every session the student was recorded in, newest first, with the author and this student's attendance."""
    return _rows(
        tx.run(
            """
            MATCH (f:Faculty)-[:LOGGED]->(x:Session)-[r:ATTENDED_BY]->(:Student {user_id: $sid})
            RETURN x.id AS id, x.date AS date, x.mode AS mode, x.kind AS kind, x.context AS context,
                   x.topics AS topics, x.notes AS notes, coalesce(x.confidential, false) AS confidential,
                   x.next_followup AS next_followup, f.user_id AS author_id, f.name AS author_name,
                   r.present AS present, r.confirmed_at AS confirmed_at
            ORDER BY x.date DESC, x.id
            """,
            sid=student_id,
        )
    )


def action_items_of_student(tx, student_id: str) -> list[dict[str, Any]]:
    return _rows(
        tx.run(
            """
            MATCH (x:Session)-[:CREATED]->(a:ActionItem)-[:FOR]->(:Student {user_id: $sid})
            RETURN a.id AS id, $sid AS student_id, a.text AS text, a.owner AS owner, a.due_date AS due_date,
                   a.status AS status, x.id AS session_id, a.created_at AS created_at, a.updated_at AS updated_at
            ORDER BY a.due_date, a.id
            """,
            sid=student_id,
        )
    )


def issues_of_student(tx, student_id: str) -> list[dict[str, Any]]:
    return issues_about(tx, [student_id])
