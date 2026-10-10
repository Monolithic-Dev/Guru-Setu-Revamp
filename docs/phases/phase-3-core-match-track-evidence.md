# Phase 3: Core B, Match, Track and Evidence (7:00–10:00)
Purpose:      Finish every P0 requirement: Fit Check and candidates, the read side of mentoring (mentor home, Mentee 360, student mentorship page), the department dashboard and exports. Then pass the core freeze.
Audience:     P1–P4.
Depends on:   phase-2-core-verify-mentor.md (G2 passed or cut decisions taken); ai-system §4; backend §4, §6.4, §7, §10; ux-flows FLOW-03, 04, 09, 10, 11; security §4
Status:       Draft v1

---

## 1. Goal and gate

**Goal:** by 10:00 the full primary flow (PRD §8, index §7) runs on a fresh seed, twice in a row, with no fixtures left in any P0 screen.

**G3 CORE FREEZE (10:00, whole team, 30 minutes):**
- [ ] `docker compose exec -e TODAY_OVERRIDE=2026-10-10 backend pytest -q` is green for all P0 tests: TEST-01..16, 18..23, 27..35, 39, 42, 43
- [ ] Index §7 scenario steps 1–10 pass on a fresh `seed --reset`, twice in a row, in 4 browser profiles
- [ ] TEST-52 (network off, `LLM_PROVIDER=none`) passes once
- [ ] `grep -rn "fixtures/" frontend/src/app` returns nothing for P0 routes
- [ ] TEST-40: API-012, 015, 024 and 033 each respond in < 2 s on the demo laptop
- [ ] Both XLSX exports open, README!A1 says DRAFT, and grepping for "SECRET-NOTE" finds nothing (TEST-21)

**If G3 fails:** Phase 4 does not start. 10:00–12:30 goes to fixing in this order: security → session/action items → mentor home → HOD dashboard → Fit Check → exports → certificate UI. Re-run G3 at 11:00 and at 12:00.

## 2. Task board

| ID | Owner | Est | Depends on | Task |
|---|---|---|---|---|
| T3.P1.1 | P1 | 1:00 | T1.P1.4 | Scorer (MDL-03) + unit TEST-18 |
| T3.P1.2 | P1 | 0:45 | T3.P1.1 | API-012 (my_fit), 013, 015, 016 |
| T3.P1.3 | P1 | 0:30 | T3.P1.2, T2.P4.2 | Tune seed and overrides so A-16 holds; TEST-19, 22, 39 |
| T3.P1.4 | P1 | 0:45 | T3.P1.2 | Fit UI components + SCR-03 (FLOW-03) |
| T3.P2.1 | P2 | 0:50 | T2.P2.4 | Needs-attention rules + API-024 (mentor home) |
| T3.P2.2 | P2 | 0:40 | T3.P2.1 | API-025 Mentee 360 + API-029 My mentorship |
| T3.P2.3 | P2 | 0:40 | T3.P2.1 | Metrics MET-01..10 + API-033 dashboard |
| T3.P2.4 | P2 | 0:30 | T3.P2.3 | Exports API-035/036 |
| T3.P2.5 | P2 | 0:20 | all | Notification and status-history audit; TEST-32..35, 42, 43 |
| T3.P3.1 | P3 | 0:50 | T3.P2.1 | SCR-06 mentor home (FLOW-09) |
| T3.P3.2 | P3 | 1:10 | T3.P2.2 | SCR-07 Mentee 360 |
| T3.P3.3 | P3 | 0:45 | T3.P1.4 (components) | SCR-09 candidates + decisions (FLOW-04) |
| T3.P3.4 | P3 | 0:15 | — | Switch SCR-08's attendee source to live API-024 |
| T3.P4.1 | P4 | 1:15 | T3.P2.3, T3.P2.4 | SCR-11 coordinator dashboard + exports (FLOW-10) |
| T3.P4.2 | P4 | 0:30 | T3.P1.2 | SCR-02 student home |
| T3.P4.3 | P4 | 0:30 | T1.P2.4 | SCR-14 notifications + SCR-15 own openings list |
| T3.P4.4 | P4 | 0:15 | T3.P2.2 | SCR-05 switch to live API-029 |
| T3.P4.5 | P4 | 0:30 | all | 9:15 dry run of the index §7 scenario; triage bug list |

