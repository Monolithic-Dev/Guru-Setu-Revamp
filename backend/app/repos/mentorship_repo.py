"""Cypher for mentoring: allotment (ENT-17), sessions (ENT-09, ENT-19), action items (ENT-10), issues (ENT-11),
terms (ENT-07) and idempotency keys (ENT-21). Dates are `YYYY-MM-DD` strings, timestamps UTC ISO strings with a Z.

Functions take a transaction `tx`. They never return `password_hash` or `embedding`.
"""
from typing import Any


def _rows(result) -> list[dict[str, Any]]:
    return [record.data() for record in result]


# ---- terms -----------------------------------------------------------------------------------------------------------


def terms(tx) -> list[dict[str, Any]]:
    return _rows(
        tx.run("MATCH (t:Term) RETURN t.id AS id, t.name AS name, t.start_date AS start_date, t.end_date AS end_date")
    )


# ---- allotment -------------------------------------------------------------------------------------------------------


def mentor_loads(tx, dept_code: str) -> list[dict[str, Any]]:
    return _rows(
        tx.run(
            """
            MATCH (f:Faculty {dept_code: $dept})
            OPTIONAL MATCH (f)-[m:MENTORS {type: 'assigned', status: 'active'}]->(:Student)
            RETURN f.user_id AS mentor_id, f.name AS name, count(m) AS mentee_count
            ORDER BY f.name
            """,
            dept=dept_code,
        )
    )


def unallotted_students(tx, dept_code: str) -> list[dict[str, Any]]:
    return _rows(
        tx.run(
            """
            MATCH (s:Student {dept_code: $dept})
            WHERE NOT EXISTS { MATCH (:Faculty)-[:MENTORS {type: 'assigned', status: 'active'}]->(s) }
            RETURN s.user_id AS user_id, s.name AS name, s.roll_no AS roll_no, s.year AS year
            ORDER BY s.roll_no
            """,
            dept=dept_code,
        )
    )


def faculty_in_dept(tx, faculty_id: str, dept_code: str) -> dict[str, Any] | None:
    record = tx.run(
        "MATCH (f:Faculty {user_id: $id, dept_code: $dept}) RETURN f.user_id AS user_id, f.name AS name",
        id=faculty_id,
        dept=dept_code,
    ).single()
    return record.data() if record else None


def students_in_dept(tx, student_ids: list[str], dept_code: str) -> list[dict[str, Any]]:
    return _rows(
        tx.run(
            """
            MATCH (s:Student {dept_code: $dept}) WHERE s.user_id IN $ids
            RETURN s.user_id AS user_id, s.name AS name
            """,
            ids=student_ids,
            dept=dept_code,
        )
    )


def active_assigned_links(tx, student_ids: list[str]) -> dict[str, dict[str, Any]]:
    rows = tx.run(
        """
        MATCH (f:Faculty)-[m:MENTORS {type: 'assigned', status: 'active'}]->(s:Student)
        WHERE s.user_id IN $ids
        RETURN s.user_id AS student_id, m.id AS link_id, f.user_id AS mentor_id
        """,
        ids=student_ids,
    )
    return {r["student_id"]: {"link_id": r["link_id"], "mentor_id": r["mentor_id"]} for r in rows}


def end_link(tx, link_id: str, until: str, reason: str) -> None:
    tx.run(
        "MATCH ()-[m:MENTORS {id: $id}]->() SET m.status = 'ended', m.until = $until, m.end_reason = $reason",
        id=link_id,
        until=until,
        reason=reason,
    ).consume()


def create_assigned_link(tx, mentor_id: str, student_id: str, link_id: str, since: str) -> None:
    tx.run(
        """
        MATCH (f:Faculty {user_id: $fid}), (s:Student {user_id: $sid})
        CREATE (f)-[:MENTORS {id: $id, type: 'assigned', status: 'active', since: $since}]->(s)
        """,
        fid=mentor_id,
        sid=student_id,
        id=link_id,
        since=since,
    ).consume()


# ---- sessions --------------------------------------------------------------------------------------------------------


def linked_students(tx, faculty_id: str, student_ids: list[str], mentor_type: str, opening_id: str | None) -> set[str]:
    """Which of `student_ids` have an active MENTORS link of this type from the faculty (and opening, for guides)."""
    rows = tx.run(
        """
        MATCH (:Faculty {user_id: $fid})-[m:MENTORS {status: 'active', type: $type}]->(s:Student)
        WHERE s.user_id IN $ids AND ($oid IS NULL OR m.opening_id = $oid)
        RETURN DISTINCT s.user_id AS id
        """,
        fid=faculty_id,
        ids=student_ids,
        type=mentor_type,
        oid=opening_id,
    )
    return {r["id"] for r in rows}


