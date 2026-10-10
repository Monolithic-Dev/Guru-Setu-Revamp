"""Certificates: upload intake, JOB-01, manual entry, review, file stream, JOB-02 (TEST-06, 12, 13, 14 and the
certificate rows of TEST-05, TEST-34, TEST-35).

P1's extraction, verification and trust code is replaced by a scripted pipeline (`set_pipeline_for_tests`), so these
tests check what P2 owns: routing, scope, transactions, notifications and privacy. The uploads folder is a tmp dir.
"""
import os
from datetime import timedelta
from types import SimpleNamespace

import pytest

from app.core.clock import utc_now
from app.core.config import get_settings
from app.services import certificates
from tests.test_tracking import cypher, reset_graph

PNG = b"\x89PNG\r\n\x1a\n"


def png() -> bytes:
    return PNG + os.urandom(64)  # unique bytes per upload


class Script:
    """What the fake extract / verify return, and what apply_certified was called with."""

    def __init__(self) -> None:
        self.status = "certified"
        self.reasons: list[str] = []
        self.duplicate_of: str | None = None
        self.extract_raises = False
        self.applied: list[tuple] = []


@pytest.fixture
def script(monkeypatch, tmp_path):
    cfg = get_settings()
    monkeypatch.setattr(cfg, "upload_dir", str(tmp_path))
    monkeypatch.setattr(cfg, "upload_rate_limit_per_hour", 50)
    certificates._limiter = None
    s = Script()

    def extract(data, media_type):
        if s.extract_raises:
            raise RuntimeError("provider down")
        return SimpleNamespace(
            source="llm", holder_name="Aarav", title="Python Basics", issuer="Coursera", issue_date="2026-08-10",
            level="online", type="course", certificate_id="C-1", verify_url=None, contains_instructions=False,
        )

    def verify(student, data, media_type, extraction, tx):
        return SimpleNamespace(
            status=s.status, confidence=0.91 if s.status == "certified" else 0.55, reasons=s.reasons,
            duplicate_of=s.duplicate_of, sha256="a" * 64, phash=None, skills=["python"],
        )

    def apply_certified(tx, student_id, evidence_id, skills):
        s.applied.append((student_id, evidence_id, tuple(skills)))

    certificates.set_pipeline_for_tests(extract, verify, apply_certified)
    yield s
    certificates.clear_pipeline_for_tests()
    certificates._limiter = None


@pytest.fixture(autouse=True)
def world(fresh_seed):
    reset_graph()
    for label in ("StatusEvent", "Notification", "Issuer"):
        cypher(f"MATCH (n:{label}) DETACH DELETE n")
    cypher("MATCH (f:Faculty {user_id: 'u-meera'}) SET f.designation = 'Professor'")
    cypher("CREATE (:Issuer {name: 'Coursera', aliases: ['coursera inc']})")
    cypher("MATCH (s:Student {user_id: 'u-aarav'}) SET s.enrolled_on = '2024-08-01'")


def upload(client, headers, data: bytes | None = None, name: str = "c.png"):
    return client.post("/api/v1/certificates", headers=headers, files={"file": (name, data or png())})


def events(evidence_id: str) -> list[tuple]:
    rows = cypher(
        "MATCH (e:StatusEvent {entity_id: $id}) RETURN e.from_status AS f, e.to_status AS t ORDER BY e.at",
        id=evidence_id,
    )
    return [(r["f"], r["t"]) for r in rows]


def notes(user_id: str) -> list[dict]:
    return cypher(
        "MATCH (n:Notification)-[:NOTIFIES]->(:User {user_id: $u}) RETURN n.type AS type, n.title AS title, "
        "n.body AS body ORDER BY n.created_at",
        u=user_id,
    )


# ---- upload and JOB-01 ------------------------------------------------------------------------------------------------


