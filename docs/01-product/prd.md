# Product Requirements: GuruSetu Verified Mentorship Graph
Purpose:      Define what this build must do, for whom, and how each behaviour is accepted; every other document traces to the IDs here.
Audience:     The 4-person team and coding agents building the backend, frontend and AI pipeline.
Depends on:   none
Inputs used:  docs/plan/prd-v2-and-15h-plan.md (PRD v2), Ideas/gurusetu-pramaan-concept.md, Ideas/gurusetu-enterprise-vision.md, Ideas/GENESIS-GuruSetu-Audit-and-Proposal.md
Status:       Draft v1 | assumptions in this document: A-01, A-02, A-03, A-04, A-05, A-06, A-07, A-08, A-09, A-10, A-11, A-12, A-15

Personas and the glossary are sections of this document (small project).

---

## 1. Summary

College mentoring runs on signed paper registers. Nobody can see which mentee hasn't been met or what was promised in the last meeting. Student skills are self-claimed and unchecked, and accreditation evidence (NAAC mentoring ratio, mentor-wise issues raised and resolved, student achievements) is compiled by hand before every audit.

**Target users:** students, faculty mentors, HOD and IQAC coordinators in one department.

**Outcome:** students prove skills once with verified certificates and use that proof to find research guides. Mentors log and track sessions, action items and issues in under two minutes. The department gets live coverage and compliance numbers, plus a one-click draft evidence pack containing aggregates only.

## 2. Goals and non-goals

| ID | Goal |
|---|---|
| G-01 | A student's certificate becomes a verified skill without manual data entry, with duplicates and mismatches caught. |
| G-02 | A student sees, for any opening, an explained fit score built on verified skills, and can apply. |
| G-03 | Every student has an assigned mentor, and every mentoring session, action item and issue is recorded and tracked digitally. |
| G-04 | A mentor sees in one screen which mentees need attention, and why. |
| G-05 | HOD and IQAC see coverage and compliance live, and export draft accreditation evidence containing no private notes. |

| ID | Non-goal (this build will not…) |
|---|---|
| NG-01 | Allow self-signup. Demo accounts are seeded; the old registration and photo-upload routes are deleted (A-04). |
| NG-02 | Offer password reset or recovery in any form. |
| NG-03 | Store or display real student data, or migrate data from the old GuruSetu database. |
| NG-04 | Provide a chatbot, Graph-RAG copilot, or any free-form LLM chat. |
| NG-05 | Run skill vivas, issue Open Badges / verifiable credentials, or provide QR verification pages. |
| NG-06 | Provide an auditor portal, hash-chained evidence vault, CO-PO attainment, NIRF simulator or SSR/AQAR drafting. |
| NG-07 | Integrate APAAR, DigiLocker, ABC, AUMS, ORCID/Scopus, IRINS/VIDWAN or any SSO. Academic snapshots are seeded `[MOCK]`. |
| NG-08 | Send email, SMS, WhatsApp or push notifications. Only in-app notifications exist. |
| NG-09 | Support multiple campuses or departments in the UI. The data model carries `dept_code`, but the seed holds one department. |
| NG-10 | Keep the old faculty collaboration hub, express-interest, student/faculty portfolio routers, AI recommender routes or mock pages. They are deleted. |
| NG-11 | Rank students or faculty globally, or show leaderboards or ratings of faculty. Scores are fit-to-one-opening only. |
| NG-12 | Build a native mobile app. The web UI must work at 360 px width. |
| NG-13 | Provide parent/guardian contact logs, counsellor referral, or peer/alumni mentors. |
| NG-14 | Verify certificates by QR code or issuer verify URL, or detect forgery beyond the signals in REQ-025. |
| NG-15 | Claim accuracy figures that §9 has not measured. |

## 3. Users and roles

| Role (`role` value) | Wants | Can do | Auth |
|---|---|---|---|
| Student (`student`) | Prove skills, find a guide/opening, track own mentoring | Upload certificates, view fit, apply, confirm sessions, mark action items done, raise issues (P1), request a meeting (P1) | Email + password (seeded), JWT |
| Faculty (`faculty`) | Know which mentees need attention; log sessions fast; see verified applicants | Everything on own mentees and own openings: log sessions, manage actions and issues, review own mentees' certificates, move own applications | Same |
| HOD (`hod`) | Coverage, compliance, allotment | Allot mentors, view department dashboard and needs-attention list, review any department certificate, handle escalated issues, export evidence | Same |
| IQAC (`iqac`) | Accreditation evidence | View department dashboard (aggregates only), export evidence | Same |

