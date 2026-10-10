"""Synthetic seed loader. [MOCK] - every row here is invented (NG-03).

    python -m scripts.seed --reset [--anchor-date YYYY-MM-DD]

Scope note: this is the match-and-trust slice of backend §10 - departments,
terms, concepts, issuers, users, claimed skills, openings with REQUIRES,
applications, and Aarav's one certified certificate - plus the embedding and
SIMILAR_TO build. Mentoring data (sessions, action items, issues) is not loaded
here; the mentoring features that need it are not part of this slice.

Dates are written as offsets from the anchor (default 2026-10-10) so
`--anchor-date` shifts the whole world and the flags still hold on demo day.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import random
import sys
import uuid

from app.core.database import apply_schema, get_driver, init_driver
from app.core.security import hash_password
from app.ml import concepts as concepts_mod
from app.ml import seed_hooks

SEED_DIR = pathlib.Path(__file__).resolve().parents[1] / "seed"
SCHEMA_PATH = pathlib.Path(__file__).resolve().parents[1] / "schema" / "schema.cypher"
DEMO_PASSWORD = "Demo@123"  # noqa: S105 - the published demo password (AGENTS.md)
DEPT = "CSE"

CONCEPTS = [
    "python", "pytorch", "deep learning", "computer vision", "machine learning",
    "tensorflow", "natural language processing", "edge ai", "internet of things",
    "embedded c", "c", "data structures", "databases", "docker", "react",
    "node.js", "javascript", "public speaking", "technical writing",
    "signal processing", "robotics", "cloud computing",
]

ISSUERS = [
    {"name": "NPTEL", "kind": "mooc",
     "aliases": ["NPTEL Online", "National Programme on Technology Enhanced Learning"]},
    {"name": "Coursera", "kind": "mooc", "aliases": ["Coursera Inc"]},
    {"name": "IEEE", "kind": "other",
     "aliases": ["Institute of Electrical and Electronics Engineers"]},
    {"name": "Smart India Hackathon", "kind": "government", "aliases": ["SIH"]},
    {"name": "Campus Coding Club", "kind": "club", "aliases": ["CCC"]},
    {"name": "Amrita ACM Chapter", "kind": "club", "aliases": ["ACM Amrita"]},
]

FACULTY = [
    ("u-meera", "Dr. Meera Raman", "meera@demo.gurusetu", "EMP001", "Associate Professor"),
    ("u-arjun", "Dr. Arjun Nair", "arjun@demo.gurusetu", "EMP002", "Assistant Professor"),
    ("u-lakshmi", "Dr. Lakshmi Iyer", "lakshmi@demo.gurusetu", "EMP003", "Professor"),
    ("u-vikram", "Dr. Vikram Shetty", "vikram@demo.gurusetu", "EMP004", "Assistant Professor"),
]

STAFF = [
    ("u-suresh", "Dr. Suresh Pillai", "suresh@demo.gurusetu", "hod"),
    ("u-kavya", "Dr. Kavya Menon", "kavya@demo.gurusetu", "iqac"),
]

# 12 openings. op-edge-ai is the demo's opening and its requirements are fixed
# by A-16; the rest give idf something to vary over.
OPENINGS = [
    ("op-edge-ai", "u-meera", "Edge AI for Agriculture",
     "Deploy deep learning models on low-power devices for crop disease detection in "
     "the field. Looking for a student comfortable with Python and PyTorch who wants "
     "to work with real field data from partner farms.",
     ["python", "pytorch", "deep learning", "computer vision"]),
    ("op-nlp-ocr", "u-meera", "NLP for Malayalam OCR",
     "Build a post-correction model for Malayalam optical character recognition on "
     "scanned manuscripts.",
     ["python", "natural language processing", "deep learning"]),
    ("op-iot-campus", "u-meera", "Campus Air Quality Sensor Mesh",
     "A low-cost sensor mesh reporting air quality across campus, with a dashboard.",
     ["embedded c", "internet of things", "python"]),
    ("op-robotics", "u-meera", "Autonomous Lab Trolley",
     "Indoor navigation for a small autonomous trolley moving samples between labs.",
     ["robotics", "computer vision", "python"]),
    ("op-vision-med", "u-arjun", "Retinal Image Screening",
     "Screening model for retinal images, with attention to class imbalance.",
     ["computer vision", "deep learning", "tensorflow"]),
    ("op-db-tuning", "u-arjun", "Query Plan Advisor",
     "A tool that explains slow query plans in teaching databases.",
     ["databases", "python", "data structures"]),
    ("op-cloud-cost", "u-arjun", "Cloud Cost Explainer",
     "Attribute cloud spend to research groups and explain the drivers.",
     ["cloud computing", "docker", "python"]),
    ("op-web-portal", "u-lakshmi", "Department Research Portal",
     "A public portal listing departmental publications and open positions.",
     ["react", "node.js", "javascript"]),
    ("op-signal", "u-lakshmi", "Wearable ECG Denoising",
     "Classical and learned denoising for a low-cost wearable ECG.",
     ["signal processing", "python", "machine learning"]),
    ("op-writing", "u-lakshmi", "Research Communication Assistant",
     "Help the department communicate research to a general audience.",
     ["technical writing", "public speaking"]),
    ("op-tinyml", "u-vikram", "TinyML Keyword Spotting",
     "On-device keyword spotting within a tight memory budget.",
     ["edge ai", "embedded c", "machine learning"]),
    ("op-ds-viz", "u-vikram", "Teaching Visualiser for Data Structures",
     "An interactive visualiser for classic data structures, used in first-year labs.",
     ["data structures", "javascript", "react"]),
]

FIRST_NAMES = [
    "Aarav", "Diya", "Karthik", "Rahul", "Priya", "Ananya", "Vivek", "Sneha",
    "Nikhil", "Ishita", "Rohit", "Meenakshi", "Arun", "Kavitha", "Sanjay",
    "Deepa", "Harish", "Lakshya", "Nandini", "Pranav", "Ritika", "Suhas",
    "Tanvi", "Varun", "Yamini", "Aditya", "Bhavya", "Chirag", "Divya",
    "Esha", "Farhan", "Gauri", "Hemant", "Indu", "Jatin", "Kiran", "Lalit",
    "Manju", "Naveen", "Omkar", "Pooja", "Rakesh", "Shalini", "Tarun",
    "Uma", "Vishal", "Wasim", "Yash", "Zoya", "Neha",
]
LAST_NAMES = [
    "Menon", "Raghavan", "Subramanian", "Pillai", "Krishnan", "Nambiar",
    "Varma", "Shetty", "Kurup", "Bhat",
]

SKILL_POOL = [
    "python", "javascript", "react", "node.js", "databases", "data structures",
    "machine learning", "deep learning", "computer vision", "tensorflow",
    "embedded c", "internet of things", "docker", "cloud computing",
    "public speaking", "signal processing", "robotics", "technical writing",
]


def offset(anchor: dt.date, days: int) -> str:
    return (anchor + dt.timedelta(days=days)).isoformat()


def now_iso() -> str:
    return dt.datetime.now(tz=dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_students(anchor: dt.date) -> list[dict]:
    """50 deterministic students. Aarav is first and is the demo's student, so
    his skills are fixed by A-16: python certified, pytorch and deep learning
    claimed only."""
    rng = random.Random(20261010)  # noqa: S311 - synthetic fixtures, not crypto
    students = []
    for i in range(50):
        first = FIRST_NAMES[i % len(FIRST_NAMES)]
        last = LAST_NAMES[i % len(LAST_NAMES)]
        number = i + 1
        if i == 0:
            user_id, name, email = "u-aarav", "Aarav Menon", "aarav@demo.gurusetu"
            skills = [("python", True), ("pytorch", False), ("deep learning", False)]
            bio = "Third-year CSE student. I build small vision models and like putting them on cheap hardware."
            interests = ["edge ai", "computer vision"]
        else:
            user_id = f"u-s{number:03d}"
            name = f"{first} {last}"
            email = f"{first.lower()}.{last.lower()}{number}@demo.gurusetu"
            picked = rng.sample(SKILL_POOL, rng.randint(2, 5))
            skills = [(s, rng.random() < 0.35) for s in picked]
            bio = f"CSE student interested in {picked[0]}."
            interests = rng.sample(SKILL_POOL, 2)
        students.append({
            "user_id": user_id,
            "name": name,
            "email": email,
            "roll_no": f"CB.EN.U4CSE24{number:03d}",
            "year": 3,
            "enrolled_on": offset(anchor, -820),
            "bio": bio,
            "interests": interests,
            "skills": skills,
        })
    return students


def load_tuning() -> dict:
    path = SEED_DIR / "fit_tuning.json"
    if not path.exists():
        return {"students": {}, "openings": {}}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {
        "students": raw.get("students") or {},
        "openings": raw.get("openings") or {},
    }


def seed(reset: bool, anchor: dt.date) -> dict[str, int]:
    init_driver()
    driver = get_driver()
    students = build_students(anchor)
    tuning = load_tuning()

    with driver.session() as session:
        if reset:
            session.run("MATCH (n) DETACH DELETE n")

    # P2's apply_schema takes the path explicitly (same file the API applies
    # at startup), so a reseed and a boot can never diverge.
    apply_schema(SCHEMA_PATH)

    with driver.session() as session:
        session.run(
            "MERGE (d:Department {code: $code}) SET d.name = $name",
            code=DEPT, name="Computer Science and Engineering",
        )
        for term_id, name, start, end in [
            ("2026-EVEN", "Even semester 2026", -278, -132),
            ("2026-ODD", "Odd semester 2026", -87, 51),
        ]:
            session.run(
                """
                MERGE (t:Term {id: $id})
                SET t.name = $name, t.start_date = $start, t.end_date = $end
                """,
                id=term_id, name=name,
                start=offset(anchor, start), end=offset(anchor, end),
            )

        for issuer in ISSUERS:
            session.run(
                "MERGE (i:Issuer {name: $name}) SET i.aliases = $aliases, i.kind = $kind",
                **issuer,
            )

        for concept in CONCEPTS:
            session.run(
                """
                MERGE (c:Concept {name: $name})
                ON CREATE SET c.source = 'seed'
                """,
                name=concepts_mod.normalise(concept),
            )

        pwd = hash_password(DEMO_PASSWORD)

        for user_id, name, email, role in STAFF:
            session.run(
                """
                MERGE (u:User {user_id: $user_id})
                SET u:Staff, u.name = $name, u.email = $email, u.role = $role,
                    u.password_hash = $pwd, u.dept_code = $dept, u.created_at = $now
                WITH u MATCH (d:Department {code: $dept}) MERGE (u)-[:IN_DEPT]->(d)
                """,
                user_id=user_id, name=name, email=email, role=role,
                pwd=pwd, dept=DEPT, now=now_iso(),
            )

        for user_id, name, email, employee_id, designation in FACULTY:
            session.run(
                """
                MERGE (u:User {user_id: $user_id})
                SET u:Faculty, u.name = $name, u.email = $email, u.role = 'faculty',
                    u.password_hash = $pwd, u.dept_code = $dept,
                    u.employee_id = $employee_id, u.designation = $designation,
                    u.created_at = $now
                WITH u MATCH (d:Department {code: $dept}) MERGE (u)-[:IN_DEPT]->(d)
                """,
                user_id=user_id, name=name, email=email, pwd=pwd, dept=DEPT,
                employee_id=employee_id, designation=designation, now=now_iso(),
            )

        for student in students:
            override = tuning["students"].get(student["user_id"], {})
            bio = override.get("bio", student["bio"])
            interests = override.get("interests", student["interests"])
            session.run(
                """
                MERGE (u:User {user_id: $user_id})
                SET u:Student, u.name = $name, u.email = $email, u.role = 'student',
                    u.password_hash = $pwd, u.dept_code = $dept,
                    u.roll_no = $roll_no, u.year = $year,
                    u.enrolled_on = $enrolled_on, u.bio = $bio,
                    u.interests = $interests, u.created_at = $now
                WITH u MATCH (d:Department {code: $dept}) MERGE (u)-[:IN_DEPT]->(d)
                """,
                user_id=student["user_id"], name=student["name"],
                email=student["email"], pwd=pwd, dept=DEPT,
                roll_no=student["roll_no"], year=student["year"],
                enrolled_on=student["enrolled_on"], bio=bio,
                interests=interests, now=now_iso(),
            )
            for skill, _certified in student["skills"]:
                session.run(
                    """
                    MATCH (s:Student {user_id: $user_id}), (c:Concept {name: $concept})
                    MERGE (s)-[r:HAS_SKILL]->(c)
                    SET r.claimed = true, r.trust_level = 0,
                        r.evidence_ids = coalesce(r.evidence_ids, []),
                        r.endorsed_by = coalesce(r.endorsed_by, []),
                        r.updated_at = $now
                    """,
                    user_id=student["user_id"],
                    concept=concepts_mod.normalise(skill),
                    now=now_iso(),
                )

        # Assigned mentors: 13 / 13 / 12 / 10, two students left unallotted.
        loads = [("u-meera", 13), ("u-arjun", 13), ("u-lakshmi", 12), ("u-vikram", 10)]
        index = 0
        for faculty_id, count in loads:
            for _ in range(count):
                if index >= len(students):
                    break
                session.run(
                    """
                    MATCH (f:Faculty {user_id: $faculty_id}),
                          (s:Student {user_id: $student_id})
                    MERGE (f)-[m:MENTORS {type: 'assigned'}]->(s)
                    SET m.id = $id, m.status = 'active', m.since = $since, m.until = null
                    """,
                    faculty_id=faculty_id, student_id=students[index]["user_id"],
                    id=str(uuid.uuid4()), since=offset(anchor, -120),
                )
                index += 1

        for opening_id, faculty_id, title, description, required in OPENINGS:
            desc = tuning["openings"].get(opening_id, {}).get("description", description)
            session.run(
                """
                MATCH (f:Faculty {user_id: $faculty_id})
                MERGE (o:Opening {id: $id})
                SET o.title = $title, o.description = $description,
                    o.status = 'open', o.created_at = $created_at
                MERGE (f)-[:POSTED]->(o)
                """,
                faculty_id=faculty_id, id=opening_id, title=title,
                description=desc, created_at=offset(anchor, -40) + "T06:30:00Z",
            )
            for concept in required:
                session.run(
                    """
                    MATCH (o:Opening {id: $id}), (c:Concept {name: $concept})
                    MERGE (o)-[:REQUIRES]->(c)
                    """,
                    id=opening_id, concept=concepts_mod.normalise(concept),
                )

        # Three pending applicants on op-edge-ai, none of them Aarav: he applies
        # during the demo (index §7 step 3).
        for student_id in ("u-s004", "u-s009", "u-s014"):
            session.run(
                """
                MATCH (s:Student {user_id: $student_id}), (o:Opening {id: 'op-edge-ai'})
                MERGE (s)-[a:APPLIED_TO]->(o)
                SET a.id = $id, a.status = 'pending',
                    a.applied_at = $at, a.updated_at = $at
                """,
                student_id=student_id, id=str(uuid.uuid4()),
                at=offset(anchor, -9) + "T04:00:00Z",
            )

        # Aarav's one seeded certificate: it is what makes python `matched` and
        # everything else `claimed_only` at the start of the demo.
        session.run(
            """
            MATCH (s:Student {user_id: 'u-aarav'}), (c:Concept {name: 'python'})
            MERGE (e:Evidence {id: 'ev-aarav-python'})
            SET e.kind = 'certificate', e.status = 'certified',
                e.file_path = '/data/uploads/seeded-aarav-python.png',
                e.media_type = 'image/png', e.size_bytes = 148000,
                e.sha256 = $sha, e.phash = null,
                e.holder_name = 'Aarav Menon', e.title = 'Python for Everybody',
                e.issuer = 'Coursera', e.issue_date = $issued,
                e.level = 'online', e.type = 'course',
                e.skills = ['python'], e.contains_instructions = false,
                e.confidence = 1.0, e.reasons = [], e.source = 'cache',
                e.created_at = $now, e.updated_at = $now
            MERGE (s)-[:SUBMITTED]->(e)
            MERGE (e)-[:PROVES]->(c)
            WITH s, c MATCH (s)-[r:HAS_SKILL]->(c)
            SET r.trust_level = 1, r.evidence_ids = ['ev-aarav-python'],
                r.updated_at = $now
            """,
            sha="a" * 64, issued=offset(anchor, -178), now=now_iso(),
        )

    # Embeddings and SIMILAR_TO last: they read the rows written above.
    concepts_mod.reload_files()
    with driver.session() as session:
        sim_stats = session.execute_write(seed_hooks.seed_similarity)
        emb_stats = session.execute_write(seed_hooks.seed_embeddings)

    return {
        "students": len(students),
        "faculty": len(FACULTY),
        "staff": len(STAFF),
        "openings": len(OPENINGS),
        "concepts": sim_stats["concepts"],
        "similar_edges": sim_stats["model_edges"] + sim_stats["override_edges"],
        "embeddings": emb_stats["students"] + emb_stats["openings"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true", help="delete all nodes first")
    parser.add_argument("--anchor-date", default="2026-10-10")
    args = parser.parse_args(argv)

    anchor = dt.date.fromisoformat(args.anchor_date)
    stats = seed(reset=args.reset, anchor=anchor)
    print("Seeded:", f"{stats['students'] + stats['faculty'] + stats['staff']} users")
    for key, value in stats.items():
        print(f"  {key:<16} {value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
