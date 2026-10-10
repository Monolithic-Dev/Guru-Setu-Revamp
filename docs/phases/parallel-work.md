# Parallel Work Without Merge Conflicts
Purpose:      Let P1–P4 work simultaneously for all 15 hours with zero merge conflicts, through single-owner files, pre-made shared files, stubs at every seam, and a pre-push ownership check.
Audience:     All four builders and coding agents.
Depends on:   docs/phases/README.md, all phase docs, docs/02-architecture/architecture.md §9
Status:       Draft v1

---

## 1. The rule

**Every file has exactly one owner, and only the owner edits it.** The map is [tools/ownership.txt](../../tools/ownership.txt). Git only conflicts when two branches change the same lines of the same file, so file-disjoint branches merge cleanly in any order.

Three exceptions, each with its own rule:

| Kind | Files | Rule |
|---|---|---|
| **ALL** (shared, append-only) | `docs/phases/status.md` | Edit only your own rows or append bugs, in a separate commit straight to `main` after `git pull --rebase`. If git still reports a conflict, keep both sides. |
| **GEN** (generated) | `frontend/src/lib/types.ts`, `backend/app/schemas/generated.py` | Never hand-edit. Change only by re-running the generator after a contract change (§5). On a conflict, re-run the generator and take its output. |
| **Seams** (one person's code shows up on another's screen) | The slots in §4 | The owner of the host file places a **slot**; the feature owner fills a separate file. Nobody edits the other's file. |

Before every push, run:
```
python tools/check_ownership.py P2      # your id
```
It prints `BLOCK` for any changed file you don't own. Make that change through its owner instead. Optional pre-push hook: `.git/hooks/pre-push` containing `python tools/check_ownership.py $GURUSETU_ME || exit 1`.

## 2. Ownership at a glance

| Area | P1 | P2 | P3 | P4 |
|---|---|---|---|---|
| Backend app | `app/ml/**`, `api/v1/match.py` (API-012/013/015/016/020/021), `api/v1/endorsements.py` (API-041), `repos/match_repo.py`, `repos/ml_repo.py` (all Cypher used by `app/ml/`), `schemas/match.py` | Everything else in `backend/app/**`: `main.py`, `core/`, `api/deps.py`, all other `api/v1/*`, `services/`, `repos/`, `schemas/` | — | — |
| Backend build | `requirements.txt`, `Dockerfile` | `docker-compose.yml`, `.env.example`, `backend/schema/` | — | — |
| Data | `seed/aliases.json`, `seed/similar_overrides.json`, `seed/fit_tuning.json`, `extraction_cache/`, eval and cache scripts | — | — | All other `backend/seed/**`, `scripts/seed.py`, `scripts/check_seed.py` |
| Backend tests | `test_verification`, `test_scorer`, `test_matching`, `test_embedding`, `test_extraction` | `conftest.py` and all other tests | — | — |
| Frontend routes | SCR-03 `student/openings/**` | — | SCR-01, 04, 06, 07, 08, 09, 10, `faculty/openings/new`, all `layout.tsx` | SCR-02 `student/page.tsx`, SCR-05, SCR-11/12/13 `coordinator/**`, SCR-14 `notifications/**`, SCR-15 `faculty/openings/page.tsx`, SCR-16 |
| Frontend shared | `components/fit/**` | — | `package.json` + lockfile, `lib/api.ts`, `lib/nav.ts`, `lib/features.ts`, `hooks/`, `components/ui/**`, `components/mentor/**`, `components/why/**` | `components/coordinator/**`, `components/student/**` |
| Fixtures | `fixtures/p1/` | — | `fixtures/p3/` | `fixtures/p4/` |
| Docs | `docs/06-ai/`, `plan/eval-results.md` | `docs/02-architecture/`, `04-backend/`, `08-security/`, `10-devops/`, `11-quality/`, `plan/decisions-log.md`, `tools/` | `docs/05-frontend/` | PRD, index, README, AGENTS.md, `docs/plan/` (except the two logs above), `docs/phases/` (except `status.md`), `plan/qa-log.md` |

**Router split.** API-014 (create opening, P2) lives in `api/v1/openings_write.py`. P1's `match.py` holds the read and fit routes. FastAPI doesn't care that both use `/openings/...` paths.

