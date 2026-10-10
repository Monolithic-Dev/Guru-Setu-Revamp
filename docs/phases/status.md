# Build Status Board

Legend: ☐ todo · ◐ doing · ☑ done · ✂ cut. Update your own rows when you start or finish a task. Bugs go in §8 with an owner (the **file owner** from `tools/ownership.txt`).
Edit this file only in its own small commit on your own feature branch (CONTRIBUTING §6). On a conflict, keep both sides ([parallel-work.md](parallel-work.md) §1).
`0:00 = ____` (real start time)

## 0. Decisions (T0.ALL.1) → details in `docs/plan/decisions-log.md`
| ID | Decision | Answer |
|---|---|---|
| D-1 | Build from scratch (decided); concept reuse allowed by Genesis rules? | Scratch: yes. Rules: ☐ confirm |
| D-2 | LLM allowed + key available | |
| D-3 | People → P1/P2/P3/P4 | |
| D-4 | Local Docker Neo4j | |
| D-5 | Submission URL required | |
| D-6 | Real start time | |

## 1. Phase 0: Setup (gate G0 at 1:00)
| Task | Owner | Status | Note |
|---|---|---|---|
| T0.P2.0 Scaffold commit (everyone pulls after) | P2 | ☑ | pushed to main (4ecfe76) |
| T0.P2.1 Compose + config + main.py + generated models | P2 | ☑ | health 200 against Neo4j; spectral clean |
| (all) Ran `check_ownership.py` once | all | ☐ | |
| T0.P3.1 Frontend clean-up + all deps + nav/features/types | P3 | ☑ | build + container OK; npm audit: 12 findings in Next 14 scaffold (fix needs major upgrade) → P2 for SEC-16 |
| T0.P1.1 All backend deps + Dockerfile + model bake + ml startup stub | P1 | ☑ | 384 offline; groq 1.7.0 + email-validator; neo4j driver 5.28.7; torch 2.14.1+cpu |
| T0.P4.1 Seed skeleton + certificate template | P4 | ☐ | |
| **G0** | all | ☐ | |

## 2. Phase 1: Foundation (gate G1 at 4:00)
| Task | Owner | Status | Note |
|---|---|---|---|
| T1.P2.1 Security helpers + ADR-03 negative test | P2 | ☑ | TEST-02 |
| T1.P2.2 Core repo/errors/logging | P2 | ☑ | conftest.py pushed on feature/p2-backend-core |
| T1.P2.3 Auth + deps + API-001/002 | P2 | ☑ | TEST-01, 03, 09, 10, 11 |
| T1.P2.4 Notify + status history + API-037/038 | P2 | ☑ | TEST-35 foundation |
| T1.P2.5 Applications + profile | P2 | ☑ | TEST-23, 07 |
| T1.P1.1 Embeddings | P1 | ☑ | 384-d offline; Aarav-opening cosine 0.7696 |
| T1.P1.2 Concepts + SIMILAR_TO | P1 | ☑ | 22 concepts, 11 edges; dl-cv pinned 0.70 by override |
| T1.P1.3 Extraction contract + adapter | P1 | ☑ | schema + prompt verbatim; cache / none / cap paths tested |
| T1.P1.4 Seed hooks + IDF | P1 | ☑ | embeddings + similarity + idf_table, called from scripts/seed.py |
| T1.P3.1 API client | P3 | ☑ | 401 → /login?expired=1 verified in browser (API mocked) |
| T1.P3.2 Shell + guard + cleanup | P3 | ☑ | nav per role + guard redirects verified; /coordinator & /notifications pages are P4's |
| T1.P3.3 SCR-01 Login | P3 | ☑ | AC-031.1–.3 verified with mocked API-001; re-check live when API-001 lands |
| T1.P3.4 Shared components | P3 | ☑ | UI kit + WhyGraph/RemindersPanel stubs pushed (seam 2:30); /dev/components |
| T1.P3.5 Route stubs + fixtures | P3 | ☑ | SCR-04/06/07/08/09/10 on fixtures/p3 |
| T1.P4.1 Seed content | P4 | ☐ | |
| T1.P4.2 Seed loader | P4 | ☐ | |
| T1.P4.3 Certificate images + labels | P4 | ☐ | |
| **G1** | all | ☐ | |

