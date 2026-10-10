"""Mentoring write side: TEST-20 (notes), 27 (allotment), 28 (session rules and rollback), 29 (confirm), 30 (action
items), 31 (issues), 35 (notifications), plus idempotency and field visibility.

Data: the `world` fixture adds terms, 12 extra mentees for Meera and 2 unallotted students on top of the base graph.
"""
import uuid
from datetime import timedelta

import bcrypt
import pytest

from app.core.clock import today
from app.core.database import run_write

MEERA_MENTEES = [f"u-s{i:02d}" for i in range(1, 12)]  # 11 + Aarav = 12 attendees
UNALLOTTED = ["u-un1", "u-un2"]
HASH = bcrypt.hashpw(b"Demo@123", bcrypt.gensalt(4)).decode()


def cypher(query: str, **params):
    return run_write(lambda tx: [r.data() for r in tx.run(query, **params)])


def counts() -> dict[str, int]:
    rows = cypher(
        """
        RETURN COUNT { MATCH (n:Session) } AS sessions, COUNT { MATCH (n:ActionItem) } AS items,
               COUNT { MATCH (n:Issue) } AS issues, COUNT { MATCH (n:StatusEvent) } AS events,
               COUNT { MATCH (n:Notification) } AS notes, COUNT { MATCH (n:IdempotencyKey) } AS keys
        """
    )
    return rows[0]


def iso(offset_days: int) -> str:
    return (today() + timedelta(days=offset_days)).isoformat()


def new_student(uid: str, name: str, roll: str, mentor_id: str | None) -> None:
    cypher(
        """
        MERGE (s:User:Student {user_id: $uid})
        ON CREATE SET s.email = $email, s.password_hash = $hash, s.name = $name, s.role = 'student',
                      s.dept_code = 'CSE', s.roll_no = $roll, s.year = 3, s.created_at = '2026-01-01T00:00:00.000Z'
        """,
        uid=uid, email=f"{uid}@demo.gurusetu", hash=HASH, name=name, roll=roll,
    )
    if mentor_id:
        cypher(
            """
            MATCH (f:Faculty {user_id: $f}), (s:Student {user_id: $s})
            MERGE (f)-[m:MENTORS {id: $id}]->(s)
            ON CREATE SET m.type = 'assigned', m.status = 'active', m.since = '2026-05-01'
            """,
            f=mentor_id, s=uid, id=f"mt-{uid}",
        )


@pytest.fixture(autouse=True)
def world(fresh_seed):
    for key in ("Session", "ActionItem", "Issue", "StatusEvent", "Notification", "IdempotencyKey"):
        cypher(f"MATCH (n:{key}) DETACH DELETE n")
    cypher("MATCH (t:Term) DETACH DELETE t")
    cypher(
        """
        CREATE (:Term {id: '2026-EVEN', name: 'Even 2026', start_date: '2026-01-05', end_date: '2026-05-31'})
        CREATE (:Term {id: '2026-ODD', name: 'Odd 2026', start_date: '2026-07-15', end_date: '2026-11-30'})
        """
    )
    for i, uid in enumerate(MEERA_MENTEES, start=1):
        new_student(uid, f"Student {i:02d}", f"CB.EN.U4CSE24{100 + i}", "u-meera")
    for i, uid in enumerate(UNALLOTTED, start=1):
        new_student(uid, f"Unallotted {i}", f"CB.EN.U4CSE24{200 + i}", None)
    # baseline links: only the base graph's Meera->Aarav and Arjun->Diya stay; everything allotted by a test is reset
    cypher(
        """
        MATCH (:Faculty)-[m:MENTORS]->(s:Student) WHERE s.user_id IN $ids
        DELETE m
        """,
        ids=UNALLOTTED,
    )
    cypher("MATCH (:Faculty {user_id: 'u-meera'})-[m:MENTORS {id: 'mt-meera-aarav'}]->() SET m.status = 'active'")
    cypher("MATCH (:Faculty)-[m:MENTORS]->(s:Student) WHERE m.id STARTS WITH 'mt-' AND m.id <> 'mt-meera-aarav' AND m.id <> 'mt-arjun-diya' AND NOT s.user_id IN $mentees DELETE m", mentees=MEERA_MENTEES)
    cypher(
        """
        MATCH (f:Faculty {user_id: 'u-meera'}) UNWIND $ids AS id
        MATCH (s:Student {user_id: id})
        MERGE (f)-[m:MENTORS {id: 'mt-' + id}]->(s) SET m.status = 'active', m.type = 'assigned', m.until = null
        """,
        ids=MEERA_MENTEES,
    )


