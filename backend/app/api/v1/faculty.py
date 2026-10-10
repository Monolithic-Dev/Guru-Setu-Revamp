"""Faculty profile (API-052), public page (API-053), track record (API-044), guide directory (API-058)."""
from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, current_user, require_role
from app.schemas.generated import FacultyCard, FacultyProfile, FacultyProfilePatch, FacultyPublic, TrackRecord
from app.services import faculty, track_record

router = APIRouter(tags=["students"])


@router.get("/me/faculty-profile", response_model=FacultyProfile, operation_id="getMyFacultyProfile")
def get_my_faculty_profile(user: CurrentUser = Depends(require_role("faculty"))) -> dict:
    return faculty.my_profile(user)


@router.patch("/me/faculty-profile", response_model=FacultyProfile, operation_id="patchMyFacultyProfile")
def patch_my_faculty_profile(
    patch: FacultyProfilePatch, user: CurrentUser = Depends(require_role("faculty"))
) -> dict:
    return faculty.update_profile(user, patch)


@router.get("/faculty", response_model=list[FacultyCard], operation_id="listFaculty")
def list_faculty(
    query: str | None = Query(None, max_length=60),
    accepting: bool | None = Query(None),
    user: CurrentUser = Depends(require_role("student")),
) -> list[dict]:
    return faculty.directory(user, query, accepting)


@router.get("/faculty/{faculty_id}", response_model=FacultyPublic, operation_id="getFacultyPublic")
def get_faculty_public(faculty_id: str, user: CurrentUser = Depends(current_user)) -> dict:
    return faculty.public_profile(faculty_id)


@router.get("/faculty/{faculty_id}/track-record", response_model=TrackRecord, operation_id="getTrackRecord")
def get_track_record(faculty_id: str, user: CurrentUser = Depends(current_user)) -> dict:
    return track_record.track_record(faculty_id)
