# Project Structure and Setup: GuruSetu Verified Mentorship Graph
Purpose:      One page that shows what the finished repo looks like, who owns each part, how data flows end to end, and what must be set up by hand (keys, accounts, database).
Audience:     The team and coding agents.
Depends on:   docs/00-index.md, architecture.md §9, parallel-work.md, backend.md §8, environments-and-deployment.md
Status:       Draft v1. Facts come from the spec pack, read on 2026-10-10. Nothing here was run: `backend/` and `frontend/` do not exist yet.

## 1. State of the repo today

| Part | Exists now | Created when |
|---|---|---|
| `docs/` spec pack, `AGENTS.md`, `CLAUDE.md`, `README.md`, `LICENSE`, `tools/` | Yes | — |
| `backend/`, `frontend/` | **No** | Hour 0: P2 scaffolds both from scratch (scaffold commit, [phase-0 T0.P2.0](phases/phase-0-setup.md)) |
| `docker-compose.yml` | **No** | Phase 0, P2 (T0.P2.1) |
| `docs/general/` | Empty | — |

**Build mode: from scratch** (A-05, decision D-1). The old GuruSetu repos are not needed, and no old code is copied. Phase 1 writes auth, core and the app shell instead of repairing them (about +2 h across P2 and P3 [I]).

## 2. Target tree (deep)

Legend: `[P1..P4]` = owner from `tools/ownership.txt` · `T<phase>.<person>.<n>` = the task that first creates it · `(GEN)` = generated, never hand-edited · `†` = not named in the other docs; added here to close a gap (see §2.8) · `(add-on)` = only if that add-on is built · `(stretch)` = Phase 5 only.

### 2.1 Root

```
Guru-Setu-Revamp/
├─ README.md                      [P4]  What it is, quick start, demo logins, disclosure
├─ AGENTS.md                      [P4]  Agent entry: commands, boundaries, traps (56 lines)
├─ CLAUDE.md                      [P4]  One line: @AGENTS.md
├─ CONTRIBUTING.md                [P4]  Branch, PR and rebase-merge workflow, checkpoints
├─ LICENSE                        [P2]  Apache-2.0
├─ .gitignore                     [P2]  .env, uploads/, caches, node_modules, .next (extraction_cache/ and seed/ are committed)
├─ .spectral.yaml                 [P2]  OpenAPI lint rules (`spectral lint docs/04-backend/openapi.yaml`)
├─ docker-compose.yml             [P2 · T0.P2.1]  neo4j + backend + frontend, healthchecks, volumes
├─ .github/
│  └─ pull_request_template.md    [P2]  Checkpoint PR template
├─ docs/                          see §2.2
├─ tools/                         see §2.7
├─ backend/                       see §2.3
└─ frontend/                      see §2.4
```

No root `.env.example`: the only template is `docs/10-devops/env.example`, copied to a gitignored `.env`.

### 2.2 docs/ (the specification pack and the build plan)

```
docs/
├─ 00-index.md                    Entry point: document map, ID registry, assumptions, VERIFY list, end-to-end scenario (§7)
├─ project-structure.md           This file
├─ 01-product/prd.md              Goals, roles, REQ/AC/NFR/NG, primary flow, metrics, risks, mocks
├─ 02-architecture/architecture.md  Components (CMP), stack, ADRs, quality strategy, project structure, import rules
├─ 04-backend/
│  ├─ backend.md                  Data model (ENT), API conventions and endpoints (API), business rules, jobs (JOB), metrics (MET), config, seed
│  ├─ openapi.yaml                Contract, source of truth for routes and schemas (45 x-id entries)
│  └─ schema.cypher               Contract, source of truth for graph labels, constraints, indexes
├─ 05-frontend/ux-flows.md        IA, flows (FLOW), screens (SCR-01..16), components, client state
├─ 06-ai/ai-system.md             Extraction, verification and confidence, fit formula, embeddings, safety, eval plan (MDL, EVAL)
├─ 08-security/security-and-privacy.md  Auth, visibility matrix, SEC and THR items
├─ 10-devops/
│  ├─ environments-and-deployment.md  Quickstart, environments, compose, release, backups, demo runbook
│  └─ env.example                 Every environment variable (the single template)
├─ 11-quality/test-strategy.md    Test cases (TEST), failure modes (FM), manual QA, traceability matrix
├─ plan/
│  ├─ prd-v2-and-15h-plan.md      Team plan overview, demo story, disclosure, pitch material
│  ├─ decisions-log.md            [P2]  Created at hour 0: answers to D-1..D-6
│  ├─ eval-results.md             [P1]  Created when first measured; numbers only, feeds the deck
│  └─ qa-log.md                   [P4]  Created at the first rehearsal; TEST-52 and rehearsal results
└─ phases/
   ├─ README.md                   Phases, gates, task IDs, working rules
   ├─ phase-0-setup.md … phase-6-freeze-demo.md   Tasks per person (seven files)
   ├─ parallel-work.md            Ownership, seams, git workflow
   ├─ status.md                   Live status board (all may edit their own rows)
   └─ prompts/                    README.md + p1-ml-fit.md, p2-backend-core.md, p3-frontend-mentor.md, p4-seed-coordinator.md
```

