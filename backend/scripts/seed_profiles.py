"""Synthetic rich profiles, faculty domains and opening rules (plan: profiles-and-matching-plan.md). [MOCK] - all invented.

Called by `scripts/seed.py` after users, links, openings and mentoring data exist and BEFORE embeddings are built, so the
richer text is part of every embedding. Dates are offsets from the anchor date.

Deliberate demo facts (so the new screens have something to show):
  * Aarav is year 3 with a recorded CGPA of 8.2 (not random) and the demo opening `op-edge-ai` admits him.
  * `op-nlp-ocr` is `strict` with a minimum CGPA of 8.5, so Aarav (8.2) sees it under "Not eligible yet" and cannot apply.
  * `op-robotics` is for year 4 only (advisory), `op-cloud-cost` has a deadline that has passed.
  * The two unallotted students have no institutional record, so their CGPA is "self-reported".
"""
from __future__ import annotations

import datetime as dt
import random
import uuid

FACULTY_PROFILES = {
    "u-meera": {
        "research": [("deep learning", True), ("computer vision", False), ("edge ai", False)],
        "expertise": ["python", "pytorch", "robotics"],
        "courses": [("CS401", "Deep Learning", ["deep learning", "machine learning"]),
                    ("CS312", "Computer Vision", ["computer vision", "deep learning"])],
        "max_guided": 6, "office_hours": "Tuesday and Thursday, 3 to 4 pm, room C-204",
        "qualifications": [("PhD, Computer Science", "IIT Madras", 2014), ("M.Tech, Computer Science", "NIT Calicut", 2009)],
    },
    "u-arjun": {
        "research": [("computer vision", True), ("tensorflow", False), ("machine learning", False)],
        "expertise": ["databases", "cloud computing", "python"],
        "courses": [("CS302", "Database Systems", ["databases", "data structures"])],
        "max_guided": 5, "office_hours": "Monday, 2 to 4 pm, room C-210",
        "qualifications": [("PhD, Computer Science", "IISc Bangalore", 2017)],
    },
    "u-lakshmi": {
        "research": [("signal processing", True), ("machine learning", False)],
        "expertise": ["react", "javascript", "node.js", "technical writing", "public speaking"],
        "courses": [("CS205", "Web Technologies", ["react", "javascript", "node.js"])],
        "max_guided": 5, "office_hours": "Wednesday, 10 am to 12 noon, room C-118",
        "qualifications": [("PhD, Electronics", "IIT Bombay", 2008)],
    },
    "u-vikram": {
        "research": [("edge ai", True), ("internet of things", False)],
        "expertise": ["embedded c", "c", "machine learning"],
        "courses": [("CS210", "Data Structures", ["data structures", "c"])],
        "max_guided": 4, "office_hours": "Friday, 11 am to 1 pm, room C-225",
        "qualifications": [("M.Tech, Embedded Systems", "NIT Trichy", 2012)],
    },
}

# opening id -> v2 fields (offsets are days from the anchor date)
OPENING_RULES = {
    "op-edge-ai": {"positions": 2, "eligible_years": [3, 4], "min_cgpa": 6.5, "eligibility_mode": "advisory",
                   "mode": "hybrid", "duration_weeks": 12, "hours_per_week": 8, "deadline": 30,
                   "preferred": ["docker"]},
    "op-nlp-ocr": {"positions": 1, "eligible_years": [3, 4], "min_cgpa": 8.5, "eligibility_mode": "strict",
                   "mode": "on_campus", "duration_weeks": 16, "hours_per_week": 10, "deadline": 40},
    "op-robotics": {"positions": 2, "eligible_years": [4], "min_cgpa": None, "eligibility_mode": "advisory",
                    "mode": "on_campus", "duration_weeks": 20, "hours_per_week": 12, "deadline": 25},
    "op-cloud-cost": {"positions": 1, "eligible_years": [], "min_cgpa": None, "eligibility_mode": "advisory",
                      "mode": "remote", "duration_weeks": 8, "hours_per_week": 6, "deadline": -5},
    "op-iot-campus": {"positions": 3, "eligible_years": [2, 3, 4], "min_cgpa": None, "eligibility_mode": "advisory",
                      "mode": "hybrid", "duration_weeks": 10, "hours_per_week": 6, "deadline": 45},
    "op-vision-med": {"positions": 1, "eligible_years": [3, 4], "min_cgpa": 7.5, "eligibility_mode": "advisory",
                      "mode": "hybrid", "duration_weeks": 14, "hours_per_week": 8, "deadline": 35},
    "op-tinyml": {"positions": 2, "eligible_years": [], "min_cgpa": None, "eligibility_mode": "advisory",
                  "mode": "on_campus", "duration_weeks": 12, "hours_per_week": 8, "deadline": 50},
}

