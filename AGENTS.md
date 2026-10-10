# AGENTS.md: GuruSetu Verified Mentorship Graph

You are building a 15-hour hackathon product. Students prove skills with verified certificates and use them to find research guides. Faculty mentors log and track sessions, action items and issues. HOD and IQAC see live mentoring compliance and export draft accreditation evidence. The stack is FastAPI + Neo4j 5 + Next.js 14, repaired and extended from the old GuruSetu code.

## Read before writing code (in this order)
1. [docs/00-index.md](docs/00-index.md): document map, ID registry, assumptions, end-to-end scenario
2. [docs/01-product/prd.md](docs/01-product/prd.md): REQ-/NFR-/NG- with acceptance criteria. **NG- items are forbidden scope.**
3. [docs/02-architecture/architecture.md](docs/02-architecture/architecture.md): components, ADRs, project structure, import rules
4. [docs/04-backend/backend.md](docs/04-backend/backend.md) + [openapi.yaml](docs/04-backend/openapi.yaml) + [schema.cypher](docs/04-backend/schema.cypher): data, API, business rules, config
5. Then the document for your area: [ai-system.md](docs/06-ai/ai-system.md), [ux-flows.md](docs/05-frontend/ux-flows.md), [security-and-privacy.md](docs/08-security/security-and-privacy.md), [environments-and-deployment.md](docs/10-devops/environments-and-deployment.md), [test-strategy.md](docs/11-quality/test-strategy.md)

**What to build now:** [docs/phases/README.md](docs/phases/README.md) lists the phases, gates and task IDs. Open the current phase doc, take a task (`T<phase>.<person>.<n>`) and follow its steps and *Done when*. Update [docs/phases/status.md](docs/phases/status.md). Where a phase doc and the spec pack disagree on a fact, the spec pack wins; fix the phase doc.

## Hard rules
- **Contracts are the source of truth.** Field names and types come from `openapi.yaml`, and labels and keys from `schema.cypher`. Change the contract file first, then the code, in the same commit.
- **Priority:** build P0 before any P1, and P1 before P2. Do not build NG- items or roadmap items.
- **Security is P0.** Every route needs a Pydantic response model (never return `password_hash`, `embedding`, `file_path`). Role checks and scope checks go in `app/api/deps.py` (security §3–§4). Out of scope → 404, wrong role → 403.
- **Privacy:** session notes go only to their author. Issue text, notes and action text never appear in dashboards, exports, notifications or logs (REQ-015, SEC-15).
- **Cypher only in `backend/app/repos/`** (and `scripts/seed.py`), always parameterised (SEC-17).
- **The LLM extracts certificate fields only.** Trust, status and confidence are deterministic code (ai-system §3). Never give the model tools.
- **Thresholds are config** (backend §8), never literals. Dates follow architecture §5.
- **Every status change** writes a StatusEvent and the listed notifications, in the same transaction as the change (backend §5, §6.9).
- Mark seeded or simulated things `[MOCK]` in the UI ("Sample data") and in code comments.
- Use the IDs (REQ-, API-, SCR-, TEST-) in commit messages, test names and comments where they help traceability.

## Commands
```
cp docs/10-devops/env.example .env      # set NEO4J_PASSWORD, JWT_SECRET_KEY (+ ANTHROPIC_API_KEY or LLM_PROVIDER=none)
docker compose up -d --build
docker compose exec backend python -m scripts.seed --reset
docker compose exec -e TODAY_OVERRIDE=2026-10-10 backend pytest -q
ruff check backend && npm --prefix frontend run lint
npx @stoplight/spectral-cli lint docs/04-backend/openapi.yaml
npx openapi-typescript docs/04-backend/openapi.yaml -o frontend/src/lib/types.ts
```
Demo logins (synthetic): `aarav@`, `meera@`, `suresh@` (HOD), `kavya@` (IQAC) at `demo.gurusetu`, password `Demo@123`.

## Definition of done for any change
- The acceptance criteria of the REQ it implements pass, and its TEST- cases from test-strategy exist and are green.
- No new endpoint, field or screen without a REQ behind it. If one is needed, add the REQ to the PRD first.
- `pytest -q`, ruff, frontend lint and the spectral lint pass. The primary flow (PRD §8) still runs on a fresh seed.
