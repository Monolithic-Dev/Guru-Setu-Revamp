"""Certificates: upload API-005, poll API-006/007, manual entry API-008, review API-009/010, file API-011."""
from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile
from fastapi.responses import FileResponse

from app.api.deps import CurrentUser, require_role
from app.schemas.generated import Certificate, ManualCertificate, ReviewDecision, ReviewItem
from app.services import certificates

router = APIRouter(tags=["certificates"])


@router.post("/certificates", response_model=Certificate, status_code=202, operation_id="uploadCertificate")
def upload_certificate(
    background: BackgroundTasks, file: UploadFile = File(...), user: CurrentUser = Depends(require_role("student"))
) -> dict:
    return certificates.intake(user, file.file, background)


@router.get("/me/certificates", response_model=list[Certificate], operation_id="listMyCertificates")
def my_certificates(user: CurrentUser = Depends(require_role("student"))) -> list[dict]:
    return certificates.list_mine(user)


@router.get("/reviews/certificates", response_model=list[ReviewItem], operation_id="listReviewQueue")
def review_queue(user: CurrentUser = Depends(require_role("faculty", "hod"))) -> list[dict]:
    return certificates.review_queue(user)


@router.get("/certificates/{certificate_id}", response_model=Certificate, operation_id="getCertificate")
def get_certificate(
    certificate_id: str, user: CurrentUser = Depends(require_role("student", "faculty", "hod"))
) -> dict:
    return certificates.get_certificate(user, certificate_id)


@router.put("/certificates/{certificate_id}/manual", response_model=Certificate, operation_id="putManualCertificate")
def put_manual(
    certificate_id: str, body: ManualCertificate, user: CurrentUser = Depends(require_role("student"))
) -> dict:
    return certificates.put_manual(user, certificate_id, body)


@router.post("/certificates/{certificate_id}/review", response_model=Certificate, operation_id="reviewCertificate")
def review_certificate(
    certificate_id: str, body: ReviewDecision, user: CurrentUser = Depends(require_role("faculty", "hod"))
) -> dict:
    return certificates.review(user, certificate_id, body)


@router.get("/certificates/{certificate_id}/file", operation_id="getCertificateFile", response_class=FileResponse)
def certificate_file(
    certificate_id: str, user: CurrentUser = Depends(require_role("student", "faculty", "hod"))
) -> FileResponse:
    path, media_type = certificates.file_for(user, certificate_id)
    return FileResponse(
        path, media_type=media_type,
        headers={"Content-Disposition": "inline", "X-Content-Type-Options": "nosniff"},
    )