HOD and IQAC share one "Coordinator" area in the UI with role-dependent content (A-03). Field-level visibility is defined once in [security-and-privacy.md §4](../08-security/security-and-privacy.md).

**Personas (synthetic):**
- **Aarav Menon**, 2nd-year CSE student, has PyTorch only as a claimed skill.
- **Dr. Meera Raman**, faculty, is the assigned mentor of 13 students and owns the opening "Edge AI for Agriculture".
- **Dr. Suresh Iyer**, HOD CSE.
- **Ms. Kavya Nair**, IQAC coordinator.

## 4. Glossary

| Term | Meaning |
|---|---|
| Assigned mentor | The faculty member allotted by the HOD. Each student has at most one active assigned mentor. Counts for the NAAC mentoring ratio. |
| Research guide | A faculty member linked to a student when the student's application to that faculty member's opening is accepted. Zero or more per student. |
| Trust level | 0 Claimed, 1 Certified, 2 Faculty-verified (P2). The match weight of a skill depends on its trust level. |
| Fit Check | The explained fit score of one student for one opening. Never a global ranking. |
| Term | An academic semester with start and end dates; "this term" means the term whose dates contain today (A-08). |
| Needs attention | A derived mentee flag with one or more reasons; rules in [backend.md §6.4](../04-backend/backend.md). |
| Evidence pack | An XLSX export of aggregates and lists, labelled DRAFT. |

## 5. User stories

| ID | Tier | Story | REQs |
|---|---|---|---|
| US-01 | P0 | As a student, I upload a certificate photo and my skill turns from Claimed to Certified without typing anything. | REQ-001, 002, 003, 037 |
| US-02 | P0 | As a student, I open an opening and see my fit, what is proven, what is only claimed, and what is missing. | REQ-004 |
| US-03 | P0 | As a student, I apply to an opening and follow its status. | REQ-006, 038 |
| US-04 | P0 | As faculty, I see applicants for my opening ranked by fit, with verified skills marked. | REQ-005, 006 |
| US-05 | P0 | As HOD, I allot mentees to mentors and see who is unallotted. | REQ-007 |
| US-06 | P0 | As a mentor, I log a group session for 12 mentees with action items in under two minutes. | REQ-008, 010, 011 |
| US-07 | P0 | As a mentee, I confirm I attended and tick off my action items. | REQ-009, 010, 014 |
| US-08 | P0 | As a mentor, I open one screen and know which mentees need follow-up and why. | REQ-012, 013 |
| US-09 | P0 | As a mentee, I trust that my session notes are seen only by my mentor. | REQ-015 |
| US-10 | P0 | As HOD, I see coverage, compliance and issue resolution for my department. | REQ-016 |
| US-11 | P0 | As IQAC, I export a draft mentoring pack and achievements list without private content. | REQ-017 |
| US-12 | P1 | As IQAC, I click a dashboard number and see the records behind it. | REQ-019 |
| US-13 | P1 | As a student, I see why I match and which skill unlocks the most openings. | REQ-020, 021 |
| US-14 | P1 | As a mentor, I am reminded about overdue actions, stale issues and mentees not met. | REQ-023 |
| US-15 | P1 | As a mentee, I raise an issue or ask my mentor for a meeting. | REQ-024 |
| US-16 | P1 | As a mentor, I escalate an issue to the HOD or mark it confidential. | REQ-022, 036 |
| US-17 | P2 | As faculty, I endorse a student's skill after working with them. | REQ-027 |
| US-18 | P2 | As HOD, I change a student's mentor and keep the history. | REQ-028 |

## 6. Functional requirements

Priorities: **P0** = CORE (must ship), **P1** = ADD-ON A, **P2** = ADD-ON B. Endpoints (API-), screens (SCR-) and tests (TEST-) that realise each REQ are listed in the index traceability table.

