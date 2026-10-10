"""Synthetic mentoring, academic and certificate data (backend section 10). [MOCK] - every row is invented (NG-03).

Called by `scripts/seed.py` after users, links and openings exist. Dates are offsets from the anchor date, so
`--anchor-date` shifts the whole world and the flags below hold on any demo day.

What the layout guarantees (the numbers backend section 10 and TEST-32/33 expect):
  * Meera has 13 assigned mentees. Exactly three are flagged: Karthik (`no_recent_session` + `overdue_action`),
    Diya (`stale_issue`) and Rahul (`overdue_action`). Aarav is NOT flagged.
  * Meera, Arjun and Lakshmi's mentees all have >= 2 present sessions this term; 4 of Vikram's 10 have fewer.
  * 8 open action items are overdue, 4 issues are unresolved (one stale in Meera's group), 1 issue is confidential.
  * 3 students have attendance below 75 percent, none of them Meera's (so they add no flag to her home).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import random
from collections import defaultdict
from typing import Any

TOPICS = ["academic", "attendance", "career", "research", "personal", "other"]
CRITERIA = [
    ("NAAC-2.3.3", "Mentor:student ratio", ["internship"], ["MET-02"]),
    ("NAAC-5.3.1", "Awards and medals", ["hackathon", "competition", "sports", "cultural"], ["MET-08"]),
]
# (title, issuer, type, level, skills) - skills are seed concepts
CERT_POOL = [
    ("Deep Learning Specialisation", "Coursera", "course", "online", ["deep learning", "python"]),
    ("Computer Vision Workshop", "IEEE", "workshop", "national", ["computer vision"]),
    ("Smart India Hackathon Finalist", "Smart India Hackathon", "hackathon", "national", ["python", "edge ai"]),
    ("Embedded Systems Programming", "NPTEL", "course", "online", ["embedded c", "internet of things"]),
    ("Campus Code Sprint Winner", "Campus Coding Club", "competition", "college", ["data structures"]),
    ("Machine Learning Foundations", "NPTEL", "course", "online", ["machine learning", "python"]),
    ("Docker for Developers", "Coursera", "course", "online", ["docker"]),
    ("Web Development Bootcamp", "Amrita ACM Chapter", "workshop", "university", ["react", "javascript"]),
    ("Database Design", "NPTEL", "course", "online", ["databases"]),
    ("Public Speaking Contest", "Campus Coding Club", "competition", "college", ["public speaking"]),
]


def _day(anchor: dt.date, n: int) -> str:
    return (anchor + dt.timedelta(days=n)).isoformat()


def _stamp(anchor: dt.date, n: int, hour: int = 9) -> str:
    return f"{_day(anchor, n)}T{hour:02d}:00:00.000Z"


def _event(entity_type: str, entity_id: str, frm: str | None, to: str, actor: tuple[str, str], at: str, n: int) -> dict:
    return {"id": f"se-{entity_id}-{n}", "entity_type": entity_type, "entity_id": entity_id, "from_status": frm,
            "to_status": to, "actor_id": actor[0], "actor_name": actor[1], "at": at}


def build(anchor: dt.date, assignments: list[tuple[str, str]], names: dict[str, str]) -> dict[str, list[dict[str, Any]]]:
    """Pure data: everything the loader writes, keyed by what it is. `assignments` is [(mentor_id, student_id)]."""
    rng = random.Random(20261011)  # noqa: S311 - synthetic fixtures, not crypto
    by_mentor: dict[str, list[str]] = defaultdict(list)
    for mentor, student in assignments:
        by_mentor[mentor].append(student)
    mentor_name = {m: names[m] for m in by_mentor}
    index = {s: i for i, (_, s) in enumerate(assignments)}

    def student_named(first: str, mentor: str) -> str:
        return next(s for s in by_mentor[mentor] if names[s].startswith(first + " "))

    karthik, diya, rahul = (student_named(n, "u-meera") for n in ("Karthik", "Diya", "Rahul"))
    sessions: list[dict] = []
    attendance: list[dict] = []
    items: list[dict] = []
    issues: list[dict] = []
    events: list[dict] = []

    def session(sid: str, mentor: str, day: int, kind: str, present: dict[str, bool], topics: list[str]) -> str:
        sessions.append({
            "id": sid, "mentor_id": mentor, "date": _day(anchor, day), "mode": rng.choice(["in_person", "online"]),
            "kind": kind, "context": "assigned", "topics": topics, "confidential": False,
            "notes": f"[MOCK] private note for {sid}: discussed {topics[0]} and next steps.",
            "next_followup": _day(anchor, day + 30) if rng.random() < 0.4 else None,
            "created_at": _stamp(anchor, day, 10),
        })
        for student, here in present.items():
            old = day < -7
            confirmed = _stamp(anchor, day + 1, 12) if here and old and rng.random() < 0.9 else None
            attendance.append({"session_id": sid, "student_id": student, "present": here, "confirmed_at": confirmed})
        return sid

    def item(session_id: str, mentor: str, student: str, text: str, due: int, status: str, session_day: int) -> None:
        iid = f"ai-{len(items) + 1:03d}"
        owner = "mentee" if rng.random() < 0.85 else "mentor"
        done_day = min(due, -3)
        items.append({
            "id": iid, "session_id": session_id, "student_id": student, "text": text, "owner": owner,
            "due_date": _day(anchor, due), "status": status, "created_at": _stamp(anchor, session_day, 10),
            "updated_at": _stamp(anchor, done_day if status != "open" else session_day, 15),
        })
        actor = (mentor, mentor_name[mentor])
        events.append(_event("action_item", iid, None, "open", actor, _stamp(anchor, session_day, 10), 0))
        if status != "open":
            events.append(_event("action_item", iid, "open", "done", (student, names[student]), _stamp(anchor, done_day, 14), 1))
        if status == "verified":
            events.append(_event("action_item", iid, "done", "verified", actor, _stamp(anchor, done_day, 15), 2))

    overdue_plan = {  # (student, due offset): the 8 overdue open items (backend section 10)
        karthik: -30, rahul: -15,
        by_mentor["u-arjun"][2]: -20, by_mentor["u-arjun"][5]: -8,
        by_mentor["u-lakshmi"][1]: -12, by_mentor["u-lakshmi"][7]: -6,
        by_mentor["u-vikram"][1]: -18, by_mentor["u-vikram"][3]: -4,
    }
    texts = ["Revise unit 3 notes", "Submit the lab record", "Draft the project abstract", "Register for the NPTEL course",
             "Prepare for the viva", "Fix the attendance shortfall", "Read two papers on the topic"]

    for mentor, group in by_mentor.items():
        roster = list(group)
        # previous term (2026-EVEN), then this term (2026-ODD): group A, individuals, group B
        session(f"s-{mentor}-even", mentor, -200, "group", {s: True for s in roster}, ["academic", "career"])
        a = session(f"s-{mentor}-a", mentor, -70, "group", {s: True for s in roster}, ["academic", "attendance"])
        present_b = {s: True for s in roster}
        if mentor == "u-meera":
            present_b[karthik] = False
        if mentor == "u-vikram":
            for s in roster[6:]:
                present_b[s] = False  # 4 of Vikram's 10 end the term with one meeting
        b = session(f"s-{mentor}-b", mentor, -25, "group", present_b, ["academic", "research"])
        if mentor == "u-meera":
            session(f"s-{mentor}-k", mentor, -60, "individual", {karthik: True}, ["personal"])  # Karthik's last
        pool = [s for s in roster if s != karthik and not (mentor == "u-vikram" and s in roster[6:])]
        for n, s in enumerate(rng.sample(pool, min(5, len(pool)))):
            session(f"s-{mentor}-i{n}", mentor, -40 + n, "individual", {s: True}, [rng.choice(TOPICS)])

        for s in roster:
            overdue_due = overdue_plan.get(s)
            if overdue_due is not None:
                item(a, mentor, s, rng.choice(texts), overdue_due, "open", -70)
            elif rng.random() < 0.45:
                item(a, mentor, s, rng.choice(texts), rng.randint(-60, -35), rng.choice(["done", "verified"]), -70)
            if s in present_b and present_b[s] and rng.random() < 0.4:
                future = rng.random() < 0.5
                item(b, mentor, s, rng.choice(texts), rng.randint(3, 20) if future else rng.randint(-20, -10),
                     "open" if future else rng.choice(["done", "verified"]), -25)

    # ---- issues: ~15, 4 unresolved (one stale in Meera's group), 1 confidential ----------------------------------
    def issue(student: str, mentor: str, category: str, raised: int, resolved: int | None, text: str,
              confidential: bool = False, session_id: str | None = None) -> None:
        iid = f"is-{len(issues) + 1:03d}"
        issues.append({
            "id": iid, "student_id": student, "mentor_id": mentor, "category": category, "text": text,
            "status": "resolved" if resolved is not None else "raised", "confidential": confidential,
            "raised_at": _stamp(anchor, raised, 11), "resolved_at": _stamp(anchor, resolved, 16) if resolved is not None else None,
            "resolution": "[MOCK] spoke to the student and agreed a plan." if resolved is not None else None,
            "session_id": session_id,
        })
        actor = (mentor, mentor_name[mentor])
        events.append(_event("issue", iid, None, "raised", actor, _stamp(anchor, raised, 11), 0))
        if resolved is not None:
            events.append(_event("issue", iid, "raised", "resolved", actor, _stamp(anchor, resolved, 16), 1))

    issue(diya, "u-meera", "attendance", -20, None, "[MOCK] Attendance has dropped in two courses.", session_id="s-u-meera-a")
    for k, s in enumerate(by_mentor["u-meera"][4:7]):
        issue(s, "u-meera", rng.choice(["academic", "personal", "career"]), -60 + k, -35 + k, "[MOCK] Needs a study plan.",
              session_id="s-u-meera-a")
    for k, s in enumerate(by_mentor["u-arjun"][3:6]):
        issue(s, "u-arjun", rng.choice(["academic", "research"]), -58 + k, -30 + k, "[MOCK] Project topic unclear.")
    issue(by_mentor["u-arjun"][8], "u-arjun", "personal", -5, None, "[MOCK] Hostel accommodation problem.")
    for k, s in enumerate(by_mentor["u-lakshmi"][3:6]):
        issue(s, "u-lakshmi", rng.choice(["career", "academic"]), -55 + k, -28 + k, "[MOCK] Internship guidance.")
    issue(by_mentor["u-lakshmi"][9], "u-lakshmi", "attendance", -9, None, "[MOCK] Missed a week of classes.")
    for k, s in enumerate(by_mentor["u-vikram"][4:6]):
        issue(s, "u-vikram", "academic", -50 + k, -26 + k, "[MOCK] Backlog clearance plan.")
    issue(by_mentor["u-vikram"][7], "u-vikram", "personal", -12, None, "[MOCK] A private family matter.", confidential=True)

    # ---- academics: 2 terms per student; 3 low-attendance students, none of them Meera's ------------------------
    low = {by_mentor["u-arjun"][4], by_mentor["u-lakshmi"][5], by_mentor["u-vikram"][3]}
    academics: list[dict] = []
    for _, student in assignments:
        base = round(rng.uniform(6.8, 9.2), 1)
        for term, cgpa, att in (
            ("2026-EVEN", base, rng.randint(82, 96)),
            ("2026-ODD", round(max(5.0, base - rng.uniform(-0.3, 0.6)), 1),
             rng.randint(66, 72) if student in low else rng.randint(80, 96)),
        ):
            academics.append({"id": f"ar-{student}-{term}", "student_id": student, "term_id": term, "cgpa": cgpa,
                              "attendance_pct": float(att), "backlogs": 0 if cgpa > 6.5 else 1})

    for record in academics:  # the demo student's CGPA is fixed, not random (see seed_profiles.py)
        if record["student_id"] == "u-aarav":
            record["cgpa"], record["attendance_pct"] = 8.2, 90.0

    # ---- certificates: ~24 more beside Aarav's, with the full range of statuses ---------------------------------
    evidence: list[dict] = []
    everyone = [s for _, s in assignments]
    statuses = ["certified"] * 15 + ["needs_review"] * 4 + ["rejected"] * 2 + ["duplicate", "failed"] + ["certified"] * 2
    for n, status in enumerate(statuses):
        student = everyone[(n * 2 + 1) % len(everyone)] if n else karthik
        title, issuer, kind, level, skills = CERT_POOL[n % len(CERT_POOL)]
        old = n % 6 == 5  # a few from the previous academic year, to test the Jul-Jun window
        issued = -rng.randint(380, 420) if old else -rng.randint(5, 95)
        eid = f"ev-{n + 1:03d}"
        reviewed = status in ("rejected",) or (status == "certified" and n % 3 == 0)
        evidence.append({
            "id": eid, "student_id": student, "status": status, "title": title, "issuer": issuer, "type": kind,
            "level": level, "skills": skills, "issue_date": _day(anchor, issued), "certificate_id": f"SEED-{n + 1:04d}",
            "holder_name": names[student], "created_at": _stamp(anchor, issued + 1, 9),
            "sha256": hashlib.sha256(eid.encode()).hexdigest(),
            "confidence": {"certified": 0.92, "needs_review": 0.60, "rejected": 0.55, "duplicate": 1.0, "failed": None}[status],
            "reasons": {"needs_review": ["name_mismatch"], "rejected": ["unknown_issuer"], "duplicate": ["duplicate_file"],
                        "failed": ["extraction_failed"]}.get(status, []),
            "reviewed_by": "u-meera" if reviewed else None,
            "review_reason": "[MOCK] The issuer could not be verified." if status == "rejected" else None,
        })
        events.append(_event("evidence", eid, None, "processing", (student, names[student]), _stamp(anchor, issued + 1, 9), 0))
        events.append(_event("evidence", eid, "processing", status, ("system", "System"), _stamp(anchor, issued + 1, 9), 1))
    return {"sessions": sessions, "attendance": attendance, "items": items, "issues": issues, "events": events,
            "academics": academics, "evidence": evidence, "flagged_meera": [karthik, diya, rahul],
            "student_index": [{"id": s, "i": i} for s, i in index.items()]}


def write_placeholder_files(items: list[tuple[str, str]], directory: str) -> int:
    """A small synthetic image per seeded certificate, so the review screen's file preview works. [MOCK]
    Skipped quietly where the uploads folder does not exist or cannot be written (a bare local run)."""
    from pathlib import Path

    from PIL import Image, ImageDraw

    root = Path(directory)
    if not root.is_dir():
        return 0
    for name, title in items:
        image = Image.new("RGB", (640, 440), "#fbf7ef")
        draw = ImageDraw.Draw(image)
        draw.rectangle((12, 12, 628, 428), outline="#8c1515", width=4)
        draw.text((40, 60), "SAMPLE CERTIFICATE [MOCK]", fill="#8c1515")
        draw.text((40, 140), title[:60], fill="#1f2937")
        draw.text((40, 380), "Synthetic data for the GuruSetu demo", fill="#6b7280")
        image.save(root / f"seeded-{name}.png")
    return len(items)


def load(driver, anchor: dt.date, assignments: list[tuple[str, str]], names: dict[str, str],
         with_evidence: bool = True) -> dict[str, int]:
    """with_evidence=False leaves certificates to the caller, which runs real files through the pipeline (T2.P4.2)."""
    data = build(anchor, assignments, names)
    if not with_evidence:
        data["evidence"] = []
        data["events"] = [e for e in data["events"] if e["entity_type"] != "evidence"]
    with driver.session() as db:
        for code, title, kinds, metrics in CRITERIA:
            db.run("MERGE (c:Criterion {code: $code}) SET c.framework = 'NAAC', c.title = $title, "
                   "c.evidence_types = $kinds, c.metric_ids = $metrics, c.verified = false",
                   code=code, title=title, kinds=kinds, metrics=metrics).consume()
        db.run(
            """
            UNWIND $rows AS r
            MATCH (f:Faculty {user_id: r.mentor_id})
            CREATE (f)-[:LOGGED]->(s:Session {id: r.id, date: r.date, mode: r.mode, kind: r.kind, context: r.context,
                   topics: r.topics, notes: r.notes, confidential: r.confidential, next_followup: r.next_followup,
                   created_at: r.created_at})
            """, rows=data["sessions"]).consume()
        db.run(
            """
            UNWIND $rows AS r
            MATCH (s:Session {id: r.session_id}), (st:Student {user_id: r.student_id})
            CREATE (s)-[:ATTENDED_BY {present: r.present, confirmed_at: r.confirmed_at}]->(st)
            """, rows=data["attendance"]).consume()
        db.run(
            """
            UNWIND $rows AS r
            MATCH (s:Session {id: r.session_id}), (st:Student {user_id: r.student_id})
            CREATE (s)-[:CREATED]->(a:ActionItem {id: r.id, text: r.text, owner: r.owner, due_date: r.due_date,
                   status: r.status, created_at: r.created_at, updated_at: r.updated_at})
            CREATE (a)-[:FOR]->(st)
            """, rows=data["items"]).consume()
        db.run(
            """
            UNWIND $rows AS r
            MATCH (st:Student {user_id: r.student_id})
            CREATE (i:Issue {id: r.id, category: r.category, text: r.text, status: r.status, escalated: false,
                   confidential: r.confidential, raised_by: r.mentor_id, raised_by_role: 'faculty',
                   raised_at: r.raised_at, resolved_at: r.resolved_at, resolution: r.resolution})
            CREATE (i)-[:ABOUT]->(st)
            WITH i, r OPTIONAL MATCH (s:Session {id: r.session_id})
            FOREACH (_ IN CASE WHEN s IS NULL THEN [] ELSE [1] END | CREATE (s)-[:RAISED]->(i))
            """, rows=data["issues"]).consume()
        db.run(
            """
            UNWIND $rows AS r
            MATCH (st:Student {user_id: r.student_id})
            CREATE (st)-[:HAS_RECORD]->(:AcademicRecord {id: r.id, term_id: r.term_id, cgpa: r.cgpa,
                   attendance_pct: r.attendance_pct, backlogs: r.backlogs})
            """, rows=data["academics"]).consume()
        db.run(
            """
            UNWIND $rows AS r
            MATCH (st:Student {user_id: r.student_id})
            CREATE (st)-[:SUBMITTED]->(e:Evidence {id: r.id, kind: 'certificate', status: r.status,
                   file_path: '/data/uploads/seeded-' + r.id + '.png', media_type: 'image/png', size_bytes: 120000,
                   sha256: r.sha256, holder_name: r.holder_name, title: r.title, issuer: r.issuer,
                   issue_date: r.issue_date, level: r.level, type: r.type, certificate_id: r.certificate_id,
                   skills: r.skills, contains_instructions: false, confidence: r.confidence, reasons: r.reasons,
                   source: 'cache', reviewed_by: r.reviewed_by, review_reason: r.review_reason,
                   created_at: r.created_at, updated_at: r.created_at})
            """, rows=data["evidence"]).consume()
        # certified certificates PROVE their skills; trust 1 unless a mentor already endorsed (none are in the seed)
        for ev in (e for e in data["evidence"] if e["status"] == "certified"):
            db.run(
                """
                MATCH (st:Student {user_id: $sid}), (e:Evidence {id: $eid})
                UNWIND $skills AS name
                MATCH (c:Concept {name: name})
                MERGE (e)-[:PROVES]->(c)
                MERGE (st)-[h:HAS_SKILL]->(c)
                ON CREATE SET h.claimed = false, h.endorsed_by = [], h.evidence_ids = [], h.trust_level = 1
                SET h.trust_level = CASE WHEN h.trust_level < 1 THEN 1 ELSE h.trust_level END,
                    h.evidence_ids = h.evidence_ids + [$eid], h.updated_at = $now
                """, sid=ev["student_id"], eid=ev["id"], skills=ev["skills"], now=ev["created_at"]).consume()
        db.run(
            """
            UNWIND $rows AS r
            CREATE (:StatusEvent {id: r.id, entity_type: r.entity_type, entity_id: r.entity_id,
                   from_status: r.from_status, to_status: r.to_status, actor_id: r.actor_id,
                   actor_name: r.actor_name, at: r.at})
            """, rows=data["events"]).consume()
    from app.core.config import get_settings

    write_placeholder_files([(e["id"], e["title"]) for e in data["evidence"]], get_settings().upload_dir)
    return {k: len(data[k]) for k in ("sessions", "attendance", "items", "issues", "academics", "evidence", "events")}
