# Spec Pack Index: GuruSetu Verified Mentorship Graph
Purpose:      Entry point to the specification pack: what exists, where each fact lives, what is assumed, and the one scenario that proves the build works.
Audience:     The team, reviewers and coding agents (start at AGENTS.md, then here).
Depends on:   all documents below
Inputs used:  docs/plan/prd-v2-and-15h-plan.md (PRD v2 + 15-hour plan), gurusetu-pramaan-concept.md, gurusetu-enterprise-vision.md, GENESIS-GuruSetu-Audit-and-Proposal.md (these three are kept outside this repo)
Status:       Draft v1 | assumptions log: §5

---

## 1. Brief as understood

- **Project:** a web app (FastAPI + Neo4j + Next.js 14) built from scratch for the Genesis hackathon, Campus Problems track (the concept comes from the earlier GuruSetu prototype; no old code is reused, D-1).
- **Users:** students, faculty (as assigned mentors and as research guides), HOD and IQAC in one department.
- **Core:**
  - certificate upload → LLM extraction → deterministic verification → trust-weighted skills;
  - an explained Fit Check for research openings, with apply and decide;
  - the digital mentor-mentee system: allotment, sessions, confirmation, action items, issues;
  - tracking: mentor home flags and Mentee 360;
  - a coordinator dashboard and draft XLSX evidence exports with no private notes.
- **Constraints:** a 15-hour time box, 4 people (A-01), synthetic data only, security requirements (SEC-) built in from the first commit.
- **Mocked:** academics, accounts, certificates, criterion codes (PRD §13).
- **Out of scope:** everything on the enterprise roadmap (PRD NG-01..15).

## 2. Document map

| # | Document | Contains | Home of IDs |
|---|---|---|---|
| 1 | [01-product/prd.md](01-product/prd.md) | Goals, roles, personas, glossary, stories, requirements + acceptance criteria, NFRs, primary flow, metrics, risks, mocks | G, NG, US, REQ, AC, NFR, RISK |
| 2 | [02-architecture/architecture.md](02-architecture/architecture.md) | Context, components, key flows, stack, cross-cutting, decisions, project structure | CMP, ADR |
| 3 | [06-ai/ai-system.md](06-ai/ai-system.md) | Extraction (model, schema, prompt, cache), verification + confidence, fit formula, embeddings, safety, cost, eval plan | MDL, EVAL |
| 4 | [04-backend/backend.md](04-backend/backend.md) + [openapi.yaml](04-backend/openapi.yaml) + [schema.cypher](04-backend/schema.cypher) | Data model, API conventions and endpoints, business rules, metrics, config, jobs, seed | ENT, API, JOB, MET |
| 5 | [05-frontend/ux-flows.md](05-frontend/ux-flows.md) | IA, flows, states and copy, a11y, screens, wireframes, components, client state | FLOW, SCR |
| 6 | [08-security/security-and-privacy.md](08-security/security-and-privacy.md) | Auth, scope and visibility rules, SEC requirements, residual risks, threat model, compliance notes | SEC, THR |
| 7 | [10-devops/environments-and-deployment.md](10-devops/environments-and-deployment.md) + [env.example](10-devops/env.example) | Environments, compose, commands, demo runbook | ENV |
| 8 | [11-quality/test-strategy.md](11-quality/test-strategy.md) | Test cases, failure modes, manual QA checklist | TEST, FM |
| 9 | [../AGENTS.md](../AGENTS.md) (+ `CLAUDE.md` → `@AGENTS.md`) | Agent entry: read order, hard rules, commands, definition of done | — |
| — | [project-structure.md](project-structure.md) | Target repo tree, ownership, end-to-end data flow, keys and manual setup, open flaws | — |
| — | [plan/prd-v2-and-15h-plan.md](plan/prd-v2-and-15h-plan.md) | Demo story, disclosure, pitch material (not part of the spec pack) | — |
| — | [phases/](phases/README.md) | Phase-wise build plan: tasks `T<phase>.<person>.<n>`, gates G0–G3, add-ons, freeze; [parallel-work.md](phases/parallel-work.md) + `tools/ownership.txt` for conflict-free work | Task IDs |