Numbering gaps (`03`, `07`, `09`, `12`) are deliberate: those domains are merged or skipped (index §3). The empty local folder `docs/general/` and the empty `docs/.gitignore` serve no purpose and can be deleted.

### 2.3 backend/ (FastAPI, Python 3.12)

```
backend/
├─ Dockerfile                     [P1 · T0.P1.1]  python:3.12-slim; CPU torch first; MiniLM baked into /models; CMD uvicorn app.main:app --workers 1
├─ .dockerignore †                [P1 · T0.P1.1]  tests/, __pycache__, .env, uploads/ out of the image
├─ requirements.txt               [P1 · T0.P1.1]  Every backend dependency pinned once (fastapi, neo4j, bcrypt, PyJWT, sentence-transformers, anthropic, Pillow, imagehash, pypdfium2, rapidfuzz, openpyxl; dev: pytest, httpx, ruff, datamodel-code-generator, pip-audit)
├─ pyproject.toml †               [P2 · T0.P2.1]  ruff and pytest settings only (no packaging)
├─ schema/
│  └─ schema.cypher               [P2 · T0.P2.1]  Copy of docs/04-backend/schema.cypher; applied idempotently at API startup
│
├─ app/
│  ├─ __init__.py
│  ├─ main.py                     [P2 · T0.P2.1]  Imports every module in api/v1 and includes its `router` under /api/v1; lifespan: apply schema, ml.startup(), jobs.startup()
│  │
│  ├─ core/                       Cross-cutting, no business rules
│  │  ├─ config.py                [P2 · T0.P2.1]  pydantic-settings; every variable of backend §8; refuses to start on a weak secret
│  │  ├─ database.py              [P2 · T1.P2.2]  One driver; run_read / run_write; ServiceUnavailable → 503 DB_UNAVAILABLE
│  │  ├─ security.py              [P2 · T1.P2.1]  bcrypt (cost 12) and PyJWT HS256 helpers; dummy hash for timing
│  │  ├─ errors.py                [P2 · T1.P2.2]  ApiError and problem+json handlers
│  │  └─ middleware.py            [P2 · T1.P2.2]  X-Request-ID, security headers, JSON access log (no bodies, no headers)
│  │
│  ├─ api/
│  │  ├─ deps.py                  [P2 · T1.P2.3]  current_user, require_role, scope helpers (403 vs 404 rules)
│  │  └─ v1/                      One router per area; prefix /api/v1
│  │     ├─ health.py             [P2 · T0.P2.1]  API-040
│  │     ├─ auth.py               [P2 · T1.P2.3]  API-001 login, API-002 me
│  │     ├─ students.py           [P2 · T1.P2.5]  API-003 profile, API-004 patch
│  │     ├─ applications.py       [P2 · T1.P2.5]  API-017..019 apply, decide, my applications
│  │     ├─ notifications.py      [P2 · T1.P2.4]  API-037, 038
│  │     ├─ certificates.py       [P2 · T2.P2.1]  API-005..011 upload, status, file, review
│  │     ├─ mentorship.py         [P2 · T2.P2.2-4] allotment 022/023, sessions 026-028, actions 030, issues 031/032, 045
│  │     ├─ tracking.py           [P2 · T3.P2.1-2] mentor home 024, Mentee 360 025, My mentorship 029, 039
│  │     ├─ dept.py               [P2 · T3.P2.3]  dashboard 033, drill-down 034
│  │     ├─ evidence.py           [P2 · T3.P2.4]  exports 035, 036
│  │     ├─ match.py              [P1 · T3.P1.2]  fit and candidates: 012, 013, 015, 016 (add-on: 020, 021)
│  │     ├─ openings_write.py     [P2 · A9] (add-on)  API-014 create opening
│  │     └─ endorsements.py       [P1] (stretch)  API-041
│  │
│  ├─ schemas/
│  │  ├─ generated.py             [GEN]  datamodel-codegen from openapi.yaml; never hand-edited
│  │  ├─ auth.py                  [P2 · T1.P2.3]  Thin wrappers where the generated model is not enough
│  │  └─ match.py                 [P1]  Fit wrappers if needed
│  │
│  ├─ services/                   Business rules and transactions (call repos and ml, never write Cypher)
│  │  ├─ notify.py                [P2 · T1.P2.4]  notify(tx, ...) titles never contain note or issue text
│  │  ├─ status_history.py        [P2 · T1.P2.4]  record_status(tx, ...) → StatusEvent
│  │  ├─ applications.py          [P2 · T1.P2.5]  Transition table, apply checks, guide link on accept
│  │  ├─ certificates.py          [P2 · T2.P2.1]  Upload intake and JOB-01 pipeline glue
│  │  ├─ jobs.py                  [P2 · T0.P2.1 / T2.P2.1]  startup hook, JOB-02 stale-processing sweep
│  │  ├─ mentorship.py            [P2 · T2.P2.2-4]  Allotment, sessions, idempotency, actions, issues
│  │  ├─ tracking.py              [P2 · T3.P2.1]  Needs-attention rules
│  │  ├─ metrics.py               [P2 · T3.P2.3]  MET-01..12
│  │  └─ evidence_export.py       [P2 · T3.P2.4]  XLSX with README!A1 "DRAFT", aggregates only
│  │
│  ├─ repos/                      ALL Cypher, always parameterised
│  │  ├─ users_repo.py            [P2 · T1.P2.3]
│  │  ├─ students_repo.py         [P2 · T1.P2.5]
│  │  ├─ applications_repo.py     [P2 · T1.P2.5]
│  │  ├─ notifications_repo.py    [P2 · T1.P2.4]
│  │  ├─ certificates_repo.py     [P2 · T2.P2.1]
│  │  ├─ mentorship_repo.py       [P2 · T2.P2.2]
│  │  ├─ tracking_repo.py         [P2 · T3.P2.1]
│  │  ├─ metrics_repo.py          [P2 · T3.P2.3]
│  │  ├─ match_repo.py            [P1 · T1.P1.4]  Fit read query, IDF table
│  │  └─ ml_repo.py               [P1 · T1.P1.1]  Cypher for embeddings, concepts, trust, duplicate lookups (ml/ has none)
│  │
│  └─ ml/                         [P1]  Models and deterministic scoring; imports only core and ml_repo/match_repo
│     ├─ __init__.py              [P1 · T0.P1.1]  startup(): load the embedding model once
│     ├─ embedding.py             [P1 · T1.P1.1]  MDL-02 MiniLM, text builders, recompute_*
│     ├─ concepts.py              [P1 · T1.P1.2]  normalise, get_or_create_concept, rebuild_similarity (MDL-04)
│     ├─ seed_hooks.py            [P1 · T1.P1.4]  seed_embeddings(tx)
│     ├─ extraction.py            [P1 · T1.P1.3 / T2.P1.1]  MDL-01 adapter: cache → LLM → schema check; LLM_PROVIDER=none switch
│     ├─ verification.py          [P1 · T2.P1.2]  Duplicate, name, issuer, date checks; confidence; routing
│     ├─ trust.py                 [P1 · T2.P1.4]  apply_certified, recompute_skill
│     ├─ scorer.py                [P1 · T3.P1.1]  MDL-03 fit formula; components sum to the score
│     ├─ prompts/extract_certificate_v1.md          [P1 · T1.P1.3]
│     └─ schemas/certificate_extraction.schema.json [P1 · T1.P1.3]  Structured-output contract
│
├─ scripts/
│  ├─ seed.py                     [P4 · T0.P4.1 / T1.P4.2]  --reset, --anchor-date; calls P1 hooks
│  ├─ check_seed.py               [P4 · T1.P4.2]  Verifies the seed against backend §10 numbers
│  ├─ build_extraction_cache.py   [P1 · T2.P1.3]  One JSON per seed and demo file (needs a key, or hand-written)
│  ├─ eval_match.py               [P1 · A6]  nDCG@10 and P@5 vs the keyword baseline (EVAL-03)
│  └─ eval_extraction.py          [P1 · T2.P1.3]  Field accuracy on the labelled set (EVAL-01)
│
├─ seed/                          [P4]  Synthetic data, all [MOCK], dates as offsets from 2026-10-10
│  ├─ users.json  departments.json  terms.json  openings.json  concepts.json
│  ├─ issuers.json  mentorships.json  sessions.json  action_items.json  issues.json  academics.json
│  ├─ certificates_index.json     Maps each seed certificate to its student and expected status
│  ├─ aliases.json  similar_overrides.json  fit_tuning.json     [P1] tuning files inside seed/
│  ├─ certificates/               25 files: 18 typical, 4 edge, 3 adversarial (including cert_injection.png) + aarav_python_basics.png
│  ├─ demo_uploads/               aarav_dl_pytorch.png, aarav_cv_workshop.png, aarav_python_copy.jpg (duplicate), aarav_embedded_c.png (name mismatch)
│  └─ labels/                     certificate_labels.csv (EVAL-01), match_labels.csv (EVAL-03)
│
├─ extraction_cache/              [P1]  <sha256>.json per seed and demo file; committed so the demo runs offline
│
└─ tests/                         pytest against the compose Neo4j, reseeded once per session
   ├─ conftest.py                 [P2 · T1.P2.2]  fresh_seed fixture; persona tokens aarav, meera, arjun, suresh, kavya
   ├─ test_security.py            [P2]  Auth, roles, scope, privacy, headers (test-strategy §2.1)
   ├─ test_applications.py        [P2]  Apply and state machine (TEST-23)
   ├─ test_certificates.py        [P2]  Upload, statuses, review
   ├─ test_mentorship.py          [P2]  Allotment, sessions, actions, issues
   ├─ test_tracking.py            [P2]  Needs-attention rules (e.g. TEST-33)
   ├─ test_metrics.py             [P2]  Dashboard and exports (e.g. TEST-32)
   ├─ test_verification.py        [P1]  Checks and confidence
   ├─ test_extraction.py          [P1]  Adapter, cache, refusal, injection
   ├─ test_embedding.py           [P1]  384-d, normalisation
   ├─ test_scorer.py              [P1]  TEST-18 (43.4 and 68.5)
   └─ test_matching.py            [P1]  TEST-19, 22, 39
```

