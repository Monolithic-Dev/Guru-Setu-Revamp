"""Assembly for the fit endpoints: read inputs, call the scorer, shape output.

Kept separate from `api/v1/match.py` so the logic can be unit-tested against a
fake transaction without FastAPI, and so the router stays thin (backend 5).
Nothing here touches the network or a model: the embeddings were computed when
the profile or opening last changed.
"""

from __future__ import annotations

from typing import Any

from app.ml import scorer
from app.ml.embedding import cosine
from app.ml.scorer import Fit, FitConfig
from app.ml.settings import get_settings
from app.repos import match_repo


def _cfg() -> FitConfig:
    return FitConfig.from_settings(get_settings())


def fit_for(
    tx,
    opening_id: str,
    student_id: str,
    with_gains: bool = True,
) -> dict[str, Any] | None:
    """One Fit Check. Returns None when either side does not exist, so the
    caller can answer 404 without leaking which one was missing (security 3)."""
    inputs = match_repo.fit_inputs(tx, opening_id, student_id)
    if inputs is None:
        return None

    required = list(inputs.get("required") or [])
    skills, sources = match_repo.student_skills(tx, student_id)
    idf_values = match_repo.idf_table(tx)
    similar = match_repo.similar_pairs(tx, sorted(set(required) | set(skills)))
    semantic = cosine(
        list(inputs.get("student_embedding") or []),
        list(inputs.get("opening_embedding") or []),
    )

    cfg = _cfg()
    result = scorer.score(required, idf_values, skills, similar, semantic, cfg, sources)
    if with_gains:
        result = scorer.with_gains(
            result, required, idf_values, skills, similar, semantic, cfg, sources
        )

    payload = result.as_dict()
    payload["opening_id"] = opening_id
    payload["student_id"] = student_id
    return payload


def fit_summary_for_openings(
    tx, student_id: str, include_closed: bool = False, limit: int = 50
) -> list[dict[str, Any]]:
    """API-012. One idf table and one skill read for the whole list, rather than
    per opening - the student's skills do not change between rows."""
    rows = match_repo.openings(tx, include_closed=include_closed, limit=limit)
    if not rows:
        return []

    skills, sources = match_repo.student_skills(tx, student_id)
    idf_values = match_repo.idf_table(tx)
    statuses = match_repo.my_application_statuses(tx, student_id)
    student_vec = match_repo.student_embedding(tx, student_id) or []

    all_required = {c for row in rows for c in (row.get("required_skills") or [])}
    similar = match_repo.similar_pairs(tx, sorted(all_required | set(skills)))
    cfg = _cfg()

    out: list[dict[str, Any]] = []
    for row in rows:
        required = list(row.get("required_skills") or [])
        semantic = cosine(student_vec, list(row.get("embedding") or []))
        result = scorer.score(
            required, idf_values, skills, similar, semantic, cfg, sources
        )
        out.append(
            {
                "id": row["id"],
                "title": row["title"],
                "status": row["status"],
                "faculty": {"user_id": row["faculty_id"], "name": row["faculty_name"]},
                "required_skills": required,
                "my_fit": {"score": result.score, "verdict": result.verdict},
                "my_application_status": statuses.get(row["id"]),
            }
        )
    return out


def candidates_for_opening(tx, opening_id: str) -> list[dict[str, Any]] | None:
    """API-016. Applicants only, ranked by fit (REQ-005, NG-11).

    Never a search over students who did not apply: TEST-39 asserts that, and
    the privacy matrix forbids it.
    """
    detail = match_repo.opening_detail(tx, opening_id)
    if detail is None:
        return None

    required = list(detail.get("required_skills") or [])
    opening_vec = list(detail.get("embedding") or [])
    idf_values = match_repo.idf_table(tx)
    cfg = _cfg()

    rows = match_repo.applicants(tx, opening_id)
    skill_names: set[str] = set(required)
    per_student = {}
    for row in rows:
        skills, sources = match_repo.student_skills(tx, row["student_id"])
        per_student[row["student_id"]] = (skills, sources)
        skill_names |= set(skills)
    similar = match_repo.similar_pairs(tx, sorted(skill_names))

    entries = []
    for row in rows:
        skills, sources = per_student[row["student_id"]]
        semantic = cosine(list(row.get("student_embedding") or []), opening_vec)
        result = scorer.score(
            required, idf_values, skills, similar, semantic, cfg, sources
        )
        result = scorer.with_gains(
            result, required, idf_values, skills, similar, semantic, cfg, sources
        )
        entries.append(
            {
                "fit": result,
                "applied_at": row.get("applied_at"),
                "application": {
                    "id": row["application_id"],
                    "opening_id": opening_id,
                    "opening_title": detail.get("title"),
                    "student_id": row["student_id"],
                    "status": row["status"],
                    "applied_at": row.get("applied_at"),
                    "updated_at": row.get("updated_at"),
                    "history": [],
                },
                "student": {
                    "user_id": row["student_id"],
                    "name": row["name"],
                    "roll_no": row["roll_no"],
                    "year": row["year"],
                },
            }
        )

    ranked = scorer.rank_candidates(entries)
    out = []
    for entry in ranked:
        payload = entry["fit"].as_dict()
        payload["opening_id"] = opening_id
        payload["student_id"] = entry["student"]["user_id"]
        out.append(
            {
                "application": entry["application"],
                "student": entry["student"],
                "fit": payload,
            }
        )
    return out


