# Test Strategy, Failure Modes and Manual QA
Purpose:      Define the tests that prove each P0 requirement and security control, the failure modes the system must survive, and the manual checks before the demo.
Audience:     All builders; whoever signs off the core freeze.
Depends on:   docs/01-product/prd.md, docs/02-architecture/architecture.md, docs/04-backend/backend.md, docs/05-frontend/ux-flows.md, docs/06-ai/ai-system.md, docs/08-security/security-and-privacy.md, docs/10-devops/environments-and-deployment.md
Inputs used:  REQ-, NFR-, SEC-, EVAL- IDs; RISK-02..05
Status:       Draft v1 | assumptions in this document: A-01, A-23

Failure modes (§4) and the manual QA checklist (§5) are sections of this document.

## 1. Approach

**Pyramid for this project:** about 40% unit tests (scorer, verification rules, needs-attention rules, XLSX sanitiser: pure functions where the business rules live), about 55% API integration tests against a real Neo4j (security, state machines, privacy filters, metrics: the risk is in queries and scope checks, which only a real database exercises), and about 5% end-to-end (one Playwright primary flow plus the manual checklist).

**Tools:** pytest 8.x, httpx 0.27.x, Playwright 1.4x, Lighthouse in Chrome DevTools; exact versions are pinned in T0.P1.1 / T0.P3.1 [VERIFY: pypi.org, npmjs.com at hour 0].

Calibrated to 15 h (A-01):

| Layer | Tool | Scope | When |
|---|---|---|---|
| API integration | `pytest` + `httpx` against the running API and a real Neo4j | Security (all P0), state machines, privacy filters, metrics | Every merge; at the core freeze |
| Unit | `pytest` | Scorer formula, confidence, needs-attention rules, XLSX sanitiser | With the code |
| Eval | Scripts in ai-system §10 | EVAL-01..04 | Once after the cache build; after any prompt change |
| E2E (P1) | Playwright | Primary flow (PRD §8) | Before the feature freeze |
| Manual | §5 checklist, stopwatch, Lighthouse | UX, a11y, offline | Core freeze + demo eve |

**Test data:**
- Integration tests run against a freshly seeded database: a session-scoped fixture runs `scripts.seed --reset`, with `TODAY_OVERRIDE=2026-10-10`.
- Tests that mutate data run in the order given, or reseed. Seed personas are named fixtures (`aarav`, `meera`, `arjun`, `suresh`, `kavya`) that return tokens.
- No mocks of Neo4j. MDL-01 is never called in tests: `LLM_PROVIDER=none` plus the cache, and failure paths use a stub adapter injected via dependency override.

## 2. Test cases