### 2.4 frontend/ (Next.js 14, TypeScript, Tailwind)

```
frontend/
├─ Dockerfile                     [P3 · T0.P3.1]  node:20-alpine; build arg NEXT_PUBLIC_API_BASE; next build then next start -p 3000
├─ .dockerignore †                [P3 · T0.P3.1]  node_modules, .next, e2e results
├─ package.json + lockfile        [P3 · T0.P3.1]  Every dependency added once (recharts, react-force-graph-2d, openapi-typescript, @playwright/test); scripts: gen:types, e2e, lint
├─ next.config.js  tailwind.config.ts  postcss.config.js  tsconfig.json  .eslintrc.json   [P3]  Produced by create-next-app in T0.P2.0
├─ e2e/
│  ├─ primary-flow.spec.ts        [P3 · T6.P3.2] (optional)  Index §7 smoke
│  └─ playwright.config.ts †      [P3 · T6.P3.2]
└─ src/
   ├─ app/                        App Router; one folder per route in ux-flows §6
   │  ├─ layout.tsx  page.tsx †  globals.css   [P3]  Root layout; `/` redirects by role
   │  ├─ login/page.tsx                         [P3 · T1.P3.3]  SCR-01
   │  ├─ student/
   │  │  ├─ layout.tsx                          [P3 · T1.P3.2]
   │  │  ├─ page.tsx                            [P4 · T3.P4.2]  SCR-02 home
   │  │  ├─ openings/[id]/page.tsx              [P1 · T3.P1.4]  SCR-03 Fit Check
   │  │  ├─ certificates/page.tsx               [P3 · T2.P3.1]  SCR-04
   │  │  └─ mentorship/page.tsx                 [P4 · T2.P4.4]  SCR-05
   │  ├─ faculty/
   │  │  ├─ layout.tsx                          [P3]
   │  │  ├─ page.tsx                            [P3 · T3.P3.1]  SCR-06 mentor home
   │  │  ├─ mentees/[studentId]/page.tsx        [P3 · T3.P3.2]  SCR-07 Mentee 360
   │  │  ├─ sessions/new/page.tsx               [P3 · T2.P3.3]  SCR-08
   │  │  ├─ openings/page.tsx                   [P4 · T3.P4.3]  SCR-15
   │  │  ├─ openings/[id]/page.tsx              [P3 · T3.P3.3]  SCR-09
   │  │  └─ openings/new/page.tsx               [P3 · A9] (add-on)
   │  ├─ reviews/{layout.tsx,page.tsx}          [P3 · T2.P3.2]  SCR-10
   │  ├─ coordinator/
   │  │  ├─ layout.tsx                          [P3]
   │  │  ├─ page.tsx                            [P4 · T3.P4.1]  SCR-11
   │  │  ├─ allotment/page.tsx                  [P4 · T2.P4.3]  SCR-12
   │  │  └─ metrics/[metric]/page.tsx           [P4 · A1] (add-on)  SCR-13
   │  ├─ notifications/{layout.tsx,page.tsx}    [layout P3, page P4 · T3.P4.3]  SCR-14
   │  ├─ faculty-profile/[id]/page.tsx          [P4] (stretch)  SCR-16
   │  └─ dev/components/page.tsx                [P3 · T1.P3.4]  Component gallery; removed in Phase 6
   ├─ components/
   │  ├─ AppShell.tsx  AuthGuard.tsx  NotificationBell.tsx   [P3 · T1.P3.2]
   │  ├─ ui/                      [P3 · T1.P3.4]  EmptyState, ErrorState (shows requestId), Skeleton, StatusPill, TrustBadge, SkillChip, AttentionBadge, Toast, KpiTile (optional href), Dialog (focus trap), Timeline, ExportButton
   │  ├─ mentor/                  [P3 · T2-T3]  SessionForm, AttendeePicker, TopicChips, ActionItemEditor/List, IssueList, MenteeRow, ReviewCard, RemindersPanel (add-on; stub returns null)
   │  ├─ why/WhyGraph.tsx         [P3 · A2] (add-on; stub returns null)
   │  ├─ fit/                     [P1 · T3.P1.4]  FitScoreRing, ScoreBreakdownBar, FitPanel, SkillGapCard (add-on)
   │  ├─ certificates/ †          [P3 · T2.P3.1]  CertificateUploader, CertificateCard, ManualCertificateForm
   │  ├─ student/                 [P4]  Home and mentorship widgets
   │  └─ coordinator/             [P4]  MentorTable, charts (recharts), exports panel
   ├─ lib/
   │  ├─ api.ts                   [P3 · T1.P3.1]  The only axios instance: base URL, Bearer token, 401 → /login?expired=1, problem+json parsing
   │  ├─ problem.ts               [P3 · T1.P3.1]
   │  ├─ nav.ts                   [P3 · T0.P3.1]  Every route of every role from day one
   │  ├─ features.ts              [P3 · T0.P3.1]  whyGraph, skillGap, reminders, createOpening (all false; one line per flag)
   │  └─ types.ts                 [GEN]  openapi-typescript output; never hand-edited
   ├─ hooks/useApi.ts             [P3 · T1.P3.4]  { data, error, loading, reload }
   └─ fixtures/                   Example payloads until the live endpoint lands
      ├─ p1/                      [P1]
      ├─ p3/                      [P3]  API-0xx.json
      └─ p4/                      [P4]  e.g. API-029.json
```

