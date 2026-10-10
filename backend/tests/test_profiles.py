"""Profiles and matching v2 (plan: profiles-and-matching-plan.md): TEST-60 to TEST-73.

Runs on the stand-in graph of `test_tracking.world` (Aarav year 3, Diya, Meera, Arjun, Suresh, Kavya). Anything that
needs P1's embedding model (saving skills, creating openings, the fit) runs in the Docker image, where it is installed.
"""
import pytest

from app.core.config import get_settings
from app.services import resume as resume_service
from tests.test_tracking import (
    cypher,
    world,  # noqa: F401  (autouse fixture: the base graph)
)

pytest.importorskip("sentence_transformers")  # the embedding model: present in the image, absent in a bare venv

TEXT_PDF = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 200]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
    b"4 0 obj<</Length 70>>stream\nBT /F1 12 Tf 20 100 Td (Skills: python, docker and pytorch) Tj ET\nendstream endobj\n"
    b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n"
)


def mm(client, headers, **body):
    return client.patch("/api/v1/me/profile", headers=headers, json=body)


def full(client, headers):
    r = client.get("/api/v1/me/profile", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def new_opening(client, headers, **extra):
    body = {"title": "Edge vision study", "description": "A study.", "required_skills": ["python", "pytorch"], **extra}
    r = client.post("/api/v1/openings", headers=headers, json=body)
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture(autouse=True)
def _clean(client, world):  # noqa: F811
    resume_service.reset_limiter()
    cypher("MATCH (o:Opening) WHERE o.id <> 'op-edge-ai' DETACH DELETE o")
    cypher("MATCH (s:Student {user_id: 'u-aarav'}) SET s.year = 3, s.enrolled_on = '2024-08-01'")
    cypher("MATCH (:Student {user_id: 'u-aarav'})-[:HAS_RECORD]->(r:AcademicRecord) DETACH DELETE r")
    cypher("MATCH (s:Student {user_id: 'u-aarav'}) REMOVE s.self_reported_cgpa")
    cypher("MATCH (f:Faculty) SET f.accepting_guides = true")
    cypher("MATCH (n:Resume) DETACH DELETE n")
    cypher("MATCH (n:Project) DETACH DELETE n")


# ---- TEST-60 profile fields -------------------------------------------------------------------------------------------


def test_60_profile_fields_save_and_partial_updates(client, aarav):
    r = mm(client, aarav, programme="btech", year=4, headline="Builds small vision models", self_reported_cgpa=8.4,
           availability_hours=10, available_from="2026-11-01", preferences=["Research", "tooling"],
           links=["https://github.com/aarav", "https://github.com/aarav"], open_to_opportunities=True,
           projects=[{"title": "Leaf classifier", "description": "CNN", "skills": ["Python"]}])
    assert r.status_code == 200, r.text
    p = full(client, aarav)
    assert (p["programme"], p["year"], p["headline"], p["availability_hours"]) == ("btech", 4, "Builds small vision models", 10)
    assert p["links"] == ["https://github.com/aarav"]  # de-duplicated
    assert p["preferences"] == ["research", "tooling"] and p["available_from"] == "2026-11-01"
    assert p["projects"][0]["title"] == "Leaf classifier" and p["projects"][0]["skills"] == ["python"]
    # a partial update leaves every other field alone; a sent null clears only that field
    mm(client, aarav, headline=None)
    q = full(client, aarav)
    assert q["headline"] is None and q["programme"] == "btech" and q["availability_hours"] == 10
    # projects are a full-list replacement
    mm(client, aarav, projects=[])
    assert full(client, aarav)["projects"] == []


@pytest.mark.parametrize("body", [
    {"links": ["http://insecure.example"]},
    {"links": ["javascript:alert(1)"]},
    {"links": [f"https://x.example/{i}" for i in range(6)]},
    {"self_reported_cgpa": 11},
    {"year": 6},
    {"availability_hours": 90},
    {"dept_code": "ECE"},  # the department is the institution's to change, not the student's
    {"projects": [{"title": "p", "link": "ftp://nope"}]},
    {"skill_levels": {"cobol": "advanced"}},  # not a skill the student has
])
def test_60_invalid_profile_input_is_refused(client, aarav, body):
    assert mm(client, aarav, **body).status_code == 422


def test_60_roles(client, meera, suresh):
    assert client.get("/api/v1/me/profile", headers=meera).status_code == 403
    assert mm(client, suresh, headline="x").status_code == 403
    assert client.get("/api/v1/me/profile").status_code == 401


# ---- TEST-61 skills ---------------------------------------------------------------------------------------------------


def test_61_skill_typeahead_and_levels(client, aarav):
    assert mm(client, aarav, claimed_skills=["Python", "PyTorch"]).status_code == 200
    names = [c["name"] for c in client.get("/api/v1/concepts", headers=aarav, params={"q": "pyt"}).json()]
    assert "python" in names and "pytorch" in names
    assert client.get("/api/v1/concepts", headers=aarav, params={"q": "x" * 41}).status_code == 422
    assert mm(client, aarav, skill_levels={"Python": "advanced"}).status_code == 200
    skills = {s["concept"]: s for s in full(client, aarav)["skills"]}
    assert skills["python"]["level"] == "advanced"
    assert skills["python"]["trust_level"] == 0 and skills["python"]["claimed"] is True  # a level never raises trust
    assert mm(client, aarav, skill_levels={"python": "expert"}).status_code == 422
    assert mm(client, aarav, claimed_skills=[f"skill {i}" for i in range(31)]).status_code == 422


# ---- TEST-62 trust labels ---------------------------------------------------------------------------------------------


def test_62_cgpa_is_labelled_and_the_record_wins(client, aarav):
    assert full(client, aarav)["cgpa"]["source"] == "unknown"
    mm(client, aarav, self_reported_cgpa=9.1)
    cg = full(client, aarav)["cgpa"]
    assert (cg["source"], cg["effective"], cg["record"], cg["self_reported"]) == ("self_reported", 9.1, None, 9.1)
    cypher("MATCH (s:Student {user_id: 'u-aarav'}) CREATE (s)-[:HAS_RECORD]->(:AcademicRecord {id: 'ar-1', "
           "term_id: '2026-ODD', cgpa: 7.4, attendance_pct: 90.0, backlogs: 0})")
    cg = full(client, aarav)["cgpa"]
    assert (cg["source"], cg["effective"], cg["record"], cg["self_reported"]) == ("record", 7.4, 7.4, 9.1)


# ---- TEST-63 completeness ---------------------------------------------------------------------------------------------


def test_63_completeness_counts_and_next_action(client, aarav):
    start = full(client, aarav)["completeness"]
    assert start["percent"] < 50 and start["next_action"]
    mm(client, aarav, programme="btech", headline="h", bio="b", availability_hours=6, interests=["vision"],
       claimed_skills=["python", "pytorch", "docker"], projects=[{"title": "p"}])
    mid = full(client, aarav)["completeness"]
    done = {i["key"]: i["done"] for i in mid["items"]}
    assert done["basics"] and done["skills"] and done["project"] and done["availability"] and done["interests"]
    assert not done["resume"] and not done["certificate"]
    assert mid["percent"] == round(100 * 5 / 7) and mid["next_action"] == "Upload a certificate to verify one skill"


# ---- TEST-64 / 65 eligibility and capacity ----------------------------------------------------------------------------


def checks(client, headers, opening_id):
    r = client.get(f"/api/v1/openings/{opening_id}/eligibility", headers=headers)
    assert r.status_code == 200, r.text
    return r.json(), {c["rule"]: c for c in r.json()["checks"]}


def test_64_advisory_warns_but_strict_refuses(client, aarav, meera):
    advisory = new_opening(client, meera, eligible_years=[4], eligibility_mode="advisory")
    strict = new_opening(client, meera, title="Strict year study", eligible_years=[4], eligibility_mode="strict")
    for opening, mode in ((advisory, "advisory"), (strict, "strict")):
        result, by_rule = checks(client, aarav, opening["id"])
        assert result["mode"] == mode and result["eligible"] is False
        assert by_rule["year"]["status"] == "failed" and "you are in year 3" in by_rule["year"]["detail"]
    assert client.post(f"/api/v1/openings/{advisory['id']}/applications", headers=aarav).status_code == 201
    r = client.post(f"/api/v1/openings/{strict['id']}/applications", headers=aarav)
    assert r.status_code == 409 and r.json()["code"] == "NOT_ELIGIBLE"
    assert [e["field"] for e in r.json()["errors"]] == ["year"]
    # applying twice still reports ALREADY_APPLIED, not eligibility
    assert client.post(f"/api/v1/openings/{advisory['id']}/applications", headers=aarav).json()["code"] == "ALREADY_APPLIED"


def test_64_min_cgpa_unknown_does_not_fail(client, aarav, meera):
    op = new_opening(client, meera, min_cgpa=7.5, eligibility_mode="strict")
    result, by_rule = checks(client, aarav, op["id"])
    assert by_rule["min_cgpa"]["status"] == "unknown" and result["eligible"] is True
    assert client.post(f"/api/v1/openings/{op['id']}/applications", headers=aarav).status_code == 201

    mm(client, aarav, self_reported_cgpa=7.0)
    low = new_opening(client, meera, title="CGPA gated study", min_cgpa=7.5, eligibility_mode="strict")
    _, by_rule = checks(client, aarav, low["id"])
    assert by_rule["min_cgpa"]["status"] == "failed" and "self-reported" in by_rule["min_cgpa"]["detail"]
    refused = client.post(f"/api/v1/openings/{low['id']}/applications", headers=aarav)
    assert refused.status_code == 409 and refused.json()["errors"][0]["field"] == "min_cgpa"
    mm(client, aarav, self_reported_cgpa=8.0)
    assert client.post(f"/api/v1/openings/{low['id']}/applications", headers=aarav).status_code == 201


def test_64_availability_rules_block_in_any_mode(client, aarav, meera):
    past = new_opening(client, meera, deadline="2026-09-01", eligibility_mode="advisory")
    assert checks(client, aarav, past["id"])[1]["deadline"]["status"] == "failed"
    r = client.post(f"/api/v1/openings/{past['id']}/applications", headers=aarav)
    assert r.status_code == 409 and r.json()["code"] == "OPENING_CLOSED"
    cypher("MATCH (f:Faculty {user_id: 'u-meera'}) SET f.accepting_guides = false")
    full_house = new_opening(client, meera, title="Not taking students study")
    assert checks(client, aarav, full_house["id"])[1]["guide_capacity"]["status"] == "failed"
    assert client.post(f"/api/v1/openings/{full_house['id']}/applications", headers=aarav).status_code == 409


def test_65_last_position_closes_the_opening_and_the_next_accept_is_refused(client, aarav, diya, meera):
    op = new_opening(client, meera, positions=1)
    a = client.post(f"/api/v1/openings/{op['id']}/applications", headers=aarav).json()
    b = client.post(f"/api/v1/openings/{op['id']}/applications", headers=diya).json()
    for app_id in (a["id"], b["id"]):
        assert client.patch(f"/api/v1/applications/{app_id}", headers=meera, json={"status": "shortlisted"}).status_code == 200
    assert client.patch(f"/api/v1/applications/{a['id']}", headers=meera, json={"status": "accepted"}).status_code == 200
    row = cypher("MATCH (o:Opening {id: $id}) RETURN o.status AS s", id=op["id"])[0]
    assert row["s"] == "closed"
    event = cypher("MATCH (e:StatusEvent {entity_type: 'opening', entity_id: $id}) RETURN e.to_status AS t, e.note AS n",
                   id=op["id"])
    assert event == [{"t": "closed", "n": "positions filled"}]
    again = client.patch(f"/api/v1/applications/{b['id']}", headers=meera, json={"status": "accepted"})
    assert again.status_code == 409 and again.json()["code"] == "OPENING_CLOSED"
    assert client.patch(f"/api/v1/applications/{b['id']}", headers=meera, json={"status": "rejected"}).status_code == 200


def test_opening_patch_is_owner_only_and_replaces_skills(client, meera, arjun, aarav):
    op = new_opening(client, meera)
    url = f"/api/v1/openings/{op['id']}"
    assert client.patch(url, headers=arjun, json={"title": "Stolen title"}).status_code == 404
    assert client.patch(url, headers=aarav, json={"title": "Student edit"}).status_code == 403
    assert client.patch(url, headers=meera, json={}).status_code == 422
    r = client.patch(url, headers=meera, json={"required_skills": ["docker"], "positions": 3, "eligible_years": [4, 3]})
    assert r.status_code == 200
    assert r.json()["required_skills"] == ["docker"] and r.json()["positions"] == 3 and r.json()["eligible_years"] == [3, 4]
    closed = client.patch(url, headers=meera, json={"status": "closed"})
    assert closed.json()["status"] == "closed"
    assert cypher("MATCH (e:StatusEvent {entity_type: 'opening', entity_id: $id}) RETURN count(e) AS n", id=op["id"])[0]["n"] == 1


# ---- TEST-66 / 67 / 68 recommendations, the score, fairness -----------------------------------------------------------


def test_66_groups_reasons_and_cold_start(client, aarav, meera):
    mm(client, aarav, claimed_skills=["python"])
    strict = new_opening(client, meera, title="Year four only", eligible_years=[4], eligibility_mode="strict")
    advisory = new_opening(client, meera, title="Year four advisory", eligible_years=[4])
    plain = new_opening(client, meera, title="Plain open study")
    r = client.get("/api/v1/me/recommendations", headers=aarav).json()
    assert r["cold_start"] is True  # one skill: ranked by interests, labelled so
    labels = {g["key"]: g["label"] for g in r["groups"]}
    assert labels["worth"] == "Based on your interests"
    by_group = {g["key"]: [i["id"] for i in g["items"]] for g in r["groups"]}
    assert strict["id"] in by_group["ineligible"] and advisory["id"] not in by_group["ineligible"]
    assert plain["id"] in by_group["worth"] and advisory["id"] in by_group["worth"]
    warned = next(i for g in r["groups"] for i in g["items"] if i["id"] == advisory["id"])
    assert warned["eligibility"]["eligible"] is False and warned["eligibility"]["mode"] == "advisory"
    assert warned["reasons"] and len(warned["reasons"]) <= 3
    mm(client, aarav, claimed_skills=["python", "pytorch", "docker"])
    assert client.get("/api/v1/me/recommendations", headers=aarav).json()["cold_start"] is False


def test_67_cgpa_never_changes_the_fit_score(client, aarav, meera):
    op = new_opening(client, meera, min_cgpa=6.0)
    mm(client, aarav, claimed_skills=["python"], self_reported_cgpa=6.0)
    before = client.get(f"/api/v1/openings/{op['id']}/fit", headers=aarav).json()
    mm(client, aarav, self_reported_cgpa=9.9)
    client.patch(f"/api/v1/openings/{op['id']}", headers=meera, json={"min_cgpa": 9.5, "eligibility_mode": "strict"})
    after = client.get(f"/api/v1/openings/{op['id']}/fit", headers=aarav).json()
    assert before["score"] == after["score"] and before["components"] == after["components"]
    assert set(before["components"]) == {"semantic", "skill", "concept"}  # no marks in the score
    parts = after["components"]
    assert round(parts["semantic"] + parts["skill"] + parts["concept"], 1) == after["score"]  # still sums exactly


def test_68_a_students_name_does_not_change_the_ranking(client, aarav, meera):
    new_opening(client, meera, title="Ranking one")
    new_opening(client, meera, title="Ranking two", required_skills=["docker", "react"])
    mm(client, aarav, claimed_skills=["python", "react"])

    def ranking():
        items = [i for g in client.get("/api/v1/me/recommendations", headers=aarav).json()["groups"] for i in g["items"]]
        return [(i["title"], i["my_fit"]["score"]) for i in items]

    first = ranking()
    cypher("MATCH (s:Student {user_id: 'u-aarav'}) SET s.name = 'Zzyzx Qwerty'")
    assert ranking() == first


# ---- TEST-69 / 70 resume ----------------------------------------------------------------------------------------------


def upload_resume(client, headers, data=TEXT_PDF, name="cv.pdf"):
    return client.post("/api/v1/me/resume", headers=headers, files={"file": (name, data)})


@pytest.fixture
def uploads(monkeypatch, tmp_path):
    monkeypatch.setattr(get_settings(), "upload_dir", str(tmp_path))
    return tmp_path


def test_69_resume_intake_rules(client, aarav, uploads, monkeypatch):
    assert upload_resume(client, aarav, b"MZ\x90\x00not a pdf").status_code == 415
    assert upload_resume(client, aarav, b"\x89PNG\r\n\x1a\n" + b"0" * 40).status_code == 415
    too_many = b"%PDF-1.4\n" + b"<< /Type /Page >>\n" * 5
    r = upload_resume(client, aarav, too_many)
    assert r.status_code == 422 and r.json()["code"] == "VALIDATION_FAILED"
    ok = upload_resume(client, aarav)
    assert ok.status_code == 201 and ok.json()["status"] == "current" and ok.json()["pages"] >= 1
    assert "file_path" not in ok.text and "sha256" not in ok.text
    assert not [p for p in (uploads / "resumes").iterdir() if p.name.startswith(".tmp-")]
    monkeypatch.setattr(get_settings(), "max_resume_mb", 0)
    assert upload_resume(client, aarav).status_code == 413
    assert client.post("/api/v1/me/resume", headers=aarav).status_code == 422


def test_69_new_upload_supersedes_and_never_deletes(client, aarav, uploads):
    first = upload_resume(client, aarav).json()["id"]
    second = upload_resume(client, aarav).json()["id"]
    assert client.get("/api/v1/me/resume", headers=aarav).json()["id"] == second
    states = {r["id"]: r["s"] for r in cypher("MATCH (r:Resume) RETURN r.id AS id, r.status AS s")}
    assert states == {first: "superseded", second: "current"}
    assert len(list((uploads / "resumes").glob("*.pdf"))) == 2  # the old file is kept


def test_69_resume_scope_matrix(client, aarav, diya, meera, arjun, suresh, kavya, uploads):
    upload_resume(client, aarav)
    url = "/api/v1/students/u-aarav/resume/file"
    got = client.get(url, headers=aarav)
    assert got.status_code == 200 and got.content.startswith(b"%PDF-")
    assert got.headers["content-disposition"] == "inline" and got.headers["x-content-type-options"] == "nosniff"
    assert client.get(url, headers=meera).status_code == 200  # assigned mentor
    assert client.get(url, headers=suresh).status_code == 200  # the HOD
    assert client.get(url, headers=arjun).status_code == 404  # not his student and Aarav has not applied to him
    assert client.get(url, headers=diya).status_code == 404  # another student
    assert client.get(url, headers=kavya).status_code == 403  # IQAC never
    assert client.get(url).status_code == 401
    # applying to Arjun's opening is what lets Arjun see it
    op = new_opening(client, arjun)
    assert client.post(f"/api/v1/openings/{op['id']}/applications", headers=aarav).status_code == 201
    assert client.get(url, headers=arjun).status_code == 200
    assert client.get("/api/v1/students/u-diya/resume/file", headers=diya).status_code == 404  # none uploaded


def test_70_suggestions_need_confirmation_and_create_claimed_skills_only(client, aarav, uploads):
    mm(client, aarav, claimed_skills=["python"])
    for name in ("docker", "pytorch"):  # concepts the resume text can match
        cypher("MERGE (:Concept {name: $n})", n=name)
    assert client.post("/api/v1/me/resume/suggestions", headers=aarav).status_code == 404  # no resume yet
    upload_resume(client, aarav)
    s = client.post("/api/v1/me/resume/suggestions", headers=aarav).json()
    found = {x["concept"]: x["already_claimed"] for x in s["skills"]}
    assert found["python"] is True and found["docker"] is False and found["pytorch"] is False
    assert "Nothing is added" in s["note"]
    assert {x["concept"] for x in full(client, aarav)["skills"]} == {"python"}  # suggesting changed nothing
    applied = client.post("/api/v1/me/resume/suggestions/apply", headers=aarav, json={"skills": ["docker"]})
    assert applied.status_code == 200
    skills = {x["concept"]: x for x in applied.json()["skills"]}
    assert skills["docker"]["trust_level"] == 0 and skills["docker"]["claimed"] is True and "python" in skills
    bad = client.post("/api/v1/me/resume/suggestions/apply", headers=aarav, json={"skills": ["not a concept"]})
    assert bad.status_code == 422
    assert client.post("/api/v1/me/resume/suggestions/apply", headers=aarav, json={"skills": []}).status_code == 422


def test_70_image_only_pdf_reports_nothing_to_suggest(client, aarav, uploads):
    from io import BytesIO

    from PIL import Image

    buffer = BytesIO()
    Image.new("RGB", (80, 60), "white").save(buffer, format="PDF")
    assert upload_resume(client, aarav, buffer.getvalue()).status_code == 201
    s = client.post("/api/v1/me/resume/suggestions", headers=aarav).json()
    assert s["skills"] == [] and "no readable text" in s["note"]


def test_70_resume_text_is_never_logged(client, aarav, uploads, caplog):
    caplog.set_level("DEBUG")
    cypher("MERGE (:Concept {name: 'docker'})")
    upload_resume(client, aarav)
    client.post("/api/v1/me/resume/suggestions", headers=aarav)
    assert "Skills: python, docker" not in caplog.text and "python, docker and pytorch" not in caplog.text


# ---- TEST-71 / 72 / 73 faculty profile, directory, mentor suggestion ---------------------------------------------------


def test_71_faculty_profile_replaces_lists(client, meera, suresh, aarav):
    body = {
        "research_areas": [{"concept": "Deep Learning", "primary": True}, {"concept": "vision"}],
        "expertise": ["Python", "python", "robotics"],
        "courses": [{"code": "cs401", "title": "Deep Learning", "term_id": "2026-ODD", "topics": ["Deep Learning"]}],
        "qualifications": [{"degree": "PhD", "institution": "IIT", "year": 2014}],
        "max_guided_students": 4, "accepting_guides": True, "office_hours": "Tue 3 pm", "publications": ["A paper"],
        "links": ["https://scholar.example/meera"],
    }
    r = client.patch("/api/v1/me/faculty-profile", headers=meera, json=body)
    assert r.status_code == 200, r.text
    p = r.json()
    assert [a["concept"] for a in p["research_areas"]] == ["deep learning", "vision"] and p["research_areas"][0]["primary"]
    assert p["expertise"] == ["python", "robotics"] and p["courses"][0]["code"] == "CS401"
    assert p["max_guided_students"] == 4 and p["guided_students"] == 0 and p["qualifications"][0]["degree"] == "PhD"
    again = client.patch("/api/v1/me/faculty-profile", headers=meera, json={"expertise": ["docker"]}).json()
    assert again["expertise"] == ["docker"] and len(again["research_areas"]) == 2  # other lists untouched
    cleared = client.patch("/api/v1/me/faculty-profile", headers=meera, json={"research_areas": []}).json()
    assert cleared["research_areas"] == []
    bad = [{"research_areas": [{"concept": "a", "primary": True}, {"concept": "b", "primary": True}]},
           {"courses": [{"code": "X1", "title": "a"}, {"code": "x1", "title": "b"}]},
           {"links": ["http://nope.example"]}, {}, {"max_guided_students": 99}]
    assert [client.patch("/api/v1/me/faculty-profile", headers=meera, json=b).status_code for b in bad] == [422] * 5
    assert client.patch("/api/v1/me/faculty-profile", headers=suresh, json={"expertise": ["x"]}).status_code == 403
    assert client.get("/api/v1/me/faculty-profile", headers=aarav).status_code == 403


def test_71_public_faculty_page_has_facts_and_no_ratings(client, aarav, meera):
    client.patch("/api/v1/me/faculty-profile", headers=meera, json={"expertise": ["python"]})
    new_opening(client, meera)
    r = client.get("/api/v1/faculty/u-meera", headers=aarav)
    assert r.status_code == 200
    body = r.json()
    assert body["profile"]["name"] == "Meera" and {o["title"] for o in body["open_openings"]} >= {"Edge vision study"}
    assert body["track_record"]["openings_posted"] >= 1
    assert "rating" not in r.text and "password" not in r.text
    assert client.get("/api/v1/faculty/u-aarav", headers=aarav).status_code == 404  # a student is not faculty
    assert client.get("/api/v1/faculty/u-meera").status_code == 401


def test_72_directory_orders_by_shared_topics_and_returns_no_score(client, aarav, meera, arjun):
    mm(client, aarav, claimed_skills=["python"], interests=["deep learning"])
    client.patch("/api/v1/me/faculty-profile", headers=meera, json={"research_areas": [{"concept": "deep learning"}],
                                                                    "expertise": ["python"]})
    client.patch("/api/v1/me/faculty-profile", headers=arjun, json={"research_areas": [{"concept": "databases"}],
                                                                    "accepting_guides": False})
    cards = client.get("/api/v1/faculty", headers=aarav).json()
    assert [c["user_id"] for c in cards][:2] == ["u-meera", "u-arjun"]
    assert set(cards[0]["shared_topics"]) >= {"deep learning", "python"} and cards[1]["shared_topics"] == []
    assert all("score" not in c and "fit" not in c and "rank" not in c for c in cards)
    only = client.get("/api/v1/faculty", headers=aarav, params={"accepting": "true"}).json()
    assert "u-arjun" not in [c["user_id"] for c in only]
    found = client.get("/api/v1/faculty", headers=aarav, params={"query": "databases"}).json()
    assert [c["user_id"] for c in found] == ["u-arjun"]
    assert client.get("/api/v1/faculty", headers=meera).status_code == 403


def test_73_mentor_suggestion_respects_the_load_limit(client, suresh, monkeypatch):
    cypher("MATCH (s:Student {user_id: 'u-diya'}) OPTIONAL MATCH ()-[m:MENTORS]->(s) DELETE m")
    cypher("MERGE (c:Concept {name: 'deep learning'}) WITH c MATCH (f:Faculty {user_id: 'u-meera'}) "
           "MERGE (f)-[:RESEARCHES {primary: true}]->(c)")
    cypher("MATCH (s:Student {user_id: 'u-diya'}) SET s.interests = ['deep learning']")
    open_view = client.get("/api/v1/dept/allotment", headers=suresh).json()
    diya = next(u for u in open_view["unallotted"] if u["user_id"] == "u-diya")
    assert diya["suggested_mentor"]["mentor_id"] == "u-meera" and "deep learning" in diya["suggested_mentor"]["reason"]
    monkeypatch.setattr(get_settings(), "mentor_load_warn", 1)  # Meera already mentors Aarav: at the limit
    capped = client.get("/api/v1/dept/allotment", headers=suresh).json()
    diya = next(u for u in capped["unallotted"] if u["user_id"] == "u-diya")
    assert diya["suggested_mentor"]["mentor_id"] != "u-meera"
