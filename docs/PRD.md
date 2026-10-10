# PRD v2: GuruSetu Verified Mentorship Graph
**Genesis Hackathon, Campus Problems track. Product requirements and 15-hour build plan.**

Status: draft v2. Owner: team. Supersedes PRD v1 (pasted draft) and merges the two concept docs:
[gurusetu-pramaan-concept.md](../../Ideas/gurusetu-pramaan-concept.md) (core loop) and [gurusetu-enterprise-vision.md](../../Ideas/gurusetu-enterprise-vision.md) (full vision), plus the [codebase audit](../../Ideas/GENESIS-GuruSetu-Audit-and-Proposal.md).

Tags: [VERIFIED] found by search or code reading · [INFERRED] reasoning · [ASSUMED] default to confirm · [UNVERIFIED] check before claiming.
Tier labels used throughout: **CORE** (must ship, hours 0–10) · **ADD-ON A** (hours 10–12.5) · **ADD-ON B** (only if A is done) · **ROADMAP** (pitch slide only, not built).

---

## 0. What changed from v1 (gap analysis)

### 0.1 Mentor-mentee items missing from the two concept docs
In the concept docs, "mentor" only means a faculty member who posts a research opening. The institutional mentor-mentee system (every student has an allotted faculty mentor) was absent. Added in v2:

| Missing item | Where it lives now |
|---|---|
| Two kinds of mentorship: **assigned mentor** (department allots, mandatory) vs **research guide** (student applies to an opening) | §4, §6 M3 |
| Mentor allotment by HOD, mentor load, unallotted-student list | M3 |
| Session log (individual **and group** sessions), attendance per mentee | M3 |
| Mentee confirmation of a session (digital replacement for the signed hard-copy register) | M3, §7 |
| Action items with owner, due date, status, overdue flag | M4 |
| Issues raised → resolved, with category and escalation | M3, M4 |
| Minimum-meetings compliance per semester (≥2 [VERIFIED in v1 from college guidelines]) | M4, M5 |
| Mentee 360 view: skills, academics, sessions, actions, issues, applications on one timeline | M4 |
| "Needs attention" flags (not met, overdue actions, stale issues, mentor-marked at-risk) | M4 |
| NAAC mentoring evidence (mentor:student ratio, mentor-wise issues raised/resolved) | M5 |
| Privacy tiers for session notes | §9 |
| Change of mentor / handover, semester review, learner-level tagging (slow/advanced) | ADD-ON B |

### 0.2 Items from the concept docs that v1 had dropped
| Item | Decision in v2 |
|---|---|
| Trust Ladder (Claimed → Certified → Faculty-verified …) | **CORE**, cut to 3 levels (§5) |
| "Am I ready?" Fit Check, both directions | **CORE** (hero screen) |
| Single application state machine (Pending → Shortlisted → Accepted/Rejected → Completed) | **CORE** (fixes audit H4) |
| Faculty track record ("is this mentor right for me?"), facts not ratings | ADD-ON B |
| Fit-not-rank guardrail, no leaderboards | **CORE** rule |
| Click-to-source evidence (every number opens its records) | ADD-ON A (lite auditor portal) |
| Closed research loop, endorsement (Trust level up after project) | ADD-ON B |
| Skill viva, Graph-RAG copilot, CO-PO, NIRF simulator, Open Badges 3.0, APAAR/DigiLocker, SSO, multi-campus, consent ledger, bridge finder, team composer, AICACE/funding opportunity types | **ROADMAP**: none fit 15 h |

### 0.3 Tracking gaps in all three documents
None of the three docs defined lifecycle states or "what counts as overdue". v2 defines a status model for every tracked object (§7) and the rules for flags and compliance (§8).

---

## 1. One-line vision

**Mentoring built on proof: a student's verified achievements find the right mentor, every mentoring session is recorded and tracked in two minutes, and the college gets its accreditation evidence as a by-product.**

---

## 2. The problem

Mentoring in a college has four stages, and each is broken in a different way.

| Stage | What happens today | Pain |
|---|---|---|
| **Discover** | Students don't know which faculty or lab fits them. Faculty can't find students with the right skills. | Word of mouth. Skills are self-claimed and unchecked. |
| **Connect** | Mentor groups are allotted by the department. Research openings are shared in WhatsApp groups. | No structured request, shortlist or status. |
| **Mentor & track** | A mentor looks after about 10–20 students and meets them at least twice a semester, recorded on signed hard-copy formats [VERIFIED: college guidelines and logbook formats]. | Paper registers. Action items are forgotten. Nobody sees which mentee hasn't been met or whose issue is still open. |
| **Evidence** | NAAC asks for the student-to-mentor ratio and mentor-wise records of issues raised and resolved, plus circulars and the approved mentor list [VERIFIED: college DVV/SSR submissions]. Student achievements are chased manually before audits [VERIFIED]. | Weeks of compilation, collected twice (students for themselves, faculty for the institution). |