def test_06_upload_then_certified(client, script, aarav):
    r = upload(client, aarav)
    assert r.status_code == 202
    body = r.json()
    assert body["status"] == "processing" and body["media_type"] == "image/png"
    for private in ("file_path", "duplicate_of", "sha256", "owner_id"):
        assert private not in r.text
    final = client.get(f"/api/v1/certificates/{body['id']}", headers=aarav).json()  # the job ran after the response
    assert final["status"] == "certified" and final["confidence"] == 0.91 and final["source"] == "llm"
    assert final["title"] == "Python Basics" and final["skills"] == ["python"]
    assert script.applied == [("u-aarav", body["id"], ("python",))]
    assert events(body["id"]) == [(None, "processing"), ("processing", "certified")]
    assert [n["type"] for n in notes("u-aarav")] == ["certificate_result"]
    assert notes("u-aarav")[0]["title"] == "Certificate 'Python Basics' is certified"
    assert [c["id"] for c in client.get("/api/v1/me/certificates", headers=aarav).json()] == [body["id"]]
    assert len(list(os.scandir(get_settings().upload_dir))) == 1  # stored once, no temp file left behind


def test_12_needs_review_routes_to_assigned_mentor(client, script, aarav, meera):
    script.status, script.reasons = "needs_review", ["name_mismatch"]
    cert = upload(client, aarav).json()
    assert client.get(f"/api/v1/certificates/{cert['id']}", headers=aarav).json()["reasons"] == ["name_mismatch"]
    assert script.applied == []  # nothing is proven until a human approves
    assert [n["type"] for n in notes("u-meera")] == ["review_needed"]
    assert notes("u-meera")[0]["title"] == "A certificate from Aarav needs review"
    assert [n["type"] for n in notes("u-aarav")] == ["certificate_result"]


def test_duplicate_is_recorded_and_visible_to_reviewers_only(client, script, aarav, meera, suresh):
    first = upload(client, aarav).json()["id"]
    script.status, script.reasons, script.duplicate_of = "needs_review", ["duplicate_image"], first
    second = upload(client, aarav).json()["id"]
    queue = client.get("/api/v1/reviews/certificates", headers=meera).json()
    assert [i["certificate"]["id"] for i in queue] == [second]
    assert queue[0]["duplicate_of"] == first and queue[0]["student"]["name"] == "Aarav"
    assert [i["certificate"]["id"] for i in client.get("/api/v1/reviews/certificates", headers=suresh).json()] == [second]
    assert "duplicate_of" not in client.get(f"/api/v1/certificates/{second}", headers=aarav).text


def test_job_failure_marks_failed_and_manual_entry_recovers(client, script, aarav, meera):
    script.extract_raises = True
    cert = upload(client, aarav).json()
    failed = client.get(f"/api/v1/certificates/{cert['id']}", headers=aarav).json()
    assert failed["status"] == "failed" and failed["reasons"] == ["extraction_failed"]
    assert events(cert["id"])[-1] == ("processing", "failed")

    manual = {"holder_name": "Aarav", "title": "Python Basics", "issuer": "Coursera", "issue_date": "2026-08-10",
              "level": "online", "type": "course", "skills": ["Python ", "PYTHON", "Pandas"]}
    r = client.put(f"/api/v1/certificates/{cert['id']}/manual", headers=aarav, json=manual)
    assert r.status_code == 200
    done = r.json()
    assert done["status"] == "needs_review" and done["source"] == "manual" and done["reasons"] == ["manual_entry"]
    assert done["confidence"] == 0.5  # name, issuer and date all fine (0.40+0.25+0.20+0.15) but capped at 0.50
    assert done["skills"] == ["python", "pandas"]
    assert events(cert["id"])[-1] == ("failed", "needs_review")
    assert "review_needed" in [n["type"] for n in notes("u-meera")]
    # a second manual entry is refused: it is no longer `failed`
    assert client.put(f"/api/v1/certificates/{cert['id']}/manual", headers=aarav, json=manual).status_code == 409


