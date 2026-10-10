"""Click-to-source (API-034, REQ-019): the exact rows behind each dashboard number, taken from the same
`department_metrics` facts, so `total` always equals the dashboard figure. Rows never contain text fields.
IQAC gets a pseudonym per student (`Student 01`...) and no ids or roll numbers."""
import base64
from datetime import date
from typing import Any

from app.core.clock import today
from app.core.database import run_read
from app.core.errors import ApiError
from app.repos import metrics_repo
from app.schemas.auth import CurrentUser
from app.services import metrics

METRICS = (
    "compliance", "issues_raised", "issues_resolved", "overdue_actions", "achievements", "needs_attention",
    "pending_reviews",
)
_IDENTITY = ("student_id", "student_name", "roll_no")


def _who(user: CurrentUser, pseudonyms: dict[str, str], row: dict[str, Any]) -> dict[str, Any]:
    if user.role == "hod":
        return {"student": row["student_name"], "roll_no": row["roll_no"], "student_id": row["student_id"]}
    return {"student": pseudonyms[row["student_id"]]}


def _base(tx, user: CurrentUser, metric: str) -> list[dict[str, Any]]:
    facts = metrics.department_metrics(tx, user.dept_code)
    start, end = facts["term_start"], facts["term_end"]
    mentor_of = facts["student_mentor_name"]

    if metric == "compliance":  # total = allotted students; compliance_pct = compliant / total
        return [
            {"student_id": r["student_id"], "student_name": r["name"], "roll_no": r["roll_no"],
             "mentor": r["mentor_name"], "meetings_this_term": r["meetings_this_term"],
             "meetings_required": r["meetings_required"],
             "compliant": r["meetings_this_term"] >= r["meetings_required"]}
            for r in facts["assigned_rows"]
        ]
    if metric in ("issues_raised", "issues_resolved"):
        field = "raised_at" if metric == "issues_raised" else "resolved_at"
        return [
            {"student_id": i["student_id"], "student_name": i["student_name"], "roll_no": i["roll_no"],
             "date": i[field][:10], "mentor": mentor_of.get(i["student_id"]), "status": i["status"],
             "category": "confidential" if i["confidential"] else i["category"]}
            for i in sorted(facts["issues"], key=lambda i: (i[field] or "", i["id"]))
            if i[field] and start <= i[field][:10] <= end
        ]
    if metric == "overdue_actions":
        now = today()
        return [
            {"student_id": r["student_id"], "student_name": r["student_name"], "roll_no": r["roll_no"],
             "due_date": r["due_date"], "owner": r["owner"], "mentor": r["mentor_name"],
             "days_overdue": (now - date.fromisoformat(r["due_date"])).days}
            for r in metrics_repo.overdue_action_rows(tx, user.dept_code, now.isoformat())
        ]
    if metric == "achievements":
        return [
            {"student_id": e["student_id"], "student_name": e["student_name"], "roll_no": e["roll_no"],
             "title": e["title"], "issuer": e["issuer"], "issue_date": e["issue_date"], "level": e["level"],
             "type": e["type"]}
            for e in facts["achievements"]
        ]
    if metric == "needs_attention":
        return [
            {"student_id": a["student_id"], "student_name": a["name"], "roll_no": a["roll_no"],
             "mentor": a["mentor_name"], "reasons": a["reasons"]}
            for a in facts["needs_attention_list"]
        ]
    return [  # pending_reviews
        {"student_id": r["student_id"], "student_name": r["student_name"], "roll_no": r["roll_no"],
         "title": r["title"], "issuer": r["issuer"], "reasons": r["reasons"], "submitted": (r["created_at"] or "")[:10]}
        for r in metrics_repo.pending_review_rows(tx, user.dept_code)
    ]


def _rows(tx, user: CurrentUser, metric: str) -> list[dict[str, Any]]:
    base = _base(tx, user, metric)
    # Pseudonyms follow the sorted student ids of the WHOLE result, so they stay the same on every page.
    ids = sorted({r["student_id"] for r in base})
    pseudonyms = {sid: f"Student {n:02d}" for n, sid in enumerate(ids, start=1)}
    return [
        {**_who(user, pseudonyms, r), **{k: v for k, v in r.items() if k not in _IDENTITY}} for r in base
    ]


def _offset(cursor: str | None) -> int:
    if not cursor:
        return 0
    try:
        return max(0, int(base64.urlsafe_b64decode(cursor.encode("ascii")).decode()))
    except (ValueError, UnicodeError) as exc:
        raise ApiError(
            "VALIDATION_FAILED", 422, "The cursor is not valid.",
            errors=[{"field": "cursor", "message": "Invalid cursor"}],
        ) from exc


def records(user: CurrentUser, metric: str, limit: int, cursor: str | None) -> dict[str, Any]:
    if metric not in METRICS:
        raise ApiError("NOT_FOUND", 404, "Unknown metric.")
    start = _offset(cursor)
    rows = run_read(lambda tx: _rows(tx, user, metric))
    more = start + limit < len(rows)
    next_cursor = base64.urlsafe_b64encode(str(start + limit).encode()).decode("ascii") if more else None
    return {"items": rows[start:start + limit], "next_cursor": next_cursor, "total": len(rows)}
