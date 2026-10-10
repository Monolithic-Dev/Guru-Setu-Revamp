"""Resume (API-055/056/057, plan section 8): one current PDF per student, privately stored, scoped download, and a
no-AI skill suggestion step.

Rules that never bend:
  * a PDF only (magic bytes), at most MAX_RESUME_MB and MAX_RESUME_PAGES, stored as UPLOAD_DIR/resumes/<uuid>.pdf, never
    served publicly, and a newer upload SUPERSEDES the old one (kept, marked `superseded`; there is no DELETE);
  * the file is visible to the student, their mentors, their HOD, and faculty the student applied to; never to IQAC and
    never to other faculty (404, so existence does not leak);
  * suggestions are read from the PDF's own text layer in memory; the text is never logged or stored; and a suggestion
    becomes a CLAIMED skill (trust 0) only after the student confirms it. A resume never certifies anything.
"""
import hashlib
import importlib
import os
import re
import uuid
from pathlib import Path
from typing import Any, BinaryIO

from app.core.clock import utc_now_iso
from app.core.config import get_settings
from app.core.database import run_read, run_write
from app.core.errors import ApiError
from app.core.ratelimit import RateLimiter
from app.repos import profile_repo, scope_repo
from app.schemas.auth import CurrentUser
from app.schemas.generated import ProfilePatch
from app.services import certificates, profile, students
from app.services.students import ml_module

MAX_CLAIMED = 30
MIN_TOKEN = 2  # one-letter concept names ("c") would match every stray letter
_limiter: RateLimiter | None = None


def _upload_limiter() -> RateLimiter:
    global _limiter
    if _limiter is None:
        _limiter = RateLimiter(get_settings().resume_rate_limit_per_hour, 3600)
    return _limiter


def reset_limiter() -> None:
    if _limiter is not None:
        _limiter.reset()


def _info(row: dict[str, Any]) -> dict[str, Any]:
    return {k: row[k] for k in ("id", "uploaded_at", "size_bytes", "pages", "status")}


def intake(user: CurrentUser, upload: BinaryIO) -> dict[str, Any]:
    """API-055 upload. Same safeguards as certificates, PDF only."""
    _upload_limiter().check(user.user_id)
    cfg = get_settings()
    directory = Path(cfg.upload_dir) / "resumes"
    directory.mkdir(parents=True, exist_ok=True)
    head = upload.read(16)
    if not head.startswith(b"%PDF-"):
        raise ApiError("UNSUPPORTED_FILE_TYPE", 415, "Upload your resume as a PDF file.")

    resume_id = str(uuid.uuid4())
    temp, final = directory / f".tmp-{resume_id}", directory / f"{resume_id}.pdf"
    digest, size = hashlib.sha256(), 0
    try:
        with temp.open("wb") as out:
            chunk = head
            while chunk:
                size += len(chunk)
                if size > cfg.max_resume_bytes:
                    raise ApiError("FILE_TOO_LARGE", 413, f"The resume is larger than {cfg.max_resume_mb} MB.")
                digest.update(chunk)
                out.write(chunk)
                chunk = upload.read(1024 * 1024)
        pages = certificates.pdf_page_count(temp)
        if pages > cfg.max_resume_pages:
            raise ApiError(
                "VALIDATION_FAILED", 422, f"The resume has more than {cfg.max_resume_pages} pages.",
                errors=[{"field": "file", "message": f"At most {cfg.max_resume_pages} pages"}],
            )
        os.replace(temp, final)
    except BaseException:
        temp.unlink(missing_ok=True)
        raise

    row = {
        "id": resume_id, "file_path": str(final), "sha256": digest.hexdigest(), "size_bytes": size,
        "pages": max(1, pages), "uploaded_at": utc_now_iso(),
    }

    def write(tx):
        profile_repo.add_resume(tx, user.user_id, row)
        return {**_info({**row, "status": "current"})}

    try:
        return run_write(write)
    except BaseException:
        final.unlink(missing_ok=True)
        raise


def my_resume(user: CurrentUser) -> dict[str, Any]:
    row = run_read(lambda tx: profile_repo.current_resume(tx, user.user_id))
    if row is None:
        raise ApiError("NOT_FOUND", 404, "You have not uploaded a resume.")
    return _info(row)


