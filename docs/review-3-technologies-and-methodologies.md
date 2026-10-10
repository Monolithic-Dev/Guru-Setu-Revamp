# GuruSetu: Review 3 (Technologies and Methodologies Used)

**The prompt:** *"Explain the technologies and methods behind your build, and how you applied them."*

**How to use this file:** it is written to be spoken to judges and mentors. **Review 2** covered *what* the stack is and *how the AI is used*; this review is about **method**: *how we worked, why the build is trustworthy, and how each technology was applied on a real feature.* **Part A** is the 90-second version. **Part B** is the technology map (short; the AI detail is in Review 2). **Part C** is the heart: eleven methods, each with *what it is, how we applied it, and the proof it is real*. **Part D** walks three features end to end and names the technology and the method at every step. **Part E** is evidence, **Part F** is honest limits, **Part G** is a short demo, **Part H** is Q&A, **Part I** is the slide outline.

Every number below comes from this repository (code, config, docs, measured results). Where something is a limit or still open, it says so.

---

# PART A: THE 90-SECOND VERSION

> **"We built GuruSetu in a way that makes it hard to get wrong. Our method has one idea: write the rules down first, then make the machine enforce them.**
>
> **Technology:** FastAPI and Neo4j behind a Next.js app, all started by one `docker compose up`. A vision model reads certificates and a small local model measures meaning, and that is the *only* AI in the product.
>
> **Methodology, in five moves:**
> **1. Contract first.** One OpenAPI file is the source of truth; the backend models and frontend types are *generated* from it, so the two sides cannot drift.
> **2. Requirements to tests.** 38 requirements, 67 acceptance criteria and 61 named test cases, traced one to the other. 284 tests run against a real Neo4j.
> **3. Rules decide, AI reads.** Anything that affects a person (trust, status, access, flags) is plain deterministic code, so every number can be explained and reproduced.
> **4. Security and privacy by design.** A threat model, 21 numbered security requirements, 403-versus-404 scoping, private text that never reaches a dashboard, an export or a model.
> **5. Parallel work without conflicts.** Four builders, every file has one owner, a script blocks edits outside your lane, and PRs merge by rebase. 110 commits, rebase-merged, linear history."**

**The three sentences to remember:**
1. **Contract first: the API spec is generated into both sides, so backend and frontend cannot disagree.**
2. **Every rule is written down, numbered, and tested; AI never decides anything that matters.**
3. **We report measured numbers only, including where our own evaluation was too weak to claim a win.**

---

# PART B: THE TECHNOLOGY MAP (SHORT)

*(Full table with versions and reasons: Review 2, Part B. This is the "which technology did which job" view.)*

| Job | Technology | The method that governs it |
|---|---|---|
| **API** | FastAPI 0.143, Pydantic 2.14, Uvicorn | Contract-first; every route has a typed response model |
| **Data** | Neo4j 5.26 Community (one database, graph + vector index) | The domain *is* relationships; "why does this fit" is a graph path |
| **Auth** | bcrypt (cost 12), PyJWT; role re-read from the database every request | Threat model, SEC-03/04/20 |
| **Frontend** | Next.js 14 (App Router), React 18, TypeScript, Tailwind, axios | Types generated from the contract; one data hook, one HTTP client |
| **AI: reading** | Groq, `qwen/qwen3.8-27b`, strict JSON schema | AI proposes, rules decide, human handles doubt |
| **AI: meaning** | sentence-transformers `all-MiniLM-L6-v2`, local, 384-d | Offline, private, explainable inside a fixed formula |
| **File safety** | Pillow, ImageHash, pypdfium2, rapidfuzz | Deterministic verification rules, in a fixed order |
| **Exports** | openpyxl | Draft-only, formula-injection safe, no private text |
| **Contracts / quality** | OpenAPI 3.1, datamodel-codegen, openapi-typescript, Spectral, pytest, ruff, ESLint, `tsc`, Playwright | Gates before every merge |
| **Packaging** | Docker Compose (3 services, health checks, ports on 127.0.0.1) | One command; demo works offline |

**The size of what was built** (measured from the repo): about **10,800 lines** of backend application code, **4,300 lines** of backend tests, **1,600 lines** of scripts (seed, evals), **8,100 lines** of frontend TypeScript, a **2,650-line** API contract (54 paths, 59 operations), and about **6,500 lines** of documentation. **21 pages** across 4 roles (student, faculty, HOD, IQAC coordinator) plus shared pages (17 designed screens, SCR-01..17).