## 3. Hotspots removed in Phase 0

These are the files everyone would otherwise touch. Phase 0 creates each one **complete**, so later phases never edit it:

| Hotspot | Fix (done once in Phase 0) | Owner |
|---|---|---|
| `backend/app/main.py` (router registration) | **Auto-discovery:** `main.py` imports every module in `app/api/v1/` and includes its `router`. Adding a router file needs no edit to `main.py`. | P2 |
| `main.py` startup hooks | `main.py` calls `app.ml.startup()` (P1 owns `ml/__init__.py`) and `app.services.jobs.startup()` (P2). Each owner fills their own hook. | P2 / P1 |
| `core/config.py` | Every variable from backend §8 is added at once, so nobody adds settings later. | P2 |
| `requirements.txt` / `Dockerfile` | Every backend dependency for all phases is pinned at once (ML, `openpyxl`, `pytest`, `httpx`, `ruff`, `datamodel-code-generator`). | P1 |
| `frontend/package.json` + lockfile | Every frontend dependency for all phases is added at once (`recharts`, `react-force-graph-2d`, `openapi-typescript`, `@playwright/test`). | P3 |
| Pydantic request/response models | Generated from `openapi.yaml` into `schemas/generated.py` (GEN). Area code may add thin wrappers in its own `schemas/<area>.py`. | GEN |
| TS types | Generated into `lib/types.ts` (GEN) | GEN |
| Navigation | `lib/nav.ts` lists every route of every role, including P1/P2 add-on routes, from the start | P3 |
| Feature switches | `lib/features.ts`: `{ whyGraph: false, skillGap: false, reminders: false, createOpening: false }`. Each add-on owner flips **only their flag** in their own commit. It's a 4-line file and each flag is its own line. | P3 (file), each flag owner flips |
| Test fixtures | `tests/conftest.py` with persona tokens and the fresh-seed fixture is written in T1.P2.2, before anyone writes tests. Others put extra fixtures in their own test files. | P2 |
| Seed text tuning | `seed.py` applies `seed/fit_tuning.json` (P1) after loading P4's JSON, so P1 can tune Aarav's bio and opening descriptions without touching P4's files | P4 (hook), P1 (file) |

**Flag lines in `features.ts`:** `whyGraph` → P3 (A2), `skillGap` → P1 (A5), `reminders` → P3 (A3), `createOpening` → P3 (A9). Two owners edit different lines of this file, so a conflict is possible only if both edit within the same minute; if so, keep both sides.

## 4. Seams: stub first, then fill

Where one person's work appears inside another person's file, the **imported module's owner commits a stub with the final signature by the deadline**. The host imports it right away. After that, each side edits only its own file.

| Seam | Stub file (owner) | Host file (owner) | Stub by | Filled in |
|---|---|---|---|---|
| ML startup | `app/ml/__init__.py::startup()` (P1) | `main.py` (P2) | 1:00 | T1.P1.1 |
| Embedding API | `ml/embedding.py::embed, student_text, opening_text, recompute_*` (P1) | `services/*` (P2), `seed.py` (P4) | 1:30 | T1.P1.1 |
| Concepts | `ml/concepts.py::normalise, get_or_create_concept, rebuild_similarity` (P1) | `seed.py` (P4), `services/*` (P2) | 1:30 | T1.P1.2 |
| Seed hooks | `ml/seed_hooks.py::seed_embeddings` (P1) | `seed.py` (P4) | 2:00 | T1.P1.4 |
| Extraction | `ml/extraction.py::extract` (P1) | `services/certificates.py` (P2) | 4:15 | T1.P1.3, T2.P1.1 |
| Verification + trust | `ml/verification.py::verify`, `ml/trust.py::apply_certified, recompute_skill` (P1) | `services/certificates.py` (P2), `seed.py` (P4) | 4:15 | T2.P1.2, T2.P1.4 |
| Deps and core | `core/database.py`, `api/deps.py`, `core/errors.py` (P2) | `api/v1/match.py` (P1) | 2:00 | T1.P2.2–3 |
| Notify / status | `services/notify.py`, `services/status_history.py` (P2) | (P1 never writes notifications) | 2:30 | T1.P2.4 |
| UI kit | `components/ui/*` (P3) | P1, P4 pages | 2:30 | T1.P3.4 |
| Why graph | `components/why/WhyGraph.tsx` (P3), returns `null` | SCR-03 page (P1), behind `features.whyGraph` | 2:30 | A2 |
| Reminders panel | `components/mentor/RemindersPanel.tsx` (P3), returns `null` | SCR-14 page (P4), behind `features.reminders` | 2:30 | A3 |
| Fit components | `components/fit/{FitScoreRing,ScoreBreakdownBar,FitPanel}.tsx` (P1) | SCR-09 page (P3) | 7:30 | T3.P1.4 |
| Skill-gap card | `components/fit/SkillGapCard.tsx` (P1), returns `null` | SCR-02 page (P4), behind `features.skillGap` | 7:30 | A5 |
| Create-opening link | route `faculty/openings/new` (P3) | SCR-15 page (P4) renders the link only when `features.createOpening` is true | 9:00 (P4 adds the link) | A9 |

