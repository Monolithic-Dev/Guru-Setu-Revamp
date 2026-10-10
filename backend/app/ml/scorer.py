"""MDL-03: the hybrid fit scorer (ai-system 4). Pure Python, no model, no I/O.

`score()` takes everything it needs as arguments so it can be unit-tested
exactly (TEST-18) and so the same function serves the student's Fit Check, the
faculty candidate ranking, the why-paths and the skill-gap list.

Three parts, weighted 0.25 / 0.60 / 0.15:
  semantic  cosine between the student and opening embeddings
  skill     rarity-weighted sum over required skills the student holds
  concept   the same, for required skills reached through a SIMILAR_TO hop

Each component is rounded first and the score is their sum, so the three
numbers shown in the UI always add up to the score exactly (AC-004.2).
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal, getcontext
from typing import Any

# A-10: starting values, tuned only against EVAL-03 before the core freeze.
TRUST_WEIGHTS = {0: 0.40, 1: 0.85, 2: 1.00}
FIT_WEIGHTS = {"semantic": 0.25, "skill": 0.60, "concept": 0.15}

# The components are computed in Decimal, not float. The spec's worked example
# needs round(100*0.15*0.07, 1) == 1.1, but in binary that product is
# 1.0499999999999998, which rounds to 1.0 - and a float sum of the three parts
# would then not equal the displayed score. Decimal makes the arithmetic the
# decimal arithmetic the spec describes, and makes the demo's headline numbers
# identical on every machine instead of subject to float jitter.
getcontext().prec = 28
_ONE_DP = Decimal("0.1")

_TRUST_D = {0: Decimal("0.40"), 1: Decimal("0.85"), 2: Decimal("1.00")}
_WEIGHT_D = {
    "semantic": Decimal("0.25"),
    "skill": Decimal("0.60"),
    "concept": Decimal("0.15"),
}
_HUNDRED = Decimal(100)


def _dec(value: Any) -> Decimal:
    """Float to Decimal via its shortest repr, so 0.7 becomes exactly 0.7."""
    return Decimal(str(value))


def _round_1dp(value: Decimal) -> float:
    return float(value.quantize(_ONE_DP, rounding=ROUND_HALF_UP))

NO_REQUIREMENTS_NOTE = "This opening lists no required skills"

VERDICT_TEXT = {
    "ready": "Ready to apply",
    "close": "Close: certify the skills below to improve your fit",
    "not_yet": "Not yet: see missing skills",
}


@dataclass
class FitConfig:
    """The thresholds the scorer reads (backend 8). Passed in, never imported,
    so a test can move a boundary without touching global settings."""

    fit_ready_min: float = 65.0
    fit_close_min: float = 40.0
    sim_min: float = 0.60

    @classmethod
    def from_settings(cls, settings: Any) -> FitConfig:
        return cls(
            fit_ready_min=float(settings.fit_ready_min),
            fit_close_min=float(settings.fit_close_min),
            sim_min=float(settings.sim_min),
        )


@dataclass
class Chip:
    """One required skill, as the UI shows it."""

    concept: str
    kind: str  # matched | claimed_only | near | missing
    trust_level: int | None = None
    via: str | None = None
    similarity: float | None = None
    source: dict[str, str] | None = None

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "concept": self.concept,
            "kind": self.kind,
            "trust_level": self.trust_level,
        }
        # Private-ish extras are omitted, not nulled, when they do not apply -
        # the same convention the API uses elsewhere.
        if self.via is not None:
            out["via"] = self.via
        if self.similarity is not None:
            out["similarity"] = self.similarity
        if self.source is not None:
            out["source"] = self.source
        return out


@dataclass
class Fit:
    score: float
    components: dict[str, float]
    verdict: str
    verdict_text: str
    chips: list[Chip] = field(default_factory=list)
    gains: list[dict[str, Any]] = field(default_factory=list)
    note: str | None = None

    @property
    def matched_count(self) -> int:
        return sum(1 for c in self.chips if c.kind == "matched")

    def as_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "components": self.components,
            "weights": dict(FIT_WEIGHTS),
            "verdict": self.verdict,
            "verdict_text": self.verdict_text,
            "chips": [c.as_dict() for c in self.chips],
            "gains": self.gains,
            "note": self.note,
        }


def idf(concept: str, open_openings: int, df: int) -> float:
    """ln(1 + N / (1 + df)): a skill every opening wants carries less weight
    than a rare one, so the score rewards the skills that actually distinguish
    candidates."""
    return math.log(1 + open_openings / (1 + df))


def idf_table_from_counts(
    df_by_concept: dict[str, int], open_openings: int
) -> dict[str, float]:
    return {c: idf(c, open_openings, df) for c, df in df_by_concept.items()}


def verdict_for(score: float, cfg: FitConfig) -> str:
    if score >= cfg.fit_ready_min:
        return "ready"
    if score >= cfg.fit_close_min:
        return "close"
    return "not_yet"




def _similarity(
    similar: dict[tuple[str, str], float], a: str, b: str
) -> float | None:
    """SIMILAR_TO is undirected; accept either key order."""
    if (a, b) in similar:
        return similar[(a, b)]
    return similar.get((b, a))


def score(
    required: Iterable[str],
    idf_values: dict[str, float],
    skills: dict[str, int],
    similar: dict[tuple[str, str], float],
    semantic: float,
    cfg: FitConfig | None = None,
    sources: dict[str, dict[str, str]] | None = None,
) -> Fit:
    """Compute one student-opening fit.

    required  required concept names, in display order
    idf_values{concept: idf} over open openings
    skills    {concept: trust_level} the student holds
    similar   {(a, b): score} SIMILAR_TO pairs
    semantic  cosine(student.embedding, opening.embedding)
    sources   {concept: {evidence_id, title}} for the first proving certificate
    """
    cfg = cfg or FitConfig()
    sources = sources or {}
    required = list(required)

    semantic = max(0.0, float(semantic))
    semantic_d = _dec(semantic)

    # An opening with no required skills cannot have a skill or concept part;
    # saying so is more honest than showing two zero bars (ai-system 4).
    if not required:
        semantic_c = _round_1dp(_HUNDRED * semantic_d)
        total = semantic_c
        verdict = verdict_for(total, cfg)
        return Fit(
            score=total,
            components={"semantic": semantic_c, "skill": 0.0, "concept": 0.0},
            verdict=verdict,
            verdict_text=VERDICT_TEXT[verdict],
            chips=[],
            gains=[],
            note=NO_REQUIREMENTS_NOTE,
        )

    weight_total = sum((_dec(idf_values.get(r, 0.0)) for r in required), Decimal(0))

    chips: list[Chip] = []
    skill_sum = Decimal(0)
    concept_sum = Decimal(0)

    for r in required:
        r_idf = _dec(idf_values.get(r, 0.0))

        if r in skills:
            trust = int(skills[r])
            skill_sum += r_idf * _TRUST_D.get(trust, Decimal(0))
            chips.append(
                Chip(
                    concept=r,
                    kind="matched" if trust >= 1 else "claimed_only",
                    trust_level=trust,
                    source=sources.get(r) if trust >= 1 else None,
                )
            )
            continue

        # Not held directly: find the best neighbour the student does hold.
        best: tuple[Decimal, str, float, int] | None = None
        for held, held_trust in skills.items():
            sim = _similarity(similar, r, held)
            if sim is None or sim < cfg.sim_min:
                continue
            value = _dec(sim) * _TRUST_D.get(int(held_trust), Decimal(0))
            candidate = (value, held, sim, int(held_trust))
            if best is None or value > best[0] or (value == best[0] and held < best[1]):
                best = candidate

        if best is not None:
            value, via, sim, via_trust = best
            concept_sum += r_idf * value
            chips.append(
                Chip(
                    concept=r,
                    kind="near",
                    trust_level=via_trust,
                    via=via,
                    similarity=round(sim, 4),
                )
            )
        else:
            chips.append(Chip(concept=r, kind="missing", trust_level=None))

    zero = Decimal(0)
    skill_part = (skill_sum / weight_total) if weight_total else zero
    concept_part = (concept_sum / weight_total) if weight_total else zero

    semantic_c = _round_1dp(_HUNDRED * _WEIGHT_D["semantic"] * semantic_d)
    skill_c = _round_1dp(_HUNDRED * _WEIGHT_D["skill"] * skill_part)
    concept_c = _round_1dp(_HUNDRED * _WEIGHT_D["concept"] * concept_part)
    # Sum the rounded components in Decimal too, so the total is exactly what
    # the three displayed numbers add up to (AC-004.2).
    total = float(_dec(semantic_c) + _dec(skill_c) + _dec(concept_c))

    verdict = verdict_for(total, cfg)
    return Fit(
        score=total,
        components={"semantic": semantic_c, "skill": skill_c, "concept": concept_c},
        verdict=verdict,
        verdict_text=VERDICT_TEXT[verdict],
        chips=chips,
        gains=[],
        note=None,
    )


def with_gains(
    fit: Fit,
    required: Iterable[str],
    idf_values: dict[str, float],
    skills: dict[str, int],
    similar: dict[tuple[str, str], float],
    semantic: float,
    cfg: FitConfig | None = None,
    sources: dict[str, dict[str, str]] | None = None,
) -> Fit:
    """Attach "certify this and your score becomes N" for every skill that is
    not already matched, highest first."""
    cfg = cfg or FitConfig()
    gains: list[dict[str, Any]] = []
    for chip in fit.chips:
        if chip.kind == "matched":
            continue
        hypothetical = dict(skills)
        hypothetical[chip.concept] = 1  # certified
        improved = score(
            required, idf_values, hypothetical, similar, semantic, cfg, sources
        )
        gains.append(
            {"concept": chip.concept, "score_if_certified": improved.score}
        )
    gains.sort(key=lambda g: (-g["score_if_certified"], g["concept"]))
    fit.gains = gains
    return fit


def rank_candidates(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort applicants by fit, breaking ties by more matched chips, then by who
    applied first (REQ-005)."""
    return sorted(
        entries,
        key=lambda e: (
            -float(e["fit"].score),
            -int(e["fit"].matched_count),
            str(e.get("applied_at") or ""),
        ),
    )
