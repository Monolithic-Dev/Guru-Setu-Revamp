# Phase 1: Foundation (1:00–4:00)
Purpose:      Build the secure API skeleton under `/api/v1` (auth, access checks, errors), load the full synthetic dataset, and give every role a working login and shell. The build is from scratch (D-1).
Audience:     P1–P4.
Depends on:   phase-0-setup.md (G0 passed); architecture §5, §8 (ADR-03), §9; backend §2–§5, §6.3, §8, §10; security §2–§5; ai-system §5; ux-flows §2, §4, §7, §8
Status:       Draft v1

## 1. Goal and exit gate

**Goal:** by 4:00 the system is safe to build on. The security tests pass, every request goes through the auth/deps/error stack, the seed builds the whole demo world, and each persona logs in to its own shell.

**G1 gate (on `main`, one machine, `TODAY_OVERRIDE=2026-10-10`):**
- [ ] `pytest -q tests/test_security.py -k "test_01 or test_02 or test_03 or test_04 or test_11"` is green (TEST-01, 02, 03, 04, 11 against the routes that exist)
- [ ] `pytest -q tests/test_applications.py` is green (TEST-23, apply and transitions)
- [ ] `python -m scripts.seed --reset` takes ≤ 60 s; `MATCH (s:Student) RETURN count(s)` = 50; Meera has 13 active assigned mentees; 12 openings; ≥ 40 sessions
- [ ] Every Student and Opening has a 384-d `embedding`, and `SIMILAR_TO (deep learning)–(computer vision)` has score 0.70
- [ ] UI: `aarav@`, `meera@`, `suresh@` and `kavya@demo.gurusetu` each log in and land on their role home with the right nav; a garbage token in localStorage redirects to `/login?expired=1`
- [ ] `ls backend/app/api/v1` shows only files named in architecture §9; none of the routes in ADR-03 exist (TEST-02)

## 2. Task board

| ID | Owner | Est | Depends on | Task |
|---|---|---|---|---|
| T1.P2.1 | P2 | 0:30 | T0.P2.1 | Password and token helpers (`core/security.py`) and the ADR-03 negative test |
| T1.P2.2 | P2 | 0:40 | T1.P2.1 | Core: repository, errors, logging middleware |
| T1.P2.3 | P2 | 0:50 | T1.P2.2 | Auth and access deps; API-001/002 |
| T1.P2.4 | P2 | 0:30 | T1.P2.2 | Notify + status history services; API-037/038 |
| T1.P2.5 | P2 | 0:30 | T1.P2.3, T1.P2.4 | Applications state machine (API-017/018/019); profile (API-003/004) |
| T1.P1.1 | P1 | 0:45 | T0.P1.1 | MDL-02 embedding module and text builders |
| T1.P1.2 | P1 | 0:45 | T1.P1.1 | Concept normalisation and SIMILAR_TO builder (MDL-04) |
| T1.P1.3 | P1 | 1:00 | T0.P1.1 | Extraction contract: schema, prompt, adapter skeleton with cache and switch |
| T1.P1.4 | P1 | 0:30 | T1.P1.2, T1.P4.2 | Seed hooks: embeddings + SIMILAR_TO in `seed.py`; IDF query helper |
| T1.P3.1 | P3 | 0:30 | T0.P3.1 | Single API client + problem parsing + 401 handling |
| T1.P3.2 | P3 | 1:00 | T1.P3.1 | AuthGuard, AppShell, role layouts |
| T1.P3.3 | P3 | 0:20 | T1.P3.2 | SCR-01 Login (FLOW-01) |
| T1.P3.4 | P3 | 0:50 | T1.P3.2 | Shared components + `useApi` + toasts |
| T1.P3.5 | P3 | 0:20 | T1.P3.2 | Route stubs for every P0 SCR, with fixtures |
| T1.P4.1 | P4 | 1:30 | T0.P4.1 | Seed content meeting backend §10 exactly |
| T1.P4.2 | P4 | 1:00 | T1.P4.1 | `scripts/seed.py` full loader with `--anchor-date` |
| T1.P4.3 | P4 | 0:30 | T0.P4.1 | Certificate images (seed + demo uploads + planted) and label CSVs |

