"""Cypher for creating openings (ENT-04). Reads of openings belong to P1's match router."""
from typing import Any


def create(tx, faculty_id: str, opening: dict[str, Any]) -> None:
    tx.run(
        """
        MATCH (f:Faculty {user_id: $fid})
        CREATE (o:Opening {id: $id, title: $title, description: $description, status: 'open', created_at: $now})
        CREATE (f)-[:POSTED]->(o)
        """,
        fid=faculty_id, **opening,
    ).consume()


def require_concept(tx, opening_id: str, name: str) -> None:
    """The Concept must already exist (`MERGE` here would create it without an embedding)."""
    tx.run(
        "MATCH (o:Opening {id: $oid}), (c:Concept {name: $name}) MERGE (o)-[:REQUIRES]->(c)",
        oid=opening_id, name=name,
    ).consume()


def get(tx, opening_id: str) -> dict[str, Any] | None:
    record = tx.run(
        """
        MATCH (f:Faculty)-[:POSTED]->(o:Opening {id: $oid})
        RETURN o.id AS id, o.title AS title, o.description AS description, o.status AS status,
               o.created_at AS created_at, f.user_id AS faculty_id, f.name AS faculty_name,
               [(o)-[:REQUIRES]->(c:Concept) | c.name] AS required_skills,
               COUNT { (o)<-[:APPLIED_TO]-(:Student) } AS applicant_count
        """,
        oid=opening_id,
    ).single()
    return record.data() if record else None
