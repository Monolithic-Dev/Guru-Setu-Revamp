"""Cypher for StatusEvent nodes (ENT-14), keyed by `entity_id` (index `status_event_entity`)."""
from typing import Any


def create(tx, event: dict[str, Any]) -> None:
    tx.run(
        """
        CREATE (e:StatusEvent {id: $id, entity_type: $entity_type, entity_id: $entity_id,
                               from_status: $from_status, to_status: $to_status,
                               actor_id: $actor_id, actor_name: $actor_name, at: $at})
        SET e.note = $note
        """,
        **event,
    ).consume()


def for_entities(tx, entity_ids: list[str]) -> dict[str, list[dict[str, Any]]]:
    """Events per entity id, oldest first, in the StatusEvent response shape."""
    result = tx.run(
        """
        UNWIND $ids AS entity_id
        MATCH (e:StatusEvent {entity_id: entity_id})
        RETURN e.entity_id AS entity_id, e.from_status AS from_status, e.to_status AS to_status,
               e.actor_name AS actor_name, e.note AS note, e.at AS at
        ORDER BY e.at ASC
        """,
        ids=entity_ids,
    )
    grouped: dict[str, list[dict[str, Any]]] = {entity_id: [] for entity_id in entity_ids}
    for record in result:
        data = record.data()
        grouped[data.pop("entity_id")].append(data)
    return grouped
