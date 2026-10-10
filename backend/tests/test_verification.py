"""Verification rules and confidence (ai-system 3), plus the six EVAL-02 cases.

Every rule row in the table gets a test, and the rules are checked in order:
a duplicate must report as a duplicate even when its name would also mismatch.

A fake transaction stands in for Neo4j so these stay unit tests - the Cypher
itself is exercised by P2's integration tests once the seed exists.
"""

from __future__ import annotations

import datetime as dt
import io
from dataclasses import dataclass, field
from typing import Any

import pytest

from app.ml import verification
from app.ml.extraction import Extraction, ExtractionFailed
from app.ml.verification import StudentCtx, norm_name, verify

TODAY = "2026-10-10"


# -- Fakes --------------------------------------------------------------------


@dataclass
class FakeSettings:
    cert_auto_certify_min: float = 0.85
    name_match_min: int = 85
    phash_max_distance: int = 6
    tamper_check_enabled: bool = False
    ela_threshold: float = 12.0
    sim_min: float = 0.60
    today_override: str = TODAY
    extraction_cache_dir: str = "/tmp/cache"  # noqa: S108 - never read; these tests do not touch the cache
    llm_model: str = "qwen/qwen3.8-27b"


@dataclass
class FakeTx:
    """Stands in for a Neo4j transaction by answering the repo's questions."""

    sha_hit: dict[str, Any] | None = None
    phashes: list[dict[str, Any]] = field(default_factory=list)
    cert_id_hit: dict[str, Any] | None = None
    issuers: list[dict[str, Any]] = field(
        default_factory=lambda: [
            {"name": "NPTEL", "aliases": ["NPTEL Online", "National Programme on Technology Enhanced Learning"]},
            {"name": "Coursera", "aliases": []},
            {"name": "Campus Coding Club", "aliases": ["CCC"]},
        ]
    )


@pytest.fixture(autouse=True)
def _patch(monkeypatch):
    """Point the module at fake settings and fake repo reads."""
    settings = FakeSettings()
    monkeypatch.setattr(verification, "get_settings", lambda: settings)
    monkeypatch.setattr("app.ml.extraction.get_settings", lambda: settings)
    monkeypatch.setattr("app.ml.concepts.get_settings", lambda: settings)

    repo = verification.ml_repo
    monkeypatch.setattr(repo, "find_by_sha256", lambda tx, sha256: tx.sha_hit)
    monkeypatch.setattr(repo, "all_phashes", lambda tx: tx.phashes)
    monkeypatch.setattr(
        repo,
        "find_by_issuer_and_certificate_id",
        lambda tx, issuer_normalised, certificate_id: tx.cert_id_hit,
    )
    monkeypatch.setattr(repo, "all_issuers", lambda tx: tx.issuers)
    return settings


AARAV = StudentCtx(user_id="u-aarav", name="Aarav Menon", enrolled_on="2024-07-15")


def good_extraction(**overrides: Any) -> Extraction:
    data: dict[str, Any] = {
        "is_certificate": True,
        "holder_name": "Aarav Menon",
        "title": "Deep Learning with PyTorch",
        "issuer": "NPTEL",
        "issue_date": "2026-04-15",
        "level": "national",
        "type": "course",
        "skills": ["deep learning", "pytorch"],
        "certificate_id": "NPTEL26CS41S7701",
        "verify_url": None,
        "contains_instructions": False,
    }
    data.update(overrides)
    return Extraction(**data)


def png_bytes(colour: str = "white", size: tuple[int, int] = (80, 60)) -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", size, colour).save(buf, format="PNG")
    return buf.getvalue()


def noisy_png(seed: int, size: tuple[int, int] = (96, 96)) -> bytes:
    """A deterministic image with real structure, so its pHash is meaningful."""
    import random

    from PIL import Image

    rng = random.Random(seed)  # noqa: S311 - deterministic test image, not crypto
    img = Image.new("RGB", size, "white")
    px = img.load()
    for x in range(size[0]):
        for y in range(size[1]):
            if rng.random() < 0.35:
                shade = rng.randrange(0, 90)
                px[x, y] = (shade, shade, shade)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# -- Rule 7: confidence and the happy path ------------------------------------


def test_clean_certificate_is_certified_with_confidence_1():
    result = verify(AARAV, png_bytes(), "image/png", good_extraction(), FakeTx())
    assert result.status == "certified"
    assert result.confidence == 1.0
    assert result.reasons == []
    assert result.skills == ["deep learning", "pytorch"]
    assert result.sha256 and len(result.sha256) == 64


def test_confidence_weights_sum_to_one_and_name_dominates():
    """Auto-certification at 0.85 is only reachable when name, issuer and date
    all pass; completeness alone can never get there."""
    assert verification.W_NAME + verification.W_ISSUER + verification.W_DATE + verification.W_COMPLETE == 1.0
    assert verification.W_NAME == 0.40
    assert 1.0 - verification.W_COMPLETE >= 0.85