def test_manual_entry_low_confidence_and_scope(client, script, aarav, diya):
    script.extract_raises = True
    cert = upload(client, aarav).json()["id"]
    bad = {"holder_name": "Someone Else", "title": "T", "issuer": "Unknown Org", "issue_date": "2999-01-01",
           "level": "other", "type": "other", "skills": ["x"]}
    assert client.put(f"/api/v1/certificates/{cert}/manual", headers=diya, json=bad).status_code == 404
    r = client.put(f"/api/v1/certificates/{cert}/manual", headers=aarav, json=bad)
    assert r.json()["confidence"] == 0.15  # only "complete" holds
    ok = {**bad, "holder_name": "Aarav"}
    assert client.put(f"/api/v1/certificates/{cert}/manual", headers=aarav, json=ok).status_code == 409
    assert client.put(f"/api/v1/certificates/{cert}/manual", headers=aarav, json={"title": "x"}).status_code == 422


# ---- intake rules -----------------------------------------------------------------------------------------------------


def test_intake_rejects_bad_files(client, script, aarav, monkeypatch):
    assert upload(client, aarav, b"just some text, not an image").status_code == 415
    assert upload(client, aarav, b"MZ\x90\x00" + b"0" * 50).status_code == 415  # an .exe renamed to .png
    pages = b"%PDF-1.4\n" + b"<< /Type /Page >>\n" * 6
    r = upload(client, aarav, pages, "x.pdf")
    assert r.status_code == 422 and r.json()["code"] == "VALIDATION_FAILED"
    assert upload(client, aarav, b"%PDF-1.4\n" + b"<< /Type /Page >>\n" * 5, "x.pdf").status_code == 202
    monkeypatch.setattr(get_settings(), "max_upload_mb", 0)
    big = upload(client, aarav)
    assert big.status_code == 413 and big.json()["code"] == "FILE_TOO_LARGE"
    leftovers = [e.name for e in os.scandir(get_settings().upload_dir) if e.name.startswith(".tmp-")]
    assert leftovers == []  # rejected uploads leave nothing behind
    assert client.post("/api/v1/certificates", headers=aarav).status_code == 422  # no file at all


def test_intake_roles_and_rate_limit(client, script, aarav, meera, monkeypatch):
    assert upload(client, meera).status_code == 403
    assert client.post("/api/v1/certificates", files={"file": ("c.png", png())}).status_code == 401
    monkeypatch.setattr(get_settings(), "upload_rate_limit_per_hour", 2)
    certificates._limiter = None
    assert [upload(client, aarav).status_code for _ in range(3)] == [202, 202, 429]


# ---- review -----------------------------------------------------------------------------------------------------------


def _needs_review(client, script, aarav) -> str:
    script.status, script.reasons = "needs_review", ["unknown_issuer"]
    return upload(client, aarav).json()["id"]


def test_13_approve(client, script, aarav, meera):
    cid = _needs_review(client, script, aarav)
    r = client.post(f"/api/v1/certificates/{cid}/review", headers=meera, json={"decision": "approve"})
    assert r.status_code == 200 and r.json()["status"] == "certified"
    assert script.applied == [("u-aarav", cid, ("python",))]
    assert events(cid) == [(None, "processing"), ("processing", "needs_review"), ("needs_review", "certified")]
    assert notes("u-aarav")[-1]["title"] == "Certificate 'Python Basics' is certified"
    again = client.post(f"/api/v1/certificates/{cid}/review", headers=meera, json={"decision": "approve"})
    assert again.status_code == 409 and again.json()["code"] == "ALREADY_REVIEWED"
    assert client.get("/api/v1/reviews/certificates", headers=meera).json() == []


def test_13_reject_needs_reason_and_student_sees_it(client, script, aarav, meera):
    cid = _needs_review(client, script, aarav)
    path = f"/api/v1/certificates/{cid}/review"
    assert client.post(path, headers=meera, json={"decision": "reject"}).status_code == 422
    assert client.post(path, headers=meera, json={"decision": "reject", "reason": "ab"}).status_code == 422
    r = client.post(path, headers=meera, json={"decision": "reject", "reason": "Name differs from profile"})
    assert r.status_code == 200 and r.json()["status"] == "rejected"
    assert client.get(f"/api/v1/certificates/{cid}", headers=aarav).json()["review_reason"] == "Name differs from profile"
    assert script.applied == []
    assert notes("u-aarav")[-1]["title"] == "Certificate 'Python Basics' is rejected"
    assert events(cid)[-1] == ("needs_review", "rejected")


