"""Needs-attention rules and mentor home (backend 6.4, REQ-012). One read gathers the facts for a set of mentors;
the rules run here in Python with the configured thresholds, so the mentor home (API-024) and the HOD views
(API-033, exports) can never disagree."""
from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from app.core.clock import today
from app.core.config import get_settings
from app.core.database import run_read
from app.repos import tracking_repo
from app.schemas.auth import CurrentUser
from app.services import terms


def _midpoint(term: dict[str, Any]) -> str:
    start, end = date.fromisoformat(term["start_date"]), date.fromisoformat(term["end_date"])
    return (start + (end - start) / 2).isoformat()


def link_rows(tx, mentor_ids: list[str]) -> list[dict[str, Any]]:
    """One row per active MENTORS link of the given mentors: MenteeRow fields plus `mentor_id`, `mentor_name`."""
    links = tracking_repo.active_links(tx, mentor_ids)
    if not links:
        return []
    cfg = get_settings()
    now = today()
    day = now.isoformat()
    no_session_cut = (now - timedelta(days=cfg.attention_no_session_days)).isoformat()
    stale_cut = (now - timedelta(days=cfg.issue_stale_days)).isoformat()
    confirm_cut = (now - timedelta(days=cfg.session_confirm_days)).isoformat()
    term = terms.resolve(tx)[0]

    student_ids = sorted({link["student_id"] for link in links})
    sessions: dict[tuple, list] = defaultdict(list)
    for row in tracking_repo.sessions_of_mentors(tx, mentor_ids, student_ids):
        sessions[(row["mentor_id"], row["student_id"])].append(row)
    items: dict[tuple, list] = defaultdict(list)
    for row in tracking_repo.action_items_of_mentors(tx, mentor_ids, student_ids):
        items[(row["mentor_id"], row["student_id"])].append(row)
    issues: dict[str, list] = defaultdict(list)
    for row in tracking_repo.issues_about(tx, student_ids):
        issues[row["student_id"]].append(row)

    def of_link(rows: list[dict], link: dict) -> list[dict]:
        """Only the rows that belong to this link: same context, and the same opening for a guide link."""
        return [
            r for r in rows
            if r["context"] == link["type"] and (link["type"] == "assigned" or r["opening_id"] == link["opening_id"])
        ]

    out = []
    for link in links:
        key = (link["mentor_id"], link["student_id"])
        assigned = link["type"] == "assigned"
        present = [s for s in of_link(sessions[key], link) if s["present"]]
        in_term = [s for s in present if term and term["start_date"] <= s["date"] <= term["end_date"]]
        mine = of_link(items[key], link)
        overdue = [a for a in mine if a["status"] == "open" and str(a["due_date"]) < day]
        # An issue is visible to the mentor unless it is confidential and someone else raised it (security section 4).
        visible = [
            i for i in issues[link["student_id"]]
            if not i["confidential"] or i["raised_by"] == link["mentor_id"]
        ]
        unresolved = [i for i in visible if i["status"] != "resolved"]

        reasons = []
        if assigned and link["since"] < no_session_cut and not any(s["date"] >= no_session_cut for s in present):
            reasons.append("no_recent_session")
        if assigned and term and not in_term and day > _midpoint(term):
            reasons.append("no_meeting_this_term")
        if overdue:
            reasons.append("overdue_action")
        if any(i["raised_at"][:10] < stale_cut for i in unresolved):
            reasons.append("stale_issue")

        out.append({
            "mentor_id": link["mentor_id"],
            "mentor_name": link["mentor_name"],
            "student_id": link["student_id"],
            "name": link["name"],
            "roll_no": link["roll_no"],
            "mentorship_type": link["type"],
            "meetings_this_term": len(in_term),
            "meetings_required": cfg.min_meetings_per_term if assigned else 0,
            "last_session_date": max((s["date"] for s in present), default=None),
            "open_actions": sum(1 for a in mine if a["status"] == "open"),
            "overdue_actions": len(overdue),
            "open_issues": len(unresolved),
            "unconfirmed_sessions": sum(1 for s in present if s["confirmed_at"] is None and s["date"] < confirm_cut),
            "needs_attention": bool(reasons),
            "attention_reasons": reasons,
        })
    out.sort(key=lambda r: (not r["needs_attention"], -len(r["attention_reasons"]), r["name"]))
    return out


def mentor_home(user: CurrentUser) -> list[dict[str, Any]]:
    """API-024: the caller's active mentees (assigned and guide), flagged ones first."""
    return run_read(lambda tx: link_rows(tx, [user.user_id]))
