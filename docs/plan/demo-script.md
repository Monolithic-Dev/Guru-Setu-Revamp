# Demo Script (5 minutes)

Purpose:      What to say and click, minute by minute, with fallbacks. Owner: P4 (T6.P4.2).
Audience:     The presenter and the person driving the laptop.
Status:       Draft for rehearsal 1. Steps and numbers follow index §7; where anything here differs, index §7 wins.

## Before you start (10 minutes before)

1. `docker compose up -d`, then `docker compose exec backend python -m scripts.seed --reset`. **Never run pytest after this** (it wipes the database, decisions-log L-8).
2. `docker compose exec backend python -m scripts.check_seed`: every line must say PASS.
3. Open four browser profiles, each logged in: **Aarav** (`aarav@demo.gurusetu`), **Meera** (`meera@`), **Suresh** (`suresh@`), **Kavya** (`kavya@`). Password `Demo@123` for all.
4. Put the 4 files from `backend/seed/demo_uploads/` in a desktop folder: `aarav_dl_pytorch.png`, `aarav_cv_workshop.png`, `aarav_embedded_c.png`, `aarav_python_copy.jpg`.
5. Have the backup video open, paused at 0:00.

## The run

| Time | Who | Click | Say |
|---|---|---|---|
| 0:00 | Slide 1-3 | Problem, solution, the loop | "Every student here has a mentor on paper. Ask the HOD who wasn't met this semester, or what was promised: the answer is a signed register in a cupboard. And anyone can type 'PyTorch' on a profile." |
| 0:30 | **Aarav** | Home → "Edge AI for Agriculture" | "Aarav's fit is **Close, about 43**. PyTorch is only *claimed*, computer vision is *near* through deep learning. The score is three parts you can see." |
| 0:50 | Aarav | Certificates → upload the 4 files | "The AI reads each certificate; **code** decides the status. Two are **Verified**. This one is the same certificate re-photographed: caught as a **duplicate**. This one says 'Arav M.', not Aarav: **sent to a human**." |
| 1:30 | Aarav | Back to the opening → **Why?** | "Now he's **Ready**, 65 or more. 'Why?' shows the path from his proven skills to the opening." Apply. |
| 1:50 | **Meera** | My openings → Edge AI | "Meera sees applicants ranked by **verified** fit, Certified versus Claimed badges." Shortlist, accept: "a guide link is created." |
| 2:10 | Meera | Reviews → approve Embedded C | "The one the rules held back, a person approves." |
| 2:20 | Meera | My mentees | "**13 mentees, 3 flagged**: not met in 45 days, an overdue action, an open issue. This is 'who am I about to forget'." Point at the reminders panel. |
| 2:40 | Meera | Log session → select all, Diya absent, Academic + Attendance, 2 action items for Aarav, attendance issue for Diya | "A 12-student group session in under two minutes." Expect **"Session saved for 12 students"**. |
| 3:20 | **Aarav** | My mentorship → Confirm I attended → Helpful → tick one action item | "The student confirms, rates the session, and his promises are visible to him too." |
| 3:40 | Meera | Open a flagged mentee (Mentee 360) | "Everything about one student on one page. My private notes and intervention note are mine only." |
| 4:00 | **Suresh** | Dashboard | "**48 of 50** allotted, ratio **1:12**, Vikram's compliance below 100% is highlighted, issues raised versus resolved." Click a tile: "every number opens its records." |
| 4:30 | **Kavya** | Dashboard → Export mentoring pack | "IQAC sees **no student names**. One click: a **DRAFT** evidence pack. Open it: no session note, no issue text anywhere." |
| 4:50 | Slide 9-10 | Roadmap, disclosure | "One verified record, one session log. The right guide, a mentor who knows who needs them, and evidence all year without an extra form." |

## Fallback lines

| If | Say and do |
|---|---|
| An upload is slow | "It's served from the extraction cache; this is the identical pipeline result." Keep talking; the status updates on its own. |
| An upload fails | "Here is the manual fallback." Click **Enter details**: it goes to review, which is the honest path. |
| A number differs from the script | Say the number on screen, not the script. Do not apologise. |
| Anything crashes | "Let me show you the same moment from our recording." Switch to the backup video at the same timestamp. |
| Network drops | Nothing changes: the demo runs offline (`LLM_PROVIDER=none` works from the committed cache). |

## Q&A prep

| Question | Answer |
|---|---|
| "Isn't this an ERP mentoring module?" | ERPs store what staff type. We verify skills, explain matches, and the mentoring log produces the accreditation evidence as a by-product. |
| "Can't students fake certificates?" | Layered checks: exact and visual duplicates, name, issuer and date checks, a planted-edit check, and a human review queue. We say openly where it stops: we do not call issuers. |
| "Is the AI real?" | The model only reads the certificate into fixed fields. Every status, trust level and score is decided by code. Measured: **98.1%** key-field accuracy on 26 labelled files, injection contained **4/4** (slide 7). |
| "What about privacy?" | Session notes are private to the mentor who wrote them, by server rule; dashboards and exports are aggregates; IQAC sees no names. |
| "Did you reuse code?" | The disclosure slide: the concept and name come from our earlier prototype; no code is reused. |

## Rehearsal log

| # | Date | Time taken | What broke | Fixed? |
|---|---|---|---|---|
| 1 | | | | |
| 2 (recorded) | | | | |