### 6.1 Access
**REQ-031 (P0) Login and role routing.** When a seeded user submits a correct email and password, the system shall issue a JWT and route the user to their role's home screen.
- AC-031.1 Given `aarav@demo.gurusetu` / `Demo@123`, when they log in, then the response is 200 with a token and the UI opens `/student`.
- AC-031.2 Given a wrong password, when they log in, then the response is 401 with code `INVALID_CREDENTIALS` and the message "Email or password is incorrect."
- AC-031.3 Given an expired or missing token, when any protected page loads, then the UI redirects to `/login`.

### 6.2 Verify (certificates and trust)
**REQ-001 (P0) Certificate extraction.** When a student uploads a JPG, PNG or PDF of up to 10 MB, the system shall extract the holder name, title, issuer, issue date, level, type and up to 8 skills, and show them with a confidence score.
- AC-001.1 Given a seeded demo certificate image, when it is uploaded, then within 20 s (2 s if cached) the certificate shows status `certified` or `needs_review`, the extracted fields, and a confidence between 0 and 1.
- AC-001.2 Given an 11 MB file, when it is uploaded, then the response is 413 `FILE_TOO_LARGE` and nothing is stored.
- AC-001.3 Given a `.docx` file renamed to `.pdf`, when it is uploaded, then the response is 415 `UNSUPPORTED_FILE_TYPE`.

**REQ-002 (P0) Verification routing.** If an uploaded certificate is a duplicate or fails the name, issuer or date checks, then the system shall mark it `duplicate` or route it to `needs_review`, and a reviewer shall approve or reject it with a reason.
- AC-002.1 Given a file whose SHA-256 or perceptual hash matches an existing certificate, when it is uploaded, then its status is `duplicate`, the reason names the matching certificate, and no skill changes.
- AC-002.2 Given a certificate whose holder name does not match the student's name (fuzzy score < 85), when it is processed, then its status is `needs_review` with reason `name_mismatch`.
- AC-002.3 Given a `needs_review` certificate of Dr. Meera's mentee, when Dr. Meera approves it, then its status becomes `certified` and the student is notified; when she rejects it with reason "Name differs", then it becomes `rejected` and the reason is shown to the student only.
- AC-002.4 Given faculty who is not the student's assigned mentor, when they request that certificate's review, then the response is 404.

**REQ-037 (P0) Manual entry fallback.** If extraction fails (provider error, timeout, refusal, or `LLM_PROVIDER=none` with no cache hit), then the system shall set the status to `failed` and let the student type the fields, after which the certificate goes to `needs_review`.
- AC-037.1 Given `LLM_PROVIDER=none` and an uncached file, when it is uploaded, then the status is `failed` and the UI shows a manual-entry form.
- AC-037.2 Given the manual form is submitted, then the status is `needs_review` and the confidence is capped at 0.5.

**REQ-003 (P0) Trust level from evidence.** When a certificate becomes `certified`, the system shall set each skill it proves to trust level ≥ 1 on the student's profile and show the source certificate.
- AC-003.1 Given Aarav has PyTorch at trust 0, when a certificate proving "pytorch" is certified, then his PyTorch skill shows "Certified · <certificate title>".
- AC-003.2 Given a certificate is later rejected, then skills whose only proof was that certificate return to their previous level (0 if claimed, removed if not claimed).

**REQ-025 (P1) Tamper signals.** Where tamper checking is enabled, the system shall route images whose metadata names an image editor, or whose error-level-analysis score exceeds the threshold, to `needs_review` with reason `tamper_signal`.
- AC-025.1 Given the planted edited certificate (EXIF Software = "Adobe Photoshop"), when it is uploaded, then its status is `needs_review` with reason `tamper_signal`.

**REQ-027 (P2) Faculty endorsement.** When a faculty member who is a mentor or guide of a student endorses one of the student's skills, the system shall set that skill to trust level 2.
- AC-027.1 Given Dr. Meera guides Aarav, when she endorses "pytorch", then it shows "Faculty-verified · Dr. Meera Raman".

