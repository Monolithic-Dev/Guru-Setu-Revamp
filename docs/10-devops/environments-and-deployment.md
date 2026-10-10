# Environments and Deployment
Purpose:      Let anyone on the team, or a coding agent, run the whole system and the demo from a clean laptop with one set of commands.
Audience:     All builders; the person running the demo.
Depends on:   docs/02-architecture/architecture.md, docs/04-backend/backend.md
Inputs used:  NFR-04, NFR-08, NFR-10, ADR-04, ADR-13, audit H6 (broken Dockerfile and env), RISK-08
Status:       Draft v1 | assumptions in this document: A-05, A-06, A-22

## 0. Local quickstart (clone to running in under 15 minutes)

**Prerequisites:**

| Tool | Version | Needed for |
|---|---|---|
| Git | any 2.x | clone |
| Docker Desktop with Compose v2 | 4.x (Compose ≥ 2.20) [VERIFY: docs.docker.com/compose/release-notes] | everything |
| RAM / disk | ≥ 8 GB RAM, ≥ 8 GB free disk (torch CPU + model + Neo4j) | containers |
| Python | 3.12 | only for `tools/check_ownership.py` and lints outside containers |
| Node.js | 20 LTS | only for frontend lints and type generation outside containers |

**Commands:**
1. `git clone <repo> && cd Guru-Setu-Revamp`
2. `cp docs/10-devops/env.example .env`
3. Edit `.env`: set `NEO4J_PASSWORD` (≥ 12 chars) and `JWT_SECRET_KEY` (`python -c "import secrets;print(secrets.token_urlsafe(48))"`); set `ANTHROPIC_API_KEY`, or `LLM_PROVIDER=none`.
4. `docker compose up -d --build`. The first build downloads torch and the model, about 8–10 min on a good connection; with cached images it takes ≤ 5 min (NFR-08).
5. `docker compose exec backend python -m scripts.seed --reset` (≤ 60 s, NFR-10)
6. Open http://localhost:3000 and log in as `aarav@demo.gurusetu` / `Demo@123`.
7. Run the tests: `docker compose exec -e TODAY_OVERRIDE=2026-10-10 backend pytest -q`. A single test: `… pytest -q tests/test_security.py::test_03_unauthenticated`.

## 1. Environments

| ID | Name | Where / URL | Purpose | Data | Access | Differences |
|---|---|---|---|---|---|---|
| ENV-01 | Local dev (also the test environment, A-23) | Each builder's laptop: http://localhost:3000, http://localhost:8000/api/v1, Neo4j browser http://localhost:7474 | Build and test | Synthetic seed | The builder | `TODAY_OVERRIDE=2026-10-10` for tests; `LLM_PROVIDER=anthropic` (key in `.env`) or `none` |
| ENV-02 | Demo | The presenting laptop, same localhost URLs | Stage demo and judging | Synthetic seed, re-anchored with `--anchor-date` | The presenter | Same images as ENV-01; `LLM_PROVIDER=none` unless venue Wi-Fi is tested; fresh `seed --reset` before each run |
| ENV-03 | Hosted (optional) | Render (backend) and Netlify (frontend) on new accounts, Neo4j Aura [A-22]; URLs assigned on deploy | Only if the rules require a URL (D-5) | Synthetic seed | Public link, demo accounts | TLS at the platform edge; `CORS_ORIGINS` set to the Netlify URL; not required for P0 |

There is no separate test, staging or production environment. Real data is out of scope (NG-03).

## 1.1 Infrastructure

- **Hosting choice:** local Docker Compose on one laptop. The demo must work offline (NFR-04) and with no account dependencies. ENV-03 is optional.
- **Resources (per laptop):**

| Service | Memory | Notes |
|---|---|---|
| neo4j | ≤ 1.5 GB (`NEO4J_server_memory_heap_max__size=1G`, `NEO4J_server_memory_pagecache_size=256M`) | Seed is < 10k nodes |
| backend | ≈ 1.5 GB (torch CPU + MiniLM) | 1 uvicorn worker (A-13) |
| frontend | ≈ 300 MB | `next start` |

