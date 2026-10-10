"""Fit and matching routes: API-012, 013, 015, 016, 020, 021. Owner: P1.

Thin by design - parse, check scope, delegate to `app.ml.fit`, return an
explicit response model (backend 5, SEC-01).

Scope rules enforced here (security 4, and the 403-vs-404 trap in AGENTS.md):
  API-015  a student sees only their own fit. A faculty may pass ?student_id=
           only for an applicant to an opening they own - anything else is 404,
           never 403, so the existence of a student is never leaked.
  API-016  the owner of the opening only, and applicants only (NG-11).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api import deps
from app.core.database import run_read
from app.core.errors import ApiError
from app.ml import fit as fit_service
from app.schemas.match import (
    Candidate,
    Fit,
    Opening,
    OpeningSummary,
    SkillGap,
    WhyGraph,
)

router = APIRouter(tags=["match"])


@router.get("/openings", response_model=list[OpeningSummary])
def list_openings(
    user: Annotated[deps.CurrentUser, Depends(deps.current_user)],
    limit: Annotated[int, Query(ge=1, le=50)] = 50,
) -> list[OpeningSummary]:
    """API-012. A student sees their own fit on each row; everyone else sees the
    list without a fit, because a fit is only meaningful for a student."""
    if user.role == "student":
        rows = run_read(fit_service.fit_summary_for_openings, student_id=user.user_id,
                        limit=limit)
        return [OpeningSummary(**row) for row in rows]

    from app.repos import match_repo

    rows = run_read(match_repo.openings, limit=limit)
    return [
        OpeningSummary(
            id=row["id"],
            title=row["title"],
            status=row["status"],
            faculty={"user_id": row["faculty_id"], "name": row["faculty_name"]},
            required_skills=row.get("required_skills") or [],
            my_fit=None,
            my_application_status=None,
        )
        for row in rows
    ]


@router.get("/openings/{opening_id}", response_model=Opening)
def get_opening(
    opening_id: str,
    user: Annotated[deps.CurrentUser, Depends(deps.current_user)],
) -> Opening:
    """API-013."""
    from app.repos import match_repo

    row = run_read(match_repo.opening_detail, opening_id=opening_id)
    if row is None:
        raise ApiError("NOT_FOUND", 404, "Opening not found")

    is_owner = user.role == "faculty" and user.user_id == row["faculty_id"]
    return Opening(
        id=row["id"],
        title=row["title"],
        description=row.get("description") or "",
        status=row["status"],
        created_at=row.get("created_at") or "",
        faculty={"user_id": row["faculty_id"], "name": row["faculty_name"]},
        required_skills=row.get("required_skills") or [],
        # Only the owner learns how many people applied.
        applicant_count=row.get("applicant_count") if is_owner else None,
    )


@router.get("/openings/{opening_id}/fit", response_model=Fit)
def get_fit(
    opening_id: str,
    user: Annotated[deps.CurrentUser, Depends(deps.current_user)],
    student_id: Annotated[str | None, Query()] = None,
) -> Fit:
    """API-015. The explained Fit Check (REQ-004)."""
    if user.role == "student":
        if student_id and student_id != user.user_id:
            # Asking about someone else is simply not found, not forbidden.
            raise ApiError("NOT_FOUND", 404, "Fit not found")
        target = user.user_id
    elif user.role == "faculty":
        if not student_id:
            raise ApiError(
                "VALIDATION_FAILED", 422, "student_id is required for faculty"
            )
        run_read(
            deps.assert_applicant_of_own,
            faculty_id=user.user_id,
            student_id=student_id,
            opening_id=opening_id,
        )
        target = student_id
    else:
        raise ApiError("FORBIDDEN", 403, "Not available for this role")

    payload = run_read(fit_service.fit_for, opening_id=opening_id, student_id=target)
    if payload is None:
        raise ApiError("NOT_FOUND", 404, "Fit not found")
    return Fit(**payload)


@router.get("/openings/{opening_id}/candidates", response_model=list[Candidate])
def get_candidates(
    opening_id: str,
    user: Annotated[deps.CurrentUser, Depends(deps.require_role("faculty"))],
) -> list[Candidate]:
    """API-016. Ranked applicants for an opening the caller owns (REQ-005)."""
    run_read(
        deps.assert_owner_of_opening, faculty_id=user.user_id, opening_id=opening_id
    )
    rows = run_read(fit_service.candidates_for_opening, opening_id=opening_id)
    if rows is None:
        raise ApiError("NOT_FOUND", 404, "Opening not found")
    return [Candidate(**row) for row in rows]


@router.get("/openings/{opening_id}/why", response_model=WhyGraph)
def get_why(
    opening_id: str,
    user: Annotated[deps.CurrentUser, Depends(deps.require_role("student"))],
) -> WhyGraph:
    """API-020. Why-paths behind the caller's own chips (REQ-020)."""
    payload = run_read(
        fit_service.why_graph, opening_id=opening_id, student_id=user.user_id
    )
    if payload is None:
        raise ApiError("NOT_FOUND", 404, "Opening not found")
    return WhyGraph(**payload)


@router.get("/me/skill-gaps", response_model=list[SkillGap])
def get_skill_gaps(
    user: Annotated[deps.CurrentUser, Depends(deps.require_role("student"))],
) -> list[SkillGap]:
    """API-021. The five skills that would unlock the most openings (REQ-021)."""
    rows = run_read(fit_service.skill_gaps, student_id=user.user_id)
    return [SkillGap(**row) for row in rows]