### 6.3 Match
**REQ-004 (P0) Fit Check.** When a student opens an opening, the system shall show a fit score from 0 to 100 with semantic, skill and concept components that sum to the total, chips for each required skill (matched with trust badge / near via a similar concept / claimed-only / missing), a verdict, and the score gain if each claimed-only or missing skill were certified.
- AC-004.1 Given seed data, when Aarav opens "Edge AI for Agriculture" before uploading anything, then his score is between 38 and 50, the verdict is "Close", PyTorch shows as claimed-only and computer vision as near (via deep learning).
- AC-004.2 Given any fit response, then `semantic + skill + concept` equals `score` to within 0.1.
- AC-004.3 Given score ≥ 65 the verdict is "Ready to apply"; 40–64.9 is "Close"; below 40 is "Not yet" (thresholds `FIT_READY_MIN`, `FIT_CLOSE_MIN`; formula in ai-system §4).
- AC-004.4 Given an opening with no required skills, then the score is based on semantic similarity only and the UI says "This opening lists no required skills."

**REQ-005 (P0) Ranked candidates.** When faculty open their own opening, the system shall list its applicants sorted by fit score, each with trust-marked skill chips. Non-applicants are never listed (NG-11).
- AC-005.1 Given Dr. Meera's opening with 4 applicants, then the applicants appear sorted by score descending, each showing its Certified/Claimed chips.
- AC-005.2 Given faculty who do not own the opening, when they request candidates, then the response is 404.

**REQ-006 (P0) Apply and decide.** When a student applies to an open opening, the system shall create a `pending` application. The opening's owner shall move it only along pending → shortlisted → accepted/rejected (pending → rejected also allowed; accepted → completed). Each transition notifies the student. Acceptance creates a research-guide link.
- AC-006.1 Given Aarav applies twice to the same opening, then the second call returns 409 `ALREADY_APPLIED`.
- AC-006.2 Given a `pending` application, when the owner sets `accepted` directly, then the response is 409 `INVALID_TRANSITION`.
- AC-006.3 Given the owner accepts a shortlisted application, then Aarav sees status "Accepted" and Dr. Meera appears under "My guides" on his mentorship page.
- AC-006.4 Given a student tries to change an application status, then the response is 403.

**REQ-030 (P1) Create opening.** When faculty submit a title (5–120 chars), description (≤ 2000 chars) and 1–10 required skills, the system shall create an open opening and compute its embedding.
- AC-030.1 Given a valid form, then the opening appears in students' opening lists with fit scores.

**REQ-020 (P1) Why this match.** When a student taps "Why?" on a Fit Check, the system shall show a graph of student → skill → (similar concept) → required skill → opening paths for every matched or near chip.
- AC-020.1 Given Aarav before uploading, then the path "Aarav → HAS_SKILL → deep learning → SIMILAR_TO → computer vision ← REQUIRES ← Edge AI for Agriculture" is drawn.

**REQ-021 (P1) Skill-gap panel.** The system shall list up to 5 missing skills ranked by how many open openings would move to ≥ 65 (`FIT_READY_MIN`) if that skill were certified.
- AC-021.1 Given seed data, then Aarav's top suggestion unlocks at least 1 opening and shows the count.

**REQ-026 (P1) Evaluation table.** The system shall provide a script that computes nDCG@10 and P@5 of the hybrid scorer and the keyword baseline on the labelled seed set.
- AC-026.1 Given `python -m scripts.eval_match`, then it prints both scorers' metrics as a Markdown table.

**REQ-035 (P2) Faculty track record.** When a student opens a faculty profile, the system shall show counts of openings posted, guide links accepted and completed, and median days to first decision on applications. These are facts, never ratings.
- AC-035.1 Given Dr. Meera's profile, then the four counts render and no rating or review field exists.

### 6.4 Mentor
**REQ-007 (P0) Allotment.** When the HOD assigns selected students to a mentor, the system shall end any previous active assigned link for those students and create new active links. The system shall also show each mentor's load and the list of unallotted students.
- AC-007.1 Given 2 unallotted students, when the HOD assigns them to Dr. Meera, then the unallotted count drops by 2 and her load rises by 2.
- AC-007.2 Given a mentor with 20 mentees, when one more is assigned, then the assignment succeeds and the mentor is marked "Overloaded (21/20)".
- AC-007.3 Given faculty or student role, when they call allotment, then the response is 403.

