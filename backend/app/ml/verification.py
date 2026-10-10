"""Deterministic certificate verification (ai-system 3). Home of these rules.

Nothing here asks a model anything. The extractor has already produced fields;
this module decides, from code alone, whether the certificate is trustworthy.
The rules run in order and the first one that applies sets the status, so a
duplicate is reported as a duplicate even if its name would also mismatch.

Rule order:
  1 exact duplicate (SHA-256)      -> duplicate / duplicate_file
  2 visual duplicate (pHash)       -> duplicate / duplicate_image
  3 id duplicate (issuer + cert id)-> duplicate / duplicate_certificate_id
  4 not a certificate              -> needs_review / not_a_certificate
  5 injection text                 -> needs_review / injection_text
  6 tamper signal (if enabled)     -> needs_review / tamper_signal
  7 confidence >= threshold        -> certified, else needs_review + reasons
"""

from __future__ import annotations

import datetime as dt
import io
import logging
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any

from app.ml import concepts
from app.ml.extraction import Extraction, ExtractionFailed, render_pdf_first_page
from app.ml.settings import get_settings
from app.repos import ml_repo

log = logging.getLogger(__name__)

# Confidence weights (ai-system 3). They sum to 1.0, and auto-certification at
# 0.85 therefore requires name, issuer and date to all pass.
W_NAME = 0.40
W_ISSUER = 0.25
W_DATE = 0.20
W_COMPLETE = 0.15

ISSUER_MATCH_MIN = 90
DATE_BACKDATE_DAYS = 730

HONORIFICS = {"mr", "mrs", "ms", "miss", "dr", "prof", "shri", "smt", "sri"}
_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)
_WS = re.compile(r"\s+")


@dataclass
class StudentCtx:
    """What verification needs to know about the uploading student."""

    user_id: str
    name: str
    enrolled_on: str | None = None


@dataclass
class VerificationResult:
    status: str
    confidence: float | None
    reasons: list[str] = field(default_factory=list)
    duplicate_of: str | None = None
    sha256: str = ""
    phash: str | None = None
    skills: list[str] = field(default_factory=list)


# -- Normalisation and the four confidence inputs -----------------------------


def norm_name(value: str | None) -> str:
    """NFKD, drop combining accents, lower-case, strip punctuation and
    honorifics, collapse spaces (TEST-62)."""
    if not value:
        return ""
    decomposed = unicodedata.normalize("NFKD", str(value))
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    cleaned = _PUNCT.sub(" ", stripped.lower())
    words = [w for w in _WS.sub(" ", cleaned).strip().split(" ") if w]
    kept = [w for w in words if w not in HONORIFICS]
    return " ".join(kept or words)


def name_ok(holder_name: str | None, student_name: str) -> bool:
    from rapidfuzz import fuzz

    threshold = int(get_settings().name_match_min)
    a, b = norm_name(holder_name), norm_name(student_name)
    if not a or not b:
        return False
    return fuzz.token_set_ratio(a, b) >= threshold


def issuer_known(issuer: str | None, issuers: list[dict[str, Any]]) -> bool:
    """Match the normalised issuer against Issuer.name or one of its aliases."""
    from rapidfuzz import fuzz

    if not issuer:
        return False
    target = norm_name(issuer)
    if not target:
        return False
    for row in issuers:
        candidates = [row.get("name") or ""] + list(row.get("aliases") or [])
        for candidate in candidates:
            if not candidate:
                continue
            if fuzz.token_set_ratio(target, norm_name(candidate)) >= ISSUER_MATCH_MIN:
                return True
    return False


def today() -> dt.date:
    """Calendar today in Asia/Kolkata, honouring today_override (architecture 5)."""
    override = getattr(get_settings(), "today_override", "") or ""
    if override:
        return dt.date.fromisoformat(str(override))
    ist = dt.timezone(dt.timedelta(hours=5, minutes=30))
    return dt.datetime.now(tz=ist).date()


