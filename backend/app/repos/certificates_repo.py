"""Cypher for certificates (Evidence, ENT-05). Never returns `file_path` except through `get_file_path`
(the only caller is the file route, which checks scope first)."""
from typing import Any

# Fields of the `Certificate` response model. `file_path` and `duplicate_of` are deliberately absent.
CERT_FIELDS = """
    e.id AS id, e.status AS status, e.media_type AS media_type, e.holder_name AS holder_name, e.title AS title,
    e.issuer AS issuer, e.issue_date AS issue_date, e.level AS level, e.type AS type,
    coalesce(e.skills, []) AS skills, e.certificate_id AS certificate_id, e.verify_url AS verify_url,
    e.confidence AS confidence, coalesce(e.reasons, []) AS reasons, e.source AS source,
    e.review_reason AS review_reason, e.created_at AS created_at, e.updated_at AS updated_at,
    coalesce(e.kind, 'certificate') AS kind, e.summary AS summary, e.output_type AS output_type,
    e.recorded_by AS recorded_by
"""


def list_for_student(tx, student_id: str, limit: int = 100) -> list[dict[str, Any]]:
    return [
        r.data()
        for r in tx.run(
            f"""
            MATCH (:Student {{user_id: $sid}})-[:SUBMITTED]->(e:Evidence)
            RETURN {CERT_FIELDS}
            ORDER BY e.created_at DESC, e.id
            LIMIT $limit
            """,
            sid=student_id,
            limit=limit,
        )
    ]


def create(tx, student_id: str, ev: dict[str, Any]) -> None:
    tx.run(
        """
        MATCH (s:Student {user_id: $sid})
        CREATE (s)-[:SUBMITTED]->(e:Evidence)
        SET e = $ev
        """,
        sid=student_id,
        ev=ev,
    ).consume()


def get_with_owner(tx, evidence_id: str) -> dict[str, Any] | None:
    """Certificate fields plus the owner's id/name/roll_no and the reviewer-only `duplicate_of`."""
    record = tx.run(
        f"""
        MATCH (s:Student)-[:SUBMITTED]->(e:Evidence {{id: $id}})
        RETURN {CERT_FIELDS}, s.user_id AS owner_id, s.name AS owner_name, s.roll_no AS owner_roll_no,
               e.duplicate_of AS duplicate_of
        """,
        id=evidence_id,
    ).single()
    return record.data() if record else None


def get_job(tx, evidence_id: str) -> dict[str, Any] | None:
    """What JOB-01 needs: status, stored file and the owner as the verifier sees them. `file_path` stays internal."""
    record = tx.run(
        """
        MATCH (s:Student)-[:SUBMITTED]->(e:Evidence {id: $id})
        RETURN e.status AS status, e.file_path AS file_path, e.media_type AS media_type,
               s.user_id AS user_id, s.name AS name, s.dept_code AS dept_code, s.roll_no AS roll_no,
               s.enrolled_on AS enrolled_on
        """,
        id=evidence_id,
    ).single()
    return record.data() if record else None


def file_path_of(tx, evidence_id: str) -> tuple[str, str] | None:
    record = tx.run(
        "MATCH (e:Evidence {id: $id}) RETURN e.file_path AS path, e.media_type AS media_type", id=evidence_id
    ).single()
    return (record["path"], record["media_type"]) if record else None


def update(tx, evidence_id: str, props: dict[str, Any]) -> None:
    tx.run("MATCH (e:Evidence {id: $id}) SET e += $props", id=evidence_id, props=props).consume()


def current_status(tx, evidence_id: str) -> str | None:
    record = tx.run("MATCH (e:Evidence {id: $id}) RETURN e.status AS status", id=evidence_id).single()
    return record["status"] if record else None


def review_queue(tx, role: str, user_id: str, dept_code: str, limit: int = 100) -> list[dict[str, Any]]:
    """`needs_review` certificates: a faculty member's assigned mentees, or the HOD's whole department."""
    scope = (
        "MATCH (:Faculty {user_id: $uid})-[:MENTORS {type: 'assigned', status: 'active'}]->(s:Student)"
        if role == "faculty"
        else "MATCH (s:Student {dept_code: $dept})"
    )
    return [
        r.data()
        for r in tx.run(
            f"""
            {scope}
            MATCH (s)-[:SUBMITTED]->(e:Evidence {{status: 'needs_review'}})
            RETURN {CERT_FIELDS}, s.user_id AS owner_id, s.name AS owner_name, s.roll_no AS owner_roll_no,
                   e.duplicate_of AS duplicate_of
            ORDER BY e.created_at, e.id
            LIMIT $limit
            """,
            uid=user_id,
            dept=dept_code,
            limit=limit,
        )
    ]


def assigned_mentor_id(tx, student_id: str) -> str | None:
    record = tx.run(
        "MATCH (f:Faculty)-[:MENTORS {type: 'assigned', status: 'active'}]->(:Student {user_id: $sid}) "
        "RETURN f.user_id AS id LIMIT 1",
        sid=student_id,
    ).single()
    return record["id"] if record else None


def issuer_known(tx, name: str) -> bool:
    """Case-insensitive match on an Issuer name or alias (ENT-06)."""
    return bool(
        tx.run(
            """
            RETURN EXISTS {
              MATCH (i:Issuer)
              WHERE toLower(i.name) = toLower($n) OR any(a IN coalesce(i.aliases, []) WHERE toLower(a) = toLower($n))
            } AS ok
            """,
            n=name,
        ).single()["ok"]
    )


def stale_processing(tx, cutoff: str) -> list[dict[str, Any]]:
    """JOB-02: evidence still `processing` since before `cutoff`, with the owner and the title for the notification."""
    return [
        r.data()
        for r in tx.run(
            """
            MATCH (s:Student)-[:SUBMITTED]->(e:Evidence {status: 'processing'}) WHERE e.updated_at < $cutoff
            RETURN e.id AS id, e.title AS title, s.user_id AS user_id
            """,
            cutoff=cutoff,
        )
    ]


def student_skill_names(tx, student_id: str) -> set[str]:
    return {r["name"] for r in tx.run(
        "MATCH (:Student {user_id: $sid})-[:HAS_SKILL]->(c:Concept) RETURN c.name AS name", sid=student_id)}