**REQ-028 (P2) Mentor handover.** When a student with an active assigned mentor is assigned to a different mentor, the system shall keep the old link as `ended` with reason `handover`. The new mentor sees the session dates, topics, action items and issues, but not the old mentor's notes.
- AC-028.1 Given the handover, when the new mentor opens Mentee 360, then earlier sessions show "Logged by Dr. X" and no notes field.

**REQ-008 (P0) Session log.** When a mentor submits a session with a date (not in the future, within the current or previous term), mode, kind (individual/group), 1–40 attendees from their mentees each marked present or absent, 1–6 topic categories, optional private notes (≤ 4000 chars), 0–10 action items and an optional next follow-up date, the system shall save it in one transaction.
- AC-008.1 Given 12 attendees, 2 action items and topics `academic, attendance`, when the session is saved, then a 201 response is returned and every present attendee's "meetings this term" increases by 1.
- AC-008.2 Given an attendee who is not the mentor's mentee or guided student, then the response is 422 `NOT_YOUR_MENTEE` and nothing is saved.
- AC-008.3 Given a date in the future, then the response is 422 with the field error "Session date cannot be in the future."

**REQ-009 (P0) Mentee confirmation.** When a present attendee taps "Confirm I attended", the system shall record the confirmation time. A session not confirmed within 7 days is shown as "Unconfirmed".
- AC-009.1 Given Aarav was present, when he confirms, then the session shows "Confirmed" on both his and his mentor's views.
- AC-009.2 Given a session 8 days old without confirmation, then the mentor's row shows `unconfirmed_sessions: 1`.
- AC-009.3 Given a student marked absent, when they try to confirm, then the response is 409 `NOT_PRESENT`.

**REQ-011 (P0) Issues.** When a mentor raises an issue (from a session or Mentee 360) with a category and text (≤ 1000 chars), the system shall create it as `raised`. The mentor shall resolve it with a resolution note (≤ 1000 chars).
- AC-011.1 Given an issue raised in a session, when it is resolved with a note, then its status is `resolved`, `resolved_at` is set, and the HOD's "issues resolved" count increases by 1.
- AC-011.2 Given resolution with an empty note, then the response is 422.

**REQ-022 (P1) Full issue lifecycle and escalation.** The system shall allow raised → acknowledged → in_progress → resolved. The mentor shall be able to escalate an issue at any unresolved state, which makes its text visible to the HOD and notifies them.
- AC-022.1 Given an escalated issue, then the HOD sees its text on the dashboard needs-attention list and can resolve it.

**REQ-036 (P1) Confidential flag.** Where a mentor marks a session or issue confidential, the system shall count it under the category "confidential" in every dashboard and export, and show its text to no one but the mentor (and the mentee, for an issue about them).
- AC-036.1 Given a confidential `personal` issue, then the HOD dashboard shows it under "confidential" and the category "personal" count excludes it.

**REQ-024 (P1) Mentee-initiated contact.** When a student raises an issue or requests a meeting with a short message (≤ 300 chars), the system shall notify their assigned mentor. A raised issue appears in the mentor's Mentee 360.
- AC-024.1 Given Aarav requests a meeting, then Dr. Meera receives a `meeting_request` notification with his message.

**REQ-033 (P2) Learner level.** The mentor shall be able to tag a mentee `slow`, `average` or `advanced` with an intervention note (≤ 500 chars), and the evidence pack shall count mentees per level.
- AC-033.1 Given 3 mentees tagged `slow`, then the mentoring pack's summary sheet shows "Slow learners identified: 3".

**REQ-034 (P2) Session feedback.** When a present attendee rates a session helpful or not helpful (optional comment ≤ 300 chars), the system shall store it, visible only to the mentor.
- AC-034.1 Given feedback is submitted twice, then the second submission replaces the first.

### 6.5 Track
**REQ-010 (P0) Action items.** The system shall store each action item with text (≤ 300 chars), owner (`mentee` or `mentor`), student and due date. The mentee shall mark their own items `done`; the mentor shall mark items `verified` or `dropped`. The system shall derive `overdue` when the due date is before today and the status is `open`.
- AC-010.1 Given an item due yesterday with status `open`, then it shows "Overdue" to the mentee and in the mentor's count.
- AC-010.2 Given the mentee marks it done, then the overdue flag clears and the mentor sees it under "To verify".
- AC-010.3 Given a mentee tries to set `verified`, then the response is 403.