def date_ok(issue_date: str | None, enrolled_on: str | None) -> bool:
    """Not null, not in the future, and not implausibly before enrolment."""
    if not issue_date:
        return False
    try:
        issued = dt.date.fromisoformat(str(issue_date))
    except ValueError:
        return False
    if issued > today():
        return False
    if enrolled_on:
        try:
            floor = dt.date.fromisoformat(str(enrolled_on)) - dt.timedelta(
                days=DATE_BACKDATE_DAYS
            )
        except ValueError:
            return True
        if issued < floor:
            return False
    return True


def complete(extraction: Extraction) -> bool:
    return bool(
        extraction.title
        and extraction.issuer
        and extraction.issue_date
        and extraction.skills
    )


def confidence_of(
    extraction: Extraction, student: StudentCtx, issuers: list[dict[str, Any]]
) -> tuple[float, list[str]]:
    """Weighted confidence plus one reason per failed check."""
    checks = {
        "name_mismatch": (name_ok(extraction.holder_name, student.name), W_NAME),
        "unknown_issuer": (issuer_known(extraction.issuer, issuers), W_ISSUER),
        "date_invalid": (date_ok(extraction.issue_date, student.enrolled_on), W_DATE),
        "incomplete": (complete(extraction), W_COMPLETE),
    }
    score = sum(weight for passed, weight in checks.values() if passed)
    reasons = [reason for reason, (passed, _) in checks.items() if not passed]
    return round(score, 2), reasons


# -- Perceptual hash ----------------------------------------------------------


def compute_phash(file_bytes: bytes, media_type: str) -> str | None:
    """64-bit pHash of the image, or of a PDF's first page. None when the file
    cannot be read: an unreadable file simply skips rule 2 (ENT-05 allows null)."""
    import imagehash
    from PIL import Image

    try:
        data = (
            render_pdf_first_page(file_bytes)
            if media_type == "application/pdf"
            else file_bytes
        )
        with Image.open(io.BytesIO(data)) as img:
            return str(imagehash.phash(img.convert("RGB")))
    except Exception:  # noqa: BLE001 - an unreadable file skips rule 2 (FM-17)
        log.info("phash could not be computed for this upload")
        return None


def hamming(a: str, b: str) -> int:
    """Distance between two hex pHash strings; a mismatch in width is 'far'."""
    try:
        if len(a) != len(b):
            return 1_000
        return (int(a, 16) ^ int(b, 16)).bit_count()
    except (TypeError, ValueError):
        return 1_000


# -- Tamper signals (rule 6, A8 / REQ-025) ------------------------------------

EDITOR_MARKERS = ("photoshop", "gimp", "pixlr", "snapseed", "picsart")


def tamper_signal(file_bytes: bytes, media_type: str) -> bool:
    """EXIF editor fingerprint, or an ELA mean above ela_threshold.

    Only consulted when tamper_check_enabled is true, because ELA is noisy and a
    false positive sends a legitimate certificate to review (A-17).

    ela_threshold <= 0 turns the ELA branch off. Tuned on the 25-file set plus
    the planted edit (A8): the planted file's whole-image ELA mean (0.185) sits
    inside the range of the genuine files (0.045 to 1.088), so no threshold
    separates them and the shipped value is 0 - the EXIF Software tag alone.
    """
    if media_type == "application/pdf":
        return False
    if _exif_editor(file_bytes):
        return True
    threshold = float(get_settings().ela_threshold)
    return threshold > 0 and _ela_mean(file_bytes) > threshold


def _exif_editor(file_bytes: bytes) -> bool:
    from PIL import Image

    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            exif = img.getexif()
            if not exif:
                return False
            # 0x0131 is the EXIF Software tag.
            software = str(exif.get(0x0131) or "").lower()
    except Exception:  # noqa: BLE001 - no readable EXIF is not a tamper signal
        return False
    return any(marker in software for marker in EDITOR_MARKERS)


def _ela_mean(file_bytes: bytes) -> float:
    """Error level analysis: re-save at a known quality and measure the mean
    absolute difference. Edited regions compress differently from the rest."""
    from PIL import Image, ImageChops, ImageStat

    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            original = img.convert("RGB")
            buf = io.BytesIO()
            original.save(buf, format="JPEG", quality=90)
            buf.seek(0)
            with Image.open(buf) as resaved:
                diff = ImageChops.difference(original, resaved.convert("RGB"))
        return float(ImageStat.Stat(diff.convert("L")).mean[0])
    except Exception:  # noqa: BLE001 - an undecodable image scores 0, never flags
        return 0.0