def test_13_review_scope_and_roles(client, script, aarav, diya, meera, arjun, suresh, kavya):
    cid = _needs_review(client, script, aarav)
    path = f"/api/v1/certificates/{cid}/review"
    approve = {"decision": "approve"}
    assert client.post(path, headers=arjun, json=approve).status_code == 404  # not Aarav's mentor
    assert client.post(path, headers=aarav, json=approve).status_code == 403
    assert client.post(path, headers=kavya, json=approve).status_code == 403
    assert client.get("/api/v1/reviews/certificates", headers=arjun).json() == []
    assert client.get("/api/v1/reviews/certificates", headers=aarav).status_code == 403
    assert client.get("/api/v1/reviews/certificates", headers=kavya).status_code == 403
    assert client.post(path.replace(cid, "nope"), headers=meera, json=approve).status_code == 404
    # a guide may read the certificate but is not the assigned mentor, so may not decide
    cypher("MATCH (f:Faculty {user_id: 'u-arjun'}), (s:Student {user_id: 'u-aarav'}) "
           "CREATE (f)-[:MENTORS {id: 'g1', type: 'guide', status: 'active', since: '2026-06-01'}]->(s)")
    assert client.get(f"/api/v1/certificates/{cid}", headers=arjun).status_code == 200
    assert client.post(path, headers=arjun, json=approve).status_code == 404
    assert client.post(path, headers=suresh, json=approve).status_code == 200  # the HOD may decide


def test_review_failure_rolls_back(client, script, aarav, meera):
    cid = _needs_review(client, script, aarav)

    def boom(tx, *args):
        raise RuntimeError("trust failed")

    certificates.set_pipeline_for_tests(lambda *a: None, lambda *a: None, boom)
    before = events(cid)
    r = client.post(f"/api/v1/certificates/{cid}/review", headers=meera, json={"decision": "approve"})
    assert r.status_code == 500
    status = cypher("MATCH (e:Evidence {id: $id}) RETURN e.status AS s", id=cid)[0]["s"]
    assert status == "needs_review" and events(cid) == before  # nothing half-applied


# ---- reads and file ---------------------------------------------------------------------------------------------------


def test_certificate_scope(client, script, aarav, diya, meera, arjun, suresh, kavya):
    cid = upload(client, aarav).json()["id"]
    url = f"/api/v1/certificates/{cid}"
    assert [client.get(url, headers=h).status_code for h in (aarav, meera, suresh)] == [200, 200, 200]
    assert [client.get(url, headers=h).status_code for h in (diya, arjun)] == [404, 404]
    assert client.get(url, headers=kavya).status_code == 403
    assert client.get(url).status_code == 401
    assert client.get("/api/v1/me/certificates", headers=diya).json() == []


def test_file_stream_headers_and_scope(client, script, aarav, diya, meera, arjun):
    cid = upload(client, aarav).json()["id"]
    url = f"/api/v1/certificates/{cid}/file"
    r = client.get(url, headers=aarav)
    assert r.status_code == 200 and r.headers["content-type"] == "image/png"
    assert r.headers["content-disposition"] == "inline" and r.headers["x-content-type-options"] == "nosniff"
    assert r.content.startswith(PNG)
    assert client.get(url, headers=meera).status_code == 200
    assert client.get(url, headers=diya).status_code == 404 and client.get(url, headers=arjun).status_code == 404
    assert client.get(url).status_code == 401
    # a stored path outside the uploads folder is never served
    cypher("MATCH (e:Evidence {id: $id}) SET e.file_path = $p", id=cid, p=os.path.abspath(__file__))
    assert client.get(url, headers=aarav).status_code == 404
    assert client.get("/uploads/anything").status_code == 404  # no static mount (ADR-03)


# ---- JOB-02 -----------------------------------------------------------------------------------------------------------


