"""Faculty track record API-044: counts and decision times, never ratings."""
from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, current_user
from app.schemas.generated import TrackRecord
from app.services import track_record

router = APIRouter(tags=["students"])


@router.get("/faculty/{faculty_id}/track-record", response_model=TrackRecord, operation_id="getTrackRecord")
def get_track_record(faculty_id: str, user: CurrentUser = Depends(current_user)) -> dict:
    return track_record.track_record(faculty_id)