# -- EVAL-02 case 4: name mismatch --------------------------------------------


def test_name_mismatch_goes_to_review():
    result = verify(
        AARAV, png_bytes(), "image/png", good_extraction(holder_name="Arav M."), FakeTx()
    )
    assert result.status == "needs_review"
    assert "name_mismatch" in result.reasons
    assert result.confidence == 0.60  # 1.00 - 0.40


# -- EVAL-02 case 5: unknown issuer -------------------------------------------


def test_unknown_issuer_goes_to_review():
    result = verify(
        AARAV, png_bytes(), "image/png",
        good_extraction(issuer="Totally Made Up Institute"), FakeTx(),
    )
    assert result.status == "needs_review"
    assert "unknown_issuer" in result.reasons
    assert result.confidence == 0.75  # 1.00 - 0.25


def test_issuer_alias_counts_as_known():
    result = verify(
        AARAV, png_bytes(), "image/png", good_extraction(issuer="NPTEL Online"), FakeTx()
    )
    assert result.status == "certified"


# -- EVAL-02 case 6: future date ----------------------------------------------


def test_future_date_goes_to_review():
    future = (dt.date.fromisoformat(TODAY) + dt.timedelta(days=30)).isoformat()
    result = verify(
        AARAV, png_bytes(), "image/png", good_extraction(issue_date=future), FakeTx()
    )
    assert result.status == "needs_review"
    assert "date_invalid" in result.reasons


def test_date_far_before_enrolment_goes_to_review():
    result = verify(
        AARAV, png_bytes(), "image/png", good_extraction(issue_date="2019-01-01"), FakeTx()
    )
    assert result.status == "needs_review"
    assert "date_invalid" in result.reasons


def test_date_within_the_two_year_grace_window_is_accepted():
    """enrolled_on - 730 days: a certificate earned in school still counts."""
    result = verify(
        AARAV, png_bytes(), "image/png", good_extraction(issue_date="2023-01-01"), FakeTx()
    )
    assert result.status == "certified"


def test_missing_date_is_invalid_and_incomplete():
    result = verify(
        AARAV, png_bytes(), "image/png", good_extraction(issue_date=None), FakeTx()
    )
    assert result.status == "needs_review"
    assert "date_invalid" in result.reasons
    assert "incomplete" in result.reasons


def test_no_skills_still_certifies_at_exactly_the_threshold():
    """Confidence 1.00 - 0.15 = 0.85, which meets cert_auto_certify_min. The
    spec intends this: "auto-certification requires the name, issuer and date
    checks all to pass (0.85)". The certificate is trustworthy; it just proves
    no skill, so it creates no PROVES edge and lifts no trust."""
    result = verify(AARAV, png_bytes(), "image/png", good_extraction(skills=[]), FakeTx())
    assert result.status == "certified"
    assert result.confidence == 0.85
    assert result.skills == []


def test_incomplete_is_reported_when_another_check_also_fails():
    result = verify(
        AARAV, png_bytes(), "image/png",
        good_extraction(skills=[], issuer="Unknown Place"), FakeTx(),
    )
    assert result.status == "needs_review"
    assert set(result.reasons) == {"unknown_issuer", "incomplete"}


# -- EVAL-02 cases 1-3: the three duplicate rules -----------------------------


def test_exact_duplicate_by_sha256():
    tx = FakeTx(sha_hit={"id": "ev-existing", "status": "certified"})
    result = verify(AARAV, png_bytes(), "image/png", good_extraction(), tx)
    assert result.status == "duplicate"
    assert result.reasons == ["duplicate_file"]
    assert result.duplicate_of == "ev-existing"
    assert result.confidence is None


def test_visual_duplicate_by_phash_within_threshold():
    data = png_bytes("white")
    own = verification.compute_phash(data, "image/png")
    tx = FakeTx(phashes=[{"id": "ev-photo", "phash": own}])
    result = verify(AARAV, png_bytes("white"), "image/png", good_extraction(), tx)
    assert result.status == "duplicate"
    assert result.reasons == ["duplicate_image"]
    assert result.duplicate_of == "ev-photo"


def test_distant_phash_is_not_a_duplicate():
    """Two visually different documents must not collide. Built from real
    content rather than flat colour: every blank image shares a degenerate
    pHash, so flat fills would collide with each other by design."""
    other = verification.compute_phash(noisy_png(seed=1), "image/png")
    tx = FakeTx(phashes=[{"id": "ev-other", "phash": other}])
    result = verify(AARAV, noisy_png(seed=2), "image/png", good_extraction(), tx)
    assert result.status != "duplicate"