---

# PART C: THE ELEVEN METHODS (WHAT, HOW WE APPLIED IT, PROOF)

## C1. Contract-first development

**What:** the API is designed as a document *before* any code. Here the document is `docs/04-backend/openapi.yaml` (OpenAPI 3.1).

**How we applied it:**
```
openapi.yaml ──datamodel-codegen──► backend/app/schemas/generated.py   (Pydantic models)
     │
     └────────openapi-typescript──► frontend/src/lib/types.ts          (TypeScript types)
Spectral lints the contract.   Generated files are never hand-edited.
```
- A contract change is its **own commit**, prefixed `CONTRACT:`; the generated output is another commit. **Additive only**: no field is renamed or removed, so no client breaks.
- Real example: the profiles-and-matching work added about fifteen endpoints and many fields. Editing the contract first meant the compiler and the type checker listed every place that needed to change.
- A real bug the contract caught: the health route returned 500 when the provider became `groq`, because the response enum did not include it. Fix was a one-line additive contract change plus regeneration.

**Proof:** `generated.py` (1,446 lines) and `types.ts` (3,440 lines) are machine output; Spectral lint is clean; a test scans **every GET route as every role** and fails if any response contains `password_hash`, `embedding` or `file_path`.

## C2. Requirements traceability (requirement → acceptance → test)

**What:** every behaviour has an ID, and the IDs link up: **REQ** (requirement) → **AC** (acceptance criterion) → **TEST** (named test) → **EVAL** (for the AI parts).

**How we applied it:** `docs/01-product/prd.md` holds **38 requirements, 67 acceptance criteria and 15 explicit non-goals (NG)**. `docs/11-quality/test-strategy.md` lists **61 named test cases** (TEST-01..) with the expected outcome and the REQ each proves. The 15 non-goals are as important as the requirements: they stop scope creep (for example, no faculty leaderboards, no student ranking).

**Proof:** commit messages carry the IDs (`T2.P2.3 REQ-008: ...`); the status board (`docs/phases/status.md`) shows each task's gate; **284 tests pass**, including 32 for the profiles feature (TEST-60..73) that were written from the plan before the code.

## C3. Layered architecture with enforced boundaries

**What:** three layers with one-way imports.

```
api (routes: auth, validation, response model)
  └─► services (business rules, one transaction per change)
        └─► repos (the only place Cypher exists, always parameterised)
              └─► ml (extraction, verification, embeddings, scorer)
```
**How we applied it:**
- **Cypher only in `repos/`**, never built from user input (SEC-17), so injection has nowhere to start. A test stores `"}) MATCH (n) DETACH DELETE n //` as an issue and checks the graph is unchanged.
- **One write transaction per change:** the change, its audit event (StatusEvent) and its notifications commit or roll back **together**. A fault-injection test proves a failure half-way leaves nothing behind.
- **Thresholds are configuration** (`core/config.py`), never literals: 45 days, 14 days, 0.85 confidence, fit cut-offs, upload sizes. The app **refuses to start** on a weak `JWT_SECRET_KEY` (under 32 characters) or `NEO4J_PASSWORD` (under 12).
- **Errors are `application/problem+json`** with stable codes (`NOT_ELIGIBLE`, `INVALID_TRANSITION`, `ALREADY_APPLIED`), so the frontend never parses English.
- **Router auto-discovery:** `main.py` mounts every module in `api/v1/`, so adding a route file never edits `main.py` (this removed a merge hotspot, see C6).

**Proof:** conventions are written in `AGENTS.md`; tests assert the 401, 403 and 404 order, problem+json shape, and rollback.

## C4. "Deterministic core, AI at the edge"

**What:** the central design rule. A model may *read* or *measure*; it may never *decide*.

**How we applied it:**
| Decision | Made by | AI's role |
|---|---|---|
| Is this certificate trusted? | Seven ordered rules + confidence formula (0.40 name, 0.25 issuer, 0.20 date, 0.15 complete; ≥ 0.85 certified) | Only reads the fields |
| How well does a student fit an opening? | Documented formula: 60 skill, 25 meaning, 15 near-miss, summing exactly | Provides one input: text similarity |
| Is a student eligible for an opening? | Plain rules (year, department, CGPA, deadline, capacity) | None |
| Does a mentee need attention? | Rules: no session in 45 days, overdue action, issue open 14 days | None |
| Who sees a record? | Role and scope predicates (403 versus 404) | None |

