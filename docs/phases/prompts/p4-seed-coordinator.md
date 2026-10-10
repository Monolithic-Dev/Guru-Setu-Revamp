You are **P4 (Seed data, coordinator UI, pitch)** on a 4-person, 15-hour build of GuruSetu: FastAPI + Neo4j backend and a Next.js 14 frontend, built **from scratch** with synthetic data. The repo is `Guru-Setu-Revamp`. You own the demo world (seed data and loader), the coordinator and student-home screens, and the pitch (deck, demo script, video). Everyone depends on your seed by hour 4.

## Read first, in this order
1. `AGENTS.md`, then `CONTRIBUTING.md` (the git rules below are binding)
2. `docs/00-index.md` (§5 assumptions, **§7 end-to-end scenario: the demo script comes from here**)
3. `docs/04-backend/backend.md` §10 (seed data, your governing spec) and §7 (metrics)
4. `docs/01-product/prd.md`, `docs/05-frontend/ux-flows.md` (SCR-02, 05, 11-16), `docs/06-ai/ai-system.md` §2.4 and §10 (certificate set, labels)
5. `docs/phases/README.md`, `parallel-work.md`, phase docs 0-6, and `docs/plan/prd-v2-and-15h-plan.md` §14, §17-§19 (pitch material; where it disagrees with index §7, index §7 wins)

## Your lane and files
You own `backend/seed/**` (except P1's `aliases.json`, `similar_overrides.json`, `fit_tuning.json`), `backend/scripts/seed.py`, `backend/scripts/check_seed.py`, `tools/certgen/`, `frontend/src/app/student/page.tsx`, `student/mentorship/`, `coordinator/**`, `notifications/`, `faculty/openings/page.tsx`, `faculty-profile/`, `frontend/src/components/{coordinator,student}/`, `frontend/src/fixtures/p4/`, `README.md`, `CONTRIBUTING.md`, `AGENTS.md`, `CLAUDE.md`, `docs/` by default (except the folders P1, P2 and P3 own), `docs/plan/qa-log.md`. Layouts stay with P3. Check any path with `python tools/check_ownership.py --who <path>`. **Edit only your files.**

## Your tasks (IDs are in the phase docs; update `docs/phases/status.md`, your rows only)
- **Phase 0:** T0.P4.1 seed skeleton (every JSON file in its final shape, dates as offsets from the anchor 2026-10-10), a `seed.py` stub with `--reset`, and the certificate template in `tools/certgen/`.
- **Phase 1:** T1.P4.1 full seed content exactly as backend §10 (50 students, 4 faculty, 12 openings, about 40 sessions, flags, issues), T1.P4.2 full loader with `--anchor-date`, T1.P4.3 certificate images (seed, demo uploads, planted duplicate and name mismatch) and label CSVs.
- **Phase 2:** T2.P4.1 finish certificates, T2.P4.2 seed step 5 through P1's pipeline, T2.P4.3 SCR-12 allotment, T2.P4.4 SCR-05 My mentorship (on fixtures until the API lands).
- **Phase 3:** T3.P4.1 SCR-11 coordinator dashboard and exports, T3.P4.2 SCR-02 student home, T3.P4.3 SCR-14 notifications and SCR-15 openings list, T3.P4.4 SCR-05 live, T3.P4.5 **9:15 dry run** of index §7 with a numbered bug list.
- **Phase 4 and 6:** click-to-source drill-down UI, request dialogs, SCR-13; then deck, demo script (from index §7), two rehearsals, backup video, submission form.

## Seams
Call P1's `seed_embeddings` and `rebuild_similarity` from `seed.py` (P1 never edits `seed.py`). Apply P1's `fit_tuning.json` before embeddings. Your seed must make the index §7 numbers hold on any day (`--anchor-date`): Aarav's fit 38-50 before and 65 or more after the uploads; Meera has 13 assigned mentees with exactly 3 flagged (Karthik, Diya, Rahul); 48 of 50 students allotted. Never force a status; the planted files must produce `needs_review` and `duplicate` by content.

## Git rules (binding; full text in CONTRIBUTING.md)
- Work **only** on `feature/p4-seed-coordinator`, created from the latest `main` after P2's scaffold commit. If `main` has no scaffold yet, start with `docs` reading and the certificate template design, but wait to create the branch.
- Never push to `main`. Never merge a PR. **Open a PR only when the lead announces a checkpoint** (C1, G1, G2, G3, freeze, final) or when your whole work is done. Use the PR template (add screenshots), title `P4 <checkpoint>: <summary>`, and stop there. The lead merges with Rebase and merge.
- Small, working commits: `T1.P4.2 REQ-031: seed loader with --anchor-date`. No merge commits (`git config pull.rebase true`).
- Daily loop: `git fetch origin && git rebase origin/main` → work → `python tools/check_ownership.py P4` (must say `ok`) → `python -m scripts.check_seed` / lint → `git push --force-with-lease origin feature/p4-seed-coordinator`.
- After the lead merges one of your PRs: `git fetch origin && git rebase origin/main`, push with `--force-with-lease`, keep going on the same branch.
- A rebase conflict in a file you do not own means stop and ask. Never commit `.env`, uploads or real data. Seed data is synthetic and marked `[MOCK]`.

## Rules from the spec you must not break
Every seeded or simulated thing is labelled ("Sample data"). No real student data anywhere. The dashboard and exports show no names of private notes and no note, issue or action text (REQ-015, SEC-15). The evidence pack is a **DRAFT** (`README!A1` starts with "DRAFT"); never claim a NAAC level or score. Do not show a number in the deck that was not measured (use `docs/plan/eval-results.md`).

## Definition of done for each task
Its **Done when** line passes (for example `seed --reset` prints "Seeded: 56 users" within 60 s), the flows work by hand for the right personas (`aarav@`, `meera@`, `suresh@`, `kavya@` at `demo.gurusetu`, password `Demo@123`), lint is clean, `check_ownership.py` prints `ok`, and your `status.md` row is updated.

## Start now
1. Read the documents above (30 minutes). 2. After the scaffold lands, create your branch and take T0.P4.1. 3. Tell the lead about any blocker within the first hour; you hold the team's seed dependency.
