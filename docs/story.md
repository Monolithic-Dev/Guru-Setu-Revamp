# GuruSetu: The Complete Story (Review 1: Research and Problem Understanding)

**How to use this file:** it is written to be *spoken*. **Part A** is the problem and the people (the heart of Review 1). **Part B** is the whole product: GuruSetu first as one idea (students and mentors finding and keeping each other), then every feature, each with **"The problem it solves"**. **Part C** is the pitch toolkit (demo story, numbers, answers to tough questions). Anything marked **[YOUR EVIDENCE]** must come from your own conversations, not from us.

---

# PART A: THE PROBLEM

## A1. What GuruSetu is (say this first)

> **GuruSetu is the bridge between students and teachers.**
> *Guru* means teacher and *Setu* means bridge. It is one platform where **students find the right mentor or research guide, mentors find the right students, and the relationship between them is recorded, followed up and proven**, instead of living in paper registers, WhatsApp messages and memory.

It works in **both directions**:
- **Student to teacher:** a student sees open research projects posted by faculty, sees **how well they fit and why**, and applies with **proof of their skills**.
- **Teacher to student:** a faculty member sees who applied, **ranked by verified fit**, picks the right students, and is automatically connected to them as their project guide.
- **Department to everyone:** the Head of Department assigns every student a **mentor**, and the whole mentor-mentee relationship from then on (meetings, promises, problems) is tracked.

**Three pillars hold it together:**
1. **Connect** (find each other): explained matching between students and faculty, plus mentor allotment.
2. **ProofOnce** (trust what you see): a student proves a skill once with a verified certificate, and everyone can rely on it.
3. **Mentor Desk** (keep the relationship alive): digital mentor-mentee tracking with follow-ups, dashboards and draft accreditation evidence.

---

## A2. The one-minute pitch (memorise this)

> "In a college department, **the most important relationship, between a student and a teacher, runs on paper and guesswork.**
> A student cannot tell which professor to approach or why they would be picked. A professor choosing research students reads CVs full of claims nobody has checked. Once a mentor is assigned, the meetings are signatures in a register that nobody reads again, so the quiet student drifts away unnoticed. And when accreditation arrives, the department rebuilds the evidence from memory.
> **GuruSetu fixes the whole chain.** Students prove their skills once. The system shows both sides who fits and why. Every mentor meeting is recorded with follow-ups, and the mentor's home screen says *who you are about to forget*. The HOD sees live compliance, and the accreditation coordinator downloads a draft evidence pack in one click, with private notes never leaving the mentor's hands."

**Tagline options:** "Find each other. Prove it. Follow through." / "Proof, not paperwork."

---

## A3. Who has the problem

| Person | Role | What they are trying to do | What goes wrong today |
|---|---|---|---|
| **Aarav Menon** | 2nd-year CSE student | Join a research project and get real guidance | Does not know which professor to approach or whether he is good enough. His certificates sit in a phone gallery, his profile says "PyTorch" but nobody believes it, and he never learns *why* he was or was not picked. His assigned mentor is a name on a list. |
| **Dr. Meera Raman** | Faculty member: mentor of 13 students and research guide | Find capable research students and support every mentee | Selecting students means reading unverified CVs and guessing. Her mentoring meetings sit in a signed register, so a month later she cannot recall who she has not met or what she promised. |
| **Dr. Suresh Iyer** | Head of Department (HOD) | Make sure every student has a mentor and every mentor really meets them | Has to chase each teacher to learn the truth. Does not know who is unallotted or overloaded. |
| **Kavya** | IQAC / accreditation coordinator | Produce mentoring and achievement evidence for NAAC-style accreditation | Collects registers, photos and spreadsheets by hand for weeks. The numbers do not tie up. |

*(These are the synthetic personas used in our demo. No real student data is used anywhere.)*

### A3b. Why four roles? (the use of each one, and why they are separate)

A department really has these four kinds of people with **different jobs and different rights**. GuruSetu mirrors that, and the separation is also what protects privacy: **each person sees only what their job needs.**

| Role | Their real job in a college | What they use GuruSetu for | What they must NOT see | What breaks without them |
|---|---|---|---|---|
| **Student** | Learns, applies for projects, receives mentoring | Upload certificates, see fit, apply, confirm meetings, tick off action items, raise an issue or ask for a meeting | Other students' data, any mentor's private notes | Nobody to prove skills or confirm meetings, so records stay one-sided |
| **Faculty (mentor and guide)** | Mentors a group of students and guides research projects | Post openings, rank applicants, log meetings, track action items and issues, review certificates of their own mentees | Students who are not theirs, other mentors' notes | The relationship is never recorded and nobody verifies certificates |
| **HOD (Head of Department)** | Runs the department day to day and is **accountable for it** | **Assign mentors**, watch compliance and workload, see who needs attention (with names), handle **issues that mentors escalate**, review any certificate | Mentors' private notes, confidential issues | No one can fix coverage gaps, move students between mentors, or resolve escalated problems |
| **IQAC coordinator** | The college's quality cell: prepares **accreditation (NAAC) evidence**; does not run the department | See the **same live numbers without student names**, download the **draft evidence pack** | Student names on the dashboard, any private text | Evidence is still collected by hand, and the person who needs it would have to be given private student data |

