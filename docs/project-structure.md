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

## 2. Target tree (after Phase 0)

```
Guru-Setu-Revamp/
├─ AGENTS.md  CLAUDE.md  README.md  LICENSE
├─ docker-compose.yml          neo4j + backend + frontend           (P2)
├─ tools/
│   ├─ ownership.txt           who may edit which path
│   └─ check_ownership.py      run before every push
├─ docs/                       specification pack (this folder)
├─ backend/                    FastAPI, Python 3.12
│   ├─ Dockerfile  requirements.txt                                  (P1)
│   ├─ schema/schema.cypher    constraints + indexes, applied on startup (P2)
│   ├─ app/
│   │   ├─ main.py             auto-includes every router in api/v1/ (P2)
│   │   ├─ core/               config, database, security (JWT, bcrypt), errors, middleware
│   │   ├─ api/deps.py         current_user, require_role, scope checks
│   │   ├─ api/v1/             one router file per area (45 endpoints)
│   │   ├─ schemas/            generated.py (GEN, from openapi.yaml) + thin wrappers
│   │   ├─ services/           business rules and transactions
│   │   ├─ repos/              ALL Cypher. match_repo.py and ml_repo.py are P1's
│   │   └─ ml/                 embeddings, concepts, extraction (LLM), verification, trust, scorer (P1)
│   ├─ scripts/                seed.py, eval_match.py, build_extraction_cache.py, check_seed.py
│   ├─ seed/                   JSON seed data, certificates/, demo_uploads/, labels/
│   ├─ extraction_cache/       <sha256>.json per seed certificate (committed)
│   └─ tests/                  pytest
└─ frontend/                   Next.js 14 + TypeScript + Tailwind     (P3 default)
    └─ src/{app,components,lib,fixtures,hooks}/
```

Import rules ([architecture §9](02-architecture/architecture.md)): `api/v1` → `services` → `repos`; `ml` may call only `repos/ml_repo.py` and `repos/match_repo.py`; Cypher exists only in `repos/` and `scripts/seed.py`.

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
