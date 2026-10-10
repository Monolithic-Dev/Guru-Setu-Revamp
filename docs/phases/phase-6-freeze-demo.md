# Phase 6: Freeze, QA, Rehearse, Submit (12:30–15:00)
Purpose:      Turn whatever is merged at 12:30 into a reliable demo and a clean submission. No new features.
Audience:     P1–P4.
Depends on:   phase-4 §4 (12:15 check); test-strategy §2.4, §5; environments §5–§6; security SEC-10, 14, 16; team plan §14 (demo story), §17 (disclosure), §19 (roadmap)
Status:       Draft v1

---

## 1. Rules after 12:30 (FEATURE FREEZE)

- Only fixes for bugs that break the demo scenario, a P0 test, or a security control. Each fix needs one reviewer who re-runs the affected scenario steps.
- **13:15 CODE FREEZE:** after this, only the demo driver (P4) can approve a change, and only for a crash on the scenario path.
- No seed changes after 13:15, except `--anchor-date`.
- Copy, labels and styling may change until 13:15 if they don't touch logic.

## 2. Timeline

| Time | Everyone | P1 | P2 | P3 | P4 |
|---|---|---|---|---|---|
| 12:30–12:35 | Stand-up: what's merged, what the demo shows | | | | |
| 12:35–13:15 | **Bug bash:** each person runs index §7 in a different role and files bugs in `status.md` | Offline run (TEST-52) | Security scans + fixes | a11y + 360 px (TEST-51) | Deck build (slides 1–6) |
| 13:15 | **CODE FREEZE** | | | | |
| 13:15–13:30 | | Eval numbers → slide | Tag candidate `rc1`; full `pytest -q` | Remove `/dev/components`; final lint | Demo script final |
| 13:30–13:45 | **Rehearsal 1:** full 5-minute demo on the demo laptop, timed, 3 people watching with the judging lens | | | | Drives |
| 13:45–14:15 | Fix list from rehearsal 1 (crash-level only) + Q&A prep | | | | Deck slides 7–10 |
| 14:15–14:30 | **Rehearsal 2** + record the backup video (screen + voice) | | | | Drives / records |
| 14:30–14:45 | Submission checklist (§5); tag `genesis-submission` | | Tag + push | | Submit form |
| 14:45–15:00 | Buffer; final reseed for the live demo; laptops charged | | | | |

## 3. Tasks

### T6.P1.1 Offline run and cache verification (0:40)
- **Spec:** TEST-52, NFR-04, RISK-03, RISK-08
- With Wi-Fi off and `LLM_PROVIDER=none`, restart the stack (`docker compose down && up -d`), then `seed --reset`, then run index §7 steps 1–3. Confirm every demo upload is a cache hit and the embedding model loads from `/models`.
- If live extraction will be shown on stage: test the venue network once with `LLM_PROVIDER=anthropic` on one file. Decide live vs cache by 13:15 and tell P4. **Default: cache.** The pipeline is identical and the cache is disclosed.
- **Done when:** a TEST-52 pass is recorded in `docs/plan/qa-log.md`.

### T6.P1.2 Evaluation numbers (0:30)
- **Spec:** PRD §9, EVAL-01..04, NG-15
- Fill the metrics slide from `docs/plan/eval-results.md` only:
  - EVAL-01 raw field accuracy (n = 25);
  - EVAL-02 6/6;
  - EVAL-03 nDCG@10 and P@5, hybrid vs baseline (n = 10);
  - EVAL-04 3/3;
  - session-logging time from TEST-50.
- Any number not measured is not shown.
- **Done when:** P4 has the numbers, and each one cites its source line.

### T6.P1.3 Help the bug bash (remaining time)
Take scoring, extraction and seed bugs from the list.

### T6.P2.1 Security and repo hygiene (0:40)
- **Spec:** SEC-10, SEC-14, SEC-16, environments §6
- Run `gitleaks detect` (0 findings), `pip-audit -r backend/requirements.txt` and `npm --prefix frontend audit --audit-level=high`. Fix, or list in security §9 with a reason.
- `git ls-files | grep -E "(^|/)\.env$|uploads/"` must be empty, and no `node_modules`, `.next` or `__pycache__` may be tracked (.gitignore).
- Run TEST-01..12 once more on the release candidate.
- **Done when:** all clean and recorded in `qa-log.md`.

