"""Mentoring routes: allotment API-022/023, sessions API-026/027/028, action items API-030, issues API-031/032.

Responses that may hold private fields are serialised with `response_model_exclude_unset=True`: the service omits
a private key entirely, so it never appears in the JSON (REQ-015, security section 4).
"""
import uuid

from fastapi import APIRouter, Depends, Header, Response

from app.api.deps import CurrentUser, require_role
from app.core.errors import ApiError
from app.schemas.generated import (
    ActionItem,
    ActionItemPatch,
    AllotmentRequest,
    AllotmentView,
    Feedback,
    Issue,
    IssueCreate,
    IssuePatch,
    MeetingRequest,
    MenteeOverview,
    MenteePatch,
    SessionCreate,
    SessionDetail,
)
from app.services import mentorship

router = APIRouter(tags=["mentorship"])


def _idempotency_key(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        return str(uuid.UUID(value))
    except ValueError as exc:
        raise ApiError(
            "VALIDATION_FAILED",
            422,
            "The Idempotency-Key header must be a UUID.",
            errors=[{"field": "Idempotency-Key", "message": "Must be a UUID"}],
        ) from exc


@router.get("/dept/allotment", response_model=AllotmentView, operation_id="getAllotment")
def get_allotment(user: CurrentUser = Depends(require_role("hod"))) -> dict:
    return mentorship.allotment_view(user)


@router.post("/allotments", response_model=AllotmentView, operation_id="allotMentees")
def allot_mentees(body: AllotmentRequest, user: CurrentUser = Depends(require_role("hod"))) -> dict:
    return mentorship.allot(user, body.mentor_id, body.student_ids)


@router.post(
    "/sessions",
    response_model=SessionDetail,
    response_model_exclude_unset=True,
    status_code=201,
    operation_id="logSession",
)
def log_session(
    body: SessionCreate,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    user: CurrentUser = Depends(require_role("faculty")),
) -> dict:
    return mentorship.log_session(user, body, _idempotency_key(idempotency_key))


@router.get(
    "/sessions/{session_id}", response_model=SessionDetail, response_model_exclude_unset=True, operation_id="getSession"
)
def get_session(session_id: str, user: CurrentUser = Depends(require_role("faculty", "student"))) -> dict:
    return mentorship.get_session(user, session_id)


@router.post(
    "/sessions/{session_id}/confirm",
    response_model=SessionDetail,
    response_model_exclude_unset=True,
    operation_id="confirmSession",
)
def confirm_session(session_id: str, user: CurrentUser = Depends(require_role("student"))) -> dict:
    return mentorship.confirm_session(user, session_id)


@router.patch("/action-items/{item_id}", response_model=ActionItem, operation_id="patchActionItem")
def patch_action_item(
    item_id: str, body: ActionItemPatch, user: CurrentUser = Depends(require_role("student", "faculty"))
) -> dict:
    return mentorship.patch_action_item(user, item_id, body.status.value)


@router.post(
    "/issues", response_model=Issue, response_model_exclude_unset=True, status_code=201, operation_id="raiseIssue"
)
def raise_issue(body: IssueCreate, user: CurrentUser = Depends(require_role("faculty", "student"))) -> dict:
    return mentorship.create_issue(user, body)


@router.patch(
    "/issues/{issue_id}", response_model=Issue, response_model_exclude_unset=True, operation_id="patchIssue"
)
def patch_issue(
    issue_id: str, body: IssuePatch, user: CurrentUser = Depends(require_role("faculty", "hod"))
) -> dict:
    return mentorship.patch_issue(user, issue_id, body)


@router.post("/me/meeting-requests", status_code=201, operation_id="requestMeeting")
def request_meeting(body: MeetingRequest, user: CurrentUser = Depends(require_role("student"))) -> Response:
    mentorship.request_meeting(user, body.message.strip())
    return Response(status_code=201)


@router.post("/sessions/{session_id}/feedback", operation_id="sessionFeedback")
def session_feedback(
    session_id: str, body: Feedback, user: CurrentUser = Depends(require_role("student"))
) -> Response:
    mentorship.submit_feedback(user, session_id, body.feedback.value, body.comment)
    return Response(status_code=200)


@router.patch(
    "/mentees/{student_id}",
    response_model=MenteeOverview,
    response_model_exclude_unset=True,
    operation_id="patchMentee",
)
def patch_mentee(
    student_id: str, body: MenteePatch, user: CurrentUser = Depends(require_role("faculty"))
) -> dict:
    return mentorship.patch_mentee(user, student_id, body)