def session_body(**overrides):
    attendees = [{"student_id": "u-aarav", "present": True}] + [
        {"student_id": uid, "present": i != 1} for i, uid in enumerate(MEERA_MENTEES)
    ]
    body = {
        "date": iso(-3),
        "mode": "in_person",
        "kind": "group",
        "context": "assigned",
        "attendees": attendees,
        "topics": ["academic", "attendance"],
        "notes": "SECRET-NOTE-123 discussed mid-sem prep",
        "action_items": [
            {"student_id": "u-aarav", "text": "Finish DL assignment 3", "owner": "mentee", "due_date": iso(7)},
            {"student_id": "u-s01", "text": "Meet the lab assistant", "owner": "mentor", "due_date": iso(7)},
        ],
        "issues": [{"student_id": "u-s02", "category": "attendance", "text": "Attendance below 75%"}],
    }
    body.update(overrides)
    return body


def post_session(client, headers, body=None, key: str | None = None):
    extra = {"Idempotency-Key": key} if key else {}
    return client.post("/api/v1/sessions", json=body or session_body(), headers={**headers, **extra})


# ================= TEST-27: allotment =================


def test_27_allotment_view_and_assign(client, suresh):
    view = client.get("/api/v1/dept/allotment", headers=suresh).json()
    mentors = {m["mentor_id"]: m for m in view["mentors"]}
    assert mentors["u-meera"]["mentee_count"] == 12 and mentors["u-meera"]["overloaded"] is False
    assert {s["user_id"] for s in view["unallotted"]} == set(UNALLOTTED)

    response = client.post("/api/v1/allotments", json={"mentor_id": "u-meera", "student_ids": UNALLOTTED}, headers=suresh)
    assert response.status_code == 200
    after = response.json()
    assert after["unallotted"] == [] and {m["mentor_id"]: m for m in after["mentors"]}["u-meera"]["mentee_count"] == 14

    # allotted notification to each student; StatusEvent per new link
    notes = cypher("MATCH (n:Notification {type: 'allotted'})-[:NOTIFIES]->(u:User) RETURN u.user_id AS u ORDER BY u")
    assert [n["u"] for n in notes] == UNALLOTTED
    events = cypher("MATCH (e:StatusEvent {entity_type: 'mentorship'}) RETURN count(e) AS c")[0]["c"]
    assert events == 2


def test_27_reallot_is_a_handover_and_same_mentor_is_a_noop(client, suresh):
    client.post("/api/v1/allotments", json={"mentor_id": "u-meera", "student_ids": ["u-un1"]}, headers=suresh)
    before = cypher("MATCH (e:StatusEvent) RETURN count(e) AS c")[0]["c"]
    client.post("/api/v1/allotments", json={"mentor_id": "u-meera", "student_ids": ["u-un1"]}, headers=suresh)
    assert cypher("MATCH (e:StatusEvent) RETURN count(e) AS c")[0]["c"] == before  # no-op: nothing written

    view = client.post("/api/v1/allotments", json={"mentor_id": "u-arjun", "student_ids": ["u-un1"]}, headers=suresh).json()
    mentors = {m["mentor_id"]: m for m in view["mentors"]}
    assert mentors["u-arjun"]["mentee_count"] == 2 and mentors["u-meera"]["mentee_count"] == 12
    links = cypher(
        """
        MATCH (f:Faculty)-[m:MENTORS {type: 'assigned'}]->(:Student {user_id: 'u-un1'})
        RETURN f.user_id AS mentor, m.status AS status, m.end_reason AS reason ORDER BY m.since, status
        """
    )
    assert {"mentor": "u-meera", "status": "ended", "reason": "handover"} in links
    assert {"mentor": "u-arjun", "status": "active", "reason": None} in links


