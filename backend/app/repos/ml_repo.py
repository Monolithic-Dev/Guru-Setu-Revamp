"""Cypher used by `app/ml/` (embeddings, concepts, verification, trust).

Owner: P1. `ml/` holds no Cypher (AGENTS.md import rules), so every query it
needs lives here. Each function takes the `tx` that the calling service opened,
so one service call stays one transaction. Every query is parameterised.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

# ── Students and openings: embedding inputs and outputs (MDL-02) ──────────────

STUDENT_TEXT_PARTS = """
MATCH (s:Student {user_id: $student_id})
OPTIONAL MATCH (s)-[:HAS_SKILL]->(c:Concept)
WITH s, collect(DISTINCT c.name) AS skills
OPTIONAL MATCH (s)-[:SUBMITTED]->(e:Evidence {status: 'certified'})
WITH s, skills, collect(DISTINCT e.title) AS cert_titles
RETURN s.dept_code   AS dept_code,
       s.bio         AS bio,
       s.interests   AS interests,
       skills        AS skills,
       cert_titles   AS certificate_titles
"""


def student_text_parts(tx, student_id: str) -> dict[str, Any] | None:
    """Fields that `embedding.student_text` renders (ai-system §5)."""
    rec = tx.run(STUDENT_TEXT_PARTS, student_id=student_id).single()
    return dict(rec) if rec else None


OPENING_TEXT_PARTS = """
MATCH (o:Opening {id: $opening_id})
OPTIONAL MATCH (o)-[:REQUIRES]->(c:Concept)
RETURN o.title       AS title,
       o.description AS description,
       collect(DISTINCT c.name) AS required_concepts
