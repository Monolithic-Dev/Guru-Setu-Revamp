"""Faculty profile (API-052, API-053), the guide directory (API-058) and the HOD's mentor suggestion (plan sections 4.5,
4.7 and 5). Lists are saved by replacement ("send the full list"): the project has no DELETE routes.

Topic overlap between a student and a faculty member uses three kinds of faculty topic, strongest first: research areas
(1.0), expertise (0.7) and subjects taught (0.5). The weights only ORDER the directory; no score is ever returned, so it
cannot become a leaderboard (NG-11).
"""
import uuid
from typing import Any

from app.core.database import run_read, run_write
from app.core.errors import ApiError
from app.repos import faculty_repo, match_repo, openings_repo, profile_repo, students_repo
from app.schemas.auth import CurrentUser
from app.schemas.generated import FacultyProfilePatch
from app.services import profile, track_record
from app.services.students import ml_module, normalise_skill

WEIGHTS = {"research": 1.0, "expertise": 0.7, "subjects": 0.5}
SIM_MIN = 0.60  # same cut-off as the fit scorer's SIM_MIN for "near" skills


def _clean(names: list) -> list[str]:
    plain = [profile.unwrap(n) for n in names]
    return list(dict.fromkeys(normalise_skill(n) for n in plain if n.strip()))


def _ensure_concepts(tx, names: list[str]) -> None:
    concepts = ml_module("concepts")
    for name in names:
        if concepts is not None and hasattr(concepts, "get_or_create_concept"):
            concepts.get_or_create_concept(tx, name, "claimed")
        else:
            students_repo.ensure_concept(tx, name)


def read_profile(tx, faculty_id: str) -> dict[str, Any]:
    core = faculty_repo.core(tx, faculty_id)
    if core is None:
        raise ApiError("NOT_FOUND", 404, "The faculty member was not found.")
    return {
        **core,
        "research_areas": faculty_repo.research_areas(tx, faculty_id),
        "expertise": faculty_repo.expertise(tx, faculty_id),
        "courses": faculty_repo.courses(tx, faculty_id),
        "qualifications": faculty_repo.qualifications(tx, faculty_id),
    }


def my_profile(user: CurrentUser) -> dict[str, Any]:
    return run_read(lambda tx: read_profile(tx, user.user_id))


def update_profile(user: CurrentUser, patch: FacultyProfilePatch) -> dict[str, Any]:
    provided = patch.model_fields_set
    if not provided:
        raise ApiError(
            "VALIDATION_FAILED", 422, "Nothing to update.",
            errors=[{"field": "research_areas", "message": "Send a field"}],
        )
    links = profile.clean_links(patch.links, "links") if "links" in provided and patch.links is not None else None

    def write(tx):
        core = faculty_repo.core(tx, user.user_id)
        props: dict[str, Any] = {}
        if "max_guided_students" in provided:
            props["max_guided_students"] = patch.max_guided_students
        if "accepting_guides" in provided and patch.accepting_guides is not None:
            props["accepting_guides"] = patch.accepting_guides
        if "office_hours" in provided:
            props["office_hours"] = (patch.office_hours or "").strip() or None
        if links is not None:
            props["links"] = links
        if "publications" in provided and patch.publications is not None:
            props["publications"] = list(
                dict.fromkeys(profile.unwrap(p).strip() for p in patch.publications if profile.unwrap(p).strip())
            )
        faculty_repo.set_props(tx, user.user_id, props)

        if "research_areas" in provided and patch.research_areas is not None:
            seen: dict[str, bool] = {}
            for area in patch.research_areas:
                name = normalise_skill(area.concept)
                seen[name] = seen.get(name, False) or bool(area.primary)
            primaries = [n for n, p in seen.items() if p]
            if len(primaries) > 1:
                raise ApiError(
                    "VALIDATION_FAILED", 422, "Only one research area can be primary.",
                    errors=[{"field": "research_areas", "message": "Mark one primary area at most"}],
                )
            _ensure_concepts(tx, list(seen))
            areas = [{"concept": n, "primary": p} for n, p in seen.items()]
            faculty_repo.replace_research_areas(tx, user.user_id, areas)
        if "expertise" in provided and patch.expertise is not None:
            names = _clean(patch.expertise)
            _ensure_concepts(tx, names)
            faculty_repo.replace_expertise(tx, user.user_id, names)
        if "courses" in provided and patch.courses is not None:
            codes = [c.code.strip().upper() for c in patch.courses]
            if len(set(codes)) != len(codes):
                raise ApiError(
                    "VALIDATION_FAILED", 422, "Each course code can appear once.",
                    errors=[{"field": "courses", "message": "Duplicate course code"}],
                )
            faculty_repo.replace_courses(
                tx, user.user_id, core["dept_code"],
                [
                    {"code": c.code.strip().upper(), "title": c.title.strip(), "term_id": c.term_id,
                     "topics": _clean(c.topics or [])}
                    for c in patch.courses
                ],
            )
        if "qualifications" in provided and patch.qualifications is not None:
            faculty_repo.replace_qualifications(
                tx, user.user_id,
                [{"id": str(uuid.uuid4()), "degree": q.degree.strip(), "institution": q.institution.strip(),
                  "year": q.year} for q in patch.qualifications],
            )
        if provided & {"research_areas", "expertise", "courses"}:
            # The faculty member's domain is part of every opening's text (plan section 4.3).
            embedding = ml_module("embedding")
            if embedding is not None and hasattr(embedding, "recompute_opening_embedding"):
                for row in openings_repo.rows(tx, include_closed=True, limit=200):
                    if row["faculty_id"] == user.user_id:
                        embedding.recompute_opening_embedding(tx, row["id"])
        return read_profile(tx, user.user_id)

    return run_write(write)


