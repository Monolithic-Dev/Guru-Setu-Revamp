"""Cypher for department metrics and the evidence exports (backend section 7). Department scope is always a
parameter. Text fields (session notes, issue text, action text, resolution) are NOT selected here, with one
exception: `escalated_issues` returns the text of unresolved, escalated, non-confidential issues, which only the HOD
dashboard may show (security section 4)."""
from typing import Any


def _rows(result) -> list[dict[str, Any]]:
    return [record.data() for record in result]


def count_students(tx, dept: str) -> int:
    return tx.run("MATCH (s:Student {dept_code: $d}) RETURN count(s) AS n", d=dept).single()["n"]


def mentors(tx, dept: str) -> list[dict[str, Any]]:
    return _rows(
        tx.run(
            """
            MATCH (f:Faculty {dept_code: $d})
            RETURN f.user_id AS mentor_id, f.name AS name, f.designation AS designation,
                   f.employee_id AS employee_id
            ORDER BY f.name
            """,
            d=dept,
        )
    )


def issues(tx, dept: str) -> list[dict[str, Any]]:
    """Issue metadata only (no text) for the department's students."""
    return _rows(
        tx.run(
            """
            MATCH (i:Issue)-[:ABOUT]->(s:Student {dept_code: $d})
            RETURN i.id AS id, s.user_id AS student_id, i.category AS category, i.status AS status,
                   coalesce(i.confidential, false) AS confidential, coalesce(i.escalated, false) AS escalated,
                   i.raised_at AS raised_at, i.resolved_at AS resolved_at
            """,
            d=dept,
        )
    )


def escalated_issues(tx, dept: str) -> list[dict[str, Any]]:
    return _rows(
        tx.run(
            """
            MATCH (i:Issue {escalated: true})-[:ABOUT]->(s:Student {dept_code: $d})
            WHERE i.status <> 'resolved' AND coalesce(i.confidential, false) = false
            OPTIONAL MATCH (m:User {user_id: i.raised_by})
            RETURN i.id AS issue_id, s.user_id AS student_id, s.name AS student_name, m.name AS mentor_name,
                   i.category AS category, i.text AS text, i.status AS status, i.raised_at AS raised_at
            ORDER BY i.raised_at, i.id
            """,
            d=dept,
        )
    )


def overdue_actions(tx, dept: str, day: str) -> int:
    return tx.run(
        """
        MATCH (a:ActionItem {status: 'open'})-[:FOR]->(:Student {dept_code: $d}) WHERE a.due_date < $day
        RETURN count(a) AS n
        """,
        d=dept,
        day=day,
    ).single()["n"]


def meetings_held(tx, dept: str, start: str, end: str) -> dict[str, int]:
    """Distinct `assigned` sessions per mentor with a date in the term (MET-05)."""
    return {
        r["mentor_id"]: r["n"]
        for r in tx.run(
            """
            MATCH (f:Faculty {dept_code: $d})-[:LOGGED]->(x:Session {context: 'assigned'})
            WHERE x.date >= $start AND x.date <= $end
            RETURN f.user_id AS mentor_id, count(x) AS n
            """,
            d=dept,
            start=start,
            end=end,
        )
    }


def attendance_confirmation(tx, dept: str, start: str, end: str) -> tuple[int, int]:
    """(present attendances in the term, how many of those are confirmed) for MET-12."""
    record = tx.run(
        """
        MATCH (x:Session)-[r:ATTENDED_BY {present: true}]->(:Student {dept_code: $d})
        WHERE x.date >= $start AND x.date <= $end
        RETURN count(r) AS present, count(r.confirmed_at) AS confirmed
        """,
        d=dept,
        start=start,
        end=end,
    ).single()
    return record["present"], record["confirmed"]


def pending_reviews(tx, dept: str) -> int:
    return tx.run(
        "MATCH (:Student {dept_code: $d})-[:SUBMITTED]->(e:Evidence {status: 'needs_review'}) RETURN count(e) AS n",
        d=dept,
    ).single()["n"]


def certified_evidence(tx, dept: str) -> list[dict[str, Any]]:
    """Certified certificates of the department's students, for MET-08 and the achievements export."""
    return _rows(
        tx.run(
            """
            MATCH (s:Student {dept_code: $d})-[:SUBMITTED]->(e:Evidence {status: 'certified'})
            OPTIONAL MATCH (r:User {user_id: e.reviewed_by})
            RETURN e.id AS id, s.user_id AS student_id, s.roll_no AS roll_no, s.name AS student_name,
                   e.title AS title, e.issuer AS issuer, e.issue_date AS issue_date, e.level AS level,
                   e.type AS type, e.certificate_id AS certificate_id, e.status AS status, r.name AS reviewed_by
            ORDER BY s.roll_no, e.issue_date, e.id
            """,
            d=dept,
        )
    )


def allotment(tx, dept: str) -> list[dict[str, Any]]:
    return _rows(
        tx.run(
            """
            MATCH (f:Faculty {dept_code: $d})-[m:MENTORS {type: 'assigned', status: 'active'}]->(s:Student)
            RETURN f.name AS mentor, s.roll_no AS roll_no, s.name AS student, m.since AS since
            ORDER BY f.name, s.roll_no
            """,
            d=dept,
        )
    )


def criteria(tx) -> list[dict[str, Any]]:
    return _rows(
        tx.run(
            """
            MATCH (c:Criterion)
            RETURN c.code AS code, c.title AS title, coalesce(c.evidence_types, []) AS evidence_types,
                   coalesce(c.verified, false) AS verified
            ORDER BY c.code
            """
        )
    )