PROJECT_POOL = [
    ("Plant disease classifier", "A small CNN that labels leaf photos on a laptop.", ["python", "deep learning"]),
    ("Campus bus tracker", "A web page showing the college buses on a map.", ["javascript", "react"]),
    ("Library catalogue search", "Search over the library's books with filters.", ["databases", "python"]),
    ("Sensor data logger", "An Arduino logger that uploads readings every minute.", ["embedded c", "internet of things"]),
    ("Resume ranking script", "Ranks sample resumes against a job text.", ["python", "machine learning"]),
    ("Study-planner app", "A weekly planner with reminders.", ["react", "node.js"]),
]
HEADLINE_TEMPLATES = [
    "Third-year CSE student interested in {a}",
    "Learning {a} and building small projects",
    "CSE undergraduate curious about {a} and {b}",
]


def build(anchor: dt.date, students: list[dict], assignments: list[tuple[str, str]]) -> dict:
    rng = random.Random(20261012)  # noqa: S311 - synthetic fixtures, not crypto
    allotted = {s for _, s in assignments}
    rows = []
    for index, student in enumerate(students):
        interests = student["interests"] or ["python"]
        skills = [name for name, _ in student["skills"]]
        headline = rng.choice(HEADLINE_TEMPLATES).format(a=interests[0], b=interests[-1])
        row = {
            "user_id": student["user_id"], "programme": "btech", "headline": headline,
            "availability_hours": rng.randint(4, 12), "available_from": (anchor + dt.timedelta(days=7)).isoformat(),
            "preferences": ["research"] if rng.random() < 0.7 else ["research", "tooling"],
            "links": [f"https://github.com/demo-{student['user_id']}"] if rng.random() < 0.35 else [],
            "open_to_opportunities": False, "profile_updated_at": f"{anchor.isoformat()}T08:00:00.000Z",
            "projects": [], "levels": {},
        }
        if student["user_id"] not in allotted:  # no institutional record: their CGPA is self-reported
            row["self_reported_cgpa"] = 8.0 if index % 2 else 7.2
        if student["user_id"] == "u-aarav":
            row["headline"] = "Third-year CSE student building small vision models on cheap hardware"
            row["projects"] = [
                {"title": "Plant disease classifier", "description": "A small CNN that labels leaf photos.",
                 "skills": ["python"], "link": None},
            ]
        elif index % 2 == 0:
            title, description, project_skills = PROJECT_POOL[index % len(PROJECT_POOL)]
            row["projects"] = [{"title": title, "description": description, "skills": project_skills, "link": None}]
        for name in skills:
            row["levels"][name] = rng.choice(["beginner", "intermediate", "advanced"])
        rows.append(row)
    return {"students": rows}


