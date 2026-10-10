You are **P4 (Seed data, coordinator UI, pitch)** on a 4-person, 15-hour hackathon build of **GuruSetu**. Paste this whole brief into your coding agent, or read it as your own brief. It is self-contained: what to build, in what order, with what interfaces, what "done" means for every task, and exactly how to use git. Where it points to a document, that document has the full detail; where it states a number or a rule, the number or rule is binding.

# 1. The product and your part in it

GuruSetu (FastAPI + Neo4j backend, Next.js 14 frontend, Docker Compose, built **from scratch**, **synthetic data only**) is a trust layer for a university department:
- Students upload certificates (LLM extracts fields, deterministic code verifies), see an explained Fit Check for research openings, and apply.
- Faculty mentors log mentoring sessions (attendance, private notes, action items, issues); mentees confirm; mentors see who needs attention.
- HOD and IQAC see live compliance and export **draft** accreditation evidence (aggregates only, never private notes).

**You own the demo world and the story:** the synthetic seed data and its loader (everyone's tests and the demo depend on it by **hour 4**), the certificate images, the coordinator dashboard (SCR-11), allotment (SCR-12), student home (SCR-02), My mentorship (SCR-05), notifications and openings list (SCR-14/15), the 9:15 dry run, and the pitch (deck, demo script, backup video, submission). **The demo script comes from `docs/00-index.md` section 7**, not from the team plan's section 14 (where they differ, section 7 wins). The repo is `Guru-Setu-Revamp`; the default branch is `main`.

# 2. Non-negotiable rules (from the spec)

1. **Everything seeded or simulated is labelled** (`[MOCK]` in code, "Sample data" in the UI). No real student data anywhere (NG-03).
2. **The seed must make the index section 7 numbers hold on any day**, via `--anchor-date`: Aarav's fit 38-50 before and 65 or more after the uploads; Meera has **13 assigned mentees with exactly 3 flagged** (Karthik, Diya, Rahul); **48 of 50** students allotted. Seed dates are offsets from the anchor `2026-10-10`, written like `"-12d"`.
3. **Never force a status in the seed.** The planted files must produce `needs_review` and `duplicate` **by content** through the real pipeline.
4. **Privacy:** dashboards and exports show no note, issue, action or resolution text (REQ-015, SEC-15). The IQAC view shows **no student names**. The evidence pack is a **DRAFT**: `README!A1` starts with "DRAFT"; **never claim a NAAC level or score**.
5. **Do not show a number on the deck that was not measured**; use `docs/plan/eval-results.md` only. State sample sizes (n = 10 students for match quality, n = 25 certificates for extraction).
6. All API calls from the UI go through `src/lib/api.ts`; render API text as text; never `dangerouslySetInnerHTML` (SEC-19); no CDN assets. Accessibility basics are part of done (NFR-05/06).
7. Never commit `.env`, uploads, API keys or real data. Contracts (`openapi.yaml`, `schema.cypher`) are changed only by P2.
8. Build **P0 before P1 before P2** items; no non-goals (NG-01..15). The spec pack wins over a phase doc on facts.

# 3. Read first (30 minutes, in this order)

1. `AGENTS.md`, then `CONTRIBUTING.md` (git rules binding)
2. `docs/00-index.md` (section 5 assumptions, **section 7 scenario: your demo script**)
3. `docs/04-backend/backend.md` section 10 (**seed data: your governing spec**), section 6.4 (flag rules), section 7 (metrics), `schema.cypher`
4. `docs/05-frontend/ux-flows.md` (SCR-02, 05, 11, 12, 14, 15, FLOW-06, 08, 10, 11), `docs/01-product/prd.md`
5. `docs/06-ai/ai-system.md` sections 2.4 and 10 (certificate set composition, labels, EVAL-01..04)
6. `docs/phases/README.md`, `parallel-work.md`, phase docs 0 to 6, and `docs/plan/prd-v2-and-15h-plan.md` sections 14, 17-19 (pitch material)

# 4. Your files (single owner: you)

`backend/seed/**` **except** P1's `aliases.json`, `similar_overrides.json`, `fit_tuning.json` · `backend/scripts/seed.py` · `backend/scripts/check_seed.py` · `tools/certgen/` · `frontend/src/app/student/page.tsx`, `student/mentorship/`, `coordinator/**`, `notifications/page.tsx`, `faculty/openings/page.tsx`, `faculty-profile/` · `frontend/src/components/{coordinator,student}/` · `frontend/src/fixtures/p4/` · `README.md`, `CONTRIBUTING.md`, `AGENTS.md`, `CLAUDE.md` · `docs/` by default (except the folders P1, P2, P3 own) including `docs/phases/` (not `status.md`, which anyone edits for their own rows) · `docs/plan/qa-log.md`. **Layouts stay with P3** (ask P3 to change one). Check any path: `python tools/check_ownership.py --who <path>`. **Do not edit files you do not own.**

# 5. Schedule (hours from the real start time, written in `docs/phases/status.md`)

| Phase | Hours | Your tasks | Est |
|---|---|---|---|
| 0 Setup | 0:00-1:00 | T0.P4.1 seed skeleton, `seed.py` stub, certificate template (wait for P2's scaffold to branch) | 1:00 |
| 1 Foundation | 1:00-4:00 | T1.P4.1 seed content (1:30) · T1.P4.2 seed loader (1:00) · T1.P4.3 certificate images + labels (0:30) | 3:00 |
| 2 Core A | 4:00-7:00 | T2.P4.1 finish certificates · T2.P4.2 seed through the pipeline · T2.P4.3 SCR-12 allotment · T2.P4.4 SCR-05 My mentorship · 0:20 buffer | 2:40 |
| 3 Core B | 7:00-10:00 | T3.P4.1 SCR-11 dashboard · T3.P4.2 SCR-02 · T3.P4.3 SCR-14 + SCR-15 · T3.P4.4 SCR-05 live · **T3.P4.5 9:15 dry run** | 3:00 |
| 4 Add-on A | 10:00-12:30 | deck start (10:00) → A1 SCR-13 (about 10:40, after P2's API-034) → A4 escalated list on SCR-11 → A7 SCR-05 dialogs → deck | 2:30 |
| 6 Freeze | 12:30-15:00 | T6.P4.1 deck · T6.P4.2 demo script + 2 rehearsals · T6.P4.3 backup video + submission | 2:30 |

**Gates:** G0 1:00, G1 4:00, G2 7:00, **G3 core freeze 10:00**, feature freeze 12:30, **code freeze 13:15** (after it only you, the demo driver, approve a change, and only for a crash on the scenario path; no seed changes except `--anchor-date`). Stand-ups (5 min): 1:00, 4:00, 7:00 (30-min integration check), 10:00, 12:30.

# 6. Task details

## Phase 0
**T0.P4.1 Seed skeleton and certificate template (45 min).** Create each file in `backend/seed/` with 1-2 example records in the **final shape** (field names exactly as the ENT- tables): `users, departments, terms, openings, concepts, issuers, mentorships, sessions, action_items, issues, academics, certificates_index` (`.json`; `aliases`, `similar_overrides`, `fit_tuning` are P1's); every date is an offset from the anchor like `"date": "-12d"`. `scripts/seed.py` stub: `--reset` deletes all nodes, applies the schema, loads departments, terms and users with `bcrypt`-hashed `Demo@123` (reject passwords over 72 bytes). `tools/certgen/`: an HTML or Pillow template with fields name, title, issuer, date, ID; render 1 sample PNG. **Done when** `docker compose exec backend python -m scripts.seed --reset` prints "Seeded: 56 users" and the sample PNG exists.

## Phase 1 (by 4:00; everyone is waiting for this)
**T1.P4.1 Seed content (1:30)** must hold **exactly** (TEST-32 and TEST-33 depend on it):
- 56 users: 2 staff (`suresh@` hod, `kavya@` iqac), 4 faculty (`meera@`, `arjun@`, `lakshmi@`, `vikram@`), 50 students (`aarav@` plus 49), all `@demo.gurusetu`, password `Demo@123`. Allotments **13/13/12/10** with **2 unallotted**.
- Current term `2026-ODD` (start -87d, end +51d); previous `2026-EVEN`.
- Meera, Arjun, Lakshmi: every assigned mentee has at least 2 present sessions this term. Vikram: 4 of his 10 have fewer than 2.
- **Meera's flagged mentees, exactly:** Karthik (last present session -60d, allotted -120d, plus an overdue open action due -3d); Diya (an issue raised -16d, unresolved); Rahul (an overdue open action due -1d). No other Meera mentee meets any rule.
- Aarav: claimed python, pytorch, deep learning; python certified via `aarav_python_basics.png` (listed in `certificates_index.json`).
- 12 open openings; `op-edge-ai` (Meera) requires python, pytorch, deep learning, computer vision, with **3 pending applicants (not Aarav)**.
- About 40 sessions, about 60 action items (8 overdue overall), about 15 issues (4 unresolved, 1 stale over 14 days in Meera's group, 1 confidential), academics for 2 terms (3 students under 75% attendance), about 25 certificates.
- Issuers (synthetic) with aliases: NPTEL, Coursera, IEEE, Smart India Hackathon, Campus Coding Club, Amrita ACM Chapter. Criteria `NAAC-2.3.3` and `NAAC-5.3.1` with `verified:false`.
- **Done when** `scripts/check_seed.py` asserts every bullet against the JSON **before** loading (phase 3 reuses it for TEST-32 by computing the expected dashboard values independently).

**T1.P4.2 Seed loader (1:00).** Parse `--reset` and `--anchor-date` (default 2026-10-10), converting every `"±Nd"` offset. Delete all nodes, apply the schema, load in dependency order: departments → terms → users → concepts → issuers → criteria → openings + `REQUIRES` → mentorships → sessions + `ATTENDED_BY` → action items → issues → academics → applications. Apply P1's `seed/fit_tuning.json` (`{"students": {id: {bio, interests}}, "openings": {id: {description}}}`), then call **P1's** `ml.seed_hooks.seed_embeddings` and `ml.concepts.rebuild_similarity` (P1 never edits `seed.py`). Leave a `TODO(T2.P4.2)` hook for certificates. Print counts. **Done when** the G1 checks pass (50 students; Meera has 13 active assigned mentees; 12 openings; 40 or more sessions; every Student and Opening has a 384-d embedding; `SIMILAR_TO (deep learning)-(computer vision)` = 0.70) and a second run gives identical counts, in 60 s or less.

**T1.P4.3 Certificate images and labels (0:30).** In `seed/certificates/`: 25 files (18 typical, 4 edge, 3 adversarial including `cert_injection.png`) plus `aarav_python_basics.png`. In `seed/demo_uploads/`: `aarav_dl_pytorch.png` (holder "Aarav Menon", NPTEL, 2026-04-15, ID `NPTEL26CS41S7701`), `aarav_cv_workshop.png` (Amrita ACM Chapter, 2026-08-20), `aarav_python_copy.jpg` (a phone-style photo or re-encode of `aarav_python_basics.png` with a slight crop; **must stay within pHash distance 6**), `aarav_embedded_c.png` (holder "Arav M."), plus a planted EXIF-Photoshop file for REQ-025. `seed/labels/certificate_labels.csv`: `file, holder_name, title, issuer, issue_date, level, type, skills (pipe-separated), cache_corrected`. **Done when** `python -c "import imagehash,PIL.Image as I;print(imagehash.phash(I.open('...basics.png'))-imagehash.phash(I.open('...copy.jpg')))"` prints 6 or less.

## Phase 2 (by 7:00)
**T2.P4.1** finish the certificate set and labels if behind; also label `seed/labels/match_labels.csv` (10 students x 12 openings, relevance 0/1/2) **before seeing any scores**. **T2.P4.2 Seed certificates through the pipeline (0:30):** in `seed.py`, for each `certificates_index.json` entry copy the file to `UPLOAD_DIR`, create the Evidence, and call P1's `extract` + `verify` + `apply_certified` synchronously (cache hits). Never force statuses. **Done when** after a reset Aarav's python skill is trust 1 with source `aarav_python_basics` and the Evidence status counts match the index. **T2.P4.3 SCR-12 Allotment (0:50):** *first (10 min)* create your own route stubs with fixtures in `src/fixtures/p4/`: SCR-02 `student/page.tsx`, SCR-05 `student/mentorship/`, SCR-11 `coordinator/page.tsx`, SCR-12 `coordinator/allotment/`, SCR-14 `notifications/page.tsx`, SCR-15 `faculty/openings/page.tsx`. Then SCR-12 (FLOW-06): left, the unallotted list with checkboxes; right, mentor cards "13 / 20" with the Overloaded badge; a mentor select plus "Assign N students to <name>" → API-023 → refresh. **Done when** assigning the 2 unallotted students updates both lists live and the student gets the `allotted` notification. **T2.P4.4 SCR-05 My mentorship (0:50):** sections: assigned mentor card, guides, next follow-up, sessions to confirm (API-028), action items (checkbox → API-030 `done`, optimistic with rollback), issues (text only when present), applications with status pills. Build against `src/fixtures/p4/API-029.json` now (API-028 and API-030 are live already). **Done when** confirming a session and marking an item done work live.

## Phase 3 (by 10:00)
**T3.P4.1 SCR-11 Coordinator dashboard (1:15)** (FLOW-10): a "DRAFT evidence · {term}" banner; KPI tiles (allotted/total, ratio, compliance %, issues resolved/raised, overdue actions, pending reviews) using `KpiTile`; mentor table with compliance below 100% highlighted plus the Overloaded badge; issues-by-category bar chart (`recharts`, raised vs resolved; the confidential bar labelled "Confidential") and achievements by type; **HOD only:** the needs-attention list linking to SCR-07; export buttons (blob download using the filename from `Content-Disposition`). **Done when** index steps 9 and 10 pass and the IQAC view shows no names. **T3.P4.2 SCR-02 Student home (0:30):** summary strip from API-029 ("My mentor: Dr. Meera · 1 to confirm"), opening cards from API-012 with fit score and verdict pill, application status pill, links to SCR-03, empty state per FLOW-11; place P1's `<SkillGapCard />` (rendered when `features.skillGap`). **T3.P4.3 SCR-14 + SCR-15 (0:30):** SCR-14: P3's `<RemindersPanel />` at the top (when `features.reminders`), then API-037 with unread in bold, [Mark read] → API-038, a link per item, "Load more" via `next_cursor`; SCR-15: own openings from API-012 filtered to `faculty.user_id == me` with `applicant_count`, linking to SCR-09, and a "New opening" link only when `features.createOpening`. **T3.P4.4 (0:15)** switch SCR-05 from the fixture to live API-029. **T3.P4.5 9:15 dry run (0:30):** drive index section 7 steps 1-10 with whatever is merged and file a **numbered bug list** in `docs/phases/status.md` section 8 (each bug: owner = the file owner, priority P0 blocks the freeze). At 9:45 reseed and run it once more. **G3 (10:00):** index section 7 passes twice in 4 browser profiles on a fresh seed.

## Phase 4 add-ons (only if G3 passed)
Start the deck at 10:00 (P2 builds API-034 meanwhile). **A1 (0:45):** at about 10:40 make `KpiTile` clickable and build SCR-13 `coordinator/metrics/[metric]` (a table with the column set per metric, "Back to dashboard", header "{label}: {total} records"; the row count equals the tile). **A4 (0:15):** render the HOD-only "Escalated issues" list on SCR-11 from `escalated_issues`, each linking to SCR-07. **A7 (0:20):** two dialogs on SCR-05: "Request a meeting" (message) and "Raise an issue" (category + text). Then the deck. Tell the team at the 12:15 check which add-ons the demo may show.

## Phase 6 (the pitch)
**T6.P4.1 Deck** (content order): problem (3 pains with 3-5 collected student/faculty quotes) → one-line solution → the Verify → Match → Mentor → Track → Evidence loop → live demo → how the AI is real and where it stops (LLM extracts, code decides; the fit formula) → privacy by design → measured results (only `docs/plan/eval-results.md` numbers) → architecture → roadmap → disclosure (the concept comes from the earlier GuruSetu prototype; **no code is reused**). **T6.P4.2 Demo script and 2 rehearsals:** 4 browser profiles logged in (Aarav, Meera, Suresh, Kavya), Chrome zoom 110%, demo uploads in a desktop folder, a fresh reseed 10 minutes before. Fallback lines: extraction slow → "it's cached; here is the identical pipeline result"; any crash → switch to the backup video at the same timestamp. Prepare Q&A: "Isn't this an ERP?", "Fake certificates?", "Privacy?", "Is the AI real?", "Did you reuse code?". **T6.P4.3 Backup video and submission:** record rehearsal 2 (1080p, under 5 minutes, with voice), save it locally and on a USB stick; fill the form with the repo URL at the `genesis-submission` tag, the video, the deck PDF and the disclosure text. Demo-day settings: `LLM_PROVIDER=none` unless P1 approved live; `TODAY_OVERRIDE` empty (re-anchor with `seed --reset --anchor-date <today>`). Submission checklist is in `phase-6-freeze-demo.md` section 5.

# 7. Seams

You owe: a seeded DB that matches backend section 10 plus persona logins **by 4:00** (the whole team); your own route stubs and fixtures in your first frontend task. You call P1's `seed_embeddings`, `rebuild_similarity` and (phase 2) `extract`/`verify`/`apply_certified`; P3's `components/ui/*`, `features.ts` and layouts (by 2:30); P2's APIs as they land. Never edit P3's layouts; ask.

# 8. Git workflow (binding; the full text is `CONTRIBUTING.md`)

- Work **only** on `feature/p4-seed-coordinator`, created from the latest `main` **after P2's scaffold commit**. No scaffold yet? Read the docs and design the certificate template, but wait to create the branch. Set once: `git config pull.rebase true`.
- **Never push to `main`. Never merge a PR.** Open a PR **only when the lead announces a checkpoint** (C1 about 2:30, G1, G2, G3, freeze, final) or when your whole work is done. Title `P4 <checkpoint>: <summary>`, fill in the PR template (add screenshots), tag the lead, then **stop**. The lead merges with "Rebase and merge", so every commit lands as written.
- Small, working commits: `T1.P4.2 REQ-031: seed loader with --anchor-date`. No merge commits, no "wip".
- Daily loop: `git fetch origin && git rebase origin/main` → work → `python tools/check_ownership.py P4` (must print `ok`) → `python -m scripts.check_seed` and frontend lint → `git push --force-with-lease origin feature/p4-seed-coordinator`.
- After the lead merges one of your PRs: `git fetch origin && git rebase origin/main`, push with `--force-with-lease`, keep working on the **same** branch.
- A rebase conflict in a file you do not own means **stop and ask**. Update only your own rows in `docs/phases/status.md` (separate small commit). Never commit `.env`, uploads or real data.

# 9. Definition of done (per task)

The task's **Done when** passes; the flow works by hand for the right personas (`aarav@`, `meera@`, `suresh@`, `kavya@` at `demo.gurusetu`, password `Demo@123`); lint is clean; `check_ownership.py` prints `ok`; your `status.md` row is updated; index section 7 still runs on a fresh seed.

# 10. If you fall behind

If the seed is late the whole team stalls: finish the JSON first, polish later. Fallbacks: load fewer students **only** if TEST-32/33 expectations are updated in the same commit (last resort; prefer finishing the JSON in Phase 2's buffer); Cut order: deck polish, SCR-13, A7. **Never cut:** the seed, SCR-11, SCR-12, the dry run. At 7:00 apply the cut order, not at 9:30.

# 11. Your first 60 minutes

1. Read section 3 (30 min). 2. When P2's scaffold lands: `git fetch && git checkout -b feature/p4-seed-coordinator origin/main`. 3. T0.P4.1. 4. `python tools/check_ownership.py --list P4`. 5. Post any blocker in the team chat within the hour; you hold the team's seed dependency.