Note: the docs do not say where `CertificateUploader`, `CertificateCard` and `ManualCertificateForm` (SCR-04) live. They belong to the student certificate flow, and `components/student/` is P4's, so they go in a P3-owned folder: `components/certificates/` † (see §2.8).

### 2.5 Runtime layout (not in git)

| Thing | Where | Notes |
|---|---|---|
| Neo4j data | Docker volume `neo4j_data` | `docker compose down -v` wipes it |
| Uploaded certificate files | Docker volume `uploads` mounted at `/data/uploads` | Served only through API-011; never committed |
| Embedding model | Baked into the backend image at `/models` (`HF_HOME`) | No network needed at runtime |
| Extraction cache | `backend/extraction_cache/` in the image | Committed JSON |
| Secrets | `.env` at the repo root | Gitignored |
| Ports | 3000 frontend, 8000 API, 7474 and 7687 Neo4j | |

### 2.6 Import and dependency rules

```
Backend    api/v1 ──▶ deps, schemas, services
           services ──▶ repos, ml, other services
           ml ──▶ core, repos/ml_repo.py, repos/match_repo.py
           repos ──▶ core.database only
           Cypher exists only in repos/ and scripts/seed.py
Frontend   app/* pages ──▶ components, hooks, lib/api.ts (never axios directly)
           components/fit, why, mentor ──▶ components/ui
           nothing imports from another person's fixtures
```