**9:15 dry run.** P4 drives the scenario with whatever is merged, and posts a numbered bug list. Each bug gets an owner and a priority: P0 blocks the freeze, P1 can wait. 9:15–10:00 is fix time for everyone.

## 3. Task details

### T3.P1.1 Scorer (1:00)
- **Spec:** ai-system §4 (the formula, rounding, verdict, gains, why-paths, ties), A-10
- **Files:** `ml/scorer.py`, `tests/test_scorer.py`
- **Steps:**
  1. Pure function `score(required: list[str], idf: dict, skills: dict[str, int], similar: dict[(str, str), float], sem: float, cfg) -> Fit`, with no I/O, so it is unit-testable.
  2. Implement the per-required-concept chip logic. For near matches, choose the `s` that maximises `score·t(s)`.
  3. Components: round each one, then sum the rounded values to get the score.
  4. Gains: re-run `score()` with `skills[r] = max(skills.get(r, -1), 1)` for each non-matched `r`, and sort descending.
  5. Why-paths come from the chips (P1 uses them in Phase 4).
- **Done when:** TEST-18 passes. The worked example gives exactly 43.4 → 68.5 with semantic fixed at 0.70; the boundaries 39.9/40.0/64.9/65.0 work; empty `R` → semantic only, with the note.

### T3.P1.2 Fit APIs (0:45)
- **Spec:** API-012, 013, 015, 016; backend §4.1 example; security §4 (applicants only)
- `repos/match_repo.py`: one read query per call that returns the required concepts, the student's HAS_SKILL trust levels plus the `evidence_ids` of the first source, the SIMILAR_TO pairs among the relevant concepts, and both embeddings. IDF comes from `idf_table` (cache it per request).
- API-015: as a student, self only. As faculty, `student_id` must be an applicant of the faculty's own opening (404 otherwise). Chips carry `source` from the first certified evidence.
- API-016: owner only. Score every applicant; tie-break by more matched chips, then `applied_at`.
- API-012: for students, compute `my_fit` (score + verdict) for each open opening (≤ 12 × scorer, fast) plus `my_application_status`.
- **Done when:** the API-015 response for Aarav matches the shape in backend §4.1, and TEST-22 and TEST-39 pass.

