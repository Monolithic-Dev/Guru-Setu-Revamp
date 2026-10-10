"""Department metrics MET-01..12 (backend section 7) and the dashboard (API-033, REQ-016).

`department_metrics` is the single place the numbers are computed; the dashboard and the XLSX exports both read from
it, so they cannot disagree. It never reads session notes, action text or resolutions.
Scope: the caller's department, the current term, `assigned` context.
"""
from collections import Counter, defaultdict
from typing import Any

from app.core.clock import today
from app.core.config import get_settings
from app.core.database import run_read
from app.repos import metrics_repo
from app.schemas.auth import CurrentUser
from app.services import terms, tracking


def _pct(part: int, whole: int) -> float:
    return round(100 * part / whole, 1) if whole else 0.0


def _in_term(stamp: str | None, start: str, end: str) -> bool:
    return bool(stamp) and start <= stamp[:10] <= end


def _group_issues(issues: list[dict], start: str, end: str) -> dict[str, dict[str, int]]:
    """MET-03 / MET-04: raised and resolved in the term per category; confidential ones under "confidential"
    (REQ-036). Only categories with something to show."""
    raised, resolved = Counter(), Counter()
    for i in issues:
        group = "confidential" if i["confidential"] else i["category"]
        raised[group] += _in_term(i["raised_at"], start, end)
        resolved[group] += _in_term(i["resolved_at"], start, end)
    return {
        c: {"raised": raised[c], "resolved": resolved[c]}
        for c in sorted(set(raised) | set(resolved)) if raised[c] or resolved[c]
    }


def department_metrics(tx, dept: str) -> dict[str, Any]:
    cfg = get_settings()
    term = terms.resolve(tx)[0]
    start, end = (term["start_date"], term["end_date"]) if term else ("0000-01-01", "9999-12-31")
    day = today().isoformat()
    need = cfg.min_meetings_per_term

    mentors = metrics_repo.mentors(tx, dept)
    rows = tracking.link_rows(tx, [m["mentor_id"] for m in mentors])
    assigned = [r for r in rows if r["mentorship_type"] == "assigned"]
    by_mentor: dict[str, list[dict]] = defaultdict(list)
    for r in assigned:
        by_mentor[r["mentor_id"]].append(r)
    student_mentor = {r["student_id"]: r["mentor_id"] for r in assigned}

    issues = metrics_repo.issues(tx, dept)
    held = metrics_repo.meetings_held(tx, dept, start, end)
    mentor_facts = []
    for m in mentors:
        mine = by_mentor[m["mentor_id"]]
        compliant = sum(1 for r in mine if r["meetings_this_term"] >= need)
        about_mine = [i for i in issues if student_mentor.get(i["student_id"]) == m["mentor_id"]]
        mentor_facts.append({
            **m,
            "mentee_count": len(mine),
            "overloaded": len(mine) > cfg.mentor_load_warn,
            "meetings_held": held.get(m["mentor_id"], 0),
            "mentees_compliant": compliant,
            "compliance_pct": _pct(compliant, len(mine)),
            "issues_raised": sum(1 for i in about_mine if _in_term(i["raised_at"], start, end)),
            "issues_resolved": sum(1 for i in about_mine if _in_term(i["resolved_at"], start, end)),
            "overdue_actions": sum(r["overdue_actions"] for r in mine),
            "issues_by_category": _group_issues(about_mine, start, end),
        })

    # MET-03 / MET-04 for the whole department.
    issues_by_category = [{"category": c, **n} for c, n in _group_issues(issues, start, end).items()]

    # MET-08: certified evidence with issue_date in the academic year (Jul 1 - Jun 30), by type and level.
    year_start, year_end = terms.academic_year(day)
    achievements = [
        e for e in metrics_repo.certified_evidence(tx, dept) if year_start <= (e["issue_date"] or "") <= year_end
    ]
    by_type = Counter(e["type"] for e in achievements)
    by_type_level = Counter((e["type"], e["level"]) for e in achievements)

    # MET-09: a student with at least one reason on any of their active links.
    attention: dict[str, dict] = {}
    for r in rows:
        if r["needs_attention"]:
            entry = attention.setdefault(
                r["student_id"], {"student_id": r["student_id"], "name": r["name"], "roll_no": r["roll_no"],
                                  "mentor_name": r["mentor_name"], "reasons": []},
            )
            entry["reasons"] += [x for x in r["attention_reasons"] if x not in entry["reasons"]]
    attention_list = sorted(attention.values(), key=lambda a: (-len(a["reasons"]), a["name"]))

    allotted = len(assigned)
    active_mentors = sum(1 for m in mentor_facts if m["mentee_count"] > 0)
    present, confirmed = metrics_repo.attendance_confirmation(tx, dept, start, end)
    students_total = metrics_repo.count_students(tx, dept)
    return {
        "term": {"id": term["id"], "name": term["name"]} if term else {"id": "none", "name": "No term configured"},
        "term_start": start,
        "term_end": end,
        "students_total": students_total,
        "students_allotted": allotted,
        "unallotted": students_total - allotted,
        "ratio": "1:" + str(round(allotted / active_mentors)) if active_mentors else "1:0",  # MET-02
        "compliance_pct": _pct(sum(m["mentees_compliant"] for m in mentor_facts), allotted),  # MET-01
        "overdue_actions": metrics_repo.overdue_actions(tx, dept, day),  # MET-06
        "pending_reviews": metrics_repo.pending_reviews(tx, dept),  # MET-10
        "needs_attention_count": len(attention_list),
        "needs_attention_list": attention_list,
        "mentors": mentor_facts,
        "assigned_rows": assigned,
        "issues": issues,
        "student_mentor_name": {r["student_id"]: r["mentor_name"] for r in assigned},
        "issues_by_category": issues_by_category,
        "achievements": achievements,
        "achievements_by_type": [{"type": t, "count": n} for t, n in sorted(by_type.items())],
        "achievements_by_type_level": sorted(
            ({"type": t, "level": lv, "count": n} for (t, lv), n in by_type_level.items()),
            key=lambda x: (x["type"], str(x["level"])),
        ),
        "confirmed_share": _pct(confirmed, present),  # MET-12
    }


_MENTOR_FIELDS = (
    "mentor_id", "name", "mentee_count", "overloaded", "meetings_held", "mentees_compliant", "compliance_pct",
    "issues_raised", "issues_resolved", "overdue_actions",
)


def dashboard(user: CurrentUser) -> dict[str, Any]:
    """API-033. The HOD sees names, escalated issues and the flagged list; IQAC sees aggregates only (no student
    names anywhere, and the escalated and flagged lists are omitted rather than empty)."""

    def read(tx):
        facts = department_metrics(tx, user.dept_code)
        out = {k: facts[k] for k in (
            "term", "students_total", "students_allotted", "unallotted", "ratio", "compliance_pct",
            "overdue_actions", "pending_reviews", "needs_attention_count", "issues_by_category",
            "achievements_by_type",
        )}
        out["mentors"] = [{k: m[k] for k in _MENTOR_FIELDS} for m in facts["mentors"]]
        if user.role == "hod":
            out["escalated_issues"] = metrics_repo.escalated_issues(tx, user.dept_code)
            out["needs_attention_list"] = [
                {k: a[k] for k in ("student_id", "name", "mentor_name", "reasons")}
                for a in facts["needs_attention_list"]
            ]
        return out

    return run_read(read)