def test_27_twenty_first_mentee_is_allowed_and_flagged(client, suresh):
    for i in range(8):  # 12 + 8 = 20 mentees
        new_student(f"u-x{i}", f"Extra {i}", f"CB.EN.U4CSE24{300 + i}", "u-meera")
    new_student("u-x21", "Extra 21", "CB.EN.U4CSE24399", None)
    response = client.post("/api/v1/allotments", json={"mentor_id": "u-meera", "student_ids": ["u-x21"]}, headers=suresh)
    assert response.status_code == 200
    meera = {m["mentor_id"]: m for m in response.json()["mentors"]}["u-meera"]
    assert meera["mentee_count"] == 21 and meera["overloaded"] is True
    cypher("MATCH (s:Student) WHERE s.user_id STARTS WITH 'u-x' DETACH DELETE s")


def test_27_allotment_roles_and_scope(client, suresh, meera, aarav, kavya):
    body = {"mentor_id": "u-meera", "student_ids": ["u-un1"]}
    for headers in (meera, aarav, kavya):
        assert client.post("/api/v1/allotments", json=body, headers=headers).status_code == 403
        assert client.get("/api/v1/dept/allotment", headers=headers).status_code == 403
    assert client.post("/api/v1/allotments", json={"mentor_id": "u-nobody", "student_ids": ["u-un1"]}, headers=suresh).status_code == 404
    assert client.post("/api/v1/allotments", json={"mentor_id": "u-aarav", "student_ids": ["u-un1"]}, headers=suresh).status_code == 404  # not faculty
    assert client.post("/api/v1/allotments", json={"mentor_id": "u-meera", "student_ids": ["u-ghost"]}, headers=suresh).status_code == 404
    assert client.post("/api/v1/allotments", json={"mentor_id": "u-meera", "student_ids": []}, headers=suresh).status_code == 422
    assert client.post("/api/v1/allotments", json={**body, "student_ids": [f"u{i}" for i in range(31)]}, headers=suresh).status_code == 422
    dup = client.post("/api/v1/allotments", json={"mentor_id": "u-meera", "student_ids": ["u-un1", "u-un1"]}, headers=suresh)
    assert dup.status_code == 200 and cypher("MATCH (:Faculty)-[m:MENTORS {status:'active'}]->(:Student {user_id:'u-un1'}) RETURN count(m) AS c")[0]["c"] == 1


# ================= TEST-28: session rules =================


def test_28_group_session_saved_in_one_go(client, meera):
    response = post_session(client, meera)
    assert response.status_code == 201
    body = response.json()
    assert body["logged_by"]["user_id"] == "u-meera" and body["kind"] == "group" and body["context"] == "assigned"
    assert len(body["attendees"]) == 12 and sum(a["present"] for a in body["attendees"]) == 11
    assert all(a["confirmed_at"] is None for a in body["attendees"])
    assert {i["owner"] for i in body["action_items"]} == {"mentee", "mentor"} and all(i["status"] == "open" for i in body["action_items"])
    assert body["issues"][0]["status"] == "raised" and body["issues"][0]["text"] == "Attendance below 75%"
    assert body["notes"].startswith("SECRET-NOTE-123")  # author sees notes
    assert counts()["sessions"] == 1


def test_28_notifications_go_to_present_attendees_only(client, meera):  # also TEST-35
    post_session(client, meera)
    logged = cypher("MATCH (n:Notification {type: 'session_logged'})-[:NOTIFIES]->(u:User) RETURN u.user_id AS u")
    recipients = {r["u"] for r in logged}
    assert len(recipients) == 11 and "u-s02" not in recipients  # u-s02 is marked absent: not notified
    assigned = cypher("MATCH (n:Notification {type: 'action_assigned'})-[:NOTIFIES]->(u:User) RETURN u.user_id AS u")
    assert [r["u"] for r in assigned] == ["u-aarav"]  # only the mentee-owned item
    titles = {r["t"] for r in cypher("MATCH (n:Notification) RETURN n.title AS t")}
    assert all("SECRET" not in t for t in titles)
    events = cypher("MATCH (e:StatusEvent) RETURN e.entity_type AS t, count(*) AS c ORDER BY t")
    assert {e["t"]: e["c"] for e in events} == {"action_item": 2, "issue": 1}


