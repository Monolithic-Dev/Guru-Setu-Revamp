# Build Status Board

Legend: ☐ todo · ◐ doing · ☑ done · ✂ cut. Update your own rows when you start or finish a task. Bugs go in §8 with an owner (the **file owner** from `tools/ownership.txt`).
Edit this file only in its own small commit straight to `main` after `git pull --rebase`. On a conflict, keep both sides ([parallel-work.md](parallel-work.md) §1).
`0:00 = ____` (real start time)

## 0. Decisions (T0.ALL.1) → details in `docs/plan/decisions-log.md`
| ID | Decision | Answer |
|---|---|---|
| D-1 | Prior code allowed + owners agree | |
| D-2 | LLM allowed + key available | |
| D-3 | People → P1/P2/P3/P4 | |
| D-4 | Local Docker Neo4j | |
| D-5 | Submission URL required | |
| D-6 | Real start time | |

## 1. Phase 0: Setup (gate G0 at 1:00)
| Task | Owner | Status | Note |
|---|---|---|---|
| T0.P2.0 Import commit (everyone pulls after) | P2 | ☐ | |
| T0.P2.1 Compose + config + main.py + generated models | P2 | ☐ | |
| (all) Ran `check_ownership.py` once | all | ☐ | |
| T0.P3.1 Frontend clean-up + all deps + nav/features/types | P3 | ☐ | |
| T0.P1.1 All backend deps + Dockerfile + model bake + ml startup stub | P1 | ☐ | |
| T0.P4.1 Seed skeleton + certificate template | P4 | ☐ | |
| **G0** | all | ☐ | |

## 2. Phase 1: Foundation (gate G1 at 4:00)
| Task | Owner | Status | Note |
|---|---|---|---|
| T1.P2.1 Delete dead code | P2 | ☐ | |
| T1.P2.2 Core repo/errors/logging | P2 | ☐ | |
| T1.P2.3 Auth + deps + API-001/002 | P2 | ☐ | |
| T1.P2.4 Notify + status history + API-037/038 | P2 | ☐ | |
| T1.P2.5 Applications + profile | P2 | ☐ | |
| T1.P1.1 Embeddings | P1 | ☐ | |
| T1.P1.2 Concepts + SIMILAR_TO | P1 | ☐ | |
| T1.P1.3 Extraction contract + adapter | P1 | ☐ | |
| T1.P1.4 Seed hooks + IDF | P1 | ☐ | |
| T1.P3.1 API client | P3 | ☐ | |
| T1.P3.2 Shell + guard + cleanup | P3 | ☐ | |
| T1.P3.3 SCR-01 Login | P3 | ☐ | |
| T1.P3.4 Shared components | P3 | ☐ | |
| T1.P3.5 Route stubs + fixtures | P3 | ☐ | |
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
| T2.P2.1 Certificates API + jobs | P2 | ☐ | |
| T2.P2.2 Allotment | P2 | ☐ | |
| T2.P2.3 Sessions | P2 | ☐ | |
| T2.P2.4 Action items + issues | P2 | ☐ | |
| T2.P3.1 SCR-04 | P3 | ☐ | |
| T2.P3.2 SCR-10 | P3 | ☐ | |
| T2.P3.3 SCR-08 | P3 | ☐ | |
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
| T3.P2.1 Needs-attention + API-024 | P2 | ☐ | |
| T3.P2.2 API-025 + API-029 | P2 | ☐ | |
| T3.P2.3 Metrics + API-033 | P2 | ☐ | |
| T3.P2.4 Exports | P2 | ☐ | |
| T3.P2.5 Audit pass | P2 | ☐ | |
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
| A1 Click-to-source | P2 | P4 | ☐ | |
| A2 Why graph | P1 | P3 | ☐ | |
| A3 Reminders | P2 | P3 | ☐ | |
| A4 Issue lifecycle + confidential | P2 | P3 | ☐ | |
| A5 Skill gap | P1 | P1 | ☐ | |
| A6 Eval table | P1 | P4 (slide) | ☐ | |
| A7 Mentee request / raise issue | P2 | P4 | ☐ | |
| A8 Tamper signals | P1 | — | ☐ | |
| A9 Create opening | P2 | P3 | ☐ | |

## 6. Phase 5: Add-on B (stretch; start before 11:30 only)
| Item | Owner | Status | Note |
|---|---|---|---|
| B1 At-risk | | ☐ | |
| B2 Semester summary | | ☐ | |
| B3 Learner level | | ☐ | |
| B4 Endorsement | | ☐ | |
| B5 Handover view | | ☐ | |
| B6 Session feedback | | ☐ | |
| B7 Track record | | ☐ | |

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
