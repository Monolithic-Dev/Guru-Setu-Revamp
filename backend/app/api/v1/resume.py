"""Resume: upload and metadata (API-055), scoped file (API-056), skill suggestions (API-057). PDF only, private."""
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import CurrentUser, require_role
from app.schemas.generated import MyProfile, ResumeInfo, ResumeSuggestions
from app.services import resume

router = APIRouter(tags=["students"])


class ApplyBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    skills: list[str] = Field(min_length=1, max_length=30)


@router.post("/me/resume", response_model=ResumeInfo, status_code=201, operation_id="uploadResume")
def upload_resume(file: UploadFile = File(...), user: CurrentUser = Depends(require_role("student"))) -> dict:
    return resume.intake(user, file.file)


@router.get("/me/resume", response_model=ResumeInfo, operation_id="getMyResume")
def get_my_resume(user: CurrentUser = Depends(require_role("student"))) -> dict:
    return resume.my_resume(user)


@router.get("/students/{student_id}/resume/file", operation_id="getResumeFile", response_class=FileResponse)
def get_resume_file(
    student_id: str, user: CurrentUser = Depends(require_role("student", "faculty", "hod"))
) -> FileResponse:
    return FileResponse(
        resume.file_for(user, student_id), media_type="application/pdf",
        headers={"Content-Disposition": "inline", "X-Content-Type-Options": "nosniff"},
    )


@router.post("/me/resume/suggestions", response_model=ResumeSuggestions, operation_id="suggestFromResume")
def suggest(user: CurrentUser = Depends(require_role("student"))) -> dict:
    return resume.suggestions(user)


@router.post("/me/resume/suggestions/apply", response_model=MyProfile, operation_id="applyResumeSuggestions")
def apply_suggestions(body: ApplyBody, user: CurrentUser = Depends(require_role("student"))) -> dict:
    return resume.apply_suggestions(user, body.skills)
