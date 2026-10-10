"""Certificates (REQ-001, REQ-002, REQ-037): upload intake API-005, JOB-01 processing, polling API-006/007, manual
entry API-008, review API-009/010 and the file stream API-011. Status machine: backend section 6.1.

Extraction, verification and trust belong to P1 (`app.ml.*`). This module only orchestrates them, so it loads them
lazily through `_pipeline()`; tests replace them with `set_pipeline_for_tests`. Each status change commits the
fields, the StatusEvent and the notifications in ONE write transaction (rule 5).
"""
import importlib
import logging
import os
import re
import uuid
from collections.abc import Callable
from datetime import timedelta
from difflib import SequenceMatcher
from pathlib import Path
from types import SimpleNamespace
from typing import Any, BinaryIO

from fastapi import BackgroundTasks

from app.core.clock import today, utc_now, utc_now_iso
from app.core.config import get_settings
from app.core.database import run_read, run_write
from app.core.errors import ApiError
from app.core.ratelimit import RateLimiter
from app.repos import certificates_repo
from app.schemas.auth import CurrentUser
from app.schemas.generated import ManualCertificate, ReviewDecision
from app.services.access import assert_dept_hod, assert_mentor_of
from app.services.notify import notify, render_title
from app.services.status_history import record_status
from app.services.students import normalise_skill

log = logging.getLogger("gurusetu.certificates")

MAX_PDF_PAGES = 5
MANUAL_CONFIDENCE_CAP = 0.50  # API-008: a hand-typed certificate never looks more trusted than this
STALE_AFTER_S = 60  # JOB-02
SYSTEM = SimpleNamespace(user_id="system", name="System")

# magic bytes -> (media type, extension), API-005
_MAGIC = (
    (b"\xff\xd8\xff", "image/jpeg", "jpg"),
    (b"\x89PNG\r\n\x1a\n", "image/png", "png"),
    (b"%PDF-", "application/pdf", "pdf"),
)
_PRIVATE = {"owner_id", "owner_name", "owner_roll_no", "duplicate_of"}
_STATUS_LABEL = {
    "certified": "certified",
    "needs_review": "waiting for review",
    "rejected": "rejected",
    "duplicate": "a duplicate",
    "failed": "unreadable (enter the details manually)",
}

# ---- P1 pipeline seam -----------------------------------------------------------------------------

_override: tuple[Callable, Callable, Callable] | None = None


def set_pipeline_for_tests(extract: Callable, verify: Callable, apply_certified: Callable) -> None:
    global _override
    _override = (extract, verify, apply_certified)


def clear_pipeline_for_tests() -> None:
    global _override
    _override = None


def _pipeline() -> tuple[Callable, Callable, Callable]:
    """(extract, verify, apply_certified) from P1, signatures in docs/phases/phase-2-core-verify-mentor.md."""
    if _override:
        return _override
    return (
        importlib.import_module("app.ml.extraction").extract,
        importlib.import_module("app.ml.verification").verify,
        importlib.import_module("app.ml.trust").apply_certified,
    )


# ---- shaping --------------------------------------------------------------------------------------


def _cert(row: dict[str, Any]) -> dict[str, Any]:
    """The `Certificate` response model: never the owner columns, `duplicate_of` or the file path."""
    return {k: v for k, v in row.items() if k not in _PRIVATE}


def _title_for(title: str | None) -> str:
    return (title or "your upload")[:60]


def _notify_result(tx, owner_id: str, title: str | None, status: str) -> None:
    notify(
        tx, owner_id, "certificate_result",
        render_title("certificate_result", title=_title_for(title), status_label=_STATUS_LABEL[status]),
        link="/student/certificates",
    )


def _notify_review_needed(tx, owner_id: str, owner_name: str) -> None:
    mentor = certificates_repo.assigned_mentor_id(tx, owner_id)
    if mentor:
        notify(tx, mentor, "review_needed", render_title("review_needed", student=owner_name), link="/reviews")


# ---- API-005 upload intake ------------------------------------------------------------------------

_limiter: RateLimiter | None = None


def _upload_limiter() -> RateLimiter:
    global _limiter
    if _limiter is None:
        _limiter = RateLimiter(get_settings().upload_rate_limit_per_hour, 3600)
    return _limiter


