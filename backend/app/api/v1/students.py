"""API-003 student profile (scope per security section 4) and API-004 partial profile update (REQ-003, REQ-004)."""
from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, current_user, require_role
from app.schemas.generated import ConceptSuggestion, MyProfile, ProfilePatch, StudentProfile
from app.services import profile, students

router = APIRouter(tags=["students"])


@router.get("/students/{student_id}", response_model=StudentProfile, operation_id="getStudent")
def get_student(student_id: str, user: CurrentUser = Depends(require_role("student", "faculty", "hod"))) -> dict:
    return students.get_profile(user, student_id)


@router.patch("/me/profile", response_model=StudentProfile, operation_id="patchMyProfile")
def patch_my_profile(patch: ProfilePatch, user: CurrentUser = Depends(require_role("student"))) -> dict:
    return students.update_profile(user, patch)


@router.get("/me/profile", response_model=MyProfile, operation_id="getMyProfile")
def get_my_profile(user: CurrentUser = Depends(require_role("student"))) -> dict:
    return profile.my_profile(user)


@router.get("/concepts", response_model=list[ConceptSuggestion], operation_id="searchConcepts")
def search_concepts(q: str = Query("", max_length=40), user: CurrentUser = Depends(current_user)) -> list[dict]:
    return students.search_concepts(q)
