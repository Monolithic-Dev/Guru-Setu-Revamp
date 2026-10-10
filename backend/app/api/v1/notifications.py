"""API-037 notifications (newest first, cursor pagination) and API-038 mark read (REQ-038)."""
from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import CurrentUser, current_user
from app.schemas.generated import NotificationPage
from app.services import notify

router = APIRouter(tags=["notifications"])


@router.get("/me/notifications", response_model=NotificationPage, operation_id="listNotifications")
def list_notifications(
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None, max_length=200),
    user: CurrentUser = Depends(current_user),
) -> dict:
    return notify.list_notifications(user.user_id, limit, cursor)


@router.post("/me/notifications/{notification_id}/read", status_code=204, operation_id="markNotificationRead")
def mark_notification_read(notification_id: str, user: CurrentUser = Depends(current_user)) -> Response:
    notify.mark_read(user.user_id, notification_id)
    return Response(status_code=204)
