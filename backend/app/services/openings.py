"""Create and edit openings (API-014, API-049; REQ-030). Concepts and the opening embedding are P1's (`app.ml.*`); until
they exist this uses the minimal local concept creation and skips the embedding.

Opening v2 fields (positions, deadline, eligibility rules, mode, duration) are all optional, so an opening written
before they existed behaves as "any year, any CGPA, one position, no deadline".
"""
import uuid
from typing import Any

from app.core.clock import utc_now_iso
from app.core.database import run_write
from app.core.errors import ApiError
from app.repos import openings_repo, students_repo
from app.schemas.auth import CurrentUser
from app.schemas.generated import OpeningCreate, OpeningPatch
from app.services import profile
from app.services.status_history import record_status
from app.services.students import ml_module, normalise_skill

_V2_FIELDS = (
    "positions", "deadline", "eligible_years", "min_cgpa", "allowed_departments", "eligibility_mode", "mode",
    "duration_weeks", "hours_per_week",
)


def _skills(raw) -> list[str]:
    """Normalised, de-duplicated skill names from a list of strings or generated RootModel items."""
    names = [item.root if hasattr(item, "root") else item for item in raw]
    return list(dict.fromkeys(normalise_skill(n) for n in names if n.strip()))


def _v2_props(body: OpeningCreate | OpeningPatch, provided: set[str]) -> dict[str, Any]:
    """The v2 fields the client sent, as stored properties. A sent null clears an optional field."""
    props: dict[str, Any] = {}
    for field in _V2_FIELDS:
        if field not in provided:
            continue
        value = getattr(body, field)
        if hasattr(value, "value"):  # an enum
            value = value.value
        elif hasattr(value, "isoformat"):  # a date
            value = value.isoformat()
        elif field == "eligible_years" and value is not None:
            value = sorted({profile.unwrap(y) for y in value})
        elif field == "allowed_departments" and value is not None:
            value = [profile.unwrap(d).strip().upper() for d in value if profile.unwrap(d).strip()]
        props[field] = value
    return props


def _link_concepts(tx, opening_id: str, names: list[str], link) -> None:
    concepts = ml_module("concepts")
    for name in names:
        if concepts is not None and hasattr(concepts, "get_or_create_concept"):
            concepts.get_or_create_concept(tx, name, "claimed")
        else:
            students_repo.ensure_concept(tx, name)
        link(tx, opening_id, name)


def _recompute_embedding(tx, opening_id: str) -> None:
    embedding = ml_module("embedding")
    if embedding is not None and hasattr(embedding, "recompute_opening_embedding"):
        embedding.recompute_opening_embedding(tx, opening_id)


def shape(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"], "title": row["title"], "description": row["description"],
        "faculty": {"user_id": row["faculty_id"], "name": row["faculty_name"]},
        "required_skills": sorted(row["required_skills"]), "preferred_skills": sorted(row["preferred_skills"]),
        "status": row["status"], "created_at": row["created_at"], "applicant_count": row["applicant_count"],
        "positions": row["positions"], "positions_left": max(0, row["positions"] - row["accepted_count"]),
        "deadline": row["deadline"], "eligible_years": row["eligible_years"], "min_cgpa": row["min_cgpa"],
        "allowed_departments": row["allowed_departments"], "eligibility_mode": row["eligibility_mode"],
        "mode": row["mode"], "duration_weeks": row["duration_weeks"], "hours_per_week": row["hours_per_week"],
    }


def create_opening(user: CurrentUser, body: OpeningCreate) -> dict[str, Any]:
    required = _skills(body.required_skills)
    preferred = [s for s in _skills(body.preferred_skills or []) if s not in required]
    opening_id = str(uuid.uuid4())
    extra = _v2_props(body, body.model_fields_set)

    def write(tx):
        openings_repo.create(
            tx, user.user_id,
            {"id": opening_id, "title": body.title.strip(), "description": body.description, "now": utc_now_iso()},
            extra,
        )
        _link_concepts(tx, opening_id, required, openings_repo.require_concept)
        _link_concepts(tx, opening_id, preferred, openings_repo.prefer_concept)
        _recompute_embedding(tx, opening_id)
        return shape(openings_repo.get(tx, opening_id))

    return run_write(write)


def patch_opening(user: CurrentUser, opening_id: str, body: OpeningPatch) -> dict[str, Any]:
    """API-049. Owner only (404 for anyone else). Skill lists are replaced in full; omitted fields are untouched."""
    provided = body.model_fields_set
    if not provided:
        raise ApiError(
            "VALIDATION_FAILED", 422, "Nothing to update.",
            errors=[{"field": "title", "message": "Send at least one field"}],
        )

    def write(tx):
        current = openings_repo.get(tx, opening_id)
        if current is None or current["faculty_id"] != user.user_id:
            raise ApiError("NOT_FOUND", 404, "The opening was not found.")
        props = _v2_props(body, provided)
        if "title" in provided:
            props["title"] = body.title.strip()
        if "description" in provided:
            props["description"] = body.description
        new_status = body.status.value if "status" in provided and body.status is not None else None
        if new_status is not None and new_status != current["status"]:
            props["status"] = new_status
        openings_repo.set_props(tx, opening_id, props)
        if new_status is not None and new_status != current["status"]:
            record_status(tx, "opening", opening_id, current["status"], new_status, user)

        required = None
        if "required_skills" in provided and body.required_skills is not None:
            required = _skills(body.required_skills)
            openings_repo.clear_requires(tx, opening_id)
            _link_concepts(tx, opening_id, required, openings_repo.require_concept)
        if "preferred_skills" in provided and body.preferred_skills is not None:
            held = set(required if required is not None else current["required_skills"])
            openings_repo.clear_prefers(tx, opening_id)
            _link_concepts(tx, opening_id, [s for s in _skills(body.preferred_skills) if s not in held],
                           openings_repo.prefer_concept)
        if provided & {"title", "description", "required_skills", "preferred_skills"}:
            _recompute_embedding(tx, opening_id)
        return shape(openings_repo.get(tx, opening_id))

    return run_write(write)
