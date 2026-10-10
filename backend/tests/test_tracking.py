"""Mentor home (TEST-33), Mentee 360 (TEST-43) and My mentorship (TEST-42), on a hand-built graph.

Dates are relative to TODAY_OVERRIDE (2026-10-10). Term 2026-ODD runs 2026-07-15 to 2026-11-30, so its midpoint is
2026-09-22 and the no-session cut-off is 2026-08-26.
"""
import bcrypt
import pytest

from app.core.database import run_write

HASH = bcrypt.hashpw(b"Demo@123", bcrypt.gensalt(4)).decode()
NOTE = "PRIVATE-NOTE-XYZ"
ISSUE_TEXT = "PRIVATE-ISSUE-XYZ"


def cypher(query: str, **params):
    return run_write(lambda tx: [r.data() for r in tx.run(query, **params)])


def student(uid: str, name: str, roll: str, since: str = "2026-05-01") -> None:
    cypher(
        """
        MERGE (s:User:Student {user_id: $uid})
        ON CREATE SET s.email = $email, s.password_hash = $hash, s.name = $name, s.role = 'student',
                      s.dept_code = 'CSE', s.roll_no = $roll, s.year = 3, s.created_at = '2026-01-01T00:00:00.000Z'
        WITH s MATCH (f:Faculty {user_id: 'u-meera'})
        MERGE (f)-[m:MENTORS {id: $link}]->(s)
        ON CREATE SET m.type = 'assigned', m.status = 'active', m.since = $since
        """,
        uid=uid, email=f"{uid}@demo.gurusetu", hash=HASH, name=name, roll=roll, link=f"mt-{uid}", since=since,
    )


def session(sid: str, author: str, student_id: str, day: str, notes: str | None = None, present: bool = True,
            confirmed: str | None = None, followup: str | None = None) -> None:
    cypher(
        """
        MATCH (f:Faculty {user_id: $author}), (s:Student {user_id: $student})
        CREATE (f)-[:LOGGED]->(x:Session {id: $sid, date: $day, mode: 'in_person', kind: 'individual',
               context: 'assigned', topics: ['academic'], notes: $notes, confidential: false,
               next_followup: $followup, created_at: $created})
        CREATE (x)-[:ATTENDED_BY {present: $present, confirmed_at: $confirmed}]->(s)
        """,
        author=author, student=student_id, sid=sid, day=day, notes=notes, present=present, confirmed=confirmed,
        followup=followup, created=f"{day}T09:00:00.000Z",
    )


def action(aid: str, session_id: str, student_id: str, due: str, status: str = "open") -> None:
    cypher(
        """
        MATCH (x:Session {id: $sid}), (s:Student {user_id: $student})
        CREATE (x)-[:CREATED]->(a:ActionItem {id: $aid, text: 'Do the thing', owner: 'mentee', due_date: $due,
               status: $status, created_at: '2026-08-01T00:00:00.000Z', updated_at: '2026-08-01T00:00:00.000Z'})
        CREATE (a)-[:FOR]->(s)
        """,
        sid=session_id, student=student_id, aid=aid, due=due, status=status,
    )


def issue(iid: str, student_id: str, raised_by: str, raised_at: str, confidential: bool = False,
          status: str = "raised") -> None:
    cypher(
        """
        MATCH (s:Student {user_id: $student})
        CREATE (i:Issue {id: $iid, category: 'personal', text: $text, status: $status, escalated: false,
               confidential: $conf, raised_by: $by, raised_by_role: 'faculty', raised_at: $at})
        CREATE (i)-[:ABOUT]->(s)
        """,
        student=student_id, iid=iid, by=raised_by, at=raised_at, conf=confidential, status=status, text=ISSUE_TEXT,
    )