def test_28_validation_failures_write_nothing(client, meera):
    before = counts()
    cases = [
        (session_body(date=iso(1)), "date", "Session date cannot be in the future."),
        (session_body(kind="individual"), "attendees", "An individual session needs exactly one attendee."),
        (session_body(context="guide"), "opening_id", "Choose the opening for a guide session."),
        (session_body(next_followup=iso(-3)), "next_followup", "Follow-up date must be after the session date."),
        (session_body(attendees=[{"student_id": "u-aarav", "present": True}] * 2), "attendees", "Each student can appear only once."),
    ]
    for body, field, message in cases:
        response = post_session(client, meera, body)
        assert response.status_code == 422, field
        errors = response.json()["errors"]
        assert {"field": field, "message": message} in errors
    bad_item = session_body(action_items=[{"student_id": "u-diya", "text": "x", "owner": "mentee", "due_date": iso(7)}])
    assert post_session(client, meera, bad_item).status_code == 422
    early_due = session_body(action_items=[{"student_id": "u-aarav", "text": "x", "owner": "mentee", "due_date": iso(-10)}])
    assert post_session(client, meera, early_due).status_code == 422
    issue_for_stranger = session_body(issues=[{"student_id": "u-diya", "category": "other", "text": "x"}])
    assert post_session(client, meera, issue_for_stranger).status_code == 422
    assert post_session(client, meera, session_body(topics=[])).status_code == 422
    assert post_session(client, meera, session_body(attendees=[])).status_code == 422
    forty_one = [{"student_id": f"u-n{i}", "present": True} for i in range(41)]
    assert post_session(client, meera, session_body(attendees=forty_one)).status_code == 422
    assert post_session(client, meera, session_body(notes="x" * 4001)).status_code == 422
    assert counts() == before


def test_28_non_mentee_attendee_is_422_and_nothing_is_saved(client, meera):
    before = counts()
    attendees = [{"student_id": "u-aarav", "present": True}, {"student_id": "u-diya", "present": True}]  # Diya is Arjun's
    response = post_session(client, meera, session_body(attendees=attendees, action_items=[], issues=[]))
    assert response.status_code == 422
    assert response.json()["code"] == "NOT_YOUR_MENTEE" and "Diya" in response.json()["detail"]
    assert counts() == before


def test_28_session_date_must_be_in_current_or_previous_term(client, meera):
    too_old = post_session(client, meera, session_body(date="2025-12-01", action_items=[], issues=[]))
    assert too_old.status_code == 422
    assert {"field": "date", "message": "Session date must be in the current or previous term."} in too_old.json()["errors"]
    previous_term = post_session(client, meera, session_body(date="2026-03-10", action_items=[], issues=[]))
    assert previous_term.status_code == 201


def test_28_fault_injection_rolls_back_everything(client, meera, monkeypatch):
    before = counts()

    def boom(*args, **kwargs):
        raise RuntimeError("injected failure after the session node exists")

    monkeypatch.setattr("app.services.mentorship.record_status", boom)
    response = client.post("/api/v1/sessions", json=session_body(), headers={**meera, "Idempotency-Key": str(uuid.uuid4())})
    assert response.status_code == 500 and response.json()["code"] == "INTERNAL"  # a clean problem+json, no stack trace
    assert response.json()["request_id"] == response.headers["x-request-id"] and "injected" not in response.text
    assert counts() == before  # no session, attendee, item, issue, event, notification or key survived


