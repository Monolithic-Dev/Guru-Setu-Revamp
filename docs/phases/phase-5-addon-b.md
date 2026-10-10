# Phase 5: Add-on B (stretch, within 10:00–12:15 only)
Purpose:      Specify the P2 requirements, so that anyone who finishes their Phase 4 items early can pick one up safely, and so that the rest are ready for the roadmap slide.
Audience:     Whoever has merged all their own ADD-ON A items before 11:30.
Depends on:   phase-4-addon-a.md rules (§1); PRD REQ-027, 028, 029, 032, 033, 034, 035; backend §6.2, §6.4, §6.8, §7 (MET-11); security §4
Status:       Draft v1

## 1. Entry rules

- Start a B item only if (a) all your A items are merged, (b) it is before **11:30**, and (c) the item's estimate fits before 12:15. No B item merges after 12:15.
- The B items are independent of each other. Pick from the top of the list.
- **Expected outcome:** 0–2 B items get built. The rest stay specified, and are shown as "designed, next" on the roadmap slide.
- The same per-item merge gate applies as in Phase 4 §1.

## 2. Items (in recommended order)

| # | Item | REQ | Best owner | Est | Test | Why this order |
|---|---|---|---|---|---|---|
| B1 | At-risk suggestions + mentor mark | 029 | P2 (+P3 badge) | 0:30 | TEST-46 | Strengthens the "needs attention" story with almost no UI |
| B2 | Semester summary in Mentee 360 | 032 | P2 + P3 | 0:30 | TEST-48 | Pure counts; one card |
| B3 | Learner-level tag + export count | 033 | P2 + P3 | 0:35 | TEST-49 | Adds a NAAC-style metric (MET-11) |
| B4 | Faculty endorsement (trust level 2) | 027 | P1 (+P3 button) | 0:35 | TEST-45 | Completes the Trust Ladder |
| B5 | Mentor handover view rules | 028 | P2 + P4 | 0:30 | TEST-27 (extended) | The data rule already works (T2.P2.2); this adds the UI and the "Logged by Dr. X" display |
| B6 | Session feedback | 034 | P2 + P4 | 0:30 | TEST-56 | Nice to have |
| B7 | Faculty track record page | 035 | P2 + P4 | 0:40 | TEST-57 | New screen SCR-16; lowest value for the demo |

## 3. Item details

### B1 At-risk (REQ-029)
- **Backend:**
  - In the T3.P2.1 rule evaluation, enable `suggested_at_risk` when the current-term AcademicRecord has `attendance_pct < 75`, or CGPA dropped by ≥ 1.0 against the previous term. Return a detail string for the UI ("attendance 68%").
  - Fill `attention_details` on the row (already in the `MenteeRow` schema), for example `{"suggested_at_risk": "attendance 68%"}`.
  - API-043 `marked_at_risk` (assigned mentor only) gives `marked_at_risk`.
- **Frontend (P3):** the badge copy "Suggested at risk: {detail}" in `AttentionBadge` (ux-flows §4.3), plus a "Mark at risk" toggle on SCR-07.
- **Done when:** TEST-46 passes. The 3 seeded low-attendance students appear flagged, which raises the needs-attention count. Re-check that TEST-33's "exactly 3 flagged for Meera" still holds; seed the low-attendance students outside Meera's group to keep it.

### B2 Semester summary (REQ-032)
- **Backend:** in API-025, `term_summary` = counts derived in Python from the lists already in the response, filtered to the current term: sessions attended (present), actions done (done or verified) / total, issues raised / resolved, certificates certified.
- **Frontend:** a "This term" card at the top of SCR-07.
- **Done when:** TEST-48 passes.

### B3 Learner level (REQ-033)
- **Backend:** API-043 `learner_level` and `learner_note`, assigned mentor only, with a `record_status(entity_type='mentorship', note='learner_level')` that never stores the note text. MET-11 in the export Summary sheet reads "Slow learners identified: N / Advanced learners identified: M".
- **Frontend:** a segmented control on SCR-07 (Slow / Average / Advanced) plus a note textarea labelled "Visible only to you".
- **Privacy:** the HOD sees the level and not the note; IQAC sees counts only (security §4).
- **Done when:** TEST-49 passes.

### B4 Endorsement (REQ-027)
- **Backend (P1, in its own router file `api/v1/endorsements.py`):** API-041, where the caller must be `mentor_of` the student (assigned or guide). The concept must already be on the student's profile (422 otherwise). Append the caller to `HAS_SKILL.endorsed_by`, then `recompute_skill` → trust 2. Fit weight 1.0 applies automatically.
- **Frontend:** an "Endorse" button next to each skill on SCR-07 (P3) and a ★ Faculty-verified `TrustBadge` variant (already built).
- **Done when:** TEST-45 passes. On stage, Aarav's pytorch shows "Faculty-verified · Dr. Meera Raman", and his fit rises (0.85 → 1.0 on that skill).

### B5 Handover view (REQ-028)
- **Backend:** already correct if T2.P2.2 and the API-025 notes rule hold. Add a check in TEST-27 that the new mentor's API-025 shows earlier sessions with `logged_by` set to the old mentor and no `notes`.
- **Frontend (P4):** on SCR-12, a "Change mentor" action per allotted student (a dialog with a mentor select → API-023).
- **Frontend (P3):** on SCR-07, the timeline shows "Logged by Dr. X" for sessions by others.
- **Done when:** the extended TEST-27 passes.

### B6 Session feedback (REQ-034)
- **Backend:** API-042 by a present attendee only (409 `NOT_PRESENT` otherwise), replacing earlier feedback on `ATTENDED_BY.feedback(_comment)`. It is visible only in the author's API-027 (add `feedback` per attendee, author only).
- **Frontend (P4):** after confirming on SCR-05, offer "Helpful" / "Not helpful" buttons (text labels) plus an optional comment.
- **Done when:** TEST-56 passes.

### B7 Faculty track record (REQ-035)
- **Backend:** API-044 counts:
  - openings POSTED;
  - guide MENTORS created (accepted);
  - guide MENTORS ended with `completed`;
  - the median of (first StatusEvent after `pending` minus `applied_at`) in days over the faculty's applications, or null when there are none.
  - No ratings, ever (NG-11).
- **Frontend (P4):** SCR-16 `/faculty-profile/[id]` with four stat tiles.
- **Frontend (P1):** link the faculty name on SCR-03 (your page) to SCR-16.
- **Done when:** TEST-57 passes.

## 4. Roadmap slide content for unbuilt B items

List each unbuilt B item as "Designed (spec REQ-0xx), next sprint". Add the enterprise roadmap from team plan §19: skill viva, Graph-RAG copilot, Open Badges / verifiable credentials, auditor portal, CO-PO, NIRF simulator, APAAR/DigiLocker/ABC, SSO, multi-campus, consent ledger, parent and counsellor workflows, peer and alumni mentors.