### 2.7 tools/

```
tools/
├─ ownership.txt                  [P2]  Path → owner; the last matching line wins
├─ check_ownership.py             [P2]  `P<n>` checks the branch; `--who <path>`; `--list P<n>`
└─ certgen/                       [P4 · T0.P4.1]  HTML template → PNG certificates (Pillow or a headless browser); makes seed, demo and planted files
```

### 2.8 Gaps this pass closes

The other docs never named these, but the commands in `AGENTS.md` need them:

| Added | Why | Owner and task |
|---|---|---|
| `backend/pyproject.toml` † | `ruff check backend` and `pytest -q` need a config (line length, rule set, test paths, `TODAY_OVERRIDE` documented) | P2, T0.P2.1 |
| `backend/.dockerignore` †, `frontend/.dockerignore` † | Keep tests, caches, `.env` and `node_modules` out of images and builds | P1 and P3, T0.P1.1 and T0.P3.1 |
| `frontend/src/components/certificates/` † | A P3-owned home for `CertificateUploader`, `CertificateCard`, `ManualCertificateForm` | P3, T2.P3.1 |
| `frontend/e2e/playwright.config.ts` † | Needed by `e2e/primary-flow.spec.ts` | P3, T6.P3.2 (optional) |

Deliberately not added: CI workflows (CI/CD is skipped for this build, index §3), a `docs/03-data` folder (merged into backend.md), a root `.env.example` (single template in `docs/10-devops/`), and `CODEOWNERS` (the ownership map plus `check_ownership.py` already does this; add it only after the four GitHub usernames are known).