A stub must compile and keep the final signature. If the signature has to change later, the stub owner tells the host owner, who then updates the call site in their own file.

## 5. Contract changes (`openapi.yaml`, `schema.cypher`, extraction schema)

1. Ask the contract owner in chat: P2 for `openapi.yaml` and `schema.cypher`, P1 for `ml/schemas/certificate_extraction.schema.json`.
2. The owner commits the contract edit **alone** to `main` within 15 minutes, with the message `CONTRACT: <what> (requested by Px)`.
3. Right after, anyone runs the generators and commits only the GEN outputs:
   ```
   npx openapi-typescript docs/04-backend/openapi.yaml -o frontend/src/lib/types.ts
   datamodel-codegen --input docs/04-backend/openapi.yaml --input-file-type openapi \
     --output backend/app/schemas/generated.py --output-model-type pydantic_v2.BaseModel
   ```
4. Everyone runs `git pull --rebase`. Contract changes are additive only (new optional fields). Never rename or remove a field after G0.

## 6. Git workflow

- **Branches:** `p<n>/<task-id>-<slug>`, for example `p2/t2-p2-3-sessions`. Branch from the latest `main`, and merge back at least once an hour and at every gate.
- **Before pushing:**
  1. `git pull --rebase origin main`
  2. `python tools/check_ownership.py P<n>`
  3. Your own tests: `pytest -q <your test files>`, or `npm run lint` plus `tsc --noEmit` for frontend
  4. Push and merge (fast-forward or a PR without review). Because files are disjoint, the merge order doesn't matter.
- **`main` must always boot.** After merging, run `docker compose up -d --build` and `seed --reset` once if you touched the backend or seed. If you break `main`, fixing it is your top priority.
- **Never commit:** `.env`, uploads, `node_modules`, `.next`, exports (`.gitignore` covers these).
- **Shared commits** (`status.md`, contract edits, GEN outputs) go straight to `main` as separate small commits, never mixed into feature commits.

## 7. Conflict-free check per phase (who touches what)

