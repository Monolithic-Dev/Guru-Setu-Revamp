# Plan: rich profiles for students and faculty, and matching that uses them

Status: proposal for the lead's decision. Written 2026-10-11 against `main` after the integration merge.
Audience: the four builders and the lead.

---

## 0. Verdict (read this first)

**The idea is right and it is the natural next step.** Today the matcher only knows a student's claimed and certified skills, a short bio and interests, and an opening's title, description and required skills. It knows nothing about the faculty member behind the opening, and there is no screen at all where a student can edit their profile. Richer profiles on both sides will make the recommendations noticeably better and the product much more complete.

**But the plan needs three guard rails, otherwise it creates problems:**

1. **CGPA must be an eligibility rule that faculty declare openly, never a hidden ingredient of the fit score.** Mixing marks into the score would be unexplainable and unfair, and it would break the rule that the three score parts add up to the total. (Section 4.2.)
2. **Self-reported data must stay visibly separate from verified data.** A typed CGPA, a typed skill and a resume line are *claims*. Only certificates, institutional records and mentor endorsements are *proof*. The "Claimed / Certified / Endorsed" ladder already does this for skills; the same idea must cover everything new. (Section 6.)
3. **Three of the ideas below collide with the current non-goals** (a faculty directory, suggesting students who have not applied, multi-department). They are marked **[DECISION]** and are stretch items; the core plan does not need them. (Section 11.)

**Size, honestly:** the full plan is roughly 22 builder-hours. With four people working in parallel that is about one long day. A smaller version (phases A to C plus E, about 12 builder-hours) already delivers the headline: *a real profile editor, eligibility, and better recommendations with reasons*. Phase 6 (deck, rehearsals, video, tags) is still the first priority; build this behind feature flags so nothing in the demo can break.

---

## 1. How openings are recommended today (end to end)

**Inputs the system has now**
- **Student:** `bio`, `interests` (up to 10), claimed skills (API-004; up to 30), certified skills from verified certificates, department, year, and the titles of certified certificates.
- **Opening:** title, description, 1 to 10 required skills, status, and the faculty who posted it.
- **Concept graph:** every skill is a `Concept`; related concepts are linked by `SIMILAR_TO` with a score (made from embeddings plus a hand-set override file).

**What happens when a student opens the home page** (`GET /openings`)
1. For each open opening, the scorer computes a **fit score from 0 to 100** in three parts that add up exactly:
   - **Skill part (60%).** For each required skill: *matched* if the student has it (a certified skill counts 0.85, an endorsed one 1.00, a claimed-only one 0.40); else *near* if the student has a similar skill (similarity at least 0.60, counted proportionally); else *missing*. Rarer required skills weigh more (`idf`).
   - **Meaning part (25%).** Cosine similarity between a text built from the student (`"{dept} student. Skills: ... Interests: ... Certificates: ... {bio}"`) and a text built from the opening (`"{title}. {description}. Requires: ..."`), using the local MiniLM embedding model.
   - **Related-skill part (15%).** The "near" matches.
2. A verdict is attached: **Ready** at 65 or more, **Close** from 40, otherwise **Not yet**.
3. The home page sorts openings by score, highest first, and shows the score and verdict. Opening one shows the chips (matched, claimed only, near, missing), what to certify to improve the score, and the "Why" graph.
4. When a student applies, the faculty member sees applicants ranked by the same score, with the same chips.

**What it does not use:** CGPA, year, resume, projects, availability, the faculty member's domain or subjects, opening capacity or deadline, or any eligibility rule. There is **no eligibility check** (a first-year can apply to something meant for seniors) and **no recommendation sections** (just one sorted list).

**What the user sees as missing:** a student can only change skills through the API; no screen calls it. Faculty have no profile data to edit at all.

---

## 2. What we are building (the target)