### T3.P1.3 Seed tuning for A-16 (0:30)
- **Spec:** AC-004.1, TEST-19, A-16
- Measure the real cosine for Aarav ↔ op-edge-ai, and check the before score falls in 38–50 and the after score is ≥ 65.
- If not, adjust **seed content only** (Aarav's bio and interests, the opening description), never the formula or thresholds. If you change the formula anyway, update AC-004.x, TEST-18/19 and ai-system §4 in the same commit.
- Also check that `op-edge-ai`'s 3 seeded applicants score in different bands, so the ranked list looks credible.
- **Done when:** TEST-19 passes on a fresh seed, after running the TEST-13 uploads.

### T3.P1.4 Fit UI and SCR-03 (0:45)
- **Spec:** FLOW-03, ux-flows §6.1 wireframe, components `FitScoreRing`, `ScoreBreakdownBar`, `SkillChip`, `TrustBadge`
- **Steps:**
  1. Build `FitScoreRing` (score + verdict text, `aria-label`, reduced-motion aware) and `ScoreBreakdownBar` (3 segments, values also as text).
  2. Chips are grouped Matched / Claimed only / Near (with "via X") / Missing. Gains are shown as "Certify X → N". "Prove it" links go to `/student/certificates`.
  3. The Apply button calls API-017: 201 → pill "Applied · Pending"; 409 `ALREADY_APPLIED` → pill "Applied"; `OPENING_CLOSED` → copy.
  4. Export the components so P3 can reuse them read-only on SCR-09.
- **Done when:** index §7 steps 1 and 3 render correctly against the live API.

### T3.P2.1 Needs-attention and mentor home (0:50)
- **Spec:** backend §6.4 (rule table, `meetings_this_term`, `unconfirmed_sessions`, sort order), API-024, `MenteeRow`
- **Files:** `services/tracking.py`, `repos/tracking_repo.py`, `api/v1/tracking.py`
- **Steps:**
  1. One read query: active MENTORS from the caller → per student, collect sessions by this mentor (date, context, present, confirmed_at), action items from this mentor's sessions (status, due), visible issues (status, raised_at, confidential, raised_by), and the latest academics.
  2. Evaluate the rules in Python with config thresholds and the term from `CURRENT_TERM_ID` or today's date. Implement the P2 reasons behind `if` checks that return nothing until Phase 5.
  3. Sort: flagged first, then by number of reasons, then by name.
- **Done when:** TEST-33 passes (13 rows, exactly Karthik, Diya and Rahul flagged with the seeded reasons).

### T3.P2.2 Mentee 360 and My mentorship (0:40)
- **Spec:** API-025, API-029, `MenteeOverview`, `MyMentorship`, security §4 (every row), REQ-013, REQ-014
- **API-025:** scope is `mentor_of` or the HOD of the department. Return:
  - the profile (API-003 shape);
  - mentorships;
  - academics (marked `[MOCK]` in a code comment);
  - sessions (`SessionSummary`, with notes only on the caller's own sessions);
  - action items;
  - issues, applying the §4 text rules;
  - applications;
  - certificates;
  - `attention_reasons`.
  - Each of the action items, issues and applications carries a `history` from StatusEvents.
  - `term_summary: null` until Phase 5.
- **API-029:** assigned mentor (name, designation, email), guides, the earliest future `next_followup`, `sessions_to_confirm` (present, unconfirmed), up to 20 recent sessions, own action items, own issues (text hidden for mentor-raised confidential ones), and applications.
- **Done when:** TEST-42 and TEST-43 pass, and TEST-20 still passes.

### T3.P2.3 Metrics and dashboard (0:40)
- **Spec:** backend §7 (MET-01..10 definitions), API-033, `Dashboard`, REQ-016, AC-016.2
- **Files:** `services/metrics.py`, `repos/metrics_repo.py`, `api/v1/dept.py`
- Compute each MET exactly as defined: department of the caller, current term, assigned context. Confidential issues go into the category `"confidential"`.
- `needs_attention_list` is for the HOD only. It reuses the T3.P2.1 rule evaluation across all department mentors.
- IQAC gets `needs_attention_count` and no names anywhere in the response.
- **Done when:** TEST-32 passes. `scripts/check_seed.py` computes the expected values independently from the JSON, and they equal API-033.

### T3.P2.4 Exports (0:30)
- **Spec:** backend §7 (export layouts), SEC-18, REQ-017, ADR-10
- **Files:** `services/evidence_export.py`, `api/v1/evidence.py`
- Use openpyxl, with sheets and columns exactly as listed. README!A1 reads "DRAFT – verify against the official NAAC manual before submission".
- `safe(v)` prefixes `'` to strings that start with `= + - @`.
- Return a `StreamingResponse` with `Content-Disposition: attachment; filename="gurusetu-mentoring-<term>-DRAFT.xlsx"`.
- Build the rows from metric functions only. Never read `notes`, `Issue.text`, `ActionItem.text` or `resolution`.
- **Done when:** TEST-08 and TEST-21 pass.

### T3.P2.5 Audit pass (0:20)
Walk backend §6.9: trigger each P0 notification type once and check the recipient and title. Check that every status-changing endpoint writes a StatusEvent (TEST-34). Fix any gaps.

### T3.P3.1 SCR-06 Mentor home (0:50)
- **Spec:** FLOW-09 step 1, ux-flows §4.3 reason labels, `MenteeRow`, `AttentionBadge`
- Assigned mentees first (flagged ones on top, with reason badges), then a "Guided students" group. Each row shows meetings x/2, last session (relative date), open/overdue actions, open issues, unconfirmed count, and [Open] and [Log session] buttons.
- A header button "Log session" goes to `/faculty/sessions/new` (group). Stacked cards below 768 px.
- **Done when:** index §7 step 6's first expectation (13 rows, 3 flagged) shows against the live API.

### T3.P3.2 SCR-07 Mentee 360 (1:10)
- **Spec:** REQ-013, FLOW-09 steps 2–3, ux-flows wireframe, `Timeline`, `ActionItemList`, `IssueList`, security §4
- **Layout:** two columns at ≥ 1280 px.
  - Header: name, roll number, year and attention badges.
  - Skills with trust badges.
  - Academics table labelled "Sample data".
  - Timeline merging sessions, action items, issues and status events by date.
  - Action items with the "To verify" group: [Verify] [Reopen] [Drop] → API-030.
  - Issues with [Resolve] → a resolution dialog → API-032.
  - Applications, certificates, and a "Log session for {first name}" button.
- When `notes` is present, render it in a "Private notes" box. Otherwise show nothing, not even an empty box.
- **Done when:** index §7 step 8 works against the live API, and the HOD view shows no notes box.

### T3.P3.3 SCR-09 Candidates (0:45)
- **Spec:** FLOW-04, REQ-005, REQ-006
- Ranked applicant cards (API-016), each expandable to the read-only Fit components. Action buttons follow the status (FLOW-04) → API-018. On 409 `INVALID_TRANSITION`: toast and refetch. The accept toast is "Aarav Menon accepted. Guide link created."
- **Done when:** index §7 step 4 works against the live API.

### T3.P3.4 SCR-08 live attendees (0:15)
Replace the fixture with API-024 rows. "Select all mentees" selects the assigned rows only. The context select shows the guide openings from those rows.

### T3.P4.1 SCR-11 Coordinator dashboard (1:15)
- **Spec:** FLOW-10, REQ-016, REQ-017, ux-flows wireframe, `KpiTile`, `MentorTable`, `ExportButton`, `recharts`
- **Steps:**
  1. A "DRAFT evidence · {term}" banner.
  2. KPI tiles: allotted/total, ratio, compliance %, issues resolved/raised, overdue actions, pending reviews.
  3. Mentor table with compliance below 100% highlighted, plus the Overloaded badge.
  4. Issues-by-category bar chart (`recharts` BarChart, raised vs resolved; the confidential bar is labelled "Confidential") and achievements-by-type.
  5. HOD only: the needs-attention list, linking to SCR-07.
  6. Export buttons (blob download with the filename from `Content-Disposition`).
- **Done when:** index §7 steps 9 and 10 pass; the IQAC view shows no names.

### T3.P4.2 SCR-02 Student home (0:30)
- **Spec:** REQ-004, REQ-014 (summary), wireframe
- A summary strip from API-029 ("My mentor: Dr. Meera · 1 to confirm ▸"), plus opening cards from API-012 with the fit score and verdict pill, and an application status pill when applied. Cards link to SCR-03.
- Empty state per FLOW-11.
- **Done when:** step 1 of the scenario starts here.

### T3.P4.3 SCR-14 and SCR-15 (0:30)
- **SCR-14:** API-037 list with unread items in bold, [Mark read] → API-038, a link per `link`, and "Load more" via `next_cursor`.
- **SCR-15:** own openings from API-012 (filtered by `faculty.user_id == me`) with `applicant_count` from API-013, linking to SCR-09. The create button is hidden until A9 (Phase 4).

### T3.P4.4 SCR-05 live (0:15)
Replace the `MyMentorship` fixture with API-029.

### T3.P4.5 Dry run (0:30)
Run the index §7 scenario at 9:15 and file numbered bugs in `status.md`. At 9:45, reseed and run it once more to warm up for G3.

## 4. Risks and fallbacks

| Risk | Fallback |
|---|---|
| Aarav's real cosine pushes the before score outside 38–50 | T3.P1.3 tunes the seed text; if still off, the test asserts the verdict `close` → `ready` only (record it in decisions-log) |
| The Mentee 360 query is slow | Split it into 3 read queries (profile+skills, mentoring, applications+certificates) in one session |
| The dashboard numbers disagree with `check_seed.py` | Trust the definitions in backend §7. Fix whichever side deviates, and never edit the expected numbers to match the API |
| P3 can't finish SCR-07 | Cut the Timeline (show the plain sections); keep action items and issues interactive |
| Exports fail on Windows Excel | Test in LibreOffice too; keep `.xlsx` only, no macros, no formulas |
