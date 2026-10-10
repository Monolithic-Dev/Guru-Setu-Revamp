"""Create an opening (API-014). Reads of openings are P1's `match.py`."""
from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, require_role
from app.schemas.generated import Opening, OpeningCreate
from app.services import openings

router = APIRouter(tags=["openings"])


@router.post("/openings", response_model=Opening, status_code=201, operation_id="createOpening")
def create_opening(body: OpeningCreate, user: CurrentUser = Depends(require_role("faculty"))) -> dict:
    return openings.create_opening(user, body)
