You are **P2 (Backend, graph, security and Docker)** on a 4-person, 15-hour hackathon build of **GuruSetu**. Paste this whole brief into your coding agent, or read it as your own brief. It is self-contained: what to build, in what order, with what interfaces, what "done" means for every task, and exactly how to use git. Where it points to a document, that document has the full detail; where it states a number or a rule, the number or rule is binding.

# 1. The product and your part in it

GuruSetu (FastAPI + Neo4j 5 + Next.js 14, Docker Compose, built **from scratch**, **synthetic data only**) is a trust layer for a university department:
- Students upload certificates; an LLM extracts fields; deterministic code verifies them; verified skills drive an explained **Fit Check** for research openings (P1's part).
- Faculty mentors log **sessions** (attendance, topics, private notes, action items, issues); mentees confirm; the mentor home flags who needs attention; **Mentee 360** shows the whole timeline.
- HOD and IQAC see live compliance and export **draft** accreditation evidence containing aggregates only, never private notes.

**You own the spine:** the API skeleton, authentication and every access rule, the data layer, notifications and status history, the certificates, mentoring, tracking, metrics and export APIs, the contracts (`openapi.yaml`, `schema.cypher`), the Docker Compose stack, and most backend tests. **You are on the critical path:** P1, P3 and P4 are blocked until your seams land. A wrong access rule leaks private mentoring data, which is the product's biggest risk.

The repo is `Guru-Setu-Revamp`. The default branch is `main`.

# 2. Non-negotiable rules (from the spec)

1. **Every route has an explicit Pydantic response model.** Never return `password_hash`, `embedding` or `file_path` (SEC-01). Private fields (`notes`, issue `text`, `duplicate_of`, `learner_note`) are **omitted**, not null, when the caller may not see them.
2. **403 vs 404:** a role not listed for a route gets **403 `FORBIDDEN`**; a listed role acting outside its scope gets **404 `NOT_FOUND`** so existence never leaks. Role and scope checks live in `app/api/deps.py` (security sections 3-4).
3. **Cypher only in `backend/app/repos/` (and `scripts/seed.py`)**, always parameterised, never built from strings (SEC-17). The import rules: `api/v1` imports `deps`, `schemas`, `services`; `services` import `repos`, `ml`, other services; `ml` imports only `core` and `repos/ml_repo.py`/`match_repo.py`; `repos` import only `core.database`.
4. **Privacy:** session notes appear only for their author; issue, note, action and resolution text never appear in dashboards, exports, notifications or logs (REQ-015, SEC-15). Notification bodies never contain session notes or issue text.
5. **Every status change writes a `StatusEvent` and the listed notifications in the same transaction** as the change.
6. **Thresholds are configuration** (backend section 8), never literals. Dates: calendar dates are `YYYY-MM-DD` in Asia/Kolkata; timestamps are UTC ISO-8601 with a `Z`. "Today" honours `TODAY_OVERRIDE`.
7. **No registration, no password reset, no profile-photo upload, no `/uploads` static mount** (NG-01, NG-02, ADR-03). No DELETE routes.
8. Errors are `application/problem+json` with a stable `code` (backend section 3.1). `HTTPException` is never swallowed into a 500.
9. **Contracts are the source of truth.** Change `openapi.yaml`/`schema.cypher` first, in their own commit prefixed `CONTRACT:`, additive only (never rename or remove a field after G0), then regenerate `schemas/generated.py` and tell P3 to regenerate `types.ts`.
10. Build **P0 before P1 before P2** items. Do not build non-goals (NG-01..15). The spec pack wins over a phase doc on facts.

# 3. Read first (30 minutes, in this order)

1. `AGENTS.md`, then `CONTRIBUTING.md` (git rules binding)
2. `docs/00-index.md` (section 5 assumptions, **section 7 end-to-end scenario**)
3. `docs/01-product/prd.md` (all REQ with ACs, NFR, NG) and `docs/02-architecture/architecture.md` (ADRs, import rules, project structure)
4. `docs/04-backend/backend.md` (**governing doc**: entities, API conventions, endpoints, business rules 6.1-6.10, metrics, config, jobs, seed) + `openapi.yaml` + `schema.cypher`
5. `docs/08-security/security-and-privacy.md` (scope predicates and the field-visibility matrix in section 4; SEC-01..21)
6. `docs/10-devops/environments-and-deployment.md`, `docs/11-quality/test-strategy.md`, `docs/phases/README.md`, `parallel-work.md`, phase docs 0 to 6

# 4. Your files (single owner: you)

All of `backend/app/**` **except** P1's: `core/` (`config.py`, `database.py`, `security.py`, `errors.py`, `middleware.py`), `main.py`, `api/deps.py`, `api/v1/*` (all but `match.py`, `endorsements.py`), `schemas/` (but not `match.py`), `services/` (`notify.py`, `status_history.py`, `applications.py`, `certificates.py`, `jobs.py`, `mentorship.py`, `tracking.py`, `metrics.py`, `evidence_export.py`), `repos/` (all but `match_repo.py`, `ml_repo.py`). Also `backend/schema/`, `backend/pyproject.toml` (ruff and pytest settings), `docker-compose.yml`, `.github/`, `tools/` (except `tools/certgen/`, which is P4's), `backend/tests/` except P1's five test files (`conftest.py`, `test_security.py`, `test_applications.py`, `test_certificates.py`, `test_mentorship.py`, `test_tracking.py`, `test_metrics.py`), `docs/02-architecture/`, `04-backend/` (the contracts), `08-security/`, `10-devops/`, `11-quality/`, `docs/plan/decisions-log.md`.

