"""StatusEvent writer (REQ-018, SEC-13). Call inside the same write transaction as the change it records."""
import uuid
from typing import Any, Protocol

from app.core.clock import utc_now_iso
from app.repos import status_history_repo

ENTITY_TYPES = {"evidence", "application", "mentorship", "action_item", "issue", "session", "opening"}
MAX_NOTE = 300


class Actor(Protocol):
    user_id: str
    name: str


def record_status(
    tx,
    entity_type: str,
    entity_id: str,
    from_status: str | None,
    to_status: str,
    actor: Actor,
    note: str | None = None,
) -> None:
    """Write one StatusEvent. `note` is a short reason (for example a review reason), never a session note."""
    if entity_type not in ENTITY_TYPES:
        raise ValueError(f"Unknown StatusEvent entity_type: {entity_type}")
    status_history_repo.create(
        tx,
        {
            "id": str(uuid.uuid4()),
            "entity_type": entity_type,
            "entity_id": entity_id,
            "from_status": from_status,
            "to_status": to_status,
            "actor_id": actor.user_id,
            "actor_name": actor.name,
            "note": note[:MAX_NOTE] if note else None,
            "at": utc_now_iso(),
        },
    )


def history_for(tx, entity_ids: list[str]) -> dict[str, list[dict[str, Any]]]:
    """Timeline per entity id (oldest first) for the `history` fields of API-018/019/025/029."""
    return status_history_repo.for_entities(tx, entity_ids)