"""


def opening_text_parts(tx, opening_id: str) -> dict[str, Any] | None:
    rec = tx.run(OPENING_TEXT_PARTS, opening_id=opening_id).single()
    return dict(rec) if rec else None


def write_student_embedding(tx, student_id: str, embedding: list[float]) -> None:
    tx.run(
        "MATCH (s:Student {user_id: $student_id}) SET s.embedding = $embedding",
        student_id=student_id,
        embedding=embedding,
    )


def write_opening_embedding(tx, opening_id: str, embedding: list[float]) -> None:
    tx.run(
        "MATCH (o:Opening {id: $opening_id}) SET o.embedding = $embedding",
        opening_id=opening_id,
        embedding=embedding,
    )


def all_student_ids(tx) -> list[str]:
    return [r["id"] for r in tx.run("MATCH (s:Student) RETURN s.user_id AS id")]


def all_opening_ids(tx) -> list[str]:
    return [r["id"] for r in tx.run("MATCH (o:Opening) RETURN o.id AS id")]


# ── Concepts and SIMILAR_TO (MDL-04) ─────────────────────────────────────────


def get_concept(tx, name: str) -> dict[str, Any] | None:
    rec = tx.run(
        "MATCH (c:Concept {name: $name}) RETURN c.name AS name, c.source AS source",
        name=name,
    ).single()
    return dict(rec) if rec else None


def create_concept(tx, name: str, source: str, embedding: list[float]) -> dict[str, Any]:
    """MERGE so a concurrent upload cannot violate the uniqueness constraint."""
    rec = tx.run(
        """
        MERGE (c:Concept {name: $name})
          ON CREATE SET c.source = $source, c.embedding = $embedding
        RETURN c.name AS name, c.source AS source
        """,
        name=name,
        source=source,
        embedding=embedding,
    ).single()
    return dict(rec)


def concepts_with_embeddings(tx) -> list[dict[str, Any]]:
    return [
        dict(r)
        for r in tx.run(
            """
            MATCH (c:Concept)
            WHERE c.embedding IS NOT NULL
            RETURN c.name AS name, c.embedding AS embedding
            ORDER BY c.name
            """
        )
    ]


def upsert_similar(tx, name_a: str, name_b: str, score: float, source: str) -> None:
    """One undirected edge per pair, stored with the smaller name first (§5)."""
    lo, hi = sorted((name_a, name_b))
    tx.run(
        """
        MATCH (a:Concept {name: $lo}), (b:Concept {name: $hi})
        MERGE (a)-[r:SIMILAR_TO]-(b)
        SET r.score = $score, r.source = $source
        """,
        lo=lo,
        hi=hi,
        score=score,
        source=source,
    )


def delete_model_similar(tx) -> None:
    """Drop model-built edges before a rebuild; overrides are re-applied after."""
    tx.run("MATCH ()-[r:SIMILAR_TO {source: 'model'}]-() DELETE r")


def similar_for_concepts(tx, names: list[str]) -> list[dict[str, Any]]:
    """SIMILAR_TO pairs touching any of `names`, queried undirected."""
    return [
        dict(r)
        for r in tx.run(
            """
            MATCH (a:Concept)-[r:SIMILAR_TO]-(b:Concept)
            WHERE a.name IN $names
            RETURN a.name AS from_name, b.name AS to_name, r.score AS score
            """,
            names=names,
        )
    ]


# -- LLM daily-call counter (ENT-15) ------------------------------------------
def get_counter(tx, name: str, date: str) -> int:
    rec = tx.run(
        "MATCH (c:Counter {name: $name, date: $date}) RETURN c.value AS value",
        name=name,
        date=date,
    ).single()
    return int(rec["value"]) if rec and rec["value"] is not None else 0


def increment_counter(tx, name: str, date: str) -> int:
    rec = tx.run(
        """
        MERGE (c:Counter {name: $name, date: $date})
          ON CREATE SET c.value = 1
          ON MATCH  SET c.value = coalesce(c.value, 0) + 1
        RETURN c.value AS value
        """,
        name=name,
        date=date,
    ).single()
    return int(rec["value"])


# -- Duplicate lookups and issuers for verification (ai-system 3) -------------
def find_by_sha256(tx, sha256: str) -> dict[str, Any] | None:
    """Rule 1. Any student, any status except `failed`: a failed row carries no
    claim, so it must not block a legitimate re-upload."""
    rec = tx.run(
        """
        MATCH (e:Evidence {sha256: $sha256})
        WHERE e.status <> 'failed'
        RETURN e.id AS id, e.status AS status
        ORDER BY e.created_at
        LIMIT 1
        """,
        sha256=sha256,
    ).single()
    return dict(rec) if rec else None


def all_phashes(tx) -> list[dict[str, Any]]:
    """Rule 2. The seed holds at most ~1,000 certificates (A-11), so a scan is
    cheaper and simpler than a vector index over 64-bit hashes."""
    return [
        dict(r)
        for r in tx.run(
            """
            MATCH (e:Evidence)
            WHERE e.phash IS NOT NULL AND e.status <> 'failed'
            RETURN e.id AS id, e.phash AS phash
            """
        )
    ]


def find_by_issuer_and_certificate_id(
    tx, issuer_normalised: str, certificate_id: str
) -> dict[str, Any] | None:
    """Rule 3. The stored issuer is normalised the same way at write time, so
    the comparison is exact rather than fuzzy."""
    rec = tx.run(
        """
        MATCH (e:Evidence {certificate_id: $certificate_id})
        WHERE e.status <> 'failed' AND toLower(trim(e.issuer)) = $issuer_normalised
        RETURN e.id AS id
        LIMIT 1
        """,
        certificate_id=certificate_id,
        issuer_normalised=issuer_normalised,
    ).single()
    return dict(rec) if rec else None


def all_issuers(tx) -> list[dict[str, Any]]:
    """Known issuers and their aliases (ENT-06), for the `issuer_known` check."""
    return [
        dict(r)
        for r in tx.run(
            "MATCH (i:Issuer) RETURN i.name AS name, i.aliases AS aliases"
        )
    ]


# -- Trust recompute (backend 6.2) -------------------------------------------
def _now_iso() -> str:
    return dt.datetime.now(tz=dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_has_skill(tx, student_id: str, concept: str) -> dict[str, Any] | None:
    rec = tx.run(
        """
        MATCH (s:Student {user_id: $student_id})-[r:HAS_SKILL]->(c:Concept {name: $concept})
        RETURN r.trust_level AS trust_level, r.claimed AS claimed,
               r.evidence_ids AS evidence_ids, r.endorsed_by AS endorsed_by
        """,
        student_id=student_id,
        concept=concept,
    ).single()
    return dict(rec) if rec else None


def ensure_has_skill(tx, student_id: str, concept: str) -> None:
    """Create the edge if a certificate proved a skill the student never claimed.

    `claimed` is left false: the certificate, not the student, is the source.
    """
    tx.run(
        """
        MATCH (s:Student {user_id: $student_id}), (c:Concept {name: $concept})
        MERGE (s)-[r:HAS_SKILL]->(c)
          ON CREATE SET r.claimed = false, r.trust_level = 0,
                        r.evidence_ids = [], r.endorsed_by = [],
                        r.updated_at = $now
        """,
        student_id=student_id,
        concept=concept,
        now=_now_iso(),
    )


def set_has_skill(
    tx, student_id: str, concept: str, trust_level: int, evidence_ids: list[str]
) -> None:
    tx.run(
        """
        MATCH (s:Student {user_id: $student_id})-[r:HAS_SKILL]->(c:Concept {name: $concept})
        SET r.trust_level = $trust_level,
            r.evidence_ids = $evidence_ids,
            r.updated_at = $now
        """,
        student_id=student_id,
        concept=concept,
        trust_level=trust_level,
        evidence_ids=evidence_ids,
        now=_now_iso(),
    )


def delete_has_skill(tx, student_id: str, concept: str) -> None:
    tx.run(
        """
        MATCH (s:Student {user_id: $student_id})-[r:HAS_SKILL]->(c:Concept {name: $concept})
        DELETE r
        """,
        student_id=student_id,
        concept=concept,
    )


def certified_evidence_ids(tx, student_id: str, concept: str) -> list[str]:
    """Ids of the student's own `certified` evidence that proves the concept."""
    return [
        r["id"]
        for r in tx.run(
            """
            MATCH (s:Student {user_id: $student_id})-[:SUBMITTED]->(e:Evidence)
            MATCH (e)-[:PROVES]->(c:Concept {name: $concept})
            WHERE e.status = 'certified'
            RETURN e.id AS id
            ORDER BY e.created_at
            """,
            student_id=student_id,
            concept=concept,
        )
    ]


