"""Trust recompute (backend 6.2). Deterministic; no model involved.

A skill's trust level is derived, never stored by hand:
  2  an endorsement exists (P2, API-041)
  1  a certified certificate proves it
  0  the student merely claims it
  -  neither: the HAS_SKILL edge is removed entirely

Every path that could change the answer calls `recompute_skill`: a certificate
becoming certified or rejected, a profile edit, an endorsement.
"""

from __future__ import annotations

import logging

from app.ml import concepts, embedding
from app.repos import ml_repo

log = logging.getLogger(__name__)

# A-10: starting values, tuned only against EVAL-03 before the core freeze.
TRUST_WEIGHTS = {0: 0.40, 1: 0.85, 2: 1.00}


def apply_certified(tx, student_id: str, evidence_id: str, skills: list[str]) -> list[str]:
    """Link a newly certified certificate to its concepts and refresh trust.

    Called inside P2's write transaction when an Evidence enters `certified`, so
    the PROVES edges, the trust levels and the student's embedding all land in
    the same commit as the status change.
    """
    canonical: list[str] = []
    for raw in concepts.normalise_all(skills):
        name = concepts.get_or_create_concept(tx, raw, source="extracted")
        if name:
            canonical.append(name)

    for name in canonical:
        ml_repo.link_proves(tx, evidence_id, name)
        ml_repo.ensure_has_skill(tx, student_id, name)

    for name in canonical:
        recompute_skill(tx, student_id, name, recompute_embedding=False)

    # One embedding rebuild for the whole certificate, not one per skill.
    embedding.recompute_student_embedding(tx, student_id)
    log.info(
        "certified evidence linked",
        extra={"student_id": student_id, "evidence_id": evidence_id,
               "concepts": len(canonical)},
    )
    return canonical


def recompute_skill(
    tx, student_id: str, concept: str, recompute_embedding: bool = True
) -> int | None:
    """Recompute one HAS_SKILL edge. Returns the new trust level, or None if the
    edge was removed."""
    name = concepts.normalise(concept)
    if not name:
        return None

    edge = ml_repo.get_has_skill(tx, student_id, name)
    if edge is None:
        return None

    cert_ids = ml_repo.certified_evidence_ids(tx, student_id, name)
    endorsed_by = list(edge.get("endorsed_by") or [])
    claimed = bool(edge.get("claimed"))

    if endorsed_by:
        trust = 2
    elif cert_ids:
        trust = 1
    elif claimed:
        trust = 0
    else:
        # Nothing supports it any more: drop the edge rather than keep a
        # zero-trust ghost that would still show as a chip (TEST-15).
        ml_repo.delete_has_skill(tx, student_id, name)
        if recompute_embedding:
            embedding.recompute_student_embedding(tx, student_id)
        return None

    ml_repo.set_has_skill(tx, student_id, name, trust, cert_ids)
    if recompute_embedding:
        embedding.recompute_student_embedding(tx, student_id)
    return trust


def recompute_all_for_evidence(tx, student_id: str, concept_names: list[str]) -> None:
    """Refresh every concept a certificate touched, then the embedding once.

    Used when a certificate leaves `certified` (a rejection, TEST-15), where the
    PROVES edges are removed by P2's service before this is called.
    """
    for name in concepts.normalise_all(concept_names):
        recompute_skill(tx, student_id, name, recompute_embedding=False)
    embedding.recompute_student_embedding(tx, student_id)