def test_reencoded_copy_of_the_same_document_is_a_visual_duplicate():
    """The TEST-13 `aarav_python_copy.jpg` case: a re-photographed or re-saved
    copy has a different SHA-256 but a near-identical pHash."""
    original = noisy_png(seed=7)
    from PIL import Image

    buf = io.BytesIO()
    with Image.open(io.BytesIO(original)) as img:
        img.convert("RGB").save(buf, format="JPEG", quality=70)
    recoded = buf.getvalue()

    tx = FakeTx(phashes=[{"id": "ev-original",
                          "phash": verification.compute_phash(original, "image/png")}])
    result = verify(AARAV, recoded, "image/jpeg", good_extraction(), tx)
    assert result.status == "duplicate"
    assert result.reasons == ["duplicate_image"]


def test_duplicate_certificate_id():
    tx = FakeTx(cert_id_hit={"id": "ev-same-id"})
    result = verify(AARAV, png_bytes(), "image/png", good_extraction(), tx)
    assert result.status == "duplicate"
    assert result.reasons == ["duplicate_certificate_id"]


def test_duplicate_rule_wins_over_name_mismatch():
    """Rule order matters: the first rule that applies sets the status."""
    tx = FakeTx(sha_hit={"id": "ev-existing", "status": "needs_review"})
    result = verify(
        AARAV, png_bytes(), "image/png", good_extraction(holder_name="Someone Else"), tx
    )
    assert result.reasons == ["duplicate_file"]


# -- Rules 4 and 5 ------------------------------------------------------------


def test_not_a_certificate():
    result = verify(
        AARAV, png_bytes(), "image/png", good_extraction(is_certificate=False), FakeTx()
    )
    assert result.status == "needs_review"
    assert result.reasons == ["not_a_certificate"]


def test_injection_text_goes_to_review_but_keeps_confidence():
    """EVAL-04: the document tried to talk to the model. Route to a human, and
    still show the reviewer how the rest of the document scored."""
    result = verify(
        AARAV, png_bytes(), "image/png",
        good_extraction(contains_instructions=True), FakeTx(),
    )
    assert result.status == "needs_review"
    assert result.reasons == ["injection_text"]
    assert result.confidence == 1.0


def test_injection_never_auto_certifies_even_when_every_field_is_perfect():
    result = verify(
        AARAV, png_bytes(), "image/png",
        good_extraction(contains_instructions=True), FakeTx(),
    )
    assert result.status != "certified"


# -- Rule 6: tamper (A8) ------------------------------------------------------


def test_tamper_check_is_skipped_when_disabled(_patch):
    _patch.tamper_check_enabled = False
    _patch.ela_threshold = -1.0  # would flag everything if consulted
    result = verify(AARAV, png_bytes(), "image/png", good_extraction(), FakeTx())
    assert result.status == "certified"


def test_tamper_signal_goes_to_review_when_enabled(_patch):
    _patch.tamper_check_enabled = True
    _patch.ela_threshold = -1.0  # force the ELA branch to trip
    result = verify(AARAV, png_bytes(), "image/png", good_extraction(), FakeTx())
    assert result.status == "needs_review"
    assert result.reasons == ["tamper_signal"]


def test_exif_editor_marker_is_detected():
    from PIL import Image

    buf = io.BytesIO()
    img = Image.new("RGB", (40, 40), "white")
    exif = img.getexif()
    exif[0x0131] = "Adobe Photoshop 2026"
    img.save(buf, format="JPEG", exif=exif)
    assert verification._exif_editor(buf.getvalue()) is True


def test_clean_image_has_no_exif_editor_marker():
    assert verification._exif_editor(png_bytes()) is False


# -- Extraction failure -------------------------------------------------------


def test_extraction_failed_becomes_failed_status():
    result = verify(AARAV, png_bytes(), "image/png", ExtractionFailed(), FakeTx())
    assert result.status == "failed"
    assert result.reasons == ["extraction_failed"]
    assert result.confidence is None
    assert result.skills == []


# -- TEST-62: name normalisation ----------------------------------------------


@pytest.mark.parametrize(
    "printed",
    ["Aarav  Menon.", "AARAV MENON", "Āarav Menon", "Mr. Aarav Menon", "aarav menon"],
)
def test_name_variants_all_match(printed):
    """TEST-62 / FM-16: spacing, case, punctuation, honorifics and diacritics
    must not produce a false name_mismatch."""
    result = verify(
        AARAV, png_bytes(), "image/png", good_extraction(holder_name=printed), FakeTx()
    )
    assert result.status == "certified", f"{printed!r} was rejected"


def test_genuinely_different_name_does_not_match():
    assert verification.name_ok("Rohit Kumar", "Aarav Menon") is False


def test_norm_name_strips_accents_punctuation_and_honorifics():
    assert norm_name("Dr. Āarav  Menon.") == "aarav menon"
    assert norm_name(None) == ""


def test_hamming_handles_malformed_hashes():
    assert verification.hamming("abc", "abcd") == 1000
    assert verification.hamming("zzzz", "0000") == 1000
    assert verification.hamming("ffff", "ffff") == 0
    assert verification.hamming("ffff", "fffe") == 1