def student_names(tx, ids: list[str]) -> dict[str, str]:
    return {
        r["id"]: r["name"]
        for r in tx.run("MATCH (s:Student) WHERE s.user_id IN $ids RETURN s.user_id AS id, s.name AS name", ids=ids)
    }


def get_idempotency_key(tx, key: str, user_id: str) -> dict[str, Any] | None:
    record = tx.run(
        "MATCH (k:IdempotencyKey {key: $key, user_id: $uid}) RETURN k.response_ref AS ref, k.created_at AS created_at",
        key=key,
        uid=user_id,
    ).single()
    return record.data() if record else None


def put_idempotency_key(tx, key: str, user_id: str, session_id: str, now: str) -> None:
    tx.run(
        "MERGE (k:IdempotencyKey {key: $key, user_id: $uid}) SET k.response_ref = $ref, k.created_at = $now",
        key=key,
        uid=user_id,
        ref=session_id,
        now=now,
    ).consume()


def create_session(tx, author_id: str, session: dict[str, Any]) -> None:
    tx.run(
        """
        MATCH (f:Faculty {user_id: $author})
        CREATE (s:Session {id: $id, date: $date, mode: $mode, kind: $kind, context: $context, topics: $topics,
                           confidential: $confidential, created_at: $now})
        SET s.opening_id = $opening_id, s.notes = $notes, s.next_followup = $next_followup
        CREATE (f)-[:LOGGED]->(s)
        """,
        author=author_id,
        **session,
    ).consume()


def add_attendees(tx, session_id: str, attendees: list[dict[str, Any]]) -> None:
    tx.run(
        """
        MATCH (s:Session {id: $sid})
        UNWIND $attendees AS a
        MATCH (st:Student {user_id: a.student_id})
        CREATE (s)-[:ATTENDED_BY {present: a.present}]->(st)
        """,
        sid=session_id,
        attendees=attendees,
    ).consume()


def add_action_items(tx, session_id: str, items: list[dict[str, Any]]) -> None:
    if not items:
        return
    tx.run(
        """
        MATCH (s:Session {id: $sid})
        UNWIND $items AS i
        MATCH (st:Student {user_id: i.student_id})
        CREATE (a:ActionItem {id: i.id, text: i.text, owner: i.owner, due_date: i.due_date, status: 'open',
                              created_at: i.now, updated_at: i.now})
        CREATE (s)-[:CREATED]->(a)
        CREATE (a)-[:FOR]->(st)
        """,
        sid=session_id,
        items=items,
    ).consume()


def add_issues(tx, session_id: str | None, author_id: str, issues: list[dict[str, Any]]) -> None:
    if not issues:
        return
    tx.run(
        """
        UNWIND $issues AS i
        MATCH (st:Student {user_id: i.student_id})
        CREATE (n:Issue {id: i.id, category: i.category, text: i.text, status: 'raised', escalated: false,
                         confidential: i.confidential, raised_by: $author, raised_by_role: i.raised_by_role,
                         raised_at: i.now})
        CREATE (n)-[:ABOUT]->(st)
        WITH n
        OPTIONAL MATCH (s:Session {id: $sid})
        FOREACH (_ IN CASE WHEN s IS NULL THEN [] ELSE [1] END | CREATE (s)-[:RAISED]->(n))
        """,
        sid=session_id,
        author=author_id,
        issues=issues,
    ).consume()


def get_session(tx, session_id: str) -> dict[str, Any] | None:
    head = tx.run(
        """
        MATCH (f:Faculty)-[:LOGGED]->(s:Session {id: $sid})
        RETURN s.id AS id, s.date AS date, s.mode AS mode, s.kind AS kind, s.context AS context,
               s.opening_id AS opening_id, s.topics AS topics, s.notes AS notes,
               coalesce(s.confidential, false) AS confidential, s.next_followup AS next_followup,
               s.created_at AS created_at, f.user_id AS author_id, f.name AS author_name
        """,
        sid=session_id,
    ).single()
    if head is None:
        return None
    session = head.data()
    session["attendees"] = _rows(
        tx.run(
            """
            MATCH (:Session {id: $sid})-[r:ATTENDED_BY]->(st:Student)
            RETURN st.user_id AS student_id, st.name AS name, r.present AS present, r.confirmed_at AS confirmed_at,
                   r.feedback AS feedback, r.feedback_comment AS feedback_comment
            ORDER BY st.name
            """,
            sid=session_id,
        )
    )
    session["action_items"] = _rows(
        tx.run(
            """
            MATCH (:Session {id: $sid})-[:CREATED]->(a:ActionItem)-[:FOR]->(st:Student)
            RETURN a.id AS id, st.user_id AS student_id, a.text AS text, a.owner AS owner, a.due_date AS due_date,
                   a.status AS status, a.created_at AS created_at, a.updated_at AS updated_at
            ORDER BY a.created_at, a.id
            """,
            sid=session_id,
        )
    )
    session["issues"] = _rows(
        tx.run(
            """
            MATCH (:Session {id: $sid})-[:RAISED]->(i:Issue)-[:ABOUT]->(st:Student)
            RETURN i.id AS id, st.user_id AS student_id, i.category AS category, i.text AS text, i.status AS status,
                   coalesce(i.escalated, false) AS escalated, coalesce(i.confidential, false) AS confidential,
                   i.raised_by AS raised_by, i.raised_by_role AS raised_by_role, i.raised_at AS raised_at,
                   i.resolved_at AS resolved_at, i.resolution AS resolution
            ORDER BY i.raised_at, i.id
            """,
            sid=session_id,
        )
    )
    return session