### 2.1 Security (`tests/test_security.py`), all P0
| ID | Case | Expected |
|---|---|---|
| TEST-01 | Call every GET route as each persona; recursively scan the JSON | No key named `password_hash`, `embedding` or `file_path` (SEC-01) |
| TEST-02 | POST `/auth/register`, `/auth/verify-identity`, `/auth/reset-password`, `/users/upload-profile-picture`; GET `/dashboard/student/home`, `/recommend/recommendations/student/openings` | 404 each (SEC-02) |
| TEST-03 | Call every route except API-001/040 with no token, `Bearer abc`, and a token signed with the wrong key | 401 `UNAUTHENTICATED` (SEC-03) |
| TEST-04 | Role matrix: student → API-016, 018, 022, 023, 024, 026, 033, 035; faculty → 022, 023, 033, 035; iqac → 024, 026, 022 | 403 `FORBIDDEN` (SEC-04) |
| TEST-05 | Scope: Arjun → API-016 on `op-edge-ai`; Arjun → API-025 for Aarav; Arjun → API-027 for Meera's session; another student → API-006/011 for Aarav's certificate; Arjun → API-018 on an `op-edge-ai` application | 404 `NOT_FOUND` (SEC-05) |
| TEST-06 | Upload without a token; upload as faculty; check the stored path is under `UPLOAD_DIR` with a UUID name; GET `/uploads/<name>` | 401; 403; path matches `^/data/uploads/[0-9a-f-]{36}\.(png\|jpg\|pdf)$`; 404 (SEC-06) |
| TEST-07 | Bio `"x' RETURN 1 //"`, issue text `"}) MATCH (n) DETACH DELETE n //"` | Stored and returned literally; node count unchanged (SEC-17) |
| TEST-08 | Student name `=HYPERLINK("http://x")` in seed override → API-035 → read the cell with openpyxl | Value starts with `'=` (SEC-18, AC-017.2) |
| TEST-09 | 11 logins in 60 s from one client; 21 uploads in an hour (time frozen) | 11th login and 21st upload → 429 with `Retry-After` (SEC-11) |
| TEST-10 | Preflight from `http://evil.test`; response headers on API-002; start the app with a 10-character `JWT_SECRET_KEY` | No ACAO header; nosniff, no-referrer, DENY present; startup fails with a clear error (SEC-10, 12, 21) |
| TEST-11 | Expired token (exp in the past); wrong password vs unknown email | 401 `TOKEN_EXPIRED`; identical 401 body `INVALID_CREDENTIALS` for both (SEC-20) |
| TEST-12 | 10 MB + 1 byte file; `.pdf` whose bytes are a ZIP; 6-page PDF | 413; 415; 422 "PDF must have at most 5 pages" (NFR-07) |

### 2.2 Certificates and matching
| ID | Case | Expected | REQ |
|---|---|---|---|
| TEST-13 | Upload the 4 demo files as Aarav and poll | `aarav_dl_pytorch` → certified; `aarav_cv_workshop` → certified; `aarav_python_copy` → duplicate (`duplicate_image`); `aarav_embedded_c` → needs_review (`name_mismatch`) | 001, 002, EVAL-02 |
| TEST-14 | Stub adapter raises a timeout → certificate `failed` → API-008 with valid fields | `failed`, then `needs_review` with confidence ≤ 0.50 and reason `manual_entry` | 037 |
| TEST-15 | Reject a certificate that was the only proof of a skill | Skill returns to trust 0 if claimed, else is removed; embedding recomputed (updated_at changes) | 003 |
| TEST-16 | Stub adapter returns schema-invalid JSON twice / invalid then valid | `failed` / processed normally | 001 |
| TEST-17 (P1) | Upload the planted Photoshop-EXIF image with `TAMPER_CHECK_ENABLED=true` | `needs_review`, `tamper_signal` | 025 |
| TEST-18 | Unit: scorer on hand-built inputs from the ai-system §4 worked example | 43.4 and 68.5; components sum to the score; verdict thresholds at 39.9/40.0/64.9/65.0 | 004 |
| TEST-19 | API-015 for Aarav before and after TEST-13 | 38 ≤ before ≤ 50 with verdict `close`; after ≥ 65 with verdict `ready` | 004 |
| TEST-22 | API-016 on `op-edge-ai` after Aarav applies | 4 applicants sorted by score descending | 005 |
| TEST-23 | Application transitions: every cell of backend §6.3; double apply; apply to a closed opening | Allowed → 200; disallowed → 409 `INVALID_TRANSITION`; 409 `ALREADY_APPLIED`; 409 `OPENING_CLOSED`; on accept, a guide MENTORS link exists | 006 |
| TEST-24 (P1) | API-020 for Aarav before uploads | Contains edges deep learning –SIMILAR_TO– computer vision and computer vision ←REQUIRES– op-edge-ai | 020 |
| TEST-25 (P1) | API-021 for Aarav | ≤ 5 items, ranked by `openings_unlocked` then summed `total_gain`. On the seed no single certificate lifts an opening past `FIT_READY_MIN`, so every item has `openings_unlocked = 0` and the order comes from the gain | 021 |

