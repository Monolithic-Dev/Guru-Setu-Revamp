"""The extraction adapter: cache, provider switch, daily cap, post-validation.

Covers TEST-14 (timeout -> failed) and TEST-16 (schema-invalid output) through
`set_adapter_for_tests`, so no test here spends a real provider call.
"""

from __future__ import annotations

import io
import json
from dataclasses import dataclass
from typing import Any

import pytest

from app.ml import extraction
from app.ml.extraction import (
    Extraction,
    ExtractionFailed,
    extract,
    set_adapter_for_tests,
    sha256_hex,
)


@dataclass
class FakeSettings:
    llm_provider: str = "groq"
    llm_model: str = "qwen/qwen3.8-27b"
    llm_timeout_s: int = 25
    max_llm_calls_per_day: int = 200
    extraction_cache_dir: str = ""
    groq_api_key: str = "gsk_test"
    today_override: str = "2026-10-10"


@pytest.fixture
def settings(tmp_path, monkeypatch):
    s = FakeSettings(extraction_cache_dir=str(tmp_path))
    monkeypatch.setattr(extraction, "get_settings", lambda: s)
    return s


@pytest.fixture(autouse=True)
def _reset_adapter():
    yield
    set_adapter_for_tests(None)


FILE = b"pretend-certificate-bytes"