Check any path: `python tools/check_ownership.py --who <path>`. **Do not edit files you do not own.** `ml/__init__.py` is P1's (call `app.ml.startup()` defensively until their stub lands).

# 5. Schedule (hours from the real start time, written in `docs/phases/status.md`)

| Phase | Hours | Your tasks | Est |
|---|---|---|---|
| 0 Setup | 0:00-1:00 | **T0.P2.0 scaffold commit (first, fast)** · T0.P2.1 compose, config, main, schema, health, generated models | 1:00 |
| 1 Foundation | 1:00-4:00 | T1.P2.1 security helpers + TEST-02 · T1.P2.2 core + `conftest.py` · T1.P2.3 auth + deps · T1.P2.4 notify + status history · T1.P2.5 applications + profile | 3:00 |
| 2 Core A | 4:00-7:00 | T2.P2.1 certificates API + JOB-01/02 · T2.P2.2 allotment · T2.P2.3 sessions · T2.P2.4 action items + issues | 3:00 |
| 3 Core B | 7:00-10:00 | T3.P2.1 needs-attention + mentor home · T3.P2.2 Mentee 360 + My mentorship · T3.P2.3 metrics + dashboard · T3.P2.4 exports · T3.P2.5 audit pass | 3:00 |
| 4 Add-on A | 10:00-12:30 | A1 API-034 (0:40) → A3 API-039 (0:30) → A4 issue lifecycle (0:40) → A7 API-045 (0:20) → A9 API-014 (0:15) | 2:25 |
| 6 Freeze | 12:30-15:00 | T6.P2.1 scans · T6.P2.2 `rc1` and submission tag · T6.P2.3 fix rota | 2:30 |

**Gates:** G0 1:00, G1 4:00, G2 7:00, **G3 core freeze 10:00**, feature freeze 12:30, code freeze 13:15. Stand-ups (5 min): 1:00, 4:00, 7:00 (30-min integration check), 10:00, 12:30. If behind at 3:30: drop cursor pagination on API-037 (return the latest 50, `next_cursor: null`).

# 6. Task details

## Phase 0
**T0.P2.0 Scaffold commit (about 20 min; the ONE allowed direct push to `main`, checkpoint C0).** Create `backend/` (FastAPI app with a stub `GET /api/v1/health`, empty packages `core`, `api/v1`, `schemas`, `services`, `repos`, `ml`, `.gitkeep` in `scripts`, `seed`, `tests`) and the frontend with `npx create-next-app@14 frontend --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --use-npm --no-git`; clear the sample page; confirm the root `.gitignore` covers `.env`, `uploads/`, `node_modules/`, `.next/`, `__pycache__/`; commit `chore: scaffold backend and frontend`; push to `main`. Then tell everyone to branch. (This is already done on `main` if you are reading this after hour 0; check `git log`.)

