"""MDL-01: the certificate field extractor.

The model's only job is to read fields off a document. It is given no tools, and
nothing it returns can set status, trust or confidence - those are decided in
`verification.py` from deterministic rules (ADR-07). The uploaded file is data;
if it contains text aimed at an assistant, that is a signal to record
(`contains_instructions`), never an instruction to follow.

Order of operations in `extract` (ai-system 2.4, 8):
  1. SHA-256 cache lookup   -> hit returns source="cache", no network at all
  2. llm_provider=none      -> failed (cache-only mode, the demo default)
  3. daily call cap reached -> failed
  4. otherwise call the provider
"""

from __future__ import annotations

import base64
import datetime as dt
import functools
import hashlib
import io
import json
import logging
import pathlib
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator

from app.ml.settings import get_settings

log = logging.getLogger(__name__)

PROMPT_VERSION = "extract_certificate_v1"
PROMPT_PATH = pathlib.Path(__file__).resolve().parent / "prompts" / (PROMPT_VERSION + ".md")
SCHEMA_PATH = (
    pathlib.Path(__file__).resolve().parent / "schemas" / "certificate_extraction.schema.json"
)

MAX_IMAGE_EDGE = 1568
MAX_STRING = 200
MAX_SKILLS = 8
MAX_SKILL_LEN = 40
PDF_RENDER_DPI = 150

LEVELS = (
    "international",
    "national",
    "state",
    "university",
    "college",
    "online",
    "other",
    "unknown",
)
TYPES = (
    "hackathon",
    "course",
    "workshop",
    "competition",
    "internship",
    "paper",
    "sports",
    "cultural",
    "other",
)


@functools.lru_cache(maxsize=1)
def prompt_text() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


@functools.lru_cache(maxsize=1)
def output_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


# -- Result types -------------------------------------------------------------


class Extraction(BaseModel):
    """The 2.2 contract, re-validated in Python after the provider call."""

    is_certificate: bool
    holder_name: str | None = None
    title: str | None = None
    issuer: str | None = None
    issue_date: str | None = None
    level: str = "unknown"
    type: str = "other"
    skills: list[str] = Field(default_factory=list)
    certificate_id: str | None = None
    verify_url: str | None = None
    contains_instructions: bool = False

    # Not part of the model's output: how we obtained it.
    source: str = "llm"

    @field_validator("holder_name", "title", "issuer", "certificate_id", "verify_url")
    @classmethod
    def _truncate(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = str(v).strip()
        return v[:MAX_STRING] or None

    @field_validator("issue_date")
    @classmethod
    def _iso_date_or_null(cls, v: str | None) -> str | None:
        """An unparseable date becomes null rather than failing the whole
        extraction: the date is one of four confidence inputs, and a missing
        date simply fails `date_ok` (ai-system 3)."""
        if not v:
            return None
        text = str(v).strip()
        try:
            return dt.date.fromisoformat(text).isoformat()
        except ValueError:
            log.info("extraction returned an unparseable issue_date; using null")
            return None

    @field_validator("level")
    @classmethod
    def _known_level(cls, v: str) -> str:
        v = (v or "").strip().lower()
        return v if v in LEVELS else "unknown"

    @field_validator("type")
    @classmethod
    def _known_type(cls, v: str) -> str:
        v = (v or "").strip().lower()
        return v if v in TYPES else "other"

    @field_validator("skills")
    @classmethod
    def _clean_skills(cls, v: list[str]) -> list[str]:
        out: dict[str, None] = {}
        for raw in v or []:
            s = " ".join(str(raw).split()).strip().lower()[:MAX_SKILL_LEN]
            if s:
                out.setdefault(s, None)
        return list(out)[:MAX_SKILLS]

    def cache_payload(self) -> dict[str, Any]:
        """The object as it is stored in `extraction_cache/<sha256>.json`."""
        data = self.model_dump(exclude={"source"})
        data["_prompt_version"] = PROMPT_VERSION
        data["_model"] = get_settings().llm_model
        return data


@dataclass
class ExtractionFailed:
    """Every failure mode collapses to this; the certificate becomes `failed`
    and the student gets the manual-entry form (REQ-037)."""

    reason: str = "extraction_failed"
    detail: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)


