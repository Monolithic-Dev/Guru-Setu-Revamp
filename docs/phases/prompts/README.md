# Builder prompts (P1-P4)
Purpose:      One self-contained prompt per builder, to paste into a coding agent (or read as a brief), so each person works on one branch, in their own files, and only opens pull requests.
Audience:     The lead, who hands them out, and P1-P4.
Depends on:   CONTRIBUTING.md, docs/phases/README.md, docs/phases/parallel-work.md, tools/ownership.txt
Status:       Draft v1

---

| Person | Lane | Branch | Prompt |
|---|---|---|---|
| P1 | ML and Fit Check | `feature/p1-ml-fit` | [p1-ml-fit.md](p1-ml-fit.md) |
| P2 | Backend, graph, security, Docker | `feature/p2-backend-core` | [p2-backend-core.md](p2-backend-core.md) |
| P3 | Frontend shell, certificate and mentor screens | `feature/p3-frontend-mentor` | [p3-frontend-mentor.md](p3-frontend-mentor.md) |
| P4 | Seed data, coordinator UI, pitch | `feature/p4-seed-coordinator` | [p4-seed-coordinator.md](p4-seed-coordinator.md) |

## How to use
1. Make sure the spec pack is on `main`, and P2 has pushed the scaffold commit (checkpoint C0, phase-0 T0.P2.0).
2. Give each person their file. Everything in it is binding, including the git rules.
3. Announce checkpoints in chat (C1, G1, G2, G3, freeze, final). Only then do people open PRs. You merge with **Rebase and merge** in the order P2, P1, P3, P4, then run the checks in CONTRIBUTING §5.
4. If a rule here and a phase doc disagree on git workflow, CONTRIBUTING.md wins. If they disagree on a product fact, the spec pack wins.

## Verify
Pick one prompt and check three things: every path it says the person owns prints that person's id with `python tools/check_ownership.py --who <path>`; every task id it lists exists in `docs/phases/status.md`; every document it tells them to read exists.