**Root cause:** the same facts (who has which verified skill, who mentors whom, what was discussed, what was promised, what was resolved) sit on paper, in WhatsApp and in folders, and are never joined.

---

## 3. Users and roles

| Role | Needs | Success looks like |
|---|---|---|
| **Student (mentee)** | Prove skills once; find a research guide or opening that fits; see "my mentor", my action items, my open issues. | Finds a fitting opening in minutes and sees why; never loses track of what the mentor asked. |
| **Faculty (mentor + research guide)** | One list of my mentees with who needs attention; log a session in under 2 minutes; see verified, ranked applicants for my openings. | Logs a group session in < 2 min; opens one screen and knows who to follow up. |
| **Coordinator: HOD view** | Allot mentors, see coverage, meeting compliance, mentor load, unresolved and escalated issues. | Sees every student has a mentor and the required meetings happened. |
| **Coordinator: IQAC view** | Evidence for mentoring and student achievements. | Exports a draft evidence pack in one click; every number traces to records. |

To save build time, HOD and IQAC are **one Coordinator role with two tabs** [ASSUMED acceptable for the demo]. A dedicated Auditor role is ROADMAP.

---

## 4. Two kinds of mentorship (the v1 gap, made explicit)

| | **Assigned mentor** | **Research guide** |
|---|---|---|
| Created by | HOD allotment (bulk, from a list) | Student applies to an opening or requests a faculty member; faculty accepts |
| Mandatory? | Yes, every student has exactly one active assigned mentor | No, zero or more |
| Scope | Academic, personal, career, attendance, wellbeing | The project/opening |
| Sessions, actions, issues | Yes | Yes (same session log, tagged with the opening) |
| Counts for NAAC mentoring ratio | Yes | No (counts as research/achievement evidence instead) |
| Matching | Not matched; allotted | Matched on verified skills (Fit Check) |

Both use the same session, action-item and issue objects; the relationship type decides which dashboards and evidence they feed.

---

## 5. Core concept: the Trust Ladder (15-hour cut)

| Level | Badge | Earned by | Match weight [ASSUMED, tune later] | Tier |
|---|---|---|---|---|
| 0 | Claimed | Student types it | ×0.4 | CORE |
| 1 | Certified | A certificate verified by the pipeline or approved in the review queue | ×0.85 | CORE |
| 2 | Faculty-verified | Mentor/guide endorses after working with the student | ×1.0 + badge | ADD-ON B |
| — | Viva-verified, Demonstrated (project output) | Skill viva; closed research loop | — | ROADMAP |

Pitch line: *"Self-claimed skills are cheap. We make every skill provable, and the proof that gets a student a mentor is the same proof the college needs for accreditation."*

**Guardrails (CORE rules):** fit, never rank (no global score, no leaderboard); facts, not ratings (no anonymous reviews of professors); private by default.

---

## 6. Modules and features

```
 Verify  ──►  Match  ──►  Mentor  ──►  Track  ──►  Evidence
(certs →     (Fit Check,  (allot,      (actions,   (dashboards,
 trust)       explained)   sessions,    issues,     draft NAAC
                           issues)      flags)      pack)
        \_______________ one graph, one profile _______________/
```

### M0. Foundation (prerequisite, from audit §5/§12)
| Feature | Tier |
|---|---|
| Close C1/C2/C3/H7: response models (no password hash or embedding ever returned), **remove** password reset, ownership checks on every mutation, authenticated size-limited upload | CORE |
| **Delete** dead/duplicate routers instead of fixing them (`recommendations`, `faculty_projects`, `student_projects`, duplicate `openings` create, duplicate `notifications`), which removes several IDOR holes at once | CORE |
| One application state machine; stop masking HTTP errors as 500 | CORE |
| Non-destructive profile save (PATCH) | CORE (minimal) |
| Embeddings: MiniLM-384 to match indexes, built from full profile/opening text, backfill script | CORE |
| Boot: Dockerfile path, full `.env.example`, Cloudinary optional (local disk fallback), schema-on-startup | CORE |
| Frontend: route guard, 401 → login, one API client, remove mock/dead pages | CORE |
| Synthetic seed dataset (§12) | CORE |
| Tests for each security finding, CI | ADD-ON B |

