"""Applications (TEST-23, REQ-006), student profile scope (API-003) and profile updates (API-004, TEST-07)."""
import pytest

from app.core.clock import today
from app.core.database import run_read, run_write

OPENING = "op-edge-ai"


def _cypher(query: str, **params):
    return run_write(lambda tx: [r.data() for r in tx.run(query, **params)])


@pytest.fixture(autouse=True)
def _clean(fresh_seed):
    """Each test starts with no applications, no guide links and no notifications for these personas."""
    _cypher("MATCH ()-[a:APPLIED_TO]->() DELETE a")
    _cypher("MATCH ()-[m:MENTORS {type: 'guide'}]->() DELETE m")
    _cypher("MATCH (e:StatusEvent) DETACH DELETE e")
    _cypher("MATCH (n:Notification) DETACH DELETE n")
    _cypher("MATCH (o:Opening {id: 'op-closed'}) DETACH DELETE o")
    _cypher("MATCH (o:Opening {id: $oid}) SET o.status = 'open'", oid=OPENING)
    _cypher(
        """
        MATCH (s:Student {user_id: 'u-aarav'}) SET s.bio = null, s.interests = []
        WITH s MATCH (s)-[h:HAS_SKILL]->() DELETE h
        """
    )


def _apply(client, headers, opening_id=OPENING):
    return client.post(f"/api/v1/openings/{opening_id}/applications", headers=headers)


def _set_status(application_id: str, status: str) -> None:
    _cypher("MATCH ()-[a:APPLIED_TO {id: $id}]->() SET a.status = $status", id=application_id, status=status)


# ---- TEST-23: apply ------------------------------------------------------------------------------------------------


def test_apply_creates_pending_application_and_notifies_owner(client, aarav, meera):
    response = _apply(client, aarav)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending" and body["opening_id"] == OPENING and body["student_id"] == "u-aarav"
    assert body["opening_title"] and [e["to_status"] for e in body["history"]] == ["pending"]
    assert body["history"][0]["from_status"] is None and body["history"][0]["actor_name"]

    inbox = client.get("/api/v1/me/notifications", headers=meera).json()
    received = [n for n in inbox["items"] if n["type"] == "application_received"]
    assert len(received) == 1
    assert received[0]["title"].endswith("applied to Edge AI for Agriculture")
    assert received[0]["link"] == f"/faculty/openings/{OPENING}"


def test_double_apply_is_409_and_creates_nothing_new(client, aarav):
    assert _apply(client, aarav).status_code == 201
    again = _apply(client, aarav)
    assert again.status_code == 409 and again.json()["code"] == "ALREADY_APPLIED"
    count = _cypher("MATCH (:Student {user_id: 'u-aarav'})-[a:APPLIED_TO]->() RETURN count(a) AS c")[0]["c"]
    assert count == 1
    assert len(client.get("/api/v1/me/applications", headers=aarav).json()) == 1


def test_apply_to_missing_and_closed_openings(client, aarav):
    missing = _apply(client, aarav, "op-does-not-exist")
    assert missing.status_code == 404 and missing.json()["code"] == "NOT_FOUND"
    _cypher("MERGE (o:Opening {id: 'op-closed'}) SET o.title = 'Closed role', o.status = 'closed'")
    closed = _apply(client, aarav, "op-closed")
    assert closed.status_code == 409 and closed.json()["code"] == "OPENING_CLOSED"
    # closed is checked before already-applied
    _cypher("MATCH (s:Student {user_id: 'u-aarav'}), (o:Opening {id: 'op-closed'}) CREATE (s)-[:APPLIED_TO {id: 'x'}]->(o)")
    assert _apply(client, aarav, "op-closed").json()["code"] == "OPENING_CLOSED"


def test_only_students_can_apply(client, meera, suresh, kavya):
    for headers in (meera, suresh, kavya):
        assert _apply(client, headers).status_code == 403


# ---- TEST-23: every cell of the transition table --------------------------------------------------------------------

STATES = ["pending", "shortlisted", "accepted", "rejected", "completed"]
TARGETS = ["shortlisted", "accepted", "rejected", "completed"]
ALLOWED = {
    ("pending", "shortlisted"), ("pending", "rejected"),
    ("shortlisted", "accepted"), ("shortlisted", "rejected"),
    ("accepted", "completed"),
}  # fmt: skip