**REQ-012 (P0) Mentor home.** When a mentor opens their home, the system shall list every active mentee (assigned and guided, labelled) with meetings this term against the required count, last session date, open and overdue action counts, open issues, unconfirmed sessions, and a needs-attention flag with its reasons. Flagged mentees are sorted first.
- AC-012.1 Given seed data, then Dr. Meera's list shows 13 assigned mentees and exactly 3 flagged, each with at least one reason label.

**REQ-013 (P0) Mentee 360.** When a mentor or the HOD opens a mentee, the system shall show on one page: skills with trust levels, the academic snapshot `[MOCK]`, a session timeline, action items, issues, applications, and status history.
- AC-013.1 Given Aarav, then every section renders from seed data, and notes appear only on sessions the viewing mentor logged.

**REQ-014 (P0) Student mentorship page.** When a student opens "My mentorship", the system shall show their assigned mentor and guides, the next follow-up date, sessions awaiting confirmation, their action items, their issues (excluding text of issues raised by the mentor as confidential), and their applications with status.
- AC-014.1 Given Aarav after the demo session, then he sees 1 session to confirm and 2 action items.

**REQ-015 (P0) Private notes.** The system shall return session notes only to the mentor who logged them, and never include them in any other response, dashboard or export.
- AC-015.1 Given Aarav requests a session he attended, then the response has no `notes` field.
- AC-015.2 Given the HOD requests the same session, then the response is 403 (HOD is not a role on API-027); given Dr. Arjun (faculty, not the author), it is 404.
- AC-015.3 Given both XLSX exports are generated, then a search for any seeded note text finds no match.

**REQ-018 (P0) Status history.** When any certificate, application, allotment, action item or issue changes status, the system shall record from, to, actor and time. Timelines shall show this history.
- AC-018.1 Given an application moved pending → shortlisted → accepted, then its history shows 3 entries (including creation) with actor names.

**REQ-023 (P1) Reminders.** The system shall show in-app reminders, computed when the reminders list is opened, for: a mentee's meeting count below the required number in the last 30 days of term, overdue action items, issues open more than 14 days, and sessions unconfirmed after 7 days.
- AC-023.1 Given an overdue action item, then the mentor and the mentee both see a reminder linking to it.

**REQ-029 (P2) At-risk suggestions.** Where the academic snapshot shows attendance below 75% or a CGPA drop of 1.0 or more from the previous term, the system shall add the reason `suggested_at_risk`. A mentor may also mark a mentee `marked_at_risk`.
- AC-029.1 Given a seeded mentee with 68% attendance, then their row shows "Suggested at risk: attendance 68%".

**REQ-032 (P2) Semester summary.** Mentee 360 shall show a computed term summary: sessions attended, action items done/total, issues raised/resolved, certificates certified. No LLM is used.
- AC-032.1 Given Aarav, then the summary numbers equal counts from the timeline.

**REQ-038 (P0) In-app notifications.** The system shall create a notification for: application status change, certificate certified/rejected, new session to confirm, new action item, issue escalated (P1), meeting request (P1). Users shall list them and mark them read.
- AC-038.1 Given a new session logged for Aarav, then his bell shows 1 unread, and marking it read sets the count to 0.

### 6.6 Evidence
**REQ-016 (P0) Department dashboard.** When a HOD or IQAC user opens the coordinator dashboard, the system shall show for the current term: students allotted/total, unallotted count, mentor:student ratio, per-mentor load, meetings held, compliance %, issues raised and resolved by category, overdue action count, and pending certificate reviews. The HOD also sees the needs-attention list with names; IQAC sees counts only.
- AC-016.1 Given seed data, then compliance shows 3 of 4 mentors at 100% of mentees with ≥ 2 meetings and one mentor below, highlighted.
- AC-016.2 Given the IQAC role, then the response contains no student names.

**REQ-017 (P0) Evidence export.** When a HOD or IQAC user clicks an export, the system shall generate an XLSX workbook: (a) mentoring pack, with DRAFT notice, mentor list, allotment list, summary ratios and mentor-wise meetings and issues by category; (b) achievements list, with certified certificates by type and level and a draft criterion code. Neither export contains notes, issue text or action item text.
- AC-017.1 Given the mentoring export, then it has sheets `README`, `Mentors`, `Allotment`, `Summary`, `Mentor-wise`, and `README!A1` reads "DRAFT – verify against the official NAAC manual before submission".
- AC-017.2 Given a student name beginning with `=`, then the cell is written prefixed with `'` (no formula executes).