def load(driver, anchor: dt.date, students: list[dict], assignments: list[tuple[str, str]], dept: str) -> dict[str, int]:
    data = build(anchor, students, assignments)
    with driver.session() as db:
        for row in data["students"]:
            props = {k: row[k] for k in ("programme", "headline", "availability_hours", "available_from", "preferences",
                                         "links", "open_to_opportunities", "profile_updated_at")}
            if "self_reported_cgpa" in row:
                props["self_reported_cgpa"] = row["self_reported_cgpa"]
            db.run("MATCH (s:Student {user_id: $sid}) SET s += $props", sid=row["user_id"], props=props).consume()
            db.run(
                """
                MATCH (s:Student {user_id: $sid})
                UNWIND $projects AS p
                CREATE (s)-[:HAS_PROJECT]->(:Project {id: p.id, title: p.title, description: p.description,
                       link: p.link, skills: p.skills, position: p.position})
                """,
                sid=row["user_id"],
                projects=[{**p, "id": str(uuid.uuid4()), "position": i} for i, p in enumerate(row["projects"])],
            ).consume()
            db.run(
                """
                UNWIND $levels AS l
                MATCH (:Student {user_id: $sid})-[h:HAS_SKILL]->(:Concept {name: l.name})
                SET h.level = l.level
                """,
                sid=row["user_id"], levels=[{"name": k, "level": v} for k, v in row["levels"].items()],
            ).consume()

        for fid, f in FACULTY_PROFILES.items():
            db.run("MATCH (u:Faculty {user_id: $fid}) SET u.max_guided_students = $cap, u.accepting_guides = true, "
                   "u.office_hours = $hours", fid=fid, cap=f["max_guided"], hours=f["office_hours"]).consume()
            db.run(
                """
                MATCH (u:Faculty {user_id: $fid})
                UNWIND $areas AS a MATCH (c:Concept {name: a.name}) MERGE (u)-[r:RESEARCHES]->(c) SET r.primary = a.primary
                """,
                fid=fid, areas=[{"name": n, "primary": p} for n, p in f["research"]],
            ).consume()
            db.run(
                "MATCH (u:Faculty {user_id: $fid}) UNWIND $names AS n MATCH (c:Concept {name: n}) MERGE (u)-[:EXPERT_IN]->(c)",
                fid=fid, names=f["expertise"],
            ).consume()
            db.run(
                """
                MATCH (u:Faculty {user_id: $fid})
                UNWIND $courses AS c
                MERGE (k:Course {key: $dept + ':' + c.code}) SET k.code = c.code, k.title = c.title, k.topics = c.topics
                MERGE (u)-[t:TEACHES]->(k) SET t.term_id = '2026-ODD'
                """,
                fid=fid, dept=dept,
                courses=[{"code": c, "title": t, "topics": topics} for c, t, topics in f["courses"]],
            ).consume()
            db.run(
                """
                MATCH (u:Faculty {user_id: $fid})
                UNWIND $q AS x
                CREATE (u)-[:HOLDS]->(:Qualification {id: x.id, degree: x.degree, institution: x.institution,
                       year: x.year, verified: false})
                """,
                fid=fid,
                q=[{"id": str(uuid.uuid4()), "degree": d, "institution": i, "year": y} for d, i, y in f["qualifications"]],
            ).consume()

        for oid, rule in OPENING_RULES.items():
            db.run(
                """
                MATCH (o:Opening {id: $oid})
                SET o.positions = $positions, o.eligible_years = $years, o.min_cgpa = $min_cgpa,
                    o.eligibility_mode = $mode_rule, o.mode = $mode, o.duration_weeks = $weeks,
                    o.hours_per_week = $hours, o.deadline = $deadline
                """,
                oid=oid, positions=rule["positions"], years=rule["eligible_years"], min_cgpa=rule["min_cgpa"],
                mode_rule=rule["eligibility_mode"], mode=rule["mode"], weeks=rule["duration_weeks"],
                hours=rule["hours_per_week"], deadline=(anchor + dt.timedelta(days=rule["deadline"])).isoformat(),
            ).consume()
            if rule.get("preferred"):
                db.run(
                    "MATCH (o:Opening {id: $oid}) UNWIND $names AS n MATCH (c:Concept {name: n}) MERGE (o)-[:PREFERS]->(c)",
                    oid=oid, names=rule["preferred"],
                ).consume()
    return {"profiles": len(data["students"]), "faculty_profiles": len(FACULTY_PROFILES),
            "opening_rules": len(OPENING_RULES)}
