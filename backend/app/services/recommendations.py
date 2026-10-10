"""Recommended openings for a student (API-050, plan section 4.4) and the eligibility read (API-051).

Two separate questions (plan section 4.1): ELIGIBILITY (rules, services/eligibility.py) and FIT (P1's explained score,
untouched). This module only combines them:

    Best matches    eligible, fit >= FIT_READY_MIN
    Worth a look    eligible, fit >= FIT_CLOSE_MIN
    Stretch         eligible, below that
    Not eligible    the student cannot apply (closed, past its deadline, full, or a strict rule failed); never hidden,
                    the failing rule is shown so the student knows what to change. An ADVISORY opening whose
                    suitability rule fails stays in its score group and carries a warning instead.

Cold start (fewer than two skills): ordered by the meaning part of the score, labelled "Based on your interests".
Reasons are one-line templates built from the fit chips: no model writes any text here.
"""
from typing import Any

from app.core.clock import today
from app.core.config import get_settings
from app.core.database import run_read
from app.core.errors import ApiError
from app.ml import fit as fit_module
from app.repos import openings_repo, profile_repo
from app.schemas.auth import CurrentUser
from app.services import eligibility, profile
from app.services.students import normalise_skill

MIN_SKILLS_FOR_FIT = 2
MAX_REASONS = 3
GROUP_LABELS = {
    "best": "Best matches",
    "worth": "Worth a look",
    "stretch": "Stretch",
    "ineligible": "Not eligible yet",
}


def _reasons(chips: list[dict[str, Any]], opening: dict[str, Any], student_terms: set[str]) -> list[str]:
    """Up to three short, factual lines: proven skills first, then what to certify, then near skills and the gap."""
    by_kind: dict[str, list[dict[str, Any]]] = {"matched": [], "claimed_only": [], "near": [], "missing": []}
    for chip in chips:
        by_kind.setdefault(chip["kind"], []).append(chip)
    lines: list[str] = []
    if by_kind["matched"]:
        lines.append("You have verified: " + ", ".join(c["concept"] for c in by_kind["matched"]))
    if by_kind["claimed_only"]:
        lines.append("Certify to count fully: " + ", ".join(c["concept"] for c in by_kind["claimed_only"]))
    for chip in by_kind["near"][:1]:
        lines.append(f"Your {chip.get('via', 'related skill')} is close to {chip['concept']}")
    if by_kind["missing"]:
        lines.append("Missing: " + ", ".join(c["concept"] for c in by_kind["missing"]))
    shared = sorted(student_terms & set(opening["faculty_research"]))
    if shared:
        said = f"{opening['faculty_name']} researches {', '.join(shared)}, which matches your profile"
        lines.insert(1 if lines else 0, said)
    return lines[:MAX_REASONS]


def _item(opening: dict[str, Any], fit: dict[str, Any], elig: dict[str, Any], status: str | None, reasons: list[str]):
    return {
        "id": opening["id"], "title": opening["title"],
        "faculty": {"user_id": opening["faculty_id"], "name": opening["faculty_name"]},
        "required_skills": sorted(opening["required_skills"]), "preferred_skills": sorted(opening["preferred_skills"]),
        "status": opening["status"],
        "my_fit": {"score": fit["score"], "verdict": fit["verdict"]},
        "my_application_status": status,
        "eligibility": elig, "reasons": reasons,
        "positions": opening["positions"], "positions_left": max(0, opening["positions"] - opening["accepted_count"]),
        "deadline": opening["deadline"], "eligible_years": opening["eligible_years"], "min_cgpa": opening["min_cgpa"],
        "mode": opening["mode"], "duration_weeks": opening["duration_weeks"],
        "hours_per_week": opening["hours_per_week"],
    }


def recommendations(user: CurrentUser) -> dict[str, Any]:
    cfg = get_settings()
    now = today()

    def read(tx):
        ctx = eligibility.student_ctx(tx, user.user_id)
        if ctx is None:
            raise ApiError("NOT_FOUND", 404, "The student was not found.")
        rows = openings_repo.rows(tx)
        summaries = fit_module.fit_summary_for_openings(tx, user.user_id)
        statuses = {s["id"]: s.get("my_application_status") for s in summaries}
        skills = profile_repo.skill_rows(tx, user.user_id)
        core = profile_repo.student_core(tx, user.user_id)
        student_terms = {s["concept"] for s in skills} | {normalise_skill(i) for i in core["interests"]}
        cold = len(skills) < MIN_SKILLS_FOR_FIT

        scored = []
        for opening in rows:
            fit = fit_module.fit_for(tx, opening["id"], user.user_id, with_gains=False)
            if fit is None:
                continue
            elig = eligibility.evaluate(opening, ctx, now)
            reasons = _reasons(fit["chips"], opening, student_terms)
            matched = sum(1 for c in fit["chips"] if c["kind"] == "matched")
            scored.append((opening, fit, elig, reasons, matched))

        def order(entry):
            opening, fit, _elig, _reasons_, matched = entry
            primary = fit["components"].get("semantic", 0.0) if cold else fit["score"]
            left = opening["positions"] - opening["accepted_count"]
            return (-primary, -matched, opening["deadline"] or "9999-12-31", -left, opening["title"])

        groups: dict[str, list] = {key: [] for key in GROUP_LABELS}
        for entry in sorted(scored, key=order):
            opening, fit, elig, reasons, _matched = entry
            unavailable, unsuitable = eligibility.blocking(elig)
            if unavailable or (unsuitable and elig["mode"] == "strict"):
                key = "ineligible"  # the student cannot apply; an advisory warning keeps its score group
            elif cold:
                key = "worth"
            elif fit["score"] >= cfg.fit_ready_min:
                key = "best"
            elif fit["score"] >= cfg.fit_close_min:
                key = "worth"
            else:
                key = "stretch"
            groups[key].append(_item(opening, fit, elig, statuses.get(opening["id"]), reasons))

        labels = dict(GROUP_LABELS)
        if cold:
            labels["worth"] = "Based on your interests"
        completeness = profile.completeness(
            core, skills, profile_repo.certified_count(tx, user.user_id), profile_repo.projects(tx, user.user_id),
            profile_repo.current_resume(tx, user.user_id),
        )
        return {
            "cold_start": cold,
            "completeness_percent": completeness["percent"],
            "groups": [{"key": k, "label": labels[k], "items": v} for k, v in groups.items() if v],
        }

    return run_read(read)


def eligibility_for(user: CurrentUser, opening_id: str) -> dict[str, Any]:
    def read(tx):
        opening = openings_repo.get(tx, opening_id)
        ctx = eligibility.student_ctx(tx, user.user_id)
        if opening is None or ctx is None:
            raise ApiError("NOT_FOUND", 404, "The opening was not found.")
        return eligibility.evaluate(opening, ctx, today())

    return run_read(read)
