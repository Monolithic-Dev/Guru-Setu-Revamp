# Phase 0: Setup (0:00–1:00)
Purpose:      Make the blocking decisions and get one bootable repo on every laptop before any feature work.
Audience:     All four builders.
Depends on:   docs/00-index.md §5 (assumptions), docs/02-architecture/architecture.md §8–§9, docs/10-devops/environments-and-deployment.md
Status:       Draft v1

## 1. Goal and exit gate

**Goal:** by 1:00, every shared file exists in its final form (parallel-work §3), every person can run `docker compose up -d --build`, sees a healthy API and a building frontend, and the decisions that would change the plan are recorded.

**G0 gate (all on `main`):**
- [ ] `docs/plan/decisions-log.md` exists with answers to D-1..D-6 (§2)
- [ ] `docker compose up -d --build` → `docker compose ps` shows neo4j, backend and frontend healthy
- [ ] `curl -s localhost:8000/api/v1/health` → `{"status":"ok","neo4j":"up","llm_provider":"…"}`
- [ ] `npm --prefix frontend run build` succeeds; `frontend/src/lib/types.ts` generated from `openapi.yaml`
- [ ] `python -c "…SentenceTransformer…"` inside the backend container prints `384`
- [ ] `backend/seed/` has the file skeleton from T0.P4.1, and `scripts/seed.py --reset` runs (it may load only departments, terms and users)
- [ ] No uploaded files are tracked (`git ls-files uploads` is empty)
- [ ] `python tools/check_ownership.py --who backend/app/main.py` prints `P2`; every builder ran it once on their branch
- [ ] Shared files exist in final form: `main.py` (auto-discovery), `config.py` (all settings), `requirements.txt`, `package.json` (all deps), `lib/nav.ts`, `lib/features.ts`, `schemas/generated.py`, `lib/types.ts`

## 2. First 15 minutes: decision gate (everyone, T0.ALL.1)

Decide, and write the answers in `docs/plan/decisions-log.md`:

| ID | Decision | Default if nobody knows | Changes |
|---|---|---|---|
| D-1 | Reuse the old GuruSetu code? **Decided: no, build from scratch** (A-05). Still confirm that the Genesis rules allow reusing the earlier project's concept and name. | Scratch build; disclose the concept origin | Phase 1 P2 and P3 write auth, core and the shell instead of repairing them (about +2 h across P2 and P3 [I]) |
| D-2 | Is LLM use allowed? Is an Anthropic key available? (A-09) | Yes; key in `.env` | If no: `LLM_PROVIDER=none`, and T2.P1.1 becomes cache-building by hand-labelling JSON |
| D-3 | Who is P1/P2/P3/P4? How many people? (A-01) | 4 people as in the README | 3 or 2 people: apply the [CUT-3]/[CUT-2] marks |
| D-4 | Local Docker Neo4j for the demo? (A-06) | Yes | Aura: set `NEO4J_URI`, skip the neo4j service |
| D-5 | Is a submission URL required? | No | Yes: P2 adds ENV-03 in Phase 6 (+30 min) |
| D-6 | Real start time `0:00 = ____`, plus gate wall-clock times | — | Fill the README §1 note |

## 3. Tasks

File ownership follows [parallel-work.md](parallel-work.md). Every task below touches only its owner's files.

### T0.P2.0 Scaffold commit (P2, during the decision gate, about 20 min)
- **Spec:** ADR-01, parallel-work §8, SEC-14. The build is from scratch (D-1): no old repos are needed.
- **Steps:**
  1. Create the backend skeleton: `backend/app/main.py` (a FastAPI app with a stub `GET /api/v1/health`), empty packages `backend/app/{core,api/v1,schemas,services,repos,ml}/__init__.py`, and `.gitkeep` files in `backend/{scripts,seed,tests}/`.
  2. Create the frontend with the official generator: `npx create-next-app@14 frontend --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"` [VERIFY: current flags], then clear the sample page.
  3. Confirm the root `.gitignore` covers `.env`, `uploads/`, `node_modules/`, `.next/`, `__pycache__/` and exports.
  4. Commit `chore: scaffold backend and frontend` and push.
