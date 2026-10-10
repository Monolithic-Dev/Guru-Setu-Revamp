"""TEST-18: the fit scorer against the ai-system 4 worked example.

Pure unit tests - no database, no model, no settings. The numbers here are the
ones written into the spec and into the API-015 example in backend 4.1, so a
change in the formula fails here first.
"""

from __future__ import annotations

import math

import pytest

from app.ml.scorer import (
    FIT_WEIGHTS,
    TRUST_WEIGHTS,
    FitConfig,
    idf,
    rank_candidates,
    score,
    with_gains,
)

# The worked example: four required skills with equal idf, so the idf value
# itself cancels out of every ratio. 1.0 keeps the arithmetic readable.
REQUIRED = ["python", "pytorch", "deep learning", "computer vision"]
IDF = {name: 1.0 for name in REQUIRED}
SIMILAR = {("deep learning", "computer vision"): 0.70}
SEMANTIC = 0.70  # fixed, as the spec fixes it for illustration

BEFORE_SKILLS = {"python": 1, "pytorch": 0, "deep learning": 0}
AFTER_SKILLS = {"python": 1, "pytorch": 1, "deep learning": 1, "computer vision": 1}

CFG = FitConfig(fit_ready_min=65.0, fit_close_min=40.0, sim_min=0.60)


def test_constants_match_the_spec():
    assert TRUST_WEIGHTS == {0: 0.40, 1: 0.85, 2: 1.00}
    assert FIT_WEIGHTS == {"semantic": 0.25, "skill": 0.60, "concept": 0.15}


def test_before_uploads_is_43_4_and_close():
    fit = score(REQUIRED, IDF, BEFORE_SKILLS, SIMILAR, SEMANTIC, CFG)
    assert fit.components == {"semantic": 17.5, "skill": 24.8, "concept": 1.1}
    assert fit.score == 43.4
    assert fit.verdict == "close"
    assert fit.verdict_text == "Close: certify the skills below to improve your fit"


def test_after_uploads_is_68_5_and_ready():
    fit = score(REQUIRED, IDF, AFTER_SKILLS, SIMILAR, SEMANTIC, CFG)
    assert fit.components == {"semantic": 17.5, "skill": 51.0, "concept": 0.0}
    assert fit.score == 68.5
    assert fit.verdict == "ready"
    assert fit.verdict_text == "Ready to apply"


def test_components_sum_to_the_score_exactly():
    """AC-004.2: the three numbers on screen must add up to the number on screen."""
    for skills in (BEFORE_SKILLS, AFTER_SKILLS, {}, {"python": 2}):
        fit = score(REQUIRED, IDF, skills, SIMILAR, SEMANTIC, CFG)
        parts = fit.components
        assert parts["semantic"] + parts["skill"] + parts["concept"] == fit.score


def test_chips_before_uploads():
    fit = score(REQUIRED, IDF, BEFORE_SKILLS, SIMILAR, SEMANTIC, CFG)
    by_concept = {c.concept: c for c in fit.chips}

    assert by_concept["python"].kind == "matched"
    assert by_concept["python"].trust_level == 1
    assert by_concept["pytorch"].kind == "claimed_only"
    assert by_concept["deep learning"].kind == "claimed_only"

    near = by_concept["computer vision"]
    assert near.kind == "near"
    assert near.via == "deep learning"
    assert near.similarity == 0.70


def test_claimed_only_is_not_matched():
    """Trust 0 is a claim, not evidence: it must never read as Certified."""
    fit = score(["pytorch"], {"pytorch": 1.0}, {"pytorch": 0}, {}, 0.0, CFG)
    assert fit.chips[0].kind == "claimed_only"
    assert fit.matched_count == 0


def test_gains_match_the_api_015_example():
    fit = score(REQUIRED, IDF, BEFORE_SKILLS, SIMILAR, SEMANTIC, CFG)
    fit = with_gains(fit, REQUIRED, IDF, BEFORE_SKILLS, SIMILAR, SEMANTIC, CFG)
    assert fit.gains == [
        {"concept": "computer vision", "score_if_certified": 55.0},
        {"concept": "deep learning", "score_if_certified": 51.2},
        {"concept": "pytorch", "score_if_certified": 50.1},
    ]


def test_gains_exclude_already_matched_skills():
    fit = score(REQUIRED, IDF, BEFORE_SKILLS, SIMILAR, SEMANTIC, CFG)
    fit = with_gains(fit, REQUIRED, IDF, BEFORE_SKILLS, SIMILAR, SEMANTIC, CFG)
    assert "python" not in {g["concept"] for g in fit.gains}


