"""Reminders API-039: computed on read, never stored."""
from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, require_role
from app.schemas.generated import Reminder
from app.services import reminders

router = APIRouter(tags=["notifications"])


@router.get("/me/reminders", response_model=list[Reminder], operation_id="listReminders")
def list_reminders(user: CurrentUser = Depends(require_role("student", "faculty"))) -> list[dict]:
    return reminders.list_reminders(user)