### 2.9 Two traces through the tree

**Certificate upload** (REQ-001, REQ-002): `student/certificates/page.tsx` → `components/certificates/CertificateUploader` → `lib/api.ts` → `api/v1/certificates.py` (API-005) → `services/certificates.py` creates the Evidence node `processing` and starts JOB-01 → `ml/extraction.py` (cache by SHA-256, else the LLM) → `ml/verification.py` (hash, name, issuer, date) → one write transaction through `repos/certificates_repo.py`, `ml/trust.py` + `repos/ml_repo.py` (skills), `services/status_history.py` and `services/notify.py` → the page polls API-006 until the final status.

**Log a session** (REQ-008): `faculty/sessions/new/page.tsx` → `components/mentor/SessionForm` + `AttendeePicker` → `api/v1/mentorship.py` (API-026) → `services/mentorship.py` (idempotency key, attendee scope check from `api/deps.py`) → `repos/mentorship_repo.py` → `status_history` and `notify` in the same transaction → mentee sees it on `student/mentorship/page.tsx` (API-029).

## 3. Who owns what (4 people, [A-01](00-index.md))

| Person | Lane | Main paths |
|---|---|---|
| **P1** | AI/ML and Fit Check | `backend/app/ml/`, `api/v1/match.py`, `repos/match_repo.py`, `repos/ml_repo.py`, requirements, Dockerfile, `extraction_cache/`, `components/fit/`, `student/openings/` |
| **P2** | Backend, graph, security | rest of `backend/app/`, compose, `docs/10-devops/env.example`, `schema/`, `tools/`, most tests |
| **P3** | Frontend shell and mentor screens | `frontend/` by default, layouts, `package.json`, UI kit, certificate, review and session screens |
| **P4** | Data, coordinator UI, pitch | `backend/seed/`, `scripts/seed.py`, coordinator and student-home screens, README, docs, deck, demo script |

The full map is `tools/ownership.txt`; the rules are in [parallel-work.md](phases/parallel-work.md).
Team size is 4 (confirmed by the team): 4 x 15 h = 60 person-hours.

## 4. How the three compulsory parts map to modules

