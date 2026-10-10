"""Cypher for the fit endpoints (API-012/013/015/016/020/021). Owner: P1.

Each endpoint gets its inputs from one read query where it can: the scorer needs
the required concepts, the student's trust levels, the SIMILAR_TO pairs and both
embeddings, and fetching them separately would turn one Fit Check into five
round trips.

`embedding` never leaves this layer in a response - it is read for the cosine
and dropped (SEC-01).
"""

from __future__ import annotations

from typing import Any

# -- IDF over open openings (ai-system 4) -------------------------------------

IDF_TABLE = """
MATCH (o:Opening {status: 'open'})
WITH count(o) AS total
MATCH (o2:Opening {status: 'open'})-[:REQUIRES]->(c:Concept)
RETURN total AS open_openings, c.name AS concept, count(DISTINCT o2) AS df
"""


def idf_table(tx) -> dict[str, float]:
    """{concept: idf} over open openings, for every required concept.

    A skill that every opening asks for carries little information; a rare one
    distinguishes candidates. Computed on read: with at most 12 openings there
    is nothing to cache (A-11).
    """
    from app.ml.scorer import idf

    rows = list(tx.run(IDF_TABLE))
    if not rows:
        return {}
    open_openings = int(rows[0]["open_openings"])
    return {r["concept"]: idf(r["concept"], open_openings, int(r["df"])) for r in rows}


def open_opening_count(tx) -> int:
    rec = tx.run(
        "MATCH (o:Opening {status: 'open'}) RETURN count(o) AS n"
    ).single()
    return int(rec["n"]) if rec else 0


# -- One student's skills, with the first proving certificate -----------------

STUDENT_SKILLS = """
MATCH (s:Student {user_id: $student_id})-[r:HAS_SKILL]->(c:Concept)
OPTIONAL MATCH (s)-[:SUBMITTED]->(e:Evidence {status: 'certified'})-[:PROVES]->(c)
WITH c.name AS concept, r.trust_level AS trust_level,
     collect({id: e.id, title: e.title})[0] AS first_evidence
RETURN concept, trust_level, first_evidence
"""


def student_skills(tx, student_id: str) -> tuple[dict[str, int], dict[str, dict[str, str]]]:
    """({concept: trust_level}, {concept: {evidence_id, title}})."""
    skills: dict[str, int] = {}
    sources: dict[str, dict[str, str]] = {}
    for row in tx.run(STUDENT_SKILLS, student_id=student_id):
        concept = row["concept"]
        skills[concept] = int(row["trust_level"] or 0)
        ev = row["first_evidence"] or {}
        if ev.get("id"):
            sources[concept] = {"evidence_id": ev["id"], "title": ev.get("title") or ""}
    return skills, sources


# -- Everything one Fit Check needs, in one query -----------------------------

FIT_INPUTS = """
MATCH (o:Opening {id: $opening_id})
OPTIONAL MATCH (o)-[:REQUIRES]->(rc:Concept)
WITH o, collect(DISTINCT rc.name) AS required
MATCH (s:Student {user_id: $student_id})
RETURN o.id          AS opening_id,
       o.title       AS opening_title,
       o.status      AS opening_status,
       o.embedding   AS opening_embedding,
       required      AS required,
       s.embedding   AS student_embedding
"""


def fit_inputs(tx, opening_id: str, student_id: str) -> dict[str, Any] | None:
    rec = tx.run(FIT_INPUTS, opening_id=opening_id, student_id=student_id).single()
    return dict(rec) if rec else None


SIMILAR_PAIRS = """
MATCH (a:Concept)-[r:SIMILAR_TO]-(b:Concept)
WHERE a.name IN $names OR b.name IN $names
RETURN a.name AS a, b.name AS b, r.score AS score
"""