**Structural proof, not a promise:** the extraction schema has **no field** for status, trust or confidence, so text hidden in a certificate has nowhere to write them. This is asserted in `test_extraction.py`. CGPA is deliberately **never** part of the fit score, and a test checks that.

**Numbers done right:** fit math runs in `Decimal`, not float. We hit a real float bug (`100 × 0.15 × 0.07 = 1.0499999999999998`, which rounds to 1.0, not 1.1) that would have broken the rule that the three displayed parts sum to the displayed score. Recorded as decision L-1.

## C5. Security and privacy by design

**What:** security work starts from a **threat model**, not from a checklist at the end. `docs/08-security/security-and-privacy.md` has **21 numbered security requirements (SEC-01..21)**, each linked to a threat and a test.

**How we applied it (the ones judges ask about):**
| Concern | Control | Test |
|---|---|---|
| Leaking secrets in responses | Explicit response model on every route; scan of every GET as every role | TEST-01 |
| Old insecure endpoints | `/auth/register`, `/auth/reset-password`, profile-picture upload do not exist (404) | TEST-02 |
| Broken access control | **403** for wrong role, **404** for right role but not your record, so existence never leaks | TEST-04, 05 |
| Private mentoring text | Session notes only to their author; confidential issues counted, never described; IQAC sees **no student names** | TEST-20, 21, 26 |
| Malicious uploads | Magic-byte type check, 10 MB cap, PDF page cap, re-encode with Pillow, UUID filename, stored privately | TEST-06, 12 |
| Brute force | 10 logins per minute per IP; 20 uploads per hour per user; `429` with `Retry-After`; equal-timing login | TEST-09, 11 |
| Prompt injection | Fixed prompt, no tools, structured output, `contains_instructions` routes to human review | EVAL-04 (4/4) |
| Spreadsheet injection | Export cells starting with `= + - @` are prefixed with `'` | TEST-08 |
| Supply chain | `pip-audit` and `npm audit`; accepted findings listed with a reason in §9 | SEC-16 |
| Secrets in git | `.env` is gitignored; example file lists names only | SEC-10 |

**Privacy method:** *minimise first.* No phone, address or photo collected. Only the certificate image goes to the model; mentoring data **never** goes to any model. Synthetic data only. The doc lists what a real deployment would still need (consent, deletion on request, a data agreement with the provider, TLS, an httpOnly cookie instead of localStorage). **Residual risks are written down, not hidden** (§9).

## C6. Parallel team method (how four people built in one repository)

**What:** the plan assumed four builders over about 15 hours, so the process was designed to remove conflicts.

**How we applied it:**
1. **Single-owner files.** `tools/ownership.txt` maps every path to one of P1 (ML and matching), P2 (backend core, graph, security, Docker), P3 (frontend and mentor screens), P4 (seed, coordinator, docs and demo).
2. **A script enforces it.** `python tools/check_ownership.py P<n>` prints `BLOCK` for any changed file you do not own. Run before every push.
3. **Hotspots removed up front.** The files everyone would touch (`main.py`, `config.py`, `requirements.txt`, `package.json`, `conftest.py`, `nav.ts`) were written **complete** in phase 0, so later phases never edit them. A `features.ts` flag file lets each add-on owner flip only their own line.
4. **Seams with stubs.** Where one person's code appears on another's screen, the host places an empty *slot*; the feature owner fills a separate file.
5. **Checkpoints and gates.** C0 scaffold → C1 stubs → **G1** foundation → **G2** upload-to-certified works → **G3** core freeze → freeze → final. Add-ons only after the core passes its gate.
6. **Git discipline.** One feature branch per person; **never push to `main`**; PRs only; the lead merges with **Rebase and merge** (no squash, no merge commits), so each commit stands alone and is traceable. Commit format `T<phase>.<person>.<n> <REQ>: what`. Contract changes in their own commit.
7. **Per-person prompts.** Each lane had a written brief (`docs/phases/prompts/`), and later a "remaining work" brief per person.

**Proof:** the history on `main` is a linear sequence of rebased commits from five contributors; PRs #5 to #9 merged cleanly in sequence; the only conflict in the last wave was a **generated file**, resolved the documented way (re-run the generator, take its output).