@pytest.fixture(autouse=True)
def world(fresh_seed):
    for label in ("Session", "ActionItem", "Issue", "StatusEvent", "Notification", "Term", "AcademicRecord"):
        cypher(f"MATCH (n:{label}) DETACH DELETE n")
    cypher(
        "CREATE (:Term {id: '2026-ODD', name: 'Odd 2026', start_date: '2026-07-15', end_date: '2026-11-30'})"
    )
    cypher("MATCH (f:Faculty {user_id: 'u-meera'}) SET f.designation = 'Professor'")
    student("u-t-ok", "Tara Ok", "CB.EN.U4CSE24301")
    student("u-t-old", "Omar Old", "CB.EN.U4CSE24302")
    student("u-t-stale", "Sana Stale", "CB.EN.U4CSE24303")
    # Aarav (base graph): no sessions at all -> no_recent_session + no_meeting_this_term
    for n, day in (("1", "2026-09-20"), ("2", "2026-10-01")):
        session(f"s-ok-{n}", "u-meera", "u-t-ok", day, notes=NOTE)
        session(f"s-stale-{n}", "u-meera", "u-t-stale", day)
    session("s-old-1", "u-meera", "u-t-old", "2026-07-20", notes=NOTE)
    action("a-old", "s-old-1", "u-t-old", "2026-09-01")
    action("a-ok-done", "s-ok-1", "u-t-ok", "2026-09-01", status="done")  # done is not overdue
    issue("i-stale", "u-t-stale", "u-meera", "2026-09-20T08:00:00.000Z")
    issue("i-fresh", "u-t-ok", "u-meera", "2026-10-05T08:00:00.000Z")  # 5 days: not stale
    issue("i-conf", "u-t-ok", "u-arjun", "2026-08-01T08:00:00.000Z", confidential=True)  # another mentor's secret
    cypher("MATCH (s:Student {user_id: 'u-aarav'}) MERGE (s)-[:HAS_RECORD]->(:AcademicRecord {id: 'ar-1', "
           "term_id: '2026-ODD', cgpa: 8.1, attendance_pct: 88.0, backlogs: 0})")


def test_33_mentor_home_flags_and_order(client, meera):
    rows = client.get("/api/v1/me/mentees", headers=meera).json()
    by_id = {r["student_id"]: r for r in rows}
    assert set(by_id) == {"u-aarav", "u-t-ok", "u-t-old", "u-t-stale"}
    assert by_id["u-aarav"]["attention_reasons"] == ["no_recent_session", "no_meeting_this_term"]
    assert by_id["u-t-old"]["attention_reasons"] == ["no_recent_session", "overdue_action"]
    assert by_id["u-t-stale"]["attention_reasons"] == ["stale_issue"]
    # Arjun's confidential issue about Tara is invisible to Meera, so Tara is clean (security section 4).
    assert by_id["u-t-ok"]["attention_reasons"] == [] and by_id["u-t-ok"]["needs_attention"] is False
    assert by_id["u-t-ok"]["open_issues"] == 1
    # flagged first, then more reasons, then name (Aarav and Omar both have 2 reasons)
    assert [r["student_id"] for r in rows] == ["u-aarav", "u-t-old", "u-t-stale", "u-t-ok"]
    ok = by_id["u-t-ok"]
    assert ok["meetings_this_term"] == 2 and ok["meetings_required"] == 2 and ok["last_session_date"] == "2026-10-01"
    assert by_id["u-t-old"]["overdue_actions"] == 1 and by_id["u-t-old"]["open_actions"] == 1
    assert by_id["u-t-ok"]["overdue_actions"] == 0 and by_id["u-t-ok"]["open_actions"] == 0


def test_33_unconfirmed_sessions_and_roles(client, meera, aarav, suresh, arjun):
    session("s-unc", "u-meera", "u-aarav", "2026-10-01")  # present, unconfirmed, 9 days old
    session("s-unc-new", "u-meera", "u-aarav", "2026-10-08")  # 2 days old: not counted yet
    rows = {r["student_id"]: r for r in client.get("/api/v1/me/mentees", headers=meera).json()}
    assert rows["u-aarav"]["unconfirmed_sessions"] == 1
    assert client.get("/api/v1/me/mentees", headers=aarav).status_code == 403
    assert client.get("/api/v1/me/mentees", headers=suresh).status_code == 403
    assert client.get("/api/v1/me/mentees", headers=arjun).json() != rows  # Arjun sees only his own mentees
    assert client.get("/api/v1/me/mentees").status_code == 401