def similar_pairs(tx, names: list[str]) -> dict[tuple[str, str], float]:
    """{(a, b): score} in both directions, so the scorer need not care which
    way the undirected edge was stored (ENT-20)."""
    out: dict[tuple[str, str], float] = {}
    if not names:
        return out
    for row in tx.run(SIMILAR_PAIRS, names=names):
        a, b, score = row["a"], row["b"], float(row["score"])
        out[(a, b)] = score
        out[(b, a)] = score
    return out


# -- Openings list (API-012 / API-013) ----------------------------------------

OPEN_OPENINGS = """
MATCH (f:Faculty)-[:POSTED]->(o:Opening)
WHERE $include_closed OR o.status = 'open'
OPTIONAL MATCH (o)-[:REQUIRES]->(c:Concept)
WITH o, f, collect(DISTINCT c.name) AS required_skills
RETURN o.id AS id, o.title AS title, o.status AS status,
       o.description AS description, o.created_at AS created_at,
       o.embedding AS embedding,
       f.user_id AS faculty_id, f.name AS faculty_name,
       required_skills AS required_skills
ORDER BY o.created_at DESC
LIMIT $limit
"""


def openings(tx, include_closed: bool = False, limit: int = 50) -> list[dict[str, Any]]:
    return [
        dict(r)
        for r in tx.run(OPEN_OPENINGS, include_closed=include_closed, limit=limit)
    ]


def opening_detail(tx, opening_id: str) -> dict[str, Any] | None:
    rec = tx.run(
        """
        MATCH (f:Faculty)-[:POSTED]->(o:Opening {id: $opening_id})
        OPTIONAL MATCH (o)-[:REQUIRES]->(c:Concept)
        OPTIONAL MATCH (:Student)-[a:APPLIED_TO]->(o)
        RETURN o.id AS id, o.title AS title, o.description AS description,
               o.status AS status, o.created_at AS created_at,
               o.embedding AS embedding,
               f.user_id AS faculty_id, f.name AS faculty_name,
               collect(DISTINCT c.name) AS required_skills,
               count(DISTINCT a) AS applicant_count
        """,
        opening_id=opening_id,
    ).single()
    return dict(rec) if rec else None


def my_application_statuses(tx, student_id: str) -> dict[str, str]:
    """{opening_id: status} for the caller, so API-012 can show the pill."""
    return {
        r["opening_id"]: r["status"]
        for r in tx.run(
            """
            MATCH (s:Student {user_id: $student_id})-[a:APPLIED_TO]->(o:Opening)
            RETURN o.id AS opening_id, a.status AS status
            """,
            student_id=student_id,
        )
    }


def student_embedding(tx, student_id: str) -> list[float] | None:
    rec = tx.run(
        "MATCH (s:Student {user_id: $student_id}) RETURN s.embedding AS embedding",
        student_id=student_id,
    ).single()
    return list(rec["embedding"]) if rec and rec["embedding"] else None


# -- Candidates (API-016, REQ-005: applicants only, never a talent search) ----

APPLICANTS = """
MATCH (s:Student)-[a:APPLIED_TO]->(o:Opening {id: $opening_id})
RETURN a.id AS application_id, a.status AS status,
       a.applied_at AS applied_at, a.updated_at AS updated_at,
       s.user_id AS student_id, s.name AS name, s.roll_no AS roll_no,
       s.year AS year, s.embedding AS student_embedding
ORDER BY a.applied_at
"""


def applicants(tx, opening_id: str) -> list[dict[str, Any]]:
    return [dict(r) for r in tx.run(APPLICANTS, opening_id=opening_id)]


# -- Skill gaps (API-021) -----------------------------------------------------

REQUIRED_BY_OPEN_OPENINGS = """
MATCH (o:Opening {status: 'open'})-[:REQUIRES]->(c:Concept)
RETURN o.id AS opening_id, o.title AS title, o.embedding AS embedding,
       collect(DISTINCT c.name) AS required
"""


def required_by_open_openings(tx) -> list[dict[str, Any]]:
    """Every open opening with its requirements, for the skill-gap sweep."""
    return [dict(r) for r in tx.run(REQUIRED_BY_OPEN_OPENINGS)]