def public_profile(faculty_id: str) -> dict[str, Any]:
    def read(tx):
        return {
            "profile": read_profile(tx, faculty_id),
            "open_openings": faculty_repo.open_openings(tx, faculty_id),
        }

    out = run_read(read)
    out["track_record"] = track_record.track_record(faculty_id)
    return out


# ---- topic overlap --------------------------------------------------------------------------------------------------


def _expand(tx, terms: set[str]) -> dict[str, str]:
    """{term: the student topic it came from}: each topic plus the concepts similar to it (similarity >= SIM_MIN)."""
    out = {t: t for t in terms}
    for (a, b), score in match_repo.similar_pairs(tx, sorted(terms)).items():
        if score >= SIM_MIN:
            out.setdefault(a, b)
    return out


def _overlap(faculty: dict[str, Any], expanded: dict[str, str]) -> tuple[float, list[str]]:
    """(weight used only for ordering, the shared topics in the faculty member's own words)."""
    weight, shared = 0.0, []
    for kind, key in (("research", "research"), ("expertise", "expertise"), ("subjects", "subjects")):
        for topic in faculty[key]:
            if topic in expanded:
                weight += WEIGHTS[kind]
                if topic not in shared:
                    shared.append(topic)
    return weight, shared


def _student_topics(tx, student_id: str) -> set[str]:
    core = profile_repo.student_core(tx, student_id)
    return {s["concept"] for s in profile_repo.skill_rows(tx, student_id)} | {
        normalise_skill(i) for i in (core["interests"] if core else [])
    }


def directory(user: CurrentUser, query: str | None, accepting: bool | None) -> list[dict[str, Any]]:
    """API-058. Faculty of the student's department ordered by shared topics; no score is returned."""

    def read(tx):
        core = profile_repo.student_core(tx, user.user_id)
        expanded = _expand(tx, _student_topics(tx, user.user_id))
        cards = []
        for f in faculty_repo.topics_by_faculty(tx, core["dept_code"]):
            if accepting is not None and f["accepting_guides"] != accepting:
                continue
            haystack = " ".join([f["name"], *f["research"], *f["expertise"], *f["subjects"]]).lower()
            if query and query.strip().lower() not in haystack:
                continue
            weight, shared = _overlap(f, expanded)
            cards.append((weight, f, shared))
        cards.sort(key=lambda c: (-c[0], -c[1]["open_openings"], c[1]["name"]))
        return [
            {
                "user_id": f["user_id"], "name": f["name"], "designation": f["designation"],
                "research_areas": f["research"], "shared_topics": shared, "open_openings": f["open_openings"],
                "accepting_guides": f["accepting_guides"], "guided_students": f["guided_students"],
                "max_guided_students": f["max_guided_students"],
            }
            for _w, f, shared in cards[:50]
        ]

    return run_read(read)


def suggest_mentors(tx, student_ids: list[str], dept_code: str, load_limit: int) -> dict[str, dict[str, str]]:
    """The HOD's assistive suggestion per unallotted student: a mentor under the load limit with the most shared
    topics (ties go to the lighter load). The HOD still decides; nothing is assigned."""
    mentors = [m for m in faculty_repo.topics_by_faculty(tx, dept_code) if m["assigned_mentees"] < load_limit]
    out: dict[str, dict[str, str]] = {}
    if not mentors:
        return out
    for sid in student_ids:
        expanded = _expand(tx, _student_topics(tx, sid))
        ranked = sorted(
            ((*_overlap(m, expanded), m) for m in mentors),
            key=lambda t: (-t[0], t[2]["assigned_mentees"], t[2]["name"]),
        )
        weight, shared, best = ranked[0]
        reason = (
            f"shares {', '.join(shared[:3])}; load {best['assigned_mentees']} of {load_limit}"
            if shared
            else f"lowest load ({best['assigned_mentees']} of {load_limit}); no shared topics yet"
        )
        out[sid] = {"mentor_id": best["user_id"], "name": best["name"], "reason": reason}
    return out