**REQ-019 (P1) Click-to-source.** When a coordinator clicks a dashboard number, the system shall list the records behind it (for example, the 11 resolved issues as date, mentor, category and status), and the counts shall equal the number shown. IQAC sees no student names.
- AC-019.1 Given "Issues resolved: 11", then the drill-down returns exactly 11 rows.

## 7. Non-functional requirements

| ID | Requirement | Measured by |
|---|---|---|
| NFR-01 | p95 latency of API-012, API-015, API-024 and API-033 is < 2000 ms on seed data on the demo laptop (Docker, 8 GB RAM), 5 sequential runs each. | TEST-40 |
| NFR-02 | Certificate processing (API-005 accepted → terminal status) is ≤ 20 s p95 with a live LLM call and ≤ 2 s on a cache hit. | TEST-41 |
| NFR-03 | A first-time user logs a 12-attendee group session with 2 action items in ≤ 120 s. | TEST-50 (stopwatch) |
| NFR-04 | With `LLM_PROVIDER=none` and no network, the full primary flow (§8) completes using cached extractions. | TEST-52 |
| NFR-05 | P0 screens score ≥ 90 in the Lighthouse accessibility audit; the primary flow is completable by keyboard only. | TEST-51 |
| NFR-06 | Supported clients: latest Chrome and Edge on desktop (≥ 1280 px) and Chrome on Android at 360 px width, with no horizontal scroll. | TEST-51 |
| NFR-07 | Uploads are limited to 10 MB and to JPG, PNG and PDF (≤ 5 pages; only page 1 is extracted). | TEST-12 |
| NFR-08 | On a laptop with images already pulled, `docker compose up` plus seeding completes in ≤ 5 minutes. | TEST-53 |
| NFR-09 | Total LLM spend for the hackathon is ≤ USD 5; one extraction costs ≤ USD 0.05 [VERIFY: anthropic.com/pricing]. | Provider usage log |
| NFR-10 | All data is synthetic. `python -m scripts.seed --reset` deletes every node and reseeds in ≤ 60 s. | TEST-53 |

## 8. Primary flow (end to end)

1. Aarav logs in (REQ-031) and opens "Edge AI for Agriculture": Fit Check is 38–50 ("Close"), with PyTorch claimed-only (REQ-004).
2. He uploads the 4 files in `seed/demo_uploads` (REQ-001). One is caught as a `duplicate`; one with a name mismatch goes to `needs_review` (REQ-002). Two become `certified`, so pytorch, deep learning and computer vision become trust 1 (REQ-003).
3. His fit rises to ≥ 65, "Ready to apply". He applies (REQ-006).
4. Dr. Meera opens her opening: Aarav is ranked among its applicants with Certified chips (REQ-005). She shortlists, then accepts him, and a guide link appears (REQ-006).
5. Dr. Meera approves the `needs_review` certificate from her review queue (REQ-002).
6. On her mentor home, 3 mentees are flagged (REQ-012). She logs a group session for 12 mentees with 2 action items and resolves one issue (REQ-008, REQ-010, REQ-011).
7. Aarav confirms attendance and marks one action item done (REQ-009, REQ-010, REQ-014).
8. Dr. Meera opens a flagged mentee's Mentee 360 (REQ-013).
9. The HOD dashboard shows updated compliance and issues resolved (REQ-016).
10. IQAC exports the mentoring pack and the achievements list. Neither contains note text (REQ-017, REQ-015).

## 9. Success metrics

| Metric | Target for the demo | How measured |
|---|---|---|
| Certificate field accuracy (holder name, title, issuer, date) | ≥ 90% of fields correct | EVAL-01 on 25 labelled synthetic certificates |
| Planted duplicate and mismatch routing | 100% (deterministic) | EVAL-02 |
| Match quality | Hybrid nDCG@10 > keyword baseline | EVAL-03 (REQ-026) |
| Time to log a 12-mentee session | ≤ 120 s (vs. paper, timed once) | TEST-50 |
| Evidence compilation time | One click, < 10 s, vs. a manual baseline timed once | Stopwatch |
| Seeded compliance shown correctly | Dashboard numbers equal hand-computed values | TEST-32 |