| You asked for | Spec module | Where |
|---|---|---|
| ProofOnce | **Verify**: upload → LLM extraction → deterministic checks → Certified / review queue | `ml/extraction.py`, `ml/verification.py`, `ml/trust.py`, `services/certificates.py`, SCR-04, SCR-10 |
| GuruSetu | **Match**: explained Fit Check, apply, ranked applicants | `ml/scorer.py`, `api/v1/match.py`, SCR-03, SCR-09 |
| Mentor-mentee | **Mentor** + **Track**: allotment, sessions, action items, issues, Mentee 360 | `services/mentorship.py`, `services/tracking.py`, SCR-05..08, SCR-12 |
| (by-product) | **Evidence**: dashboards and draft XLSX with no private notes | `services/metrics.py`, `services/evidence_export.py`, SCR-11 |

## 5. End-to-end data flow

1. **Seed** (`scripts.seed --reset`): clears Neo4j, applies the schema, loads JSON, builds embeddings, and runs seed certificates through the same pipeline from cache.
2. **Upload:** student posts a file (API-005). The API stores it under `UPLOAD_DIR`, creates an Evidence node `processing`, and starts a background job (JOB-01).
3. **Extract:** the job hashes the file, checks the SHA-256 cache, and otherwise calls the Anthropic API once (vision, structured output). The LLM returns fields only.
4. **Verify:** plain code checks duplicate (hash and perceptual hash), name match, known issuer and date, and sets `certified`, `needs_review` or `rejected`. Certified evidence creates PROVES edges and recomputes skill trust.
5. **Match:** Fit Check reads the opening's required concepts and the student's skills and trust, then computes a score in Python (no LLM). Thresholds: Ready ≥ 65, Close ≥ 40 ([ai-system §4](06-ai/ai-system.md)).
6. **Mentor:** HOD allots mentors; mentors log sessions with attendance, private notes, action items, issues. Every status change writes a StatusEvent and notifications in the same transaction.
7. **Evidence:** HOD and IQAC dashboards are computed at read time; exports contain aggregates only.

## 6. Manual setup: keys, accounts, database

### 6.1 What you must provide

| Item | Needed? | What to do |
|---|---|---|
| **Anthropic API key** (`ANTHROPIC_API_KEY`) | Only if `LLM_PROVIDER=anthropic` | Create a key in the Anthropic Console, put it in `.env` (never commit). It is used for certificate extraction only. |
| `NEO4J_PASSWORD` | **Yes** | You choose it: 12+ characters. It is not an account; it protects your local database. |
| `JWT_SECRET_KEY` | **Yes** | Generate: `python -c "import secrets;print(secrets.token_urlsafe(48))"` (32+ characters; the app refuses to start otherwise) |
| Docker Desktop (Compose v2) | **Yes** | Install; on Windows it uses WSL2 or Hyper-V. Allow about 5+ GB for images. |
| Node 20 and Python 3.12 on each laptop | For running tools and tests outside Docker (`npx`, `ruff`, `ownership` checker) | Install if you will run those commands locally |
| Node 20 (for `npx create-next-app@14`) | **Yes** for the scaffold commit | Install on P2's and P3's laptops |

### 6.2 What you do NOT need
- **No database account and no manual DB creation.** Neo4j runs in Docker (`neo4j:5.26-community`). The schema is applied automatically on API startup, and `seed --reset` fills it.
- **No Cloudinary, no OpenAI key.** Both are removed (ADR-13).
- **No Hugging Face token.** The embedding model is public and is baked into the backend image at build time.
- **No hosting account**, unless the Genesis rules require a URL (then Render/Netlify/Neo4j Aura, ENV-03).

### 6.3 Manual steps in order

1. Decide D-1..D-6 and record them ([phase-0](phases/phase-0-setup.md)): reuse allowed? LLM allowed? who is P1-P4? start time?
2. P2 scaffolds `backend/` and `frontend/` and pushes the scaffold commit (about 20 min). Others pull after it.
3. Each person: `cp docs/10-devops/env.example .env`; set `NEO4J_PASSWORD`, `JWT_SECRET_KEY`, and `ANTHROPIC_API_KEY` or `LLM_PROVIDER=none`.
4. `docker compose up -d --build` (slow the first time: torch CPU wheel and model download; share the image by `docker save` if venue Wi-Fi is bad).
5. `docker compose exec backend python -m scripts.seed --reset`.
6. **Build the extraction cache once, while online with a key:** `docker compose exec backend python -m scripts.build_extraction_cache seed/certificates seed/demo_uploads`, then **commit the JSON files**. Without a key, P1 hand-writes the cache JSON (phase-0 risk table).
7. Create the synthetic certificate images (P4, `tools/certgen/`), including the duplicate and the name-mismatch files.
8. Tag the submission commit `genesis-submission`. The repo must contain no `.env`, no uploads, no real data.

