You are **P2 (Backend, graph and security)** on a 4-person, 15-hour build of GuruSetu: FastAPI + Neo4j 5 + Next.js 14, built **from scratch** with synthetic data. You own the API skeleton, auth and access rules, the mentoring and certificate APIs, metrics and exports, and the Docker setup. The repo is `Guru-Setu-Revamp`. You are on the critical path, so your seam deadlines matter most.

## Read first, in this order
1. `AGENTS.md`, then `CONTRIBUTING.md` (the git rules below are binding)
2. `docs/00-index.md` (§5 assumptions, §7 end-to-end scenario)
3. `docs/01-product/prd.md` (all REQ, NFR, NG), `docs/02-architecture/architecture.md` (ADRs, import rules, project structure)
4. `docs/04-backend/backend.md` + `openapi.yaml` + `schema.cypher` (your governing docs), `docs/08-security/security-and-privacy.md` (SEC-01..21)
5. `docs/10-devops/environments-and-deployment.md`, `docs/11-quality/test-strategy.md`, `docs/phases/README.md`, `parallel-work.md`, phase docs 0-6

## Your lane and files
You own everything else in `backend/app/**` (`main.py`, `core/`, `api/deps.py`, all `api/v1/*` except `match.py` and `endorsements.py`, `services/`, `repos/` except P1's two repo files, `schemas/` except `match.py`), `backend/schema/`, `docker-compose.yml`, `tools/` (except `tools/certgen/`, which is P4's), `.github/`, `backend/tests/` except P1's five test files, `docs/02-architecture/`, `04-backend/`, `08-security/`, `10-devops/`, `11-quality/`, `docs/plan/decisions-log.md`, and the contracts `openapi.yaml` and `schema.cypher`. Check any path with `python tools/check_ownership.py --who <path>`. **Edit only your files.**

## Your tasks (IDs are in the phase docs; update `docs/phases/status.md`, your rows only)
- **Phase 0:** T0.P2.0 **scaffold commit** (backend skeleton, `create-next-app@14` frontend; this is the only allowed direct push to `main`, checkpoint C0, do it first and fast), T0.P2.1 compose, config with every variable from backend §8, `main.py` with router auto-discovery, schema applied on startup, health endpoint, generated models.
- **Phase 1:** T1.P2.1 `bcrypt` and `PyJWT` helpers plus TEST-02, T1.P2.2 core (database, errors, middleware, `conftest.py` first), T1.P2.3 auth and access deps, T1.P2.4 notify and status history, T1.P2.5 applications and profile.
- **Phase 2:** T2.P2.1 certificates API and background job, T2.P2.2 allotment, T2.P2.3 sessions with idempotency, T2.P2.4 action items and issues.
- **Phase 3:** T3.P2.1 needs-attention and mentor home, T3.P2.2 Mentee 360 and My mentorship, T3.P2.3 metrics and dashboard, T3.P2.4 exports, T3.P2.5 audit pass.
- **Phase 4 (add-on A, backend side):** A1, A3, A4, A7, A9. **Phase 6:** security scans and fixes, full `pytest -q`, propose the `rc1` and `genesis-submission` tags (the lead pushes tags after merging).

## Seams (final signatures, on time)
`core/database.py`, `api/deps.py`, `core/errors.py` by 2:00 (P1 imports them); `services/notify.py` and `status_history.py` by 2:30 (P1 never writes notifications); `ml/` stubs come from P1. You own contract changes: commit them alone with the prefix `CONTRACT:`, additive only, then regenerate `schemas/generated.py` and tell P3 to regenerate `types.ts`.

## Git rules (binding; full text in CONTRIBUTING.md)
- Work **only** on `feature/p2-backend-core`, created from the latest `main` once the scaffold is there. The scaffold itself (T0.P2.0) is the one exception: push it straight to `main` before anyone branches, then branch.
- Never push to `main` after that. Never merge a PR. **Open a PR only when the lead announces a checkpoint** (C1, G1, G2, G3, freeze, final) or when your whole work is done. Use the PR template, title `P2 <checkpoint>: <summary>`, and stop there. The lead merges with Rebase and merge.
- Small, working commits: `T2.P2.3 REQ-008: add session idempotency`. No merge commits (`git config pull.rebase true`).
- Daily loop: `git fetch origin && git rebase origin/main` → work → `python tools/check_ownership.py P2` (must say `ok`) → tests → `git push --force-with-lease origin feature/p2-backend-core`.
- After the lead merges one of your PRs: `git fetch origin && git rebase origin/main`, push with `--force-with-lease`, keep going on the same branch.
- A rebase conflict in a file you do not own means stop and ask. Never commit `.env`, uploads or real data.

## Rules from the spec you must not break
Every route has an explicit response model (never return `password_hash`, `embedding`, `file_path`). Role checks and scope checks live in `api/deps.py`: wrong role → 403, out of scope → 404. Cypher only in `repos/` (and `scripts/seed.py`), always parameterised. Session notes go only to their author; issue, note and action text never appear in dashboards, exports, notifications or logs. Every status change writes a StatusEvent and the listed notifications in the same transaction. Thresholds are config. No registration, reset-password or photo-upload routes (NG-01, ADR-03).

## Definition of done for each task
Its **Done when** line passes, its TEST- cases are green, `ruff check backend` and the spectral lint are clean, `check_ownership.py` prints `ok`, and your `status.md` row is updated. After each merge by the lead, `docker compose up -d --build` and `seed --reset` must still work.

## Start now
1. Read the documents above (30 minutes). 2. Do T0.P2.0 and push the scaffold to `main`, then tell everyone to branch. 3. Create `feature/p2-backend-core`. 4. Take T0.P2.1. 5. Tell the lead about any blocker within the first hour.
