"""Eligibility: "can this student apply?" (plan section 4.2). Rules the faculty member wrote down, evaluated openly,
each with a plain-words detail. This is deliberately separate from the fit score: CGPA, year and department decide
eligibility ONLY and never enter the score (which would make it unexplainable and unfair).

Two kinds of rule:
  * availability (open, deadline, capacity, guide_capacity): always block an application, in any mode;
  * suitability (year, department, min_cgpa): block only when the opening is `strict`; otherwise they warn.
An `unknown` CGPA (nothing recorded and nothing self-reported) never fails the rule.
"""
from dataclasses import dataclass
from datetime import date
from typing import Any

from app.repos import profile_repo
from app.services import profile, terms

AVAILABILITY_RULES = ("open", "deadline", "capacity", "guide_capacity")
SUITABILITY_RULES = ("year", "department", "min_cgpa")


@dataclass
class StudentCtx:
    user_id: str
    dept_code: str
    year: int
    cgpa: float | None
    cgpa_source: str  # record | self_reported | unknown


def student_ctx(tx, student_id: str) -> StudentCtx | None:
    core = profile_repo.student_core(tx, student_id)
    if core is None:
        return None
    term = terms.resolve(tx)[0]
    cgpa = profile.cgpa_view(
        profile_repo.academic_records(tx, student_id), core["self_reported_cgpa"], term["id"] if term else None
    )
    return StudentCtx(student_id, core["dept_code"], core["year"], cgpa["effective"], cgpa["source"])


def _check(rule: str, status: str, detail: str) -> dict[str, str]:
    return {"rule": rule, "status": status, "detail": detail}


def evaluate(opening: dict[str, Any], ctx: StudentCtx, today: date) -> dict[str, Any]:
    """`opening` is a row from `openings_repo.rows` or `.get`. Returns the `Eligibility` response shape."""
    checks: list[dict[str, str]] = []

    checks.append(
        _check("open", "ok", "The opening is open.") if opening["status"] == "open"
        else _check("open", "failed", "The opening is closed.")
    )

    deadline = opening["deadline"]
    if deadline and today.isoformat() > str(deadline):
        checks.append(_check("deadline", "failed", f"The deadline was {deadline}."))
    else:
        checks.append(_check("deadline", "ok", f"Apply by {deadline}." if deadline else "There is no deadline."))

    left = max(0, opening["positions"] - opening["accepted_count"])
    if left == 0:
        checks.append(_check("capacity", "failed", "All positions are filled."))
    else:
        noun = "position" if left == 1 else "positions"
        checks.append(_check("capacity", "ok", f"{left} of {opening['positions']} {noun} left."))

    cap = opening["max_guided_students"]
    if not opening["accepting_guides"]:
        name = opening["faculty_name"]
        checks.append(_check("guide_capacity", "failed", f"{name} is not taking new guided students."))
    elif cap is not None and opening["guided_students"] >= cap:
        detail = f"{opening['faculty_name']} is at capacity ({opening['guided_students']} of {cap})."
        checks.append(_check("guide_capacity", "failed", detail))
    else:
        checks.append(_check("guide_capacity", "ok", f"{opening['faculty_name']} is taking guided students."))

    years = opening["eligible_years"]
    if not years:
        checks.append(_check("year", "ok", "Open to every year."))
    else:
        detail = f"Open to year {', '.join(map(str, sorted(years)))}; you are in year {ctx.year}."
        checks.append(_check("year", "ok" if ctx.year in years else "failed", detail))

    allowed = opening["allowed_departments"] or [opening["faculty_dept"]]
    if ctx.dept_code in allowed:
        checks.append(_check("department", "ok", f"Open to {', '.join(allowed)}; you are in {ctx.dept_code}."))
    else:
        checks.append(_check("department", "failed", f"Open to {', '.join(allowed)}; you are in {ctx.dept_code}."))

    minimum = opening["min_cgpa"]
    if minimum is None:
        checks.append(_check("min_cgpa", "ok", "No minimum CGPA."))
    elif ctx.cgpa is None:
        checks.append(_check("min_cgpa", "unknown", f"Needs CGPA {minimum:g} or more; add yours to your profile."))
    else:
        label = "from your record" if ctx.cgpa_source == "record" else "self-reported"
        status = "ok" if ctx.cgpa >= minimum else "failed"
        word = "meets" if status == "ok" else "is below"
        detail = f"Needs CGPA {minimum:g} or more; yours is {ctx.cgpa:g} ({label}), which {word} it."
        checks.append(_check("min_cgpa", status, detail))

    return {
        "eligible": not any(c["status"] == "failed" for c in checks),
        "mode": opening["eligibility_mode"],
        "checks": checks,
    }


def blocking(eligibility: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """(availability failures, suitability failures that count in strict mode)."""
    failed = [c for c in eligibility["checks"] if c["status"] == "failed"]
    return (
        [c for c in failed if c["rule"] in AVAILABILITY_RULES],
        [c for c in failed if c["rule"] in SUITABILITY_RULES],
    )