**T0.P2.1 Compose, config, app entry, schema, generated models (45 min)**
1. `core/config.py` with pydantic-settings fields for **every** variable in backend section 8 and `docs/10-devops/env.example`. At startup raise a clear error if `len(JWT_SECRET_KEY) < 32` or `len(NEO4J_PASSWORD) < 12` (SEC-10), and if `LLM_PROVIDER=anthropic` with no `ANTHROPIC_API_KEY`. Treat an empty `TODAY_OVERRIDE` as unset; warn at startup when it is set.
2. `main.py`, written **once in final form**: router auto-discovery (import every module in `app/api/v1/` that has a `router`, include under `/api/v1`); a lifespan that waits for Neo4j, applies `schema.cypher` idempotently (split on `;`, run each statement), then calls `app.ml.startup()` (P1; tolerate it being absent) and `app.services.jobs.startup()` (your stub, filled with JOB-02 in Phase 2); the middleware and error handlers live in `core/` modules that `main.py` imports, so `main.py` never changes again.
3. Copy `docs/04-backend/schema.cypher` to `backend/schema/schema.cypher`.
4. `api/v1/health.py` (API-040): `RETURN 1` on Neo4j → `{"status":"ok","neo4j":"up","llm_provider":...}`; 503 on failure.
5. Generate `schemas/generated.py`: `datamodel-codegen --input docs/04-backend/openapi.yaml --input-file-type openapi --output backend/app/schemas/generated.py --output-model-type pydantic_v2.BaseModel` (this file is GEN: never hand-edit).
6. `docker-compose.yml` per environments section 2 (neo4j `5.26-community` with healthcheck; backend depends on healthy neo4j; frontend depends on healthy backend; volumes `neo4j_data`, `uploads`; `env_file: .env`; ports bound to 127.0.0.1). `backend/pyproject.toml` with ruff and pytest settings.
7. Do not create a root `.env.example`: the one template is `docs/10-devops/env.example`.
**Done when** the G0 health check passes on your machine and on one teammate's after `git pull`.

## Phase 1 (by 4:00)
**T1.P2.1 Security helpers + ADR-03 negative test (0:30)**: `core/security.py`: `hash_password`/`verify_password` with `bcrypt` directly (cost 12; reject passwords over 72 bytes), `create_token(sub, role)`/`decode_token` with `PyJWT` HS256 (`{sub, role, iat, exp}`), and a fixed dummy hash for timing equalisation. TEST-02: POST `/auth/register`, `/auth/verify-identity`, `/auth/reset-password`, `/users/upload-profile-picture` and GET `/dashboard/student/home`, `/recommend/recommendations/student/openings` all return 404. **Done when** hash/verify/73-byte rejection/token round-trip tests pass.

**T1.P2.2 Core (0:40)**: **first (10 min)** write `tests/conftest.py`: the `fresh_seed` session fixture (runs `scripts.seed --reset` with `TODAY_OVERRIDE=2026-10-10`) and persona token fixtures `aarav`, `meera`, `arjun`, `suresh`, `kavya`; push it alone so others can write tests. Then `core/database.py` (one driver at startup; `run_read(fn, **params)`/`run_write(fn, **params)` wrapping `session.execute_read/write`; `ServiceUnavailable` → `ApiError("DB_UNAVAILABLE", 503)`), `core/errors.py` (`ApiError(code, status, detail, errors=None)` plus handlers returning problem+json with `type, title, status, detail, instance, code, request_id`; `RequestValidationError` → 422 `VALIDATION_FAILED` with `errors[]`; generic exception → 500 `INTERNAL`, never wrapping `HTTPException`), `core/middleware.py` (`X-Request-ID`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `X-Frame-Options: DENY`; one JSON log line per request with method, route template, status, latency_ms, user_id, request_id; **no bodies, no headers**), CORS from `CORS_ORIGINS`. **Done when** an unknown route returns problem+json 404 with `request_id`, and the log line has no `Authorization`.

**T1.P2.3 Auth and access deps; API-001/002 (0:50)**: JWT as above; decode errors → 401 `UNAUTHENTICATED`, expired → 401 `TOKEN_EXPIRED`. `current_user` decodes, **re-reads the user by `user_id`, and takes the role from the database** (missing user → 401), returning `CurrentUser(user_id, name, role, dept_code)`. `require_role(*roles)` → 403 `FORBIDDEN`. Scope helpers (each takes a `tx`, raises 404 `NOT_FOUND` on failure, and is one Cypher `EXISTS` query in a repo): `assert_self_or_scope`, `assert_mentor_of(f, s, type=None)`, `assert_owner_of_opening`, `assert_applicant_of_own`, `assert_dept_hod`. API-001: look up by lower-cased email; if absent, still verify against the dummy hash (SEC-20); the same 401 `INVALID_CREDENTIALS` for unknown email and wrong password; in-memory rate limit 10/min per IP (a dict of deques; one worker) returning 429 with `Retry-After`. API-002 returns `Me`. **Done when** TEST-03 and TEST-11 pass plus a unit test per scope helper with seed ids (Meera is the mentor of Aarav, Arjun is not).