def reset_upload_limiter() -> None:
    if _limiter is not None:
        _limiter.reset()


def _sniff(head: bytes) -> tuple[str, str]:
    for magic, media_type, ext in _MAGIC:
        if head.startswith(magic):
            return media_type, ext
    raise ApiError("UNSUPPORTED_FILE_TYPE", 415, "Upload a JPEG, PNG or PDF file.")


def _pdf_pages(path: Path) -> int:
    # ponytail: counts /Type /Page objects and the largest /Count; a PDF that hides its page tree in an object stream
    # reads low. Swap in pypdfium2's page count if that ever matters.
    data = path.read_bytes()
    leaves = len(re.findall(rb"/Type\s*/Page(?![A-Za-z])", data))
    counts = [int(n) for n in re.findall(rb"/Count\s+(\d+)", data)]
    return max([leaves, *counts])


def intake(user: CurrentUser, upload: BinaryIO, background: BackgroundTasks) -> dict[str, Any]:
    """API-005. Stream to a temp file counting bytes, check magic bytes, store `<uuid>.<ext>`, start JOB-01."""
    _upload_limiter().check(user.user_id)
    cfg = get_settings()
    directory = Path(cfg.upload_dir)
    directory.mkdir(parents=True, exist_ok=True)
    head = upload.read(16)
    media_type, ext = _sniff(head)

    evidence_id = str(uuid.uuid4())
    temp, final = directory / f".tmp-{evidence_id}", directory / f"{evidence_id}.{ext}"
    size = 0
    try:
        with temp.open("wb") as out:
            chunk = head
            while chunk:
                size += len(chunk)
                if size > cfg.max_upload_bytes:
                    raise ApiError("FILE_TOO_LARGE", 413, f"The file is larger than {cfg.max_upload_mb} MB.")
                out.write(chunk)
                chunk = upload.read(1024 * 1024)
        if media_type == "application/pdf" and _pdf_pages(temp) > MAX_PDF_PAGES:
            raise ApiError(
                "VALIDATION_FAILED", 422, f"The PDF has more than {MAX_PDF_PAGES} pages.",
                errors=[{"field": "file", "message": f"At most {MAX_PDF_PAGES} pages"}],
            )
        os.replace(temp, final)
    except BaseException:
        temp.unlink(missing_ok=True)
        raise

    # The hash is stored by JOB-01 with the verification result, NOT here: verification asks "does any Evidence already
    # carry this SHA-256?", and a `processing` row that already carried it would be reported as its own duplicate.
    now = utc_now_iso()
    props = {
        "id": evidence_id, "kind": "certificate", "status": "processing", "file_path": str(final),
        "media_type": media_type, "size_bytes": size, "skills": [],
        "contains_instructions": False, "reasons": [], "created_at": now, "updated_at": now,
    }

    def write(tx):
        certificates_repo.create(tx, user.user_id, props)
        record_status(tx, "evidence", evidence_id, None, "processing", user)
        return _cert(certificates_repo.get_with_owner(tx, evidence_id))

    try:
        result = run_write(write)
    except BaseException:
        final.unlink(missing_ok=True)
        raise
    background.add_task(process_certificate, evidence_id)
    return result


# ---- JOB-01 ---------------------------------------------------------------------------------------


def process_certificate(evidence_id: str) -> None:
    """Extract, verify and store the result. Never raises: any failure marks the certificate `failed`."""
    try:
        _process(evidence_id)
    except Exception:
        log.exception("certificate job failed", extra={"evidence_id": evidence_id})
        try:
            _mark_failed(evidence_id, "extraction_failed")
        except Exception:
            log.exception("could not mark certificate failed", extra={"evidence_id": evidence_id})