## C7. A test strategy shaped like the risk

**What:** the test pyramid weighted to where bugs hide: pure rule functions (unit), and API behaviour against a **real Neo4j** (no database mocks).

**How we applied it:**
| Layer | Tool | What it proves |
|---|---|---|
| Unit | pytest | Scorer reproduces the spec's worked example (**43.4 and 68.5**) with the exact component split; every verification rule; needs-attention rules; XLSX sanitiser |
| API integration | pytest + httpx against real Neo4j | Security matrix, state machines (applications, actions, issues), privacy filters, metrics |
| Fault injection | pytest | A forced failure mid-transaction rolls back everything |
| Hand-computed oracles | pytest | Dashboard numbers are computed *in the test*, not read back from the code; dashboard totals equal the click-through row counts |
| AI evals | scripts | EVAL-01..04 against the live model, once after the cache build |
| End to end | Playwright | The primary flow in a real browser; every new page as student, faculty and HOD with no console errors |
| Static gates | ruff, ESLint, `tsc --noEmit`, Spectral | Clean before every merge |

**Method detail worth saying:** the model is **never called in tests**; a SHA-256 cache plus a stub adapter covers success, timeout and bad-JSON paths deterministically. The seed is **deterministic and checked**: `check_seed` independently re-derives the demo figures (50 students, 48 allotted, ratio 1:12, 91.7% compliance, 8 overdue actions, exactly 3 flagged mentees for Meera) and prints PASS or FAIL per figure.

**Test hygiene:** the suite wipes the database it runs on by design (decision L-8), so a reseed is part of the demo checklist.

## C8. Evaluation-driven AI (measure, do not claim)

**What:** the AI parts have their own evaluation, with targets set *before* running, and results reported even when unflattering.

**How we applied it** (`docs/plan/eval-results.md`, owned by P1):
| Eval | Target | Measured |
|---|---|---|
| EVAL-01 extraction, 4 key fields | ≥ 90% | **98.1%** (102/104, **26 files**, raw model output, no cache corrections) |
| EVAL-02 verification routing | 6/6 | **6/6** |
| EVAL-04 injection containment | all | **4/4** (two injection files, a receipt, a blank page) |
| Tamper signal | only the planted file | **1 of 32** files flagged (the planted edit); metadata check only, ELA turned off with a reason (L-7) |
| Demo fit (Aarav, Edge AI) | 38–50 then ≥ 65 | **43.5 Close → 70.9 Ready** |
| Offline demo | every file a cache hit | **6/6** |
| EVAL-03 hybrid vs keyword baseline | hybrid wins | **Tie, 1.000 vs 1.000: reported as not a valid test**, because the label set was too easy; we did not tune against the labels |

**The honesty rule:** *"only measured numbers go on slides."* Level/type accuracy is only **36.5%** and skill recall **59.6%**, which is exactly why every result shows a confidence and low-confidence ones go to a human reviewer. The weak numbers *justify the design*.

## C9. Decision log and written assumptions

**What:** every decision that changes the plan gets a row with the date and the evidence.

**How we applied it:** `docs/plan/decisions-log.md` records, among others:
- **D-2** Groq instead of the originally planned provider, because the only key available worked with one model that supports both images and strict JSON schema (verified with live calls).
- **L-1** Decimal arithmetic for the score. **L-2** Neo4j driver pinned to 5.28.7 to match the 5.26 server.
- **L-4** Trust is **derived from certified evidence**, never read back off the skill edge (otherwise a rejected certificate would leave a skill "verified").
- **L-5** Stay on Next 14 despite advisories (the vulnerable features are not used; a major upgrade is a team decision), with the three advisories named.
- **L-6** Seed certificate templates must be visually distinct, and the generator **asserts** it (a first version produced near-identical perceptual hashes that falsely flagged duplicates).
- **L-7** Tamper check uses the metadata tag only, with the measurements that led there.
- **L-9** Richer profile text moves the demo fit from 42.7→70.0 to 43.5→70.9; still inside the target range.

There are also **24 numbered assumptions (A-01…)** and the accepted risks. *This is the trust signal:* a mentor can ask "why X?" and we can point to the row.

## C10. Environment and operations method

**What:** the product runs the same everywhere, and the demo cannot be broken by the network.