**T1.P2.4 Notify and status history; API-037/038 (0:30)**: `notify(tx, user_id, type, title, body=None, link)` creates a `Notification`+`NOTIFIES` (titles from the backend section 6.9 templates; **never** note or issue text). `record_status(tx, entity_type, entity_id, from_status, to_status, actor, note=None)` creates a `StatusEvent`. API-037: cursor = base64 of `created_at|id`, newest first, with `unread` count. API-038: 204, or 404 if not the caller's. **Done when** a unit test creates two notifications in one transaction, reads them via API-037, marks one read, and `unread` drops by 1.

**T1.P2.5 Applications and profile (0:30)**: `ALLOWED = {"pending": {"shortlisted","rejected"}, "shortlisted": {"accepted","rejected"}, "accepted": {"completed"}}`. API-018 in one write tx: re-read status, owner check (404), transition check (409 `INVALID_TRANSITION`), update, `record_status`, notify the student (`application_status`); on `accepted` MERGE the guide `MENTORS {type:'guide', opening_id, status:'active', since: today}`; on `completed` end it (`end_reason:'completed'`). API-017 checks in order: 404, `OPENING_CLOSED`, `ALREADY_APPLIED` (use `MERGE ... ON CREATE`); notify the owner (`application_received`). API-004 PATCH changes only provided fields; `claimed_skills` is the full list; removed names set `claimed=false` then call P1's `recompute_skill`; recompute the embedding via P1. API-003 scope: self, `mentor_of`, `applicant_of_own`, or the HOD of the department. **Done when** TEST-23 passes (every transition cell, double apply, closed opening, guide link on accept).

**Handoff at 4:00 (what P1, P3, P4 get from you):** `run_write`, deps, `notify`, `record_status` usable; `conftest.py` fixtures; API-001/002/003/004/017-019/037/038 live.

