"""MDL-04: concept normalisation and the SIMILAR_TO graph.

A skill name arrives from three places - a student's claimed list, an LLM
extraction, or an opening's requirements - and all three funnel through
`normalise` so "DL", "dl " and "Deep Learning" become one `Concept`.
"""

from __future__ import annotations

import functools
import json
import logging
import pathlib
import re
from typing import Any

from app.ml import embedding
from app.ml.settings import get_settings
from app.repos import ml_repo

log = logging.getLogger(__name__)

SEED_DIR = pathlib.Path(__file__).resolve().parents[2] / "seed"
ALIASES_PATH = SEED_DIR / "aliases.json"
OVERRIDES_PATH = SEED_DIR / "similar_overrides.json"

TOP_K_NEIGHBOURS = 5
MAX_CONCEPT_NAME = 40

_WS = re.compile(r"\s+")


@functools.lru_cache(maxsize=1)
def _aliases() -> dict[str, str]:
    if not ALIASES_PATH.exists():
        log.warning("aliases file missing", extra={"path": str(ALIASES_PATH)})
        return {}
    raw = json.loads(ALIASES_PATH.read_text(encoding="utf-8"))
    return {k: v for k, v in raw.items() if not k.startswith("_")}


@functools.lru_cache(maxsize=1)
def _overrides() -> list[tuple[str, str, float]]:
    if not OVERRIDES_PATH.exists():
        return []
    raw = json.loads(OVERRIDES_PATH.read_text(encoding="utf-8"))
    out = []
    for a, b, score in raw.get("pairs", []):
        out.append((normalise(a), normalise(b), float(score)))
    return out


def normalise(name: str) -> str:
    """Lower-case, trim, collapse spaces, then map through `seed/aliases.json`.

    Aliases are applied after whitespace folding so the file can key on clean
    names, and the result is clipped to Concept.name's 40-character limit
    (ENT-03).
    """
    cleaned = _WS.sub(" ", (name or "").strip().lower())
    if not cleaned:
        return ""
    return _aliases().get(cleaned, cleaned)[:MAX_CONCEPT_NAME]


def normalise_all(names: list[str]) -> list[str]:
    """Normalise, drop blanks, de-duplicate, preserve first-seen order."""
    seen: dict[str, None] = {}
    for n in names or []:
        c = normalise(n)
        if c:
            seen.setdefault(c, None)
    return list(seen)


# ── Concept creation ─────────────────────────────────────────────────────────


def get_or_create_concept(tx, name: str, source: str) -> str | None:
    """Return the canonical concept name, creating the node if it is new.

    A new concept is embedded and immediately linked to its nearest existing
    neighbours, so a skill extracted from a certificate can take part in the
    `near` branch of the fit score straight away (ai-system §4 step 2).
    """
    canonical = normalise(name)
    if not canonical:
        return None
    if ml_repo.get_concept(tx, canonical) is not None:
        return canonical

    vector = embedding.embed_one(canonical)
    ml_repo.create_concept(tx, canonical, source, vector)
    _link_neighbours(tx, canonical, vector)
    return canonical


def _link_neighbours(tx, name: str, vector: list[float]) -> None:
    """Top-5 neighbours of one concept with cosine >= sim_min."""
    sim_min = float(get_settings().sim_min)
    others = [c for c in ml_repo.concepts_with_embeddings(tx) if c["name"] != name]
    scored = [
        (other["name"], embedding.cosine(vector, other["embedding"]))
        for other in others
    ]
    scored = [(n, s) for n, s in scored if s >= sim_min]
    scored.sort(key=lambda pair: (-pair[1], pair[0]))
    for other_name, score in scored[:TOP_K_NEIGHBOURS]:
        ml_repo.upsert_similar(tx, name, other_name, round(float(score), 4), "model")
    _apply_overrides_touching(tx, name)


def _apply_overrides_touching(tx, name: str) -> None:
    for a, b, score in _overrides():
        if name in (a, b):
            ml_repo.upsert_similar(tx, a, b, score, "override")


# ── Seed-time rebuild ────────────────────────────────────────────────────────


def rebuild_similarity(tx) -> dict[str, int]:
    """Rebuild SIMILAR_TO over every concept, then apply the override file.

    Called by `scripts/seed.py` (P4 owns the call site). Overrides are applied
    last and win, including for pairs the model scored below sim_min - that is
    what pins `deep learning`-`computer vision` to 0.70 for the demo (A-16).
    """
    sim_min = float(get_settings().sim_min)
    concepts = ml_repo.concepts_with_embeddings(tx)
    if not concepts:
        return {"concepts": 0, "model_edges": 0, "override_edges": 0}

    ml_repo.delete_model_similar(tx)

    names = [c["name"] for c in concepts]
    vectors = [c["embedding"] for c in concepts]

    # Keep each pair once: the top-k is computed per concept, then the pair set
    # is de-duplicated with the alphabetically smaller name first (§5).
    pairs: dict[tuple[str, str], float] = {}
    for i, name in enumerate(names):
        scored = [
            (names[j], embedding.cosine(vectors[i], vectors[j]))
            for j in range(len(names))
            if j != i
        ]
        scored = [(n, s) for n, s in scored if s >= sim_min]
        scored.sort(key=lambda pair: (-pair[1], pair[0]))
        for other, score in scored[:TOP_K_NEIGHBOURS]:
            key = tuple(sorted((name, other)))  # type: ignore[assignment]
            pairs[key] = max(pairs.get(key, 0.0), round(float(score), 4))

    for (lo, hi), score in pairs.items():
        ml_repo.upsert_similar(tx, lo, hi, score, "model")

    known = set(names)
    override_count = 0
    for a, b, score in _overrides():
        if a in known and b in known:
            ml_repo.upsert_similar(tx, a, b, score, "override")
            override_count += 1
        else:
            log.info(
                "similarity override skipped: concept absent from the seed",
                extra={"pair": [a, b]},
            )

    stats = {
        "concepts": len(names),
        "model_edges": len(pairs),
        "override_edges": override_count,
    }
    log.info("SIMILAR_TO rebuilt", extra=stats)
    return stats


def similar_map(tx, names: list[str]) -> dict[tuple[str, str], float]:
    """{(a, b): score} for pairs touching `names`, both directions present."""
    out: dict[tuple[str, str], float] = {}
    for row in ml_repo.similar_for_concepts(tx, names):
        a, b, score = row["from_name"], row["to_name"], float(row["score"])
        out[(a, b)] = score
        out[(b, a)] = score
    return out


def reload_files() -> None:
    """Drop the cached alias/override files (used by tests and the seed)."""
    _aliases.cache_clear()
    _overrides.cache_clear()


def load_json_or_default(path: pathlib.Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))
