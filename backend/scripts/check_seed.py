"""Independent seed check (E5, TEST-32).

    python -m scripts.check_seed            # inside the backend container, after seed --reset

Recomputes the dashboard figures straight from Neo4j with its own Cypher, from
the definitions in backend §6.4, §6.6 and §8 (MET-01, 02, 06, 10), and compares
them with what the API serves (GET /dept/dashboard as the HOD, GET /me/mentees
as Meera). It deliberately imports nothing from app.services or app.repos, so a
bug in the service layer cannot hide itself. Prints PASS or FAIL per figure and
exits 1 on any mismatch.

Environment: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD (as for the backend),
CHECK_API_BASE (default http://localhost:8000/api/v1), TODAY_OVERRIDE,
MIN_MEETINGS_PER_TERM (2), ATTENTION_NO_SESSION_DAYS (45), ISSUE_STALE_DAYS (14).
"""

from __future__ import annotations

import os
import sys
from datetime import date, timedelta

import httpx
from neo4j import GraphDatabase

API = os.environ.get("CHECK_API_BASE", "http://localhost:8000/api/v1").rstrip("/")
PASSWORD = "Demo@123"  # noqa: S105 - the published demo password (AGENTS.md)
HOD, MENTOR = "suresh@demo.gurusetu", "meera@demo.gurusetu"

TODAY = date.fromisoformat(os.environ.get("TODAY_OVERRIDE") or date.today().isoformat())
MIN_MEETINGS = int(os.environ.get("MIN_MEETINGS_PER_TERM", "2"))
NO_SESSION_DAYS = int(os.environ.get("ATTENTION_NO_SESSION_DAYS", "45"))
STALE_DAYS = int(os.environ.get("ISSUE_STALE_DAYS", "14"))

# ---- API -------------------------------------------------------------------