**Why HOD and IQAC are two roles, not one**
- **They do different work.** The HOD *acts* on the department (assigns mentors, resolves escalations). The IQAC *reports* on it (evidence for inspectors). The HOD needs names to act; the IQAC only needs numbers to report.
- **Least privilege.** The IQAC cell often covers the whole college and exports files that go to outside inspectors. So it gets **aggregates and pseudonyms only** ("Student 01"), and the draft exports contain **no names of private matters at all**. If one person did both jobs, either the HOD could not delegate reporting safely, or the IQAC would see private student information it does not need.
- **Accountability.** Every action is tied to a role and recorded: who allotted, who escalated, who approved a certificate.

**"Faculty already see students through openings, so why does the HOD assign mentors?"** Because they are two different relationships. An **opening** creates a **guide** link for one research project, and only for students who choose to apply. **Allotment** gives **every** student an assigned **mentor** for overall guidance, so students who never apply are not left without support. Accreditation expects every student to have a mentor and a healthy mentor-to-student ratio, and only the HOD can balance load across teachers (the dashboard shows who is unallotted and who is above 20 mentees).

**"How does a mentor review certificates?"** Only doubtful ones reach a human. A certificate scoring 85% or more is certified automatically. Anything with a name mismatch, unknown issuer, odd date or possible duplicate becomes "needs review", and the student's **assigned mentor** is notified. They open a queue of their own mentees' certificates, view the original file with the reason, and **approve** (the skill becomes verified) or **reject with a written reason** (3 to 300 characters, shown to the student). A decision is final and recorded with who and when. A guide may read but not decide; the HOD can review any certificate in the department. A student with no assigned mentor appears only in the HOD's queue, which is one more reason every student gets a mentor.

**Why faculty is one role covering both "mentor" and "guide":** it is the same person with two relationships to a student (assigned mentor and project guide). The relationship type, not the role, decides what they can see for each student.

**If a college is small:** one person can hold the HOD login and another login for IQAC duties. The roles are about *permissions*, not about headcount.

---

## A4. The problems, in plain words

### Problem 1: Students and teachers cannot find each other well (the "Guru-Setu" problem)
- **Students** do not know which research opening suits them, what is missing in their profile, or how to improve. Applying is a leap of faith, and rejection comes with no reason.
- **Teachers** pick research students from CVs and conversations. The "best" CV is often the most inflated one, and a genuinely capable student with no polished CV is invisible.
- **Mentor assignment** is a spreadsheet exercise. Nobody can see who is overloaded or who has no mentor at all, and changes are not tracked.

**Who it hurts:** capable but unnoticed students, faculty who pick blindly, and a department that cannot see its own mentoring coverage.