## 3. Phase 2: Core A (gate G2 at 7:00)
| Task | Owner | Status | Note |
|---|---|---|---|
| T2.P1.1 MDL-01 call | P1 | ☑ | Groq qwen/qwen3.8-27b, 2.2-2.6 s, schema-valid (D-2) |
| T2.P1.2 Verification | P1 | ☑ | every rule row; EVAL-02 6/6 |
| T2.P1.3 Extraction cache | P1 | ☑ | 6 demo files committed; all cache hits with LLM_PROVIDER=none |
| T2.P1.4 Trust recompute | P1 | ☑ | 2/1/0/delete derived from Evidence, never read back off the edge |
| T2.P2.1 Certificates API + jobs | P2 | ☑ | TEST-06, 12, 13 against a scripted P1 pipeline; re-run with P1's real `extract`/`verify` |
| T2.P2.2 Allotment | P2 | ☑ | TEST-27 |
| T2.P2.3 Sessions | P2 | ☑ | TEST-20, 28, 29 |
| T2.P2.4 Action items + issues | P2 | ☑ | TEST-30, 31 |
| T2.P3.1 SCR-04 | P3 | ☑ | TEST-13 statuses + copy verified with mocked API; manual entry (API-008) done |
| T2.P3.2 SCR-10 | P3 | ☑ | approve/reject/409 verified with mocked API; preview via API-011 blob |
| T2.P3.3 SCR-08 | P3 | ☑ | 12-present group session + 2 actions + issue; 422 mapping; Retry reuses Idempotency-Key (mocked API) |
| T2.P4.1 Finish certificates | P4 | ☐ | |
| T2.P4.2 Seed certificates via pipeline | P4 | ☐ | |
| T2.P4.3 SCR-12 | P4 | ☐ | |
| T2.P4.4 SCR-05 | P4 | ☐ | |
| **G2 midpoint** | all | ☐ | |

## 4. Phase 3: Core B (gate G3 CORE FREEZE at 10:00)
| Task | Owner | Status | Note |
|---|---|---|---|
| T3.P1.1 Scorer | P1 | ☑ | TEST-18 exact: 43.4 / 68.5, gains, boundaries; Decimal arithmetic |
| T3.P1.2 Fit APIs | P1 | ☑ | API-012/013/015/016/020/021 + API-041 live on the stack |
| T3.P1.3 Seed tuning (A-16) | P1 | ☑ | 42.7 close -> 70.0 ready on a fresh seed (cosine 0.7696) |
| T3.P1.4 Fit UI + SCR-03 | P1 | ☑ | tsc + next build green; chips are P3's SkillChip |
| T3.P2.1 Needs-attention + API-024 | P2 | ☑ | TEST-33 logic on a hand-built graph; re-check on the real seed |
| T3.P2.2 API-025 + API-029 | P2 | ☑ | TEST-42, 43 |
| T3.P2.3 Metrics + API-033 | P2 | ☑ | TEST-32 on a hand-built graph; P4's check_seed still to compare |
| T3.P2.4 Exports | P2 | ☑ | TEST-08, 21 (needs `openpyxl` in requirements.txt, P1) |
| T3.P2.5 Audit pass | P2 | ☑ | every P0/P1 P2-owned route in openapi.yaml exists; notifications and StatusEvents asserted per type in tests |
| T3.P3.1 SCR-06 | P3 | ☑ | 13 assigned, 3 flagged first, guided listed separately (mocked API-024) |
| T3.P3.2 SCR-07 | P3 | ☑ | notes only when sent; HOD read-only; verify/reopen/drop + resolve (mocked API-025/030/032) |
| T3.P3.3 SCR-09 | P3 | ☑ | ranked + actions + 409 handling; interim CandidateFit until P1 components/fit lands |
| T3.P3.4 SCR-08 live attendees | P3 | ☑ | live by default; sample data only with NEXT_PUBLIC_USE_FIXTURES=1; G3 grep clean |
| T3.P4.1 SCR-11 | P4 | ☐ | |
| T3.P4.2 SCR-02 | P4 | ☐ | |
| T3.P4.3 SCR-14 + SCR-15 | P4 | ☐ | |
| T3.P4.4 SCR-05 live | P4 | ☐ | |
| T3.P4.5 Dry run 9:15 | P4 | ☐ | |
| **G3 CORE FREEZE** | all | ☐ | |

