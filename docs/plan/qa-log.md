# QA Log

Purpose:      Every quality check run before the freeze, with its measured result. Owner: P4 (P2 and P3 supply rows).
Audience:     The team, reviewers.
Status:       Phase 6 pass, 2026-10-11, on the local integration of main + the P1/P2/P3/P4 branches.

Only measured results appear here. Each row says what was run and on what.

## Environment

Local compose stack (ENV-02): `neo4j:5.26-community`, backend (FastAPI, Python 3.12), frontend (Next 14 standalone).
Fresh `python -m scripts.seed --reset` before each check unless a row says otherwise. `TODAY_OVERRIDE=2026-10-10`.

## Backend (P2)

| Check | Command | Result |
|---|---|---|
| Tests | `docker compose exec -e TODAY_OVERRIDE=2026-10-10 backend pytest -q` | **249 passed**, 1 deprecation warning (starlette `httpx` test client) |
| Lint | `docker compose exec backend ruff check .` | All checks passed |
| Dependencies | `pip-audit -r requirements.txt` | No known vulnerabilities |
| Contract lint | `npx @stoplight/spectral-cli@6.15.0 lint docs/04-backend/openapi.yaml --ruleset .spectral.yaml` | No errors |
| Secret scan | `gitleaks detect --log-opts=--all` (v8.24.3) | **No leaks**, 116 commits scanned |
| Tracked secrets | `git ls-files \| grep -E "(^\|/)\.env$\|uploads/"` | No `.env`. Only `backend/seed/demo_uploads/*` match: the synthetic demo certificates, committed on purpose |

**Operator note.** pytest wipes and edits the database it runs against (decisions-log L-8). Run `seed --reset` after any test run and before a demo.

## Frontend (P3)

| Check | Result |
|---|---|
| `npx tsc --noEmit`, `npx next lint`, `npx next build` | Clean |
| `npm audit` | 12 findings (1 critical, 9 high, 2 moderate), all in the Next 14 toolchain; reason in security §9 and L-5 |
| `npm audit --omit=dev` | 2 (`next` critical, its bundled `postcss` high); the runtime image ships only these |
| Runtime image | 1.11 GB → **225 MB** (Next standalone output, T5.P3.2); `/login` 200 and the health check passes |

### Lighthouse accessibility (TEST-51)

Live stack on :3000, real logins, Lighthouse accessibility category. Desktop 1350 px, mobile 360 px.

| Screen | Route | Desktop | Mobile |
|---|---|---|---|
| SCR-02 student home | `/student` | 100 | 100 |
| SCR-03 Fit Check | `/student/openings/op-edge-ai` | 100 | 100 |
| SCR-05 My mentorship | `/student/mentorship` | 100 | 100 |
| SCR-06 mentor home | `/faculty` | 100 | 100 |
| SCR-07 Mentee 360 | `/faculty/mentees/u-s003` | 100 | 100 |
| SCR-08 session form | `/faculty/sessions/new` | 100 | 100 |
| SCR-11 coordinator dashboard | `/coordinator` | 100 | 100 |

SCR-03 first scored 96: the fit components carried `dark:` colour variants, so a browser in dark mode drew light grey text on the white card (8 contrast failures). Removed on P1's branch; re-run 100.

### 360 px (no horizontal scroll)

`/student`, `/student/mentorship`, `/student/openings/op-edge-ai`, `/faculty`, `/faculty/mentees/u-s003`: all `scrollWidth == clientWidth == 360`.

### End to end (TEST-54)

`npm --prefix frontend run e2e` on a fresh seed: **1 passed** (index §7 steps 1, 3, 4, 6, 7, 9, 10). The spec was updated for the real seed names and for the Fit Check status text.

## Seed and evidence (P4)

| Check | Result |
|---|---|
| `python -m scripts.check_seed` (E5, TEST-32) | **11/11 PASS**: students 50, allotted 48, ratio 1:12, compliance 91.7% (per mentor 100/100/100/60), overdue actions 8, pending reviews 4, Meera's flagged mentees 3 |
| Negative control | Same script with `MIN_MEETINGS_PER_TERM=3`: 5 FAIL, exit 1 (the check can fail) |
| Certificate set (T1.P4.3) | 25 files (18 typical, 4 edge, 3 adversarial); closest unrelated pHash pair 16 (threshold 6), including PDFs rendered as the pipeline renders them |

## Add-on screens, live API

| Feature | As | Result |
|---|---|---|
| B1/B3 learner card (API-043) | Meera | level, note, at-risk save and refresh from the PATCH response; badge appears and clears |
| B1/B3 privacy | Suresh (HOD) | sees the level read-only, never the note or the toggle; PATCH returns 403 |
| B1/B3 privacy | Arjun (not the mentor) | overview 404 |
| B2 term summary | Meera | counts render |
| Suggested-at-risk detail | Arjun | "Suggested at risk: attendance 69%" on the mentor home and on Mentee 360 (after the `attention_details` contract fix) |
| B6 session feedback (API-042) | Aarav | offered right after "Confirm I attended"; a second submission replaces the first (checked in Neo4j); no button on absent sessions |
| B7 faculty profile links | Aarav | SCR-03 and My mentorship link to `/faculty-profile/{id}`, which loads |
| A5 skill-gap card | Aarav | renders on `/student`, shows the summed gain because no single skill unlocks an opening on this seed |
