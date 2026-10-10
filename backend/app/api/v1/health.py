"""API-040 liveness, database and LLM mode. Public (the only route besides login)."""
from fastapi import APIRouter

from app.core.config import get_settings
from app.core.database import ping
from app.core.errors import ApiError
from app.schemas.generated import Health

router = APIRouter(tags=["ops"])


@router.get("/health", response_model=Health, operation_id="health")
def health() -> dict:
    if not ping():
        raise ApiError("DB_UNAVAILABLE", 503, "The database is not reachable. Try again in a moment.")
    return {"status": "ok", "neo4j": "up", "llm_provider": get_settings().llm_provider}