### 2.3 Mentorship, tracking, privacy and metrics
| ID | Case | Expected | REQ |
|---|---|---|---|
| TEST-20 | Log a session with notes "SECRET-NOTE-123". Fetch via API-027 as the author, as an attendee, as the HOD (expect 403) and as Arjun; API-025 as the author and as the HOD; API-029 as the attendee | Notes present only for the author; absent elsewhere; 404 for Arjun (SEC-07) | 015 |
| TEST-21 | After TEST-20 and issue text "SECRET-ISSUE-456": generate both XLSX exports, check the sheet names and README!A1, grep every cell; grep backend logs | Mentoring sheets `README`, `Mentors`, `Allotment`, `Summary`, `Mentor-wise`; A1 is the DRAFT notice; neither string found in exports or logs (SEC-15) | 015, 017 |
| TEST-26 (P1) | Confidential `personal` issue: HOD dashboard, HOD API-025, student API-029 for a mentor-raised confidential issue | Counted under "confidential"; text absent for HOD and student | 036 |
| TEST-27 | Allot 2 unallotted students to Meera; re-allot one to Arjun; give a mentor a 21st mentee | Unallotted −2; Meera +2; then the old link `ended` / `handover` and Arjun +1; the 21st assignment succeeds with `overloaded: true`; 403 for a faculty caller | 007, 028 |
| TEST-28 | Valid 12-attendee group session with 2 action items (201; each present attendee's `meetings_this_term` +1). Session validation: a non-mentee attendee; future date; individual with 2 attendees; action item for a non-attendee; force a failure after the Session node is created (fault injection) | 422 `NOT_YOUR_MENTEE`; 422 field error; 422; 422; nothing persisted (node counts unchanged) | 008 |
| TEST-29 | Confirm as a present attendee (twice); as an absent attendee; a session 8 days old left unconfirmed | 200 with `confirmed_at` set and unchanged on repeat; 409 `NOT_PRESENT`; the mentor's row shows `unconfirmed_sessions: 1` | 009 |
| TEST-30 | Action items: due yesterday + open → overdue; mentee `done`; mentee `verified`; mentor `verified`; mentor `done → open` | overdue true; 200; 403; 200; 200 | 010 |
| TEST-31 | Issue resolve with an empty resolution; with text | 422; 200 with `resolved_at` set; HOD resolved count +1 | 011 |
| TEST-32 | API-033 as HOD and as IQAC on a fresh seed vs hand-computed values from seed JSON (a script computes the expected values independently, in Python, from `seed/*.json`) | students 50, allotted 48, compliance per mentor equal; Vikram < 100%; others 100%; the IQAC response contains no student names | 016 |
| TEST-33 | API-024 for Meera on a fresh seed | 13 assigned rows; exactly 3 `needs_attention`, with the reason sets defined in backend §10 | 012 |
| TEST-34 | Move an application pending → shortlisted → accepted; read `history` | 3 StatusEvents with actor names and ascending `at` | 018 |
| TEST-35 | Logging a session creates `session_logged` for present attendees only; API-038 marks read and the unread count drops | Correct recipients; unread −1 | 038 |
| TEST-36 (P1) | API-039 for Meera and for the mentee of an overdue item | Both contain `action_overdue` with the item's `ref_id` | 023 |
| TEST-37 (P1) | For each metric, API-034 `total` equals the API-033 number; IQAC rows contain no `name` or `roll_no` | Equal; pseudonyms only | 019 |
| TEST-38 (P1) | Escalate an issue; HOD reads it and resolves it; HOD gets `issue_escalated` | 200s; notification present | 022 |
| TEST-39 | API-016 as Meera returns only applicants; API-003 as Meera for a non-applicant, non-mentee student | No non-applicants; 404 | 005, NG-11 |
| TEST-42 | After Meera logs a session for Aarav with 2 mentee action items: API-029 as Aarav | `assigned_mentor.name` = "Dr. Meera Raman"; 1 item in `sessions_to_confirm`; 2 open `action_items`; applications listed with status | 014 |
| TEST-58 | Each persona logs in via API-001, then calls API-002 | 200 with the correct `role`; the token works on a role route | 031 |
| TEST-59 | Meera approves one `needs_review` certificate and rejects another with "Name differs"; Aarav reads both via API-006 | Approved → `certified` and the skill becomes trust 1; rejected → `rejected` with `review_reason` visible to Aarav; both create `certificate_result` notifications; Arjun calling API-010 gets 404 | 002 |
| TEST-43 | API-025 as Meera for Aarav, and as the HOD | `skills`, `academics`, `sessions`, `action_items`, `applications` non-empty; `notes` only on sessions Meera logged; HOD response has no `notes` | 013 |

### 2.5 P1 and P2 feature tests (run only for features built)
| ID | Case | Expected | REQ |
|---|---|---|---|
| TEST-44 (P1) | API-045 as Aarav; API-031 as Aarav about self | Meera gets `meeting_request` and `issue_raised_by_mentee`; the issue appears in API-025 for Meera | 024 |
| TEST-45 (P2) | API-041 by Meera (guide of Aarav after accept) for "pytorch"; by Arjun | 201 with the student profile: trust_level 2 and `endorsed_by` showing the faculty **name** ("Dr. Meera Raman"); 404 for Arjun, 403 for HOD / student / IQAC, 404 for a skill the student does not list. Realised in `tests/test_endorsements.py` | 027 |
| TEST-46 (P2) | Seed mentee with 68% attendance; API-043 `marked_at_risk: true` on another | Row reasons include `suggested_at_risk` and `marked_at_risk` respectively | 029 |
| TEST-47 (P1) | API-014 valid; 4-character title; 11 skills | 201 and visible in API-012 with fit; 422; 422 | 030 |
| TEST-48 (P2) | API-025 `term_summary` for Aarav | Each number equals the count derived from the same response's lists | 032 |
| TEST-49 (P2) | Tag 3 mentees `slow` via API-043 → API-035 | Summary sheet shows "Slow learners identified: 3"; `learner_note` text absent from the export | 033 |
| TEST-56 (P2) | API-042 twice by Aarav; once by an absent attendee | Second replaces first, visible only in the author's API-027; 409 `NOT_PRESENT` | 034 |
| TEST-57 (P2) | API-044 for Meera | 4 count fields; schema has no rating fields | 035 |

### 2.4 Non-functional
| ID | Case | Expected | NFR |
|---|---|---|---|
| TEST-40 | 5 sequential calls each to API-012, 015, 024, 033 on the demo laptop; take p95 (max of 5) | < 2000 ms each | NFR-01 |
| TEST-41 | Time API-005 → terminal status: cached file ×5; one live call ×3 (only with a key) | Cached ≤ 2 s; live ≤ 20 s | NFR-02 |
| TEST-50 | Manual stopwatch: a teammate who hasn't used SCR-08 logs a 12-attendee group session with 2 action items | ≤ 120 s | NFR-03 |
| TEST-51 | Lighthouse a11y on SCR-02, 03, 06, 08, 11; keyboard-only primary flow; 360 px check on SCR-05, 06 | ≥ 90; completable; no horizontal scroll | NFR-05, 06 |
| TEST-52 | Network off, `LLM_PROVIDER=none`, fresh seed: run PRD §8 end to end | All 10 steps succeed | NFR-04 |
| TEST-53 | Clean clone → compose up → seed (images cached), timed | ≤ 5 min total; seed ≤ 60 s | NFR-08, 10 |
| TEST-54 (P1) | Playwright `e2e/primary-flow.spec.ts`: 4 browser contexts (Aarav, Meera, Suresh, Kavya) executing PRD §8 | Passes headless | all P0 in §8 |

### 2.6 Edge-case inputs
| ID | Case | Expected | Covers |
|---|---|---|---|
| TEST-61 | Timezone: a session dated 2026-10-10 created at 00:30 IST (19:00 UTC on the 9th); an action due today | The session counts for 10 Oct in `meetings_this_term` and `last_session_date`; the action is not overdue until 11 Oct IST (architecture §5) | FM-15 |
| TEST-62 | Locale: holder name "Aarav  Menon." vs profile "Aarav Menon"; "AARAV MENON"; "Āarav Menon" (diacritic) | All pass `name_ok` after normalisation (lower-case, NFKD accent strip, punctuation and space collapse) | FM-16 |
| TEST-63 | Malformed and empty files: a truncated PNG with valid magic bytes; a 0-byte file; a PDF with 0 pages | Truncated → `failed` (`extraction_failed`), no crash; 0-byte → 415; 0-page PDF → 422 | FM-17 |

## 3. Coverage rule

Every AC- maps to at least one TEST- (the matrix in §6). Every P0 row must be filled; a blank cell is a gap. At the core freeze, `pytest -q` must be green, and TEST-50, 51 and 52 must be done and recorded in `docs/plan/qa-log.md` (the date, who ran it, and the result).

## 4. Failure modes

| ID | Failure | Detection | Behaviour | User sees | Test |
|---|---|---|---|---|---|
| FM-01 | Anthropic timeout, outage or refusal | SDK exception / `stop_reason` | `failed` → manual entry | "We couldn't read this file automatically…" | TEST-14 |
| FM-02 | API restarts mid-JOB-01 | JOB-02 at startup | `processing` > 60 s → `failed` / `interrupted` | Manual-entry option | Manual: kill the backend during an upload |
| FM-03 | Neo4j down or starting | `ServiceUnavailable` | 503 `DB_UNAVAILABLE`; health shows `neo4j: down` | "Service is starting, try again in a moment." | Manual: stop neo4j |
| FM-04 | Double-click "Save session" or a network retry | Same Idempotency-Key | Second request returns the first 201 body | One session, one toast | TEST-28 variant |
| FM-05 | Two faculty move the same application concurrently | Status re-read inside the write tx | Second gets 409 `INVALID_TRANSITION` | "This application changed. Refreshing." | TEST-23 |
| FM-06 | A failure partway through session creation | Exception inside `run_write` | Whole tx rolled back | 500 or 422; nothing saved | TEST-28 |
| FM-07 | Token expires during the demo | 401 `TOKEN_EXPIRED` | Redirect to login with a banner | "Session expired, please log in again." | TEST-11 + manual |
| FM-08 | Embedding model missing offline | Startup load fails | API refuses to start with a log line naming `HF_HOME` | Health check fails before the demo | TEST-53 offline variant |
| FM-09 | Duplicate apply race (two tabs) | MERGE + check in one tx | One 201, one 409 | "You have already applied." | TEST-23 |
| FM-10 | HOD re-allots a student while their mentor is logging a session | Attendee check inside the session tx | Session fails 422 `NOT_YOUR_MENTEE` for that student | Field error on that attendee | TEST-28 variant |
| FM-11 | Polling exceeds 30 s | Client timer | Stop polling; the notification arrives later | "Still working. We'll notify you." | Manual (stub delay 35 s) |
| FM-12 | Daily LLM cap reached | Counter ≥ `MAX_LLM_CALLS_PER_DAY` | No call; `failed` | Manual-entry form | Unit test on the adapter |
| FM-13 | XLSX generation error | Exception in the export | 500 `INTERNAL` with request_id; no partial file | Error toast | Manual |
| FM-14 | Huge input: a 40-attendee session; 10 action items; 1000-character issue text | Limits from SessionCreate | Accepted at the limit; one over → 422 field error | Field error | TEST-28 variant |
| FM-15 | Timezone boundary around midnight IST | All calendar dates computed in Asia/Kolkata | Counts and overdue flags use the IST date | Correct dates | TEST-61 |
| FM-16 | Locale: diacritics, extra spaces or case in printed names | Normalisation before fuzzy match | No false `name_mismatch` | Correct status | TEST-62 |
| FM-17 | Corrupt, empty or 0-page files | Pillow / pypdfium2 errors caught in JOB-01; size and page checks at intake | `failed`, 415 or 422 | Matching copy (ux-flows §4.2) | TEST-63 |
| FM-18 | Out-of-order calls: confirm before the session exists; transition on a stale status; polling after a terminal status | 404; 409 `INVALID_TRANSITION`; the poll returns the terminal status unchanged | Refresh and toast | TEST-23, TEST-29 |

## 5. Manual QA checklist (core freeze and demo eve)

- [ ] Fresh seed. Log in as all 4 personas in separate browser profiles.
- [ ] PRD §8 steps 1–10, each with its REQ ticked, twice in a row without errors.
- [ ] SCR-02, 03, 06, 08, 11 at 360 px and at 1280 px.
- [ ] Keyboard-only FLOW-07 within 120 s (TEST-50).
- [ ] Stop the backend: every page shows `ErrorState`, not a blank screen.
- [ ] Both exports open in Excel / LibreOffice; README!A1 shows the DRAFT notice; search for note text finds nothing.
- [ ] `LLM_PROVIDER=none` and network off: demo uploads give the TEST-13 statuses.
- [ ] `git ls-files | grep -E "\.env$|uploads/"` is empty; `gitleaks detect` is clean.
- [ ] The backup video is recorded and saved locally.

## 6. Traceability matrix (AC → realisation → test)

Layers: U = unit, I = API integration, E = end-to-end or manual. Status: all `planned` until built; update it in this table at each gate.

| REQ | Tier | AC → TEST (layer) | Realised by |
|---|---|---|---|
| 031 | P0 | .1 → TEST-58 (I), §5 (E); .2 → TEST-11 (I); .3 → TEST-03 (I), §5 (E) | API-001, 002; SCR-01 |
| 001 | P0 | .1 → TEST-13 (I); .2 → TEST-12 (I); .3 → TEST-12 (I) | API-005..007; JOB-01; MDL-01; SCR-04; ENT-05 |
| 002 | P0 | .1 → TEST-13 (I); .2 → TEST-13 (I); .3 → TEST-59 (I); .4 → TEST-05 (I) | API-009..011; SCR-10; ai-system §3 |
| 037 | P0 | .1 → TEST-14 (I); .2 → TEST-14 (I) | API-008; SCR-04 |
| 003 | P0 | .1 → TEST-13 + TEST-19 (I); .2 → TEST-15 (I) | ENT-16; backend §6.2 |
| 004 | P0 | .1 → TEST-19 (I); .2 → TEST-18 (U); .3 → TEST-18 (U); .4 → TEST-18 (U) | API-012, 013, 015; MDL-02, 03; SCR-02, 03 |
| 005 | P0 | .1 → TEST-22 (I); .2 → TEST-05 (I) | API-016; SCR-09 |
| 006 | P0 | .1 → TEST-23 (I); .2 → TEST-23 (I); .3 → TEST-23 + TEST-42 (I); .4 → TEST-04 (I) | API-017..019; ENT-17, 18; SCR-03, 09 |
| 007 | P0 | .1 → TEST-27 (I); .2 → TEST-27 (I); .3 → TEST-27 (I) | API-022, 023; SCR-12 |
| 008 | P0 | .1 → TEST-28 (I); .2 → TEST-28 (I); .3 → TEST-28 (I) | API-026, 027; ENT-09, 19; SCR-08 |
| 009 | P0 | .1 → TEST-29 (I); .2 → TEST-29 (I); .3 → TEST-29 (I) | API-028; SCR-05 |
| 010 | P0 | .1 → TEST-30 (I); .2 → TEST-30 (I); .3 → TEST-30 (I) | API-026, 030; ENT-10; SCR-05, 07 |
| 011 | P0 | .1 → TEST-31 (I); .2 → TEST-31 (I) | API-026, 031, 032; ENT-11; SCR-07 |
| 012 | P0 | .1 → TEST-33 (I) | API-024; SCR-06 |
| 013 | P0 | .1 → TEST-43 (I) | API-025; SCR-07 |
| 014 | P0 | .1 → TEST-42 (I) | API-029; SCR-05 |
| 015 | P0 | .1 → TEST-20 (I); .2 → TEST-20 (I); .3 → TEST-21 (I) | API-025, 027, 035; security §4 |
| 016 | P0 | .1 → TEST-32 (I); .2 → TEST-32 (I) | API-033; MET-01..10; SCR-11 |
| 017 | P0 | .1 → TEST-21 (I); .2 → TEST-08 (I) | API-035, 036; SCR-11 |
| 018 | P0 | .1 → TEST-34 (I) | ENT-14; all status endpoints |
| 038 | P0 | .1 → TEST-35 (I) | API-037, 038; ENT-12; SCR-14 |
| 019 | P1 | .1 → TEST-37 (I) | API-034; SCR-13 |
| 020 | P1 | .1 → TEST-24 (I) | API-020; SCR-03 |
| 021 | P1 | .1 → TEST-25 (I) | API-021; SCR-02 |
| 022 | P1 | .1 → TEST-38 (I) | API-032, 033; SCR-07, 11 |
| 023 | P1 | .1 → TEST-36 (I) | API-039; SCR-14 |
| 024 | P1 | .1 → TEST-44 (I) | API-031, 045; SCR-05 |
| 025 | P1 | .1 → TEST-17 (I) | JOB-01; ai-system §3 rule 6 |
| 026 | P1 | .1 → EVAL-03 (script) | `scripts.eval_match` |
| 030 | P1 | .1 → TEST-47 (I) | API-014; SCR-15 |
| 036 | P1 | .1 → TEST-26 (I) | API-026, 032; SCR-07, 08 |
| 027 | P2 | .1 → TEST-45 (I) | API-041; SCR-07 |
| 028 | P2 | .1 → TEST-27 extended (I) | API-023, 025; SCR-12 |
| 029 | P2 | .1 → TEST-46 (I) | API-024, 043; SCR-06, 07 |
| 032 | P2 | .1 → TEST-48 (I) | API-025; SCR-07 |
| 033 | P2 | .1 → TEST-49 (I) | API-043, 035; SCR-07 |
| 034 | P2 | .1 → TEST-56 (I) | API-042; SCR-05 |
| 035 | P2 | .1 → TEST-57 (I) | API-044; SCR-16 |

NFRs: NFR-01 → TEST-40; NFR-02 → TEST-41; NFR-03 → TEST-50; NFR-04 → TEST-52; NFR-05/06 → TEST-51; NFR-07 → TEST-12; NFR-08/10 → TEST-53; NFR-09 → provider usage log (ai-system §7). AI evals: EVAL-01..04 (ai-system §10).

## 7. Execution, flaky tests, definition of done

- **Runtime targets:** the full `pytest -q` run < 3 min (seeded once per session); unit tests alone < 10 s (`pytest -q tests/test_scorer.py tests/test_verification.py`); Playwright < 2 min.
- **Flaky-test policy:** no automatic retries. A test that fails intermittently is fixed by its file owner within the current phase, or skipped with `@pytest.mark.skip(reason="flaky: status.md bug #n")` plus a bug row. A P0 test may not stay skipped past G3.
- **AI gating:** EVAL-02 and EVAL-04 run inside pytest (deterministic and cached). EVAL-01 runs on demand because it costs money; any prompt or model change re-runs EVAL-01 and EVAL-04 (ai-system §10).
- **Definition of done for a feature:** its ACs pass via the TEST- IDs in §6; tests are added; ruff, frontend lint and `tsc --noEmit` are green; the owning spec doc is updated if behaviour changed; `pip-audit` / `npm audit` report no new high findings; `check_ownership.py` passes.
- **Coverage:** a risk guide only, never a goal. Aim for every branch of `ml/scorer.py`, `ml/verification.py`, the backend §6.3/§6.4/§6.6 rule code and the security deps to be exercised; there is no global percentage target.

## Verify

Run `docker compose exec -e TODAY_OVERRIDE=2026-10-10 backend pytest -q`: all P0 tests pass (TEST-01..16, 18..23, 27..35, 39, 42, 43). Then complete §5 and record the result in `docs/plan/qa-log.md`.
