"""Cypher for the richer student profile (plan: profiles-and-matching-plan.md): the extra student properties,
skill levels, projects, the current resume, the institutional CGPA record and the concept typeahead.

Every function takes a transaction. Nothing here returns `password_hash` or `embedding`. All queries are parameterised.
"""
from typing import Any

from app.repos.students_repo import endorser_names


def _rows(result) -> list[dict[str, Any]]:
    return [record.data() for record in result]


def student_core(tx, student_id: str) -> dict[str, Any] | None:
    record = tx.run(
        """
        MATCH (s:Student {user_id: $sid})
        RETURN s.user_id AS user_id, s.name AS name, s.roll_no AS roll_no, s.year AS year, s.dept_code AS dept_code,
               s.programme AS programme, s.headline AS headline, s.bio AS bio,
               coalesce(s.interests, []) AS interests, coalesce(s.links, []) AS links,
               s.availability_hours AS availability_hours, s.available_from AS available_from,
               coalesce(s.preferences, []) AS preferences,
               coalesce(s.open_to_opportunities, false) AS open_to_opportunities,
               s.self_reported_cgpa AS self_reported_cgpa
        """,
        sid=student_id,
    ).single()
    return record.data() if record else None


def academic_records(tx, student_id: str) -> list[dict[str, Any]]:
    """The institutional record `[MOCK]`, newest term id first."""
    return _rows(
        tx.run(
            """
            MATCH (:Student {user_id: $sid})-[:HAS_RECORD]->(r:AcademicRecord)
            RETURN r.term_id AS term_id, r.cgpa AS cgpa, r.attendance_pct AS attendance_pct
            ORDER BY r.term_id DESC
            """,
            sid=student_id,
        )
    )


def skill_rows(tx, student_id: str) -> list[dict[str, Any]]:
    """Every HAS_SKILL edge with the titles of the certificates that prove it."""
    rows = _rows(
        tx.run(
            """
            MATCH (:Student {user_id: $sid})-[h:HAS_SKILL]->(c:Concept)
            RETURN c.name AS concept, coalesce(h.trust_level, 0) AS trust_level, coalesce(h.claimed, false) AS claimed,
                   h.level AS level, coalesce(h.endorsed_by, []) AS endorsed_by,
                   coalesce(h.evidence_ids, []) AS evidence_ids
            ORDER BY h.trust_level DESC, c.name
            """,
            sid=student_id,
        )
    )
    endorser_names(tx, rows)
    ids = sorted({eid for row in rows for eid in row["evidence_ids"]})
    titles = (
        {
            r["id"]: r["title"]
            for r in tx.run(
                "MATCH (e:Evidence) WHERE e.id IN $ids RETURN e.id AS id, coalesce(e.title, 'Certificate') AS title",
                ids=ids,
            )
        }
        if ids
        else {}
    )
    for row in rows:
        row["sources"] = [{"evidence_id": e, "title": titles.get(e, "Certificate")} for e in row.pop("evidence_ids")]
    return rows


def set_skill_levels(tx, student_id: str, levels: dict[str, str | None]) -> None:
    """Self-assessed level per skill (None clears it). It never touches `trust_level`."""
    if levels:
        tx.run(
            """
            UNWIND $rows AS r
            MATCH (:Student {user_id: $sid})-[h:HAS_SKILL]->(:Concept {name: r.concept})
            SET h.level = r.level
            """,
            sid=student_id,
            rows=[{"concept": k, "level": v} for k, v in levels.items()],
        ).consume()


def projects(tx, student_id: str) -> list[dict[str, Any]]:
    return _rows(
        tx.run(
            """
            MATCH (:Student {user_id: $sid})-[:HAS_PROJECT]->(p:Project)
            RETURN p.id AS id, p.title AS title, p.description AS description, p.link AS link,
                   coalesce(p.skills, []) AS skills
            ORDER BY p.position, p.id
            """,
            sid=student_id,
        )
    )


def replace_projects(tx, student_id: str, items: list[dict[str, Any]]) -> None:
    """Full-list replacement (the project has no DELETE routes)."""
    tx.run(
        "MATCH (:Student {user_id: $sid})-[:HAS_PROJECT]->(p:Project) DETACH DELETE p", sid=student_id
    ).consume()
    if items:
        tx.run(
            """
            MATCH (s:Student {user_id: $sid})
            UNWIND $items AS i
            CREATE (s)-[:HAS_PROJECT]->(:Project {id: i.id, title: i.title, description: i.description,
                   link: i.link, skills: i.skills, position: i.position})
            """,
            sid=student_id,
            items=items,
        ).consume()


def certified_count(tx, student_id: str) -> int:
    return tx.run(
        "MATCH (:Student {user_id: $sid})-[:SUBMITTED]->(e:Evidence {status: 'certified'}) RETURN count(e) AS n",
        sid=student_id,
    ).single()["n"]


def current_resume(tx, student_id: str) -> dict[str, Any] | None:
    record = tx.run(
        """
        MATCH (:Student {user_id: $sid})-[:HAS_RESUME]->(r:Resume {status: 'current'})
        RETURN r.id AS id, r.uploaded_at AS uploaded_at, r.size_bytes AS size_bytes, r.pages AS pages,
               r.status AS status, r.file_path AS file_path
        """,
        sid=student_id,
    ).single()
    return record.data() if record else None


def add_resume(tx, student_id: str, resume: dict[str, Any]) -> None:
    """The new resume becomes `current`; every earlier one is marked `superseded` (kept, never deleted)."""
    tx.run(
        """
        MATCH (s:Student {user_id: $sid})
        OPTIONAL MATCH (s)-[:HAS_RESUME]->(old:Resume {status: 'current'})
        SET old.status = 'superseded'
        CREATE (s)-[:HAS_RESUME]->(:Resume {id: $id, file_path: $file_path, sha256: $sha256, size_bytes: $size_bytes,
               pages: $pages, uploaded_at: $uploaded_at, status: 'current'})
        """,
        sid=student_id,
        **resume,
    ).consume()


def search_concepts(tx, query: str, limit: int = 10) -> list[str]:
    return [
        r["name"]
        for r in tx.run(
            """
            MATCH (c:Concept) WHERE $q = '' OR c.name CONTAINS $q
            RETURN c.name AS name
            ORDER BY CASE WHEN c.name STARTS WITH $q THEN 0 ELSE 1 END, c.name
            LIMIT $limit
            """,
            q=query,
            limit=limit,
        )
    ]


def all_concept_names(tx) -> list[str]:
    return [r["name"] for r in tx.run("MATCH (c:Concept) RETURN c.name AS name")]


def concept_names_known(tx, names: list[str]) -> set[str]:
    return {r["name"] for r in tx.run("MATCH (c:Concept) WHERE c.name IN $names RETURN c.name AS name", names=names)}
