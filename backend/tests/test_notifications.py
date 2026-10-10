"""Notifications (API-037/038, REQ-038) and StatusEvents (REQ-018, TEST-34 foundation)."""
import pytest

from app.core.database import run_read, run_write
from app.services import notify, status_history


class _Actor:
    user_id = "u-meera"
    name = "Meera"


def _clear(user_id: str) -> None:
    def work(tx):
        tx.run("MATCH (n:Notification)-[:NOTIFIES]->(:User {user_id: $u}) DETACH DELETE n", u=user_id).consume()

    run_write(work)


def _create(user_id: str, count: int, prefix: str = "n") -> None:
    def work(tx):
        for i in range(count):
            notify.notify(tx, user_id, "session_logged", f"{prefix}{i:02d}", "/student/mentorship")

    run_write(work)


def test_two_notifications_in_one_transaction_then_read_one(client, aarav):
    _clear("u-aarav")
    _create("u-aarav", 2)
    page = client.get("/api/v1/me/notifications", headers=aarav).json()
    assert page["unread"] == 2 and len(page["items"]) == 2 and page["next_cursor"] is None
    first = page["items"][0]
    assert set(first) >= {"id", "type", "title", "link", "read", "created_at"} and first["read"] is False

    done = client.post(f"/api/v1/me/notifications/{first['id']}/read", headers=aarav)
    assert done.status_code == 204 and done.content == b""
    after = client.get("/api/v1/me/notifications", headers=aarav).json()
    assert after["unread"] == 1  # dropped by 1
    # idempotent
    assert client.post(f"/api/v1/me/notifications/{first['id']}/read", headers=aarav).status_code == 204


def test_other_users_notification_is_404(client, aarav, diya):
    _clear("u-aarav")
    _create("u-aarav", 1)
    nid = client.get("/api/v1/me/notifications", headers=aarav).json()["items"][0]["id"]
    response = client.post(f"/api/v1/me/notifications/{nid}/read", headers=diya)
    assert response.status_code == 404 and response.json()["code"] == "NOT_FOUND"
    assert client.post("/api/v1/me/notifications/does-not-exist/read", headers=aarav).status_code == 404


def test_pagination_newest_first_without_duplicates(client, aarav):
    _clear("u-aarav")
    _create("u-aarav", 25)
    seen, cursor, pages = [], None, 0
    while True:
        params = {"limit": 10, **({"cursor": cursor} if cursor else {})}
        page = client.get("/api/v1/me/notifications", params=params, headers=aarav).json()
        seen.extend(item["id"] for item in page["items"])
        pages += 1
        cursor = page["next_cursor"]
        if not cursor:
            break
    assert pages == 3 and len(seen) == 25 and len(set(seen)) == 25
    # newest first overall
    items = client.get("/api/v1/me/notifications", params={"limit": 100}, headers=aarav).json()["items"]
    stamps = [item["created_at"] for item in items]
    assert stamps == sorted(stamps, reverse=True)


def test_limit_and_cursor_validation(client, aarav):
    assert client.get("/api/v1/me/notifications", params={"limit": 0}, headers=aarav).status_code == 422
    assert client.get("/api/v1/me/notifications", params={"limit": 101}, headers=aarav).status_code == 422
    bad = client.get("/api/v1/me/notifications", params={"cursor": "@@@"}, headers=aarav)
    assert bad.status_code == 422 and bad.json()["code"] == "VALIDATION_FAILED"


def test_notification_and_status_event_roll_back_together(client):
    _clear("u-diya")

    def failing(tx):
        notify.notify(tx, "u-diya", "allotted", "Your mentor is now Meera", "/student/mentorship")
        status_history.record_status(tx, "mentorship", "m-test", None, "active", _Actor())
        raise RuntimeError("boom")  # nothing written before this may survive

    with pytest.raises(RuntimeError):
        run_write(failing)
    count = run_read(
        lambda tx: tx.run(
            "MATCH (n:Notification)-[:NOTIFIES]->(:User {user_id: 'u-diya'}) RETURN count(n) AS c"
        ).single()["c"]
    )
    events = run_read(lambda tx: status_history.history_for(tx, ["m-test"]))
    assert count == 0 and events["m-test"] == []


def test_status_history_roundtrip_and_validation(client):
    def write(tx):
        status_history.record_status(tx, "application", "app-1", None, "pending", _Actor())
        status_history.record_status(tx, "application", "app-1", "pending", "shortlisted", _Actor(), note="x" * 400)

    run_write(write)
    events = run_read(lambda tx: status_history.history_for(tx, ["app-1"]))["app-1"]
    assert [e["to_status"] for e in events] == ["pending", "shortlisted"]
    assert events[0]["from_status"] is None and events[1]["actor_name"] == "Meera"
    assert len(events[1]["note"]) == 300  # note is capped
    with pytest.raises(ValueError):
        run_write(lambda tx: status_history.record_status(tx, "session_notes", "x", None, "y", _Actor()))
    with pytest.raises(ValueError):
        run_write(lambda tx: notify.notify(tx, "u-aarav", "not_a_type", "t", "/x"))


def test_titles_and_text_limits(client):
    assert notify.render_title("allotted", mentor="Dr. Meera") == "Your mentor is now Dr. Meera"
    _clear("u-aarav")
    run_write(lambda tx: notify.notify(tx, "u-aarav", "session_logged", "t" * 500, "/x", body="b" * 500))
    item = run_read(lambda tx: notify.notifications_repo.page(tx, "u-aarav", 5, None, None))[0]
    assert len(item["title"]) == 120 and len(item["body"]) == 200