def _process(evidence_id: str) -> None:
    job = run_read(lambda tx: certificates_repo.get_job(tx, evidence_id))
    if job is None or job["status"] != "processing":
        return  # idempotent: someone else already finished it
    extract, verify, apply_certified = _pipeline()
    data = Path(job["file_path"]).read_bytes()
    extraction = extract(data, job["media_type"])  # the slow part (3-20 s): outside any DB transaction
    student = SimpleNamespace(
        user_id=job["user_id"], name=job["name"], dept_code=job["dept_code"], roll_no=job["roll_no"],
        enrolled_on=job["enrolled_on"],
    )

    def write(tx):
        if certificates_repo.current_status(tx, evidence_id) != "processing":
            return
        result = verify(student, data, job["media_type"], extraction, tx)
        status = result.status
        props: dict[str, Any] = {
            "status": status, "confidence": result.confidence, "reasons": list(result.reasons),
            "duplicate_of": result.duplicate_of, "sha256": result.sha256, "phash": result.phash,
            "skills": list(result.skills), "updated_at": utc_now_iso(),
            "source": getattr(extraction, "source", None),
        }
        for field in ("holder_name", "title", "issuer", "issue_date", "level", "type", "certificate_id", "verify_url",
                      "contains_instructions"):
            if hasattr(extraction, field):
                props[field] = getattr(extraction, field)
        certificates_repo.update(tx, evidence_id, props)
        if status == "certified":
            apply_certified(tx, job["user_id"], evidence_id, list(result.skills))
        record_status(tx, "evidence", evidence_id, "processing", status, SYSTEM)
        _notify_result(tx, job["user_id"], props.get("title"), status)
        if status == "needs_review":
            _notify_review_needed(tx, job["user_id"], job["name"])

    run_write(write)


def _mark_failed(evidence_id: str, reason: str) -> None:
    def write(tx):
        row = certificates_repo.get_with_owner(tx, evidence_id)
        if row is None or row["status"] != "processing":
            return
        certificates_repo.update(
            tx, evidence_id, {"status": "failed", "reasons": [reason], "updated_at": utc_now_iso()}
        )
        record_status(tx, "evidence", evidence_id, "processing", "failed", SYSTEM, note=reason)
        _notify_result(tx, row["owner_id"], row["title"], "failed")

    run_write(write)


def sweep_stale() -> int:
    """JOB-02, at startup: anything still `processing` after 60 s lost its worker, so it becomes `failed`."""
    cutoff = (utc_now() - timedelta(seconds=STALE_AFTER_S)).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    stale = run_read(lambda tx: certificates_repo.stale_processing(tx, cutoff))
    for item in stale:
        _mark_failed(item["id"], "interrupted")
    return len(stale)


# ---- API-006 / 007 / 011 reads --------------------------------------------------------------------


def _readable(tx, user: CurrentUser, evidence_id: str) -> dict[str, Any]:
    """The certificate, if the caller may see it: the owner, a mentor of the owner, or the owner's HOD. Else 404."""
    row = certificates_repo.get_with_owner(tx, evidence_id)
    if row is None:
        raise ApiError("NOT_FOUND", 404, "The certificate was not found.")
    if user.role == "student":
        if row["owner_id"] != user.user_id:
            raise ApiError("NOT_FOUND", 404, "The certificate was not found.")
    elif user.role == "faculty":
        assert_mentor_of(tx, user.user_id, row["owner_id"])
    else:
        assert_dept_hod(tx, user.user_id, row["owner_id"])
    return row


def get_certificate(user: CurrentUser, evidence_id: str) -> dict[str, Any]:
    return run_read(lambda tx: _cert(_readable(tx, user, evidence_id)))


def list_mine(user: CurrentUser) -> list[dict[str, Any]]:
    return run_read(lambda tx: certificates_repo.list_for_student(tx, user.user_id))


def file_for(user: CurrentUser, evidence_id: str) -> tuple[Path, str]:
    def read(tx):
        _readable(tx, user, evidence_id)
        return certificates_repo.file_path_of(tx, evidence_id)

    found = run_read(read)
    if found is None:
        raise ApiError("NOT_FOUND", 404, "The certificate was not found.")
    path = Path(found[0]).resolve()
    if Path(get_settings().upload_dir).resolve() not in path.parents or not path.is_file():
        raise ApiError("NOT_FOUND", 404, "The file is no longer available.")
    return path, found[1]


# ---- API-008 manual entry -------------------------------------------------------------------------