## Phase 2 (by 7:00)
**T2.P2.1 Certificates API and jobs (1:00)**: API-005 upload intake: stream to a temp file counting bytes (over `MAX_UPLOAD_MB` → 413 `FILE_TOO_LARGE`); check magic bytes (`FF D8 FF`, `89 50 4E 47 0D 0A 1A 0A`, `25 50 44 46 2D`, else 415 `UNSUPPORTED_FILE_TYPE`); PDFs over 5 pages → 422; store as `UPLOAD_DIR/<uuid>.<ext>`; create `Evidence{status:'processing', sha256, ...}`+`SUBMITTED`; schedule JOB-01 with `BackgroundTasks`; return 202; rate-limit 20/hour/user (429). JOB-01: re-read the Evidence and exit if not `processing`; `extract()` → `verify()` (P1's interface); one write tx: set fields, status, confidence, reasons, source; if certified call `apply_certified`; `record_status`; notify (`certificate_result` to the student; `review_needed` to the assigned mentor when `needs_review`); any exception → `failed`. JOB-02 in `services/jobs.py::startup()`: `processing` older than 60 s → `failed` (`interrupted`). API-006/007 (student scope; omit `duplicate_of` for students). API-008 (only from `failed`; `source:'manual'`, confidence = min(computed, 0.50), reason `manual_entry`, → `needs_review`). API-009/010 (faculty sees assigned mentees; HOD the department; review only from `needs_review`, else 409 `ALREADY_REVIEWED`; reject needs a reason of 3-300 chars; approve → `apply_certified`). API-011 `FileResponse` with `X-Content-Type-Options: nosniff` and `Content-Disposition: inline`. **Done when** TEST-06, 12, 13, 14 and the certificate cases of TEST-05 pass.

**T2.P2.2 Allotment (0:25)**: API-022/023 exactly per backend section 6.8 in one write tx per request (handover of an existing assigned link to a different mentor, no-op if already the target, create, notify `allotted`, `record_status`). API-022 returns mentor loads with `overloaded` (> `MENTOR_LOAD_WARN`) and the unallotted list. **Done when** TEST-27 passes.

**T2.P2.3 Sessions (1:00)**: `SessionCreate` mirrors the openapi schema plus: date ≤ today and within the current or previous term; `individual` → exactly 1 attendee; `guide` → `opening_id` required; follow-up after the date; action/issue students ⊆ attendees; due ≥ date. **Idempotency:** same `Idempotency-Key` + user within 24 h returns the stored `SessionDetail` with 201. **One write tx:** every attendee needs an active `MENTORS` link of the right type (422 `NOT_YOUR_MENTEE`, naming the attendee); create Session, `LOGGED`, `ATTENDED_BY{present}`, ActionItems (`open`)+`CREATED`+`FOR`, Issues (`raised`)+`RAISED`+`ABOUT`; `record_status` for each created item; notify `session_logged` (present attendees) and `action_assigned` (per mentee-owned item); store the IdempotencyKey; any failure rolls everything back. API-027 shaping: `notes` only for the author; students see only their own attendee row; **role check first (HOD → 403), then scope (other faculty → 404)**. API-028: attendee only (404), `present=false` → 409 `NOT_PRESENT`, idempotent `confirmed_at`. **Done when** TEST-20, 28, 29 pass including the fault-injection rollback.

**T2.P2.4 Action items and issues (0:35)**: API-030 transition table keyed by role relation (mentee: `open → done`; author mentor: `done → verified`, `open|done → dropped`, `done → open`; else 409; role not allowed 403); `overdue` computed in the response; `record_status`. Issues (P0 subset): API-031 by faculty with `mentor_of`; API-032 only `raised → resolved` with a resolution of 1-1000 chars; the other statuses, `escalated` and `confidential` return 409 `INVALID_TRANSITION` until add-on A4. **Done when** TEST-30 and TEST-31 pass.

## Phase 3 (by 10:00)
**T3.P2.1 Needs-attention + mentor home (0:50)**: `services/tracking.py`, `repos/tracking_repo.py`, `api/v1/tracking.py`. One read query: active `MENTORS` from the caller, per student the sessions by this mentor (date, context, present, confirmed_at), action items from this mentor's sessions, visible issues, latest academics. Evaluate backend section 6.4 in Python with config thresholds (`ATTENTION_NO_SESSION_DAYS` 45, `ISSUE_STALE_DAYS` 14, `SESSION_CONFIRM_DAYS` 7, `MIN_MEETINGS_PER_TERM` 2) and the term from `CURRENT_TERM_ID` or today's date. Sort: flagged first, then by number of reasons, then name. **Done when** TEST-33 passes: 13 rows, exactly Karthik, Diya and Rahul flagged with the seeded reasons.

**T3.P2.2 Mentee 360 + My mentorship (0:40)**: API-025 (scope `mentor_of` or the HOD of the department): profile, mentorships, academics (`[MOCK]`), sessions (notes only on the caller's own), action items, issues (apply the section 4 text rules), applications, certificates, `attention_reasons`; each action item, issue and application carries a `history` from StatusEvents; `term_summary: null`. API-029: assigned mentor, guides, the earliest future `next_followup`, `sessions_to_confirm`, up to 20 recent sessions, own action items, own issues (text hidden for mentor-raised confidential ones), applications. **Done when** TEST-42 and TEST-43 pass and TEST-20 still passes.

**T3.P2.3 Metrics + dashboard (0:40)**: `services/metrics.py`, `repos/metrics_repo.py`, `api/v1/dept.py`. MET-01..10 exactly as defined (department of the caller, current term, assigned context; confidential issues grouped as `"confidential"`). `needs_attention_list` for the HOD only (reuse T3.P2.1); IQAC gets `needs_attention_count` and **no names anywhere**. **Done when** TEST-32 passes; P4's `scripts/check_seed.py` computes the expected values independently and they equal API-033.

**T3.P2.4 Exports (0:30)**: openpyxl; sheets and columns exactly per backend section 7. `README!A1` reads "DRAFT – verify against the official NAAC manual before submission". `safe(v)` prefixes `'` to strings starting with `= + - @` (SEC-18). `StreamingResponse` with `Content-Disposition: attachment; filename="gurusetu-mentoring-<term>-DRAFT.xlsx"`. Build rows from metric functions only; never read `notes`, `Issue.text`, `ActionItem.text` or `resolution`. **Done when** TEST-08 and TEST-21 pass.

**T3.P2.5 Audit pass (0:20)**: trigger each P0 notification type once and check recipient and title (section 6.9); check every status-changing endpoint writes a StatusEvent (TEST-34).

## Phase 4 add-ons (only if G3 passed; each merges only with TEST-xx green and the scenario still passing)
A1 API-034 (refactor so each metric's count and rows come from one function; rows never contain text; IQAC gets stable `Student 01…` pseudonyms; cursor pagination; `total` equals the dashboard number) · A3 API-039 (4 reminder kinds from section 6.10) · A4 issue lifecycle (`raised → acknowledged → in_progress → resolved`; `escalated: true` from any unresolved state, irreversible; escalation notifies the HOD; confidential filtering; a confidential issue cannot be escalated, 409 "Confidential issues cannot be escalated"; fill `escalated_issues` in API-033) · A7 API-045 and the student path of API-031 · A9 API-014 in `api/v1/openings_write.py`. Cut order if short: skip A9 and A7 first.

## Phase 6
T6.P2.1: `gitleaks detect` (0 findings), `pip-audit -r backend/requirements.txt`, `npm --prefix frontend audit --audit-level=high` (note: the generated Next.js 14 app may report vulnerabilities; fix or list each in security section 9), `git ls-files | grep -E "(^|/)\.env$|uploads/"` empty, rerun TEST-01..12. T6.P2.2: at 13:15 propose `rc1` and run the full `pytest -q` on a fresh seed; after rehearsal 2 propose the `genesis-submission` tag on the exact commit used in the video (**the lead pushes tags after merging**); update the README status line. T6.P2.3: backend bug fixes, each re-tested.

# 7. Seams you owe (final signatures, on time)

`core/database.py`, `api/deps.py`, `core/errors.py` by **2:00** (P1 imports them) · `services/notify.py` and `status_history.py` by **2:30** · `conftest.py` by about 2:00 · stable contracts after G0. You depend on: P1's `ml/` stubs (1:00-2:00, `verify`/`apply_certified` interface by 4:15) and P4's seed loader (4:00). Until a stub lands, code against the agreed signature.

# 8. Git workflow (binding; the full text is `CONTRIBUTING.md`)

- Work **only** on `feature/p2-backend-core`, created from the latest `main` once the scaffold is there (the scaffold is your one direct push). Set once: `git config pull.rebase true`.
- **Never push to `main` after the scaffold. Never merge a PR.** Open a PR **only when the lead announces a checkpoint** (C1 about 2:30, G1, G2, G3, freeze, final) or when your whole work is done. Title `P2 <checkpoint>: <summary>`, fill in `.github/pull_request_template.md`, tag the lead, then **stop**. The lead merges with "Rebase and merge", so every commit lands as written.
- Small, working commits: `T2.P2.3 REQ-008: add session idempotency`. No merge commits, no "wip". Contract changes are their own `CONTRACT:` commit; GEN outputs are their own commit.
- Daily loop: `git fetch origin && git rebase origin/main` → work → `python tools/check_ownership.py P2` (must print `ok`) → tests (`docker compose exec -e TODAY_OVERRIDE=2026-10-10 backend pytest -q <files>`) → `git push --force-with-lease origin feature/p2-backend-core`.
- After the lead merges one of your PRs: `git fetch origin && git rebase origin/main`, push with `--force-with-lease`, keep working on the **same** branch.
- A rebase conflict in a file you do not own means **stop and ask**. Update only your own rows in `docs/phases/status.md` (separate small commit). Never commit `.env`, uploads or real data.

# 9. Definition of done (per task)

The task's **Done when** passes; its TEST- cases exist and are green; `ruff check backend` and `npx @stoplight/spectral-cli lint docs/04-backend/openapi.yaml` are clean; `check_ownership.py` prints `ok`; your `status.md` row is updated. After each merge by the lead, `docker compose up -d --build` and `docker compose exec backend python -m scripts.seed --reset` must still work, and index section 7 must still run.

# 10. If you fall behind

Order of cuts: add-ons A9, A7, A4 detail, then P1-tier items; keep security, the session log, action items, mentor home, the HOD dashboard and exports. If P4's seed is late, use a minimal seed fixture to unblock your tests. If Phase 1 overruns (it has no slack), say so at the 4:00 stand-up and apply the cut order at the 7:00 integration check, not at 9:30.

# 11. Your first 60 minutes

1. Read section 3 (30 min). 2. T0.P2.0 scaffold to `main` (or confirm it is there), tell everyone to branch. 3. `git checkout -b feature/p2-backend-core`. 4. T0.P2.1. 5. Run `python tools/check_ownership.py --who backend/app/main.py` (prints `P2`). 6. Post any blocker in the team chat within the hour.
