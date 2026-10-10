"""API-041: a mentor endorses a mentee's skill (REQ-027, P2 tier). Owner: P1.

An endorsement is the only route to trust level 2. It is a named human vouching
for a skill, so it is recorded against the endorsing faculty and recomputed
through the same `recompute_skill` as every other trust change - the endorsement
is evidence, not a stored trust value.

Scope: the endorsing faculty must be the student's assigned mentor or a guide,
otherwise 404 (the HOD is not listed for this route, so an HOD gets 403 - the
same distinction as API-027, AGENTS.md "known traps").
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api import deps
from app.core.database import run_write
from app.core.errors import ApiError
from app.ml import concepts, trust
from app.repos import ml_repo

router = APIRouter(tags=["endorsements"])


class EndorsementCreate(BaseModel):
    concept: str = Field(min_length=1, max_length=40)


def _endorse(
    tx, faculty_id: str, faculty_name: str, student_id: str, concept_name: str
) -> str:
    name = concepts.normalise(concept_name)
    if not name:
        raise ApiError("VALIDATION_FAILED", 422, "concept is required")

    # Only an existing skill can be endorsed: endorsing something the student
    # never claimed and no certificate proves would invent a skill for them.
    edge = ml_repo.get_has_skill(tx, student_id, name)
    if edge is None:
        raise ApiError(
            "NOT_FOUND", 404, "This student does not list that skill"
        )

    endorsed_by = list(edge.get("endorsed_by") or [])
    if faculty_id not in endorsed_by:
        endorsed_by.append(faculty_id)
        ml_repo.set_endorsed_by(tx, student_id, name, endorsed_by)

    trust.recompute_skill(tx, student_id, name)
    return name


@router.post("/students/{student_id}/endorsements", status_code=201)
def create_endorsement(
    student_id: str,
    body: EndorsementCreate,
    user: Annotated[deps.CurrentUser, Depends(deps.require_role("faculty"))],
) -> dict:
    """API-041. Returns the student's profile, which P2's students route owns,
    so only the concept and its new trust level are returned here."""

    def work(tx):
        deps.assert_mentor_of(tx, user.user_id, student_id)
        name = _endorse(tx, user.user_id, user.name, student_id, body.concept)
        level = ml_repo.get_has_skill(tx, student_id, name) or {}
        return {
            "student_id": student_id,
            "concept": name,
            "trust_level": int(level.get("trust_level") or 0),
            "endorsed_by": list(level.get("endorsed_by") or []),
        }

    return run_write(work)