**How we applied it:**
- **Docker Compose** with three services, health checks (Neo4j `cypher-shell`, backend `/health`, frontend `wget`), `depends_on: service_healthy`, ports bound to `127.0.0.1`, named volumes.
- **CPU-only PyTorch** installed from PyTorch's own index (the PyPI wheel is the multi-GB CUDA build), and the embedding model is **baked into the image** with `HF_HUB_OFFLINE=1`, so startup never reaches for the network.
- **Schema applied at startup** from `schema.cypher` (constraints and indexes), so there are no migrations to run.
- **One uvicorn worker by design:** the rate limiter and background jobs are in-process; a note says what scaling out would need (shared queue and rate-limit store).
- **Demo resilience:** SHA-256 extraction cache, `LLM_PROVIDER=none` mode, `seed --anchor-date` to pin "today", `TODAY_OVERRIDE` for tests, a daily LLM call cap.
- **Frontend image:** multi-stage build, standalone Next server, no dev dependencies at runtime.

## C11. User-centred and accessible design

**What:** screens designed from flows, with accessibility treated as a requirement.

**How we applied it:**
- `docs/05-frontend/ux-flows.md` defines **17 screens (SCR-01..)** and flows per role. Navigation is role-based; a route guard redirects by role; expired tokens go to login with a message.
- **One UI kit** (`components/ui`: pills, badges, empty/error/loading states, dialog, toast, timeline) so states are consistent everywhere.
- **Accessibility:** Lighthouse accessibility **100 on desktop and mobile** across the P3 screens; keyboard-only flow verified; **360 px no horizontal scroll**; about 260 `aria-`/`role` attributes in the source; loading regions announced; no raw HTML ever rendered (SEC-19).
- **Explain, do not just score:** every recommendation shows reasons built from the fit chips; no model writes text a user reads. Ineligible openings show an **eligibility checklist** with the exact failed rule.
- **Respect for people:** no student ranking, no faculty leaderboard, track record shows facts (openings posted, guide links accepted, median days to decision), not ratings.

---

# PART D: THREE FEATURES, END TO END (TECHNOLOGY AND METHOD AT EACH STEP)

## D1. ProofOnce: certificate to trusted skill

| Step | What happens | Technology | Method |
|---|---|---|---|
| 1 | Student uploads a PNG/JPG/PDF | Next.js form, axios, FastAPI `UploadFile` | Contract-first; typed response |
| 2 | Magic bytes, size, page count; re-encode image; SHA-256 and pHash | Pillow, ImageHash, pypdfium2 | Security by design (SEC-06) |
| 3 | Known file? Cache hit skips the network | JSON cache keyed by SHA-256 | Resilience: offline demo |
| 4 | Vision model reads fields under a strict schema | Groq `qwen/qwen3.8-27b`, `temperature 0`, one retry, 25 s timeout | AI at the edge; no field for trust |
| 5 | Seven ordered rules: duplicate file, duplicate image, same issuer + certificate ID, not a certificate, injection text, tamper, confidence | rapidfuzz, pure Python | Deterministic core; EVAL-02 |
| 6 | `certified` or `needs_review` with one reason per failed check | Neo4j: `Evidence -[:PROVES]-> Concept`, trust derived from evidence | Decision L-4; one transaction with StatusEvent and notifications |
| 7 | Mentor reviews doubtful ones (approve or reject with a reason) | Review queue screen | Human in the loop |
| 8 | Skill trust and profile embedding recomputed | MiniLM, local | Offline, private |

## D2. GuruSetu Match: explained fit, eligibility and recommendations

| Step | What happens | Technology | Method |
|---|---|---|---|
| 1 | Faculty creates an opening with rules: positions, deadline, years, minimum CGPA, departments, mode (`strict` or `advisory`) | Next.js form → `POST/PATCH` | Plan-first (`profiles-and-matching-plan.md`), contract-first |
| 2 | Eligibility evaluated: availability rules (closed, deadline, full, faculty at capacity) **always** block; suitability rules (year, department, CGPA) block only `strict` openings | Pure Python `eligibility.py` | Deterministic core; unknown CGPA never fails a student |
| 3 | Per required skill: has it (verified 0.85, endorsed 1.00, claimed 0.40), else a similar skill (SIMILAR_TO ≥ 0.60), else missing; rarer skills weigh more | Neo4j graph + `Decimal` scorer | Formula in `docs/06-ai/ai-system.md`, reproduced by a test |
| 4 | Score = 25·meaning + 60·skill + 15·near-miss; parts sum exactly | MiniLM + formula | Rounding rule: round each part, then sum |
| 5 | Recommendations grouped: Best matches, Worth a look, Stretch, Not eligible yet, each with up to three reason lines | Template reasons from the chips | No model-written text |
| 6 | "Why" graph draws student → skill → similar concept → required skill → opening | react-force-graph-2d | The explanation is literally a graph path |
| 7 | Apply; faculty sees applicants ranked by verified fit; accepting the last position closes the opening **in the same transaction** | Neo4j transaction | One write transaction per change |

