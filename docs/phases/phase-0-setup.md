# Phase 0: Setup (0:00–1:00)
Purpose:      Make the blocking decisions and get one bootable repo on every laptop before any feature work.
Audience:     All four builders.
Depends on:   docs/00-index.md §5 (assumptions), docs/02-architecture/architecture.md §8–§9, docs/10-devops/environments-and-deployment.md
Status:       Draft v1

---

## 1. Goal and exit gate

**Goal:** by 1:00, every person can run `docker compose up -d --build`, sees a healthy API and a building frontend, and the decisions that would change the plan are recorded.

**G0 gate (all on `main`):**
- [ ] `docs/plan/decisions-log.md` exists with answers to D-1..D-6 (§2)
- [ ] `docker compose up -d --build` → `docker compose ps` shows neo4j, backend and frontend healthy
- [ ] `curl -s localhost:8000/api/v1/health` → `{"status":"ok","neo4j":"up","llm_provider":"…"}`
- [ ] `npm --prefix frontend run build` succeeds; `frontend/src/lib/types.ts` generated from `openapi.yaml`
- [ ] `python -c "…SentenceTransformer…"` inside the backend container prints `384`
- [ ] `backend/seed/` has the file skeleton from T0.P4.1, and `scripts/seed.py --reset` runs (it may load only departments, terms and users)
- [ ] `uploads/` from the old repo is not in the tree (`git ls-files uploads` is empty)

## 2. First 15 minutes: decision gate (everyone, T0.ALL.1)

Decide, and write the answers in `docs/plan/decisions-log.md`:

| ID | Decision | Default if nobody knows | Changes |
|---|---|---|---|
| D-1 | Do the Genesis rules allow reusing the GuruSetu code (with disclosure), and do the original owners agree? (A-05, RISK-01) | Yes, and disclose | If no: build fresh on the same stack from the spec. Phase 1 P2 work becomes "scaffold", not "repair" (about +1 h) |
| D-2 | Is LLM use allowed? Is an Anthropic key available? (A-09) | Yes; key in `.env` | If no: `LLM_PROVIDER=none`, and T2.P1.1 becomes cache-building by hand-labelling JSON |
| D-3 | Who is P1/P2/P3/P4? How many people? (A-01) | 4 people as in the README | 3 or 2 people: apply the [CUT-3]/[CUT-2] marks |
| D-4 | Local Docker Neo4j for the demo? (A-06) | Yes | Aura: set `NEO4J_URI`, skip the neo4j service |
| D-5 | Is a submission URL required? | No | Yes: P2 adds ENV-03 in Phase 6 (+30 min) |
| D-6 | Real start time `0:00 = ____`, plus gate wall-clock times | — | Fill the README §1 note |

## 3. Tasks (45 minutes after the decision gate)

### T0.P2.1 Import backend and wire Compose (45 min)
- **Spec:** ADR-01, ADR-13, architecture §9, environments §2, backend §8
- **Files:** `backend/**`, `docker-compose.yml`, `backend/Dockerfile`, `backend/app/core/config.py`, `backend/app/main.py`, `backend/schema/schema.cypher`, `backend/app/api/v1/health.py`
- **Steps:**
  1. Copy the old `Gurusetu-backend` `main` into `backend/` without its `.git` folder. Delete `backend/uploads/` and any committed photos (SEC-14).
  2. Fix the Dockerfile: `CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000","--workers","1"]` (audit H6).
  3. Rewrite `config.py` with pydantic-settings fields for every variable in backend §8. Remove `CLOUDINARY_*` and `OPENAI_API_KEY`. At startup, check `len(JWT_SECRET_KEY) >= 32` and `len(NEO4J_PASSWORD) >= 12`, and raise with a clear message otherwise (SEC-10).
  4. Copy `docs/04-backend/schema.cypher` to `backend/schema/schema.cypher`. In the app lifespan, split it on `;` and run each statement. It is idempotent (`IF NOT EXISTS`).
  5. Add `api/v1/health.py` (API-040): run `RETURN 1` against Neo4j and return `{status, neo4j, llm_provider}`; 503 on failure.
  6. Write `docker-compose.yml` per environments §2: neo4j `5.26-community` with healthcheck, backend depending on healthy neo4j, frontend depending on healthy backend; volumes `neo4j_data` and `uploads`; `env_file: .env`.
  7. `cp docs/10-devops/env.example .env.example` at the root (the README and AGENTS.md reference it).
- **Done when:** the G0 health check passes on your machine, and on one teammate's machine after `git pull`.

### T0.P3.1 Import frontend and generate types (45 min)
- **Spec:** architecture §9, ux-flows §8
- **Files:** `frontend/**`, `frontend/Dockerfile`, `frontend/src/lib/types.ts`
- **Steps:**
  1. Copy the old `Gurusetu-frontend` `main` into `frontend/` without its `.git` folder.
  2. `npm ci && npx tsc --noEmit && npm run build`. The audit could not run these, so note any failures in `status.md` and fix only build blockers now.
  3. Write `frontend/Dockerfile` (node:20-alpine, build arg `NEXT_PUBLIC_API_BASE`, `next build` then `next start -p 3000`).
  4. `npx openapi-typescript docs/04-backend/openapi.yaml -o frontend/src/lib/types.ts`, and add the same command as `npm run gen:types`.
  5. Add `recharts` now (used in Phase 3) to avoid a lockfile conflict later.
- **Done when:** `npm run build` passes, and the frontend container serves `/login` (the old page is fine for now).

### T0.P1.1 Backend ML dependencies and model bake (45 min)
- **Spec:** architecture §4, ai-system §2.1 and §5, environments §2
- **Files:** `backend/requirements.txt`, `backend/Dockerfile`
- **Steps:**
  1. Add pinned versions of `sentence-transformers`, `anthropic` (latest at hour 0), `Pillow`, `imagehash`, `pypdfium2`, `rapidfuzz`, `openpyxl`, `python-multipart`, `pydantic-settings`. Remove `cloudinary` and `openai`.
  2. In the Dockerfile, install the CPU torch wheel before the requirements, then bake the model into `/models` (environments §2). Set `ENV HF_HOME=/models`.
  3. Verify inside the container: `python -c "from sentence_transformers import SentenceTransformer as S;m=S('sentence-transformers/all-MiniLM-L6-v2');print(m.get_sentence_embedding_dimension())"` prints `384`.
  4. If D-2 is yes, send one tiny Messages API call with `claude-opus-5-5` to confirm the key and model ID. Record the outcome in the decisions log. **Do not commit the key.**
- **Done when:** `384` is printed with the network off (the model was baked), and the key check is recorded.

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
| The old frontend doesn't build (never verified, audit §1) | Fix only build blockers. Delete broken mock pages now (they are deleted in Phase 1 anyway). |
| Torch wheel download is slow at the venue | One person builds the backend image first and shares it with `docker save \| docker load` via USB |
| No Anthropic key | `LLM_PROVIDER=none`; P1 hand-writes cache JSON in Phase 2 (`source:"cache"`) |
| D-1 is "no" | Start from empty FastAPI/Next.js scaffolds with the same structure (architecture §9); the spec is unchanged |
