"""Draft accreditation exports (API-035, API-036; backend section 7, REQ-017).

Rows come from `metrics.department_metrics` and the metric queries only. Session notes, issue text, action text and
resolutions are never read, so they cannot reach a cell (SEC-15). Every string cell passes through `safe` (SEC-18).
"""
import re
from io import BytesIO
from typing import Any

from openpyxl import Workbook

from app.core.clock import utc_now_iso
from app.core.database import run_read
from app.repos import metrics_repo
from app.schemas.auth import CurrentUser
from app.services import metrics

DRAFT_NOTICE = "DRAFT – verify against the official NAAC manual before submission"


def safe(value: Any) -> Any:
    """Neutralise spreadsheet formulas: a string starting with = + - @ (or tab / CR) gets a leading apostrophe."""
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value


def _sheet(wb: Workbook, title: str, header: list[str], rows: list[list[Any]]) -> None:
    ws = wb.create_sheet()
    ws.title = title
    ws.append([safe(h) for h in header])
    for row in rows:
        ws.append([safe(v) for v in row])


def _readme(wb: Workbook, user: CurrentUser, facts: dict[str, Any], criteria: list[dict[str, Any]]) -> None:
    ws = wb.active
    ws.title = "README"
    ws["A1"] = DRAFT_NOTICE  # a constant: never passed through user data
    ws.append(["generated_at", utc_now_iso()])
    ws.append(["term", safe(facts["term"]["name"])])
    ws.append(["generated_by_role", user.role])
    ws.append([])
    ws.append(["Draft criterion code", "Title", "Verified against the official manual"])
    for c in criteria:
        ws.append([safe(c["code"]), safe(c["title"]), "yes" if c["verified"] else "no"])


def _build(user: CurrentUser):
    def read(tx):
        return (
            metrics.department_metrics(tx, user.dept_code),
            metrics_repo.criteria(tx),
            metrics_repo.mentors(tx, user.dept_code),
            metrics_repo.allotment(tx, user.dept_code),
        )

    return run_read(read)


def _file_name(kind: str, facts: dict[str, Any]) -> str:
    term = re.sub(r"[^A-Za-z0-9_-]", "", facts["term"]["id"])
    return f"gurusetu-{kind}-{term}-DRAFT.xlsx"


def _bytes(wb: Workbook) -> bytes:
    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def mentoring_pack(user: CurrentUser) -> tuple[str, bytes]:
    facts, criteria, mentors, allotment = _build(user)
    wb = Workbook()
    _readme(wb, user, facts, criteria)
    by_id = {m["mentor_id"]: m for m in facts["mentors"]}
    _sheet(wb, "Mentors", ["name", "designation", "employee_id", "mentee_count"],
           [[m["name"], m["designation"], m["employee_id"], by_id[m["mentor_id"]]["mentee_count"]] for m in mentors])
    _sheet(wb, "Allotment", ["mentor", "roll_no", "student", "since"],
           [[a["mentor"], a["roll_no"], a["student"], a["since"]] for a in allotment])

    summary: list[list[Any]] = [
        ["MET-01", "compliance_pct", facts["compliance_pct"]],
        ["MET-02", "ratio", facts["ratio"]],
        ["MET-06", "overdue_actions", facts["overdue_actions"]],
        ["MET-12", "confirmed_share_pct", facts["confirmed_share"]],
    ]
    for c in facts["issues_by_category"]:
        summary.append(["MET-03", f"issues_raised:{c['category']}", c["raised"]])
        summary.append(["MET-04", f"issues_resolved:{c['category']}", c["resolved"]])
    _sheet(wb, "Summary", ["metric", "name", "value"], summary)

    categories = [c["category"] for c in facts["issues_by_category"]]
    header = ["mentor", "meetings_held", "mentees", "mentees_compliant", "compliance_pct"]
    header += [f"raised:{c}" for c in categories] + [f"resolved:{c}" for c in categories]
    rows = []
    for m in facts["mentors"]:
        per = m["issues_by_category"]
        rows.append(
            [m["name"], m["meetings_held"], m["mentee_count"], m["mentees_compliant"], m["compliance_pct"]]
            + [per.get(c, {}).get("raised", 0) for c in categories]
            + [per.get(c, {}).get("resolved", 0) for c in categories]
        )
    _sheet(wb, "Mentor-wise", header, rows)
    return _file_name("mentoring", facts), _bytes(wb)


def achievements_pack(user: CurrentUser) -> tuple[str, bytes]:
    facts, criteria, _, _ = _build(user)
    wb = Workbook()
    _readme(wb, user, facts, criteria)

    def criterion(kind: str | None) -> str:
        return next((c["code"] for c in criteria if kind in c["evidence_types"]), "")

    _sheet(
        wb, "Achievements",
        ["roll_no", "name", "title", "issuer", "issue_date", "level", "type", "certificate_id", "status",
         "reviewed_by", "draft_criterion_code"],
        [[e["roll_no"], e["student_name"], e["title"], e["issuer"], e["issue_date"], e["level"], e["type"],
          e["certificate_id"], e["status"], e["reviewed_by"], criterion(e["type"])] for e in facts["achievements"]],
    )
    _sheet(wb, "By type", ["type", "level", "count"],
           [[x["type"], x["level"], x["count"]] for x in facts["achievements_by_type_level"]])
    return _file_name("achievements", facts), _bytes(wb)