## D3. Mentor Desk: mentoring that leaves a trail

| Step | What happens | Technology | Method |
|---|---|---|---|
| 1 | HOD allots students; capacity warning at 20; handover keeps history (old link `ended`) | Graph `MENTORS` edges with type | State machine tests (TEST-27) |
| 2 | Mentor logs a session, attendance, topics, private notes; creates action items and issues | FastAPI + one transaction | Idempotent logging; fault-injection rollback |
| 3 | "Needs attention": no session in 45 days, action overdue, issue open 14 days | Rules over records, thresholds in config | No AI; exactly 3 flagged for Meera on the seed |
| 4 | Student sees their own summary; confidential issues are counted, never described | Field-level omission (omit, not null) | Privacy tests (TEST-20, 21, 26) |
| 5 | HOD and IQAC dashboards: 50 students, 48 allotted, 1:12, 91.7% compliance; click a number to see the exact rows | One metrics function shared by dashboard and export | Same code path = reproducible numbers |
| 6 | DRAFT NAAC-style export (editable XLSX, no private text, formulas neutralised) | openpyxl | SEC-18; marked DRAFT, never claimed as an official submission |

---

# PART E: EVIDENCE SUMMARY

| Dimension | Evidence |
|---|---|
| **Traceability** | 38 REQ · 67 AC · 61 TEST IDs · 15 non-goals · 21 SEC requirements · 17 screens |
| **Automated tests** | **284 pass**, inside the Docker container, against a real Neo4j |
| **Static gates** | `ruff`, ESLint, `tsc --noEmit`, Spectral all clean; container builds clean |
| **Real-browser check** | Playwright over every new page as student, faculty and HOD; a real profile edit persisted; strict opening refused with the failing rule |
| **End-to-end scenario** | The documented demo scenario passes on a fresh seed (fit 43.5 → 70.9; 2 certified, 1 duplicate image, 1 name-mismatch to review) |
| **Seed verification** | `check_seed`: every figure PASS |
| **AI evaluation** | EVAL-01 98.1% (26 files) · EVAL-02 6/6 · EVAL-04 4/4 · tamper 1 of 32 · EVAL-03 reported as a tie, not a win |
| **Accessibility** | Lighthouse a11y 100 (desktop and mobile), keyboard-only flow, 360 px |
| **Security** | Scan of every GET for forbidden keys; 401/403/404 order; rate limits; upload checks; injection stored literally; log grep for private text |
| **Process** | 110 commits, five contributors, linear history, PRs merged by rebase, ownership checker, decision log |

---

# PART F: HONEST LIMITS (SAID UPFRONT)

- **Scale:** one worker by design; the free Groq tier is about 3 certificates per minute. Fine for a department, not for thousands of students without a queue.
- **AI accuracy:** extraction is strong on the four key fields (98.1%) but weak on `level`/`type` (36.5%) and skill recall (59.6%); that is why humans review low confidence.
- **Forgery:** we detect duplicates, mismatches, injection text and (optionally) an editing-software tag. We do **not** claim to detect a skilled forgery.
- **EVAL-03:** our labels were too easy, so the baseline tied the hybrid; we did not tune to fake a win.
- **Not built:** faculty certificates through ProofOnce; opt-in student discovery by faculty (it conflicts with a requirement and non-goal, so it needs a decision); the seed's extra certificates still hand-written rather than pushed through the pipeline.
- **Security residuals:** JWT in browser storage, no MFA, HTTP on localhost, Next 14 advisories accepted with reasons. All are listed with the condition to revisit.
- **Data:** synthetic only. A real deployment needs consent, deletion on request, TLS, a provider data agreement.
- **Naming honesty:** exports are **drafts** to assist a NAAC process; we never claim official submission.

---