```
 STUDENT PROFILE                    FACULTY PROFILE                  OPENING (v2)
 department (read-only)             department (read-only)           required skills (as today)
 programme, year                    designation, qualifications      preferred skills (nice to have)
 CGPA: record [MOCK] + self-rep.    research areas (tags)            positions, deadline
 skills + level + proof badge       expertise (tags)                 eligible years, min CGPA,
 projects, links, headline          subjects taught (course, term)     allowed departments
 resume (PDF)                       certificates (reviewed by HOD)   strict or advisory eligibility
 availability, preferences          capacity (max guided students)   mode, duration, hours per week
 open-to-opportunities toggle       accepting or not
        │                                   │                                 │
        └───────────────┬───────────────────┴──────────────┬──────────────────┘
                        ▼                                   ▼
              ELIGIBILITY (rules, transparent)      FIT SCORE (formula unchanged, richer text)
                        └──────────────┬───────────────────┘
                                       ▼
        Recommended openings (grouped, with reasons)   ·   Find a guide (shared-topic chips)
        Ranked applicants (as today, plus eligibility)  ·   HOD mentor suggestions (assistive)
```

---

## 3. Student profile

### 3.1 Fields

| Field | Who sets it | Notes |
|---|---|---|
| Department | The institution | **Read-only.** A student cannot move themselves between departments; the HOD or the seed controls it. Shown on the page. |
| Programme (B.Tech, M.Tech, PhD, other) | Student | New. |
| Year of study (1 to 5) | Student | Editable; the page nudges "still year 3?" at the start of a term. |
| CGPA | Two sources | **Institutional record** (`AcademicRecord`, `[MOCK]` here, read-only) and **self-reported CGPA** (editable). Eligibility uses the record when it exists, else the self-reported value, **labelled "self-reported"** everywhere. |
| Headline (one line) and bio (500) | Student | Headline is new. |
| Interests (up to 10) | Student | As today. |
| Skills | Student | Typeahead over existing concepts and aliases; each has an optional self-assessed level (beginner, intermediate, advanced) shown only to the student's mentor and applied-to faculty; **trust badge** (Claimed, Certified, Endorsed) comes from the system, never from the student. Up to 30. |
| Projects (up to 10) | Student | Title, description (300), link, skills used. A project's skills do **not** become claimed skills automatically; the page offers "add these to my skills". |
| Links | Student | GitHub, LinkedIn, portfolio: `https` URLs only, validated, shown as plain links with `rel="noopener noreferrer"`. No integrations (NG-07). |
| Resume | Student | One current PDF (section 8). |
| Availability | Student | Hours per week, and available-from date. |
| Preferences | Student | Kinds of work (research project, tooling, data), preferred mode. Used only as a gentle tie-break and shown in explanations. |
| Open to opportunities | Student | Off by default. Only matters for the optional discovery feature (section 5.5). |
| Certificates | Student | Already exist (ProofOnce); the profile page shows them and the "Certify this skill" link. |

### 3.2 Profile completeness
A computed percentage (no AI): basics, at least 3 skills, at least one certificate, a project, a resume, availability. Shown as a meter with the next best action ("add 2 more skills to improve your recommendations"). It also drives the cold-start behaviour in section 4.4.

### 3.3 The editor screen
`/student/profile` (new, SCR-17), tabbed: **Basics**, **Skills**, **Projects**, **Resume**, **Preferences**. Saves per tab, so a half-finished profile is fine. Every claimed skill shows an inline "Certify this" link to the certificates page.

---

## 4. Matching v2

### 4.1 Principle
Keep **two separate questions**, because mixing them is what makes recommenders unfair and unexplainable:
1. **Can this student apply?** (eligibility: rules the faculty member wrote down, evaluated openly)
2. **How well does the student fit?** (the existing explained score)

### 4.2 Eligibility (new, rules only, no AI)

