"""Create an opening (API-014, REQ-030). Concepts and the opening embedding are P1's (`app.ml.*`); until they exist
this uses the minimal local concept creation and skips the embedding."""
import uuid
from typing import Any

from app.core.clock import utc_now_iso
from app.core.database import run_write
from app.repos import openings_repo, students_repo
from app.schemas.auth import CurrentUser
from app.schemas.generated import OpeningCreate
from app.services.students import ml_module, normalise_skill


def create_opening(user: CurrentUser, body: OpeningCreate) -> dict[str, Any]:
    skills = list(dict.fromkeys(normalise_skill(s.root) for s in body.required_skills if s.root.strip()))
    opening_id = str(uuid.uuid4())

    def write(tx):
        openings_repo.create(
            tx, user.user_id,
            {"id": opening_id, "title": body.title.strip(), "description": body.description, "now": utc_now_iso()},
        )
        concepts = ml_module("concepts")
        for name in skills:
            if concepts is not None and hasattr(concepts, "get_or_create_concept"):
                concepts.get_or_create_concept(tx, name, "claimed")
            else:
                students_repo.ensure_concept(tx, name)
            openings_repo.require_concept(tx, opening_id, name)
        embedding = ml_module("embedding")
        if embedding is not None and hasattr(embedding, "recompute_opening_embedding"):
            embedding.recompute_opening_embedding(tx, opening_id)
        row = openings_repo.get(tx, opening_id)
        return {
            "id": row["id"], "title": row["title"], "description": row["description"],
            "faculty": {"user_id": row["faculty_id"], "name": row["faculty_name"]},
            "required_skills": sorted(row["required_skills"]), "status": row["status"],
            "created_at": row["created_at"], "applicant_count": row["applicant_count"],
        }

    return run_write(write)