| Phase | P1 files | P2 files | P3 files | P4 files | Overlap |
|---|---|---|---|---|---|
| 0 | `requirements.txt`, `Dockerfile`, `ml/__init__.py` | scaffold commit (first), `docker-compose.yml`, `.env.example`, `main.py`, `config.py`, `schema/`, `api/v1/health.py`, `schemas/generated.py` (first run) | `frontend/**` cleanup, `package.json`, `lib/{types,nav,features}.ts`, frontend `Dockerfile` | `backend/seed/**` skeleton, `scripts/seed.py` stub, `tools/certgen/` | None after the scaffold commit (§8) |
| 1 | `ml/embedding.py`, `ml/concepts.py`, `repos/ml_repo.py`, `ml/extraction.py`, `ml/seed_hooks.py`, `ml/schemas/`, `ml/prompts/`, `seed/aliases.json`, `seed/similar_overrides.json`, `seed/fit_tuning.json`, P1 tests | `core/*`, `api/deps.py`, `api/v1/{auth,students,applications,notifications}.py`, `services/{notify,status_history,applications}.py`, `repos/{users,students,applications,notifications}_repo.py`, `tests/conftest.py`, `tests/test_security.py`, `tests/test_applications.py` | `lib/api.ts`, `lib/problem.ts`, `hooks/`, `components/ui/**`, `components/why/WhyGraph.tsx` (stub), `components/mentor/RemindersPanel.tsx` (stub), layouts, `app/login`, P3 route stubs, `fixtures/p3/` | `seed/*.json` (except P1's three), `seed/labels/`, `seed/certificates/`, `seed/demo_uploads/`, `scripts/seed.py`, `scripts/check_seed.py` | None |
| 2 | `ml/extraction.py`, `ml/verification.py`, `ml/trust.py`, `repos/ml_repo.py`, `extraction_cache/`, `scripts/build_extraction_cache.py`, `test_verification.py`, `test_extraction.py` | `api/v1/{certificates,mentorship}.py`, `services/{certificates,jobs,mentorship}.py`, `repos/{certificates,mentorship}_repo.py`, `tests/test_certificates.py`, `tests/test_mentorship.py` | `app/student/certificates/`, `app/reviews/`, `app/faculty/sessions/`, `components/mentor/*` (form parts) | `seed/certificates_index.json`, `scripts/seed.py` (step 5), P4 route stubs, `app/coordinator/allotment/`, `app/student/mentorship/`, `fixtures/p4/` | None |
| 3 | `ml/scorer.py`, `api/v1/match.py`, `repos/match_repo.py`, `seed/fit_tuning.json`, `components/fit/**`, `app/student/openings/**`, `test_scorer.py`, `test_matching.py` | `api/v1/{tracking,dept,evidence}.py`, `services/{tracking,metrics,evidence_export}.py`, `repos/{tracking,metrics}_repo.py`, `tests/test_{tracking,metrics}.py` | `app/faculty/page.tsx`, `app/faculty/mentees/`, `app/faculty/openings/[id]/` | `app/coordinator/page.tsx`, `components/coordinator/`, `app/student/page.tsx`, `app/notifications/`, `app/faculty/openings/page.tsx` | None |
| 4 | `api/v1/match.py` (API-020/021), `repos/match_repo.py`, `ml/verification.py` (rule 6), `scripts/eval_match.py`, `components/fit/SkillGapCard.tsx`, `features.ts` line `skillGap`, `plan/eval-results.md` | `api/v1/dept.py` (API-034, `escalated_issues`), `api/v1/tracking.py` (API-039), `api/v1/mentorship.py` (issues, API-045), `api/v1/openings_write.py` (API-014), related services and tests | `components/why/WhyGraph.tsx`, `components/mentor/RemindersPanel.tsx`, `app/faculty/page.tsx` (reminder link), `app/faculty/mentees/` (issue actions), `app/faculty/sessions/` (confidential), `app/faculty/openings/new/`, `features.ts` lines `whyGraph`/`reminders`/`createOpening` | `app/coordinator/metrics/`, `components/coordinator/` (clickable tiles, escalated list), `app/student/mentorship/` (dialogs), deck | `features.ts` (separate lines, §3) |
| 6 | `plan/eval-results.md`, P1 bug fixes | `tools/`, P2 bug fixes, tags | P3 bug fixes, `e2e/` | `README.md`, `plan/qa-log.md`, deck | None |

Bug fixes in Phase 6 go to the **file owner**, even if someone else found the bug.

## 8. The one sequential moment: the scaffold commit (0:00–0:20)

The scaffold is committed once, by P2 during the decision gate (T0.P2.0; the build is from scratch, no old repos):
1. Create the `backend/` skeleton and generate `frontend/` with `create-next-app@14`.
2. Confirm the root `.gitignore` covers `uploads/`.
3. Commit `chore: scaffold backend and frontend` and push.

Everyone else pulls **after** this commit before creating a branch. This is the only point where one person's commit blocks the others, and it takes about 20 minutes.

## 9. If a conflict happens anyway

1. Stop. Run `python tools/check_ownership.py <you>` to find out who owns the file.
2. If it's your file and someone else edited it: their change is wrong by the rules. Keep your version, and ask them to send the change to you.
3. If it's a GEN file: re-run the generator.
4. If it's `status.md` or `features.ts`: keep both sides.
5. Record it in `status.md` §8 so the ownership map can be fixed (P2 owns `tools/ownership.txt`).
