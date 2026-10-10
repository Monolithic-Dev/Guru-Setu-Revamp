"""Cypher for student profiles and claimed skills (ENT-01, ENT-16). Never returns `embedding` or `password_hash`."""
from typing import Any


def endorser_names(tx, rows: list[dict[str, Any]]) -> None:
    """`endorsed_by` is stored as faculty ids; every read shows the name instead (AC-027.1). Edits the rows in place."""
    ids = sorted({uid for row in rows for uid in row["endorsed_by"]})
    if not ids:
        return
    found = tx.run("MATCH (u:User) WHERE u.user_id IN $ids RETURN u.user_id AS id, u.name AS name", ids=ids)
    names = {r["id"]: r["name"] for r in found}
    for row in rows:
        row["endorsed_by"] = [names.get(uid, uid) for uid in row["endorsed_by"]]


def get_profile(tx, student_id: str) -> dict[str, Any] | None:
    """Profile fields plus trust-marked skills with the titles of their source certificates."""
    head = tx.run(
        """
        MATCH (s:Student {user_id: $sid})
        RETURN s.user_id AS user_id, s.name AS name, s.roll_no AS roll_no, s.year AS year,
               s.dept_code AS dept_code, s.bio AS bio, coalesce(s.interests, []) AS interests
        """,
        sid=student_id,
    ).single()
    if head is None:
        return None
    profile = head.data()
    skill_rows = [
        record.data()
        for record in tx.run(
            """
            MATCH (:Student {user_id: $sid})-[h:HAS_SKILL]->(c:Concept)
            RETURN c.name AS concept, h.trust_level AS trust_level, h.claimed AS claimed,
                   coalesce(h.evidence_ids, []) AS evidence_ids, coalesce(h.endorsed_by, []) AS endorsed_by
            ORDER BY h.trust_level DESC, c.name
            """,
            sid=student_id,
        )
    ]
    endorser_names(tx, skill_rows)
    evidence_ids = sorted({eid for row in skill_rows for eid in row["evidence_ids"]})
    titles = {}
    if evidence_ids:
        titles = {
            r["id"]: r["title"]
            for r in tx.run(
                "MATCH (e:Evidence) WHERE e.id IN $ids RETURN e.id AS id, coalesce(e.title, 'Certificate') AS title",
                ids=evidence_ids,
            )
        }
    profile["skills"] = [
        {
            "concept": row["concept"],
            "trust_level": row["trust_level"],
            "claimed": bool(row["claimed"]),
            "sources": [{"evidence_id": eid, "title": titles.get(eid, "Certificate")} for eid in row["evidence_ids"]],
            "endorsed_by": row["endorsed_by"],
        }
        for row in skill_rows
    ]
    return profile


def set_profile_fields(tx, student_id: str, props: dict[str, Any]) -> None:
    """Set only the provided properties (`bio`, `interests`). A None value clears the property."""
    if props:
        tx.run("MATCH (s:Student {user_id: $sid}) SET s += $props", sid=student_id, props=props).consume()


def claimed_skill_names(tx, student_id: str) -> list[str]:
    return [
        r["name"]
        for r in tx.run(
            "MATCH (:Student {user_id: $sid})-[h:HAS_SKILL {claimed: true}]->(c:Concept) RETURN c.name AS name",
            sid=student_id,
        )
    ]


def ensure_concept(tx, name: str) -> None:
    """Minimal concept creation. P1's `ml.concepts.get_or_create_concept` replaces this when it exists (it also
    embeds the concept and computes SIMILAR_TO)."""
    tx.run("MERGE (c:Concept {name: $name}) ON CREATE SET c.source = 'claimed'", name=name).consume()


def upsert_claim(tx, student_id: str, concept: str, now: str) -> None:
    tx.run(
        """
        MATCH (s:Student {user_id: $sid}), (c:Concept {name: $concept})
        MERGE (s)-[h:HAS_SKILL]->(c)
        ON CREATE SET h.trust_level = 0, h.claimed = true, h.evidence_ids = [], h.endorsed_by = [], h.updated_at = $now
        ON MATCH SET h.claimed = true, h.updated_at = $now
        """,
        sid=student_id, concept=concept, now=now,
    ).consume()


def unclaim(tx, student_id: str, concept: str, now: str) -> None:
    """Basic trust recompute (backend 6.2) for a skill the student stopped claiming: the edge is deleted unless a
    certificate or an endorsement still supports it. P1's `ml.trust.recompute_skill` handles the full ladder."""
    tx.run(
        """
        MATCH (:Student {user_id: $sid})-[h:HAS_SKILL]->(c:Concept {name: $concept})
        SET h.claimed = false, h.updated_at = $now
        WITH h, size(coalesce(h.evidence_ids, [])) + size(coalesce(h.endorsed_by, [])) AS support
        FOREACH (_ IN CASE WHEN support = 0 THEN [1] ELSE [] END | DELETE h)
        """,
        sid=student_id, concept=concept, now=now,
    ).consume()