def link_proves(tx, evidence_id: str, concept: str) -> None:
    tx.run(
        """
        MATCH (e:Evidence {id: $evidence_id}), (c:Concept {name: $concept})
        MERGE (e)-[:PROVES]->(c)
        """,
        evidence_id=evidence_id,
        concept=concept,
    )


def set_endorsed_by(tx, student_id: str, concept: str, endorsed_by: list[str]) -> None:
    """Record who has endorsed a skill (API-041). Trust itself is never written
    here: `trust.recompute_skill` derives it from this list."""
    tx.run(
        """
        MATCH (s:Student {user_id: $student_id})-[r:HAS_SKILL]->(c:Concept {name: $concept})
        SET r.endorsed_by = $endorsed_by, r.updated_at = $now
        """,
        student_id=student_id,
        concept=concept,
        endorsed_by=endorsed_by,
        now=_now_iso(),
    )


def concepts_missing_embeddings(tx) -> list[str]:
    """Concept names with no vector yet - the seed creates nodes before any
    embedding exists, and SIMILAR_TO cannot be built without them."""
    return [
        r["name"]
        for r in tx.run(
            """
            MATCH (c:Concept)
            WHERE c.embedding IS NULL
            RETURN c.name AS name
            ORDER BY c.name
            """
        )
    ]


def write_concept_embedding(tx, name: str, embedding: list[float]) -> None:
    tx.run(
        "MATCH (c:Concept {name: $name}) SET c.embedding = $embedding",
        name=name,
        embedding=embedding,
    )
