"""MDL-02: the local sentence embedder and the two text builders.

Model: `sentence-transformers/all-MiniLM-L6-v2`, 384-d, normalised, cosine.
It is baked into the image at `HF_HOME` (backend/Dockerfile) and loaded once at
startup, so no request ever waits for a download (ai-system §5, RISK-08).
"""

from __future__ import annotations

import logging
import math
import os
import threading
from typing import Any

from app.ml.settings import get_settings
from app.repos import ml_repo

log = logging.getLogger(__name__)

EMBEDDING_DIM = 384

_model: Any = None
_lock = threading.Lock()


def load_model() -> Any:
    """Load the model once. Raises if it cannot be loaded (FM-08)."""
    global _model
    if _model is not None:
        return _model
    with _lock:
        if _model is not None:
            return _model
        name = get_settings().embedding_model
        try:
            from sentence_transformers import SentenceTransformer
        except Exception as exc:  # pragma: no cover - import-time environment fault
            raise RuntimeError(
                f"sentence-transformers is not importable, so {name} cannot be loaded"
            ) from exc
        try:
            model = SentenceTransformer(name)
        except Exception as exc:
            # The usual cause is a model that was never baked into the image, so
            # name HF_HOME: that is the knob the reader needs (FM-08).
            raise RuntimeError(
                f"could not load embedding model {name!r} from HF_HOME="
                f"{os.environ.get('HF_HOME', '<unset>')!r}. The model is baked at "
                "image build time; rebuild the backend image."
            ) from exc
        dim = model.get_embedding_dimension()
        if dim != EMBEDDING_DIM:
            # The vector indexes in schema.cypher are fixed at 384 (audit H1).
            raise RuntimeError(
                f"embedding model {name!r} has dimension {dim}, but the Neo4j "
                f"vector indexes require {EMBEDDING_DIM}"
            )
        _model = model
        log.info("embedding model loaded", extra={"model": name, "dim": dim})
        return _model


def embed(texts: list[str]) -> list[list[float]]:
    """Embed texts into normalised 384-d vectors, in the order given."""
    if not texts:
        return []
    vectors = load_model().encode(
        texts, normalize_embeddings=True, show_progress_bar=False
    )
    return [[float(x) for x in row] for row in vectors]


def embed_one(text: str) -> list[float]:
    return embed([text])[0]


def cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity. Vectors from `embed` are already unit length, but the
    division is kept so stored vectors from any source behave correctly."""
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


# ── Text builders (ai-system §5; the exact strings are part of the contract) ──


def _join(values: Any) -> str:
    if not values:
        return ""
    return ", ".join(str(v) for v in values if v)


def _sentence(value: Any) -> str:
    """A field that the template follows with ". ".

    The templates in ai-system 5 append a full stop after the title and the
    description. Seed descriptions already end in one, which would render
    "...in the field.. Requires:", so a trailing terminator is dropped first.
    One separator, never two; the wording itself is untouched.
    """
    text = str(value or "").strip()
    return text[:-1].rstrip() if text.endswith((".", "!", "?")) else text


def student_text(profile: dict[str, Any]) -> str:
    """"{dept} student. Skills: {names}. Interests: {interests}. Certificates:
    {certified titles}. {bio}" """
    text = (
        f"{profile.get('dept_code') or ''} student. "
        f"Skills: {_sentence(_join(profile.get('skills')))}. "
        f"Interests: {_sentence(_join(profile.get('interests')))}. "
        f"Certificates: {_sentence(_join(profile.get('certificate_titles')))}. "
        f"{str(profile.get('bio') or '').strip()}"
    ).strip()
    # Richer-profile extras (plan section 4.3), appended only when present so an old profile reads exactly as before.
    extras = []
    if profile.get("programme"):
        extras.append(f"Programme: {profile['programme']}.")
    if profile.get("year"):
        extras.append(f"Year {profile['year']}.")
    if profile.get("headline"):
        extras.append(f"{_sentence(profile['headline'])}.")
    if profile.get("project_titles"):
        extras.append(f"Projects: {_sentence(_join(profile['project_titles']))}.")
    return " ".join([text, *extras]).strip()


def opening_text(opening: dict[str, Any]) -> str:
    """"{title}. {description}. Requires: {concept names}." """
    text = (
        f"{_sentence(opening.get('title'))}. "
        f"{_sentence(opening.get('description'))}. "
        f"Requires: {_sentence(_join(opening.get('required_concepts')))}."
    ).strip()
    # The faculty member's domain and the nice-to-have skills (plan section 4.3), only when present.
    extras = []
    if opening.get("preferred_concepts"):
        extras.append(f"Preferred: {_sentence(_join(opening['preferred_concepts']))}.")
    if opening.get("faculty_research"):
        extras.append(f"Faculty research: {_sentence(_join(opening['faculty_research']))}.")
    if opening.get("faculty_subjects"):
        extras.append(f"Faculty teaches: {_sentence(_join(opening['faculty_subjects']))}.")
    return " ".join([text, *extras]).strip()


# ── Recompute hooks (called by P2's services and P4's seed) ───────────────────


def recompute_student_embedding(tx, student_id: str) -> list[float] | None:
    """Rebuild and store a student's embedding. Returns the vector, or None if
    the student does not exist."""
    parts = ml_repo.student_text_parts(tx, student_id)
    if parts is None:
        return None
    vector = embed_one(student_text(parts))
    ml_repo.write_student_embedding(tx, student_id, vector)
    return vector


def recompute_opening_embedding(tx, opening_id: str) -> list[float] | None:
    parts = ml_repo.opening_text_parts(tx, opening_id)
    if parts is None:
        return None
    vector = embed_one(opening_text(parts))
    ml_repo.write_opening_embedding(tx, opening_id, vector)
    return vector