## 5. Phase 4: Add-on A (merge by 12:15)
| Item | Backend | Frontend | Status | Note |
|---|---|---|---|---|
| A1 Click-to-source | P2 | P4 | ◐ | backend API-034 done (tests green); frontend P4 |
| A2 Why graph | P1 | P3 | ◐ | frontend P3 done + whyGraph flag on (verified on mocked API-020); waiting on P1 API-020 and the SCR-03 host |
| A3 Reminders | P2 | P3 | ☑ | backend API-039 done; frontend P3 done: RemindersPanel + SCR-06 'N reminders' link, reminders flag on |
| A4 Issue lifecycle + confidential | P2 | P3 | ☑ | backend done (TEST-31 extended); frontend P3 done: SCR-07 acknowledge/in progress/escalate/confidential + SCR-08 checkbox |
| A5 Skill gap | P1 | P1 | ☐ | |
| A6 Eval table | P1 | P4 (slide) | ☐ | |
| A7 Mentee request / raise issue | P2 | P4 | ◐ | backend done (API-031 student path, API-045); frontend P4 |
| A8 Tamper signals | P1 | — | ☐ | |
| A9 Create opening | P2 | P3 | ☑ | backend API-014 done (embedding via P1 hook); frontend P3 done: /faculty/openings/new, verified live against API-014; createOpening flag on |

## 6. Phase 5: Add-on B (stretch; start before 11:30 only)
| Item | Owner | Status | Note |
|---|---|---|---|
| B1 At-risk | P2 | ◐ | backend done (marked + suggested at-risk, API-043); frontend open |
| B2 Semester summary | P2 | ◐ | backend done (`term_summary` in Mentee 360); frontend open |
| B3 Learner level | P2 | ◐ | backend done (API-043, MET-11 in the pack); frontend open |
| B4 Endorsement | | ☐ | |
| B5 Handover view | | ☐ | |
| B6 Session feedback | P2 | ◐ | backend done (API-042, author-only); frontend open |
| B7 Track record | P2 | ◐ | backend done (API-044); frontend open |

## 7. Phase 6: Freeze and demo
| Task | Owner | Status | Note |
|---|---|---|---|
| T6.P1.1 Offline run (TEST-52) | P1 | ◐ | every demo upload is a cache hit offline; full 10-step run needs the mentoring seed |
| T6.P1.2 Eval numbers → slide | P1 | ☑ | docs/plan/eval-results.md; EVAL-03 marked invalid, not a win |
| T6.P2.1 Scans + hygiene | P2 | ☐ | |
| T6.P2.2 rc1 + submission tag | P2 | ☐ | |
| T6.P3.1 a11y + responsive (TEST-51) | P3 | ☑ | Lighthouse a11y 100 desktop + 100 mobile on SCR-01/04/06/07/08/09/10 + A9; FLOW-07 keyboard-only OK; 360 px no h-scroll on all P3 screens (sample data). For P4's qa-log. SCR-02/03/05/11 are P1/P4 screens |
| T6.P3.2 Playwright (optional) | P3 | ◐ | e2e/primary-flow.spec.ts written (index §7 steps 1,3,4,6,7,9,10); not run yet: needs live API + seed on main |
| T6.P3.3 Cleanup | P3 | ☑ | /dev/components removed; no console.log; no fixture imports in src/app; lint + tsc clean |
| T6.P4.1 Deck | P4 | ☐ | |
| T6.P4.2 Script + rehearsals ×2 | P4 | ☐ | |
| T6.P4.3 Video + submission | P4 | ☐ | |

## 8. Bugs
| # | Found at | Description | Steps / scenario step | Owner | Priority (P0 blocks freeze) | Status |
|---|---|---|---|---|---|---|
| B-1 | P1 integration, 2026-10-10 | `tests/test_mentorship.py` is intermittently red: about one failure per four full-suite runs, a different test each time (`test_30_mentor_can_reopen_and_drop`, `test_a4_escalation_notifies_the_hod_and_unlocks_the_text`). Each passes in isolation and when run with just one other file, so this is shared seed state and ordering rather than logic - most likely a `collect()` without `ORDER BY`. Not caused by P1's tests: running them first leaves the suite clean. | `pytest -q` repeatedly | P2 | P1 - a flaky suite hides real regressions | open |
| B-2 | P1 integration, 2026-10-10 | `main` could not build the backend: `docker-compose.yml` declares `build: ./backend` but there was no `backend/Dockerfile` and no `backend/requirements.txt`. Both are P1-owned and land with the P1 PR. | `docker compose build backend` on main | P1 | P0 | fixed |
| B-3 | P1 integration, 2026-10-10 | The seed covers only the match-and-trust slice: no sessions, action items or issues, so the mentor screens, the coordinator dashboard and the exports have no data and the full 10-step index 7 run cannot be completed. | `python -m scripts.seed --reset` then SCR-06 | P4 | P0 for the demo | open |