def test_28_individual_and_guide_sessions(client, meera):
    individual = session_body(kind="individual", attendees=[{"student_id": "u-aarav", "present": True}], action_items=[], issues=[])
    assert post_session(client, meera, individual).status_code == 201
    # a guide session needs an active guide link for that opening
    guide = session_body(context="guide", opening_id="op-edge-ai", attendees=[{"student_id": "u-aarav", "present": True}], kind="individual", action_items=[], issues=[])
    assert post_session(client, meera, guide).status_code == 422  # Aarav is not (yet) a guided student
    cypher(
        "MATCH (f:Faculty {user_id: 'u-meera'}), (s:Student {user_id: 'u-aarav'}) "
        "MERGE (f)-[m:MENTORS {id: 'mt-guide-test', type: 'guide', opening_id: 'op-edge-ai'}]->(s) SET m.status = 'active'"
    )
    ok = post_session(client, meera, guide)
    assert ok.status_code == 201 and ok.json()["context"] == "guide" and ok.json()["opening_id"] == "op-edge-ai"
    cypher("MATCH ()-[m:MENTORS {id: 'mt-guide-test'}]->() DELETE m")


def test_28_only_faculty_can_log(client, aarav, suresh, kavya):
    for headers in (aarav, suresh, kavya):
        assert post_session(client, headers).status_code == 403


# ================= idempotency =================


def test_idempotency_replay_returns_the_original(client, meera):
    key = str(uuid.uuid4())
    first = post_session(client, meera, key=key)
    second = post_session(client, meera, key=key)
    assert first.status_code == second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert counts()["sessions"] == 1
    third = post_session(client, meera, key=str(uuid.uuid4()))
    assert third.json()["id"] != first.json()["id"] and counts()["sessions"] == 2


def test_idempotency_key_must_be_a_uuid_and_expires(client, meera):
    bad = post_session(client, meera, key="not-a-uuid")
    assert bad.status_code == 422 and bad.json()["errors"][0]["field"] == "Idempotency-Key"
    key = str(uuid.uuid4())
    original = post_session(client, meera, key=key).json()["id"]
    cypher("MATCH (k:IdempotencyKey {key: $k}) SET k.created_at = '2020-01-01T00:00:00.000Z'", k=key)  # older than 24 h
    fresh = post_session(client, meera, key=key)
    assert fresh.status_code == 201 and fresh.json()["id"] != original


# ================= TEST-20 and visibility =================


def test_20_notes_are_visible_only_to_the_author(client, meera, arjun, aarav, suresh, kavya):
    session_id = post_session(client, meera).json()["id"]
    url = f"/api/v1/sessions/{session_id}"
    author = client.get(url, headers=meera)
    assert author.status_code == 200 and author.json()["notes"].startswith("SECRET-NOTE-123")
    attendee = client.get(url, headers=aarav)
    assert attendee.status_code == 200 and "notes" not in attendee.json() and "SECRET-NOTE" not in attendee.text
    assert client.get(url, headers=suresh).status_code == 403  # HOD is not a role on API-027
    assert client.get(url, headers=kavya).status_code == 403
    assert client.get(url, headers=arjun).status_code == 404  # faculty, not the author
    assert client.get("/api/v1/sessions/does-not-exist", headers=meera).status_code == 404


def test_attendee_sees_only_their_own_rows(client, meera, aarav, diya):
    session_id = post_session(client, meera).json()["id"]
    mine = client.get(f"/api/v1/sessions/{session_id}", headers=aarav).json()
    assert [a["student_id"] for a in mine["attendees"]] == ["u-aarav"]
    assert [i["student_id"] for i in mine["action_items"]] == ["u-aarav"]
    assert mine["issues"] == []  # the issue is about another student
    assert client.get(f"/api/v1/sessions/{session_id}", headers=diya).status_code == 404  # not an attendee


def test_confidential_issue_text_is_hidden_from_the_student(client, meera, aarav):
    body = session_body(issues=[{"student_id": "u-aarav", "category": "personal", "text": "SECRET-ISSUE-456", "confidential": True}])
    session_id = post_session(client, meera, body).json()["id"]
    student_view = client.get(f"/api/v1/sessions/{session_id}", headers=aarav).json()
    issue = student_view["issues"][0]
    assert issue["category"] == "personal" and issue["status"] == "raised" and issue["confidential"] is True
    assert "text" not in issue and "resolution" not in issue and "SECRET-ISSUE" not in str(student_view)
    author_view = client.get(f"/api/v1/sessions/{session_id}", headers=meera).json()
    assert author_view["issues"][0]["text"] == "SECRET-ISSUE-456"