| Rule | Opening field | Check |
|---|---|---|
| Year | `eligible_years` (e.g. 3, 4) | student's year is in the list (empty list = any) |
| Department | `allowed_departments` (default: the poster's) | student's department is allowed |
| Minimum CGPA | `min_cgpa` (optional) | CGPA from the record, else self-reported; **if unknown, the rule is "unknown", not "failed"** |
| Open | `status` | opening is open |
| Deadline | `deadline` | today is on or before the deadline |
| Capacity | `positions` | accepted students are fewer than `positions` |
| Not a repeat | existing | the student has not already applied or been accepted |
| Guide load (optional) | faculty `max_guided_students` | the faculty member is not at capacity |

Each check returns `{rule, ok, detail}` in plain words ("Needs CGPA 7.5 or more; yours is 7.1 (self-reported)"). The opening's **eligibility mode** is set by the faculty member:
- **Advisory (default):** the student sees the warning and may still apply; the faculty member sees the same warning next to the applicant.
- **Strict:** applying is refused with `409 NOT_ELIGIBLE` and the failing rules listed.

**CGPA never enters the fit score.** It appears only as a visible rule. Nothing about the student's name, gender, community or photo is stored or used anywhere.

### 4.3 Fit score (formula unchanged)
The three components, the weights (25, 60, 15), the verdict cut-offs and the exact-sum rule stay as they are, so every existing test and the demo numbers (42.7 to 70.0) keep working. What improves is the **text** behind the meaning part:
- **Student text** gains programme, year, project titles, headline and (later) confirmed resume keywords.
- **Opening text** gains the faculty member's research areas and the subjects they teach, plus preferred skills.
Be honest in the pitch: this lifts only the 25% meaning part, so the effect is real but modest. The bigger gains come from eligibility, grouping and reasons.

### 4.4 Recommendation page (home) v2
Sections, in order, each with a one-line reason built from the chips (templates, no LLM):
1. **Best matches** (eligible, score 65 or more)
2. **Worth a look** (eligible, 40 to 64)
3. **Stretch** (eligible, below 40, collapsed by default)
4. **Not eligible yet** (never hidden: shows the failing rule so the student knows what to change)

Ordering inside a section: score, then more *matched* (verified) skills, then sooner deadline, then more positions left. Filters: department, mode, deadline within 14 days.

**Cold start** (fewer than 2 skills): rank by the meaning part from interests, department, programme and coursework, label the list "Based on your interests" and show the completeness meter at the top.

### 4.5 Student to faculty: "Find a guide" [DECISION]
A directory of faculty with open positions or an interest in the student's area, ranked **per student** by *shared topics* (the student's skills and interests against the faculty member's research areas and subjects, using the same concept-similarity map). It shows shared-topic chips and the faculty member's open openings, **not a numeric score and never a leaderboard**. This relaxes NG-10 (recommender routes) and NG-11 (no global ranking of faculty), so it needs the lead's sign-off; the compromise is "ordered by overlap, shown as chips, only visible to the student it was computed for".

### 4.6 Faculty to student, for their own opening
- **Applicants** (as today): ranked by fit, now also showing eligibility status and the student's availability.
- **Suggested students** (optional, section 5.5).

### 4.7 HOD: mentor suggestion (assistive)
On the allotment screen, each unallotted student gets a **suggested mentor**: mentors under the load limit ordered by domain overlap with the student, with the reason ("shares: machine learning, vision; load 11 of 20"). The HOD still decides; nothing is auto-assigned.

---

## 5. Faculty profile

### 5.1 Fields

| Field | Notes |
|---|---|
| Department, designation, employee id | Department read-only; designation already exists. |
| Qualifications | Degree, institution, year (up to 5). Self-reported; becomes "verified" when a certificate is approved by the HOD. |
| Research areas | Concept tags (up to 10, one marked primary). The strongest matching signal on the faculty side. |
| Expertise | Concept tags (up to 15). |
| Subjects taught | Course code, title, term, topic tags (up to 15). Shows what students will have studied with them. |
| Selected publications | Optional titles, up to 10, labelled "self-listed" (no Scopus or ORCID integration, NG-07). |
| Capacity | `max_guided_students` and an "accepting guides" switch. Used by eligibility and by the directory. |
| Office hours | Free text, up to 200 characters. |
| Links | Same rules as students. |
| Certificates | Same ProofOnce pipeline (upload, read, verify); **reviewed by the HOD** because a faculty member has no mentor. Tags backed by a verified certificate show a "Verified" badge. |

### 5.2 Editor
`/faculty/profile` (new, SCR-18): **Basics**, **Research and expertise**, **Subjects**, **Certificates**, **Capacity**. The public view reuses the existing `/faculty-profile/[id]` page (track record, facts only) and adds the profile above it.

### 5.3 How faculty data is used
- **Opening text** (section 4.3), so a student's meaning match reflects the faculty member's domain.
- **Directory** and **HOD mentor suggestion** (sections 4.5 and 4.7).
- **Capacity** in eligibility.

### 5.4 Opening v2 (new fields, all optional so old openings keep working)
`positions` (default 1), `deadline`, `eligible_years`, `min_cgpa`, `allowed_departments`, `eligibility_mode` (advisory or strict), `mode` (on campus, remote, hybrid), `duration_weeks`, `hours_per_week`, `preferred_skills`. When accepted students reach `positions`, the opening closes by itself and a status event records why.

### 5.5 Optional: open-to-opportunities discovery [DECISION]
A student can switch on "open to opportunities". A faculty member then sees, for their own opening, **suggested students** among those who opted in: verified skills and the fit score only, no CGPA value, no resume, no contact details. The faculty member can send an **invitation**, which is a notification linking to the opening; the student decides whether to apply. This contradicts REQ-005 ("non-applicants are never listed") and NG-11 unless the student consents, so it is opt-in, off by default, and a stretch phase.

---

## 6. Privacy, trust and fairness rules (extends security section 4)

| Data | Student (self) | Assigned mentor / guide | Faculty with the student as applicant | HOD | IQAC |
|---|---|---|---|---|---|
| Programme, year, headline, bio, links | ✔ | ✔ | ✔ | ✔ | ✘ |
| CGPA value | ✔ | ✔ assigned mentor | pass or fail on the rule only | ✔ | ✘ |
| Self-assessed skill level | ✔ | ✔ | ✔ | ✔ | ✘ |
| Projects | ✔ | ✔ | ✔ | ✔ | ✘ |
| Resume file | ✔ | ✔ | ✔ **only after applying** | ✔ | ✘ |
| Availability, preferences | ✔ | ✔ | ✔ | ✔ | ✘ |
| Open-to-opportunities flag | ✔ | ✘ | only if on, and only the discoverable card | ✘ | ✘ |
| Faculty profile | public to every signed-in user | | | | |
| Faculty certificates and their review | the faculty member | | | ✔ | ✘ |

Rules that never change:
- **Self-reported is always labelled** and never raises a trust level. Trust levels come from certificates, endorsements and institutional records only.
- **No sensitive attributes** are collected: no gender, caste, religion, photo, parents' details or contact numbers.
- **Explain every ordering.** Each recommendation shows its reasons; ineligible openings show the failing rule.
- **Fairness check script:** recompute the ranking after swapping student names and confirm nothing changes; confirm CGPA never appears in any score component.
- **No private text in logs or exports.** Resume content, project text and links never reach logs, dashboards or exports.
- **No DELETE routes** (project rule): lists are saved by replacement ("save the full list"), the resume is superseded by a newer one, and the old file is marked superseded. A purge for real deployments is a documented operations task, not an API.

---

## 7. Data model (additive; update `schema.cypher` in a `CONTRACT:` commit first)

```
Student   + programme, headline, self_reported_cgpa, availability_hours, available_from,
            open_to_opportunities, links[], preferences[], profile_updated_at
(Student)-[:HAS_PROJECT]->(Project {id, title, description, link, skills[]})
(Student)-[:HAS_RESUME]->(Resume {id, file_path, sha256, size_bytes, pages, uploaded_at, status: current|superseded})

Faculty   + max_guided_students, accepting_guides, office_hours, links[], publications[]
(Faculty)-[:RESEARCHES {primary}]->(Concept)
(Faculty)-[:EXPERT_IN]->(Concept)
(Faculty)-[:TEACHES {term_id}]->(Course {code, title, topics[]})
(Faculty)-[:HOLDS]->(Qualification {id, degree, institution, year, verified})

Opening   + positions, deadline, eligible_years[], min_cgpa, allowed_departments[], eligibility_mode,
            mode, duration_weeks, hours_per_week
(Opening)-[:PREFERS]->(Concept)

Evidence: `SUBMITTED` may now come from a Faculty; add `owner_role`. Review by the HOD for faculty-owned evidence.
Indexes: Resume.id unique, Project.id unique, Course (code, dept) unique, Qualification.id unique.
```
Neo4j cannot store lists of maps as properties, so projects, qualifications and courses are small nodes. Nothing existing is renamed or removed, so old data and tests keep working.

---

## 8. Resume handling (how, safely)

**Upload:** `POST /me/resume` (multipart, PDF only). Same intake rules as certificates: real file-type check (`%PDF-`), at most 5 MB and 4 pages, stored privately as `UPLOAD_DIR/resumes/<uuid>.pdf`, never served publicly, rate-limited (5 per hour). A new upload supersedes the old one.

**Download:** `GET /students/{id}/resume/file` with the scope in section 6 (404 outside it, never leaking existence), `inline`, `nosniff`.

**Suggestions (optional, stretch):**
1. **Phase 1, no AI:** read the PDF text layer (pypdfium2, already a dependency) and match words against concept names and aliases. Show "We found these skills in your resume: ..." with checkboxes.
2. **Phase 2, with AI:** reuse the existing Groq extraction pattern to propose skills and projects from the resume, with the same controls as certificates (fixed prompt, schema-only output, `contains_instructions` flag, daily cap, cache, timeout, manual fallback).
3. **Whatever the method, a student must confirm each item**, and confirmed skills become **claimed (trust 0)**. A resume never certifies anything.
4. Resume text is never logged, and is deleted from memory after matching.

---

## 9. API additions (all additive; IDs continue after API-045)

| ID | Method and path | Purpose | Roles | Phase |
|---|---|---|---|---|
| API-046 | `PATCH /me/profile` (extended) | programme, year, headline, self-reported CGPA, links, availability, preferences, open flag, projects (full list) | S | A |
| API-047 | `GET /concepts?q=` | skill typeahead | S, F | A |
| API-048 | `GET /me/profile` | own profile with completeness and per-field trust labels | S | A |
| API-049 | `PATCH /openings/{id}` and extended `POST /openings` | opening v2 fields | F (owner) | B |
| API-050 | `GET /openings` (extended) | adds `eligibility`, `group`, `reasons`; sorting `recommended` | S | B |
| API-051 | `GET /openings/{id}/fit` (extended) | adds `eligibility` | S, F | B |
| API-052 | `GET /me/faculty-profile`, `PATCH /me/faculty-profile` | faculty profile; replace-lists for research, expertise, courses, qualifications | F | C |
| API-053 | `GET /faculty/{id}` (extended) | public profile plus the existing track record | all | C |
| API-054 | `POST /certificates` by faculty; review by HOD | faculty certificates through ProofOnce | F, H | C |
| API-055 | `POST /me/resume`, `GET /me/resume` | upload and metadata | S | D |
| API-056 | `GET /students/{id}/resume/file` | scoped download | S, F, H | D |
| API-057 | `POST /me/resume/suggestions`, `POST /me/resume/suggestions/apply` | optional skill suggestions | S | D |
| API-058 | `GET /faculty?query=&accepting=` | guide directory with shared-topic chips | S | E [DECISION] |
| API-059 | `GET /dept/allotment` (extended) | `suggested_mentor` per unallotted student | H | E |
| API-060 | `GET /openings/{id}/suggested-students`, `POST /openings/{id}/invitations` | opt-in discovery and invitation | F (owner) | F [DECISION] |

Every route keeps the project rules: explicit response models, 403 for the wrong role, 404 for outside scope, problem+json errors, one write transaction per change with a status event, no DELETE.

---

## 10. Screens

| ID | Route | Role | Content | Phase |
|---|---|---|---|---|
| SCR-17 | `/student/profile` | student | Tabbed editor with completeness meter, skill typeahead and badges, projects, resume | A, D |
| SCR-02 (changed) | `/student` | student | Sections: Best matches, Worth a look, Stretch, Not eligible yet; reasons; filters; cold-start banner | B |
| SCR-03 (changed) | `/student/openings/[id]` | student | Eligibility checklist above the fit panel | B |
| SCR-15 / SCR-09 (changed) | `/faculty/openings/new`, `/faculty/openings/[id]` | faculty | Opening v2 fields; applicants show eligibility and availability | B |
| SCR-18 | `/faculty/profile` | faculty | Tabbed editor: basics, research and expertise, subjects, certificates, capacity | C |
| SCR-16 (changed) | `/faculty-profile/[id]` | all | Profile plus track record | C |
| SCR-19 | `/student/guides` | student | Directory with shared-topic chips and open openings | E |
| SCR-12 (changed) | `/coordinator/allotment` | HOD | Suggested mentor chip with the reason | E |
| SCR-20 | `/faculty/openings/[id]/suggested` | faculty | Opt-in suggested students, invite button | F |

Navigation: add **Profile** to the student and faculty menus in `src/lib/nav.ts`, and **Find a guide** to the student menu (flagged).

---

## 11. Decisions the lead must make

| # | Decision | Recommendation |
|---|---|---|
| X-1 | Lift NG-10 and NG-11 for the guide directory (4.5)? | **Yes, in the restricted form** (chips only, per-student, no scores, no leaderboard). |
| X-2 | Allow student discovery by faculty (5.5)? | **Not now.** Stretch only, opt-in, after the core ships; it contradicts REQ-005. |
| X-3 | Default eligibility mode | **Advisory.** Strict is opt-in per opening. |
| X-4 | CGPA source for eligibility | Institutional record first, self-reported second, always labelled. |
| X-5 | Multi-department students (NG-09) | **Keep one department** in the UI; the `allowed_departments` field is stored but defaults to the poster's department. |
| X-6 | Resume parsing with AI | Start with the no-AI text match; add the Groq pass only if time remains (token limit is about 3 documents per minute). |
| X-7 | Right to erasure vs "no DELETE routes" | Keep the project rule; document an operator-run purge for any real deployment. |

---

## 12. Edge cases (and what the system does)

**Student profile**
- *Brand-new student, nothing filled in:* cold-start list from department and programme, completeness meter, prompt to add skills.
- *Student types a skill nobody has used:* normalised through aliases; created as a concept with `source: claimed`; capped at 30 skills; typeahead nudges toward existing names to avoid near-duplicates ("pytorch" vs "py torch").
- *Typo-squatting or spam skills:* length and count limits; HOD can merge or alias concepts later (stretch).
- *Claimed skill later certified:* the badge upgrades; the self-assessed level stays.
- *Certificate rejected after a skill was certified:* the existing trust recompute drops it back to claimed.
- *CGPA typed as 9.9 with no record:* accepted but labelled "self-reported"; eligibility shows "unverified" and the faculty member can see that.
- *CGPA record and self-reported disagree:* the record wins; the page shows both.
- *Year changes mid-term:* eligibility is re-evaluated on every read, never cached.
- *Student changes year to something false to qualify:* advisory mode shows the warning to the faculty member, who sees the year; the mentor sees it too. The institutional record can later override.
- *Links with `javascript:` or a non-https scheme:* rejected with a field error.
- *Resume is an image-only PDF:* no text layer, so the no-AI suggestions return nothing; the student is told and can add skills manually.
- *Resume contains instructions aimed at an AI:* only reached in the AI phase; same containment as certificates (flag, schema-only output, human confirmation).
- *Resume with a photo or phone number:* stored privately; never displayed in lists; downloadable only under the scope table.
- *Student uploads a huge or corrupt PDF:* same 413, 415, 422 responses as certificates; temp file removed.
- *Student has no mentor yet:* profile works fully; mentorship sections show the existing empty state.

**Faculty profile**
- *Faculty with no research areas:* the meaning text falls back to the opening description; the directory lists them last with "no research areas listed".
- *Faculty with research areas but no openings:* appear in the directory with "no open positions"; students can still see the profile.
- *Faculty at capacity:* openings show "Full" and are listed under Not eligible with the reason; the faculty member can raise the limit.
- *Faculty uploads a degree certificate with a different name format (Dr., initials):* the existing name normalisation applies; mismatches go to the HOD queue.
- *Faculty has no HOD to review (single-user test data):* certificates wait in `needs_review`; nothing is auto-approved.
- *Faculty on leave or retired:* `accepting_guides` off hides them from the directory and closes new applications.
- *Faculty teaches a subject but has no research in it:* subjects are weighted below research areas in alignment (research counts 1.0, expertise 0.7, subject 0.5).

**Openings and matching**
- *Opening with `min_cgpa` and a student with unknown CGPA:* the rule shows "unknown", not "failed"; in strict mode the student is told to add a CGPA; the faculty member sees "unverified".
- *Strict opening and an ineligible student tries the API directly:* `409 NOT_ELIGIBLE` with the failing rules, regardless of the UI.
- *Deadline passes after the student opened the page:* apply returns the same error as a closed opening.
- *Two students accepted for the last position at the same time:* the accept runs in one transaction that re-checks capacity; the second gets `409` "positions filled".
- *Positions filled:* the opening closes with a status event and a notification to the owner.
- *Opening edited after applicants exist:* eligibility changes do not remove existing applicants; the faculty member sees which applicants no longer pass.
- *Cross-department students (when `allowed_departments` has more than one):* works in the rules; the UI keeps one department for now (X-5).
- *Student already accepted elsewhere:* allowed (a student may guide-link with several faculty) unless the faculty sets a per-student cap later; shown as information.
- *Identical scores:* deterministic tie-break (matched count, deadline, positions left, then application time).
- *No openings at all:* the existing empty state.
- *Very many openings (hundreds):* group counts and pagination; the scorer already runs per opening and the data is small (A-11), so cap at 50 per page.
- *Student interests change:* embeddings are recomputed on every profile save (already the rule).

**System and process**
- *Embedding model unavailable:* the existing fallback behaviour; the page shows scores without the meaning part rather than failing.
- *LLM down or rate-limited (resume AI phase):* the no-AI path still works; the AI button reports "try again later".
- *Concurrent edits (two tabs):* last write wins per section; saves are full-list replacements and return the stored value.
- *Old clients and old data:* every new field is optional; old openings behave as "any year, any CGPA, 1 position, no deadline".
- *Accessibility:* every new form is label-based, keyboard reachable, and shows status as text, not colour only.
- *Offline demo:* none of the new features need the network except the optional resume AI phase.

---

## 13. Delivery plan

All work is behind feature flags in `src/lib/features.ts` (`studentProfile`, `eligibility`, `facultyProfile`, `resume`, `guideDirectory`, `discovery`). Each phase ends with the full backend suite, `tsc`, lint and a fresh seed all green, and the index section 7 scenario still passing.

| Phase | Hours (builder) | Owner split | Content | Done when |
|---|---|---|---|---|
| **A: Student profile** | 4 | P2 backend 2 · P3 UI 2 | Contract and schema commit (`CONTRACT:`); API-046/047/048; completeness; SCR-17 tabs Basics, Skills, Projects, Preferences; nav item | A student edits skills and basics in the UI, sees badges and completeness; self-reported CGPA is labelled; tests TEST-60..63 |
| **B: Opening v2 and eligibility** | 5 | P2 eligibility service and APIs 2 · P1 text enrichment and ordering 1 · P3 SCR-02/03/09/15 changes 2 | New opening fields; eligibility rules and `409 NOT_ELIGIBLE`; grouping and reasons; cold start | Home shows the four groups with reasons; strict and advisory modes behave; capacity race test passes; demo scenario unchanged (42.7 to 70.0) |
| **C: Faculty profile** | 4 | P2 backend 2 · P3 UI 2 | Faculty fields, courses, qualifications, capacity; API-052/053/054; HOD review for faculty certificates; opening text gains faculty areas; SCR-18; SCR-16 extended | A faculty member edits their profile and uploads a certificate that the HOD reviews; student sees the profile |
| **D: Resume** | 4 | P2 intake and scope 2 · P3 UI 1 · P1 suggestions 1 | Upload, supersede, scoped download; no-AI suggestions; confirm-to-claim | Student uploads a PDF; applied-to faculty can open it, others get 404; suggestions need confirmation |
| **E: Guide directory and HOD suggestion** | 3 | P1 alignment 1 · P2 API 1 · P3/P4 UI 1 | API-058/059; SCR-19; chip on SCR-12 | Directory ordered by shared topics, no scores; HOD sees a suggested mentor with the reason |
| **F: Discovery (stretch)** | 3 | P2 · P3 | Opt-in flag, suggested students, invitations | Only opted-in students appear; no CGPA or resume shown; invitation notifies |

**Smaller version:** A + B + C (minimum) + E ≈ 16 builder-hours, about a day with four people. A alone (4 hours) already closes the biggest visible gap.

**Seed changes (P4, with each phase):** profiles for all 50 students (programme, year, headline, 2 to 5 skills, one project for about half, availability), research areas, expertise, subjects and capacity for the four faculty and the HOD, v2 fields on the 12 openings (a few with `min_cgpa` and `eligible_years`, one nearly full, one with a near deadline) so the demo can show an ineligible opening and a "Full" badge.

**Demo script additions:** 1) Aarav fills in his profile and sees his completeness rise; 2) the home page regroups into Best matches and Not eligible yet, with the failing rule named; 3) Dr. Meera's profile feeds the opening's reasons; 4) Suresh sees a suggested mentor with the reason.

