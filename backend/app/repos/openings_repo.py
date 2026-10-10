"""Cypher for creating, editing and reading the v2 fields of openings (ENT-04, plan: profiles-and-matching-plan.md).

Reads of the fit itself belong to P1's match router; this file holds the structure around it: capacity, eligibility
inputs, preferred skills and the faculty member's research areas.
"""
from typing import Any

_ROW = """
    o.id AS id, o.title AS title, o.description AS description, o.status AS status, o.created_at AS created_at,
    f.user_id AS faculty_id, f.name AS faculty_name, f.dept_code AS faculty_dept,
    coalesce(o.positions, 1) AS positions, o.deadline AS deadline, coalesce(o.eligible_years, []) AS eligible_years,
    o.min_cgpa AS min_cgpa, coalesce(o.allowed_departments, []) AS allowed_departments,
    coalesce(o.eligibility_mode, 'advisory') AS eligibility_mode, o.mode AS mode,
    o.duration_weeks AS duration_weeks, o.hours_per_week AS hours_per_week,
    [(o)-[:REQUIRES]->(c:Concept) | c.name] AS required_skills,
    [(o)-[:PREFERS]->(p:Concept) | p.name] AS preferred_skills,
    COUNT { (o)<-[:APPLIED_TO]-(:Student) } AS applicant_count,
    COUNT { (o)<-[a:APPLIED_TO]-(:Student) WHERE a.status IN ['accepted', 'completed'] } AS accepted_count,
    f.max_guided_students AS max_guided_students, coalesce(f.accepting_guides, true) AS accepting_guides,
    COUNT { (f)-[:MENTORS {type: 'guide', status: 'active'}]->(:Student) } AS guided_students,
    [(f)-[:RESEARCHES]->(r:Concept) | r.name] AS faculty_research,
    [(f)-[:EXPERT_IN]->(e:Concept) | e.name] AS faculty_expertise
"""


def create(tx, faculty_id: str, opening: dict[str, Any], extra: dict[str, Any]) -> None:
    tx.run(
        """
        MATCH (f:Faculty {user_id: $fid})
        CREATE (o:Opening {id: $id, title: $title, description: $description, status: 'open', created_at: $now})
        SET o += $extra
        CREATE (f)-[:POSTED]->(o)
        """,
        fid=faculty_id, extra=extra, **opening,
    ).consume()


def set_props(tx, opening_id: str, props: dict[str, Any]) -> None:
    """Set only the given properties; a None value clears the property."""
    if props:
        tx.run("MATCH (o:Opening {id: $oid}) SET o += $props", oid=opening_id, props=props).consume()


def require_concept(tx, opening_id: str, name: str) -> None:
    """The Concept must already exist (`MERGE` here would create it without an embedding)."""
    tx.run(
        "MATCH (o:Opening {id: $oid}), (c:Concept {name: $name}) MERGE (o)-[:REQUIRES]->(c)",
        oid=opening_id, name=name,
    ).consume()


def prefer_concept(tx, opening_id: str, name: str) -> None:
    tx.run(
        "MATCH (o:Opening {id: $oid}), (c:Concept {name: $name}) MERGE (o)-[:PREFERS]->(c)",
        oid=opening_id, name=name,
    ).consume()


def clear_requires(tx, opening_id: str) -> None:
    tx.run("MATCH (:Opening {id: $oid})-[r:REQUIRES]->() DELETE r", oid=opening_id).consume()


def clear_prefers(tx, opening_id: str) -> None:
    tx.run("MATCH (:Opening {id: $oid})-[r:PREFERS]->() DELETE r", oid=opening_id).consume()


def owner_id(tx, opening_id: str) -> str | None:
    record = tx.run(
        "MATCH (f:Faculty)-[:POSTED]->(:Opening {id: $oid}) RETURN f.user_id AS id", oid=opening_id
    ).single()
    return record["id"] if record else None


def get(tx, opening_id: str) -> dict[str, Any] | None:
    record = tx.run(
        f"MATCH (f:Faculty)-[:POSTED]->(o:Opening {{id: $oid}}) RETURN {_ROW}", oid=opening_id
    ).single()
    return record.data() if record else None


def rows(tx, include_closed: bool = False, limit: int = 50) -> list[dict[str, Any]]:
    """Every (open) opening with the structure eligibility and recommendations need."""
    return [
        r.data()
        for r in tx.run(
            f"""
            MATCH (f:Faculty)-[:POSTED]->(o:Opening)
            WHERE $closed OR o.status = 'open'
            RETURN {_ROW}
            ORDER BY o.created_at DESC, o.id
            LIMIT $limit
            """,
            closed=include_closed,
            limit=limit,
        )
    ]


def has_applied(tx, student_id: str, opening_id: str) -> bool:
    return bool(
        tx.run(
            "RETURN EXISTS { MATCH (:Student {user_id: $sid})-[:APPLIED_TO]->(:Opening {id: $oid}) } AS ok",
            sid=student_id, oid=opening_id,
        ).single()["ok"]
    )


def close(tx, opening_id: str) -> None:
    tx.run("MATCH (o:Opening {id: $oid}) SET o.status = 'closed'", oid=opening_id).consume()