# -- The entry point ----------------------------------------------------------


def verify(
    student: StudentCtx,
    file_bytes: bytes,
    media_type: str,
    extraction: Extraction | ExtractionFailed,
    tx: Any,
) -> VerificationResult:
    """Decide the status of one uploaded certificate. Pure rules, no model."""
    from app.ml.extraction import sha256_hex

    settings = get_settings()
    sha256 = sha256_hex(file_bytes)

    if isinstance(extraction, ExtractionFailed):
        # No fields to judge. The student gets the manual-entry form (REQ-037).
        return VerificationResult(
            status="failed",
            confidence=None,
            reasons=[extraction.reason],
            sha256=sha256,
            phash=None,
            skills=[],
        )

    phash = compute_phash(file_bytes, media_type)

    # Rule 1: exact duplicate. Any student, any status except `failed` - a
    # failed row holds no verified claim, so it should not block a re-upload.
    existing = ml_repo.find_by_sha256(tx, sha256)
    if existing:
        return VerificationResult(
            status="duplicate",
            confidence=None,
            reasons=["duplicate_file"],
            duplicate_of=existing["id"],
            sha256=sha256,
            phash=phash,
            skills=[],
        )

    # Rule 2: visual duplicate - catches a re-photographed or re-encoded copy,
    # which has a different SHA but a near-identical pHash.
    if phash:
        max_distance = int(settings.phash_max_distance)
        for row in ml_repo.all_phashes(tx):
            if row.get("phash") and hamming(phash, row["phash"]) <= max_distance:
                return VerificationResult(
                    status="duplicate",
                    confidence=None,
                    reasons=["duplicate_image"],
                    duplicate_of=row["id"],
                    sha256=sha256,
                    phash=phash,
                    skills=[],
                )

    # Rule 3: the same certificate ID from the same issuer.
    if extraction.issuer and extraction.certificate_id:
        match = ml_repo.find_by_issuer_and_certificate_id(
            tx, norm_name(extraction.issuer), extraction.certificate_id.strip()
        )
        if match:
            return VerificationResult(
                status="duplicate",
                confidence=None,
                reasons=["duplicate_certificate_id"],
                duplicate_of=match["id"],
                sha256=sha256,
                phash=phash,
                skills=[],
            )

    issuers = ml_repo.all_issuers(tx)
    score, failed_checks = confidence_of(extraction, student, issuers)
    skills = concepts.normalise_all(extraction.skills)

    # Rule 4: not a certificate at all.
    if not extraction.is_certificate:
        return VerificationResult(
            status="needs_review",
            confidence=score,
            reasons=["not_a_certificate"],
            sha256=sha256,
            phash=phash,
            skills=skills,
        )

    # Rule 5: the document talks to an assistant. Confidence is still computed
    # so the reviewer sees how the rest of the document scored.
    if extraction.contains_instructions:
        return VerificationResult(
            status="needs_review",
            confidence=score,
            reasons=["injection_text"],
            sha256=sha256,
            phash=phash,
            skills=skills,
        )

    # Rule 6: tamper signals, only when switched on.
    if bool(settings.tamper_check_enabled) and tamper_signal(file_bytes, media_type):
        return VerificationResult(
            status="needs_review",
            confidence=score,
            reasons=["tamper_signal"],
            sha256=sha256,
            phash=phash,
            skills=skills,
        )

    # Rule 7: confidence decides.
    if score >= float(settings.cert_auto_certify_min):
        return VerificationResult(
            status="certified",
            confidence=score,
            reasons=[],
            sha256=sha256,
            phash=phash,
            skills=skills,
        )
    return VerificationResult(
        status="needs_review",
        confidence=score,
        reasons=failed_checks,
        sha256=sha256,
        phash=phash,
        skills=skills,
    )