### Problem 2: Skills are claims, not proof
- Anyone can type "Machine Learning" on a profile.
- Certificates exist, but checking each one (Is it real? Is it really this student's? Has someone already used it? Is the issuer real?) is slow, so **nobody checks**.
- Matching without proof is just matching on claims.

**Who it hurts:** honest students (they cannot stand out), professors (they pick blindly), the department (CVs cannot be trusted).

### Problem 3: Mentoring is invisible after the introduction
- Every student is supposed to have a mentor. In practice the proof is a **signed paper register**.
- There is **no reminder**, no record of **what was agreed**, no follow-up on action items, no way to see **who has been missed**.
- A problem raised in a meeting ("I am struggling with attendance") can simply be **forgotten**. A student who quietly drifts away is noticed too late.
- Students cannot see their own mentoring record or confirm what was discussed.

**Who it hurts:** struggling students (no support), mentors (no memory aid, no credit for effort), the HOD (no visibility).

### Problem 4: Evidence is rebuilt, not recorded
- Accreditation bodies ask for proof: mentor-student ratio, how many meetings happened, how many issues were resolved, student achievements.
- Because daily records are on paper, the department **reconstructs** the proof at the last minute. It is slow, error-prone and sometimes inflated.
- Private matters (a student's personal problem) risk leaking into those reports, because nobody has clear rules about what is shareable.

**Who it hurts:** the IQAC coordinator (weeks of work), the HOD (credibility), students (privacy risk).

> **The root cause behind all four: the department's most important information (who fits whom, who has proven what, who has met whom, what was promised) is not recorded in a structured, trusted way at the moment it happens.**

---

## A5. Why it matters (say this to justify the problem)

- **For students:** a lost opportunity (the right research project and guide) and lost support (the struggling student nobody noticed).
- **For faculty:** time wasted on paperwork and guesswork instead of mentoring and research.
- **For the department:** accreditation is not optional. Mentoring and achievement evidence is a formal requirement, and weak records cost credibility and weeks of effort.
- **For trust:** when skills and meetings cannot be verified, every decision built on them (selection, support, ranking) is weaker.

---

## A6. [YOUR EVIDENCE] What we found out

Reviewers will ask: *"How do you know this is a real problem?"* The argument above is solid, but **the findings must be yours**. Do not quote numbers you did not collect. Even 5 short conversations are enough.

**Questions to ask**
- *Students:* "How did you find your last project guide? Do you know why you were or were not picked? Where do you keep your certificates? Has anyone checked them? Do you ever see what your mentor wrote about you? Do you even know who your mentor is?"
- *Mentors:* "How do you choose research students? How do you record a meeting? How do you remember what you promised? How would you know a mentee was struggling?"
- *IQAC / office:* "How long does it take to collect mentoring proof for an inspection? What goes wrong? What do you wish you could just download?"

**Record the answers**

| Who | What they told us (their words) |
|---|---|
| Student 1 | |
| Student 2 | |
| Student 3 | |
| Mentor 1 | |
| Mentor 2 | |
| Office / IQAC | |

**How to say it:** "We spoke to **N** people. **X of N** said ______. The most common frustration was ______."

**If you have few conversations, say honestly:** "This is early research from a small sample. The problem also appears in accreditation requirements, and our system is designed to be validated with a pilot department."

---

## A7. What we studied before building (our research approach)

- We looked at the **campus workflow end to end** (who asks for what, who has to prove what) instead of building one feature in isolation.
- We compared several ideas and combined three that share one backbone: **certificate verification, explained matching between students and faculty, and digital mentor-mentee tracking**. They are really one story: *proof in, decisions out, relationship recorded*.
- We chose a **graph database** because the problem is about relationships (student, mentor, guide, skill, opening, certificate) and a graph stores those directly.
- We deliberately kept the scope tight: depth and trust over a long feature list (see B9).

---

# PART B: THE SOLUTION

## B0. GuruSetu as one story (read this aloud before the feature details)

Meet **Aarav**. He is a student who wants to do research in AI for agriculture, but he has no idea whom to approach.

1. **He opens GuruSetu** and sees open research projects posted by faculty. One is *"Edge AI for Agriculture"* by **Dr. Meera**. Next to it is a number: **fit 43, Close**, with a reason: *"Python is verified. PyTorch is only claimed. Deep Learning and Computer Vision are missing."* For the first time he knows exactly what stands between him and the project.
2. **He proves his skills.** He uploads two certificates. The system reads them, checks them with rules, and turns his claimed skills into **verified** ones. His fit rises to **Ready to apply**, and he applies.
3. **Dr. Meera sees him** in her list of applicants, **ranked by verified fit**, with proof chips next to each skill. She did not have to guess. She shortlists him and accepts him. **GuruSetu automatically makes her his project guide.**
4. **Meanwhile, the HOD has assigned Aarav a mentor** (also Dr. Meera, for personal and academic guidance). Now the **relationship is tracked**: after every meeting she records attendance, topics, her private notes, action items and any issue. Aarav confirms he attended and ticks off his tasks.
5. **Nobody falls through the cracks.** Dr. Meera's home screen shows all 13 mentees and flags the ones she is about to forget, with the reason. When she opens a student she sees **their whole story in one place**.
6. **The department sees the truth.** The HOD sees live compliance and workload. The accreditation coordinator downloads a **draft evidence pack in one click**, containing counts and records, **never anyone's private notes**.

> **The same data entered once, by the people doing the work, becomes: a fair match for the student, a better selection for the teacher, a record of care for the mentee, and evidence for the department.**

---

## B1. The map of GuruSetu

```
 ┌───────────────────────── CONNECT (find each other) ─────────────────────────┐
 │  Faculty post openings ──► Student sees explained FIT ──► Student applies   │
 │  Faculty see ranked, verified applicants ──► accept ──► becomes GUIDE       │
 │  HOD assigns every student a MENTOR (load-aware, tracked, notified)         │
 └───────────────▲───────────────────────────────────────────┬─────────────────┘
                 │ verified skills drive the fit               │ relationship begins
 ┌───────────────┴──────── PROOFONCE (trust) ─┐   ┌────────────▼──── MENTOR DESK (follow through) ─┐
 │ Upload certificate ► AI READS ► RULES decide│   │ Log meeting ► student confirms ► action items   │
 │ duplicates / mismatch ► human review        │   │ issues ► NEEDS-ATTENTION home ► MENTEE 360      │
 └─────────────────────────────────────────────┘   └────────────┬────────────────────────────────────┘
                                                                  ▼
                                   HOD / IQAC DASHBOARD (live) ──► DRAFT EVIDENCE EXPORT (one click)
```

**Two kinds of student-teacher relationship, both handled:**

| | **Guide** (research) | **Mentor** (assigned guidance) |
|---|---|---|
| How it starts | Student applies to an opening; faculty accepts | HOD assigns the student to a mentor |
| What it is for | A specific research project | Overall academic and personal guidance |
| Who chooses | Both sides, based on explained fit | The department, load-aware |
| Counts toward compliance | No (project work) | **Yes** (the minimum meetings per term) |
| Tracked with sessions, actions, issues | Yes | Yes |

---

## B2. CONNECT, part 1: students find the right opportunity (GuruSetu Match)

### The story
Aarav opens **"Edge AI for Agriculture"**, which needs Python, PyTorch, Deep Learning and Computer Vision. He sees **Fit 43, Close**, with a reason he can act on. He uploads two certificates, his fit rises to **65 or more, "Ready to apply"**, and he applies. He can then follow the application status (pending, shortlisted, accepted or rejected) with a full history.

### How the score is built (explain it like a recipe)
The score from 0 to 100 has **three parts that add up exactly**, so nothing is hidden:
- **Skill match (60%):** each required skill is compared with his skills. A **verified skill counts fully**, a **claimed-only skill counts a fraction**, a **similar skill** (for example Deep Learning for Machine Learning) counts partly, and **rarer skills weigh more** than common ones.
- **Meaning match (25%):** how close his overall profile (skills, interests, certificates, bio) is to the opening's description, using AI embeddings (a way of turning text into numbers so similar meanings sit close together).
- **Related-concept match (15%):** how close his skills are to the required ones through a map of related concepts.
- **Verdict:** **Ready** (65 and above), **Close** (40 to 64), **Not yet** (below 40), with one sentence telling him what to do next.

### The problem it solves
| Problem | How Match solves it |
|---|---|
| Students do not know which opening suits them or why | A score with **exact reasons and next steps** |
| Rejection comes with no explanation | Every score shows what is proven, what is only claimed, and what is missing |
| Scores feel like a black box | Three components that **sum exactly** to the total, explainable in one sentence |
| Fit that rewards CV inflation | Verified skills outweigh claimed ones |
| Applying is opaque | A visible application status with history and notifications |
| People being unfairly ranked | **No leaderboards and no ratings of people.** A score is only "fit to one opening" |

### Also designed (add-ons)
- **"Why this match" graph:** shows the path from student to skill to similar concept to required skill to opening.
- **Skill-gap panel:** the top 5 missing skills that would unlock the most openings.
- **Evaluation table:** compares our hybrid scorer against a plain keyword baseline on labelled data, so "better" is measured, not asserted.

---

## B3. CONNECT, part 2: faculty find the right students

### The story
**Dr. Meera creates an opening** (a title, a description and the skills required, up to 10). Students see it immediately with their own fit. Later she opens her opening and sees **only the students who actually applied, ranked by verified fit**, each with chips showing **Verified, Claimed or Missing** for every required skill. She **shortlists**, then **accepts or rejects**. If she accepts, **GuruSetu automatically makes her that student's project guide**. When the project ends, she marks it completed and the guide link ends with the reason "completed".

### Rules that keep it fair
- Only people who **applied** are listed. Nobody is ranked globally.
- A faculty member can see a student's fit **only if that student applied to her opening**.
- The decision follows a strict path: pending, then shortlisted, then accepted or rejected, then completed. No skipping, no undoing.
- The student is notified at each step, and every step is recorded with who did it and when.
- Faculty see only **facts** about a track record (openings posted, guides accepted and completed, how quickly decisions are made), **never ratings**.

### The problem it solves
| Problem | How it is solved |
|---|---|
| Professors pick students by guessing from CVs | Applicants ranked by **verified** fit with proof chips |
| Strong students with plain CVs are invisible | The score uses proven skills and meaning, not CV polish |
| Applicant lists are messy | One ranked list with the reason for each position |
| The research relationship is not recorded | Accepting creates a tracked guide link automatically |

---

## B4. CONNECT, part 3: mentor allotment (who mentors whom)

### The story
**Dr. Suresh opens the allotment screen.** On the left are **unallotted students**. On the right are **mentor cards: "13 / 20"** (load against a recommended maximum), with an **Overloaded** badge once a mentor goes beyond 20. He selects two unallotted students, picks a mentor and clicks **Assign**. Both students instantly receive: **"Your mentor is now Dr. Meera."**

### How it behaves
- Each student has **at most one active mentor** at a time.
- If a student already had a mentor, the old link is **ended with the reason "handover"** and kept for history; the new one starts today.
- A new mentor sees the **dates** of earlier sessions but **never the previous mentor's private notes**.
- Assigning a student to the mentor they already have changes nothing.
- The mentor must belong to the same department.

### The problem it solves
Nobody used to know who was unallotted or overloaded, and changes were untracked. Now it is one screen, with load, notifications and history.

---

## B5. PROOFONCE: certificate verification

### The story
Aarav opens "My certificates" and uploads a photo of his Python certificate. A few seconds later it shows **Certified**, and his profile gains *Python: Verified, source: Python Basics certificate*.

### What actually happens (explain this slowly, it is the "wow")
1. **Safe upload.** The system checks the file really is a JPEG, PNG or PDF (by its real contents, not its name), rejects anything over 10 MB, limits PDFs to 5 pages, stores it privately and **never serves it publicly**.
2. **AI reads it.** An AI model extracts the **holder name, title, issuer, issue date, level (college, national, and so on), type (course, hackathon, ...), certificate ID and up to 8 skills**. It also reports whether the document looks like a real certificate and whether it contains text trying to instruct the AI.
3. **Rules decide, not the AI.** Plain deterministic code runs the checks in order:
   - **Exact duplicate?** The same file already uploaded.
   - **Visual duplicate?** A re-photographed copy of an existing certificate (caught by an image fingerprint).
   - **Same certificate ID from the same issuer?** Also a duplicate.
   - **Is it even a certificate?** A receipt or blank page goes to review.
   - **Hidden AI instructions?** Flagged (defence against prompt injection).
   - **Confidence score** from four weighted checks: **name matches profile (40%)**, **issuer is known (25%)**, **date is sensible (20%)**, **all key fields present (15%)**.
   - **85% or above becomes Certified automatically.** Lower goes to a human, with the reason shown (name mismatch, unknown issuer, date invalid, incomplete).
4. **Humans handle the doubtful ones.** The student's mentor (or the HOD) sees a **review queue**, opens the original file and **approves or rejects with a written reason**, which is shown back to the student.
5. **If the AI fails** (unreadable file, timeout, outage), the status is **Failed** and the student can **type the details**. That entry is capped at a lower confidence and **always goes to the mentor for approval**, so manual entry can never become an easy back door.
6. **Verified skills update the profile and the fit score.** Every status change is recorded with who and when.

### Trust levels on skills
- **Claimed:** the student typed it.
- **Certified:** a verified certificate proves it (source shown).
- **Endorsed (add-on):** a mentor or guide who has worked with the student vouches for it; this counts the most.
- Levels are recomputed whenever evidence changes.

### The problem it solves
| Problem | How ProofOnce solves it |
|---|---|
| Skills are unchecked claims | A skill becomes **Verified** only through a certificate that passed checks, with the source shown |
| Checking certificates by hand is slow | AI reads the fields in seconds; humans see only the doubtful ones |
| The same certificate can be reused or copied | Exact, visual and certificate-ID duplicate detection |
| AI can be wrong or fooled | **The AI never decides.** Rules decide; doubtful cases go to a human |
| Typing details is tedious | The student types nothing on the normal path |
| AI outage on demo day | Cached results for known files plus a manual-entry fallback, so the flow never dead-ends |

### The one-liner
> **"The AI reads. The rules decide. The humans handle the exceptions."**

---

## B6. MENTOR DESK: keeping the mentor-mentee relationship alive

This is the day-to-day heart of the department.

### B6.1 Session logging (under two minutes)
**The story:** After a group meeting with 12 mentees, Dr. Meera logs it: **date, in person or online, individual or group, who attended (each marked present or absent), topics (academic, attendance, career, research, personal, other), her private notes, action items and any issue.** One tap and it is saved.

**Rules that protect quality**
- The date **cannot be in the future** and must be in the **current or previous term**.
- An **individual** session has exactly **one** attendee.
- Every attendee **must really be her mentee** (otherwise it is rejected, naming the student).
- Action items and issues can only be about people **who attended**.
- A follow-up date must be **after** the session date.
- **Double-tap safe:** if the network hiccups and she taps Save twice, the system stores it **once**.
- **All or nothing:** the session, attendance, action items, issues, history and notifications are saved **together or not at all**.

**Problem solved:** paper registers are slow, forgettable and un-auditable. This takes two minutes and creates a complete structured record.

### B6.2 Mentee confirmation
**The story:** Aarav gets *"Please confirm your session on 12 Oct."* He taps **Confirm I attended**. A session not confirmed within **7 days** shows as **Unconfirmed**.
**Problem solved:** a signature is easy to fake or forget. The student's own confirmation makes attendance **two-sided and believable**.

### B6.3 Action items (promises that do not vanish)
**The story:** Dr. Meera adds *"Submit the draft report by Friday"* for Aarav. Aarav sees it and marks it **Done**. She then marks it **Verified**, **Dropped**, or **reopens** it.
**Rules:** a student can move his own item **Open to Done** only. Only the mentor who set it can verify, drop or reopen. An open item past its due date shows as **Overdue**.
**Problem solved:** promises made in meetings used to vanish. Now each one has an owner, a deadline, a status and a history.

### B6.4 Issues (problems that get followed up)
**The story:** Aarav mentions he is struggling with attendance. Dr. Meera raises an **issue** and later **resolves** it with a written resolution.
**Full lifecycle:** raised, acknowledged, in progress, resolved. A mentor can **escalate** an issue to the HOD (the HOD is notified and can then read and resolve it) or mark it **confidential**: it is counted in reports but never described, and a confidential issue cannot be escalated.
**Students can raise issues too, and ask for a meeting:** Aarav can raise an issue about himself or send his mentor a short meeting request; the mentor is notified.
**Problem solved:** a student's problem used to depend on one person's memory. Now it is tracked until resolved, and nothing is lost if the mentor changes.

### B6.5 Needs-attention home: "who am I about to forget?"
**The story:** Dr. Meera's home screen lists all her mentees with **meetings this term against the required number**, last meeting date, open and overdue actions, open issues and unconfirmed sessions. Students who need attention are **at the top, with the reason**.

| Flag | Meaning in plain words |
|---|---|
| **No recent session** | Not met in the last **45 days** (and the mentorship began more than 45 days ago) |
| **No meeting this term** | Zero meetings, and more than half the term is over |
| **Overdue action** | An agreed action item is past its due date |
| **Stale issue** | An issue has been open longer than **14 days** |
| *(later)* **Marked at risk / suggested at risk** | The mentor flagged the student, or attendance is below 75 percent or CGPA dropped by 1.0 or more |

Mentees are ordered flagged first, then by number of reasons, then by name.
**Problem solved:** the quiet student who drifts away is no longer discovered too late. The system **does the remembering**.

### B6.6 Mentee 360: the whole story of one student
**The story:** Dr. Meera clicks a flagged student and sees **everything on one page**: profile, skills with trust levels, academic snapshot (sample data), every session in a timeline, action items, issues, applications, certificates, and the **history of every status change**.
**Privacy built in:** she sees **her own private notes**. Sessions written by **another mentor** (for example before a handover) show the date but **never the text**. The HOD sees the page **without any notes**.
**Problem solved:** a new mentor or the HOD used to start from zero. Now the full, privacy-safe story is one click away.

### B6.7 "My mentorship": the student's own view
**The story:** Aarav sees his **assigned mentor** (name, designation, email), his **project guides**, the **next follow-up date**, **sessions waiting for his confirmation**, **his action items**, **his issues** and **his applications with status**. In group sessions he sees only **his own** row.
**Problem solved:** mentoring used to happen *about* students without being visible *to* them. Now it is transparent and two-sided.

### B6.8 Notifications, reminders and history
- **In-app notifications** for: application received or changed, certificate result, certificate needs review, you were assigned a mentor, a session to confirm, a new action item, an issue escalated, a meeting request. They carry names, dates and statuses, **never private text**.
- **Reminders** (computed when opened, no hidden spam): meetings due near term end, overdue actions, stale issues, unconfirmed sessions.
- **Every status change leaves a trail:** who changed what, from what to what, and when.

**Problem solved:** nobody chases anybody, and every decision can be traced.

---

## B7. Department dashboard and draft evidence (HOD and IQAC)

### The dashboard
Dr. Suresh opens the **Coordinator dashboard**. For the **current term** he sees: students allotted versus total and the unallotted count, the **mentor-to-student ratio**, **compliance %** (the share of allotted students who met the minimum **2 meetings per term**, overall and per mentor), each mentor's load with an Overloaded badge, issues raised and resolved by category (confidential ones grouped without detail), overdue actions, certificates waiting for review, achievements by type, the **needs-attention count and names** (HOD only) and **escalated issues** (HOD only).
**Two views, one truth:** the **HOD** sees student names; **IQAC** sees the **same numbers but never a student's name**.
**Click-to-source (add-on):** click any number (for example "11 resolved issues") and see the exact records behind it, with the count matching. IQAC sees pseudonyms such as "Student 01".

### The one-click draft evidence pack
Kavya clicks **Export mentoring pack** and **Export achievements** and gets Excel files:
- **Mentoring pack:** README (clearly marked **"DRAFT, verify against the official NAAC manual before submission"**), Mentors, Allotment, Summary (compliance %, ratio, issues, overdue actions, confirmed-attendance share), Mentor-wise table.
- **Achievements list:** every certified achievement of the academic year with roll number, name, title, issuer, date, level, type, certificate ID, reviewer and draft criterion code, plus a by-type summary.
**Safety:** the export **never reads private text** (notes, issue text, action text, resolutions), formula-looking names are neutralised, and it is clearly a draft.

### The problem it solves
| Problem | How it is solved |
|---|---|
| The HOD has to chase each mentor | One live view of compliance per mentor |
| Overloaded mentors are invisible | Load shown against the recommended maximum |
| Numbers are rebuilt at the last minute | **Computed live from the records mentors already enter** |
| Reports risk leaking private matters | Counts only, **never note or issue text** |
| Dashboard and export could disagree | Both come from **one single calculation** |
| Weeks of manual collection | **One click** |

---

## B8. Trust, privacy and security (the "we thought about this" slide)

| Concern | What we built |
|---|---|
| Who can see what | Four roles (student, faculty, HOD, IQAC), each with strict rules |
| Leaking existence | A teacher asking for a student who is not theirs gets **"not found"**, so even the *existence* of the record is not revealed |
| Private notes | Returned **only to the author**; never in dashboards, exports, notifications or logs |
| Confidential issues | Counted but never described |
| Roles cannot be faked | The role is **re-read from the database on every request** |
| Login | Passwords hashed; the same message for a wrong email or password; login attempts rate-limited |
| Uploads | Real file-type check, size and page limits, private storage, never publicly served |
| AI | The AI never decides trust or status; hidden instructions in documents are flagged |
| Auditability | Every status change records who, from, to and when |
| Data honesty | **Synthetic data only**; sample sections are labelled; we claim no accuracy we have not measured |
| Secrets | The app refuses to start with weak secrets; none are stored in the code |

---

## B9. What we deliberately did NOT build (and why)

We chose **depth and trust over a long feature list**. We do **not** build: self sign-up, password recovery, a chatbot, SMS or email alerts, integration with government or university systems, faculty rating or leaderboards, a free browsable directory of all faculty, a native mobile app (the website works on a phone), parent-contact logs, or any claim to detect all forgery.
**Why this is a strength:** each is a real but separate project. Building them would have weakened the core: matching on proof, and a trustworthy mentor-mentee record.

---

## B10. How it is built (one slide)

| Layer | Technology | In plain words |
|---|---|---|
| Face | Next.js website (works on a phone) | What students, teachers and the HOD click |
| Brain | FastAPI (Python) backend | Applies the rules and checks who may see what |
| Memory | **Neo4j graph database** | Stores people, meetings, skills and certificates **as connections** |
| AI | Language model for reading certificates, embeddings for fit | Reads and explains; **never decides trust on its own** |
| Packaging | Docker Compose | The whole system starts with one command |

**Why a graph database?** Our problem *is* relationships: student to mentor, student to skill, skill to opening, certificate to skill, faculty to student. A graph stores those directly, so questions like "who mentors whom and who has proved what" are natural.
**Quality bar:** the backend has an automated test suite (about 130 tests pass today) covering access rules, privacy, mentoring flows, the dashboard and the exports.

---

## B11. Where the project stands today (be honest, reviewers respect it)

| Area | Status |
|---|---|
| Login, roles, access rules, notifications, status history | **Built and tested** |
| Applications, student profile, guide link on acceptance | **Built and tested** |
| Mentor allotment | **Built and tested** |
| Sessions, confirmation, private notes, action items, issues (full lifecycle, escalation, confidential) | **Built and tested** |
| Needs-attention home, Mentee 360, student mentorship page | **Built and tested** |
| Dashboard, click-to-source, draft Excel exports | **Built and tested** |
| Reminders, meeting requests, create opening | **Built and tested** |
| Certificate upload, review and manual entry (backend) | **Built and tested against a stand-in for the AI part** |
| AI reading, verification rules, fit scoring and ranked candidates | In progress |
| Website screens, demo data, rehearsals | In progress |

*Adjust this table so it is accurate on the day you present.*

---

# PART C: THE PITCH TOOLKIT

## C1. The end-to-end demo story (about 5 minutes)

1. **Aarav logs in** and opens "Edge AI for Agriculture". Fit is **Close**; PyTorch is *claimed only*.
2. He **uploads four certificates**. One is caught as a **duplicate**, one with a **name mismatch** goes to review, two become **Certified**, so PyTorch, Deep Learning and Computer Vision turn from claimed to verified.
3. His fit rises to **Ready to apply** and he **applies**.
4. **Dr. Meera** sees Aarav **ranked** among the applicants with **Certified chips**. She **shortlists** then **accepts** him; a **guide link** appears.
5. She **approves the pending certificate** from her review queue.
6. On her **mentor home**, **three mentees are flagged**. She **logs a group session** for 12 mentees with two action items and **resolves an issue**.
7. **Aarav confirms** attendance and marks an action item **done**.
8. She opens a flagged mentee's **Mentee 360**.
9. The **HOD dashboard** now shows updated compliance and issues resolved. He **assigns two unallotted students** and they are notified.
10. **IQAC exports** the mentoring pack and achievements list. **Neither contains any note text.**

*Closing line for the demo:* "Everything you just saw was recorded once, by the people doing the work. It became a fair match for the student, a better choice for the teacher, a record of care for the mentee and evidence for the department."

---

## C2. Feature to problem map (one slide)

| Feature | The problem it solves | Who benefits |
|---|---|---|
| Explained fit score | Students do not know why they fit or not | Student |
| Ranked applicants with proof chips | Faculty pick students by guessing | Faculty |
| Create opening | No structured way to find students | Faculty |
| Application status and history | Opaque applying | Student |
| Accept creates a guide link | Research relationship not recorded | Student, faculty |
| Allotment screen with load | Unknown unallotted or overloaded mentors | HOD |
| Certificate upload and AI reading | Typing certificate details by hand | Student |
| Rule-based verification and duplicate detection | Unchecked, copied or fake-looking certificates | Everyone |
| Human review queue and manual fallback | AI mistakes and outages | Faculty, student |
| Verified skill trust levels | Claims with no proof | Student, faculty |
| Session log | Slow, forgettable paper registers | Mentor |
| Student confirmation | Easily faked signatures | Mentor, department |
| Private notes | Fear that personal matters will leak | Mentor, student |
| Action items | Promises that vanish | Mentor, student |
| Issues, escalation, confidential flag | Problems forgotten or mishandled | Student, HOD |
| Student-raised issues and meeting requests | Students are passive | Student |
| Needs-attention home | Forgetting the quiet student | Mentor, student |
| Mentee 360 | Starting from zero with each student | Mentor, HOD |
| My mentorship page | Mentoring invisible to the student | Student |
| Notifications, reminders, status history | Chasing people, untraceable decisions | Everyone |
| Live dashboard and click-to-source | Chasing mentors for numbers | HOD, IQAC |
| One-click draft evidence export | Weeks of last-minute collection | IQAC, HOD |
| Privacy rules everywhere | Leakage of private matters | Student, mentor |

---

## C3. Numbers and facts you can quote (all from the project's own settings)

- **Confidence formula:** name 40%, issuer 25%, date 20%, completeness 15%. **85% or above** becomes Certified automatically.
- **Fit score:** skill 60%, meaning 25%, related concepts 15%. **65 and above Ready, 40 to 64 Close, below 40 Not yet.**
- **Upload limits:** 10 MB, JPEG, PNG or PDF only, PDF up to 5 pages, 20 uploads per hour per student.
- **Mentoring rules:** at least **2 meetings per term**, flag after **45 days** without a session, issues stale after **14 days**, sessions unconfirmed after **7 days**, mentor overloaded above **20** mentees.
- **Logging time:** a session with attendance, action items and issues in **under two minutes**.
- **Test suite:** about **130 automated backend tests** pass today.

*(Do not quote AI accuracy percentages. We have not measured them yet, and we say so honestly.)*

---

## C4. Tough questions and strong answers

| Question | Answer |
|---|---|
| "So is GuruSetu a job portal or a mentoring app?" | Both halves of one relationship: **finding** the right student or guide (explained matching) and **keeping** the mentor-mentee relationship alive (tracking), with proof underneath. |
| "How do students find mentors?" | Research guides are found through **openings** with an explained fit; assigned mentors come from the **HOD's allotment**, which is load-aware, notified and tracked. We deliberately do not build a free directory or ratings of faculty. |
| "How do mentors find students?" | They post an opening and see **ranked, verified applicants** with proof chips, then shortlist and accept. Accepting makes them the guide automatically. |
| "Isn't this just a CRUD app?" | The value is **verification** (AI reads, rules decide, humans review), **explained fit**, and **live compliance computed from the same records**, all guarded by strict privacy rules. The hard part is trust, not forms. |
| "Can the AI be fooled by a fake certificate?" | It can read a fake. That is why **the AI never decides**: duplicate, name and issuer checks are rules, and anything doubtful goes to a human. We do **not** claim to detect all forgery. |
| "What if the AI is down?" | Known files come from a cache, and the student can type the details. That entry is capped at lower confidence and **always reviewed by a mentor**. |
| "Why would teachers use it?" | Logging a meeting takes under two minutes, and the home screen tells them **who to meet next**. It reduces their effort. |
| "What about student privacy?" | Notes are **author-only**. IQAC sees **no names**. Exports and dashboards hold **no private text**. A teacher cannot even learn that another teacher's student exists. The demo uses **synthetic data only**. |
| "Is the fit score fair?" | It is **fit to one opening**, not a ranking of people. It is explainable: three parts that sum exactly. Verified skills count more than claimed ones. |
| "Why a graph database?" | The problem is relationships. A graph stores student, mentor, skill, certificate and opening, and their connections, directly. |
| "Is the NAAC export official?" | No. It is clearly marked **DRAFT**, and tells the user to verify against the official manual. |
| "Will it scale beyond one department?" | The data model already carries a department code, so extending is a data and interface task, not a redesign. We scoped the build to one department on purpose. |
| "How do you know it is a real problem?" | Our conversations (A6), plus the fact that accreditation formally requires this evidence. |
| "What next?" | Pilot with one real department, then add endorsements, richer reminders, learner-level tagging and a student skill-gap view. |

---

## C5. Glossary

- **Mentor (assigned):** a teacher assigned by the HOD to guide a group of students.
- **Guide:** the faculty member guiding a student's research project; created when an application is accepted.
- **Opening:** a research position a faculty member posts.
- **Fit check:** an explained score of how well a student matches an opening.
- **Trust level:** how well a skill is proven (claimed, certified, endorsed).
- **Needs attention:** a flag with a reason on a mentee who may be falling through the cracks.
- **Mentee 360:** one page with the complete picture of one student.
- **HOD:** Head of Department. **IQAC:** the internal quality assurance cell that prepares accreditation evidence. **NAAC:** the national accreditation body for Indian colleges.
- **Embedding:** a way of turning text into numbers so similar meanings are close together.
- **Graph database:** a database that stores data as connected nodes (people, skills) rather than rows.

---

## C6. The closing line

> **"Today a department runs on registers and trust-me.
> GuruSetu runs on proof: it helps students and teachers find each other, proves what students can do, and keeps the mentor-mentee relationship visible, all from the same records, entered once."**