def test_43_mentee_360_scope_and_notes(client, meera, arjun, suresh, aarav, kavya):
    r = client.get("/api/v1/mentees/u-t-ok/overview", headers=meera)
    assert r.status_code == 200
    body = r.json()
    assert body["student"]["user_id"] == "u-t-ok"
    assert len(body["sessions"]) == 2 and all(s["notes"] == NOTE for s in body["sessions"])
    assert len(body["action_items"]) == 1 and body["action_items"][0]["overdue"] is False
    assert "password_hash" not in r.text and "embedding" not in r.text
    # Meera sees her own issue's text; Arjun's confidential issue is listed without text
    issues = {i["id"]: i for i in body["issues"]}
    assert issues["i-fresh"]["text"] == ISSUE_TEXT
    assert "text" not in issues["i-conf"] and issues["i-conf"]["confidential"] is True
    assert body["attention_reasons"] == []
    assert body["term_summary"] is None

    # HOD: same student, never any notes
    hod = client.get("/api/v1/mentees/u-t-ok/overview", headers=suresh)
    assert hod.status_code == 200 and NOTE not in hod.text and "notes" not in hod.json()["sessions"][0]
    # other faculty and other roles
    assert client.get("/api/v1/mentees/u-t-ok/overview", headers=arjun).status_code == 404
    assert client.get("/api/v1/mentees/u-t-ok/overview", headers=aarav).status_code == 403
    assert client.get("/api/v1/mentees/u-t-ok/overview", headers=kavya).status_code == 403
    assert client.get("/api/v1/mentees/u-nobody/overview", headers=meera).status_code == 404


def test_43_other_mentors_notes_never_shown(client, meera):
    """A session written by another mentor (e.g. before a handover) shows its date but never its notes (REQ-028)."""
    session("s-prev", "u-arjun", "u-t-ok", "2026-07-30", notes="ARJUN-ONLY-NOTE")
    r = client.get("/api/v1/mentees/u-t-ok/overview", headers=meera)
    assert "ARJUN-ONLY-NOTE" not in r.text
    prev = next(s for s in r.json()["sessions"] if s["id"] == "s-prev")
    assert prev["logged_by"]["name"] == "Arjun" and "notes" not in prev


def test_42_my_mentorship(client, aarav, meera):
    session("s-a1", "u-meera", "u-aarav", "2026-10-02", notes=NOTE, followup="2026-10-20")
    session("s-a2", "u-meera", "u-aarav", "2026-09-10", confirmed="2026-09-11T10:00:00.000Z", followup="2026-10-05")
    action("a-aarav", "s-a1", "u-aarav", "2026-10-15")
    issue("i-aarav", "u-aarav", "u-meera", "2026-10-02T08:00:00.000Z", confidential=True)
    r = client.get("/api/v1/me/mentorship", headers=aarav)
    assert r.status_code == 200
    body = r.json()
    assert body["assigned_mentor"]["name"] == "Meera"
    assert [s["id"] for s in body["sessions_to_confirm"]] == ["s-a1"]
    assert [s["id"] for s in body["recent_sessions"]] == ["s-a1", "s-a2"]
    assert body["next_followup"] == "2026-10-20"  # the earliest FUTURE follow-up (2026-10-05 has passed)
    assert [a["id"] for a in body["action_items"]] == ["a-aarav"]
    assert NOTE not in r.text and ISSUE_TEXT not in r.text  # notes never; a confidential issue's text never
    assert "text" not in body["issues"][0]
    assert client.get("/api/v1/me/mentorship", headers=meera).status_code == 403