- **Networking:** the Compose default bridge network. Only ports 3000, 8000 and 7474/7687 are published, bound to `127.0.0.1`. No domain and no TLS for ENV-01/02.
- **Managed services:** none for ENV-01/02. ENV-03 would use the free tiers of Render, Netlify and Neo4j Aura [VERIFY: each provider's current free-tier limits].
- **Cost:** USD 0 for infrastructure. LLM spend is ≤ USD 5 total (NFR-09, ai-system §7).

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

## 6. Release

| Item | Rule |
|---|---|
| Build artifact | The git tag plus Docker images built locally from it (`docker compose build`). No registry. |
| Versioning | Tags `rc1` (13:15 code freeze) and `genesis-submission` (the final submitted commit). |
| Schema migration order | `schema.cypher` is applied idempotently at API startup (constraints and indexes only), then `scripts.seed --reset`. There is no data migration: all data is synthetic and re-seeded. |
| Downtime | Acceptable (demo system). A release is `docker compose up -d --build` followed by a reseed. |
| Rollback | `git checkout <previous tag> && docker compose up -d --build && docker compose exec backend python -m scripts.seed --reset` (about 2 min with cached layers). |
| Repo hygiene | The repo must contain no `.env`, no real data and no `uploads/` (SEC-10, SEC-14). |

**Smoke-test checklist (after every release, rehearsal or rollback):**
1. `curl -s localhost:8000/api/v1/health` returns 200 with `neo4j: "up"`.
2. All 4 personas log in and land on their home screen.
3. API-015 for Aarav on `op-edge-ai` returns a score of 38–50 with verdict `close`.
4. Upload `seed/demo_uploads/aarav_cv_workshop.png`: status `certified` in ≤ 2 s (cache hit).
5. Meera's SCR-06 shows 13 mentees with 3 flagged.
6. API-033 as Suresh returns 200; API-035 downloads an XLSX whose README!A1 starts with "DRAFT".

## 7. Backups and recovery

- **What is backed up:** nothing beyond git. Every runtime datum is synthetic and reproducible from `backend/seed/` plus `scripts.seed`. The only non-reproducible artifacts are the extraction cache, the eval labels and the results, and all of them are committed (`backend/extraction_cache/`, `backend/seed/labels/`, `docs/plan/eval-results.md`).
- **Targets:** RPO is not applicable (no user data). RTO is ≤ 5 minutes (compose up plus seed).
- **Restore drill:** TEST-53 (clean clone to running) is the drill. It is run at the core freeze and on demo eve.

## 8. Domains not included

- **CI/CD:** skipped. With a 15-hour, 4-person build, the checks run manually (§4) at each gate (docs/phases), and `tools/check_ownership.py` runs before every push. A pipeline would cost about 1 hour to set up and would never deploy.
- **Observability:** merged here and in backend §11. Logs are JSON lines with `request_id` (architecture §5), and liveness and readiness are API-040. There are no metrics, traces or alerts: one process on one laptop, watched by its operator.
- **Distribution:** skipped. Nothing is packaged or published.

## Verify

1. On a clean clone: `cp docs/10-devops/env.example .env`, set the two secrets, then run `docker compose up -d --build` and `docker compose ps`. All 3 services report healthy.
2. `curl -s localhost:8000/api/v1/health` → `{"status":"ok","neo4j":"up","llm_provider":"none"}` (with `LLM_PROVIDER=none`).
3. `docker compose exec backend python -m scripts.seed --reset` finishes in ≤ 60 s. http://localhost:3000/login loads, and `aarav@demo.gurusetu` / `Demo@123` logs in.
4. Disconnect the network, restart the backend, and upload `seed/demo_uploads/aarav_cv_workshop.png`: it becomes `certified` (cache hit, no model download).
