"""Student profile reads and the self-service profile update (REQ-003, REQ-004; API-003 and API-004).

P1 owns concept creation, trust and embeddings (`app.ml.*`). Until those exist this module uses a minimal local path;
when P1's functions are importable they are called as well (they are idempotent and supersede the local result).
"""
import importlib
import re
from types import ModuleType
from typing import Any

from app.core.clock import utc_now_iso
from app.core.database import run_read, run_write
from app.core.errors import ApiError
from app.repos import students_repo
from app.schemas.auth import CurrentUser
from app.schemas.generated import ProfilePatch
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


def update_profile(user: CurrentUser, patch: ProfilePatch) -> dict[str, Any]:
    """API-004. Omitted fields are untouched. `claimed_skills` is the full list of claimed names."""
    provided = patch.model_fields_set
    now = utc_now_iso()

    def write(tx):
        props: dict[str, Any] = {}
        if "bio" in provided:
            props["bio"] = patch.bio
        if "interests" in provided and patch.interests is not None:
            props["interests"] = [item.root.strip() for item in patch.interests if item.root.strip()]
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
        if provided & {"bio", "interests", "claimed_skills"}:
            embedding = ml_module("embedding")
            if embedding is not None and hasattr(embedding, "recompute_student_embedding"):
                embedding.recompute_student_embedding(tx, user.user_id)
        return students_repo.get_profile(tx, user.user_id)

    return run_write(write)