@pytest.mark.parametrize("current", STATES)
@pytest.mark.parametrize("target", TARGETS)
def test_transition_table(client, aarav, meera, current, target):
    application_id = _apply(client, aarav).json()["id"]
    _set_status(application_id, current)
    response = client.patch(f"/api/v1/applications/{application_id}", json={"status": target}, headers=meera)
    if (current, target) in ALLOWED:
        assert response.status_code == 200, (current, target)
        assert response.json()["status"] == target
    else:
        assert response.status_code == 409, (current, target)
        assert response.json()["code"] == "INVALID_TRANSITION"
        assert f"from {current} to {target}" in response.json()["detail"]
        stored = _cypher("MATCH ()-[a:APPLIED_TO {id: $id}]->() RETURN a.status AS s", id=application_id)[0]["s"]
        assert stored == current  # nothing changed


def test_transition_notifies_student_and_records_history(client, aarav, meera):
    application_id = _apply(client, aarav).json()["id"]
    done = client.patch(f"/api/v1/applications/{application_id}", json={"status": "shortlisted"}, headers=meera)
    assert done.status_code == 200
    assert [e["to_status"] for e in done.json()["history"]] == ["pending", "shortlisted"]
    inbox = client.get("/api/v1/me/notifications", headers=aarav).json()["items"]
    status_notes = [n for n in inbox if n["type"] == "application_status"]
    assert len(status_notes) == 1 and status_notes[0]["title"].endswith("is now shortlisted")


def test_accept_creates_guide_link_and_complete_ends_it(client, aarav, meera):
    application_id = _apply(client, aarav).json()["id"]
    client.patch(f"/api/v1/applications/{application_id}", json={"status": "shortlisted"}, headers=meera)
    accepted = client.patch(f"/api/v1/applications/{application_id}", json={"status": "accepted"}, headers=meera)
    assert accepted.status_code == 200
    link = _cypher(
        """
        MATCH (:Faculty {user_id: 'u-meera'})-[m:MENTORS {type: 'guide'}]->(:Student {user_id: 'u-aarav'})
        RETURN m.status AS status, m.opening_id AS opening_id, m.since AS since
        """
    )
    assert link == [{"status": "active", "opening_id": OPENING, "since": today().isoformat()}]

    client.patch(f"/api/v1/applications/{application_id}", json={"status": "completed"}, headers=meera)
    ended = _cypher(
        "MATCH (:Faculty)-[m:MENTORS {type: 'guide'}]->(:Student {user_id: 'u-aarav'}) "
        "RETURN m.status AS status, m.end_reason AS reason, m.until AS until"
    )
    assert ended == [{"status": "ended", "reason": "completed", "until": today().isoformat()}]


def test_decide_scope_and_roles(client, aarav, meera, arjun, suresh):
    application_id = _apply(client, aarav).json()["id"]
    body = {"status": "shortlisted"}
    assert client.patch(f"/api/v1/applications/{application_id}", json=body, headers=arjun).status_code == 404
    assert client.patch(f"/api/v1/applications/{application_id}", json=body, headers=aarav).status_code == 403
    assert client.patch(f"/api/v1/applications/{application_id}", json=body, headers=suresh).status_code == 403
    assert client.patch("/api/v1/applications/nope", json=body, headers=meera).status_code == 404
    assert client.patch(f"/api/v1/applications/{application_id}", json={"status": "pending"}, headers=meera).status_code == 422
    assert client.patch(f"/api/v1/applications/{application_id}", json={"status": "x", "extra": 1}, headers=meera).status_code == 422


def test_my_applications_lists_only_own(client, aarav, diya):
    first = _apply(client, aarav).json()
    assert _apply(client, diya).status_code == 201
    mine = client.get("/api/v1/me/applications", headers=aarav).json()
    assert [a["id"] for a in mine] == [first["id"]] and mine[0]["student_id"] == "u-aarav"
    assert client.get("/api/v1/me/applications", headers=diya).json()[0]["student_id"] == "u-diya"


# ---- API-003: profile scope ----------------------------------------------------------------------------------------


def test_profile_scope_matrix(client, aarav, diya, meera, arjun, suresh, kavya):
    url = "/api/v1/students/u-aarav"
    assert client.get(url, headers=aarav).status_code == 200  # self
    assert client.get(url, headers=meera).status_code == 200  # assigned mentor
    assert client.get(url, headers=suresh).status_code == 200  # HOD of the department
    assert client.get(url, headers=diya).status_code == 404  # another student: out of scope
    assert client.get(url, headers=arjun).status_code == 404  # faculty who is neither mentor nor owner of an applied opening
    assert client.get(url, headers=kavya).status_code == 403  # IQAC role not listed
    assert client.get("/api/v1/students/u-nobody", headers=suresh).status_code == 404

    # An applicant becomes visible to the faculty who owns the opening (REQ-005)
    assert client.get("/api/v1/students/u-diya", headers=meera).status_code == 404
    assert _apply(client, diya).status_code == 201
    assert client.get("/api/v1/students/u-diya", headers=meera).status_code == 200


