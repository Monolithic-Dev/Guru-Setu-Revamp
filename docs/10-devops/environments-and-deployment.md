# Environments and Deployment
Purpose:      Let anyone on the team, or a coding agent, run the whole system and the demo from a clean laptop with one set of commands.
Audience:     All builders; the person running the demo.
Depends on:   docs/02-architecture/architecture.md, docs/04-backend/backend.md
Inputs used:  NFR-04, NFR-08, NFR-10, ADR-04, ADR-13, audit H6 (broken Dockerfile and env), RISK-08
Status:       Draft v1 | assumptions in this document: A-05, A-06, A-22

---

## 1. Environments

| ID | Name | Where | Purpose | Differences |
|---|---|---|---|---|
| ENV-01 | Local dev | Each builder's laptop, Docker Compose | Build and test | `TODAY_OVERRIDE=2026-10-10`, `LLM_PROVIDER=anthropic` (key in `.env`) or `none` |
| ENV-02 | Demo | The presenting laptop, Docker Compose | Stage demo and judging | Same images as ENV-01; `LLM_PROVIDER=none` unless venue Wi-Fi is tested; fresh `seed --reset` before each run |
| ENV-03 | Hosted (optional) | The old deployment targets (Render backend, Netlify frontend) [A-22] | Only if the rules require a URL | Neo4j Aura; TLS at the platform edge; synthetic data only; not required for P0 |

There is no staging and no production. Real data is out of scope (NG-03).

## 2. Docker Compose (`docker-compose.yml` at repo root)

| Service | Image / build | Ports | Volumes | Healthcheck | Depends on |
|---|---|---|---|---|---|
| neo4j | `neo4j:5.26-community` [VERIFY: tag exists on Docker Hub] | 7474, 7687 | `neo4j_data:/data`, `./backend/schema:/schema:ro` | `cypher-shell -u neo4j -p $NEO4J_PASSWORD "RETURN 1"` every 5 s | — |
| backend | `./backend/Dockerfile` (python:3.12-slim) | 8000 | `uploads:/data/uploads` | `curl -f localhost:8000/api/v1/health` | neo4j healthy |
| frontend | `./frontend/Dockerfile` (node:20-alpine, `next build` then `next start`) | 3000 | — | `wget -qO- localhost:3000/login` | backend healthy |

**Environment wiring:**
- `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}` for the neo4j service.
- The backend reads the `.env` file.
- The frontend gets `NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1` at build time.

**Backend Dockerfile requirements:**
- `CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000","--workers","1"]` (fixes audit H6; A-13).
- A build step pre-downloads MiniLM into `/models`: `python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', cache_folder='/models')"`, so the demo needs no network (RISK-08, NFR-04).
- CPU-only torch wheel (audit M8): `pip install torch --index-url https://download.pytorch.org/whl/cpu` before `requirements.txt` [VERIFY: current CPU wheel index URL].
- `backend/extraction_cache/` and `backend/seed/` are copied into the image.

## 3. Configuration

Copy [env.example](env.example) to `.env` at the repo root. Every variable is defined once in [backend.md §8](../04-backend/backend.md). Required before first run: `NEO4J_PASSWORD` (≥ 12 chars), `JWT_SECRET_KEY` (≥ 32 chars; generate with `python -c "import secrets;print(secrets.token_urlsafe(48))"`), and `ANTHROPIC_API_KEY` if `LLM_PROVIDER=anthropic`.

## 4. Commands

| Task | Command | Expected |
|---|---|---|
| First run | `cp docs/10-devops/env.example .env` → edit the secrets → `docker compose up -d --build` | 3 services healthy in ≤ 5 min with images cached (NFR-08) |
| Seed / reset | `docker compose exec backend python -m scripts.seed --reset` | "Seeded: 56 users, 12 openings, 40 sessions…" in ≤ 60 s (NFR-10) |
| Build extraction cache | `docker compose exec backend python -m scripts.build_extraction_cache seed/certificates seed/demo_uploads` | One JSON per file in `extraction_cache/`; commit them |
| Backend tests | `docker compose exec -e TODAY_OVERRIDE=2026-10-10 backend pytest -q` | All pass |
| Match eval | `docker compose exec backend python -m scripts.eval_match` | Markdown table (EVAL-03) |
| Lint | `ruff check backend` · `npm --prefix frontend run lint` | 0 errors |
| Contract lint | `npx @stoplight/spectral-cli lint docs/04-backend/openapi.yaml` | 0 errors |
| Generate TS types | `npx openapi-typescript docs/04-backend/openapi.yaml -o frontend/src/lib/types.ts` | File regenerated; `tsc --noEmit` passes |
| Security scans | `pip-audit -r backend/requirements.txt` · `npm --prefix frontend audit --audit-level=high` · `gitleaks detect` | SEC-10, SEC-16 |
| Logs | `docker compose logs -f backend` | JSON lines with `request_id` |
| Stop / wipe | `docker compose down` · `docker compose down -v` (deletes DB and uploads) | — |

## 5. Demo-day runbook (ENV-02)

1. The evening before: `docker compose pull && docker compose build`. Run the full primary flow (PRD §8) twice with `LLM_PROVIDER=none` and the network off (TEST-52).
2. Set `TODAY_OVERRIDE=2026-10-10` only if the demo date differs and the seeded flags must hold. Otherwise leave it empty, and re-date the seed by running `python -m scripts.seed --reset --anchor-date <demo date>`. The seed shifts all dates relative to the anchor, which defaults to 2026-10-10.
3. Ten minutes before: `docker compose up -d`, `seed --reset`, then log in as each persona in separate browser profiles (student, faculty, HOD, IQAC).
4. Keep the backup video (team plan §13) on the desktop.

## 6. Release and distribution

There are no releases. The submission is the repo at a tagged commit, `genesis-submission`, plus the running demo. The repo must contain no `.env`, no real data and no `uploads/` (SEC-10, SEC-14).

## Verify

1. On a clean clone: `cp docs/10-devops/env.example .env`, set the two secrets, then run `docker compose up -d --build` and `docker compose ps`. All 3 services report healthy.
2. `curl -s localhost:8000/api/v1/health` → `{"status":"ok","neo4j":"up","llm_provider":"none"}` (with `LLM_PROVIDER=none`).
3. `docker compose exec backend python -m scripts.seed --reset` finishes in ≤ 60 s. http://localhost:3000/login loads, and `aarav@demo.gurusetu` / `Demo@123` logs in.
4. Disconnect the network, restart the backend, and upload `seed/demo_uploads/aarav_cv_workshop.png`: it becomes `certified` (cache hit, no model download).
