"""API-017 apply, API-018 decide, API-019 my applications (REQ-006)."""
from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, require_role
from app.schemas.generated import Application, ApplicationPatch
from app.services import applications

router = APIRouter(tags=["applications"])


@router.post(
    "/openings/{opening_id}/applications", response_model=Application, status_code=201, operation_id="applyToOpening"
)
def apply_to_opening(opening_id: str, user: CurrentUser = Depends(require_role("student"))) -> dict:
    return applications.apply(user, opening_id)


@router.patch("/applications/{application_id}", response_model=Application, operation_id="decideApplication")
def decide_application(
    application_id: str, body: ApplicationPatch, user: CurrentUser = Depends(require_role("faculty"))
) -> dict:
    return applications.decide(user, application_id, body.status.value)


@router.get("/me/applications", response_model=list[Application], operation_id="listMyApplications")
def list_my_applications(user: CurrentUser = Depends(require_role("student"))) -> list[dict]:
    return applications.list_mine(user)