def _call(path: str, token: str | None = None, body: dict | None = None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    resp = httpx.request("POST" if body else "GET", API + path, json=body, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def login(email: str) -> str:
    return _call("/auth/login", body={"email": email, "password": PASSWORD})["access_token"]


# ---- graph -----------------------------------------------------------------

TERM = """
MATCH (t:Term) WHERE t.start_date <= $today AND $today <= t.end_date
RETURN t.id AS id, t.start_date AS start, t.end_date AS end
"""

STUDENTS = "MATCH (s:Student {dept_code: $dept}) RETURN count(s) AS n"

# One row per active assigned link, with everything §6.4 needs.
LINKS = """
MATCH (f:Faculty)-[m:MENTORS {type: 'assigned', status: 'active'}]->(s:Student {dept_code: $dept})
OPTIONAL MATCH (f)-[:LOGGED]->(x:Session {context: 'assigned'})-[a:ATTENDED_BY {present: true}]->(s)
WITH f, m, s, collect(DISTINCT x {.date}) AS sessions
OPTIONAL MATCH (f)-[:LOGGED]->(:Session)-[:CREATED]->(ai:ActionItem {status: 'open'})-[:FOR]->(s)
  WHERE ai.due_date < $today
WITH f, m, s, sessions, count(DISTINCT ai) AS overdue
OPTIONAL MATCH (i:Issue)-[:ABOUT]->(s)
  WHERE i.status <> 'resolved' AND substring(toString(i.raised_at), 0, 10) < $stale_before
WITH f, m, s, sessions, overdue, count(DISTINCT i) AS stale
OPTIONAL MATCH (s)-[:HAS_RECORD]->(r:AcademicRecord)
WITH f, m, s, sessions, overdue, stale, collect(r {.term_id, .cgpa, .attendance_pct}) AS records
RETURN f.user_id AS mentor, f.email AS mentor_email, s.user_id AS student, toString(m.since) AS since,
       [x IN sessions | toString(x.date)] AS session_dates, overdue, stale, records,
       coalesce(s.marked_at_risk, false) AS marked
"""

ALL_OVERDUE = """
MATCH (ai:ActionItem {status: 'open'})-[:FOR]->(s:Student {dept_code: $dept})
WHERE ai.due_date < $today
RETURN count(DISTINCT ai) AS n
"""

PENDING_REVIEWS = """
MATCH (s:Student {dept_code: $dept})-[:SUBMITTED]->(e:Evidence {status: 'needs_review'})
RETURN count(DISTINCT e) AS n
"""

MENTOR_IDS = "MATCH (f:Faculty) RETURN f.user_id AS id, f.email AS email"


def reasons_for(row: dict, term: dict, prev_term_id: str | None) -> set[str]:
    in_term = [d for d in row["session_dates"] if term["start"] <= d[:10] <= term["end"]]
    reasons = set()
    recent_cut = (TODAY - timedelta(days=NO_SESSION_DAYS)).isoformat()
    since = (row["since"] or "")[:10]
    if since and since < recent_cut and not any(d[:10] >= recent_cut for d in row["session_dates"]):
        reasons.add("no_recent_session")
    start, end = date.fromisoformat(term["start"]), date.fromisoformat(term["end"])
    if not in_term and TODAY > start + (end - start) / 2:
        reasons.add("no_meeting_this_term")
    if row["overdue"]:
        reasons.add("overdue_action")
    if row["stale"]:
        reasons.add("stale_issue")
    if row["marked"]:
        reasons.add("marked_at_risk")
    records = {r["term_id"]: r for r in row["records"]}
    cur = records.get(term["id"])
    if cur:
        prev = records.get(prev_term_id) if prev_term_id else None
        if cur["attendance_pct"] < 75 or (prev and prev["cgpa"] - cur["cgpa"] >= 1.0):
            reasons.add("suggested_at_risk")
    return reasons


def main() -> int:
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    auth = (os.environ.get("NEO4J_USER", "neo4j"), os.environ["NEO4J_PASSWORD"])
    dept = os.environ.get("DEMO_DEPT", "CSE")
    stale_before = (TODAY - timedelta(days=STALE_DAYS)).isoformat()
    params = {"dept": dept, "today": TODAY.isoformat(), "stale_before": stale_before}

    with GraphDatabase.driver(uri, auth=auth) as driver, driver.session() as s:
        term = s.run(TERM, params).single()
        if term is None:
            print(f"FAIL  no Term contains {TODAY}")
            return 1
        term = dict(term)
        prev = s.run("MATCH (t:Term) WHERE t.end_date < $start RETURN t.id AS id ORDER BY t.end_date DESC LIMIT 1",
                     start=term["start"]).single()
        prev_id = prev["id"] if prev else None
        students = s.run(STUDENTS, params).single()["n"]
        links = [dict(r) for r in s.run(LINKS, params)]
        overdue = s.run(ALL_OVERDUE, params).single()["n"]
        pending = s.run(PENDING_REVIEWS, params).single()["n"]
        email_of = {r["id"]: r["email"] for r in s.run(MENTOR_IDS)}

    allotted_ids = {r["student"] for r in links}
    by_mentor: dict[str, list[dict]] = {}
    for r in links:
        by_mentor.setdefault(r["mentor"], []).append(r)

    def compliant(r: dict) -> bool:
        return sum(term["start"] <= d[:10] <= term["end"] for d in r["session_dates"]) >= MIN_MEETINGS

    mine = {
        "students_total": students,
        "students_allotted": len(allotted_ids),
        "ratio": f"1:{round(len(allotted_ids) / len(by_mentor))}" if by_mentor else "1:0",
        "compliance_pct": round(100 * sum(compliant(r) for r in links) / len(links), 1) if links else 0.0,
        "overdue_actions": overdue,
        "pending_reviews": pending,
    }
    per_mentor = {m: round(100 * sum(compliant(r) for r in rows) / len(rows), 1) for m, rows in by_mentor.items()}
    meera_id = next((k for k, v in email_of.items() if v == MENTOR), None)
    meera_flagged = sum(1 for r in by_mentor.get(meera_id, []) if reasons_for(r, term, prev_id))

    dash = _call("/dept/dashboard", login(HOD))
    rows = _call("/me/mentees", login(MENTOR))
    api_flagged = sum(1 for r in rows if r.get("mentorship_type") == "assigned" and r.get("needs_attention"))

    failures = 0

    def check(name: str, ours, theirs) -> None:
        nonlocal failures
        ok = ours == theirs
        failures += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {name:<34} graph={ours!r:<10} api={theirs!r}")

    print(f"check_seed: today={TODAY} term={term['id']} dept={dept}")
    for key, value in mine.items():
        check(key, value, dash.get(key))
    api_mentors = {m["mentor_id"]: m.get("compliance_pct") for m in dash.get("mentors", [])}
    for mentor_id in sorted(per_mentor):
        check(f"compliance_pct[{mentor_id}]", per_mentor[mentor_id], api_mentors.get(mentor_id))
    check("flagged assigned mentees (Meera)", meera_flagged, api_flagged)
    print("all figures match" if not failures else f"{failures} figure(s) differ")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