### M1. Verify (ProofOnce)
| Feature | Tier |
|---|---|
| Upload certificate (photo/PDF) → vision LLM extracts name, title, issuer, date, level, **skills proven**, into a strict JSON schema | CORE |
| Checks: exact + perceptual hash duplicate, name match against profile, known-issuer match, date sanity (after enrolment) → **confidence score** | CORE |
| Routing: high confidence → Certified; low → **review queue** (mentor or coordinator one-tap approve/reject with reason) | CORE |
| Verified certificate raises the skill to Trust level 1; profile shows Claimed vs Certified chips with source | CORE |
| Cached extraction results for every demo certificate + manual-entry fallback if the LLM call fails | CORE |
| Tamper signals (EXIF/metadata, error-level analysis) shown as "suspicious" | ADD-ON A |
| QR / verify-URL check (NPTEL, Coursera) | ADD-ON B |
| Bulk upload, email forwarding, résumé import | ROADMAP |

### M2. Match (Fit Check)
| Feature | Tier |
|---|---|
| Hybrid score = semantic similarity + IDF-weighted skill overlap + similar-concept overlap, **weighted by trust level** | CORE |
| **"Am I ready?" Fit Check** per opening: matched (with trust badge) / claimed-only / missing chips, verdict line, per-component breakdown that sums to the total | CORE |
| Faculty: ranked candidates per opening, Certified vs Claimed shown; fit-not-rank wording | CORE |
| Apply / request a guide → Pending → Shortlisted → Accepted/Rejected, with in-app notifications | CORE |
| "Why this match?" graph (student → skill → SIMILAR_TO → required skill → opening) | ADD-ON A |
| Skill-gap "Unlock" panel: "learn X to unlock N more openings" | ADD-ON A |
| Evaluation table: keyword baseline vs hybrid (nDCG@10, P@5) on a hand-labelled seed set | ADD-ON A |
| Faculty track record (openings posted, students mentored, outcomes, response time) | ADD-ON B |
| Live match notifications, feedback re-ranking, bridge finder, team composer | ROADMAP |

### M3. Mentor (the college mentor-mentee system, digitised)
| Feature | Tier |
|---|---|
| **Allotment:** HOD assigns mentees to mentors (multi-select or CSV of seeded data); shows mentor load and **unallotted students** | CORE |
| **Research guide link:** created automatically when an application is Accepted | CORE |
| **Session log (< 2 min):** date, mode (in-person/online), type (individual/group), attendees with present/absent, topic category chips (academic, attendance, career, research, personal, other), private notes, action items, next follow-up date | CORE |
| **Group sessions:** one log for many mentees, attendance per mentee, so a 15-mentee meeting is one entry | CORE |
| **Mentee confirmation:** mentee taps "confirm I attended" (replaces the signature on the paper register); unconfirmed after 7 days shows as unconfirmed, not deleted | CORE |
| **Issue (light):** raised from a session or by the mentee; category; status Raised / Resolved; resolution note | CORE |
| Mentee requests a meeting / raises an issue from their own screen | ADD-ON A |
| Full issue tracker: Raised → Acknowledged → In progress → Resolved, **Escalate to HOD** | ADD-ON A |
| Confidential flag on a session/issue (mentor-only, excluded even from HOD counts by category) | ADD-ON A |
| 1-tap mentee feedback after a session ("helpful / not helpful", optional comment, visible to mentor only) | ADD-ON B |
| Change of mentor / handover (history kept, new mentor sees summary, not private notes) | ADD-ON B |
| Semester review: auto-summary of a mentee's semester (sessions, actions done, issues), mentor-only | ADD-ON B |
| Learner-level tag (slow / advanced learner) with intervention note, for the NAAC slow/advanced learner metric [UNVERIFIED metric number] | ADD-ON B |
| Parent/guardian contact log [INFERRED: common in college mentor formats], counsellor referral, peer/alumni mentors | ROADMAP |