def _manual_confidence(tx, student: dict[str, Any], body: ManualCertificate) -> float:
    """The same 0.40/0.25/0.20/0.15 weights as verification (ai-system section 3), capped at 0.50."""
    typed, profile = body.holder_name.lower().strip(), student["owner_name"].lower().strip()
    name_ok = SequenceMatcher(None, typed, profile).ratio() >= 0.85
    issuer_ok = certificates_repo.issuer_known(tx, body.issuer)
    date_ok = body.issue_date <= today()
    score = 0.40 * name_ok + 0.25 * issuer_ok + 0.20 * date_ok + 0.15  # every manual field is required, so complete
    return min(round(score, 2), MANUAL_CONFIDENCE_CAP)


def put_manual(user: CurrentUser, evidence_id: str, body: ManualCertificate) -> dict[str, Any]:
    def write(tx):
        row = certificates_repo.get_with_owner(tx, evidence_id)
        if row is None or row["owner_id"] != user.user_id:
            raise ApiError("NOT_FOUND", 404, "The certificate was not found.")
        if row["status"] != "failed":
            raise ApiError("INVALID_TRANSITION", 409, "Details can only be entered for a certificate that failed.")
        skills = list(dict.fromkeys(normalise_skill(s.root if hasattr(s, "root") else str(s)) for s in body.skills))
        certificates_repo.update(tx, evidence_id, {
            "holder_name": body.holder_name, "title": body.title, "issuer": body.issuer,
            "issue_date": body.issue_date.isoformat(), "level": body.level.value, "type": body.type.value,
            "skills": skills[:8], "source": "manual", "confidence": _manual_confidence(tx, row, body),
            "reasons": ["manual_entry"], "status": "needs_review", "updated_at": utc_now_iso(),
        })
        record_status(tx, "evidence", evidence_id, "failed", "needs_review", user, note="manual entry")
        _notify_review_needed(tx, user.user_id, user.name)
        return _cert(certificates_repo.get_with_owner(tx, evidence_id))

    return run_write(write)


# ---- API-009 / 010 review -------------------------------------------------------------------------


def review_queue(user: CurrentUser) -> list[dict[str, Any]]:
    """`needs_review` certificates of the caller's assigned mentees (faculty) or department (HOD), oldest first."""

    def read(tx):
        return [
            {
                "certificate": _cert(r),
                "student": {"user_id": r["owner_id"], "name": r["owner_name"], "roll_no": r["owner_roll_no"]},
                "duplicate_of": r["duplicate_of"],
            }
            for r in certificates_repo.review_queue(tx, user.role, user.user_id, user.dept_code)
        ]

    return run_read(read)


def review(user: CurrentUser, evidence_id: str, body: ReviewDecision) -> dict[str, Any]:
    approve = body.decision.value == "approve"
    if not approve and not body.reason:
        raise ApiError(
            "VALIDATION_FAILED", 422, "A reason is required to reject a certificate.",
            errors=[{"field": "reason", "message": "Required when rejecting (3-300 characters)"}],
        )
    apply_certified = _pipeline()[2] if approve else None

    def write(tx):
        row = certificates_repo.get_with_owner(tx, evidence_id)
        if row is None:
            raise ApiError("NOT_FOUND", 404, "The certificate was not found.")
        if user.role == "hod":
            assert_dept_hod(tx, user.user_id, row["owner_id"])
        else:  # only the ASSIGNED mentor reviews (a guide may read but not decide)
            assert_mentor_of(tx, user.user_id, row["owner_id"], "assigned")
        if row["status"] != "needs_review":
            raise ApiError("ALREADY_REVIEWED", 409, "This certificate has already been reviewed.")
        status = "certified" if approve else "rejected"
        props = {"status": status, "reviewed_by": user.user_id, "updated_at": utc_now_iso()}
        if not approve:
            props["review_reason"] = body.reason
        certificates_repo.update(tx, evidence_id, props)
        if approve:
            apply_certified(tx, row["owner_id"], evidence_id, list(row["skills"]))
        record_status(tx, "evidence", evidence_id, "needs_review", status, user, note=None if approve else body.reason)
        _notify_result(tx, row["owner_id"], row["title"], status)
        return _cert(certificates_repo.get_with_owner(tx, evidence_id))

    return run_write(write)
