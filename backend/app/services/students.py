"""Student profile reads and the self-service profile update (REQ-003, REQ-004; API-003 and API-004).

P1 owns concept creation, trust and embeddings (`app.ml.*`). Until those exist this module uses a minimal local path;
when P1's functions are importable they are called as well (they are idempotent and supersede the local result).
"""
import importlib
import re
import uuid
from types import ModuleType
from typing import Any

from app.core.clock import utc_now_iso
from app.core.database import run_read, run_write
from app.core.errors import ApiError
from app.repos import profile_repo, students_repo
from app.schemas.auth import CurrentUser
from app.schemas.generated import ProfilePatch
from app.services import profile
from app.services.access import assert_self_or_scope


def ml_module(name: str) -> ModuleType | None:
    """P1's module `app.ml.<name>`, or None while it is missing or its dependencies are not installed."""
    try:
        return importlib.import_module(f"app.ml.{name}")
    except ImportError:
        return None


def normalise_skill(name: str) -> str:
    """Lower-case, trim, collapse spaces. P1's `ml.concepts.normalise` (which also applies aliases) wins if present."""
    concepts = ml_module("concepts")
    if concepts is not None and hasattr(concepts, "normalise"):
        return concepts.normalise(name)
    return re.sub(r"\s+", " ", name.strip().lower())


def get_profile(user: CurrentUser, student_id: str) -> dict[str, Any]:
    """API-003. Scope: self, mentor/guide, faculty the student applied to, HOD of the department."""

    def read(tx):
        assert_self_or_scope(tx, user, student_id)
        profile = students_repo.get_profile(tx, student_id)
        if profile is None:
            raise ApiError("NOT_FOUND", 404, "The student was not found.")
        return profile

    return run_read(read)


_SIMPLE_FIELDS = ("headline", "self_reported_cgpa", "availability_hours", "available_from", "open_to_opportunities")
_EMBEDDING_FIELDS = {"bio", "interests", "claimed_skills", "programme", "year", "headline", "projects"}


def _extras(patch: ProfilePatch, provided: set[str]) -> dict[str, Any]:
    """The new profile fields as stored properties. A field the client did not send is left alone; a sent null clears
    it. Typed values are claims: nothing here touches a trust level."""
    props: dict[str, Any] = {}
    for field in _SIMPLE_FIELDS:
        if field in provided:
            value = getattr(patch, field)
            props[field] = value.isoformat() if hasattr(value, "isoformat") else value
    if "headline" in props and props["headline"] is not None:
        props["headline"] = props["headline"].strip() or None
    if "programme" in provided:
        props["programme"] = patch.programme.value if patch.programme else None
    if "year" in provided and patch.year is not None:  # the year is never cleared, only changed
        props["year"] = patch.year
    if "links" in provided and patch.links is not None:
        props["links"] = profile.clean_links(patch.links)
    if "preferences" in provided and patch.preferences is not None:
        props["preferences"] = list(
            dict.fromkeys(profile.unwrap(p).strip().lower() for p in patch.preferences if profile.unwrap(p).strip())
        )
    return props


def update_profile(user: CurrentUser, patch: ProfilePatch) -> dict[str, Any]:
    """API-004 and API-046. Omitted fields are untouched. `claimed_skills` is the full list of claimed names and
    `projects` the full list of projects (there are no DELETE routes)."""
    provided = patch.model_fields_set
    now = utc_now_iso()
    props_extra = _extras(patch, provided)  # validates links before anything is written

    def write(tx):
        props: dict[str, Any] = dict(props_extra)
        if "bio" in provided:
            props["bio"] = patch.bio
        if "interests" in provided and patch.interests is not None:
            props["interests"] = [item.root.strip() for item in patch.interests if item.root.strip()]
        if props:
            props["profile_updated_at"] = now
        students_repo.set_profile_fields(tx, user.user_id, props)

        if "claimed_skills" in provided and patch.claimed_skills is not None:
            wanted = sorted({normalise_skill(skill.root) for skill in patch.claimed_skills if skill.root.strip()})
            current = set(students_repo.claimed_skill_names(tx, user.user_id))
            concepts = ml_module("concepts")
            for name in wanted:
                if concepts is not None and hasattr(concepts, "get_or_create_concept"):
                    concepts.get_or_create_concept(tx, name, "claimed")
                else:
                    students_repo.ensure_concept(tx, name)
                students_repo.upsert_claim(tx, user.user_id, name, now)
            trust = ml_module("trust")
            for name in sorted(current - set(wanted)):
                students_repo.unclaim(tx, user.user_id, name, now)
                if trust is not None and hasattr(trust, "recompute_skill"):
                    trust.recompute_skill(tx, user.user_id, name)  # full trust ladder (P1)

        if "projects" in provided and patch.projects is not None:
            items = []
            for index, project in enumerate(patch.projects):
                project_skills = [profile.unwrap(x) for x in (project.skills or [])]
                link = profile.clean_links([project.link], f"projects.{index}.link")[0] if project.link else None
                items.append({
                    "id": str(uuid.uuid4()), "title": project.title.strip(), "position": index, "link": link,
                    "description": (project.description or "").strip() or None,
                    "skills": list(dict.fromkeys(normalise_skill(n) for n in project_skills if n.strip())),
                })
            profile_repo.replace_projects(tx, user.user_id, items)

        if "skill_levels" in provided and patch.skill_levels is not None:
            held = {row["concept"] for row in profile_repo.skill_rows(tx, user.user_id)}
            levels: dict[str, str | None] = {}
            for name, level in patch.skill_levels.items():
                key = normalise_skill(name)
                if key not in held:
                    raise ApiError(
                        "VALIDATION_FAILED", 422, "A level can only be set on a skill you have.",
                        errors=[{"field": f"skill_levels.{name}", "message": "Add the skill first"}],
                    )
                levels[key] = level.value
            profile_repo.set_skill_levels(tx, user.user_id, levels)

        if provided & _EMBEDDING_FIELDS:
            embedding = ml_module("embedding")
            if embedding is not None and hasattr(embedding, "recompute_student_embedding"):
                embedding.recompute_student_embedding(tx, user.user_id)
        return students_repo.get_profile(tx, user.user_id)

    return run_write(write)


def search_concepts(query: str) -> list[dict[str, Any]]:
    """API-047 typeahead: concept names containing the text, plus concepts reached through an alias (max 10)."""
    needle = re.sub(r"\s+", " ", query.strip().lower())

    def read(tx):
        names = profile_repo.search_concepts(tx, needle, 10)
        out = [{"name": n, "matched_alias": None} for n in names]
        if needle and len(out) < 10:
            concepts = ml_module("concepts")
            aliases = getattr(concepts, "_aliases", None)
            if callable(aliases):
                seen = {o["name"] for o in out}
                known = profile_repo.concept_names_known(tx, sorted(set(aliases().values())))
                for alias, canonical in sorted(aliases().items()):
                    if needle in alias and canonical in known and canonical not in seen and len(out) < 10:
                        out.append({"name": canonical, "matched_alias": alias})
                        seen.add(canonical)
        return out

    return run_read(read)