# -- Test seam ----------------------------------------------------------------

_adapter_override: Callable[[bytes, str], Any] | None = None


def set_adapter_for_tests(fn: Callable[[bytes, str], Any] | None) -> None:
    """Replace the provider call. Used by TEST-14 and TEST-16 to simulate a
    timeout and schema-invalid output without spending a real call."""
    global _adapter_override
    _adapter_override = fn


# -- Cache --------------------------------------------------------------------


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def cache_dir() -> pathlib.Path:
    return pathlib.Path(get_settings().extraction_cache_dir)


def cache_path(sha256: str) -> pathlib.Path:
    return cache_dir() / (sha256 + ".json")


def read_cache(sha256: str) -> Extraction | None:
    path = cache_path(sha256)
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        log.warning("extraction cache entry unreadable", extra={"sha256": sha256})
        return None
    raw = {k: v for k, v in raw.items() if not k.startswith("_")}
    raw.pop("source", None)
    try:
        return Extraction(source="cache", **raw)
    except ValidationError:
        log.warning("extraction cache entry does not validate", extra={"sha256": sha256})
        return None


def write_cache(sha256: str, extraction: Extraction) -> pathlib.Path:
    path = cache_path(sha256)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(
        extraction.cache_payload(), indent=2, sort_keys=True, ensure_ascii=False
    )
    path.write_text(body + "\n", encoding="utf-8")
    return path


# -- Daily cap (ENT-15 Counter) -----------------------------------------------


def _today_iso() -> str:
    s = get_settings()
    override = getattr(s, "today_override", "") or ""
    if override:
        return str(override)
    # Calendar dates are Asia/Kolkata (architecture 5), so the daily cap rolls
    # over at IST midnight rather than the server's.
    ist = dt.timezone(dt.timedelta(hours=5, minutes=30))
    return dt.datetime.now(tz=ist).date().isoformat()


def cap_reached(tx: Any = None) -> bool:
    """True when today's call count has reached max_llm_calls_per_day.

    `tx` may be None in cache-only paths and in unit tests; without a
    transaction there is no counter to read, so the cap cannot bind.
    """
    if tx is None:
        return False
    from app.repos import ml_repo

    limit = int(get_settings().max_llm_calls_per_day)
    used = ml_repo.get_counter(tx, "llm_calls", _today_iso())
    return used >= limit


def record_call(tx: Any = None) -> None:
    if tx is None:
        return
    from app.repos import ml_repo

    ml_repo.increment_counter(tx, "llm_calls", _today_iso())


# -- Image preparation --------------------------------------------------------


def prepare_image_png(file_bytes: bytes, media_type: str) -> bytes:
    """Return PNG bytes for the provider, whatever came in.

    Images: EXIF orientation applied, converted to RGB, longest side capped at
    1568 px, re-encoded through Pillow (which also drops anything odd in the
    original container, SEC-06). PDFs: page 1 rendered at 150 dpi, because the
    provider accepts images only (ai-system 2.1).
    """
    if media_type == "application/pdf":
        return render_pdf_first_page(file_bytes)

    from PIL import Image, ImageOps

    with Image.open(io.BytesIO(file_bytes)) as img:
        oriented = ImageOps.exif_transpose(img) or img
        rgb = oriented.convert("RGB")
        rgb.thumbnail((MAX_IMAGE_EDGE, MAX_IMAGE_EDGE))
        buf = io.BytesIO()
        rgb.save(buf, format="PNG")
        return buf.getvalue()