### M4. Track (follow-up, flags, mentee 360)
| Feature | Tier |
|---|---|
| **Action items:** text, owner (mentee or mentor), due date, status Open → Done (mentee marks) → Verified (mentor confirms) / Dropped; **overdue** when past due and not Done | CORE |
| **Mentor home "My mentees":** per mentee: last met, meetings this semester (x/2), open actions, overdue actions, open issues, **needs-attention flag** with reason | CORE |
| **Mentee 360 (mentor view):** verified skills + trust, academic snapshot (seeded CGPA, attendance %, backlogs), session timeline, action items, issues, applications | CORE |
| **Student "My mentor" page:** assigned mentor, guides, upcoming follow-up, my action items, my issues, my applications with status | CORE |
| Status history on every tracked object (who, when), shown as a timeline | CORE |
| In-app reminders: meeting due in 7 days, action overdue, issue open > 14 days, session unconfirmed | ADD-ON A |
| Mentor-marked "at risk" plus auto-suggested at-risk from seeded academics (attendance < 75%, CGPA drop) [ASSUMED thresholds] | ADD-ON B |
| Email / WhatsApp reminders | ROADMAP |

### M5. Evidence (Pramaan, applied to mentoring and achievements)
| Feature | Tier |
|---|---|
| **HOD dashboard:** students allotted vs total, mentor load (mentees per mentor), % mentees with ≥2 meetings this semester, issues raised vs resolved by category, overdue actions, needs-attention list, pending certificate reviews | CORE |
| **One-click draft mentoring pack** (PDF or XLSX): mentor list, allotment list, mentor:student ratio, mentor-wise meetings held, issues raised/resolved by category. **Aggregates only, never notes** | CORE |
| **Achievements pack:** verified certificates grouped by type/level, mapped to 1–2 draft criteria | CORE |
| Every export and mapping labelled **DRAFT**; criteria must be checked against the official NAAC/NBA manuals [UNVERIFIED] | CORE |
| **Click-to-source:** every dashboard number opens the list of records behind it (lite auditor portal) | ADD-ON A |
| Gap report: "no sports/cultural achievements from CSE this semester", "3 mentors below minimum meetings" | ADD-ON A |
| Auditor portal, hash-chained evidence vault, Open Badges 3.0, NIRF simulator, CO-PO, SSR drafts | ROADMAP |

---

## 7. Status models (what is tracked)

| Object | States | Who moves it |
|---|---|---|
| **Certificate** | Uploaded → Extracted → Certified · Needs review → Certified / Rejected · Duplicate | System; reviewer (mentor or coordinator) |
| **Skill** | Claimed (0) → Certified (1) → Faculty-verified (2, ADD-ON B) | System from certificates; faculty endorsement |
| **Application / guide request** | Pending → Shortlisted → Accepted / Rejected → Completed | Faculty owner of the opening only |
| **Mentor allotment** | Active → Ended (reason: handover, graduation) | HOD |
| **Session** | Logged → Confirmed per attendee (or Unconfirmed after 7 days) | Mentor logs; each mentee confirms own attendance |
| **Action item** | Open → Done → Verified · Dropped; derived flag **Overdue** | Mentee marks Done; mentor verifies or drops |
| **Issue** | CORE: Raised → Resolved. ADD-ON A: Raised → Acknowledged → In progress → Resolved, any → Escalated | Mentor; mentee can raise; HOD on escalation |
| **Notification** | Unread → Read | Recipient |

Every transition writes `{from, to, by, at}` to the object's history (audit trail, NFR).

---

## 8. Tracking rules (flags and compliance)

All thresholds are configuration, not code [ASSUMED defaults; confirm with a faculty member].

| Rule | Default |
|---|---|
| Minimum meetings per mentee per semester | 2 [VERIFIED in v1] |
| **Needs attention** if any of | no session in 45 days · any overdue action · issue open > 14 days · 0 meetings and semester > 50% elapsed · mentor-marked at risk |
| Action overdue | past due date and not Done |
| Session unconfirmed | mentee hasn't confirmed within 7 days |
| Compliance % (HOD, NAAC) | mentees with ≥ minimum meetings ÷ allotted mentees |
| Issue resolution rate | resolved ÷ raised, per mentor and category |
| Mentor load warning | > 20 mentees [VERIFIED range 10–20 in v1] |

---

## 9. Privacy and access matrix

| Data | Mentee | Mentor (own mentees) | Other faculty | HOD | IQAC |
|---|---|---|---|---|---|
| Session notes | ✘ (sees date, topics, actions) | ✔ | ✘ | ✘ | ✘ |
| Session date, topics, attendance | ✔ own | ✔ | ✘ | counts only | counts only |
| Action items | ✔ own | ✔ | ✘ | counts | ✘ |
| Issue text | ✔ own | ✔ | ✘ | only if escalated | ✘ |
| Issue category + status | ✔ own | ✔ | ✘ | ✔ (not confidential ones) | aggregates |
| Academic snapshot | ✔ own | ✔ | ✘ | ✔ | ✘ |
| Verified skills / certificates | ✔ | ✔ | ✔ if student applied to their opening | ✔ | aggregates + certificate list |
| Rejected/flagged certificates | ✔ own | reviewer only | ✘ | reviewer only | ✘ |
| Exports | — | — | — | — | aggregates only |