- **Done when:** the commit is on `main`. **Everyone else pulls before creating a branch.** This is the only sequential step of the build.

### T0.P2.1 Compose, config, app entry, schema, generated models (45 min)
- **Spec:** ADR-13, architecture §9, environments §2, backend §8, parallel-work §3
- **Files (P2):** `docker-compose.yml`, `docs/10-devops/env.example` (only if a variable is missing), `backend/app/main.py`, `backend/app/core/config.py`, `backend/schema/schema.cypher`, `backend/app/api/v1/health.py`, `backend/app/services/jobs.py`, `backend/app/schemas/generated.py` (GEN, first run)
- **Steps:**
  1. Rewrite `config.py` with pydantic-settings fields for **every** variable in backend §8, so nobody adds settings later. Remove `CLOUDINARY_*` and `OPENAI_API_KEY`. At startup, check `len(JWT_SECRET_KEY) >= 32` and `len(NEO4J_PASSWORD) >= 12`, and raise with a clear message otherwise (SEC-10).
  2. Write `main.py` once, in final form:
     - **router auto-discovery:** `for m in pkgutil.iter_modules(app.api.v1.__path__): include importlib.import_module(...).router` when the module has a `router`, all under prefix `/api/v1`;
     - a lifespan that applies the schema (split `schema.cypher` on `;`, run each statement; idempotent), then calls `app.ml.startup()` (P1's stub) and `app.services.jobs.startup()` (your stub, filled with JOB-02 in Phase 2);
     - placeholder lines for the middleware and error handlers, filled in T1.P2.2. Keep them in `core/` modules that `main.py` imports, so `main.py` itself never changes again.
  3. Copy `docs/04-backend/schema.cypher` to `backend/schema/schema.cypher`.
  4. Add `api/v1/health.py` (API-040): run `RETURN 1` against Neo4j and return `{status, neo4j, llm_provider}`; 503 on failure.
  5. Run `datamodel-codegen --input docs/04-backend/openapi.yaml --input-file-type openapi --output backend/app/schemas/generated.py --output-model-type pydantic_v2.BaseModel`. The tool comes from P1's requirements; if T0.P1.1 isn't merged yet, run it from a local venv.
  6. Write `docker-compose.yml` per environments §2: neo4j `5.26-community` with healthcheck, backend depending on healthy neo4j, frontend depending on healthy backend; volumes `neo4j_data` and `uploads`; `env_file: .env`.
  7. Do not create a root `.env.example`: the single template is `docs/10-devops/env.example` (`cp docs/10-devops/env.example .env`).
- **Done when:** the G0 health check passes on your machine, and on one teammate's machine after `git pull`.

### T0.P3.1 Frontend clean-up, dependencies, shared frontend files (45 min)
- **Spec:** architecture §9, ux-flows §2, §8, parallel-work §3
- **Files (P3):** `frontend/**` (except P1/P4 folders and GEN), `frontend/package.json` + lockfile, `frontend/Dockerfile`, `src/lib/nav.ts`, `src/lib/features.ts`, `src/lib/types.ts` (GEN, first run)
- **Steps:**
  1. After pulling the scaffold commit: `npm ci && npx tsc --noEmit && npm run build` to confirm the generated app builds.
  2. Add **every** frontend dependency for all phases now, so the lockfile never changes again: `recharts`, `react-force-graph-2d`, dev `openapi-typescript`, dev `@playwright/test`. Add the scripts `gen:types` and `e2e`.
  3. Write `frontend/Dockerfile` (node:20-alpine, build arg `NEXT_PUBLIC_API_BASE`, `next build` then `next start -p 3000`).
  4. `npm run gen:types` → `src/lib/types.ts`.
  5. `src/lib/nav.ts`: the full route list per role from ux-flows §2 and §6, including the P1/P2 add-on routes (`/coordinator/metrics/[metric]`, `/faculty/openings/new`, `/faculty-profile/[id]`).
  6. `src/lib/features.ts`, exactly 4 flags, one per line: `whyGraph: false`, `skillGap: false`, `reminders: false`, `createOpening: false`.
  7. Create empty owner folders with a `.gitkeep`: `src/fixtures/{p1,p3,p4}/`, `src/components/{ui,fit,mentor,why,coordinator,student}/`.
- **Done when:** `npm run build` passes, and the frontend container serves `/login` (the generated placeholder page is fine for now).

### T0.P1.1 Backend dependencies, Dockerfile, model bake, ML startup stub (45 min)
- **Spec:** architecture §4, ai-system §2.1 and §5, environments §2, parallel-work §3
- **Files (P1):** `backend/requirements.txt`, `backend/Dockerfile`, `backend/app/ml/__init__.py`
- **Steps:**
  1. Pin **every** backend dependency for all phases now: `fastapi`, `uvicorn`, `neo4j`, `pydantic-settings`, `python-multipart`, `bcrypt`, `PyJWT`, `sentence-transformers`, `anthropic` (latest at hour 0), `Pillow`, `imagehash`, `pypdfium2`, `rapidfuzz`, `openpyxl`, and dev tools `pytest`, `httpx`, `ruff`, `datamodel-code-generator`, `pip-audit`. Do not add `cloudinary`, `openai` or `passlib`.
  2. Dockerfile:
     - `CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000","--workers","1"]` (audit H6);
     - CPU torch wheel installed before the requirements;
     - bake the model into `/models`, with `ENV HF_HOME=/models` (environments §2);
     - copy `seed/` and `extraction_cache/`.
  3. `app/ml/__init__.py` with `def startup() -> None: pass`. You fill it in T1.P1.1 (model load).
  4. Verify inside the container: `python -c "from sentence_transformers import SentenceTransformer as S;m=S('sentence-transformers/all-MiniLM-L6-v2');print(m.get_sentence_embedding_dimension())"` prints `384`.
  5. If D-2 is yes, send one tiny Messages API call with `claude-opus-5-5` to confirm the key and model ID. Record the outcome in the decisions log via P2. **Do not commit the key.**
- **Done when:** `384` is printed with the network off (the model was baked), `app.ml.startup` imports, and the key check is recorded.

### T0.P4.1 Seed skeleton and certificate template (45 min)
- **Spec:** backend §10, ai-system §2.4 and §10
- **Files:** `backend/seed/{users,departments,terms,openings,concepts,aliases,similar_overrides,issuers,mentorships,sessions,action_items,issues,academics,certificates_index}.json`, `backend/seed/labels/`, `backend/scripts/seed.py` (stub), `tools/certgen/`
- **Steps:**
  1. Create each JSON file with 1–2 example records in the final shape (fields named exactly as ENT- tables). Every date is written as an offset from the anchor 2026-10-10, for example `"date": "-12d"`, so `--anchor-date` can shift them.
  2. A `seed.py` stub: `--reset` deletes all nodes, applies the schema, and loads departments, terms and users with bcrypt-hashed `Demo@123`.
  3. Certificate generator: an HTML template rendered to PNG (any tool you are fast with, for example a headless browser screenshot or Pillow text drawing) with fields name, title, issuer, date, ID. Produce 1 sample.
- **Done when:** `docker compose exec backend python -m scripts.seed --reset` prints "Seeded: 56 users", and the sample certificate PNG exists.

## 4. Risks in this phase

| Risk | Response |
|---|---|
| The scaffold command or its flags differ from what is written here | Run `npx create-next-app@14 --help` and adapt; the goal is only a TypeScript + Tailwind app-router project with `src/` |
| Torch wheel download is slow at the venue | One person builds the backend image first and shares it with `docker save \| docker load` via USB |
| No Anthropic key | `LLM_PROVIDER=none`; P1 hand-writes cache JSON in Phase 2 (`source:"cache"`) |
| Genesis rules forbid reusing the earlier project's idea or name | Rename the product in the README and UI (a text change only); the spec is unchanged |
