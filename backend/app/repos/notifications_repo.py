"""Cypher for notifications (ENT-12). Edge name `NOTIFIES` as in the earlier prototype."""
from typing import Any


def create(tx, user_id: str, notification: dict[str, Any]) -> None:
    tx.run(
        """
        MATCH (u:User {user_id: $user_id})
        CREATE (n:Notification {id: $id, type: $type, title: $title, link: $link, read: false, created_at: $created_at})
        SET n.body = $body
        CREATE (n)-[:NOTIFIES]->(u)
        """,
        user_id=user_id,
        **notification,
    ).consume()


def page(tx, user_id: str, limit: int, cursor_ts: str | None, cursor_id: str | None) -> list[dict[str, Any]]:
    """Newest first. Returns up to `limit + 1` rows so the caller can tell whether another page exists."""
    result = tx.run(
        """
        MATCH (n:Notification)-[:NOTIFIES]->(:User {user_id: $user_id})
        WHERE $cursor_ts IS NULL OR n.created_at < $cursor_ts
              OR (n.created_at = $cursor_ts AND n.id < $cursor_id)
        RETURN n.id AS id, n.type AS type, n.title AS title, n.body AS body, n.link AS link,
               n.read AS read, n.created_at AS created_at
        ORDER BY n.created_at DESC, n.id DESC
        LIMIT $limit
        """,
        user_id=user_id,
        cursor_ts=cursor_ts,
        cursor_id=cursor_id,
        limit=limit + 1,
    )
    return [record.data() for record in result]


def unread_count(tx, user_id: str) -> int:
    return tx.run(
        "MATCH (n:Notification {read: false})-[:NOTIFIES]->(:User {user_id: $user_id}) RETURN count(n) AS c",
        user_id=user_id,
    ).single()["c"]


def mark_read(tx, user_id: str, notification_id: str) -> bool:
    """True if the notification exists and belongs to the user (idempotent)."""
    record = tx.run(
        """
        MATCH (n:Notification {id: $id})-[:NOTIFIES]->(:User {user_id: $user_id})
        SET n.read = true
        RETURN count(n) AS c
        """,
        id=notification_id,
        user_id=user_id,
    ).single()
    return record["c"] > 0
