"""Department dashboard (API-033) and the evidence exports (API-035, API-036)."""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.api.deps import CurrentUser, require_role
from app.schemas.generated import Dashboard, MetricRecords
from app.services import evidence_export, metric_records, metrics

router = APIRouter(tags=["department"])

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.get("/dept/dashboard", response_model=Dashboard, response_model_exclude_unset=True, operation_id="getDashboard")
def get_dashboard(user: CurrentUser = Depends(require_role("hod", "iqac"))) -> dict:
    return metrics.dashboard(user)


@router.get("/dept/metrics/{metric}/records", response_model=MetricRecords, operation_id="getMetricRecords")
def get_metric_records(
    metric: str,
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None, max_length=200),
    user: CurrentUser = Depends(require_role("hod", "iqac")),
) -> dict:
    return metric_records.records(user, metric, limit, cursor)


def _xlsx(name: str, data: bytes) -> StreamingResponse:
    return StreamingResponse(
        iter([data]), media_type=XLSX, headers={"Content-Disposition": f'attachment; filename="{name}"'}
    )


@router.get("/evidence/mentoring.xlsx", response_class=StreamingResponse, operation_id="exportMentoring")
def export_mentoring(user: CurrentUser = Depends(require_role("hod", "iqac"))) -> StreamingResponse:
    return _xlsx(*evidence_export.mentoring_pack(user))


@router.get("/evidence/achievements.xlsx", response_class=StreamingResponse, operation_id="exportAchievements")
def export_achievements(user: CurrentUser = Depends(require_role("hod", "iqac"))) -> StreamingResponse:
    return _xlsx(*evidence_export.achievements_pack(user))