# ================= TEST-29: confirm =================


def test_29_confirm_present_absent_and_repeat(client, meera, aarav):
    session = post_session(client, meera).json()
    url = f"/api/v1/sessions/{session['id']}/confirm"
    first = client.post(url, headers=aarav)
    assert first.status_code == 200
    stamp = first.json()["attendees"][0]["confirmed_at"]
    assert stamp is not None
    again = client.post(url, headers=aarav)
    assert again.status_code == 200 and again.json()["attendees"][0]["confirmed_at"] == stamp  # unchanged
    assert "notes" not in first.json()

    absent_headers = _headers_for("u-s02")  # the one attendee marked absent
    absent = client.post(url, headers=absent_headers)
    assert absent.status_code == 409 and absent.json()["code"] == "NOT_PRESENT"

    assert client.post(url, headers=_headers_for("u-diya")).status_code == 404  # not an attendee
    assert client.post(url, headers=meera).status_code == 403  # faculty role
    # the author's view shows who confirmed
    view = client.get(f"/api/v1/sessions/{session['id']}", headers=meera).json()
    assert next(a for a in view["attendees"] if a["student_id"] == "u-aarav")["confirmed_at"] == stamp


def _headers_for(user_id: str, role: str = "student"):
    from app.core.security import create_token

    token, _ = create_token(user_id, role)
    return {"Authorization": f"Bearer {token}"}


# ================= TEST-30: action items =================


def _first_item(client, headers, owner="mentee", due=None):
    body = session_body(
        action_items=[{"student_id": "u-aarav", "text": "Task", "owner": owner, "due_date": due or iso(7)}], issues=[]
    )
    return post_session(client, headers, body).json()["action_items"][0]


def test_30_overdue_is_derived_and_clears_when_done(client, meera, aarav):
    item = _first_item(client, meera, due=iso(-1))
    assert item["overdue"] is True and item["status"] == "open"
    done = client.patch(f"/api/v1/action-items/{item['id']}", json={"status": "done"}, headers=aarav)
    assert done.status_code == 200 and done.json()["status"] == "done" and done.json()["overdue"] is False
    assert [e["to_status"] for e in done.json()["history"]] == ["open", "done"]


def test_30_who_may_change_what(client, meera, arjun, aarav, diya):
    item = _first_item(client, meera)
    url = f"/api/v1/action-items/{item['id']}"
    assert client.patch(url, json={"status": "verified"}, headers=aarav).status_code == 403  # mentee cannot verify
    assert client.patch(url, json={"status": "dropped"}, headers=aarav).status_code == 403
    assert client.patch(url, json={"status": "done"}, headers=meera).status_code == 403  # mentor cannot mark it done
    assert client.patch(url, json={"status": "done"}, headers=diya).status_code == 404  # someone else's item
    assert client.patch(url, json={"status": "verified"}, headers=arjun).status_code == 404  # not the author
    assert client.patch(url, json={"status": "verified"}, headers=meera).status_code == 409  # still open
    assert client.patch(url, json={"status": "done"}, headers=aarav).status_code == 200
    assert client.patch(url, json={"status": "done"}, headers=aarav).status_code == 409  # already done
    verified = client.patch(url, json={"status": "verified"}, headers=meera)
    assert verified.status_code == 200 and verified.json()["status"] == "verified"
    assert client.patch(url, json={"status": "dropped"}, headers=meera).status_code == 409  # verified is final
    assert client.patch("/api/v1/action-items/nope", json={"status": "done"}, headers=aarav).status_code == 404
    assert client.patch(url, json={"status": "bogus"}, headers=meera).status_code == 422