def test_job_02_sweeps_stale_processing(client, script, aarav):
    old = (utc_now() - timedelta(seconds=120)).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    fresh = utc_now().isoformat(timespec="milliseconds").replace("+00:00", "Z")
    cypher(
        """
        MATCH (s:Student {user_id: 'u-aarav'})
        CREATE (s)-[:SUBMITTED]->(:Evidence {id: 'e-old', status: 'processing', title: 'Stuck', updated_at: $old,
               created_at: $old, skills: [], reasons: [], media_type: 'image/png'})
        CREATE (s)-[:SUBMITTED]->(:Evidence {id: 'e-new', status: 'processing', title: 'Busy', updated_at: $fresh,
               created_at: $fresh, skills: [], reasons: [], media_type: 'image/png'})
        """,
        old=old, fresh=fresh,
    )
    assert certificates.sweep_stale() == 1
    rows = {r["id"]: r for r in cypher("MATCH (e:Evidence) RETURN e.id AS id, e.status AS s, e.reasons AS r")}
    assert rows["e-old"]["s"] == "failed" and rows["e-old"]["r"] == ["interrupted"]
    assert rows["e-new"]["s"] == "processing"
    assert events("e-old") == [("processing", "failed")]
    assert certificates.sweep_stale() == 0  # idempotent


def test_job_01_is_idempotent(client, script, aarav):
    cid = upload(client, aarav).json()["id"]
    before = events(cid)
    certificates.process_certificate(cid)  # already certified: exits without doing anything
    assert events(cid) == before and len(script.applied) == 1
    certificates.process_certificate("does-not-exist")  # unknown id never raises


def test_no_secret_text_in_notifications(client, script, aarav, meera):
    cid = _needs_review(client, script, aarav)
    client.post(f"/api/v1/certificates/{cid}/review", headers=aarav, json={"decision": "approve"})
    for user in ("u-aarav", "u-meera"):
        assert all("sha256" not in (n["body"] or "") and "uploads" not in n["title"] for n in notes(user))


# ---- P1's real verification, not the stand-in ---------------------------------------------------------------------------


def test_an_upload_is_never_its_own_duplicate(client, aarav):
    """Regression for the integration bug: intake used to store the SHA-256 on the `processing` row, so P1's rule 1
    ("does any Evidence carry this hash?") matched the upload against itself and every file came back `duplicate`."""
    pytest.importorskip("rapidfuzz")
    pytest.importorskip("imagehash")
    from app.ml.extraction import Extraction
    from app.ml.trust import apply_certified
    from app.ml.verification import verify

    cypher("MATCH (s:Student {user_id: 'u-aarav'}) SET s.name = 'Aarav Menon', s.enrolled_on = '2024-08-01'")
    cypher("MATCH (i:Issuer) DETACH DELETE i")
    cypher("CREATE (:Issuer {name: 'Coursera', aliases: [], kind: 'mooc'})")

    def extract(data, media_type):
        return Extraction(  # a different certificate ID per file, so rule 3 (same issuer + ID) never fires
            is_certificate=True, holder_name="Aarav Menon", title="Deep Learning with PyTorch", issuer="Coursera",
            issue_date="2026-08-10", level="online", type="course", skills=["pytorch"], certificate_id=data[8:16].hex(),
            verify_url=None, contains_instructions=False, source="llm",
        )

    certificates.set_pipeline_for_tests(extract, verify, apply_certified)
    first = upload(client, aarav).json()["id"]
    done = client.get(f"/api/v1/certificates/{first}", headers=aarav).json()
    assert done["status"] == "certified", done  # not "duplicate"
    # the very same bytes uploaded again ARE a duplicate of the first
    data = png()
    one = upload(client, aarav, data).json()["id"]
    two = upload(client, aarav, data).json()["id"]
    assert client.get(f"/api/v1/certificates/{one}", headers=aarav).json()["status"] in ("certified", "needs_review")
    assert client.get(f"/api/v1/certificates/{two}", headers=aarav).json()["status"] == "duplicate"