---

## 14. Test plan (new IDs continue the strategy list)

| ID | What | Layer |
|---|---|---|
| TEST-60 | Profile fields save, omit-vs-null semantics, field limits, `https`-only links | backend |
| TEST-61 | Skill typeahead and normalisation; cap of 30; certified skill survives un-claiming | backend |
| TEST-62 | Trust labels: self-reported CGPA is labelled; nothing self-reported raises a trust level | backend |
| TEST-63 | Completeness percentage on hand-built profiles | backend |
| TEST-64 | Every eligibility rule, including "unknown" CGPA; advisory vs strict; `409 NOT_ELIGIBLE` on a direct call | backend |
| TEST-65 | Capacity race: two accepts for the last position, one succeeds, the opening closes with a status event | backend |
| TEST-66 | Recommendation groups, ordering and tie-breaks are deterministic; cold start | backend |
| TEST-67 | The fit formula and the 42.7 to 70.0 demo numbers are unchanged; CGPA appears in no component | backend |
| TEST-68 | Fairness: swapping student names does not change any ranking | backend |
| TEST-69 | Resume intake (type, size, pages), supersede, scope matrix (self, mentor, HOD, applied-to faculty, other faculty 404, IQAC 403) | backend |
| TEST-70 | Resume text never in logs; suggestions require confirmation and create claimed (trust 0) skills only | backend |
| TEST-71 | Faculty profile replace-lists; faculty certificate reviewed by HOD only | backend |
| TEST-72 | Directory ordering by shared topics, no numeric score in the response | backend |
| TEST-73 | HOD suggested mentor respects the load limit | backend |
| TEST-74 | Browser: edit profile, see regrouped home, apply to a strict opening and see the refusal | Playwright |
| TEST-75 | Accessibility (Lighthouse at least 90) and 360 px on SCR-17 and SCR-18 | manual |

