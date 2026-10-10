"""REQ-040 / TEST-74: marking guided work completed leaves a project record (Evidence certified by the guide) and the
guide endorses the skills they vouch for. Uses the stand-in graph of test_applications: Meera posted op-edge-ai
(it requires pytorch); Aarav applies; Arjun is another faculty member; Diya another student."""
import io

import openpyxl

from tests.test_applications import COMPLETION, OPENING, _apply, _clean, _cypher  # noqa: F401  (autouse: clean graph)

URL = "/api/v1/applications/{}"


def _accepted(client, aarav, meera) -> str:
    application_id = _apply(client, aarav).json()["id"]
    for status in ("shortlisted", "accepted"):
        assert client.patch(URL.format(application_id), json={"status": status}, headers=meera).status_code == 200
    return application_id


def _complete(client, meera, application_id, completion=COMPLETION):
    body = {"status": "completed"}
    if completion is not None:
        body["completion"] = completion
    return client.patch(URL.format(application_id), json=body, headers=meera)


def _records(client, headers) -> list[dict]:
    return [c for c in client.get("/api/v1/me/certificates", headers=headers).json() if c["kind"] == "project_record"]


def test_74_completion_leaves_a_record_and_the_guide_vouches(client, aarav, meera, suresh):
    application_id = _accepted(client, aarav, meera)
    done = _complete(client, meera, application_id)
    assert done.status_code == 200, done.text
    assert [e["to_status"] for e in done.json()["history"]][-1] == "completed"

    (record,) = _records(client, aarav)
    assert record["status"] == "certified" and record["media_type"] is None and record["source"] == "guide"
    assert record["title"] == _cypher("MATCH (o:Opening {id: $id}) RETURN o.title AS t", id=OPENING)[0]["t"]
    assert record["summary"] == COMPLETION["summary"] and record["output_type"] == "prototype"
    assert record["recorded_by"] == "Meera" and record["skills"] == ["pytorch"] and record["type"] == "project"

    mine = client.get("/api/v1/me/profile", headers=aarav).json()
    skill = next(k for k in mine["skills"] if k["concept"] == "pytorch")
    assert skill["trust_level"] == 2 and skill["endorsed_by"] == ["Meera"] and not skill["claimed"]
    assert any(s["evidence_id"] == record["id"] for s in skill["sources"])

    notes = [n for n in client.get("/api/v1/me/notifications", headers=aarav).json()["items"] if n["type"] == "project_recorded"]
    assert len(notes) == 1 and "Meera" in notes[0]["title"] and notes[0]["link"] == "/student/certificates"
    events = _cypher("MATCH (e:StatusEvent {entity_type: 'evidence', entity_id: $id}) RETURN e.to_status AS s", id=record["id"])
    assert events == [{"s": "certified"}]  # the audit trail has the record

    assert client.get(f"/api/v1/certificates/{record['id']}", headers=meera).status_code == 200
    assert client.get(f"/api/v1/certificates/{record['id']}", headers=suresh).status_code == 200  # the HOD


def test_74_a_completion_without_the_record_is_refused_and_changes_nothing(client, aarav, meera):
    application_id = _accepted(client, aarav, meera)
    r = _complete(client, meera, application_id, completion=None)
    assert r.status_code == 422 and r.json()["errors"][0]["field"] == "completion"
    assert _cypher("MATCH ()-[a:APPLIED_TO {id: $id}]->() RETURN a.status AS s", id=application_id) == [{"s": "accepted"}]
    assert _records(client, aarav) == []


def test_74_the_record_only_goes_with_completing(client, aarav, meera):
    application_id = _apply(client, aarav).json()["id"]
    r = client.patch(URL.format(application_id), json={"status": "shortlisted", "completion": COMPLETION}, headers=meera)
    assert r.status_code == 422


def test_74_the_guide_cannot_vouch_for_an_unrelated_skill_and_the_whole_change_rolls_back(client, aarav, meera):
    application_id = _accepted(client, aarav, meera)
    bad = {**COMPLETION, "skills": ["pytorch", "kubernetes"]}
    r = _complete(client, meera, application_id, bad)
    assert r.status_code == 422 and "kubernetes" in r.json()["detail"]
    assert _cypher("MATCH ()-[a:APPLIED_TO {id: $id}]->() RETURN a.status AS s", id=application_id) == [{"s": "accepted"}]
    assert _cypher("MATCH (:Student {user_id: 'u-aarav'})-[h:HAS_SKILL]->() RETURN count(h) AS n") == [{"n": 0}]
    assert _records(client, aarav) == []


def test_74_a_skill_the_student_already_lists_can_be_vouched_for(client, aarav, meera):
    application_id = _accepted(client, aarav, meera)
    _cypher(
        "MATCH (s:Student {user_id: 'u-aarav'}) MERGE (c:Concept {name: 'git'}) "
        "MERGE (s)-[h:HAS_SKILL]->(c) SET h.claimed = true, h.trust_level = 0, h.evidence_ids = [], h.endorsed_by = []"
    )
    r = _complete(client, meera, application_id, {**COMPLETION, "skills": ["git", "pytorch"]})
    assert r.status_code == 200, r.text
    levels = {k["concept"]: k["trust_level"] for k in client.get("/api/v1/me/profile", headers=aarav).json()["skills"]}
    assert levels == {"git": 2, "pytorch": 2}


def test_74_scope_and_validation(client, aarav, meera, arjun, diya):
    application_id = _accepted(client, aarav, meera)
    assert _complete(client, arjun, application_id).status_code == 404  # not the opening's owner
    assert client.patch(URL.format(application_id), json={"status": "completed", "completion": COMPLETION}, headers=aarav).status_code == 403
    too_short = {**COMPLETION, "summary": "done"}
    assert _complete(client, meera, application_id, too_short).status_code == 422
    assert _complete(client, meera, application_id, {**COMPLETION, "skills": []}).status_code == 422
    assert _complete(client, meera, application_id, {**COMPLETION, "output_type": "excellent"}).status_code == 422  # no grades
    assert _complete(client, meera, application_id).status_code == 200
    (record,) = _records(client, aarav)
    assert client.get(f"/api/v1/certificates/{record['id']}", headers=diya).status_code == 404  # another student
    assert client.get(f"/api/v1/certificates/{record['id']}/file", headers=aarav).status_code == 404  # no file exists
    assert _complete(client, meera, application_id).status_code == 409  # completed is terminal: no second record


def test_74_the_record_counts_as_an_achievement_but_its_text_never_leaves(client, aarav, meera, suresh, kavya):
    application_id = _accepted(client, aarav, meera)
    assert _complete(client, meera, application_id).status_code == 200
    board = client.get("/api/v1/dept/dashboard", headers=suresh).json()
    assert {"type": "project", "count": 1} in [
        {"type": a["type"], "count": a["count"]} for a in board["achievements_by_type"]
    ]
    for who in (suresh, kavya):
        xlsx = client.get("/api/v1/evidence/achievements.xlsx", headers=who)
        assert xlsx.status_code == 200
        cells = " ".join(
            str(c.value) for ws in openpyxl.load_workbook(io.BytesIO(xlsx.content)).worksheets
            for row in ws.iter_rows() for c in row if c.value is not None
        )
        assert COMPLETION["summary"] not in cells  # free text stays with the student and the people who know them
