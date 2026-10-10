"""Add-ons on the P2 side: A3 reminders (API-039), A7 meeting request (API-045), A9 create opening (API-014).
Uses the hand-built graph from test_tracking (`world`); today is 2026-10-10 and the term ends 2026-11-30 (51 days)."""
import pytest

from app.core.config import get_settings
from tests.test_tracking import (
    ISSUE_TEXT,
    NOTE,
    cypher,
    session,
    world,  # noqa: F401  (autouse fixture: the base graph)
)


def _reminders(client, headers):
    r = client.get("/api/v1/me/reminders", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


# ---- A3 reminders -----------------------------------------------------------------------------------------------------


def test_a3_mentor_reminders(client, meera):
    rows = _reminders(client, meera)
    kinds = sorted((r["kind"], r["student_id"] and r["student_name"]) for r in rows)
    # the term ends in 51 days (> 30), so no meetings_due yet; Omar's action is overdue; Sana's issue is stale;
    # Tara's confidential issue (raised by Arjun) and the fresh one are not reminders
    assert kinds == [("action_overdue", "Omar Old"), ("issue_stale", "Sana Stale")]
    action = next(r for r in rows if r["kind"] == "action_overdue")
    assert action["ref_id"] == "a-old" and action["due_date"] == "2026-09-01"
    assert next(r for r in rows if r["kind"] == "issue_stale")["ref_id"] == "i-stale"
    text = str(rows)
    assert ISSUE_TEXT not in text and NOTE not in text and "Do the thing" not in text


def test_a3_meetings_due_near_term_end(client, meera, monkeypatch):
    monkeypatch.setattr(get_settings(), "reminder_term_end_days", 60)
    due = [r for r in _reminders(client, meera) if r["kind"] == "meetings_due"]
    assert sorted(r["student_name"] for r in due) == ["Aarav", "Omar Old"]  # 0 and 1 of 2 meetings
    assert all(r["due_date"] == "2026-11-30" for r in due)
    assert "ends in 51 days" in due[0]["message"]


def test_a3_student_reminders(client, aarav, monkeypatch):
    session("s-unc", "u-meera", "u-aarav", "2026-09-30")  # present, unconfirmed for 10 days
    session("s-new", "u-meera", "u-aarav", "2026-10-08")  # 2 days: too early
    session("s-conf", "u-meera", "u-aarav", "2026-09-01", confirmed="2026-09-02T00:00:00.000Z")
    rows = _reminders(client, aarav)
    assert [(r["kind"], r["ref_id"]) for r in rows] == [("session_unconfirmed", "s-unc")]
    # three present meetings this term: nothing due even near term end; with a higher minimum it is
    monkeypatch.setattr(get_settings(), "reminder_term_end_days", 60)
    assert sorted(r["kind"] for r in _reminders(client, aarav)) == ["session_unconfirmed"]
    monkeypatch.setattr(get_settings(), "min_meetings_per_term", 5)
    assert sorted(r["kind"] for r in _reminders(client, aarav)) == ["meetings_due", "session_unconfirmed"]


def test_a3_roles(client, suresh, kavya):
    assert client.get("/api/v1/me/reminders", headers=suresh).status_code == 403
    assert client.get("/api/v1/me/reminders", headers=kavya).status_code == 403
    assert client.get("/api/v1/me/reminders").status_code == 401


# ---- A7 meeting request -----------------------------------------------------------------------------------------------


def test_a7_meeting_request_notifies_the_assigned_mentor(client, aarav, meera, arjun):
    r = client.post("/api/v1/me/meeting-requests", headers=aarav, json={"message": "Can we meet before the exam?"})
    assert r.status_code == 201
    got = cypher(
        "MATCH (n:Notification {type: 'meeting_request'})-[:NOTIFIES]->(u:User) "
        "RETURN u.user_id AS u, n.title AS t, n.body AS b, n.link AS l"
    )
    assert got == [{"u": "u-meera", "t": "Aarav requested a meeting", "b": "Can we meet before the exam?",
                    "l": "/faculty/mentees/u-aarav"}]
    inbox = client.get("/api/v1/me/notifications", headers=meera).json()
    assert [n["type"] for n in inbox["items"]] == ["meeting_request"]
    assert client.get("/api/v1/me/notifications", headers=arjun).json()["items"] == []


def test_a7_meeting_request_rules(client, aarav, diya, meera):
    url = "/api/v1/me/meeting-requests"
    assert client.post(url, headers=aarav, json={"message": "   "}).status_code == 422
    assert client.post(url, headers=aarav, json={"message": ""}).status_code == 422
    assert client.post(url, headers=aarav, json={"message": "x" * 301}).status_code == 422
    assert client.post(url, headers=meera, json={"message": "hi"}).status_code == 403
    cypher("MATCH (:Faculty)-[m:MENTORS]->(:Student {user_id: 'u-diya'}) DELETE m")
    assert client.post(url, headers=diya, json={"message": "hello"}).status_code == 404  # no mentor to tell


# ---- A9 create opening ------------------------------------------------------------------------------------------------


def test_a9_create_opening(client, meera):
    body = {"title": "Federated Learning for Health", "description": "Privacy-preserving training on hospital data.",
            "required_skills": ["Python", " python ", "Federated  Learning", "PyTorch"]}
    r = client.post("/api/v1/openings", headers=meera, json=body)
    assert r.status_code == 201
    out = r.json()
    assert out["faculty"]["name"] == "Meera" and out["status"] == "open" and out["applicant_count"] == 0
    assert out["required_skills"] == ["federated learning", "python", "pytorch"]  # normalised, de-duplicated
    node = cypher(
        "MATCH (f:Faculty {user_id: 'u-meera'})-[:POSTED]->(o:Opening {id: $id})-[:REQUIRES]->(c:Concept) "
        "RETURN count(c) AS n", id=out["id"],
    )
    assert node == [{"n": 3}]


@pytest.mark.parametrize("patch", [
    {"title": "Hey"},  # under 5 characters
    {"required_skills": []},
    {"required_skills": [f"skill {i}" for i in range(11)]},
    {"description": "x" * 2001},
    {"unknown": 1},
])
def test_a9_validation(client, meera, patch):
    body = {"title": "A valid title", "description": "d", "required_skills": ["python"], **patch}
    assert client.post("/api/v1/openings", headers=meera, json=body).status_code == 422


def test_a9_roles(client, aarav, suresh, kavya):
    body = {"title": "A valid title", "description": "d", "required_skills": ["python"]}
    for headers in (aarav, suresh, kavya):
        assert client.post("/api/v1/openings", headers=headers, json=body).status_code == 403
    assert client.post("/api/v1/openings", json=body).status_code == 401
