# Phase 4: Add-on A (10:00–12:30)
Purpose:      Add the P1 requirements that make the demo stronger, in a fixed priority order, without ever breaking the core flow.
Audience:     P1–P4.
Depends on:   phase-3 G3 passed (if it didn't, this phase is replaced by fixing; see phase-3 §1); PRD REQ-019..026, 030, 036; backend §4, §6.7, §6.10, §7; ai-system §3 (rule 6), §4, §10; ux-flows FLOW-03, 08, 09, 11
Status:       Draft v1

---

## 1. Rules for this phase

1. **Priority order is fixed** (team plan §13.2, with REQ-030/036 slotted in). If time runs out, the lowest items are dropped, never the higher ones.
2. **Per-item merge gate:** an item merges to `main` only after (a) its TEST-xx passes, (b) `pytest -q` stays green for all P0 tests, and (c) the person merging re-runs index §7 steps that touch the changed screens. An item that misses the gate by 12:15 is reverted or left on its branch.
3. **Feature flags are unnecessary.** Each item is additive (a new endpoint, panel or button). If one misbehaves on stage, hide its entry point with a one-line revert.
4. Nobody starts a Phase 5 (ADD-ON B) item until all their own A items are merged.

## 2. Items, owners and estimates

| # | Item | REQ | Backend | Frontend | Test | Est (be + fe) |
|---|---|---|---|---|---|---|
| A1 | Click-to-source drill-down | 019 | P2: API-034 | P4: SCR-13 + clickable KpiTiles | TEST-37 | 0:40 + 0:45 |
| A2 | "Why this match?" graph | 020 | P1: API-020 | P3: WhyGraph on SCR-03 | TEST-24 | 0:30 + 1:15 |
| A3 | Reminders | 023 | P2: API-039 | P3: reminders on SCR-14 + SCR-06 badge | TEST-36 | 0:30 + 0:20 |
| A4 | Full issue lifecycle, escalation, confidential | 022, 036 | P2: API-032 transitions, escalation notify, confidential filtering, API-033 `escalated_issues` | P3: SCR-07 issue actions; SCR-08 confidential toggle. P4: SCR-11 escalated list (0:15) | TEST-38, TEST-26 | 0:40 + 0:45 |
| A5 | Skill-gap panel | 021 | P1: API-021 | P1: fills `SkillGapCard` (rendered on P4's SCR-02) | TEST-25 | 0:30 + 0:20 |
| A6 | Evaluation table | 026 | P1: `scripts/eval_match.py` + EVAL-01 raw run summary | P4: slide | EVAL-03 | 0:45 |
| A7 | Mentee request meeting / raise issue | 024 | P2: API-045 + student path of API-031 | P4: SCR-05 dialogs | TEST-44 | 0:20 + 0:20 |
| A8 | Tamper signals | 025 | P1: rule 6 | — (copy already exists) | TEST-17 | 0:30 |
| A9 | Create opening | 030 | P2: API-014 (`openings_write.py`) | P3: route `/faculty/openings/new`; P4's SCR-15 link appears via flag | TEST-47 | 0:15 + 0:20 |

**Per-person sequence (2.5 h each):**

| Person | Order | Total |
|---|---|---|
| P1 | A2 backend (0:30) → A5 (0:50) → A6 (0:45) → A8 (0:30) | 2:35 |
| P2 | A1 backend (0:40) → A3 backend (0:30) → A4 backend (0:40) → A7 backend (0:20) → A9 backend (0:15) | 2:25 |
| P3 | A2 frontend (1:15) → A3 frontend (0:20) → A4 frontend (0:30) → A9 frontend (0:20) | 2:25 |
| P4 | A1 frontend (0:45, after P2's A1 at ~10:40) → A4 SCR-11 escalated list (0:15) → A7 frontend (0:20) → deck build (1:10) | 2:30 |

P4 starts the deck at 10:00 while P2 builds API-034, then switches to SCR-13 at about 10:40.

## 3. Item details

### A1 Click-to-source (REQ-019)
- **Backend (P2), API-034:**
  - `metric` must be one of the 7 enum values. Each one reuses the exact filter of the matching MET function from backend §7: refactor so the count and the rows come from one function (`rows = metric_rows(name, ctx)`, `count = len(rows)`).
  - Rows per metric:
    - compliance: student, mentor, meetings, compliant y/n
    - issues_raised / issues_resolved: date, mentor, category, status (never text)
    - overdue_actions: due, mentor, owner, status (never text)
    - achievements: title, issuer, date, level, type, status
    - needs_attention: student, mentor, reasons
    - pending_reviews: certificate title, student, created
  - IQAC: replace student name and roll number with `Student 01…` in row order, with the numbering stable within the response.
  - Cursor pagination (backend §3); `total` equals the dashboard number.
- **Frontend (P4):** make `KpiTile` clickable (a link with the metric). SCR-13 is a table with the column set per metric, a "Back to dashboard" link, and the header "{label}: {total} records".
- **Done when:** TEST-37 passes for every metric. On stage, click "Issues resolved" and the row count equals the tile.

### A2 Why graph (REQ-020)
- **Backend (P1), API-020:**
  - Run `score()` for the caller, then convert the chips into `WhyGraph`:
    - node ids are `student:<id>`, `concept:<name>`, `opening:<id>`;
    - edges are HAS_SKILL (student → concept, with trust in the label), SIMILAR_TO (with score) and REQUIRES (opening → concept).
  - Only matched, claimed_only and near chips produce paths. Missing concepts appear as isolated concept nodes connected to the opening only.
- **Frontend (P3):** replace the stub in `components/why/WhyGraph.tsx` and set `whyGraph: true` in `lib/features.ts` (your line only). P1's SCR-03 already renders the button and the component behind the flag (T3.P1.4). The component uses `react-force-graph-2d` in a panel or dialog:
  - node colour by kind, plus a text label (not colour only);
  - edge labels for the SIMILAR_TO score;
  - a fixed height of 360 px.
  - **A11y:** render the same paths as a text list below the graph ("deep learning → similar to (0.70) → computer vision → required by Edge AI for Agriculture").
  - Lazy-load the graph library (`next/dynamic`, `ssr:false`).
- **Done when:** TEST-24 passes, and the AC-020.1 path is visible for Aarav before the uploads.

### A3 Reminders (REQ-023)
- **Backend (P2), API-039:**
  - Compute the 4 kinds from backend §6.10, reusing the T3.P2.1 rule data. Mentor reminders cover each mentee; student reminders cover their own items.
  - `message` examples: "Karthik S has 2 of 2 meetings but an action is overdue since 7 Oct", "Confirm your session on 10 Oct".
  - Sort by due date.
- **Frontend (P3):** fill `components/mentor/RemindersPanel.tsx` (P4's SCR-14 already renders it at the top) and set `reminders: true` in `lib/features.ts`. On SCR-06 (your page), show a small "N reminders" link in the header.
- **Done when:** TEST-36 passes.

### A4 Issue lifecycle, escalation, confidential (REQ-022, REQ-036)
- **Backend (P2):**
  - **Transitions:** raised → acknowledged → in_progress → resolved, plus raised → resolved still allowed. `escalated: true` is allowed from any unresolved state and can't be undone.
  - **On escalation:** notify the department HOD (`issue_escalated`). From then on the HOD passes the issue-text predicate (security §4) and may PATCH the status or resolution.
  - **Confidential:**
    - settable by the raising mentor at creation (API-026/031) or by PATCH;
    - text visibility per security §4;
    - MET-03/04 count it under `"confidential"`;
    - a confidential issue can't be escalated (409 `INVALID_TRANSITION`, detail "Confidential issues cannot be escalated"). This keeps the HOD rule simple.
- **Frontend (P3):**
  - SCR-07 issue row: [Acknowledge] [In progress] [Resolve] [Escalate to HOD] (confirm dialog "The HOD will be able to read this issue."), and a "Confidential" toggle with an explanatory tooltip.
  - SCR-08 issue repeater: a confidential checkbox.
- **Backend (P2), dashboard:** fill `escalated_issues` in API-033 (HOD only; schema already in `openapi.yaml`).
- **Frontend (P4, SCR-11):** render an "Escalated issues" list (HOD only) from `escalated_issues`, each linking to SCR-07, where the HOD resolves it.
- **Done when:** TEST-38 and TEST-26 pass.

### A5 Skill-gap panel (REQ-021)
- **Backend (P1), API-021:** for each concept c that is required by any open opening and that the student lacks (or holds at trust 0), compute for each opening whether `score(with c at trust 1) ≥ FIT_READY_MIN` while the current score is below it. Return the top 5 by `openings_unlocked`, then by `total_gain`. This is at most about 40 concepts × 12 openings of pure scorer calls.
- **Frontend (P1):** fill `components/fit/SkillGapCard.tsx` (P4's SCR-02 already renders it) and set `skillGap: true` in `lib/features.ts`. The card: "Learn docker → unlocks 2 openings", with a "Prove it" link to SCR-04. It is hidden when the list is empty.
- **Done when:** TEST-25 passes.

### A6 Evaluation table (REQ-026)
- **Steps:**
  1. Read `seed/labels/match_labels.csv` (10 students × 12 openings, relevance 0/1/2, labelled by P4 before seeing scores; do the labelling in Phase 2's buffer if possible).
  2. For each student, rank the openings by hybrid `score()` and by the baseline (Jaccard of claimed + certified skill names vs required names, the old GuruSetu method).
  3. Compute nDCG@10 (gains 2^rel − 1, log2 discount) and P@5 (rel ≥ 1 counts as relevant), averaged over students.
  4. Print a Markdown table, and also write it to `docs/plan/eval-results.md` together with the EVAL-01 raw accuracy from T2.P1.3.
- **Honesty rule:** the slide shows exactly these numbers, with n = 10 students stated. If the hybrid doesn't beat the baseline, say so; don't re-tune on the test labels.
- **Done when:** the script runs in < 30 s and the results file is committed.

### A7 Mentee-initiated contact (REQ-024)
- **Backend (P2):**
  - API-045: 404 if there's no active assigned mentor; message 1–300 characters; notify `meeting_request` with the message in `body` (it is the student's own text and the mentor is the intended reader).
  - API-031 as a student: `student_id` must be self; `raised_by_role:'student'`; notify `issue_raised_by_mentee` with no text in the notification.
- **Frontend (P4):** two dialogs on SCR-05: "Request a meeting" (message) and "Raise an issue" (category + text). Toasts per FLOW-08.
- **Done when:** TEST-44 passes.

### A8 Tamper signals (REQ-025)
- **Backend (P1):** rule 6 in `verification.py`:
  - read the EXIF `Software` tag (Pillow `getexif().get(305)`) and match it against the editor list (case-insensitive);
  - ELA: re-save as JPEG at quality 90, take the mean absolute difference over all channels, and flag if > `ELA_THRESHOLD`.
  - Tune `ELA_THRESHOLD` on the seed files so that only the planted file trips it (A-17). If no value separates them, use the EXIF signal only and note it in the decisions log.
  - Enable with `TAMPER_CHECK_ENABLED=true` in `.env.example` only after tuning.
- **Done when:** TEST-17 passes, and a full seed reset produces no new `tamper_signal` on non-planted files.

### A9 Create opening (REQ-030)
- **Backend (P2):** API-014 in its own router file `api/v1/openings_write.py` (P1's `match.py` keeps the read routes). Validation per the `OpeningCreate` schema. Normalise skills via `get_or_create_concept`, create `POSTED` and `REQUIRES`, and compute the embedding. IDF changes automatically, since it is computed per request.
- **Frontend (P3):** the page `src/app/faculty/openings/new/` (your route) with a form (title, description, skills as a chip input) and the validation copy from ux-flows §6. On success, go to SCR-09 for the new opening. Then set `createOpening: true` in `lib/features.ts`, which makes P4's existing link on SCR-15 appear.
- **Done when:** TEST-47 passes.

## 4. 12:15 check

- Every merged item: its test is green, and the core scenario was re-run once after the last merge.
- Unmerged items: decide **merge now** (only if green) or **drop**. Dropped items go on the roadmap slide under "next".
- Update `status.md` and tell P4 which add-ons the demo script may show.