The spec pack itself holds no schedules. The hour-by-hour build plan lives in [phases/README.md](phases/README.md), with phase docs 0–6 and a live [status board](phases/status.md). It refines the team plan in `docs/plan/` §13.

## 3. Document plan (domains 1–15)

| # | Domain | Decision | Path | Trigger or reason |
|---|---|---|---|---|
| 1 | Product and requirements | include (personas + glossary as sections) | 01-product/prd.md | Always |
| 2 | Architecture and structure | include (ADRs + project structure as sections) | 02-architecture/architecture.md | Always; repair-vs-rewrite and datastore decisions |
| 3 | Data and persistence | merge into #4 | 04-backend/backend.md, schema.cypher | Neo4j graph with ~20 entities; small project → merged |
| 4 | Backend and API | include | 04-backend/backend.md, openapi.yaml | FastAPI server, 45 endpoints, background job |
| 5 | Frontend and UX | include (screens, components, client state as sections) | 05-frontend/ux-flows.md | 16 screens across 4 roles |
| 6 | AI, LLM and agents | include (eval plan as section; drafted before #4 because P0 needs it) | 06-ai/ai-system.md | Vision LLM extraction (REQ-001), embeddings + scorer (REQ-004) |
| 7 | ML training and serving | skip | — | No model is trained; MiniLM is used pretrained, and its eval is EVAL-03 in #6 |
| 8 | Data science and analytics | merge into #4 §7 | 04-backend/backend.md | Dashboard metrics only (MET-); no experiments or pipelines |
| 9 | Security, privacy and compliance | include (threat model + compliance as sections) | 08-security/security-and-privacy.md | Personal and sensitive mentoring data, uploads, untrusted text into an LLM, audit criticals C1–C3 |
| 10 | Integrations | merge into #6 (Anthropic) and #7 (none else) | — | The only third party is the Anthropic API; Cloudinary removed (ADR-13) |
| 11 | DevOps, environments, release | include (short) | 10-devops/environments-and-deployment.md | Always; a working Dockerfile and env from hour 0 |
| 12 | Testing and quality | include (failure modes + manual QA as sections) | 11-quality/test-strategy.md | Always |
| 13 | Project-type specials | skip | — | No library API, game, contract or hardware |
| 14–15 | Agent entry file + index | include | AGENTS.md, CLAUDE.md, 00-index.md | Always |

**Drafting order used:** PRD → architecture → AI system → backend (data + API) → frontend → security → DevOps → tests → AGENTS.md → index.

**Size:** 10 Markdown files (excluding CLAUDE.md), plus 3 contract files (`openapi.yaml`, `schema.cypher`, `env.example`), within the 6–10 target for a 15-hour, 4-person build.

## 4. ID registry

| Prefix | Meaning | Home | Range used |
|---|---|---|---|
| G / NG | Goal / non-goal | PRD §2 | G-01..05 / NG-01..15 |
| US | User story | PRD §5 | US-01..18 |
| REQ / AC | Requirement / acceptance criterion | PRD §6 | REQ-001..038 (all used) |
| NFR | Non-functional requirement | PRD §7 | NFR-01..10 |
| RISK | Project risk | PRD §11 | RISK-01..09 |
| A | Assumption | this file §5 | A-01..23 |
| CMP / ADR | Component / decision | architecture §2, §8 | CMP-01..16 / ADR-01..13 |
| MDL / EVAL | Model / eval set | ai-system §1, §10 | MDL-01..04 / EVAL-01..04 |
| ENT | Entity / relationship | backend §2 (merged data domain) | ENT-01..21 |
| API | Endpoint | backend §4, openapi.yaml `x-id` | API-001..045 |
| JOB | Background job | backend §9 | JOB-01..02 |
| MET | Metric | backend §7 (merged analytics domain) | MET-01..12 |
| FLOW / SCR | Flow / screen | ux-flows §3, §6 | FLOW-01..11 / SCR-01..16 |
| SEC / THR | Security requirement / threat | security §5, §10 | SEC-01..21 / THR-01..14 |
| ENV | Environment | environments §1 | ENV-01..03 |
| TEST / FM | Test / failure mode | test-strategy §2, §4 | TEST-01..57 (gaps unused) / FM-01..13 |

## 5. Assumptions log

The three with the largest effect if wrong are marked ★. Correct these first.

| ID | Assumption | Where used | If wrong |
|---|---|---|---|
| A-01 ★ | Team of 4, about 15 working hours each | PRD §10, test strategy | Use the 2–3-person cut in the team plan §13.4 |
| A-02 | Stack chosen: FastAPI, Neo4j 5, Next.js 14 (kept from the earlier prototype's stack because the team knows it) | Architecture §4 | Re-plan ADR-01/02 |
| A-03 | HOD and IQAC share one Coordinator area | PRD §3, ux-flows | Split SCR-11 by role |
| A-04 | No self-signup; seeded accounts only | NG-01, ADR-03 | Rebuild a secured registration flow (not specced) |
| A-05 ★ | **Decided: build from scratch.** No old code is copied; `backend/` and `frontend/` are scaffolded at hour 0. The old repos are not needed. | ADR-01, project structure | If the team later wants old code, reuse is allowed only after the Genesis rules are confirmed |
| A-06 | The demo runs locally via Docker Compose; no hosted URL required | ENV-02 | Use ENV-03 (Render/Netlify + Aura) |
| A-07 | One department (CSE) in the seed | NG-09, seed | Add departments to the seed; the model already supports it |
| A-08 | The current term comes from seeded Term dates or `CURRENT_TERM_ID` | ENT-07, MET- | Set `CURRENT_TERM_ID` |
| A-09 ★ | LLM use is allowed by the rules; an Anthropic API key is available; the Python SDK is used | ADR-08, MDL-01 | Run `LLM_PROVIDER=none` (cache + manual entry); say so in the pitch |
| A-10 | Trust weights 0.40/0.85/1.00 and fit weights 0.25/0.60/0.15 are starting values, tuned only on EVAL-03 before the core freeze | ai-system §4 | Retune; update the AC-004.1 range and TEST-18/19 together |
| A-11 | Seed scale ≤ 60 students, 12 openings, ≤ 1,000 certificates | Backend access patterns, NFR-01 | Add pagination and indexes |
| A-12 | Tracking thresholds of 45 / 14 / 7 days | Backend §6.4, §8 | Change config values only |
| A-13 | One uvicorn worker is enough | Architecture §5 | Rate limiter and BackgroundTasks need a shared store |
| A-14 | MiniLM on CPU embeds one text in < 50 ms | ai-system §5 | Recompute embeddings asynchronously |
| A-15 | NAAC criterion codes 2.3.3 (mentoring ratio) and 5.3.1 (awards) are the right drafts | ENT-13 | Update `Criterion` seed rows |
| A-16 | The seed and SIMILAR_TO overrides put Aarav's fit at 38–50 before and ≥ 65 after the demo uploads | AC-004.1, TEST-19 | Tune the seed, not the formula |
| A-17 | An ELA threshold of 12.0 flags the planted edited image and not the clean ones | ai-system §3 | Tune on the seed files, or leave TAMPER_CHECK disabled |
| A-18 | Relationship property indexes work in Neo4j 5.26 Community | schema.cypher | Drop those two indexes (performance only) |
| A-19 | Idempotency keys checked for a 24 h age on read need no cleanup job | ENT-21 | Delete old keys in the seed reset |
| A-20 | Frontend copy uses default threshold numbers rather than fetching config | ux-flows §4.3 | Add the thresholds to API-002 |
| A-21 | `bcrypt` (used directly, cost 12) and laptop disk encryption are acceptable for a synthetic-data demo | Security §2, §7 | Use a managed identity provider (out of scope) |
| A-22 | Render/Netlify (new accounts) are usable for an optional hosted demo | ENV-03 | Local demo only |
| A-23 | Tests run against the compose Neo4j and reseed per test session | Test strategy §1 | Add a separate test Neo4j service on port 7688 |

**Scratch build and the "audit" references:** with a from-scratch build, the old-code audit (kept outside this repo) is not a task list. References such as "audit H6" or "fixes audit C3" in the docs name lessons already built into the spec, so there is nothing to repair. Phase tasks about deleting or moving old code were rewritten as scaffold tasks.

**External facts to confirm ([VERIFY] in the docs):**
- Genesis rules on prior code and AI use
- Model ID and pricing (`claude-opus-5-5`) and fallback compatibility with structured output
- Anthropic SDK version
- `neo4j:5.26-community` tag
- PyTorch CPU wheel URL
- FastAPI, Pydantic, PyJWT and bcrypt versions (pin at hour 0)
- Next.js 14 scaffold command and version
- NAAC criterion codes
- DPDP Rules

## 6. Traceability (REQ → realisation → test)

| REQ | Tier | API | SCR / JOB | TEST |
|---|---|---|---|---|
| 001 | P0 | 005, 006, 007 | SCR-04, JOB-01 | 12, 13, 16 |
| 002 | P0 | 009, 010, 011 | SCR-04, 10, JOB-01 | 05, 13 |
| 003 | P0 | 003, 004 | SCR-04, JOB-01 | 15, 19 |
| 004 | P0 | 012, 013, 015 | SCR-02, 03 | 18, 19 |
| 005 | P0 | 015, 016, 003 | SCR-09 | 22, 39 |
| 006 | P0 | 017, 018, 019 | SCR-03, 05, 09 | 23 |
| 007 | P0 | 022, 023 | SCR-12 | 27 |
| 008 | P0 | 026, 027 | SCR-08 | 28 |
| 009 | P0 | 028 | SCR-05 | 29 |
| 010 | P0 | 026, 030 | SCR-05, 07, 08 | 30 |
| 011 | P0 | 026, 031, 032 | SCR-07, 08 | 31 |
| 012 | P0 | 024 | SCR-06 | 33 |
| 013 | P0 | 025 | SCR-07 | 43 |
| 014 | P0 | 029, 019 | SCR-05 | 42 |
| 015 | P0 | 027, 025, 035 | SCR-07 | 20, 21 |
| 016 | P0 | 033 | SCR-11 | 32 |
| 017 | P0 | 035, 036 | SCR-11 | 08, 21 |
| 018 | P0 | 010, 018, 023, 030, 032 | SCR-07 timeline | 34 |
| 031 | P0 | 001, 002 | SCR-01 | 03, 11 |
| 037 | P0 | 008 | SCR-04 | 14 |
| 038 | P0 | 037, 038 | SCR-14 | 35 |
| 019 | P1 | 034 | SCR-13 | 37 |
| 020 | P1 | 020 | SCR-03 | 24 |
| 021 | P1 | 021 | SCR-02 | 25 |
| 022 | P1 | 032 | SCR-07 | 38 |
| 023 | P1 | 039 | SCR-14 | 36 |
| 024 | P1 | 031, 045 | SCR-05 | 44 |
| 025 | P1 | — | SCR-04, JOB-01 | 17 |
| 026 | P1 | — (`scripts.eval_match`) | — | EVAL-03 |
| 030 | P1 | 014 | SCR-15 | 47 |
| 036 | P1 | 026, 032 | SCR-07, 08 | 26 |
| 027 | P2 | 041 | SCR-07 | 45 |
| 028 | P2 | 023 | SCR-12 | 27 |
| 029 | P2 | 024, 043 | SCR-06, 07 | 46 |
| 032 | P2 | 025 | SCR-07 | 48 |
| 033 | P2 | 043, 035 | SCR-07 | 49 |
| 034 | P2 | 042 | SCR-05 | 56 |
| 035 | P2 | 044 | SCR-16 | 57 |

API-040 (health) has no REQ; it serves ENV-/NFR-08 operations.

## 7. End-to-end verification scenario

Run on ENV-02 after `seed --reset`, with `LLM_PROVIDER=none`, and the network off for the strict version (TEST-52):

1. Log in as `aarav@demo.gurusetu` and open "Edge AI for Agriculture". **Expect** a fit of 38–50, "Close", PyTorch claimed-only and computer vision near.
2. Upload the 4 files in `backend/seed/demo_uploads/`. **Expect** 2 Verified, 1 "Already uploaded", and 1 "Waiting for review" (name mismatch).
3. Reopen the opening. **Expect** a fit ≥ 65, "Ready to apply". Apply. **Expect** "Applied · Pending"; applying again shows "Applied".
4. Log in as `meera@` and open the opening. **Expect** Aarav among 4 ranked applicants with Certified chips. Shortlist, then accept. **Expect** a toast that a guide link was created.
5. Open Reviews and approve Aarav's Embedded C certificate. **Expect** it to leave the queue; Aarav's skill shows Certified.
6. Open My mentees. **Expect** 13 assigned rows, 3 flagged (Aarav, now also Meera's guided student after step 4, is listed separately under "Guided students", not in the 13). Log a group session with 12 mentees selected (Aarav present, Diya marked absent), 2 action items for Aarav, and an attendance issue for Diya. **Expect** "Session saved for 12 students".
7. Log in as Aarav and open My mentorship. **Expect** 1 session to confirm, 2 action items and Dr. Meera under guides. Confirm the session and mark one item done.
8. As Meera, open a flagged mentee and resolve their open issue with a note. **Expect** status Resolved.
9. Log in as `suresh@` and open the Coordinator dashboard. **Expect** 48/50 allotted, Vikram below 100% compliance (highlighted), issues resolved incremented, and a needs-attention list with names.
10. Log in as `kavya@` and open the dashboard. **Expect** no student names. Export both packs. **Expect** README!A1 to start with "DRAFT", and no session note or issue text anywhere in either file.

## 8. Audit result (Stage 3)

**What I checked:**
- Every P0 REQ has acceptance criteria, at least one API/SCR/JOB and at least one TEST (§6).
- Every referenced ID resolves to a definition (scripted check over the pack; only A- IDs were undefined before this file).
- `openapi.yaml` parses, all `$ref`s resolve, and `x-id` covers API-001..045 exactly once.
- Role names, enum values, status machines and thresholds were compared across documents.
- NG- items were checked against the endpoints and screens.

**What I fixed while auditing:**
1. The fit thresholds (75/50 in PRD v2) could not be reached with trust weight 0.85. They were changed to 65/40, with AC-004.1/.3, REQ-021 and PRD §8 updated, and a worked example added (ai-system §4).
2. "Top 10 non-applicant candidates" contradicted the privacy matrix and NG-11, so REQ-005 is now applicants only, with TEST-39 added.
3. HOD access to API-027 is 403 (role not listed), not 404. AC-015.2 and the security Verify step were fixed.
4. REQ-013 and REQ-014 had no dedicated tests, so TEST-42 and TEST-43 were added; P1/P2 tests 44–49, 56 and 57 were added.
5. The frontend route guard was moved from Next middleware (which cannot read localStorage) to the `AuthGuard` component.
6. The why-path example was corrected to the near path that exists before the uploads.
7. The gain values in the API-015 example were recomputed (55.0 / 51.2 / 50.1).
8. Demo upload file names were unified across the AI doc, backend seed, tests and scenario.
9. A seed `--anchor-date` was added so the flags hold on any demo day.

**What remains assumed:** §5 (A-01..A-23) and the [VERIFY] facts listed under it. The scorer's exact before/after values depend on real MiniLM cosine values, so the tests assert ranges (A-16).