The backend enforces this; the UI hiding a field is not enough. One test per row is ADD-ON B.

---

## 10. Graph model (Neo4j) additions

On top of the repaired base model (audit §2.4/§11):

```
(:Student|Faculty)-[:SUBMITTED]->(:Evidence {type:'certificate', status, confidence, file_url, sha256, phash, extracted:{...}})
(:Evidence)-[:PROVES]->(:Concept)
(:Evidence)-[:REVIEWED_BY {decision, reason, at}]->(:Faculty)
(:Student)-[:HAS_SKILL {trust_level, evidence_count, updated_at}]->(:Concept)
(:Concept)-[:SIMILAR_TO {score}]->(:Concept)

(:Faculty)-[:MENTORS {type:'assigned'|'guide', status:'active'|'ended', since, until, opening_id?}]->(:Student)
(:Session {id, date, mode, kind:'individual'|'group', topics:[...], notes_private, next_followup})
(:Faculty)-[:LOGGED]->(:Session)
(:Session)-[:ATTENDED_BY {present, confirmed_at?}]->(:Student)
(:Session)-[:CREATED]->(:ActionItem {id, text, owner, due, status})-[:FOR]->(:Student)
(:Issue {id, category, text, status, confidential, raised_at, resolved_at, resolution})-[:ABOUT]->(:Student)
(:Session)-[:RAISED]->(:Issue)
(:Student)-[:APPLIED_TO {status, history:[...]}]->(:Opening)      // single state machine
(:Student)-[:HAS_ACADEMICS {sem, cgpa, attendance, backlogs}]->(:Term)  // seeded snapshot
(:Evidence)-[:MAPS_TO {confidence, draft:true}]->(:Criterion {framework, code, title})
(:User)-[:IN_DEPT]->(:Department)
```

Status history is stored as an append-only list on the node/edge (`history`) for the demo; a separate event log is ROADMAP.

---

## 11. Functional requirements

| ID | Requirement | Tier |
|---|---|---|
| FR-1 | Student uploads a certificate and gets extracted fields, skills and a confidence score. | CORE |
| FR-2 | System flags duplicates and inconsistencies and routes low confidence to a review queue. | CORE |
| FR-3 | Certified items set the skill to trust level 1, with source shown. | CORE |
| FR-4 | Student sees a Fit Check per opening with matched/claimed/missing chips and a breakdown that sums to the total. | CORE |
| FR-5 | Faculty see ranked candidates per opening with trust badges. | CORE |
| FR-6 | Student applies or requests a guide; the opening owner moves it through the state machine; both get notifications. Accept creates a guide link. | CORE |
| FR-7 | HOD allots mentors to mentees and sees load and unallotted students. | CORE |
| FR-8 | Mentor logs an individual or group session with attendance, topics, private notes, action items, follow-up date in < 2 minutes. | CORE |
| FR-9 | Mentee confirms attendance; unconfirmed sessions are marked after 7 days. | CORE |
| FR-10 | Action items have owner, due date, status; mentee marks Done, mentor verifies; overdue is derived. | CORE |
| FR-11 | Issues can be raised from a session and resolved with a note; category recorded. | CORE |
| FR-12 | Mentor home lists mentees with meetings x/2, open/overdue actions, open issues and a needs-attention reason. | CORE |
| FR-13 | Mentee 360 shows skills, academics, sessions, actions, issues and applications on one page. | CORE |
| FR-14 | Student "My mentor" page shows mentor(s), follow-up, action items, issues, applications. | CORE |
| FR-15 | Session notes are visible only to the mentor (and never in any export or dashboard). | CORE |
| FR-16 | HOD dashboard shows coverage, compliance %, load, issues raised/resolved, overdue actions. | CORE |
| FR-17 | IQAC exports a draft mentoring pack and an achievements pack, aggregates only. | CORE |
| FR-18 | Every status change records who and when. | CORE |
| FR-19 | Click any dashboard number to see its records. | ADD-ON A |
| FR-20 | "Why this match?" graph. | ADD-ON A |
| FR-21 | Skill-gap panel ranks missing skills by openings unlocked. | ADD-ON A |
| FR-22 | Full issue lifecycle with escalation to HOD; confidential flag. | ADD-ON A |
| FR-23 | In-app reminders for meetings due, overdue actions, stale issues, unconfirmed sessions. | ADD-ON A |
| FR-24 | Mentee can request a meeting and raise an issue. | ADD-ON A |
| FR-25 | Tamper signals on certificates. | ADD-ON A |
| FR-26 | Evaluation table: keyword vs hybrid. | ADD-ON A |
| FR-27 | Faculty endorsement → trust level 2; faculty track record. | ADD-ON B |
| FR-28 | Change of mentor with handover; semester review summary; learner-level tag; mentee feedback. | ADD-ON B |
| FR-29 | At-risk suggestions from academics. | ADD-ON B |

