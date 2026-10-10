# What is left, and a prompt for each person

*As of `main` at the integration merge (PR #4), 2026-10-10. Compiled by comparing `docs/phases/*.md` (phases 0 to 6, phase-4 add-ons, phase-5 add-ons B1-B7) and `docs/11-quality/test-strategy.md` with the actual code, a Docker run and a browser run.*

## 1. Where we are

| Area | State |
|---|---|
| Phases 0 to 3 (setup, foundation, core A, core B) | **Done and verified.** All 45 contract routes exist; 249 backend tests pass in Docker; all 16 screens exist; the seed matches backend section 10; the index section 7 scenario passes end to end on the real stack. |
| Phase 4, add-ons A1 to A9 | **Done** (backend and screens), except two polish items: A5 skill-gap card is switched off, A8 tamper detection is switched off and untested live. |
| Phase 5, add-ons B1 to B7 | **Backend done for all seven. Screens missing** for B1 (mark control), B2 (summary card), B3 (level control), B6 (feedback buttons), B7 (link to the page). B4 and B5 screens exist. |
| Phase 6, freeze and demo | **Not started:** accessibility and responsive pass, Playwright run, deck, script, rehearsals, video, submission, tags, QA log. Secret scan not run. |
| Evaluation numbers | **Thin:** extraction accuracy is measured on 4 files; the fit comparison is a tie on a set too easy to separate the scorers. |

## 2. Complete list of what is not done

### Product gaps (code)
| # | Item | Phase | Owner | Evidence |
|---|---|---|---|---|
| G1 | Learner level, intervention note and at-risk mark: controls on Mentee 360 (API-043) | B1, B3 | P3 | `learner_level` appears nowhere in `frontend/src/app` |
| G2 | Term summary card on Mentee 360 (`term_summary` is returned by API-025) | B2 | P3 | `term_summary` appears nowhere in the frontend |
| G3 | "Helpful / Not helpful" buttons after confirming a session on SCR-05 (API-042) | B6 | P4 | no call to `/sessions/{id}/feedback` |
| G4 | Link to the faculty profile (SCR-16) from the opening page and My mentorship | B7 | P3 or P4 | nothing links to `/faculty-profile/[id]` |
| G5 | Skill-gap card is off (`features.skillGap = false`) and every gap shows `openings_unlocked: 0` | A5 | P1 | `GET /me/skill-gaps` returns gaps with 0 unlocked on the seed |
| G6 | Tamper detection (A8) exists but `TAMPER_CHECK_ENABLED=false`; threshold not tuned | A8 | P1 | `docs/04-backend` rule 6; no seed file trips it |
| G7 | A leaner frontend runtime image (it copies dev packages) | hygiene | P3 | `frontend/Dockerfile` last stage |

### Evidence and evaluation gaps
| # | Item | Owner |
|---|---|---|
| E1 | `backend/seed/certificates/*`: the planned 25 labelled certificate images (18 typical, 4 edge, 3 adversarial) and a full `certificate_labels.csv` (it has 5 rows) | P4 |
| E2 | EVAL-01 on all 25 files (`python -m scripts.eval_extraction --raw`), raw numbers recorded | P1 |
| E3 | A valid EVAL-03: harder `match_labels.csv` so hybrid and keyword baseline can differ, then `python -m scripts.eval_match` | P1 + P4 |
| E4 | EVAL-04 full run: two more adversarial files (3 total) | P4 + P1 |
| E5 | `scripts/check_seed.py`: recomputes the dashboard numbers independently of the API and compares (TEST-32) | P4 |

### Phase 6 (freeze and demo)
| # | Item | Owner |
|---|---|---|
| F1 | T6.P1.1 offline run: `LLM_PROVIDER=none`, network off, every demo file a cache hit (TEST-52) | P1 |
| F2 | T6.P1.2 measured numbers into `docs/plan/eval-results.md` and the slide | P1 |
| F3 | T6.P3.1 accessibility (Lighthouse at least 90 on SCR-02, 03, 06, 08, 11) and responsive (no horizontal scroll at 360 px on SCR-05 and SCR-06) | P3 |
| F4 | T6.P3.2 run `frontend/e2e/primary-flow.spec.ts` against the stack | P3 |
| F5 | T6.P3.3 cleanup: unused fixtures, dead flags | P3 |
| F6 | T6.P4.1 deck | P4 |
| F7 | T6.P4.2 demo script and two rehearsals | P4 |
| F8 | T6.P4.3 backup video and submission form | P4 |
| F9 | T6.P2.1 secret scan (`gitleaks detect`) and `docs/plan/qa-log.md` | P2 |
| F10 | T6.P2.2 tag `rc1`, then `genesis-submission` on the video commit (the lead pushes tags) | P2 + lead |

### Decisions only the lead can make
- **D-1:** confirm the Genesis rules allow reusing the earlier project's concept and name.
- **D-5:** is a hosted submission URL required? If yes, deploy ENV-03 from the tag.
- **D-6:** record the real start time in `docs/phases/status.md`.
- **GitHub settings:** branch protection on `main` (PR required, rebase-and-merge only, no force push).
- **Known accepted risk:** `npm audit` shows 12 findings (1 critical) that need a Next 16 jump; they are recorded in security section 9. Decide if that stays accepted.

### Housekeeping
- `docs/phases/status.md` has about 24 rows still unchecked, mostly P4's and the gates. Each owner ticks their own rows.
- Demo day settings: `LLM_PROVIDER=none` unless approved live; `TODAY_OVERRIDE` empty; reseed with `--anchor-date <today>` ten minutes before.

---

## 3. Prompts

Each prompt is self-contained. Read `AGENTS.md` and `CONTRIBUTING.md` first (one branch per person, PR only at a checkpoint, never push to `main`, no Claude attribution in commits). To run everything: copy `docs/10-devops/env.example` to `.env`, then `docker compose up -d --build` and `docker compose exec backend python -m scripts.seed --reset`. Demo logins (password `Demo@123`): `aarav@`, `meera@`, `suresh@`, `kavya@demo.gurusetu`. If port 8000 is busy on your machine, map the backend to another host port in a local compose override and rebuild the frontend with `NEXT_PUBLIC_API_BASE` pointing at it.

### Prompt for P3 (frontend)

> You are P3 on GuruSetu (Next.js 14, TypeScript, Tailwind). The backend and all 16 screens are merged. Your job now is to finish the screens for the Phase 5 add-ons and run the Phase 6 quality pass. Work only on `feature/p3-frontend-mentor` rebased on the latest `main`. Use the existing components (`@/components/ui`, `useApi`, `api`, `useToast`). Types come from `src/lib/types.ts` (regenerate with `npm run gen:types` if `docs/04-backend/openapi.yaml` changed). Do not hand-edit generated files.
>
> **Tasks, in this order**
> 1. **Learner level, note and at-risk mark (B1, B3, REQ-029, REQ-033).** On Mentee 360 (`src/app/faculty/mentees/[studentId]/page.tsx`), show a card for the assigned mentor only: a level select (slow, average, advanced, none), a note textarea (max 500) and an "At risk" toggle, saved with `PATCH /mentees/{student_id}` (API-043). The response is the full overview, so refresh from it. The server omits `learner_note` and `marked_at_risk` for everyone but the assigned mentor, and shows only `learner_level` to the HOD; render exactly what arrives and never show the card to the HOD or a guide. Show `attention_details` text next to the "Suggested at risk" badge (`AttentionBadge` already takes a `detail` prop).
> 2. **Term summary card (B2, REQ-032).** On the same page, render `term_summary` (sessions attended, actions done of total, issues raised and resolved, certificates certified) as one small card of counts. It can be null.
> 3. **Link to the faculty profile (B7, REQ-035).** On `/student/openings/[id]` and on My mentorship (`/student/mentorship`), make the faculty name a link to `/faculty-profile/{user_id}` (the page already exists).
> 4. **Slim the runtime image.** In `frontend/Dockerfile`, make the last stage ship only what `next start` needs (use `npm ci --omit=dev` in a separate stage, or Next standalone output). Confirm `docker compose up -d --build frontend` still serves `/login` and the health check passes.
> 5. **T6.P3.1 Accessibility and responsive.** Run Lighthouse accessibility on `/student`, `/student/openings/op-edge-ai`, `/faculty`, `/faculty/sessions/new`, `/coordinator`: each must score at least 90. Check `/student/mentorship` and `/faculty` at 360 px width: no horizontal scroll. Fix what fails (labels, contrast, focus order). Record scores in `docs/plan/qa-log.md` (create it if missing).
> 6. **T6.P3.2 Playwright.** Run `npm run e2e` (`frontend/e2e/primary-flow.spec.ts`) against the running stack; fix the spec or the screen until it passes. If the bug list is long, report instead of fixing.
> 7. **T6.P3.3 Cleanup.** Remove unused fixtures and flags in `src/fixtures` and `src/lib/features.ts` that no screen reads.
>
> **Done when:** `npx tsc --noEmit`, `npx next lint` and `npx next build` are clean; each new control works against the live API as Meera and Suresh (HOD sees the level but never the note); Lighthouse and 360 px results are in `qa-log.md`. Open a PR only when the lead announces a checkpoint.

### Prompt for P4 (seed, evidence, deck)

> You are P4 on GuruSetu. The backend, ML and screens are merged. The seed loader exists (`backend/scripts/seed.py` plus `seed_mentoring.py`); the demo uploads exist in `backend/seed/demo_uploads/`. Your remaining work is the evidence set, an independent seed check, one small screen, and the whole demo package. Work only on your P4 branch (the remote one is `p4-seed-handoff`; rebase it on the latest `main`, or start a fresh `feature/p4-...` branch).
>
> **Tasks, in this order**
> 1. **Certificate image set (T1.P4.3, T2.P4.1).** Using `tools/certgen/make_demo_uploads.py` as the starting point, generate `backend/seed/certificates/` with 25 synthetic certificates: 18 typical (varied templates, PNG and PDF), 4 edge (rotated 90 degrees, phone photo with glare, two names printed, month-only date), 3 adversarial (a prompt-injection footer, a non-certificate receipt, a blank page). Templates must look visually distinct (decision L-6: pHash keys on layout, so near-identical templates collide). Write `backend/seed/labels/certificate_labels.csv` with one row per file: holder name, title, issuer, issue date, level, type, skills, `cache_corrected`. Hand-label before running any model.
> 2. **Build the extraction cache.** With a Groq key in `.env`, run `python -m scripts.build_extraction_cache seed/certificates seed/demo_uploads` (about 3 files per minute on the free tier). Commit the new files in `backend/extraction_cache/`.
> 3. **Seed certificates through the pipeline (T2.P4.2).** Make step 5 of the seed (backend section 10) process `seed/certificates/*` through P1's `extract`, `verify` and `apply_certified` with `source: cache`, instead of the hand-written rows in `seed_mentoring.py`, so statuses come from the real rules. Never force a status. Keep the spec counts true after a reset: Meera has exactly 3 flagged mentees, the dashboard shows 48/50, 1:12, 8 overdue actions.
> 4. **Independent seed check (E5, TEST-32).** Write `backend/scripts/check_seed.py`: it queries Neo4j directly with its own Cypher (not through the API or the services) and recomputes the dashboard figures (students, allotted, compliance per mentor, overdue actions, pending reviews, flagged students for Meera), then compares them with `GET /dept/dashboard` and `GET /me/mentees`. Print PASS or FAIL per figure and exit non-zero on any mismatch.
> 5. **Session feedback buttons (G3, B6).** On `/student/mentorship`, after "Confirm I attended" succeeds, offer "Helpful" and "Not helpful" buttons plus an optional comment (max 300) that call `POST /sessions/{id}/feedback`. A second submission replaces the first. Hide the buttons if the student was marked absent.
> 6. **Deck (T6.P4.1).** Ten slides in the order of `docs/phases/phase-6-freeze-demo.md` (problem with your collected quotes, one-line solution, the loop, live demo, how the AI is real and where it stops, privacy by design, measured results, architecture, roadmap, disclosure). Use only numbers in `docs/plan/eval-results.md`. `docs/story.md` and `docs/review-2-tech-stack-and-ai.md` already hold the wording.
> 7. **Script and rehearsals (T6.P4.2).** Write the 5-minute script from `docs/00-index.md` section 7, with fallback lines. Prepare four logged-in browser profiles (Aarav, Meera, Suresh, Kavya), reseed ten minutes before, and rehearse twice.
> 8. **Video and submission (T6.P4.3).** Record rehearsal 2 (1080p, under 5 minutes, with voice), keep a copy on a USB stick, fill the submission form with the repo URL at tag `genesis-submission`, the video, the deck PDF and the disclosure text.
> 9. Tick your own rows in `docs/phases/status.md`.
>
> **Done when:** `python -m scripts.seed --reset` finishes with the 25 certificates processed by the pipeline and `python -m scripts.check_seed` prints PASS on every figure; the feedback buttons work as Aarav; deck, script, video and submission are ready. Open a PR only when the lead announces a checkpoint.

### Prompt for P1 (ML)

> You are P1 on GuruSetu. The ML package, the fit APIs and the scorer are merged and work on the real stack. Your remaining work is measurement, two add-ons and the offline check. Work only on `feature/p1-ml-fit` rebased on the latest `main`. Do not tune anything against the test labels (REQ-026).
>
> **Tasks, in this order**
> 1. **Skill-gap card (A5, G5).** `GET /me/skill-gaps` returns gaps with `openings_unlocked: 0` on the seed, so the card would read "unlocks 0 openings". Check the definition in `docs/06-ai/ai-system.md` section 4: the card counts openings that cross `FIT_READY_MIN` if the skill were certified. If zero is correct on this seed, change `SkillGapCard` to show `total_gain` ("raises your best fit by up to N points") when `openings_unlocked` is 0. Then set `skillGap: true` in `frontend/src/lib/features.ts` and confirm it renders on `/student` for Aarav. Add TEST-25 coverage.
> 2. **Tamper signals (A8, G6).** `ml/verification.py` has `tamper_signal` behind `TAMPER_CHECK_ENABLED=false`. With P4's 25 files (and the planted tampered file), tune `ELA_THRESHOLD` so only the planted file trips it. If no value separates them, use the EXIF `Software` signal only and say so in `docs/plan/decisions-log.md`. Enable it in `docs/10-devops/env.example` only after tuning. A full seed reset must produce no `tamper_signal` on any other file. TEST-17 must pass.
> 3. **EVAL-01 full run (E2).** When P4's `seed/certificates/` and labels exist, run `python -m scripts.eval_extraction --raw` (about 10 minutes at the free-tier rate). Record the raw accuracy on the four key fields before correcting any cache entry, then record which fields were corrected.
> 4. **A valid EVAL-03 (E3).** The current labels give a tie (1.000 vs 1.000). Work with P4 to write harder `seed/labels/match_labels.csv` (students whose keywords match but whose proven skills do not, near-synonym cases, claimed versus certified), labelled before you see any scores. Run `python -m scripts.eval_match`. Report the result as measured, including a tie or a loss.
> 5. **EVAL-04 full run (E4).** With two more adversarial files from P4, run all three against the live model and record 3/3 or what happened.
> 6. **Offline run (T6.P1.1, TEST-52).** Set `LLM_PROVIDER=none`, turn the network off, run `python -m scripts.seed --reset`, then upload all six demo files as Aarav. Every one must be a cache hit with the statuses in `docs/plan/eval-results.md`. Report any miss.
> 7. **Numbers for the deck (T6.P1.2).** Update `docs/plan/eval-results.md` so every figure is measured; only those numbers may go on a slide.
>
> **Done when:** `pytest -q` in the container is green; `eval-results.md` has measured EVAL-01 (25 files), a valid EVAL-03, EVAL-04 3/3 and the offline result; the skill-gap card shows something meaningful. Open a PR only when the lead announces a checkpoint.

### Prompt for P2 (backend and release), or for whoever takes over

> You are P2 on GuruSetu. The backend is merged and verified. Your remaining work is hygiene and the release. Work only on `feature/p2-backend-core` rebased on the latest `main`.
>
> 1. **Secret scan (F9).** Install `gitleaks` and run `gitleaks detect` over the whole history: zero findings are required. If anything is found, rotate the secret and tell the lead. Also confirm `git ls-files | grep -E "(^|/)\.env$|uploads/"` is empty.
> 2. **QA log.** Create `docs/plan/qa-log.md` and record: `pip-audit` clean, the `npm audit` findings (see `docs/08-security/security-and-privacy.md` section 9), `pytest -q` result on a fresh seed, `ruff` and spectral lint, the secret-scan result, plus P3's Lighthouse and 360 px numbers when they arrive.
> 3. **Re-verify after each merge.** `docker compose up -d --build`, `docker compose exec backend python -m scripts.seed --reset`, `docker compose exec -e TODAY_OVERRIDE=2026-10-10 backend pytest -q`, then re-run the index section 7 scenario.
> 4. **Decisions log.** Fill D-5 and D-6 in `docs/plan/decisions-log.md` after the lead decides.
> 5. **Release (F10).** When the lead says so, propose tag `rc1` and, after rehearsal 2, `genesis-submission` on the exact commit used in the video. The lead pushes tags.
> 6. **Fix rota.** Take backend bugs from the list, one fix per commit, each re-tested with its TEST id.

---

## 4. Suggested order and who waits for whom

1. **P4 item 1 and 2** (certificate images, cache) unblock **P1 items 2 to 5** and **P4 item 3**. Start there.
2. **P3 items 1 to 4** and **P4 item 5** are independent of everything else: do them in parallel now.
3. **P1 item 1** (skill-gap card) touches `features.ts`: tell P3 before you edit it.
4. **Phase 6** (P3 items 5 to 7, P1 items 6 and 7, P4 items 6 to 8, P2 items 1 to 5) starts once the screens and the evaluation are in.
5. **Lead:** D-1, D-5, D-6 and branch protection today; tags at the end.
