You are **P3 (Frontend shell, certificate and mentor screens)** on a 4-person, 15-hour hackathon build of **GuruSetu**. Paste this whole brief into your coding agent, or read it as your own brief. It is self-contained: what to build, in what order, with what interfaces, what "done" means for every task, and exactly how to use git. Where it points to a document, that document has the full detail; where it states a number or a rule, the number or rule is binding.

# 1. The product and your part in it

GuruSetu (FastAPI + Neo4j backend, **Next.js 14 + TypeScript + Tailwind** frontend, Docker Compose, built **from scratch**, **synthetic data only**) is a trust layer for a university department:
- Students upload certificates (LLM extracts fields, deterministic code verifies), see an explained Fit Check for research openings, and apply.
- Faculty mentors log mentoring sessions (attendance, topics, private notes, action items, issues); mentees confirm; the mentor home flags who needs attention; **Mentee 360** shows the whole timeline.
- HOD and IQAC see compliance and export draft accreditation evidence (aggregates only, never private notes).

**You own the frontend foundation and the mentor-side screens:** the app shell and route guard, login, the shared UI kit, the API client, navigation and feature flags, the certificate screen (SCR-04), the review queue (SCR-10), the session form (SCR-08), mentor home (SCR-06), Mentee 360 (SCR-07), candidates (SCR-09), and in add-on A the Why graph, reminders panel, issue actions and the create-opening form. **Everyone else's screens build on your shell and UI kit**, so your 2:30 seam is on the critical path. The repo is `Guru-Setu-Revamp`; the default branch is `main`.

# 2. Non-negotiable rules (from the spec)

1. **All API calls go through `src/lib/api.ts`** (one axios instance). No per-feature service modules, no direct axios/fetch in pages.
2. **Render API text as text** (React escaping). `dangerouslySetInnerHTML` is forbidden (SEC-19). PDF previews use `<iframe sandbox>`; images use `<img>` from API-011 (fetch as a blob with the auth header, then `URL.createObjectURL`).
3. **The token lives in localStorage and the guard is UX only**; the server enforces access. Never rely on the UI to hide private data. Private fields are **omitted, never null**: render nothing when `notes` is absent, not even an empty box.
4. **Every data view has its states** with the exact copy from `docs/05-frontend/ux-flows.md`: loading, empty, populated, error (with `requestId`), partial, permission-denied.
5. **Accessibility is part of done** (NFR-05/06): keyboard path through each flow, labels, status as text (never colour only), focus trap in dialogs, `role="alert"` on errors, reduced-motion respected, usable at 360 px.
6. Mark seeded or sample data "Sample data" (`[MOCK]`). No CDN fonts or external assets (the demo runs offline).
7. `src/lib/types.ts` is **generated** (`npm run gen:types`); never hand-edit it. Contracts (`openapi.yaml`) are changed only by P2.
8. Build **P0 before P1 before P2** items. Do not build non-goals (NG-01..15: no registration, no password reset, no mock/collaboration/support pages). The spec pack wins over a phase doc on facts.

# 3. Read first (30 minutes, in this order)

1. `AGENTS.md`, then `CONTRIBUTING.md` (git rules binding)
2. `docs/00-index.md` (section 5 assumptions, **section 7 end-to-end scenario**)
3. `docs/05-frontend/ux-flows.md` (**governing doc**: IA, flows FLOW-01..11, states and copy, accessibility, screens SCR-01..16, components, client state)
4. `docs/01-product/prd.md` (REQ and ACs for your screens) and `docs/04-backend/openapi.yaml` plus backend section 4.1 (example payloads)
5. `docs/08-security/security-and-privacy.md` section 4 (what each role may see)
6. `docs/phases/README.md`, `parallel-work.md` (seams, feature flags), phase docs 0 to 4 and 6

# 4. Your files (single owner: you)