def why_graph(tx, opening_id: str, student_id: str) -> dict[str, Any] | None:
    """API-020. The chips, re-expressed as the graph path that produced them.

    matched / claimed_only -> student -HAS_SKILL-> concept <-REQUIRES- opening
    near                   -> student -HAS_SKILL-> held -SIMILAR_TO-> concept
                              <-REQUIRES- opening
    """
    payload = fit_for(tx, opening_id, student_id, with_gains=False)
    if payload is None:
        return None

    student_node = f"student:{student_id}"
    opening_node = f"opening:{opening_id}"
    nodes: dict[str, dict[str, Any]] = {
        student_node: {"id": student_node, "kind": "student", "label": "You"},
        opening_node: {
            "id": opening_node,
            "kind": "opening",
            "label": payload.get("opening_title") or opening_id,
        },
    }
    edges: list[dict[str, Any]] = []

    for chip in payload["chips"]:
        concept = chip["concept"]
        concept_node = f"concept:{concept}"
        nodes.setdefault(
            concept_node, {"id": concept_node, "kind": "concept", "label": concept}
        )
        edges.append({"from": opening_node, "to": concept_node, "kind": "REQUIRES"})

        if chip["kind"] in ("matched", "claimed_only"):
            edges.append(
                {
                    "from": student_node,
                    "to": concept_node,
                    "kind": "HAS_SKILL",
                    "trust_level": chip.get("trust_level"),
                }
            )
        elif chip["kind"] == "near":
            via = chip.get("via")
            via_node = f"concept:{via}"
            nodes.setdefault(
                via_node, {"id": via_node, "kind": "concept", "label": via}
            )
            edges.append(
                {
                    "from": student_node,
                    "to": via_node,
                    "kind": "HAS_SKILL",
                    "trust_level": chip.get("trust_level"),
                }
            )
            edges.append(
                {
                    "from": via_node,
                    "to": concept_node,
                    "kind": "SIMILAR_TO",
                    "score": chip.get("similarity"),
                }
            )

    return {"nodes": list(nodes.values()), "edges": edges}


def skill_gaps(tx, student_id: str, top_n: int = 5) -> list[dict[str, Any]]:
    """API-021. The skills that would unlock the most openings.

    For each concept the student lacks but some open opening requires, count how
    many openings would cross fit_ready_min if it were certified, and sum the
    gain. Ranked by openings unlocked, then by total gain (REQ-021).
    """
    openings = match_repo.required_by_open_openings(tx)
    if not openings:
        return []

    skills, sources = match_repo.student_skills(tx, student_id)
    idf_values = match_repo.idf_table(tx)
    student_vec = match_repo.student_embedding(tx, student_id) or []
    cfg = _cfg()

    candidate_concepts = {
        c
        for row in openings
        for c in (row.get("required") or [])
        if c not in skills or int(skills.get(c, 0)) < 1
    }
    all_names = {c for row in openings for c in (row.get("required") or [])}
    similar = match_repo.similar_pairs(tx, sorted(all_names | set(skills)))

    baseline: dict[str, Fit] = {}
    for row in openings:
        semantic = cosine(student_vec, list(row.get("embedding") or []))
        baseline[row["opening_id"]] = scorer.score(
            list(row.get("required") or []), idf_values, skills, similar,
            semantic, cfg, sources,
        )

    results = []
    for concept in sorted(candidate_concepts):
        hypothetical = dict(skills)
        hypothetical[concept] = 1
        unlocked = 0
        total_gain = 0.0
        for row in openings:
            required = list(row.get("required") or [])
            if concept not in required:
                continue
            semantic = cosine(student_vec, list(row.get("embedding") or []))
            improved = scorer.score(
                required, idf_values, hypothetical, similar, semantic, cfg, sources
            )
            before = baseline[row["opening_id"]]
            total_gain += improved.score - before.score
            if before.score < cfg.fit_ready_min <= improved.score:
                unlocked += 1
        if total_gain > 0:
            results.append(
                {
                    "concept": concept,
                    "openings_unlocked": unlocked,
                    "total_gain": round(total_gain, 1),
                }
            )

    results.sort(key=lambda r: (-r["openings_unlocked"], -r["total_gain"], r["concept"]))
    return results[:top_n]