@pytest.mark.parametrize(
    "total, expected",
    [(39.9, "not_yet"), (40.0, "close"), (64.9, "close"), (65.0, "ready")],
)
def test_verdict_boundaries(total, expected):
    """The exact boundary values named in TEST-18. Driven through the real
    scorer by choosing a semantic value that lands on each total."""
    fit = score([], {}, {}, {}, total / 100.0, CFG)
    assert fit.score == pytest.approx(total, abs=0.05)
    assert fit.verdict == expected


def test_empty_requirements_returns_semantic_only_with_a_note():
    fit = score([], {}, {"python": 2}, {}, 0.80, CFG)
    assert fit.components == {"semantic": 80.0, "skill": 0.0, "concept": 0.0}
    assert fit.score == 80.0
    assert fit.note == "This opening lists no required skills"
    assert fit.chips == []


def test_negative_cosine_is_clamped_to_zero():
    """An opposing embedding must not subtract from an earned skill score."""
    fit = score(["python"], {"python": 1.0}, {"python": 1}, {}, -0.4, CFG)
    assert fit.components["semantic"] == 0.0


def test_similarity_below_sim_min_is_missing_not_near():
    weak = {("deep learning", "computer vision"): 0.59}
    fit = score(["computer vision"], {"computer vision": 1.0},
                {"deep learning": 1}, weak, 0.0, CFG)
    assert fit.chips[0].kind == "missing"
    assert fit.components["concept"] == 0.0


def test_similar_to_is_undirected():
    """Stored one way round, usable either way (ENT-20)."""
    forward = score(["computer vision"], {"computer vision": 1.0},
                    {"deep learning": 1},
                    {("deep learning", "computer vision"): 0.7}, 0.0, CFG)
    reverse = score(["computer vision"], {"computer vision": 1.0},
                    {"deep learning": 1},
                    {("computer vision", "deep learning"): 0.7}, 0.0, CFG)
    assert forward.score == reverse.score
    assert forward.chips[0].via == reverse.chips[0].via == "deep learning"


def test_near_picks_the_highest_value_neighbour():
    """Best is score x trust, not score alone: a certified weaker synonym beats
    a merely claimed stronger one."""
    similar = {
        ("computer vision", "deep learning"): 0.70,  # claimed only -> 0.70*0.40
        ("computer vision", "edge ai"): 0.65,        # certified    -> 0.65*0.85
    }
    fit = score(["computer vision"], {"computer vision": 1.0},
                {"deep learning": 0, "edge ai": 1}, similar, 0.0, CFG)
    assert fit.chips[0].via == "edge ai"


def test_idf_rewards_rarer_skills():
    common = idf("python", open_openings=12, df=12)
    rare = idf("computer vision", open_openings=12, df=1)
    assert rare > common
    assert common == math.log(1 + 12 / 13)


def test_rare_required_skill_dominates_the_skill_part():
    idf_values = {"python": idf("python", 12, 12), "computer vision": idf("computer vision", 12, 1)}
    holds_rare = score(["python", "computer vision"], idf_values,
                       {"computer vision": 1}, {}, 0.0, CFG)
    holds_common = score(["python", "computer vision"], idf_values,
                         {"python": 1}, {}, 0.0, CFG)
    assert holds_rare.score > holds_common.score


def test_source_is_attached_only_to_matched_chips():
    sources = {"python": {"evidence_id": "ev-1", "title": "Python for Everybody"}}
    fit = score(["python", "pytorch"], {"python": 1.0, "pytorch": 1.0},
                {"python": 1, "pytorch": 0}, {}, 0.0, CFG, sources)
    chips = {c.concept: c.as_dict() for c in fit.chips}
    assert chips["python"]["source"] == sources["python"]
    assert "source" not in chips["pytorch"]


def test_rank_candidates_breaks_ties_on_matched_then_time():
    high = score(REQUIRED, IDF, AFTER_SKILLS, SIMILAR, SEMANTIC, CFG)
    low = score(REQUIRED, IDF, BEFORE_SKILLS, SIMILAR, SEMANTIC, CFG)
    tie_a = score(REQUIRED, IDF, BEFORE_SKILLS, SIMILAR, SEMANTIC, CFG)

    ranked = rank_candidates([
        {"id": "low", "fit": low, "applied_at": "2026-10-02T00:00:00Z"},
        {"id": "high", "fit": high, "applied_at": "2026-10-03T00:00:00Z"},
        {"id": "tie-earlier", "fit": tie_a, "applied_at": "2026-10-01T00:00:00Z"},
    ])
    assert [e["id"] for e in ranked] == ["high", "tie-earlier", "low"]


def test_trust_2_scores_above_trust_1():
    endorsed = score(["python"], {"python": 1.0}, {"python": 2}, {}, 0.0, CFG)
    certified = score(["python"], {"python": 1.0}, {"python": 1}, {}, 0.0, CFG)
    claimed = score(["python"], {"python": 1.0}, {"python": 0}, {}, 0.0, CFG)
    assert endorsed.score > certified.score > claimed.score