def test_30_mentor_can_reopen_and_drop(client, meera, aarav):
    item = _first_item(client, meera)
    url = f"/api/v1/action-items/{item['id']}"
    client.patch(url, json={"status": "done"}, headers=aarav)
    reopened = client.patch(url, json={"status": "open"}, headers=meera)
    assert reopened.status_code == 200 and reopened.json()["status"] == "open"
    dropped = client.patch(url, json={"status": "dropped"}, headers=meera)
    assert dropped.status_code == 200 and dropped.json()["status"] == "dropped"


# ================= TEST-31: issues =================


def _issue_in_session(client, headers, student="u-s02"):
    body = session_body(issues=[{"student_id": student, "category": "attendance", "text": "Low attendance"}], action_items=[])
    session = post_session(client, headers, body).json()
    return session["issues"][0]


def test_31_resolve_needs_a_note_and_sets_resolved_at(client, meera):
    issue = _issue_in_session(client, meera)
    url = f"/api/v1/issues/{issue['id']}"
    assert client.patch(url, json={"status": "resolved", "resolution": ""}, headers=meera).status_code == 422
    assert client.patch(url, json={"status": "resolved"}, headers=meera).status_code == 422
    resolved = client.patch(url, json={"status": "resolved", "resolution": "Spoke to the student."}, headers=meera)
    assert resolved.status_code == 200
    body = resolved.json()
    assert body["status"] == "resolved" and body["resolved_at"] and body["resolution"] == "Spoke to the student."
    assert [e["to_status"] for e in body["history"]] == ["raised", "resolved"]
    assert client.patch(url, json={"status": "resolved", "resolution": "again"}, headers=meera).status_code == 409


def test_31_not_available_yet_actions_return_409(client, meera):
    issue = _issue_in_session(client, meera)
    url = f"/api/v1/issues/{issue['id']}"
    for body in ({"status": "acknowledged"}, {"status": "in_progress"}, {"escalated": True}, {"confidential": True}):
        response = client.patch(url, json=body, headers=meera)
        assert response.status_code == 409 and response.json()["code"] == "INVALID_TRANSITION", body


def test_31_raise_issue_scope_roles_and_literal_text(client, meera, arjun, aarav, suresh):
    before = counts()
    payload = "}) MATCH (n) DETACH DELETE n //"
    created = client.post("/api/v1/issues", json={"student_id": "u-aarav", "category": "academic", "text": payload}, headers=meera)
    assert created.status_code == 201 and created.json()["text"] == payload  # TEST-07: stored literally
    assert counts()["issues"] == before["issues"] + 1
    assert cypher("MATCH (u:User {user_id: 'u-aarav'}) RETURN count(u) AS c")[0]["c"] == 1  # nothing was deleted
    body = {"student_id": "u-aarav", "category": "academic", "text": "x"}
    assert client.post("/api/v1/issues", json=body, headers=arjun).status_code == 404  # not Aarav's mentor
    assert client.post("/api/v1/issues", json=body, headers=aarav).status_code == 403  # student path arrives with A7
    assert client.post("/api/v1/issues", json=body, headers=suresh).status_code == 403
    other_session = post_session(client, meera).json()["id"]
    assert client.post("/api/v1/issues", json={**body, "session_id": other_session}, headers=meera).status_code == 201
    assert client.post("/api/v1/issues", json={**body, "session_id": "nope"}, headers=meera).status_code == 404
    assert client.post("/api/v1/issues", json={**body, "text": ""}, headers=meera).status_code == 422


def test_31_scope_on_patch(client, meera, arjun, aarav, suresh, kavya):
    issue = _issue_in_session(client, meera)
    url = f"/api/v1/issues/{issue['id']}"
    body = {"status": "resolved", "resolution": "ok"}
    assert client.patch(url, json=body, headers=arjun).status_code == 404  # not the student's mentor
    assert client.patch(url, json=body, headers=aarav).status_code == 403
    assert client.patch(url, json=body, headers=kavya).status_code == 403
    assert client.patch(url, json=body, headers=suresh).status_code == 404  # HOD: only escalated issues
    assert client.patch("/api/v1/issues/nope", json=body, headers=meera).status_code == 404
