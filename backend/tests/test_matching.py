"""Fit assembly: API-015 shape, candidate ranking, why-paths and skill gaps.

Driven through `app.ml.fit` against a fake transaction, so these run without
FastAPI, Neo4j or P2's deps. The route-level scope rules (404-not-403) are
integration tests that belong with the live API.

Covers TEST-22 (candidates sorted by score) and TEST-39 (applicants only).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import pytest

from app.ml import fit as fit_service

# A unit vector pair with a known cosine, so `semantic` is predictable.
STUDENT_VEC = [1.0, 0.0]
OPENING_VEC = [0.70, math.sqrt(1 - 0.70**2)]  # cosine with STUDENT_VEC == 0.70

REQUIRED = ["python", "pytorch", "deep learning", "computer vision"]


@dataclass
class FakeSettings:
    fit_ready_min: float = 65.0
    fit_close_min: float = 40.0
    sim_min: float = 0.60


@dataclass
class FakeWorld:
    """Everything the fake repo answers from, in one place."""

    required: list[str] = field(default_factory=lambda: list(REQUIRED))
    skills: dict[str, int] = field(
        default_factory=lambda: {"python": 1, "pytorch": 0, "deep learning": 0}
    )
    sources: dict[str, dict[str, str]] = field(
        default_factory=lambda: {
            "python": {"evidence_id": "ev-aarav-python", "title": "Python for Everybody"}
        }
    )
    similar: dict[tuple[str, str], float] = field(
        default_factory=lambda: {
            ("deep learning", "computer vision"): 0.70,
            ("computer vision", "deep learning"): 0.70,
        }
    )
    idf: dict[str, float] = field(
        default_factory=lambda: {name: 1.0 for name in REQUIRED}
    )
    applicants: list[dict[str, Any]] = field(default_factory=list)
    per_student_skills: dict[str, dict[str, int]] = field(default_factory=dict)
    openings: list[dict[str, Any]] = field(default_factory=list)


@pytest.fixture
def world():
    return FakeWorld()


@pytest.fixture(autouse=True)
def _patch(monkeypatch, world):
    monkeypatch.setattr(fit_service, "get_settings", lambda: FakeSettings())
    repo = fit_service.match_repo

    monkeypatch.setattr(repo, "idf_table", lambda tx: world.idf)
    monkeypatch.setattr(
        repo, "similar_pairs", lambda tx, names: world.similar
    )
    monkeypatch.setattr(
        repo,
        "fit_inputs",
        lambda tx, opening_id, student_id: {
            "opening_id": opening_id,
            "opening_title": "Edge AI for Agriculture",
            "opening_status": "open",
            "opening_embedding": OPENING_VEC,
            "required": world.required,
            "student_embedding": STUDENT_VEC,
        },
    )

    def student_skills(tx, student_id):
        if student_id in world.per_student_skills:
            return world.per_student_skills[student_id], {}
        return world.skills, world.sources

    monkeypatch.setattr(repo, "student_skills", student_skills)
    monkeypatch.setattr(repo, "student_embedding", lambda tx, student_id: STUDENT_VEC)
    monkeypatch.setattr(repo, "my_application_statuses", lambda tx, student_id: {})
    monkeypatch.setattr(repo, "applicants", lambda tx, opening_id: world.applicants)
    monkeypatch.setattr(
        repo,
        "opening_detail",
        lambda tx, opening_id: {
            "id": opening_id,
            "title": "Edge AI for Agriculture",
            "description": "Edge deep learning for crops.",
            "status": "open",
            "embedding": OPENING_VEC,
            "faculty_id": "u-meera",
            "faculty_name": "Dr. Meera Raman",
            "required_skills": world.required,
            "applicant_count": len(world.applicants),
        },
    )
    monkeypatch.setattr(
        repo, "required_by_open_openings", lambda tx: world.openings
    )
    monkeypatch.setattr(
        repo,
        "openings",
        lambda tx, include_closed=False, limit=50: [
            {
                "id": "op-edge-ai",
                "title": "Edge AI for Agriculture",
                "status": "open",
                "description": "",
                "created_at": "2026-09-01T00:00:00Z",
                "embedding": OPENING_VEC,
                "faculty_id": "u-meera",
                "faculty_name": "Dr. Meera Raman",
                "required_skills": world.required,
            }
        ],
    )
    return world


TX = object()


# -- API-015 ------------------------------------------------------------------


def test_fit_matches_the_backend_4_1_example():
    """The worked example, end to end through the assembly layer."""
    payload = fit_service.fit_for(TX, "op-edge-ai", "u-aarav")

    assert payload["opening_id"] == "op-edge-ai"
    assert payload["student_id"] == "u-aarav"
    assert payload["score"] == 43.4
    assert payload["components"] == {"semantic": 17.5, "skill": 24.8, "concept": 1.1}
    assert payload["weights"] == {"semantic": 0.25, "skill": 0.60, "concept": 0.15}
    assert payload["verdict"] == "close"
    assert payload["gains"] == [
        {"concept": "computer vision", "score_if_certified": 55.0},
        {"concept": "deep learning", "score_if_certified": 51.2},
        {"concept": "pytorch", "score_if_certified": 50.1},
    ]


def test_fit_chips_carry_their_source_certificate():
    payload = fit_service.fit_for(TX, "op-edge-ai", "u-aarav")
    chips = {c["concept"]: c for c in payload["chips"]}
    assert chips["python"]["source"] == {
        "evidence_id": "ev-aarav-python",
        "title": "Python for Everybody",
    }
    assert "source" not in chips["pytorch"]


def test_fit_never_returns_an_embedding():
    """SEC-01: the vectors are read for the cosine and must not escape."""
    payload = fit_service.fit_for(TX, "op-edge-ai", "u-aarav")
    assert "embedding" not in payload
    for chip in payload["chips"]:
        assert "embedding" not in chip


def test_fit_after_certifying_three_skills_is_ready(world):
    world.skills = {
        "python": 1, "pytorch": 1, "deep learning": 1, "computer vision": 1,
    }
    payload = fit_service.fit_for(TX, "op-edge-ai", "u-aarav")
    assert payload["score"] == 68.5
    assert payload["verdict"] == "ready"


def test_missing_opening_returns_none(monkeypatch):
    monkeypatch.setattr(
        fit_service.match_repo, "fit_inputs", lambda tx, opening_id, student_id: None
    )
    assert fit_service.fit_for(TX, "nope", "u-aarav") is None


def test_opening_with_no_requirements_gets_the_note(world):
    world.required = []
    payload = fit_service.fit_for(TX, "op-edge-ai", "u-aarav")
    assert payload["note"] == "This opening lists no required skills"
    assert payload["components"]["skill"] == 0.0


# -- API-012 ------------------------------------------------------------------


def test_openings_list_carries_my_fit_and_application_status():
    rows = fit_service.fit_summary_for_openings(TX, "u-aarav")
    assert len(rows) == 1
    assert rows[0]["my_fit"] == {"score": 43.4, "verdict": "close"}
    assert rows[0]["my_application_status"] is None
    assert rows[0]["faculty"] == {"user_id": "u-meera", "name": "Dr. Meera Raman"}
    assert "embedding" not in rows[0]


# -- API-016: TEST-22 and TEST-39 --------------------------------------------


def _applicant(student_id: str, name: str, applied_at: str) -> dict[str, Any]:
    return {
        "application_id": f"app-{student_id}",
        "status": "pending",
        "applied_at": applied_at,
        "updated_at": applied_at,
        "student_id": student_id,
        "name": name,
        "roll_no": f"CB.EN.U4CSE24{student_id[-3:]}",
        "year": 3,
        "student_embedding": STUDENT_VEC,
    }


def test_candidates_are_sorted_by_score_descending(world):
    """TEST-22."""
    world.applicants = [
        _applicant("u-001", "Low Fit", "2026-10-01T00:00:00Z"),
        _applicant("u-002", "High Fit", "2026-10-02T00:00:00Z"),
        _applicant("u-003", "Mid Fit", "2026-10-03T00:00:00Z"),
    ]
    world.per_student_skills = {
        "u-001": {"python": 0},
        "u-002": {"python": 1, "pytorch": 1, "deep learning": 1, "computer vision": 1},
        "u-003": {"python": 1, "pytorch": 0, "deep learning": 0},
    }
    rows = fit_service.candidates_for_opening(TX, "op-edge-ai")

    scores = [r["fit"]["score"] for r in rows]
    assert scores == sorted(scores, reverse=True)
    assert rows[0]["student"]["name"] == "High Fit"
    assert rows[0]["fit"]["verdict"] == "ready"


def test_candidates_returns_only_applicants(world):
    """TEST-39 / NG-11: there is no path here that reaches a non-applicant."""
    world.applicants = [_applicant("u-001", "Applicant", "2026-10-01T00:00:00Z")]
    world.per_student_skills = {"u-001": {"python": 1}}
    rows = fit_service.candidates_for_opening(TX, "op-edge-ai")
    assert [r["student"]["user_id"] for r in rows] == ["u-001"]


def test_candidate_payload_shape(world):
    world.applicants = [_applicant("u-001", "Applicant", "2026-10-01T00:00:00Z")]
    world.per_student_skills = {"u-001": {"python": 1}}
    row = fit_service.candidates_for_opening(TX, "op-edge-ai")[0]

    assert set(row) == {"application", "student", "fit"}
    assert set(row["student"]) == {"user_id", "name", "roll_no", "year"}
    assert "embedding" not in row["student"]
    assert row["application"]["status"] == "pending"


def test_candidates_for_missing_opening_is_none(monkeypatch):
    monkeypatch.setattr(
        fit_service.match_repo, "opening_detail", lambda tx, opening_id: None
    )
    assert fit_service.candidates_for_opening(TX, "nope") is None


def test_no_applicants_is_an_empty_list(world):
    world.applicants = []
    assert fit_service.candidates_for_opening(TX, "op-edge-ai") == []


# -- API-020: why-paths -------------------------------------------------------


def test_why_graph_has_a_requires_edge_for_every_chip():
    graph = fit_service.why_graph(TX, "op-edge-ai", "u-aarav")
    requires = [e for e in graph["edges"] if e["kind"] == "REQUIRES"]
    assert len(requires) == len(REQUIRED)


def test_why_graph_near_path_goes_through_the_similar_concept():
    """The path that exists before the uploads: computer vision is reached via
    deep learning (index 8, audit fix 6)."""
    graph = fit_service.why_graph(TX, "op-edge-ai", "u-aarav")
    similar = [e for e in graph["edges"] if e["kind"] == "SIMILAR_TO"]
    assert len(similar) == 1
    assert similar[0]["from"] == "concept:deep learning"
    assert similar[0]["to"] == "concept:computer vision"
    assert similar[0]["score"] == 0.70


def test_why_graph_node_ids_follow_the_documented_scheme():
    graph = fit_service.why_graph(TX, "op-edge-ai", "u-aarav")
    ids = {n["id"] for n in graph["nodes"]}
    assert "student:u-aarav" in ids
    assert "opening:op-edge-ai" in ids
    assert "concept:python" in ids


def test_why_graph_for_missing_opening_is_none(monkeypatch):
    monkeypatch.setattr(
        fit_service.match_repo, "fit_inputs", lambda tx, opening_id, student_id: None
    )
    assert fit_service.why_graph(TX, "nope", "u-aarav") is None


# -- API-021: skill gaps ------------------------------------------------------


def test_skill_gaps_rank_by_openings_unlocked_then_gain(world):
    world.openings = [
        {"opening_id": "op-1", "title": "A", "embedding": OPENING_VEC,
         "required": ["python", "pytorch"]},
        {"opening_id": "op-2", "title": "B", "embedding": OPENING_VEC,
         "required": ["python", "pytorch"]},
        {"opening_id": "op-3", "title": "C", "embedding": OPENING_VEC,
         "required": ["computer vision"]},
    ]
    world.idf = {"python": 1.0, "pytorch": 1.0, "computer vision": 1.0}
    world.skills = {"python": 1}

    gaps = fit_service.skill_gaps(TX, "u-aarav")
    concepts = [g["concept"] for g in gaps]

    assert "pytorch" in concepts
    assert gaps[0]["openings_unlocked"] >= gaps[-1]["openings_unlocked"]
    for gap in gaps:
        assert gap["total_gain"] > 0


def test_skill_gaps_exclude_skills_already_certified(world):
    world.openings = [
        {"opening_id": "op-1", "title": "A", "embedding": OPENING_VEC,
         "required": ["python"]},
    ]
    world.idf = {"python": 1.0}
    world.skills = {"python": 1}
    assert fit_service.skill_gaps(TX, "u-aarav") == []


def test_skill_gaps_include_a_claimed_only_skill(world):
    """Trust 0 is not proof, so certifying it is still a real gain."""
    world.openings = [
        {"opening_id": "op-1", "title": "A", "embedding": OPENING_VEC,
         "required": ["pytorch"]},
    ]
    world.idf = {"pytorch": 1.0}
    world.skills = {"pytorch": 0}
    gaps = fit_service.skill_gaps(TX, "u-aarav")
    assert [g["concept"] for g in gaps] == ["pytorch"]


def test_skill_gaps_returns_at_most_five(world):
    world.openings = [
        {"opening_id": f"op-{i}", "title": str(i), "embedding": OPENING_VEC,
         "required": [f"skill{i}"]}
        for i in range(9)
    ]
    world.idf = {f"skill{i}": 1.0 for i in range(9)}
    world.skills = {}
    assert len(fit_service.skill_gaps(TX, "u-aarav")) == 5


def test_skill_gaps_with_no_openings_is_empty(world):
    world.openings = []
    assert fit_service.skill_gaps(TX, "u-aarav") == []