### T6.P2.2 Release candidate and tag (0:30)
- At 13:15, tag `rc1` and run the full `pytest -q` on a fresh seed.
- After rehearsal 2, tag `genesis-submission` on the exact commit used in the video, and push.
- Update the README status line from "specification complete, implementation starting" to the real status, listing which add-ons are included.
- If D-5 required a URL: deploy ENV-03 from the tag (environments §1). Use synthetic data and TLS at the platform edge.

### T6.P2.3 Fix rota (remaining time)
Own backend fixes from the bug list. Every fix is re-tested with its TEST-xx before merging.

### T6.P3.1 Accessibility and responsive pass (0:40)
- **Spec:** TEST-51, NFR-05, NFR-06, ux-flows §5
- Run Lighthouse a11y on SCR-02, 03, 06, 08 and 11 (≥ 90 each). Check 360 px for SCR-05 and SCR-06. Walk FLOW-07 keyboard-only.
- Fix only labels, contrast, focus order and overflow. No layout rewrites.
- **Done when:** scores are recorded in `qa-log.md`.

### T6.P3.2 Playwright smoke (0:40) [optional; skip if bug list is long]
- **Spec:** TEST-54
- `e2e/primary-flow.spec.ts` with 4 browser contexts covering index §7 steps 1, 3, 4, 6, 7, 9 and 10 (skip the file uploads if time is short; step 2 is covered by TEST-13).
- **Done when:** it passes headless once. If it doesn't by 13:15, drop it.

### T6.P3.3 Cleanup (0:15)
Remove `/dev/components`, any leftover fixtures from P0 routes and `console.log` calls. Run `npm run lint` and `tsc --noEmit`.

### T6.P4.1 Deck (1:00 total across the slots)
Content order:
1. Problem (3 pains, with the collected quotes)
2. Solution in one line
3. The Verify → Match → Mentor → Track → Evidence loop
4. Live demo (switch to the app)
5. How the AI is real and where it stops: LLM extracts, code decides; fit formula
6. Privacy by design (notes private; exports aggregates only)
7. Measured results (T6.P1.2 numbers only)
8. Architecture (architecture §2 diagram)
9. Roadmap (phase-5 §4 plus enterprise items)
10. Disclosure (team plan §17, adapted to D-1)

### T6.P4.2 Demo script and rehearsals (1:00)
- **Spec:** team plan §14 (5-minute story), index §7 (exact steps)
- Prepare 4 browser profiles logged in (Aarav, Meera, Suresh, Kavya). Keep the demo uploads in a desktop folder. Run a fresh reseed 10 minutes before.
- The script marks which add-ons to show (from the phase-4 12:15 check): Why graph after step 3, click-to-source in step 9, reminders in step 6.
- **Fallback lines:**
  - extraction slow → "it's cached; here is the identical pipeline result";
  - any crash → switch to the backup video at the same timestamp.
- **Q&A prep:**
  - "Isn't this an ERP?" → verified evidence + tracking that produces evidence as a by-product.
  - "Fake certificates?" → layered checks + review queue + honest limits.
  - "Privacy?" → security §4 matrix.
  - "Is the AI real?" → ai-system §1 table + eval slide.
  - "Did you reuse code?" → disclosure slide.

### T6.P4.3 Backup video and submission (0:30)
- Record rehearsal 2 (1080p, under 5 minutes, with voice). Save it locally and on a USB stick. Upload it if the submission asks for a video.
- Fill the submission form with the repo URL at tag `genesis-submission`, the video, the deck PDF and the disclosure text.

## 4. Demo-day settings

| Setting | Value |
|---|---|
| `LLM_PROVIDER` | `none` unless T6.P1.1 approved live |
| `TODAY_OVERRIDE` | empty; use `seed --reset --anchor-date <today>` instead |
| `TAMPER_CHECK_ENABLED` | `true` only if A8 merged and was tuned |
| Browser | Chrome, 4 profiles, zoom 110%, notifications off, bookmarks bar hidden |
| Laptop | Charging, Do Not Disturb on, Docker already running, `docker compose up -d` done 15 minutes before |

## 5. Submission checklist (14:30)

- [ ] `genesis-submission` tag pushed. The README status line is updated, and the README disclosure matches D-1.
- [ ] No `.env`, uploads or real data in the repo (T6.P2.1).
- [ ] `docs/plan/qa-log.md` lists TEST-50, 51, 52, the scans and the final `pytest -q` result, with times.
- [ ] `docs/plan/eval-results.md` is committed, and every number on the deck appears in it.
- [ ] The deck PDF is exported. The backup video is saved in 2 places.
- [ ] The phase status board (`docs/phases/status.md`) is final: built ☑, cut ✂ (cut items are listed on the roadmap slide).
