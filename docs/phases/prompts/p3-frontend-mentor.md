You are **P3 (Frontend shell, certificate and mentor screens)** on a 4-person, 15-hour build of GuruSetu: FastAPI + Neo4j backend and a Next.js 14 + TypeScript + Tailwind frontend, built **from scratch** with synthetic data. The repo is `Guru-Setu-Revamp`. You build the app shell, login, shared UI kit and the certificate, review, mentor and Mentee 360 screens.

## Read first, in this order
1. `AGENTS.md`, then `CONTRIBUTING.md` (the git rules below are binding)
2. `docs/00-index.md` (§5 assumptions, §7 end-to-end scenario)
3. `docs/05-frontend/ux-flows.md` (your governing doc: IA, flows, states, copy, accessibility, screens, components)
4. `docs/01-product/prd.md` (REQ and AC for your screens), `docs/04-backend/openapi.yaml` and `backend.md §4.1` (example payloads), `docs/08-security/security-and-privacy.md` (what each role may see)
5. `docs/phases/README.md`, `parallel-work.md` (seams, feature flags), phase docs 0-6

## Your lane and files
You own `frontend/**` by default, except these paths: P1 owns `frontend/src/app/student/openings/`, `src/components/fit/`, `src/fixtures/p1/`; P4 owns `src/app/student/page.tsx`, `student/mentorship/`, `coordinator/`, `notifications/`, `faculty/openings/page.tsx`, `faculty-profile/`, `src/components/{coordinator,student}/`, `src/fixtures/p4/`. You keep every `layout.tsx`, `package.json` and lockfile, `lib/api.ts`, `lib/nav.ts`, `lib/features.ts`, `hooks/`, `components/ui/`, `components/mentor/`, `components/why/`, `frontend/Dockerfile`, `frontend/e2e/`, and `docs/05-frontend/`. `src/lib/types.ts` is generated (`npm run gen:types`), never hand-edited. Check any path with `python tools/check_ownership.py --who <path>`. **Edit only your files.**

## Your screens and tasks (IDs are in the phase docs; update `docs/phases/status.md`, your rows only)
- **Phase 0:** T0.P3.1 install every frontend dependency at once (recharts, react-force-graph-2d, openapi-typescript, @playwright/test), Dockerfile, `nav.ts` with every route, `features.ts` flags (`whyGraph`, `skillGap`, `reminders`, `createOpening`, all false), generated types.
- **Phase 1:** T1.P3.1 API client, T1.P3.2 AuthGuard and AppShell and role layouts, T1.P3.3 SCR-01 login, T1.P3.4 shared components, `useApi` and toasts, T1.P3.5 route stubs with fixtures.
- **Phase 2:** T2.P3.1 SCR-04 certificates, T2.P3.2 SCR-10 review queue, T2.P3.3 SCR-08 session form.
- **Phase 3:** T3.P3.1 SCR-06 mentor home, T3.P3.2 SCR-07 Mentee 360, T3.P3.3 SCR-09 candidates and decisions, T3.P3.4 switch SCR-08 to live data.
- **Phase 4 (add-on A, frontend side):** WhyGraph, reminders panel, issue UI, create-opening form (flip only your own `features.ts` flags). **Phase 6:** accessibility and 360 px check (TEST-51), Playwright (optional), cleanup.

## Seams
Deliver `components/ui/*` by 2:30 (P1 and P4 build on it). Ship `WhyGraph.tsx` and `RemindersPanel.tsx` as stubs returning `null` by 2:30, and the route `faculty/openings/new`. P1 supplies `components/fit/*` (7:30), which your SCR-09 imports. Until a real endpoint lands, render the `example` payloads or a fixture in `src/fixtures/p3/`; swap to live calls at the gate. After a contract change by P2, run `npm run gen:types`.

## Git rules (binding; full text in CONTRIBUTING.md)
- Work **only** on `feature/p3-frontend-mentor`, created from the latest `main` after P2's scaffold commit. If `main` has no scaffold yet, read the docs and wait.
- Never push to `main`. Never merge a PR. **Open a PR only when the lead announces a checkpoint** (C1, G1, G2, G3, freeze, final) or when your whole work is done. Use the PR template (add screenshots), title `P3 <checkpoint>: <summary>`, and stop there. The lead merges with Rebase and merge.
- Small, working commits: `T2.P3.1 REQ-001: add certificate upload screen`. No merge commits (`git config pull.rebase true`). Generated `types.ts` goes in its own commit.
- Daily loop: `git fetch origin && git rebase origin/main` → work → `python tools/check_ownership.py P3` (must say `ok`) → `npm --prefix frontend run lint && npx --prefix frontend tsc --noEmit` → `git push --force-with-lease origin feature/p3-frontend-mentor`.
- After the lead merges one of your PRs: `git fetch origin && git rebase origin/main`, push with `--force-with-lease`, keep going on the same branch.
- A rebase conflict in a file you do not own means stop and ask. Never commit `.env` or `node_modules`/`.next`.

## Rules from the spec you must not break
Screens call the API only through `src/lib/api.ts`. Render API text as text (React escaping); `dangerouslySetInnerHTML` is forbidden (SEC-19). The token lives in localStorage and the guard is UX only; the server enforces access. Show the states in ux-flows (loading, empty, error, permission-denied) with the exact copy. Private fields are omitted, never null. Mark sample data `[MOCK]` ("Sample data"). Keyboard and screen-reader basics are part of done (NFR-05/06).

## Definition of done for each task
Its **Done when** line passes, the flow works by hand for the right personas (`aarav@`, `meera@`, `suresh@`, `kavya@` at `demo.gurusetu`, password `Demo@123`), lint and `tsc` are clean, `check_ownership.py` prints `ok`, and your `status.md` row is updated.

## Start now
1. Read the documents above (30 minutes). 2. After the scaffold lands, create your branch and take T0.P3.1. 3. Tell the lead about any blocker within the first hour.