def file_for(user: CurrentUser, student_id: str) -> Path:
    """API-056. 404 unless the caller is in the scope above (the role check, IQAC 403, happens in the route)."""

    def read(tx):
        if user.role == "student":
            allowed = user.user_id == student_id
        elif user.role == "faculty":
            allowed = scope_repo.is_mentor_of(tx, user.user_id, student_id) or scope_repo.is_applicant_of_own(
                tx, user.user_id, student_id
            )
        else:
            allowed = scope_repo.is_dept_hod_of(tx, user.user_id, student_id)
        return profile_repo.current_resume(tx, student_id) if allowed else None

    row = run_read(read)
    if row is None:
        raise ApiError("NOT_FOUND", 404, "The resume was not found.")
    path = Path(row["file_path"]).resolve()
    if (Path(get_settings().upload_dir) / "resumes").resolve() not in path.parents or not path.is_file():
        raise ApiError("NOT_FOUND", 404, "The resume was not found.")
    return path


# ---- suggestions (no AI) -------------------------------------------------------------------------------------


def _text_of(path: Path) -> str | None:
    """The PDF's text layer, in memory only. None when the PDF has no text (an image-only scan)."""
    try:
        pdfium = importlib.import_module("pypdfium2")
    except ImportError:
        return None
    document = pdfium.PdfDocument(str(path))
    try:
        parts = [document[i].get_textpage().get_text_range() for i in range(len(document))]
    finally:
        document.close()
    text = " ".join(parts).strip()
    return text or None


def _vocabulary(tx) -> dict[str, str]:
    """{word or phrase as it may appear in a resume: concept name}, from concept names and the alias file."""
    vocabulary = {name: name for name in profile_repo.all_concept_names(tx) if len(name) >= MIN_TOKEN}
    concepts = ml_module("concepts")
    aliases = getattr(concepts, "_aliases", None)
    if callable(aliases):
        for alias, canonical in aliases().items():
            if len(alias) >= MIN_TOKEN and canonical in vocabulary.values():
                vocabulary.setdefault(alias, canonical)
    return vocabulary


def found_skills(text: str, vocabulary: dict[str, str]) -> list[str]:
    lowered = text.lower()
    found: list[str] = []
    for phrase, concept in vocabulary.items():
        if concept in found:
            continue
        if re.search(rf"(?<![a-z0-9+#.]){re.escape(phrase)}(?![a-z0-9+#])", lowered):
            found.append(concept)
    return sorted(found)


def suggestions(user: CurrentUser) -> dict[str, Any]:
    def read(tx):
        row = profile_repo.current_resume(tx, user.user_id)
        if row is None:
            raise ApiError("NOT_FOUND", 404, "Upload a resume first.")
        text = _text_of(Path(row["file_path"]))
        if text is None:
            return {"skills": [], "note": "This PDF has no readable text (a scan?), so nothing could be suggested."}
        claimed = {s["concept"] for s in profile_repo.skill_rows(tx, user.user_id)}
        skills = found_skills(text, _vocabulary(tx))
        return {
            "skills": [{"concept": s, "already_claimed": s in claimed} for s in skills],
            "note": "Nothing is added until you choose skills. Resume skills count as claimed, not verified.",
        }

    return run_read(read)


def apply_suggestions(user: CurrentUser, names: list[str]) -> dict[str, Any]:
    wanted = list(dict.fromkeys(students.normalise_skill(n) for n in names if n.strip()))

    def read(tx):
        known = profile_repo.concept_names_known(tx, wanted)
        current = [s["concept"] for s in profile_repo.skill_rows(tx, user.user_id) if s["claimed"]]
        return known, current

    known, current = run_read(read)
    unknown = [n for n in wanted if n not in known]
    if unknown:
        raise ApiError(
            "VALIDATION_FAILED", 422, "Choose skills from the suggestions.",
            errors=[{"field": "skills", "message": f"Unknown skill: {unknown[0]}"}],
        )
    merged = list(dict.fromkeys([*current, *wanted]))
    if len(merged) > MAX_CLAIMED:
        raise ApiError(
            "VALIDATION_FAILED", 422, f"You can claim at most {MAX_CLAIMED} skills.",
            errors=[{"field": "skills", "message": f"At most {MAX_CLAIMED} claimed skills"}],
        )
    students.update_profile(user, ProfilePatch(claimed_skills=merged))
    return profile.my_profile(user)