# PART G: SHORT DEMO (about 5 minutes, method-flavoured)

1. **`docker compose up`:** three healthy services; show `/api/v1/health` (database and provider status).
2. **Show the contract:** open `openapi.yaml`, then `types.ts` header "generated"; "change the contract, regenerate, the compiler finds the rest".
3. **Aarav's fit** 43.5 Close with three parts that sum exactly; open **Why** (graph path).
4. **Upload three certificates:** one certified (AI read, rules decided), one duplicate (pHash), one name mismatch to review. Say: "the model has no field to set trust".
5. **Eligibility:** open the strict NLP opening; the checklist names the failing CGPA rule; apply is refused with `NOT_ELIGIBLE`. Say: "CGPA is never in the score".
6. **Mentor home:** exactly three flagged mentees, each with a reason: "no AI here, three plain rules".
7. **Dashboard click-through:** a number opens the exact rows; download the DRAFT export and open it: no private text.
8. **Show the safety net:** `LLM_PROVIDER=none` and an unknown file falls to manual entry; run `pytest` (284) and `check_seed` (all PASS) if time allows.

---

# PART H: Q&A TOOLKIT

| Question | Answer |
|---|---|
| **What methodology did you follow?** | Contract-first, requirements-to-tests traceability, a deterministic core with AI at the edge, security by design from a threat model, and a conflict-free parallel workflow with single-owner files and rebase merges. |
| **Why contract-first?** | Four people built backend, frontend and ML in parallel. One spec generates both sides' types, so they cannot drift, and a contract change shows every place to fix. |
| **How do you know it works?** | 284 automated tests on a real database, hand-computed expected values, fault-injection for rollback, a Playwright run in a real browser, a seed checker that re-derives the demo numbers, and AI evaluations on 26 labelled files. |
| **How do you keep AI from making decisions?** | The schema has no field for status, trust or confidence; rules decide; low confidence goes to a human. This is tested, not promised. |
| **Why a graph database?** | Students, skills, certificates, openings, faculty and mentoring are relationships; the "why" explanation is a path; vector index lives in the same store. |
| **How did four people avoid conflicts?** | Every file has one owner, a script blocks edits outside your lane, hotspot files were finished in phase 0, and the lead merges by rebase. |
| **What is your security approach?** | Threat model first, 21 numbered requirements each with a test: typed responses, 403 versus 404, private text never leaving its owner, upload hardening, rate limits, injection tests. |
| **How do you handle privacy?** | Minimise, scope, never send mentoring data to a model, synthetic data, and a written list of what a real deployment needs. |
| **What went wrong, and what did you learn?** | A float rounding bug broke "parts sum to the score", so we moved to Decimal. Near-identical certificate templates caused false duplicates, so the generator now asserts visual distance. A rejected certificate could leave a skill "verified", so trust is now derived from evidence. A student's own upload was flagged as its own duplicate, so the fingerprint is stored only with the final result. All are in the decision log or tests. |
| **What is your weakest part?** | Level/type and skill recall from the model; our baseline comparison was a tie. We say so and keep humans in the loop. |
| **Did you use AI to build it?** | The product's AI use is in Review 2. For development, builders used coding assistants against written specs and per-person briefs; the specs, tests and ownership checks are what keep generated code correct. *(Adjust this line to match what your team will state.)* |
| **Can it scale?** | Today one worker and a free model tier. The layering isolates the in-process pieces (rate limiter, background jobs), so a shared queue and rate-limit store are the upgrade path. |
| **What would you do next?** | Faculty certificates via the same pipeline, an opt-in discovery flow (after a policy decision), a harder blind evaluation set, a second model provider as fallback, httpOnly cookies and TLS for a hosted version. |

---

# PART I: SLIDE OUTLINE (7 slides)

1. **Our method in one line:** "Write the rules down first, then make the machine enforce them."
2. **Technology map:** the Part B table, six rows.
3. **Contract-first:** the generation diagram (one spec, two generated sides, Spectral).
4. **Rules decide, AI reads:** the C4 table and "no field for trust".
5. **Built to be tested:** REQ → AC → TEST traceability numbers, 284 tests, real Neo4j, seed checker.
6. **Secure and private by design:** threat model, 21 SEC requirements, 403/404, private text never leaves.
7. **How four people shipped:** ownership map, checkpoints and gates, rebase merges, decision log; then the honest limits and the next steps.
