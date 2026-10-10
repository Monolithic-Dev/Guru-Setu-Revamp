"""The student's own full profile (API-048): extra fields, trust labels, projects, resume and a completeness meter.

Trust rule (plan section 6): a typed value is a CLAIM. Self-reported CGPA and self-assessed skill levels are labelled
as such and never change a trust level; only certificates, endorsements and the institutional record count as proof.
"""
import re
from typing import Any

from app.core.database import run_read
from app.core.errors import ApiError
from app.repos import profile_repo
from app.schemas.auth import CurrentUser
from app.services import terms

MAX_LINKS = 5
MAX_LINK_LENGTH = 200
SKILLS_FOR_COMPLETE = 3
_HTTPS = re.compile(r"^https://[^\s/$.?#][^\s]*$", re.IGNORECASE)


def unwrap(item):
    """Constrained string items come from the generated models wrapped in a small root type; plain strings pass."""
    return item.root if hasattr(item, "root") else item


def clean_links(links: list, field: str = "links") -> list[str]:
    """https URLs only (a `javascript:` or `http:` link is refused), trimmed, de-duplicated, at most five."""
    out: list[str] = []
    for index, raw in enumerate(links):
        link = unwrap(raw).strip()
        if len(link) > MAX_LINK_LENGTH or not _HTTPS.match(link):
            raise ApiError(
                "VALIDATION_FAILED", 422, "Links must be https URLs.",
                errors=[{"field": f"{field}.{index}", "message": "Use a full https:// link of at most 200 characters"}],
            )
        if link not in out:
            out.append(link)
    if len(out) > MAX_LINKS:
        raise ApiError(
            "VALIDATION_FAILED", 422, "Too many links.", errors=[{"field": field, "message": f"At most {MAX_LINKS}"}]
        )
    return out


def cgpa_view(
    records: list[dict[str, Any]], self_reported: float | None, current_term_id: str | None
) -> dict[str, Any]:
    """The record wins; the self-reported value is the fallback and is always reported as such."""
    record = next((r for r in records if r["term_id"] == current_term_id), records[0] if records else None)
    if record is not None:
        effective, source = float(record["cgpa"]), "record"
    elif self_reported is not None:
        effective, source = float(self_reported), "self_reported"
    else:
        effective, source = None, "unknown"
    return {
        "record": float(record["cgpa"]) if record else None,
        "record_term": record["term_id"] if record else None,
        "self_reported": float(self_reported) if self_reported is not None else None,
        "effective": effective,
        "source": source,
    }


def completeness(
    core: dict[str, Any], skills: list[dict], certified: int, projects: list, resume: Any
) -> dict[str, Any]:
    """Seven equal items, no AI. `next_action` names the first thing left to do."""
    items = [
        (
            "basics", "Add your programme, a headline and a short bio",
            bool(core["programme"] and core["headline"] and core["bio"]),
        ),
        ("skills", f"Add at least {SKILLS_FOR_COMPLETE} skills", len(skills) >= SKILLS_FOR_COMPLETE),
        ("certificate", "Upload a certificate to verify one skill", certified >= 1),
        ("project", "Add a project", len(projects) >= 1),
        ("resume", "Upload your resume", resume is not None),
        ("availability", "Say how many hours a week you can give", core["availability_hours"] is not None),
        ("interests", "Add at least one interest", len(core["interests"]) >= 1),
    ]
    done = sum(1 for _, _, ok in items if ok)
    return {
        "percent": round(100 * done / len(items)),
        "items": [{"key": k, "label": label, "done": ok} for k, label, ok in items],
        "next_action": next((label for _, label, ok in items if not ok), None),
    }


def _resume_info(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {k: row[k] for k in ("id", "uploaded_at", "size_bytes", "pages", "status")}


def read_profile(tx, student_id: str) -> dict[str, Any]:
    core = profile_repo.student_core(tx, student_id)
    if core is None:
        raise ApiError("NOT_FOUND", 404, "The student was not found.")
    current_term = terms.resolve(tx)[0]
    skills = profile_repo.skill_rows(tx, student_id)
    projects = profile_repo.projects(tx, student_id)
    resume = profile_repo.current_resume(tx, student_id)
    certified = profile_repo.certified_count(tx, student_id)
    return {
        "user_id": core["user_id"],
        "name": core["name"],
        "roll_no": core["roll_no"],
        "dept_code": core["dept_code"],
        "programme": core["programme"],
        "year": core["year"],
        "headline": core["headline"],
        "bio": core["bio"],
        "interests": core["interests"],
        "links": core["links"],
        "availability_hours": core["availability_hours"],
        "available_from": core["available_from"],
        "preferences": core["preferences"],
        "open_to_opportunities": core["open_to_opportunities"],
        "cgpa": cgpa_view(profile_repo.academic_records(tx, student_id), core["self_reported_cgpa"],
                          current_term["id"] if current_term else None),
        "skills": [
            {k: v for k, v in row.items() if v is not None or k != "level"} for row in skills
        ],
        "projects": [{k: p[k] for k in ("id", "title", "description", "link", "skills")} for p in projects],
        "resume": _resume_info(resume),
        "certificates_certified": certified,
        "completeness": completeness(core, skills, certified, projects, resume),
    }


def my_profile(user: CurrentUser) -> dict[str, Any]:
    return run_read(lambda tx: read_profile(tx, user.user_id))