---

## 12. Non-functional requirements

- **Security:** no endpoint returns password hashes or embeddings; role + ownership checks on every mutation; authenticated, size- and type-limited uploads; password reset removed.
- **Privacy:** synthetic data only; §9 enforced server-side; exports are aggregates.
- **Honesty:** the UI labels what is Certified vs Claimed, what is DRAFT, what is simulated (seeded academics).
- **Demo reliability:** one-command seed; cached LLM extraction for every demo file; manual-entry fallback; app works with the LLM key removed.
- **Performance:** Fit Check, mentor home and HOD dashboard load in ~2 s on seed data [ASSUMED].
- **Auditability:** status history on every tracked object.
- **Prompt injection:** uploaded document text is treated as data; the extraction prompt only fills a fixed schema.

**Seed dataset (synthetic):** 1 department, 4 mentors, ~50 students (12–13 each), 1 HOD, 1 IQAC; 8 openings; 2 semesters of academics; ~40 past sessions (mix of individual/group), ~60 action items (some overdue), ~15 issues (some open, one escalated); ~25 certificates including **1 duplicate and 1 suspicious**; 3 mentors compliant, 1 not (so the dashboard has something to show); hero personas Aarav (student) and Dr. Meera (mentor + guide).

---

## 13. The 15-hour build plan

### 13.1 Assumptions [ASSUMED, confirm at hour 0]
- **4 people × 15 hours ≈ 60 person-hours.** Reserve ~10 for integration, demo and deck → ~50 for building.
- The old repos (`Gurusetu-backend` FastAPI + Neo4j, `Gurusetu-frontend` Next.js 14) are copied into this repo at hour 0, if the rules allow reusing them (§17).
- One LLM API with vision is allowed and a key is available. If not, extraction uses cached JSON + manual entry, and that's said openly.
- Neo4j via local Docker (no Aura dependency on stage).

### 13.2 Phases and gates

| Hours | Phase | Exit gate (all must pass) |
|---|---|---|
| **0–1** | Setup | Repos copied, `docker compose up` works for everyone, API contracts for §11 CORE written in a shared file, seed skeleton runs |
| **1–4** | Foundation (M0) | No hash/embedding in any response; reset removed; dead routers deleted; application state machine; MiniLM-384 search returns results; seed loads full dataset; route guard works |
| **4–7** | Core build, part 1 | Certificate upload → Certified skill end to end; session log + action items saved and listed; allotment works |
| **7** | **Midpoint integration check** (30 min, whole team) | Front-end talks to real endpoints for every CORE screen built so far; cut list re-checked |
| **7–10** | Core build, part 2 | Fit Check + ranked candidates; mentor home + mentee 360; student "My mentor"; HOD dashboard; evidence export |
| **10** | **CORE FREEZE**: full §14 demo story runs end to end on seed data, twice, without errors | If not green, **no add-ons**; spend 10–12.5 fixing |
| **10–12.5** | ADD-ON A, in this order | Each add-on merged only if the demo still runs |
| **12.5** | **FEATURE FREEZE** | No new features after this |
| **12.5–15** | Polish, rehearse, record backup video, deck, disclosure | 2 full rehearsals; video saved offline |

**ADD-ON A priority order** (stop wherever time runs out): 1) click-to-source · 2) "Why this match?" graph · 3) in-app reminders + needs-attention reasons · 4) full issue lifecycle + escalation · 5) skill-gap panel · 6) evaluation table · 7) mentee request meeting / raise issue · 8) tamper signals.

### 13.3 Team split (hours per person)

**P1: AI/ML**
| Task | h | Tier |
|---|---|---|
| Embedding fix (MiniLM-384, text builders, backfill) | 1.5 | CORE |
| Certificate extraction: schema, prompt, cache, fallback | 3 | CORE |
| Duplicate hash, name/issuer/date checks, confidence, routing | 2 | CORE |
| Hybrid scorer + trust weights + breakdown + Fit Check API | 3.5 | CORE |
| Concept similarity table (SIMILAR_TO) for seed skills | 1 | CORE |
| Skill-gap panel API | 1 | ADD-ON A |
| Evaluation table (label 10 students × 8 openings, nDCG/P@5) | 1.5 | ADD-ON A |
| Demo caching, buffer | 1.5 | — |