---

## 15. Risks and how the plan handles them

| Risk | Handling |
|---|---|
| Scope creep before the review or submission | Flags per phase; Phase 6 stays first; the smaller version is a clean cut line. |
| Bias or unexplainable ranking | CGPA is a visible rule only; the score formula is untouched; fairness test; reasons everywhere. |
| Sensitive data leaks (resume, CGPA) | Scope table; omit-not-null fields; scoped file route with 404; no logging of content; IQAC sees none of it. |
| Fake or inflated self-reported data | Always labelled; never raises trust; mentors and faculty see the label; certificates remain the only path to "verified". |
| Resume AI cost and injection | Optional second step; same controls as certificates; no-AI path first. |
| Breaking the demo | Additive contract, optional fields, unchanged score formula, existing tests as the regression net, flags off by default until each phase passes. |
| Concept spam from free-text skills | Count and length limits, normalisation, typeahead nudge, later HOD merge tool. |

---

## 16. Summary of the answer to "is this plan good to go?"

**Yes, with the guard rails.** Build in this order: **A (profile editor)** because it fixes the biggest visible gap alone, then **B (eligibility and grouped recommendations)**, then **C (faculty profile)**, then **E (suggestions)**, with **D (resume)** when time allows and **F (discovery)** only if the lead accepts the consent trade-off. Keep the fit formula unchanged, keep CGPA out of the score, label everything self-reported, and ship each phase behind a flag with the existing tests as the safety net.
