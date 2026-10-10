"""Cypher for faculty profiles (research areas, expertise, subjects taught, qualifications, capacity) and the
topic data behind the guide directory and the HOD's mentor suggestion. Parameterised, one transaction per caller."""
from typing import Any


def _rows(result) -> list[dict[str, Any]]:
    return [record.data() for record in result]


def core(tx, faculty_id: str) -> dict[str, Any] | None:
    record = tx.run(
        """
        MATCH (f:Faculty {user_id: $fid})
        RETURN f.user_id AS user_id, f.name AS name, coalesce(f.designation, '') AS designation,
               f.dept_code AS dept_code, f.employee_id AS employee_id,
               f.max_guided_students AS max_guided_students, coalesce(f.accepting_guides, true) AS accepting_guides,
               f.office_hours AS office_hours, coalesce(f.links, []) AS links,
               coalesce(f.publications, []) AS publications,
               COUNT { (f)-[:MENTORS {type: 'guide', status: 'active'}]->(:Student) } AS guided_students
        """,
        fid=faculty_id,
    ).single()
    return record.data() if record else None


def research_areas(tx, faculty_id: str) -> list[dict[str, Any]]:
    return _rows(
        tx.run(
            """
            MATCH (:Faculty {user_id: $fid})-[r:RESEARCHES]->(c:Concept)
            RETURN c.name AS concept, coalesce(r.primary, false) AS primary
            ORDER BY primary DESC, c.name
            """,
            fid=faculty_id,
        )
    )


def expertise(tx, faculty_id: str) -> list[str]:
    return [
        r["name"]
        for r in tx.run(
            "MATCH (:Faculty {user_id: $fid})-[:EXPERT_IN]->(c:Concept) RETURN c.name AS name ORDER BY c.name",
            fid=faculty_id,
        )
    ]


def courses(tx, faculty_id: str) -> list[dict[str, Any]]:
    return _rows(
        tx.run(
            """
            MATCH (:Faculty {user_id: $fid})-[t:TEACHES]->(c:Course)
            RETURN c.code AS code, c.title AS title, t.term_id AS term_id, coalesce(c.topics, []) AS topics
            ORDER BY c.code
            """,
            fid=faculty_id,
        )
    )


def qualifications(tx, faculty_id: str) -> list[dict[str, Any]]:
    return _rows(
        tx.run(
            """
            MATCH (:Faculty {user_id: $fid})-[:HOLDS]->(q:Qualification)
            RETURN q.degree AS degree, q.institution AS institution, q.year AS year
            ORDER BY q.year DESC, q.degree
            """,
            fid=faculty_id,
        )
    )


def set_props(tx, faculty_id: str, props: dict[str, Any]) -> None:
    if props:
        tx.run("MATCH (f:Faculty {user_id: $fid}) SET f += $props", fid=faculty_id, props=props).consume()


def replace_research_areas(tx, faculty_id: str, items: list[dict[str, Any]]) -> None:
    """Concepts must already exist (the service creates them first). Full-list replacement."""
    tx.run("MATCH (:Faculty {user_id: $fid})-[r:RESEARCHES]->() DELETE r", fid=faculty_id).consume()
    if items:
        tx.run(
            """
            MATCH (f:Faculty {user_id: $fid})
            UNWIND $items AS i
            MATCH (c:Concept {name: i.concept})
            CREATE (f)-[:RESEARCHES {primary: i.primary}]->(c)
            """,
            fid=faculty_id,
            items=items,
        ).consume()


def replace_expertise(tx, faculty_id: str, names: list[str]) -> None:
    tx.run("MATCH (:Faculty {user_id: $fid})-[r:EXPERT_IN]->() DELETE r", fid=faculty_id).consume()
    if names:
        tx.run(
            """
            MATCH (f:Faculty {user_id: $fid})
            UNWIND $names AS n
            MATCH (c:Concept {name: n})
            CREATE (f)-[:EXPERT_IN]->(c)
            """,
            fid=faculty_id,
            names=names,
        ).consume()


def replace_courses(tx, faculty_id: str, dept_code: str, items: list[dict[str, Any]]) -> None:
    tx.run("MATCH (:Faculty {user_id: $fid})-[t:TEACHES]->() DELETE t", fid=faculty_id).consume()
    if items:
        tx.run(
            """
            MATCH (f:Faculty {user_id: $fid})
            UNWIND $items AS i
            MERGE (c:Course {key: $dept + ':' + i.code})
            SET c.code = i.code, c.title = i.title, c.topics = i.topics
            CREATE (f)-[:TEACHES {term_id: i.term_id}]->(c)
            """,
            fid=faculty_id,
            dept=dept_code,
            items=items,
        ).consume()


def replace_qualifications(tx, faculty_id: str, items: list[dict[str, Any]]) -> None:
    tx.run("MATCH (:Faculty {user_id: $fid})-[:HOLDS]->(q:Qualification) DETACH DELETE q", fid=faculty_id).consume()
    if items:
        tx.run(
            """
            MATCH (f:Faculty {user_id: $fid})
            UNWIND $items AS i
            CREATE (f)-[:HOLDS]->(:Qualification {id: i.id, degree: i.degree, institution: i.institution,
                   year: i.year, verified: false})
            """,
            fid=faculty_id,
            items=items,
        ).consume()


def open_openings(tx, faculty_id: str) -> list[dict[str, Any]]:
    return _rows(
        tx.run(
            """
            MATCH (:Faculty {user_id: $fid})-[:POSTED]->(o:Opening {status: 'open'})
            RETURN o.id AS id, o.title AS title ORDER BY o.created_at DESC, o.id
            """,
            fid=faculty_id,
        )
    )


def topics_by_faculty(tx, dept_code: str) -> list[dict[str, Any]]:
    """Per faculty member in the department: capacity and the three kinds of topic (research, expertise, subjects)."""
    return _rows(
        tx.run(
            """
            MATCH (f:Faculty {dept_code: $dept})
            RETURN f.user_id AS user_id, f.name AS name, coalesce(f.designation, '') AS designation,
                   f.max_guided_students AS max_guided_students, coalesce(f.accepting_guides, true) AS accepting_guides,
                   COUNT { (f)-[:MENTORS {type: 'guide', status: 'active'}]->(:Student) } AS guided_students,
                   COUNT { (f)-[:MENTORS {type: 'assigned', status: 'active'}]->(:Student) } AS assigned_mentees,
                   COUNT { (f)-[:POSTED]->(:Opening {status: 'open'}) } AS open_openings,
                   [(f)-[:RESEARCHES]->(c:Concept) | c.name] AS research,
                   [(f)-[:EXPERT_IN]->(c:Concept) | c.name] AS expertise,
                   reduce(all = [], t IN [(f)-[:TEACHES]->(co:Course) | coalesce(co.topics, [])] | all + t) AS subjects
            ORDER BY f.name
            """,
            dept=dept_code,
        )
    )