**P2: Backend / graph**
| Task | h | Tier |
|---|---|---|
| Setup: Docker, env, schema-on-startup | 1 | CORE |
| Security cuts: response models, delete dead routers, ownership deps, upload limits, remove reset | 2.5 | CORE |
| Application state machine + guide link on accept + PATCH profile | 2 | CORE |
| Mentorship API: allotment, sessions (group + confirm), action items, issues, status history | 4 | CORE |
| Tracking queries: mentor home flags, mentee 360, HOD aggregates (§8 rules) | 2 | CORE |
| Evidence export (XLSX/PDF, aggregates only) | 1 | CORE |
| Click-to-source endpoints, reminders, escalation | 1.5 | ADD-ON A |
| Integration, bug fixing | 1 | — |

**P3: Frontend (student + mentor)**
| Task | h | Tier |
|---|---|---|
| Route guard, 401, one API client, remove mock pages, role-based layout/nav | 2.5 | CORE |
| Certificate upload + review queue UI | 2 | CORE |
| Fit Check screen + ranked candidates + apply/shortlist flow | 2.5 | CORE |
| Mentor home "My mentees" + mentee 360 | 2.5 | CORE |
| Session log form (2-min, group attendance, action items) | 1.5 | CORE |
| Student "My mentor" page (actions mark Done, confirm session) | 1 | CORE |
| "Why this match?" graph (react-force-graph or similar) | 2 | ADD-ON A |
| Polish | 1 | — |

**P4: Coordinator UI, data, pitch**
| Task | h | Tier |
|---|---|---|
| Seed dataset + personas + certificate images (incl. duplicate, suspicious) | 3 | CORE |
| HOD dashboard + allotment screen | 3 | CORE |
| IQAC tab + export template + DRAFT criterion mapping (1–2 criteria) | 2 | CORE |
| Click-to-source drill-down UI | 1 | ADD-ON A |
| Deck, demo script, disclosure, roadmap slide | 3 | — |
| Rehearsal + backup video | 2 | — |
| 3–5 quotes from students/faculty about mentoring pain (in breaks) | 1 | — |

### 13.4 If you have fewer people
- **3 people:** P4's UI work splits between P2 (export) and P3 (HOD dashboard as one page); drop tamper signals, eval table, guide request (keep apply only).
- **2 people:** M1 becomes 3 pre-checked sample certificates (no live pipeline); Fit Check stays; mentor home + session log + action items stay; HOD dashboard is one page; evidence pack is a real export of mentoring aggregates only. All ADD-ONs become roadmap.

**Cut order under pressure** (cut from the top): tamper signals → eval table → skill-gap → Why graph → full issue lifecycle → live certificate pipeline (switch to cached samples). **Never cut:** security fixes, session log, action-item tracking, mentor home, HOD dashboard, Fit Check.

---

## 14. Demo story (5 minutes, one continuous flow; all data synthetic)

1. **Hook (30 s).** "Every student here has a faculty mentor on paper. Ask a HOD which mentees weren't met this semester, or what was promised in the last meeting. The answer is in a signed register in a cupboard. And skills on a profile? Anyone can type 'PyTorch'."
2. **Student: Verify + Match (75 s).** Aarav opens Dr. Meera's "Edge AI for Agriculture" opening → **Fit Check 54%**, PyTorch only *claimed*. He uploads 4 certificates: one **duplicate** is caught, one goes to **review**. Two become **Certified**; the fit rises to **82%** with the breakdown. *(ADD-ON A: tap "Why?" and the path lights up.)* He applies.
3. **Faculty as guide (30 s).** Dr. Meera sees ranked applicants with Certified vs Claimed badges, accepts Aarav. A guide link appears on both profiles.
4. **Faculty as assigned mentor (75 s).** Dr. Meera's **My mentees** list: 13 mentees, 3 flagged *needs attention* (not met in 45 days, overdue action, open issue). She logs a **group session** for 12 mentees in under 2 minutes, adds two action items and marks an attendance issue resolved. Aarav's phone: confirm attendance, action item appears; he marks one Done. Open **Mentee 360** for a flagged student: skills, academics, timeline on one page.
5. **HOD (45 s).** Coverage 50/50 allotted; compliance 3 of 4 mentors at ≥2 meetings; issues raised vs resolved by category; one mentor overloaded. *(ADD-ON A: click "11 issues resolved" → the records.)*
6. **IQAC (30 s).** "Generate evidence pack" → a **DRAFT** mentoring summary (ratio, mentor list, mentor-wise meetings and issues) and an achievements list. Show that **no private notes** are in it.
7. **Close (15 s).** "One verified record, one session log. The student gets the right guide, the mentor knows who needs them, and the college has its evidence all year, without a single extra form." Then the roadmap slide.

