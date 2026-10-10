"""Cypher for applications (ENT-18) and the guide links they create (ENT-17)."""
from typing import Any

_APP_FIELDS = """
    a.id AS id, o.id AS opening_id, o.title AS opening_title, s.user_id AS student_id,
    s.name AS student_name, f.user_id AS owner_id, f.name AS owner_name, o.status AS opening_status,
    a.status AS status, a.applied_at AS applied_at, a.updated_at AS updated_at
"""


def get_opening(tx, opening_id: str) -> dict[str, Any] | None:
    record = tx.run(
        """
        MATCH (o:Opening {id: $oid})
        OPTIONAL MATCH (f:Faculty)-[:POSTED]->(o)
        RETURN o.id AS id, o.title AS title, o.status AS status, f.user_id AS owner_id, f.name AS owner_name
        """,
        oid=opening_id,
    ).single()
    return record.data() if record else None


def create_application(tx, student_id: str, opening_id: str, application_id: str, now: str) -> bool:
    """MERGE on the relationship: True if this call created it, False if the student had already applied."""
    record = tx.run(
        """
        MATCH (s:Student {user_id: $sid}), (o:Opening {id: $oid})
        MERGE (s)-[a:APPLIED_TO]->(o)
        ON CREATE SET a.id = $aid, a.status = 'pending', a.applied_at = $now, a.updated_at = $now
        RETURN a.id = $aid AS created
        """,
        sid=student_id, oid=opening_id, aid=application_id, now=now,
    ).single()
    return bool(record and record["created"])


def get_application(tx, application_id: str) -> dict[str, Any] | None:
    record = tx.run(
        f"""
        MATCH (s:Student)-[a:APPLIED_TO {{id: $aid}}]->(o:Opening)
        OPTIONAL MATCH (f:Faculty)-[:POSTED]->(o)
        RETURN {_APP_FIELDS}
        """,
        aid=application_id,
    ).single()
    return record.data() if record else None


def list_for_student(tx, student_id: str) -> list[dict[str, Any]]:
    return [
        r.data()
        for r in tx.run(
            f"""
            MATCH (s:Student {{user_id: $sid}})-[a:APPLIED_TO]->(o:Opening)
            OPTIONAL MATCH (f:Faculty)-[:POSTED]->(o)
            RETURN {_APP_FIELDS}
            ORDER BY a.applied_at DESC
            """,
            sid=student_id,
        )
    ]


def set_status(tx, application_id: str, status: str, now: str) -> None:
    tx.run(
        "MATCH ()-[a:APPLIED_TO {id: $aid}]->() SET a.status = $status, a.updated_at = $now",
        aid=application_id, status=status, now=now,
    ).consume()


def ensure_guide_link(tx, faculty_id: str, student_id: str, opening_id: str, link_id: str, since: str) -> str:
    """Create (or reactivate) the active `guide` MENTORS link for an accepted applicant; returns its id."""
    record = tx.run(
        """
        MATCH (f:Faculty {user_id: $fid}), (s:Student {user_id: $sid})
        MERGE (f)-[m:MENTORS {type: 'guide', opening_id: $oid}]->(s)
        ON CREATE SET m.id = $mid, m.since = $since
        SET m.status = 'active', m.until = null, m.end_reason = null
        RETURN m.id AS id
        """,
        fid=faculty_id, sid=student_id, oid=opening_id, mid=link_id, since=since,
    ).single()
    return record["id"]


def end_guide_link(tx, faculty_id: str, student_id: str, opening_id: str, until: str) -> str | None:
    """End the guide link when the application is completed. Returns the link id, or None if there is none."""
    record = tx.run(
        """
        MATCH (:Faculty {user_id: $fid})-[m:MENTORS {type: 'guide', opening_id: $oid}]->(:Student {user_id: $sid})
        SET m.status = 'ended', m.until = $until, m.end_reason = 'completed'
        RETURN m.id AS id
        """,
        fid=faculty_id, sid=student_id, oid=opening_id, until=until,
    ).single()
    return record["id"] if record else None