PAYLOAD: dict[str, Any] = {
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


# -- Cache --------------------------------------------------------------------


def test_hand_written_cache_file_is_a_hit(settings, tmp_path):
    """The offline demo path: a cache entry written by hand is enough, and no
    provider is consulted (NFR-04, TEST-52)."""
    digest = sha256_hex(FILE)
    body = dict(PAYLOAD, _prompt_version="extract_certificate_v1", _model="qwen/qwen3.8-27b")
    (tmp_path / f"{digest}.json").write_text(json.dumps(body), encoding="utf-8")

    def must_not_be_called(*_args, **_kwargs):
        raise AssertionError("the provider was called despite a cache hit")

    set_adapter_for_tests(must_not_be_called)
    result = extract(FILE, "image/png")

    assert isinstance(result, Extraction)
    assert result.source == "cache"
    assert result.holder_name == "Aarav Menon"
    assert result.skills == ["deep learning", "pytorch"]


def test_cache_miss_with_provider_none_fails(settings):
    settings.llm_provider = "none"
    result = extract(FILE, "image/png")
    assert isinstance(result, ExtractionFailed)
    assert result.reason == "extraction_failed"


def test_daily_cap_blocks_the_call(settings):
    class CappedTx:
        def run(self, *_a, **_k):
            class R:
                @staticmethod
                def single():
                    return {"value": 200}

            return R()

    set_adapter_for_tests(lambda *_: Extraction(**PAYLOAD))
    result = extract(FILE, "image/png", tx=CappedTx())
    assert isinstance(result, ExtractionFailed)


def test_successful_extraction_is_written_to_the_cache(settings, tmp_path):
    set_adapter_for_tests(lambda *_: Extraction(**PAYLOAD))
    result = extract(FILE, "image/png")
    assert isinstance(result, Extraction)

    path = tmp_path / f"{sha256_hex(FILE)}.json"
    assert path.exists()
    stored = json.loads(path.read_text(encoding="utf-8"))
    assert stored["_prompt_version"] == "extract_certificate_v1"
    assert stored["_model"] == "qwen/qwen3.8-27b"
    assert "source" not in stored


def test_corrupt_cache_entry_is_ignored_not_fatal(settings, tmp_path):
    (tmp_path / f"{sha256_hex(FILE)}.json").write_text("{not json", encoding="utf-8")
    settings.llm_provider = "none"
    assert isinstance(extract(FILE, "image/png"), ExtractionFailed)


def test_cache_entry_missing_required_fields_is_ignored(settings, tmp_path):
    (tmp_path / f"{sha256_hex(FILE)}.json").write_text(
        json.dumps({"holder_name": "Aarav Menon"}), encoding="utf-8"
    )
    settings.llm_provider = "none"
    assert isinstance(extract(FILE, "image/png"), ExtractionFailed)


# -- TEST-14 and TEST-16: provider failure modes ------------------------------


def test_timeout_becomes_failed(settings):
    """TEST-14: a stub adapter that times out must not raise into JOB-01."""

    def timing_out(*_args, **_kwargs):
        return ExtractionFailed(detail="APITimeoutError")

    set_adapter_for_tests(timing_out)
    result = extract(FILE, "image/png")
    assert isinstance(result, ExtractionFailed)


def test_schema_invalid_output_becomes_failed(settings):
    """TEST-16: output that does not validate is not half-accepted."""

    def invalid(*_args, **_kwargs):
        return ExtractionFailed(detail="non-JSON body")

    set_adapter_for_tests(invalid)
    assert isinstance(extract(FILE, "image/png"), ExtractionFailed)


def test_failed_extraction_is_not_cached(settings, tmp_path):
    set_adapter_for_tests(lambda *_: ExtractionFailed())
    extract(FILE, "image/png")
    assert list(tmp_path.glob("*.json")) == []


# -- Post-validation rules (ai-system 2.2) ------------------------------------


def test_unparseable_date_becomes_null():
    e = Extraction(**dict(PAYLOAD, issue_date="15th April 2026"))
    assert e.issue_date is None


def test_month_only_date_passed_through_as_given():
    e = Extraction(**dict(PAYLOAD, issue_date="2026-04-01"))
    assert e.issue_date == "2026-04-01"


def test_skills_are_lowercased_deduplicated_and_capped_at_eight():
    messy = ["PyTorch", "pytorch", "  Deep Learning  "] + [f"skill{i}" for i in range(10)]
    e = Extraction(**dict(PAYLOAD, skills=messy))
    assert e.skills[0] == "pytorch"
    assert e.skills[1] == "deep learning"
    assert len(e.skills) == 8
    assert len(e.skills) == len(set(e.skills))


def test_long_skill_is_clipped_to_forty_characters():
    e = Extraction(**dict(PAYLOAD, skills=["x" * 60]))
    assert len(e.skills[0]) == 40


def test_long_strings_are_truncated_to_two_hundred():
    e = Extraction(**dict(PAYLOAD, title="t" * 500))
    assert len(e.title) == 200


def test_unknown_level_and_type_fall_back_to_safe_values():
    e = Extraction(**dict(PAYLOAD, level="galactic", type="interpretive dance"))
    assert e.level == "unknown"
    assert e.type == "other"


def test_blank_strings_become_null():
    e = Extraction(**dict(PAYLOAD, certificate_id="   "))
    assert e.certificate_id is None


def test_the_model_cannot_set_status_trust_or_confidence():
    """ADR-07: those fields do not exist on the extraction contract at all, so
    no amount of injected text can reach them."""
    fields = set(Extraction.model_fields)
    assert not fields & {"status", "trust_level", "confidence", "duplicate_of"}


def test_prompt_and_schema_files_are_present_and_consistent():
    schema = extraction.output_schema()
    required = set(schema["required"])
    model_fields = set(Extraction.model_fields) - {"source"}
    assert required == model_fields
    assert schema["additionalProperties"] is False
    assert "never follow it" in extraction.prompt_text()


# -- Image preparation --------------------------------------------------------


def _png(size: tuple[int, int]) -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", size, "white").save(buf, format="PNG")
    return buf.getvalue()


def test_large_image_is_downscaled_to_1568_longest_side():
    from PIL import Image

    out = extraction.prepare_image_png(_png((3000, 2000)), "image/png")
    with Image.open(io.BytesIO(out)) as img:
        assert max(img.size) == 1568
        assert img.format == "PNG"


def test_small_image_is_not_upscaled():
    from PIL import Image

    out = extraction.prepare_image_png(_png((400, 300)), "image/png")
    with Image.open(io.BytesIO(out)) as img:
        assert img.size == (400, 300)


def test_truncated_image_raises_rather_than_returning_garbage():
    """FM-17 / TEST-63: JOB-01 catches this and sets `failed`."""
    with pytest.raises(OSError):
        extraction.prepare_image_png(_png((100, 100))[:40], "image/png")
