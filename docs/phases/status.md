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
| T0.P1.1 All backend deps + Dockerfile + model bake + ml startup stub | P1 | ☐ | |
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
| T1.P1.1 Embeddings | P1 | ☐ | |
| T1.P1.2 Concepts + SIMILAR_TO | P1 | ☐ | |
| T1.P1.3 Extraction contract + adapter | P1 | ☐ | |
| T1.P1.4 Seed hooks + IDF | P1 | ☐ | |
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
| T2.P1.1 MDL-01 call | P1 | ☐ | |
| T2.P1.2 Verification | P1 | ☐ | |
| T2.P1.3 Extraction cache | P1 | ☐ | |
| T2.P1.4 Trust recompute | P1 | ☐ | |
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
| T3.P1.1 Scorer | P1 | ☐ | |
| T3.P1.2 Fit APIs | P1 | ☐ | |
| T3.P1.3 Seed tuning (A-16) | P1 | ☐ | |
| T3.P1.4 Fit UI + SCR-03 | P1 | ☐ | |
| T3.P2.1 Needs-attention + API-024 | P2 | ☑ | TEST-33 logic on a hand-built graph; re-check on the real seed |
| T3.P2.2 API-025 + API-029 | P2 | ☑ | TEST-42, 43 |
| T3.P2.3 Metrics + API-033 | P2 | ☑ | TEST-32 on a hand-built graph; P4's check_seed still to compare |
| T3.P2.4 Exports | P2 | ☑ | TEST-08, 21 (needs `openpyxl` in requirements.txt, P1) |
| T3.P2.5 Audit pass | P2 | ☑ | every P0/P1 P2-owned route in openapi.yaml exists; notifications and StatusEvents asserted per type in tests |
| T3.P3.1 SCR-06 | P3 | ☐ | |
| T3.P3.2 SCR-07 | P3 | ☐ | |
| T3.P3.3 SCR-09 | P3 | ☐ | |
| T3.P3.4 SCR-08 live attendees | P3 | ☐ | |
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
| A2 Why graph | P1 | P3 | ☐ | |
| A3 Reminders | P2 | P3 | ◐ | backend API-039 done; frontend P3 |
| A4 Issue lifecycle + confidential | P2 | P3 | ◐ | backend done (TEST-31 extended); frontend P3 |
| A5 Skill gap | P1 | P1 | ☐ | |
| A6 Eval table | P1 | P4 (slide) | ☐ | |
| A7 Mentee request / raise issue | P2 | P4 | ◐ | backend done (API-031 student path, API-045); frontend P4 |
| A8 Tamper signals | P1 | — | ☐ | |
| A9 Create opening | P2 | P3 | ◐ | backend API-014 done (embedding via P1 hook); frontend P3 |

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
| T6.P1.1 Offline run (TEST-52) | P1 | ☐ | |
| T6.P1.2 Eval numbers → slide | P1 | ☐ | |
| T6.P2.1 Scans + hygiene | P2 | ☐ | |
| T6.P2.2 rc1 + submission tag | P2 | ☐ | |
| T6.P3.1 a11y + responsive (TEST-51) | P3 | ☐ | |
| T6.P3.2 Playwright (optional) | P3 | ☐ | |
| T6.P3.3 Cleanup | P3 | ☐ | |
| T6.P4.1 Deck | P4 | ☐ | |
| T6.P4.2 Script + rehearsals ×2 | P4 | ☐ | |
| T6.P4.3 Video + submission | P4 | ☐ | |

## 8. Bugs
| # | Found at | Description | Steps / scenario step | Owner | Priority (P0 blocks freeze) | Status |
|---|---|---|---|---|---|---|
| | | | | | | |