Targeted judging criteria are mapped in the team plan (docs/plan, §18). Every figure presented must come from this table.

## 10. Constraints

- Time box: 15 hours, team of 4 (A-01). The stack is fixed by the existing GuruSetu code: FastAPI, Neo4j, Next.js 14 (A-02). Details are in [architecture.md](../02-architecture/architecture.md).
- Genesis rules on pre-existing code must permit reuse, with a disclosure statement [VERIFY: Genesis rules document].
- LLM use must be permitted by the rules [VERIFY: Genesis rules]. If it is not, run with `LLM_PROVIDER=none` and the manual and cached path (REQ-037).
- Synthetic data only (NG-03).

## 11. Risks

| ID | Risk | Likelihood | Impact | Mitigation / fallback |
|---|---|---|---|---|
| RISK-01 | Genesis rules forbid reusing exhibited code | M | H | Check at hour 0; disclosure statement; list new work explicitly |
| RISK-02 | 15 h is too short for repair plus build | H | H | Delete dead code instead of fixing it (NG-10); P0 only until the core freeze; cut order in the team plan |
| RISK-03 | LLM extraction fails or is slow on stage | M | H | Cache keyed by SHA-256 for every demo file (NFR-04); manual entry (REQ-037) |
| RISK-04 | A judge finds a security hole | M | H | SEC- items in security doc are P0; tests TEST-01..11 |
| RISK-05 | Session notes or confidential text leak via an endpoint or export | L | H | Server-side field filtering (REQ-015, REQ-036); TEST-20, TEST-21 |
| RISK-06 | Wrong accreditation criterion codes | M | M | DRAFT labels; codes tagged [VERIFY]; faculty review |
| RISK-07 | "This is just an ERP mentoring module" | M | M | Lead the pitch with verified-skill matching plus tracking that produces evidence as a by-product |
| RISK-08 | Embedding model download fails offline at the venue | M | M | Model baked into the backend image at build time (environments doc) |
| RISK-09 | Integration breaks late | M | H | `openapi.yaml` is the contract from hour 1; seed data mirrors API examples |

## 12. Alternatives considered

From PRD v2 and the enterprise vision, rejected for this build:
- **The enterprise demo spine** (Open Badges, auditor portal, copilot, NIRF): over budget for 15 h. It goes on the roadmap slide.
- **Separate HOD and IQAC apps:** replaced by one Coordinator area (A-03).
- **A full certificate pipeline replaced by 3 pre-checked samples:** kept only as the 2-person fallback in the team plan.

## 13. Mocked or simulated parts

| Part | Marker | Real replacement contract |
|---|---|---|
| Academic snapshot (CGPA, attendance, backlogs per term) | `[MOCK]` seeded `AcademicRecord` nodes | An AUMS import job writing the same `AcademicRecord` shape (ENT-08) |
| User accounts | `[MOCK]` seeded users with password `Demo@123` | SSO (Microsoft Entra) mapping to `User.email`; `role` from a directory group |
| Certificates | `[MOCK]` synthetic images generated by the team | Real uploads through the same API-005 |
| Extraction cache | `[MOCK]` pre-computed JSON for seeded files | Live MDL-01 call (same schema) |
| Accreditation criterion codes | `[MOCK]` draft mapping | Codes checked against the official NAAC manual |

## 14. Traceability note (PRD v2 → this document)

FR-1..FR-21 and FR-23..FR-27 of PRD v2 map to REQ-001..REQ-021 and REQ-023..REQ-027 with the same numbers. FR-22 became REQ-022 + REQ-036. FR-28 became REQ-028 + REQ-032 + REQ-033 + REQ-034. FR-29 is REQ-029. REQ-030, 031, 035, 037 and 038 are new. PRD v2 §7's certificate states are refined in [backend.md §6.1](../04-backend/backend.md).

## Verify

Open this file next to [00-index.md](../00-index.md). For each P0 REQ, confirm that the index traceability table lists at least one API-, SCR- or JOB- item and one TEST- item. Then walk through §8 against the running app and tick each step's REQ.