`frontend/**` by default **except** P1's `src/app/student/openings/**`, `src/components/fit/**`, `src/fixtures/p1/`, and P4's `src/app/student/page.tsx`, `student/mentorship/`, `coordinator/**`, `notifications/page.tsx`, `faculty/openings/page.tsx`, `faculty-profile/`, `src/components/coordinator/`, `src/components/student/`, `src/fixtures/p4/`. **You always keep** every `layout.tsx` (even inside P4's folders), `package.json` and the lockfile, `frontend/Dockerfile`, `frontend/.dockerignore`, `src/lib/{api,problem,nav,features}.ts`, `src/hooks/`, `src/components/{AppShell,AuthGuard,NotificationBell}.tsx`, `components/ui/`, `components/mentor/`, `components/certificates/`, `components/why/`, `frontend/e2e/`, `src/fixtures/p3/`, `docs/05-frontend/`. `src/lib/types.ts` is GEN.

Your routes: `login/`, `student/certificates/`, `faculty/page.tsx`, `faculty/mentees/[studentId]/`, `faculty/sessions/new/`, `faculty/openings/[id]/`, `faculty/openings/new/` (add-on), `reviews/`, `dev/components/` (removed in Phase 6). Check any path: `python tools/check_ownership.py --who <path>`. **Do not edit files you do not own.**

# 5. Schedule (hours from the real start time, written in `docs/phases/status.md`)

| Phase | Hours | Your tasks | Est |
|---|---|---|---|
| 0 Setup | 0:00-1:00 | T0.P3.1 dependencies, Dockerfile, `nav.ts`, `features.ts`, types, owner folders | 1:00 (wait for P2's scaffold) |
| 1 Foundation | 1:00-4:00 | T1.P3.1 API client · T1.P3.2 shell + guard + layouts · T1.P3.3 SCR-01 login · T1.P3.4 shared components + `useApi` · T1.P3.5 route stubs | 3:00 |
| 2 Core A | 4:00-7:00 | T2.P3.1 SCR-04 certificates · T2.P3.2 SCR-10 review queue · T2.P3.3 SCR-08 session form | 3:00 |
| 3 Core B | 7:00-10:00 | T3.P3.1 SCR-06 mentor home · T3.P3.2 SCR-07 Mentee 360 · T3.P3.3 SCR-09 candidates · T3.P3.4 SCR-08 live attendees | 3:00 |
| 4 Add-on A | 10:00-12:30 | A2 WhyGraph (1:15) → A3 reminders (0:20) → A4 issue UI (0:30) → A9 create opening (0:20) | 2:25 |
| 6 Freeze | 12:30-15:00 | T6.P3.1 accessibility and 360 px · T6.P3.2 Playwright (optional) · T6.P3.3 cleanup | 2:30 |

**Gates:** G0 1:00, G1 4:00, G2 7:00, **G3 core freeze 10:00**, feature freeze 12:30, code freeze 13:15. Stand-ups (5 min): 1:00, 4:00, 7:00 (30-min integration check), 10:00, 12:30. Until a real endpoint lands, render the `example` payloads from backend section 4.1 or a fixture in `src/fixtures/p3/API-0xx.json`; swap to live calls at the gate. The G3 check `grep -rn "fixtures/" frontend/src/app` must return nothing for P0 routes.

# 6. Task details

## Phase 0
**T0.P3.1 (45 min).** After P2's scaffold commit: `npm ci && npx tsc --noEmit && npm run build`. Add **every** frontend dependency for all phases now so the lockfile never changes again: `axios`, `recharts`, `react-force-graph-2d`, dev `openapi-typescript`, dev `@playwright/test`; add scripts `gen:types` (`openapi-typescript ../docs/04-backend/openapi.yaml -o src/lib/types.ts`) and `e2e`. Write `frontend/Dockerfile` (node:20-alpine, build arg `NEXT_PUBLIC_API_BASE`, `next build` then `next start -p 3000`) and `frontend/.dockerignore`. Generate `src/lib/types.ts`. `src/lib/nav.ts`: the full route list per role from ux-flows sections 2 and 6, including add-on routes (`/coordinator/metrics/[metric]`, `/faculty/openings/new`, `/faculty-profile/[id]`). `src/lib/features.ts`: exactly 4 flags, one per line, all false: `whyGraph`, `skillGap`, `reminders`, `createOpening`. Create empty owner folders with `.gitkeep`: `src/fixtures/{p1,p3,p4}/`, `src/components/{ui,fit,mentor,why,coordinator,student,certificates}/`. Note the generated Next 14 app may report `npm audit` findings; tell P2 (they track SEC-16). **Done when** `npm run build` passes and the frontend container serves the placeholder page.

## Phase 1 (by 4:00)
**T1.P3.1 API client (0:30)**: one axios instance with `baseURL = process.env.NEXT_PUBLIC_API_BASE`; a request interceptor adds `Authorization: Bearer <token>`; the response interceptor, on 401, clears `token`, `role`, `user_id` and routes to `/login?expired=1`, and on any problem+json rejects with `{status, code, detail, errors, requestId}` (`lib/problem.ts`). **Done when** calling API-002 with a bad token lands on `/login?expired=1`.

**T1.P3.2 Shell, guard, layouts (1:00)**: `AuthGuard allowedRoles` checks localStorage (no token or the wrong role redirects to `/login`); `AppShell` renders the sidebar (≥ 768 px) or bottom nav (< 768 px) with the role items from ux-flows section 2, a header with name, role label, `NotificationBell` (polls API-037 `unread` every 30 s while visible) and Log out; layouts for `student`, `faculty`, `coordinator`, `reviews`, `notifications`; remove the generator's sample page. **Done when** each role sees exactly its nav items and another role's route redirects.

**T1.P3.3 SCR-01 Login (0:20)**: on success store `token`, `role`, `user_id`; route student → `/student`, faculty → `/faculty`, hod/iqac → `/coordinator`; show the expired banner when `?expired=1`; error copy per FLOW-01; focus the password field on a 401. **Done when** AC-031.1-031.3 pass by hand for `aarav@`, `meera@`, `suresh@`, `kavya@` at `demo.gurusetu` (password `Demo@123`).

**T1.P3.4 Shared components and data hook (0:50)**: `hooks/useApi(path) -> {data, error, loading, reload}`; in `components/ui/`: `EmptyState`, `ErrorState` (shows `requestId`), `Skeleton`, `StatusPill`, `TrustBadge`, `SkillChip`, `AttentionBadge`, `Toast` (`role="status"`), `KpiTile` (**with an optional `href` prop from the start**, for add-on A1), a `Dialog` with a focus trap, `Timeline`, `ExportButton`. **Seam stubs by 2:30:** `components/why/WhyGraph.tsx` (props `{openingId}`) and `components/mentor/RemindersPanel.tsx` (props `{}`), each returning `null`. **Done when** a `/dev/components` page renders every component in every variant.

**T1.P3.5 Route stubs with fixtures (0:20)**: create only your P0 routes (SCR-04, 06, 07, 08, 09, 10), each rendering its title plus data from `src/fixtures/p3/API-0xx.json` through the shared states. **Done when** all P3 routes render without errors for the right role.

**Handoff at 4:00 (what P1 and P4 get from you):** shell, `components/ui/*`, the two stubs, `lib/features.ts`, and the fixtures pattern.

## Phase 2 (by 7:00)
**T2.P3.1 SCR-04 Certificates (1:15)** (FLOW-02): file input accepting `.jpg,.jpeg,.png,.pdf` (reject over 10 MB client-side with the exact copy); after the 202 add the card in `processing` and poll API-006 every 2 s for 30 s, then show "Still working. We'll notify you."; status rendering with the reason copy from ux-flows section 4.2; a "My skills" section from API-003 (self) with `TrustBadge`; a manual form for `failed` → API-008. Put `CertificateUploader`, `CertificateCard`, `ManualCertificateForm` in `components/certificates/`. **Done when** uploading the 4 demo files shows the TEST-13 statuses (certified, certified, duplicate, needs_review) with the right copy.

**T2.P3.2 SCR-10 Review queue (0:40)** (FLOW-05): `ReviewCard` with the file preview (blob URL; PDFs in `<iframe sandbox>`); Approve/Reject (reject needs a reason, 3-300 chars) → API-010; remove the card; toast; handle 409 `ALREADY_REVIEWED` by refetching. **Done when** Meera approves Aarav's Embedded C certificate and Aarav's SCR-04 shows it Verified.

**T2.P3.3 SCR-08 Session form (1:05)** (FLOW-07, NFR-03): components `SessionForm`, `AttendeePicker` (checkbox plus present radio group per row, "select all mentees"), `TopicChips` (`role="group"`, toggle buttons with `aria-pressed`), `ActionItemEditor`. The attendee source is API-024 (fixture until Phase 3); `?student=<id>` pre-fills an individual session. Generate the `Idempotency-Key` with `crypto.randomUUID()` on mount and **reuse it on Retry**. Client validation mirrors server rules; on a server 422 map `errors[].field` onto inputs and focus the first. On success navigate back with the toast "Session saved for N students" (N = attendees with `present=true`). **Done when** a 12-attendee group session with 2 action items saves in 120 s or less, keyboard only (rehearse for TEST-50).

## Phase 3 (by 10:00)
**T3.P3.1 SCR-06 Mentor home (0:50)** (FLOW-09): assigned mentees first (flagged on top with reason badges per ux-flows section 4.3), then a "Guided students" group. Each row: meetings x/2, last session (relative date), open/overdue actions, open issues, unconfirmed count, [Open] and [Log session]. Header button "Log session" → `/faculty/sessions/new` (group). Stacked cards below 768 px. **Done when** index section 7 step 6's first expectation shows against the live API: **13 assigned rows, 3 flagged**; guided students are listed separately.

**T3.P3.2 SCR-07 Mentee 360 (1:10)** (REQ-013): two columns at ≥ 1280 px. Header (name, roll number, year, attention badges); skills with trust badges; academics table labelled "Sample data"; `Timeline` merging sessions, action items, issues and status events by date; action items with a "To verify" group [Verify] [Reopen] [Drop] → API-030; issues with [Resolve] → resolution dialog → API-032; applications, certificates, a "Log session for {first name}" button. When `notes` is present show a "Private notes" box, otherwise **nothing**. **Done when** index step 8 works live and the HOD view shows no notes box.

**T3.P3.3 SCR-09 Candidates (0:45)** (FLOW-04): ranked applicant cards (API-016), each expandable to P1's `components/fit/*` read-only; action buttons follow the status → API-018; on 409 `INVALID_TRANSITION` toast and refetch; accept toast "Aarav Menon accepted. Guide link created." **Done when** index step 4 works live (depends on P1's fit components at 7:30).

**T3.P3.4 SCR-08 live attendees (0:15)**: replace the fixture with API-024 rows; "Select all mentees" selects the assigned rows only; the context select shows the guide openings from those rows.

## Phase 4 add-ons (only if G3 passed; each merges only with its test green and the scenario still passing)
**A2 WhyGraph (1:15):** replace the stub, lazy-load `react-force-graph-2d` (`next/dynamic`, `ssr:false`) in a panel or dialog, fixed height 360 px, node colour **plus** a text label, SIMILAR_TO score on edges, and render the same paths as a text list below for screen readers ("deep learning → similar to (0.70) → computer vision → required by Edge AI for Agriculture"); set `whyGraph: true` in `lib/features.ts` (your line only). **A3 Reminders (0:20):** fill `RemindersPanel` (P4's SCR-14 already renders it); `reminders: true`; a small "N reminders" link in the SCR-06 header. **A4 Issue UI (0:30):** SCR-07 issue row [Acknowledge] [In progress] [Resolve] [Escalate to HOD] (confirm "The HOD will be able to read this issue.") and a "Confidential" toggle with a tooltip; SCR-08 issue repeater gets a confidential checkbox. **A9 Create opening (0:20):** `src/app/faculty/openings/new/` form (title, description, skills as a chip input) with the ux-flows section 6 validation copy; on success go to SCR-09; set `createOpening: true` (this makes P4's SCR-15 link appear). Cut order if short: A9, A4 UI detail, A3, then A2.

## Phase 6
T6.P3.1: Lighthouse accessibility ≥ 90 on SCR-02, 03, 06, 08, 11; check 360 px for SCR-05 and SCR-06; walk FLOW-07 keyboard-only; fix only labels, contrast, focus order and overflow; record in `docs/plan/qa-log.md` (P4 owns that file: send the numbers to P4). T6.P3.2 (optional, drop if the bug list is long): `e2e/primary-flow.spec.ts` with 4 browser contexts for index steps 1, 3, 4, 6, 7, 9, 10. T6.P3.3: remove `/dev/components`, leftover fixtures on P0 routes, `console.log` calls; run `npm run lint` and `npx tsc --noEmit`.

# 7. Seams

You owe: `components/ui/*` and the two stubs by **2:30**; `lib/features.ts`, `lib/nav.ts` from hour 0. You depend on: P2's scaffold (0:20), `API-001/002` (about 2:30-3:00), and the other APIs as they land (use fixtures until then); P1's `components/fit/*` stubs (7:30). After a contract change by P2, run `npm run gen:types` and commit the generated file alone. Two owners edit different lines of `features.ts`; on a conflict keep both sides.

# 8. Git workflow (binding; the full text is `CONTRIBUTING.md`)

- Work **only** on `feature/p3-frontend-mentor`, created from the latest `main` **after P2's scaffold commit**. No scaffold yet? Read the docs and wait. Set once: `git config pull.rebase true`.
- **Never push to `main`. Never merge a PR.** Open a PR **only when the lead announces a checkpoint** (C1 about 2:30, G1, G2, G3, freeze, final) or when your whole work is done. Title `P3 <checkpoint>: <summary>`, fill in the PR template (add screenshots), tag the lead, then **stop**. The lead merges with "Rebase and merge", so every commit lands as written.
- Small, working commits: `T2.P3.1 REQ-001: add certificate upload screen`. No merge commits, no "wip". The generated `types.ts` goes in its own commit.
- Daily loop: `git fetch origin && git rebase origin/main` → work → `python tools/check_ownership.py P3` (must print `ok`) → `npm --prefix frontend run lint && npx --prefix frontend tsc --noEmit` → `git push --force-with-lease origin feature/p3-frontend-mentor`.
- After the lead merges one of your PRs: `git fetch origin && git rebase origin/main`, push with `--force-with-lease`, keep working on the **same** branch.
- A rebase conflict in a file you do not own means **stop and ask**. Update only your own rows in `docs/phases/status.md` (separate small commit). Never commit `.env`, `node_modules` or `.next`.

# 9. Definition of done (per task)

The task's **Done when** passes; the flow works by hand for the right personas; `npm --prefix frontend run lint` and `tsc --noEmit` are clean; `check_ownership.py` prints `ok`; your `status.md` row is updated; index section 7 still runs. Verify against the live API wherever the endpoint exists.

# 10. If you fall behind

Cut order: A9, A4 UI, A3, A2; drop `/dev/components` and Playwright. **Never cut:** the shell and guard, login, SCR-04, SCR-08 (session log), SCR-06, SCR-07. P4 can take `ActionItemEditor` in their buffer slot; ask at the 4:00 or 7:00 stand-up.

# 11. Your first 60 minutes

1. Read section 3 (30 min). 2. When P2's scaffold lands: `git fetch && git checkout -b feature/p3-frontend-mentor origin/main`. 3. T0.P3.1. 4. `python tools/check_ownership.py --list P3`. 5. Post any blocker in the team chat within the hour.