def confirm_attendance(tx, session_id: str, student_id: str, now: str) -> None:
    """Idempotent: `confirmed_at` is set only when it is still empty."""
    tx.run(
        """
        MATCH (:Session {id: $sid})-[r:ATTENDED_BY]->(:Student {user_id: $stid})
        WHERE r.confirmed_at IS NULL
        SET r.confirmed_at = $now
        """,
        sid=session_id,
        stid=student_id,
        now=now,
    ).consume()


def set_feedback(tx, session_id: str, student_id: str, feedback: str, comment: str | None) -> None:
    """A second submission replaces the first (AC-034.1)."""
    tx.run(
        """
        MATCH (:Session {id: $sid})-[r:ATTENDED_BY]->(:Student {user_id: $stid})
        SET r.feedback = $feedback, r.feedback_comment = $comment
        """,
        sid=session_id, stid=student_id, feedback=feedback, comment=comment,
    ).consume()


# ---- action items ----------------------------------------------------------------------------------------------------


def get_action_item(tx, item_id: str) -> dict[str, Any] | None:
    record = tx.run(
        """
        MATCH (f:Faculty)-[:LOGGED]->(s:Session)-[:CREATED]->(a:ActionItem {id: $id})-[:FOR]->(st:Student)
        RETURN a.id AS id, st.user_id AS student_id, a.text AS text, a.owner AS owner, a.due_date AS due_date,
               a.status AS status, a.created_at AS created_at, a.updated_at AS updated_at,
               s.id AS session_id, f.user_id AS author_id
        """,
        id=item_id,
    ).single()
    return record.data() if record else None


def set_action_status(tx, item_id: str, status: str, now: str) -> None:
    tx.run(
        "MATCH (a:ActionItem {id: $id}) SET a.status = $status, a.updated_at = $now", id=item_id, status=status, now=now
    ).consume()


# ---- issues ----------------------------------------------------------------------------------------------------------


def get_issue(tx, issue_id: str) -> dict[str, Any] | None:
    record = tx.run(
        """
        MATCH (i:Issue {id: $id})-[:ABOUT]->(st:Student)
        RETURN i.id AS id, st.user_id AS student_id, st.dept_code AS dept_code,
               i.category AS category, i.text AS text, i.status AS status,
               coalesce(i.escalated, false) AS escalated, coalesce(i.confidential, false) AS confidential,
               i.raised_by AS raised_by, i.raised_by_role AS raised_by_role, i.raised_at AS raised_at,
               i.resolved_at AS resolved_at, i.resolution AS resolution
        """,
        id=issue_id,
    ).single()
    return record.data() if record else None


def update_issue(tx, issue_id: str, props: dict[str, Any]) -> None:
    """Set only the given properties (status, resolution, resolved_at, escalated, confidential)."""
    tx.run("MATCH (i:Issue {id: $id}) SET i += $props", id=issue_id, props=props).consume()


def hod_ids(tx, dept_code: str) -> list[str]:
    return [
        r["id"]
        for r in tx.run(
            "MATCH (h:Staff {role: 'hod', dept_code: $d}) RETURN h.user_id AS id ORDER BY h.user_id", d=dept_code
        )
    ]


def assigned_mentor_id(tx, student_id: str) -> str | None:
    record = tx.run(
        "MATCH (f:Faculty)-[:MENTORS {type: 'assigned', status: 'active'}]->(:Student {user_id: $sid}) "
        "RETURN f.user_id AS id LIMIT 1",
        sid=student_id,
    ).single()
    return record["id"] if record else None


def session_logged_by(tx, session_id: str, faculty_id: str) -> bool:
    return bool(
        tx.run(
            "RETURN EXISTS { MATCH (:Faculty {user_id: $f})-[:LOGGED]->(:Session {id: $s}) } AS ok",
            f=faculty_id,
            s=session_id,
        ).single()["ok"]
    )
