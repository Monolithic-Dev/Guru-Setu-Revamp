"""Explicit response models for the fit endpoints (SEC-01). Owner: P1.

Every field a client receives is listed here. `embedding`, `password_hash` and
`file_path` have no field on any of these models, so they cannot leak through a
widened query.

These mirror the `Fit`, `FitChip`, `OpeningSummary`, `Opening`, `Candidate`,
`WhyGraph` and `SkillGap` schemas in openapi.yaml, which P2 owns. Keep them in
step; the generated models in `schemas/generated.py` are the contract of record.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Verdict = Literal["ready", "close", "not_yet"]
ChipKind = Literal["matched", "claimed_only", "near", "missing"]
ApplicationStatus = Literal["pending", "shortlisted", "accepted", "rejected", "completed"]


class UserRef(BaseModel):
    user_id: str
    name: str


class ChipSource(BaseModel):
    """Which certificate proved a skill, so the UI can link to it (A1)."""

    evidence_id: str
    title: str


class FitChip(BaseModel):
    concept: str
    kind: ChipKind
    trust_level: int | None = None
    # Omitted rather than nulled when they do not apply, matching the
    # "private fields are omitted, not null" convention.
    via: str | None = None
    similarity: float | None = None
    source: ChipSource | None = None

    model_config = {"json_schema_extra": {"example": {
        "concept": "computer vision", "kind": "near",
        "via": "deep learning", "similarity": 0.7, "trust_level": 0,
    }}}


class FitComponents(BaseModel):
    semantic: float
    skill: float
    concept: float


class FitGain(BaseModel):
    concept: str
    score_if_certified: float


class Fit(BaseModel):
    opening_id: str
    student_id: str
    score: float = Field(ge=0, le=100)
    components: FitComponents
    weights: FitComponents
    verdict: Verdict
    verdict_text: str
    chips: list[FitChip] = Field(default_factory=list)
    gains: list[FitGain] = Field(default_factory=list)
    note: str | None = None


class MyFit(BaseModel):
    score: float
    verdict: Verdict


class OpeningSummary(BaseModel):
    id: str
    title: str
    faculty: UserRef
    required_skills: list[str] = Field(default_factory=list)
    status: Literal["open", "closed"]
    my_fit: MyFit | None = None
    my_application_status: ApplicationStatus | None = None


class Opening(BaseModel):
    id: str
    title: str
    description: str
    faculty: UserRef
    required_skills: list[str] = Field(default_factory=list)
    status: Literal["open", "closed"]
    created_at: str
    applicant_count: int | None = None


class ApplicationRef(BaseModel):
    id: str
    opening_id: str
    opening_title: str
    student_id: str
    status: ApplicationStatus
    applied_at: str
    updated_at: str
    history: list[dict] = Field(default_factory=list)


class CandidateStudent(BaseModel):
    user_id: str
    name: str
    roll_no: str
    year: int


class Candidate(BaseModel):
    application: ApplicationRef
    student: CandidateStudent
    fit: Fit


class WhyNode(BaseModel):
    id: str
    kind: Literal["student", "concept", "opening"]
    label: str


class WhyEdge(BaseModel):
    from_: str = Field(alias="from")
    to: str
    kind: Literal["HAS_SKILL", "SIMILAR_TO", "REQUIRES"]
    score: float | None = None
    trust_level: int | None = None

    model_config = {"populate_by_name": True}


class WhyGraph(BaseModel):
    nodes: list[WhyNode]
    edges: list[WhyEdge]


class SkillGap(BaseModel):
    concept: str
    openings_unlocked: int
    total_gain: float