## 3. Task details

### T1.P2.1 Security helpers and the ADR-03 negative test (0:30)
- **Spec:** ADR-03, SEC-02, SEC-03, A-21, NG-01, NG-02, NG-10
- **Files:** `core/security.py`, `tests/test_security.py` (TEST-02 case)
- **Steps:**
  1. `hash_password(plain)` and `verify_password(plain, hashed)` using `bcrypt` directly with cost 12. Reject passwords longer than 72 bytes (bcrypt's limit). `create_token(sub, role)` and `decode_token(token)` using `PyJWT`, HS256, with `JWT_SECRET_KEY` and `JWT_EXPIRE_MINUTES`.
  2. A fixed dummy bcrypt hash constant, used by login to equalise timing for unknown emails (SEC-20, T1.P2.3).
  3. Write TEST-02 exactly as in test-strategy: POST `/auth/register`, `/auth/verify-identity`, `/auth/reset-password`, `/users/upload-profile-picture` and GET `/dashboard/student/home`, `/recommend/recommendations/student/openings` return 404 each. They pass trivially now and guard against someone adding them later.
- **Done when:** a unit test hashes and verifies a password, rejects a 73-byte password, and round-trips a token; TEST-02 passes.

### T1.P2.2 Core: repository, errors, logging (0:40)
- **Spec:** CMP-12, architecture §5, backend §3.1, §11, SEC-15, SEC-21
- **Files:** `core/database.py`, `core/errors.py`, `core/middleware.py`, `tests/conftest.py` (`main.py` already imports these from T0.P2.1 and is not edited)
- **First (10 min):** write `tests/conftest.py`: the `fresh_seed` session fixture (runs `scripts.seed --reset` with `TODAY_OVERRIDE=2026-10-10`) and persona token fixtures `aarav`, `meera`, `arjun`, `suresh`, `kavya`. Push it alone so others can write tests against it. Nobody else edits `conftest.py`; extra fixtures live in each owner's own test files.
- **Steps:**
  1. `database.py`: one driver created at startup (never verify connectivity per request; that was audit M4 in the old prototype); `run_read(fn, **params)` and `run_write(fn, **params)` wrap `session.execute_read/write`; `ServiceUnavailable` becomes `ApiError("DB_UNAVAILABLE", 503)`.
  2. `errors.py`: `ApiError(code, status, detail, errors=None)` plus handlers that return `application/problem+json` with `type`, `title`, `status`, `detail`, `instance`, `code` and `request_id`. Pydantic `RequestValidationError` becomes 422 `VALIDATION_FAILED` with `errors[]`. The generic `Exception` handler returns 500 `INTERNAL` and never wraps `HTTPException` (audit H5).
  3. Middleware: take or generate `X-Request-ID` and echo it back; set `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer` and `X-Frame-Options: DENY`; log one JSON line per request with method, route template, status, latency_ms, user_id and request_id. No bodies and no headers (SEC-15).
  4. CORS from `CORS_ORIGINS` (SEC-12).
- **Done when:** a request to an unknown route returns problem+json 404 with `request_id`, and the log line contains no `Authorization`.

### T1.P2.3 Auth and access deps; API-001/002 (0:50)
- **Spec:** security §2–§4, SEC-03, 04, 05, 11, 20; backend §4 (API-001, 002)
- **Files:** `core/security.py`, `api/deps.py`, `api/v1/auth.py`, `schemas/auth.py`, `repos/users_repo.py`
- **Steps:**
  1. JWT `{sub, role, iat, exp}` HS256, `exp = now + JWT_EXPIRE_MINUTES`. Decode errors give 401 `UNAUTHENTICATED`; an expired token gives 401 `TOKEN_EXPIRED`.
  2. `current_user`: decode the token, re-read the user by `user_id`, and take the role from the database (a missing user gives 401). It returns a small `CurrentUser(user_id, name, role, dept_code)`.
  3. `require_role(*roles)` raises 403 `FORBIDDEN`.
  4. Scope helpers. Each takes a `tx` and raises 404 `NOT_FOUND` when the check fails, and each is a single Cypher `EXISTS` query: `assert_self_or_scope(user, student_id, allow=…)`, `assert_mentor_of(f, s, type=None)`, `assert_owner_of_opening(f, o)`, `assert_applicant_of_own(f, s)`, `assert_dept_hod(h, s)`.
  5. API-001: look the user up by lower-cased email. If not found, verify against a fixed dummy bcrypt hash anyway (SEC-20), then return the same 401 `INVALID_CREDENTIALS`. In-memory rate limit of 10/min per client IP (a dict of deques; one worker, A-13), returning 429 with `Retry-After`. The response is `TokenResponse`.
  6. API-002 returns `Me`. Every response uses an explicit `response_model` (SEC-01).
- **Done when:** TEST-03 and TEST-11 pass for the routes that exist, plus a unit test for each scope helper with seed IDs (Meera is the mentor of Aarav, Arjun is not).

### T1.P2.4 Notify and status history; API-037/038 (0:30)
- **Spec:** CMP-11, backend §6.9, ENT-12, ENT-14, REQ-018, REQ-038
- **Files:** `services/notify.py`, `services/status_history.py`, `api/v1/notifications.py`, `repos/notifications_repo.py`
- **Steps:**
  1. `notify(tx, user_id, type, title, body=None, link)` creates a `Notification` and `NOTIFIES`. Titles follow the templates in backend §6.9. Never put note or issue text in them.
  2. `record_status(tx, entity_type, entity_id, from_status, to_status, actor, note=None)` creates a `StatusEvent`.
  3. API-037: cursor = base64 of `created_at|id`, newest first, with `unread` count. API-038 returns 204, or 404 if the notification isn't the caller's.
- **Done when:** a unit test creates two notifications in one transaction, reads them via API-037, marks one read, and sees `unread` drop by 1.

### T1.P2.5 Applications and profile (0:30)
- **Spec:** backend §6.3 (transition table), §6.2 (claimed skills), REQ-006, REQ-004, REQ-003; API-003, 004, 017, 018, 019
- **Files:** `api/v1/applications.py`, `api/v1/students.py`, `services/applications.py`, `repos/applications_repo.py`, `repos/students_repo.py`
- **Steps:**
  1. Encode the transition table as a dict, `ALLOWED = {"pending": {"shortlisted","rejected"}, "shortlisted": {"accepted","rejected"}, "accepted": {"completed"}}`.
  2. In API-018, inside one write tx: re-read the status, check the caller is the owner (404 otherwise), check the transition (409), update, record the status, and notify. On `accepted`, MERGE the guide `MENTORS`; on `completed`, end it.
  3. API-017 checks, in order: 404, `OPENING_CLOSED`, `ALREADY_APPLIED`, using `MERGE` with `ON CREATE`. Notify the owner.
  4. API-004 PATCH: only the provided fields change. `claimed_skills` is the full list of claimed names. For removed names set `claimed=false`, then call `recompute_skill` (backend §6.2; full trust logic lands in T2.P1.4, here only the trust 0 / delete branch). The embedding is recomputed via P1's function.
  5. API-003 scope: self, `mentor_of`, `applicant_of_own`, or HOD of the department.
- **Done when:** TEST-23 passes (every table cell, double apply, closed opening, guide link on accept).

### T1.P1.1 MDL-02 embedding module (0:45)
- **Spec:** ai-system §5, MDL-02
- **Files:** `ml/embedding.py`, `repos/ml_repo.py` (the Cypher behind `recompute_*`; `ml/` holds no Cypher)
- **Steps:**
  1. Load once at startup from `EMBEDDING_MODEL`, with `HF_HOME` set. If loading fails, the API refuses to start with a log line naming `HF_HOME` (FM-08).
  2. `embed(texts) -> list[list[float]]` (normalised); `student_text(profile)` and `opening_text(opening)` exactly per ai-system §5.
  3. `recompute_student_embedding(tx, student_id)` and `recompute_opening_embedding(tx, opening_id)` read, build, embed and write.
- **Done when:** a unit test checks that `len(embed(["x"])[0]) == 384` and that cosine(student_text(Aarav), opening_text(op-edge-ai)) > 0.3.

### T1.P1.2 Concepts and SIMILAR_TO (0:45)
- **Spec:** MDL-04, ai-system §3 (skill linking), §5
- **Files:** `ml/concepts.py`, `repos/ml_repo.py` (the Cypher behind `get_or_create_concept` and `rebuild_similarity`)
- **Steps:**
  1. `normalise(name)`: lower-case, trim, collapse spaces, then map through `seed/aliases.json`.
  2. `get_or_create_concept(tx, name, source)`: on creation, embed the name and compute its top-5 neighbours with cosine ≥ `SIM_MIN` → `SIMILAR_TO {score, source:'model'}`.
  3. `rebuild_similarity(tx)` for the seed: all pairs, top 5 per concept, then apply `similar_overrides.json` (`source:'override'`, overrides win). Store each pair once with the alphabetically smaller name first.
- **Done when:** after the seed, `MATCH (:Concept {name:'deep learning'})-[r:SIMILAR_TO]-(:Concept {name:'computer vision'}) RETURN r.score` returns 0.7.

### T1.P1.3 Extraction contract and adapter skeleton (1:00)
- **Spec:** ai-system §2.1–§2.4, §8, ENT-15
- **Files:** `ml/schemas/certificate_extraction.schema.json`, `ml/prompts/extract_certificate_v1.md`, `ml/extraction.py`
- **Steps:**
  1. Write the schema and prompt verbatim from ai-system §2.2 and §2.3.
  2. Add a Pydantic `Extraction` model with the post-validation rules from ai-system §2.2.
  3. `extract(file_bytes, media_type) -> Extraction | ExtractionFailed(reason)`, in this order:
     - SHA-256 cache lookup in `EXTRACTION_CACHE_DIR`; a hit returns `source="cache"`;
     - if `LLM_PROVIDER=none`, return failed;
     - check the daily `Counter` cap;
     - otherwise call the provider, stubbed in this task to raise `NotImplementedError`.
  4. Expose `set_adapter_for_tests(fn)` for the dependency override used by TEST-14 and TEST-16.
- **Done when:** a unit test with a hand-written cache file returns `source="cache"`, a miss with `none` returns failed, and the cap returns failed.

### T1.P1.4 Seed hooks (0:30)
- **Spec:** backend §10 (steps 4–5), ai-system §4 (IDF)
- **Steps:**
  1. Provide `ml/seed_hooks.py::seed_embeddings(tx)` (all Students and Openings) and `ml/concepts.py::rebuild_similarity(tx)`, with stubs pushed by 2:00 (parallel-work §4). **P4 adds the calls in `seed.py`; P1 never edits `seed.py`.** Also commit `seed/fit_tuning.json` as `{}` (P1-owned text overrides, applied by `seed.py` before embeddings).
  2. Write `repos/match_repo.py::idf_table(tx)`, which returns `{concept: idf}` over open openings. The scorer uses it in Phase 3.
- **Done when:** the G1 embedding and SIMILAR_TO checks pass.

### T1.P3.1 API client (0:30)
- **Spec:** ux-flows §8, FLOW-01 failure branch
- **Files:** `src/lib/api.ts`, `src/lib/problem.ts`
- **Steps:**
  1. One axios instance, `baseURL = process.env.NEXT_PUBLIC_API_BASE`.
  2. A request interceptor adds `Authorization: Bearer <token>`.
  3. The response interceptor:
     - on 401, clears `token`, `role` and `user_id` and routes to `/login?expired=1`;
     - on any problem+json, rejects with `{status, code, detail, errors, requestId}`.
  4. All screens call the API only through this client (no per-feature service modules).
- **Done when:** calling API-002 with a bad token lands on `/login?expired=1`.

### T1.P3.2 Shell, guard, layouts (1:00)
- **Spec:** ux-flows §2 (nav per role), §5 (breakpoints), architecture §9 (AuthGuard)
- **Files:** `src/components/{AppShell,AuthGuard,NotificationBell}.tsx`, `src/app/{student,faculty,coordinator}/layout.tsx`, `src/app/reviews/layout.tsx`, `src/app/notifications/layout.tsx`
- **Steps:**
  1. `AuthGuard allowedRoles` checks localStorage; no token or the wrong role redirects to `/login`.
  2. `AppShell` renders the sidebar (≥ 768 px) or bottom nav (< 768 px) with the role items from ux-flows §2, a header with name, role label, `NotificationBell` (polls API-037 `unread` every 30 s while visible) and Log out.
  3. Remove the generator's sample page and styles that the shell replaces. Do not create mock, collaboration or support pages (NG-10).
- **Done when:** each role sees exactly its nav items, and visiting another role's route redirects.

### T1.P3.3 SCR-01 Login (0:20)
- **Spec:** FLOW-01, REQ-031, ux-flows §6 validation copy
- On success, store the token, role and user_id, then route student → `/student`, faculty → `/faculty`, hod/iqac → `/coordinator`.
- Show the expired banner when `?expired=1`.
- Error copy per FLOW-01; focus the password field on a 401.
- **Done when:** AC-031.1–031.3 pass by hand for all 4 personas.

### T1.P3.4 Shared components and data hook (0:50)
- **Spec:** ux-flows §4.1, §7
- **Build in `components/ui/`:** `useApi(path)` (in `hooks/`) → `{data, error, loading, reload}`; `EmptyState`, `ErrorState` (shows `requestId`), `Skeleton`, `StatusPill`, `TrustBadge`, `SkillChip`, `AttentionBadge`, `Toast` (`role="status"`), `KpiTile` (with an optional `href` prop from the start, for A1), and a `Dialog` with a focus trap.
- **Seam stubs (push by 2:30, parallel-work §4):** `components/why/WhyGraph.tsx` and `components/mentor/RemindersPanel.tsx`, each exporting a component with its final props (`{openingId}` and `{}`) that returns `null`.
- **Done when:** a `/dev/components` page (removed in Phase 6) renders every component in every variant.

### T1.P3.5 Route stubs with fixtures (0:20)
- **Spec:** README rule 2, ux-flows §6
- Create only the P0 routes P3 owns: SCR-04, 06, 07, 08, 09, 10 (SCR-01 is real already). P1 creates SCR-03, and P4 creates SCR-02, 05, 11, 12, 14, 15 in their first frontend task (parallel-work §2). Each renders its title plus data from `src/fixtures/p3/API-0xx.json`, copied from the backend §4.1 examples or hand-written to the `openapi.yaml` schema, using the shared states.
- **Done when:** all P3-owned P0 routes render without errors for the right role.

### T1.P4.1 Seed content (1:30)
- **Spec:** backend §10 (all constraints), §6.4 (flag rules), ENT- field names, A-16
- **Must hold exactly** (TEST-32 and TEST-33 depend on it):
  - 56 users (2 staff, 4 faculty, 50 students). Allotments 13/13/12/10, with 2 unallotted.
  - Current term `2026-ODD` (offsets: start −87d, end +51d). Previous term `2026-EVEN`.
  - Meera, Arjun and Lakshmi: every assigned mentee has ≥ 2 present sessions this term. Vikram: 4 of 10 have < 2.
  - Meera's flagged mentees:
    - Karthik: last present session −60d (allotted −120d) plus an overdue action (due −3d, open);
    - Diya: an issue raised −16d, unresolved;
    - Rahul: an overdue action (due −1d).
    - No other Meera mentee meets any rule.
  - Aarav: claimed python, pytorch, deep learning. Python is certified via `aarav_python_basics.png`, which is in `certificates_index.json` as a seeded certificate.
  - 12 openings. `op-edge-ai` (Meera) requires python, pytorch, deep learning, computer vision, and has 3 pending applicants (not Aarav).
  - About 60 action items (8 overdue overall) and about 15 issues (4 unresolved). Academics for 2 terms, with 3 students under 75% attendance.
  - Issuers: NPTEL, Coursera, IEEE, Smart India Hackathon, Campus Coding Club, Amrita ACM Chapter (synthetic), with aliases.
  - Criteria `NAAC-2.3.3`, `NAAC-5.3.1`, `verified:false`.
- **Done when:** a quick Python script asserts each bullet above against the JSON before loading. Save it as `scripts/check_seed.py`; Phase 3 reuses it for TEST-32.

### T1.P4.2 Seed loader (1:00)
- **Spec:** backend §10 steps 1–5, environments §5 (anchor date)
- **Steps:**
  1. Parse `--reset` and `--anchor-date` (default 2026-10-10). Convert every `"±Nd"` offset to a date.
  2. Delete all nodes, apply the schema, and load in dependency order: departments → terms → users → concepts → issuers → criteria → openings + REQUIRES → mentorships → sessions + ATTENDED_BY → action items → issues → academics → applications.
  3. Apply `seed/fit_tuning.json` (P1-owned overrides: `{"students": {id: {bio, interests}}, "openings": {id: {description}}}`), then call P1's `seed_embeddings` and `rebuild_similarity`.
  4. Certificates are loaded in T2.P4.2, once the pipeline exists. Leave a `TODO(T2.P4.2)` hook.
  5. Print counts.
- **Done when:** the G1 seed checks pass, and a second run gives identical counts.

### T1.P4.3 Certificate images and labels (0:30) [CUT-2: 3 samples only]
- **Spec:** ai-system §10 (EVAL-01 set composition), backend §10 (demo uploads)
- **Produce in `seed/certificates/`:** 25 files (18 typical, 4 edge, 3 adversarial per EVAL-01, including `cert_injection.png`), plus `aarav_python_basics.png`.
- **Produce in `seed/demo_uploads/`:**
  - `aarav_dl_pytorch.png` (holder "Aarav Menon", NPTEL, 2026-04-15, ID `NPTEL26CS41S7701`);
  - `aarav_cv_workshop.png` (Amrita ACM Chapter, 2026-08-20);
  - `aarav_python_copy.jpg`: a phone photo or re-encode of `aarav_python_basics.png` with a slight crop, which must stay within pHash distance ≤ 6 (check it);
  - `aarav_embedded_c.png` (holder "Arav M.").
  - Also a planted EXIF-Photoshop file for REQ-025.
- `labels/certificate_labels.csv`: file, holder_name, title, issuer, issue_date, level, type, skills (pipe-separated), cache_corrected.
- **Done when:** `python -c "import imagehash,PIL.Image as I;print(imagehash.phash(I.open('…basics.png'))-imagehash.phash(I.open('…copy.jpg')))"` prints ≤ 6.

## 4. Handoffs at 4:00

| From | To | Artifact |
|---|---|---|
| P2 | P1, P3, P4 | `run_write`, deps, `notify`, `record_status` usable; `conftest.py` fixtures; API-001/002/003/004/017–019/037/038 live |
| P1 | P2, P4 | `ml/extraction.extract()` with cache; `ml/concepts.get_or_create_concept()`; `recompute_student_embedding()`; `ml/seed_hooks.seed_embeddings()`; stubs of `ml/verification.verify` and `ml/trust.*` with final signatures (by 4:15) |
| P4 | all | A seeded DB that matches backend §10; persona logins |
| P3 | P1, P4 | Shell, `components/ui/*`, the WhyGraph and RemindersPanel stubs, `lib/features.ts`, and the fixtures pattern, so P1 and P4 can build their screens in their own folders |

## 5. If behind at 3:30

- P2 drops T1.P2.4 cursor pagination: return the latest 50 and `next_cursor: null`. The schema allows null.
- P3 drops the `/dev/components` page.
- P4 loads 30 students instead of 50 only if TEST-32/33 expectations are updated in the same commit. Do this as a last resort; prefer finishing the JSON in Phase 2's buffer.
