"""API-003 student profile (scope per security section 4) and API-004 partial profile update (REQ-003, REQ-004)."""
from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, require_role
from app.schemas.generated import ProfilePatch, StudentProfile
from app.services import students

router = APIRouter(tags=["students"])


@router.get("/students/{student_id}", response_model=StudentProfile, operation_id="getStudent")
def get_student(student_id: str, user: CurrentUser = Depends(require_role("student", "faculty", "hod"))) -> dict:
    return students.get_profile(user, student_id)


@router.patch("/me/profile", response_model=StudentProfile, operation_id="patchMyProfile")
def patch_my_profile(patch: ProfilePatch, user: CurrentUser = Depends(require_role("student"))) -> dict:
    return students.update_profile(user, patch)
