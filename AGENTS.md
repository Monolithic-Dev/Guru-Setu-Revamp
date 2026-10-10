# AGENTS.md: GuruSetu Verified Mentorship Graph

## Commands
```
cp docs/10-devops/env.example .env                                   # set NEO4J_PASSWORD, JWT_SECRET_KEY; ANTHROPIC_API_KEY or LLM_PROVIDER=none
docker compose up -d --build                                         # build + run (schema is applied at API startup; no migrations)
docker compose exec backend python -m scripts.seed --reset           # seed synthetic data (add --anchor-date YYYY-MM-DD for demo day)
docker compose exec -e TODAY_OVERRIDE=2026-10-10 backend pytest -q   # all backend tests
docker compose exec -e TODAY_OVERRIDE=2026-10-10 backend pytest -q tests/test_security.py::test_03_unauthenticated   # one test
ruff check backend                                                   # backend lint
npm --prefix frontend run lint && npx --prefix frontend tsc --noEmit # frontend lint + type-check
npx @stoplight/spectral-cli lint docs/04-backend/openapi.yaml        # contract lint
npm --prefix frontend run gen:types                                  # regenerate frontend/src/lib/types.ts
python tools/check_ownership.py P<n>                                 # before every push
```
Demo logins (synthetic): `aarav@`, `meera@`, `suresh@` (HOD), `kavya@` (IQAC) at `demo.gurusetu`, password `Demo@123`.

## Project
A 15-hour hackathon build. Students verify certificates and get explained fit for research openings. Faculty mentors log and track sessions, action items and issues. HOD and IQAC get live compliance and draft NAAC evidence exports. FastAPI + Neo4j 5 + Next.js 14, **built from scratch** (no old GuruSetu code is copied; decision D-1). Start at [docs/00-index.md](docs/00-index.md).

## Where things live
| Path | What | Governing doc |
|---|---|---|
| `backend/app/api/v1/` | Routers, auto-discovered by `main.py` | [backend.md §4](docs/04-backend/backend.md), [openapi.yaml](docs/04-backend/openapi.yaml) |
| `backend/app/services/`, `repos/` | Business rules / Cypher | backend.md §5–§7, [schema.cypher](docs/04-backend/schema.cypher) |
| `backend/app/ml/` | Extraction, verification, embeddings, scorer | [ai-system.md](docs/06-ai/ai-system.md) |
| `backend/seed/`, `scripts/` | Synthetic data, seed and eval scripts | backend.md §10 |
| `frontend/src/app/` | Screens SCR-01..16 | [ux-flows.md](docs/05-frontend/ux-flows.md) |
| access and visibility rules | — | [security-and-privacy.md §4](docs/08-security/security-and-privacy.md) |
| tests and traceability | — | [test-strategy.md](docs/11-quality/test-strategy.md) |
| what to build now | Task `T<phase>.<person>.<n>` | [docs/phases/README.md](docs/phases/README.md), status in `docs/phases/status.md` |

## Conventions
- JSON and Python `snake_case`; Neo4j labels `PascalCase`, relationships `UPPER_SNAKE`.
- Errors are `application/problem+json` with a stable `code` (backend §3.1). Raise `ApiError(code, status, detail)`.
- Import rules: `api → deps, schemas, services`; `services → repos, ml`; Cypher only in `repos/` and `scripts/seed.py`, always parameterised.
- Thresholds come from config (backend §8). Calendar dates are Asia/Kolkata; timestamps are UTC with a `Z` suffix.
- Commit messages: `T2.P2.3 REQ-008: <what>`.

## Boundaries
**Always:** run your tests before finishing; build P0 before P1 before P2; write a StatusEvent and the listed notifications in the same transaction as any status change; update the governing doc when behaviour changes; edit only files your owner id owns (`tools/ownership.txt`).

**Ask first:** adding a dependency (P1 owns `requirements.txt`, P3 owns `package.json`); changing `openapi.yaml` or `schema.cypher` (P2; additive only, docs/phases/parallel-work.md §5); changing a threshold default or a fit weight.

**Never:** commit `.env`, uploads or real data; hand-edit `schemas/generated.py` or `lib/types.ts`; return `password_hash`, `embedding` or `file_path`; put note, issue or action text in dashboards, exports, notifications or logs; let the LLM decide status, trust or confidence; build NG- items from the PRD; change files outside your task.

## Definition of done
The REQ's acceptance criteria pass through the TEST- IDs in test-strategy §6; ruff, frontend lint, `tsc` and the spectral lint are green; `check_ownership.py` passes; the index §7 scenario still runs on a fresh seed.

## Known traps
- **403 vs 404:** wrong role → 403; right role but outside scope → 404, so existence never leaks (security §3–§4). HOD on API-027 is 403.
- **Private fields are omitted, not null:** `notes`, issue `text` and `duplicate_of` are left out of the response when the caller may not see them.
- **"Today" is seeded:** tests need `TODAY_OVERRIDE=2026-10-10`, and the demo needs `seed --anchor-date`. Otherwise the needs-attention flags and compliance numbers shift.
- **Fit score rounding:** each component is rounded first, then summed, so `semantic + skill + concept == score` exactly (ai-system §4).
