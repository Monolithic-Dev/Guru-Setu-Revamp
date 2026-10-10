"""Seed-time ML hooks, called from `scripts/seed.py`.

P4 owns `seed.py` and adds the calls; P1 owns what they call. The signatures
here are the seam (parallel-work 4) and do not change without telling P4.
"""

from __future__ import annotations

import logging

from app.ml import concepts, embedding
from app.repos import ml_repo

log = logging.getLogger(__name__)


def seed_embeddings(tx) -> dict[str, int]:
    """Embed every Student and Opening in one pass.

    Batched through one `embed` call per entity type: MiniLM amortises far
    better over a batch than over 60 single calls, which keeps the seed inside
    its 60-second budget (G1).
    """
    student_ids = ml_repo.all_student_ids(tx)
    student_texts = []
    kept_students = []
    for sid in student_ids:
        parts = ml_repo.student_text_parts(tx, sid)
        if parts is None:
            continue
        kept_students.append(sid)
        student_texts.append(embedding.student_text(parts))
    for sid, vector in zip(kept_students, embedding.embed(student_texts), strict=True):
        ml_repo.write_student_embedding(tx, sid, vector)

    opening_ids = ml_repo.all_opening_ids(tx)
    opening_texts = []
    kept_openings = []
    for oid in opening_ids:
        parts = ml_repo.opening_text_parts(tx, oid)
        if parts is None:
            continue
        kept_openings.append(oid)
        opening_texts.append(embedding.opening_text(parts))
    for oid, vector in zip(kept_openings, embedding.embed(opening_texts), strict=True):
        ml_repo.write_opening_embedding(tx, oid, vector)

    stats = {"students": len(kept_students), "openings": len(kept_openings)}
    log.info("seed embeddings written", extra=stats)
    return stats


def embed_concepts(tx) -> int:
    """Embed every Concept that has no vector yet.

    The seed creates Concept nodes first and builds vectors afterwards, so this
    has to run before `seed_similarity`: `rebuild_similarity` only considers
    concepts that already have an embedding, and would otherwise build nothing.
    One batched encode rather than one call per concept.
    """
    names = ml_repo.concepts_missing_embeddings(tx)
    if not names:
        return 0
    for name, vector in zip(names, embedding.embed(names), strict=True):
        ml_repo.write_concept_embedding(tx, name, vector)
    log.info("concept embeddings written", extra={"concepts": len(names)})
    return len(names)


def seed_similarity(tx) -> dict[str, int]:
    """Embed any new concepts, then rebuild SIMILAR_TO over all of them."""
    embed_concepts(tx)
    return concepts.rebuild_similarity(tx)
