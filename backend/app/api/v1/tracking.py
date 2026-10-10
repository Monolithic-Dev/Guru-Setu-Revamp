"""Mentor home API-024, Mentee 360 API-025, My mentorship API-029. All read-only.

Mentee 360 and My mentorship hold private fields, so they serialise with `response_model_exclude_unset=True`.
"""
from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, require_role
from app.schemas.generated import MenteeOverview, MenteeRow, MyMentorship
from app.services import overview, tracking

router = APIRouter(tags=["tracking"])


@router.get("/me/mentees", response_model=list[MenteeRow], operation_id="listMyMentees")
def my_mentees(user: CurrentUser = Depends(require_role("faculty"))) -> list[dict]:
    return tracking.mentor_home(user)


@router.get(
    "/mentees/{student_id}/overview",
    response_model=MenteeOverview,
    response_model_exclude_unset=True,
    operation_id="getMenteeOverview",
)
def mentee_overview(student_id: str, user: CurrentUser = Depends(require_role("faculty", "hod"))) -> dict:
    return overview.mentee_overview(user, student_id)


@router.get(
    "/me/mentorship", response_model=MyMentorship, response_model_exclude_unset=True, operation_id="getMyMentorship"
)
def my_mentorship(user: CurrentUser = Depends(require_role("student"))) -> dict:
    return overview.my_mentorship(user)
