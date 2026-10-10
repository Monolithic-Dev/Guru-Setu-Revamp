"""Project completion record (REQ-040): when a guide marks guided work completed, they vouch for what was done and
which skills it showed. The record is Evidence (so it shows in the achievements export and click-to-source) that is
already `certified` by a named human, and each vouched skill gets that guide as an endorser, so it reads
"Faculty-verified" with their name. Nothing here asks a model anything.
"""
from typing import Any

from app.core.clock import today, utc_now_iso
from app.core.errors import ApiError
from app.repos import certificates_repo, mentorship_repo
from app.schemas.auth import CurrentUser
from app.services.notify import notify, render_title
from app.services.status_history import record_status
from app.services.students import normalise_skill


def _invalid(message: str, field: str = "completion") -> ApiError:
    return ApiError("VALIDATION_FAILED", 422, message, errors=[{"field": field, "message": message}])


def vouched_skills(tx, student_id: str, required: list[str], asked: list[str]) -> list[str]:
    """The guide can vouch only for skills the opening required or the student already lists, so a record never
    invents a skill out of thin air."""
    allowed = {normalise_skill(s) for s in required} | certificates_repo.student_skill_names(tx, student_id)
    skills = list(dict.fromkeys(normalise_skill(s) for s in asked))
    unknown = [s for s in skills if s not in allowed]
    if unknown:
        raise _invalid(f"Not a skill of this opening or of the student: {', '.join(unknown)}", "completion.skills")
    return skills


def record(tx, guide: CurrentUser, application: dict[str, Any], opening: dict[str, Any], completion) -> str:
    """Write the record, link the skills it proves, endorse them by the guide, notify the student. The caller's
    transaction commits this together with the application's move to `completed`."""
    from app.ml import embedding, trust  # P1's package; imported here so the services layer loads without it

    student_id = application["student_id"]
    asked = [x.root if hasattr(x, "root") else str(x) for x in completion.skills]  # generated models wrap each skill
    skills = vouched_skills(tx, student_id, opening["required_skills"], asked)
    evidence_id = f"proj-{application['id']}"
    now = utc_now_iso()
    name = mentorship_repo.student_names(tx, [student_id]).get(student_id, "")
    certificates_repo.create(tx, student_id, {
        "id": evidence_id, "kind": "project_record", "status": "certified", "source": "guide",
        "title": application["opening_title"], "holder_name": name, "issuer": f"{guide.name} ({guide.dept_code})",
        "issue_date": today().isoformat(), "level": "college", "type": "project", "skills": skills,
        "summary": completion.summary.strip(), "output_type": completion.output_type.value,
        "recorded_by": guide.name, "reviewed_by": guide.user_id, "reasons": [], "application_id": application["id"],
        "created_at": now, "updated_at": now,
    })
    canonical = trust.apply_certified(tx, student_id, evidence_id, skills)
    from app.repos import ml_repo

    for concept in canonical:
        endorsed = list((ml_repo.get_has_skill(tx, student_id, concept) or {}).get("endorsed_by") or [])
        if guide.user_id not in endorsed:
            ml_repo.set_endorsed_by(tx, student_id, concept, [*endorsed, guide.user_id])
        trust.recompute_skill(tx, student_id, concept, recompute_embedding=False)
    embedding.recompute_student_embedding(tx, student_id)
    record_status(tx, "evidence", evidence_id, None, "certified", guide, note="project completion")
    notify(
        tx, student_id, "project_recorded",
        render_title("project_recorded", faculty=guide.name, opening=application["opening_title"]),
        link="/student/certificates",
    )
    return evidence_id