---

## 15. Success metrics (measured on synthetic/consented data, not assumed)

| Metric | How |
|---|---|
| Certificate field accuracy | Correct fields ÷ total on 20–30 labelled certificates |
| Duplicate/suspicious detection | Flagged ÷ planted cases |
| Match quality | nDCG@10, P@5 vs keyword baseline on the labelled seed set |
| Time to log a session | Stopwatch: paper register vs app, individual and 12-mentee group |
| Follow-up visibility | Time for a mentor to answer "who needs follow-up?": paper vs mentor home |
| Evidence compilation time | Manual vs one-click export, timed once |
| Mentee coverage / compliance | % allotted; % with ≥2 meetings in seed data |

---

## 16. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Reusing an exhibited project breaks Genesis rules | Read the rules at hour 0; disclose; list exactly what is new (§17) |
| 15 h is too short for repair + build | Delete dead code instead of fixing it; gates in §13.2; cut order in §13.4 |
| LLM extraction fails on stage | Cached results, manual fallback, confidence + review queue shown openly |
| Security hole found by a judge | M0 before any feature; synthetic data only |
| Mentor notes are sensitive | Server-side §9 matrix; excluded from every export and dashboard |
| Wrong accreditation mapping | DRAFT labels; only 1–2 criteria; faculty review |
| "Isn't this just an ERP mentoring module?" | Lead with verified-skill matching + tracking that produces evidence as a by-product; ERPs store what staff type in |
| Over-claiming (ML, RAG, "TRL 9") | Only claim what the demo shows and §15 measures |
| Integration breaks late | Contracts at hour 1, midpoint check at hour 7, core freeze at hour 10 |

---

## 17. Disclosure statement (draft, adapt to the rules)

> This project extends GuruSetu, an earlier prototype by members of our team, exhibited at TechFair 2026. For Genesis we built new: certificate verification and the trust ladder, explainable Fit Check matching, the digital mentor-mentee system (allotment, session logs, action items, issues, tracking), the coordinator dashboards and the draft evidence export, plus security fixes to the original code. The earlier prototype's matching was keyword-based.

Use only if the rules allow prior code and the original owners agree.

---

## 18. How this meets typical judging criteria [ASSUMED criteria]

| Criterion | Where we earn it |
|---|---|
| Real problem | Paper mentor registers, untracked follow-ups, accreditation evidence burden; student/faculty quotes |
| Innovation | Verified-skill matching; mentoring records that become evidence as a by-product |
| Technical depth | Knowledge graph, trust-weighted explainable scoring, extraction + verification pipeline, evaluation table |
| Working demo | One end-to-end flow across four roles on seeded data |
| Impact | Time to log, follow-up visibility, compliance, evidence ready all year |
| Responsibility | Privacy matrix, DRAFT labels, synthetic data, fit-not-rank |

---

## 19. Roadmap slide (vision, not built)

From the enterprise vision: skill viva · Graph-RAG copilot with cited answers · Open Badges 3.0 signed credentials with QR verifier · auditor/peer-team portal with hash-chained evidence vault · CO-PO autopilot · NIRF simulator · SSR/AQAR draft generator · APAAR / DigiLocker / ABC · Microsoft SSO · multi-campus tenancy · DPDP consent ledger · parent and counsellor workflows · peer and alumni mentors · email/WhatsApp capture and reminders · bridge finder, team composer, funding calls, AICACE co-founder matching.

---

## 20. Decide at hour 0 (15 minutes, before any code)

1. Genesis rules on pre-existing code, and Tensor Club's agreement to reuse.
2. Team size and who takes P1–P4 (sets §13.3 / §13.4).
3. LLM provider allowed and key available? Required sponsor tools?
4. Local Docker Neo4j for the demo (recommended) vs Aura.
5. Which 1–2 accreditation indicators to encode, and who checks them against the official manual.
6. Confirm §8 defaults (45 days, 14 days, 7 days, ≥2 meetings) with one faculty member if reachable.