def test_profile_shape_has_no_private_fields(client, aarav):
    body = client.get("/api/v1/students/u-aarav", headers=aarav).json()
    assert set(body) == {"user_id", "name", "roll_no", "year", "dept_code", "bio", "interests", "skills"}
    assert "embedding" not in body and "password_hash" not in body


# ---- API-004: partial profile update -------------------------------------------------------------------------------


def test_patch_updates_only_provided_fields(client, aarav):
    first = client.patch("/api/v1/me/profile", json={"bio": "I like robots.", "interests": ["robotics", "AI"]}, headers=aarav)
    assert first.status_code == 200 and first.json()["bio"] == "I like robots."
    second = client.patch("/api/v1/me/profile", json={"interests": ["vision"]}, headers=aarav)
    assert second.json()["bio"] == "I like robots." and second.json()["interests"] == ["vision"]  # bio untouched
    cleared = client.patch("/api/v1/me/profile", json={"bio": None}, headers=aarav)
    assert cleared.json()["bio"] is None and cleared.json()["interests"] == ["vision"]
    assert client.patch("/api/v1/me/profile", json={}, headers=aarav).status_code == 200  # empty patch is a no-op


def test_patch_claimed_skills_full_list_semantics(client, aarav):
    added = client.patch("/api/v1/me/profile", json={"claimed_skills": ["Python", "  deep   learning ", "PyTorch"]}, headers=aarav)
    assert added.status_code == 200
    skills = {s["concept"]: s for s in added.json()["skills"]}
    assert set(skills) == {"python", "deep learning", "pytorch"}
    assert all(s["claimed"] and s["trust_level"] == 0 and s["sources"] == [] for s in skills.values())

    # a certified skill the student stops claiming must survive (claimed false, trust kept)
    _cypher(
        """
        MATCH (:Student {user_id: 'u-aarav'})-[h:HAS_SKILL]->(:Concept {name: 'python'})
        SET h.trust_level = 1, h.evidence_ids = ['ev-test']
        """
    )
    reduced = client.patch("/api/v1/me/profile", json={"claimed_skills": ["pytorch"]}, headers=aarav)
    after = {s["concept"]: s for s in reduced.json()["skills"]}
    assert set(after) == {"python", "pytorch"}  # deep learning (claim only) is gone, python (certified) stays
    assert after["python"]["claimed"] is False and after["python"]["trust_level"] == 1
    assert after["pytorch"]["claimed"] is True

    omitted = client.patch("/api/v1/me/profile", json={"bio": "hi"}, headers=aarav)
    assert {s["concept"] for s in omitted.json()["skills"]} == {"python", "pytorch"}  # skills untouched when omitted


def test_patch_validation_and_roles(client, aarav, meera):
    too_many = client.patch("/api/v1/me/profile", json={"interests": [str(i) for i in range(11)]}, headers=aarav)
    assert too_many.status_code == 422 and too_many.json()["code"] == "VALIDATION_FAILED"
    assert client.patch("/api/v1/me/profile", json={"bio": "x" * 501}, headers=aarav).status_code == 422
    assert client.patch("/api/v1/me/profile", json={"claimed_skills": [""]}, headers=aarav).status_code == 422
    assert client.patch("/api/v1/me/profile", json={"password_hash": "x"}, headers=aarav).status_code == 422  # extra field
    assert client.patch("/api/v1/me/profile", json={"bio": "x"}, headers=meera).status_code == 403


def test_07_injection_text_is_stored_literally(client, aarav):
    before = _cypher("MATCH (n) RETURN count(n) AS c")[0]["c"]
    payload = "x' RETURN 1 //"
    response = client.patch("/api/v1/me/profile", json={"bio": payload, "claimed_skills": ["}) MATCH (n) DETACH DELETE n //"]}, headers=aarav)
    assert response.status_code == 200 and response.json()["bio"] == payload
    after = _cypher("MATCH (n) RETURN count(n) AS c")[0]["c"]
    assert after >= before  # nothing was deleted (one concept node may have been added)
    assert run_read(lambda tx: tx.run("MATCH (u:User {user_id: 'u-aarav'}) RETURN u.bio AS bio").single()["bio"]) == payload
