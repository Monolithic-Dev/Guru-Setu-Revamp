"""Recommended openings with eligibility and reasons (API-050), and the eligibility read (API-051).
New file so P1's `match.py` (the plain list and the Fit Check) stays untouched."""
from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, require_role
from app.schemas.generated import Eligibility, Recommendations
from app.services import recommendations

router = APIRouter(tags=["openings"])


@router.get("/me/recommendations", response_model=Recommendations, operation_id="getMyRecommendations")
def my_recommendations(user: CurrentUser = Depends(require_role("student"))) -> dict:
    return recommendations.recommendations(user)


@router.get("/openings/{opening_id}/eligibility", response_model=Eligibility, operation_id="getEligibility")
def get_eligibility(opening_id: str, user: CurrentUser = Depends(require_role("student"))) -> dict:
    return recommendations.eligibility_for(user, opening_id)