def render_pdf_first_page(file_bytes: bytes) -> bytes:
    """Page 1 as PNG at PDF_RENDER_DPI. Also used by the pHash check (3 rule 2),
    so a PDF is rasterised with identical settings wherever it is inspected."""
    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(file_bytes)
    try:
        if len(doc) == 0:
            raise ValueError("pdf has no pages")
        bitmap = doc[0].render(scale=PDF_RENDER_DPI / 72)
        img = bitmap.to_pil().convert("RGB")
        img.thumbnail((MAX_IMAGE_EDGE, MAX_IMAGE_EDGE))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    finally:
        doc.close()


# -- The provider call --------------------------------------------------------


def call_groq(file_bytes: bytes, media_type: str) -> Any:
    """One Groq call, validated against the 2.2 schema.

    Retries once on an unparseable or schema-invalid body, per 2.2. A refusal,
    a timeout or a second invalid body ends as `failed`.
    """
    from groq import Groq

    s = get_settings()
    client = Groq(
        api_key=s.groq_api_key,
        timeout=float(s.llm_timeout_s),
        max_retries=1,
    )
    png = prepare_image_png(file_bytes, media_type)
    data_url = "data:image/png;base64," + base64.b64encode(png).decode("ascii")

    request: dict[str, Any] = {
        "model": s.llm_model,
        "max_tokens": 2048,
        "temperature": 0,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
                    {"type": "text", "text": prompt_text()},
                ],
            }
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "certificate_extraction",
                "strict": True,
                "schema": output_schema(),
            },
        },
    }

    last_detail: str | None = None
    for attempt in (1, 2):
        started = time.monotonic()
        outcome = "error"
        usage: Any = None
        result: Any = None
        try:
            response = client.chat.completions.create(**request)
            choice = response.choices[0]
            usage = response.usage
            if choice.finish_reason not in ("stop", None):
                # Length-capped or refused: fail rather than guess at fields.
                outcome = "refusal" if choice.finish_reason == "refusal" else "invalid"
                last_detail = "finish_reason=" + str(choice.finish_reason)
            else:
                payload = json.loads(choice.message.content or "")
                result = Extraction(source="llm", **payload)
                outcome = "ok"
        except json.JSONDecodeError as exc:
            outcome = "invalid"
            last_detail = "non-JSON body: " + str(exc)
        except Exception as exc:  # noqa: BLE001 - JOB-01: any exception means `failed`
            name = type(exc).__name__
            outcome = "timeout" if "timeout" in name.lower() else "error"
            last_detail = name
        finally:
            # SEC-15: identifiers and counters only. Never the file, the base64
            # payload, the extracted holder name, or the key.
            log.info(
                "mdl-01 call",
                extra={
                    "model": s.llm_model,
                    "prompt_version": PROMPT_VERSION,
                    "cache_hit": False,
                    "attempt": attempt,
                    "input_tokens": getattr(usage, "prompt_tokens", None),
                    "output_tokens": getattr(usage, "completion_tokens", None),
                    "latency_ms": int((time.monotonic() - started) * 1000),
                    "outcome": outcome,
                },
            )
        if result is not None:
            return result
    return ExtractionFailed(detail=last_detail)


# -- Entry point --------------------------------------------------------------


def extract(
    file_bytes: bytes,
    media_type: str,
    tx: Any = None,
    sha256: str | None = None,
) -> Any:
    """Extract certificate fields, preferring the cache over the network."""
    digest = sha256 or sha256_hex(file_bytes)

    cached = read_cache(digest)
    if cached is not None:
        log.info(
            "mdl-01 call",
            extra={"cache_hit": True, "prompt_version": PROMPT_VERSION, "outcome": "ok"},
        )
        return cached

    provider = str(get_settings().llm_provider).lower()
    if provider == "none":
        return ExtractionFailed(detail="cache miss with llm_provider=none")

    if cap_reached(tx):
        log.warning("mdl-01 daily cap reached; routing to manual entry")
        return ExtractionFailed(detail="daily call cap reached")

    adapter = _adapter_override or call_groq
    record_call(tx)
    result = adapter(file_bytes, media_type)

    if isinstance(result, Extraction):
        try:
            write_cache(digest, result)
        except OSError:
            log.warning("could not write extraction cache entry")
    return result