## 7. Check result: flaws and fixes

**Fixed in this pass (your four items):**
1. Database queries by `ml/` conflicted with the Cypher-only-in-`repos/` rule. Added P1-owned `repos/ml_repo.py` to `tools/ownership.txt`, the architecture import rules and tree, parallel-work, and the phase 1 and 2 file lists.
2. `docs/plan/prd-v2-and-15h-plan.md` §14 had old numbers (54 → 82, 50/50). Now 38–50 → at least 65 (43.4 → 68.5 worked example) and 48 of 50 allotted, with a note to write the demo from index §7.
3. Index §7 step 6 and the phase 3 Done-when now say "13 assigned rows, 3 flagged" with guided students listed separately.
4. Links to the `Ideas/` files were removed from the plan, index and PRD header (those files are not in the repo).

**Also fixed (found while checking):** plan §14 said the HOD sees "one mentor overloaded", but the seed's highest load is 13 against a warning at 20. Now it says Vikram is highlighted for low compliance.

**Scratch-build pass (decision D-1):** the docs no longer say to copy or repair old code. Changed: index (A-02, A-05, A-21, summary lines), README and AGENTS.md (disclosure now says no code is reused), architecture (ADR-01, 03, 11, 13 and the stack table: `bcrypt` + `PyJWT`, no `passlib`), PRD constraints and NG items, security (bcrypt, SEC-14), phase 0 (T0.P2.0 is now a scaffold commit), phase 1 (T1.P2.1 is now security helpers plus the ADR-03 negative test; no "delete old code" steps), parallel-work §7-§8, status board, and a banner on the plan file. The old audit references (for example "audit H6") remain as lessons and are explained in the index.

**Still open:**
1. **Time cost of scratch.** The docs estimate about +2 h across P2 and P3 for writing auth, core and the shell instead of repairing them [I]. Phase 1 had no slack on the P2 critical path, so P2's Phase 1 may overrun; use the cut order early.
2. **Genesis rules:** whether reusing the earlier project's concept and name is allowed is unconfirmed [VERIFY]. The README has a bracketed note to confirm.
3. **Scope is large for 15 hours:** 45 endpoints, 16 screens, Neo4j with vectors, an LLM pipeline, XLSX exports. The docs' own cut order is sensible; use it early.
4. **Unchecked external facts** the docs mark [VERIFY]: Genesis rules on prior code and AI, the model ID `claude-opus-5-5` and cost, the Anthropic SDK version, the `neo4j:5.26-community` tag, the CPU torch wheel URL, and NAAC criterion codes.
5. **Vision input on stage:** the offline demo works only for files in the cache. Any new certificate needs a key and network.
6. **Resolved:** one env template only, `docs/10-devops/env.example`; every doc says `cp docs/10-devops/env.example .env` (the root `.env.example` copy was dropped). Previously: both worked after Phase 0, but pick one.

Verified mechanically: all relative Markdown links resolve, and `openapi.yaml` has 45 `x-id: API-` lines (I did not check that they are unique).

**What I read in full:** `00-index.md`, `AGENTS.md`, `README.md`, `env.example`, `environments-and-deployment.md`, `phases/README.md`, `phase-0-setup.md`, `status.md`, `parallel-work.md`, `tools/*`, and parts of `architecture.md`, `backend.md` (§8–§10) and the plan's §13–§14. The rest (`prd.md`, `ux-flows.md`, `security-and-privacy.md`, `test-strategy.md`, `ai-system.md`, phases 1–6, `openapi.yaml`, `schema.cypher`) I searched with targeted greps only, so more inconsistencies may remain there.

## Verify

1. Every relative Markdown link under `docs/`, `README.md`, `AGENTS.md` and `CONTRIBUTING.md` resolves (a ten-line script that follows each Markdown link target finds no missing file).
2. `python tools/check_ownership.py --who <path>` prints the owner named in §3 for `backend/app/ml/x.py` (P1), `backend/app/repos/ml_repo.py` (P1), `tools/certgen/x.py` (P4), `backend/app/main.py` (P2) and `frontend/src/app/login/page.tsx` (P3).
3. After the scaffold commit, `docker compose up -d --build` followed by `curl -s localhost:8000/api/v1/health` returns `{"status":"ok",...}`.
