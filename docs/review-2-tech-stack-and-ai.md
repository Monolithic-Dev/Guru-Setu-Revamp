# GuruSetu: Review 2 (Tech Stack and AI Usage)

**How to use this file:** it is written to be spoken to judges and mentors. **Part A** is the 90-second version. **Part B** is the tech stack, layer by layer, with *why* each choice was made. **Part C** is exactly how AI is used (and where it is deliberately not used). **Part D** is evidence: what we measured, what we tested, and what we have *not* measured. **Part E** is the live demo, **Part F** is the Q&A toolkit. Every number below comes from this repository (config, code or measured results). Where something is a limit or still open, it says so, because honest limits are what mentors trust.

---

# PART A: THE 90-SECOND VERSION

> **"GuruSetu is a graph-backed trust layer for a university department. It has three jobs: prove what a student can do, match students and faculty with an explanation, and keep the mentor-mentee relationship visible and auditable.**
>
> **Our stack is deliberately boring where trust matters and smart where it helps.** The backend is FastAPI on a Neo4j graph database, the frontend is Next.js, and the whole thing starts with one `docker compose up`. **AI is used in exactly two places:** a vision language model **reads** certificates into structured fields, and a small local embedding model gives the matcher a sense of **meaning**. **Everything that decides something** (is this certificate trusted, what status, how much, who sees what) **is plain, deterministic, tested code.** The AI proposes; the rules decide; a human handles the exceptions."

**The three sentences to remember:**
1. **AI reads and measures similarity. It never decides trust, status, or access.**
2. **Every number the user sees can be explained in one sentence and reproduced on any machine.**
3. **Private data never goes near a model:** only the certificate image is sent out; mentoring notes and issues never are.

---

# PART B: THE TECH STACK

## B1. The picture

```
                    Browser (phone or laptop)
                              │  HTTPS-ready, JWT Bearer
                              ▼
        ┌──────────────────────────────────────────────┐
        │  FRONTEND  Next.js 14 (App Router) + TypeScript│
        │  Tailwind · axios (one client) · types generated│
        │  from the API contract                          │
        └───────────────────────┬──────────────────────┘
                                │  REST /api/v1  (OpenAPI is the contract)
                                ▼
        ┌──────────────────────────────────────────────┐
        │  BACKEND  FastAPI (Python 3.12) + Pydantic v2 │
        │  api  →  services (rules)  →  repos (Cypher)   │
        │  ml/ : extraction · verification · scorer       │
        └───────┬───────────────┬──────────────┬───────┘
                │               │              │
                ▼               ▼              ▼
          Neo4j 5.26      Local embedding    Groq API (LLM)
          graph store     model MiniLM       vision → JSON
          (the only DB)   (384-d, offline)   (only the certificate image)
```

**Everything runs in Docker Compose:** `neo4j`, `backend`, `frontend`, with health checks, a private network, and ports bound to `127.0.0.1` only.

## B2. Layer by layer

| Layer | Technology (pinned version) | Why this and not something else |
|---|---|---|
| **Web framework** | **FastAPI 0.143**, Uvicorn, **Pydantic 2.14** | Typed request/response models for *every* route, which is how we guarantee a password hash or file path can never leak. Automatic validation errors in one consistent shape. |
| **Database** | **Neo4j 5.26 Community** (official driver 5.28) | The product *is* relationships: student–mentor, student–skill, skill–opening, certificate–skill, skill–similar skill. One query language, plus built-in vector indexes, so no second database. (ADR-02) |
| **Auth** | **bcrypt** (cost 12) used directly, **PyJWT** (HS256) | Passwords hashed, never stored. Role is **re-read from the database on every request**, so a stale token cannot keep old powers. |
| **Frontend** | **Next.js 14.2** (App Router), **React 18**, **TypeScript**, **Tailwind CSS** | Server-rendered shell, role-based layouts, works at 360 px on a phone. One HTTP client (`axios`), one data hook. |
| **Charts / graph** | recharts, react-force-graph-2d | The "Why this match" graph and dashboard visuals. |
| **AI: reading** | **Groq** SDK 1.7, model **`qwen/qwen3.8-27b`** | Accepts an image *and* honours strict `json_schema` output, which is exactly what field extraction needs. Free tier, 2–3 s per certificate. |
| **AI: meaning** | **sentence-transformers 6.1**, **`all-MiniLM-L6-v2`** (384-d), CPU PyTorch | Runs **locally and offline**, baked into the Docker image. No data leaves the machine for similarity. |
| **Image / PDF checks** | **Pillow**, **ImageHash** (pHash), **pypdfium2** | Re-encodes uploads (drops hidden payloads), computes a perceptual fingerprint, renders page 1 of a PDF. |
| **Fuzzy matching** | **rapidfuzz** | Name and issuer comparison that survives "Mr. AARAV  Menon." vs "Aarav Menon". |
| **Exports** | **openpyxl** | Editable XLSX so the IQAC coordinator can fix a draft; formula-injection safe. |
| **Contracts** | **OpenAPI 3.1** (`openapi.yaml`) → `datamodel-codegen` (Python models) and `openapi-typescript` (frontend types) | **Contract-first:** the API spec is the single source of truth; backend models and frontend types are *generated*, so they cannot drift. Linted with Spectral. |
| **Quality** | **pytest** (248 tests), **ruff**, ESLint, `tsc --noEmit`, Spectral | Run in CI-style gates before every merge. |
| **Packaging** | **Docker Compose** | One command to run the whole product, offline-capable for demos. |

## B3. Architecture rules that make it trustworthy

| Rule | What it prevents |
|---|---|
| **Layering:** `api → services → repos`; Cypher exists *only* in `repos/` and is always parameterised | Query injection, business logic scattered through routes |
| **Every route has an explicit response model** | Accidental leaks of `password_hash`, `embedding`, `file_path` |
| **403 vs 404:** wrong role → 403; right role but not your student → **404** | Leaking that a record *exists* |
| **One write transaction per change:** the change, its audit event and its notifications commit or roll back **together** | Half-saved meetings, notifications without a cause |
| **Thresholds are configuration**, never literals in code (45 days, 14 days, 0.85, 65 …) | "Magic numbers", untuned demos |
| **Errors are `application/problem+json` with stable codes** | Frontends guessing at error text |
| **Private text never leaves its owner:** notes, issue text and resolutions are never in dashboards, exports, notifications or logs | The product's biggest risk: leaking a mentee's private matter |

## B4. The data model (why a graph)

```
(Student)-[:HAS_SKILL {trust 0/1/2}]->(Concept)<-[:REQUIRES]-(Opening)<-[:POSTED]-(Faculty)
(Evidence)-[:PROVES]->(Concept)         (Concept)-[:SIMILAR_TO {score}]-(Concept)
(Faculty)-[:MENTORS {type: assigned|guide}]->(Student)
(Faculty)-[:LOGGED]->(Session)-[:ATTENDED_BY]->(Student)
(Session)-[:CREATED]->(ActionItem)-[:FOR]->(Student)     (Issue)-[:ABOUT]->(Student)
(StatusEvent)  audit trail for evidence, applications, mentorship, actions, issues
```
**The payoff:** "why does this student fit this opening?" is a *path* in the graph (`student → skill → similar concept → required skill → opening`), and the product draws exactly that path in the "Why" view.

## B5. Contract-first workflow (a strength to call out)

`docs/04-backend/openapi.yaml` → **generated** `backend/app/schemas/generated.py` and **generated** `frontend/src/lib/types.ts`. A change to the API is: edit the contract, regenerate both sides, and the compiler tells you everything that broke. This is how four people built backend, frontend and ML in parallel without integration surprises.

---

# PART C: HOW AI IS USED

## C1. The principle

> **AI is a tool inside a pipeline, never the decision maker.** Four components use or surround models. No model ever makes a trust decision, sees mentoring data, or writes free text that a user reads.

| ID | Component | What it is | Used for | What stays deterministic |
|---|---|---|---|---|
| **MDL-01** | Certificate extractor | **Vision LLM** (Groq, `qwen/qwen3.8-27b`), strict structured output | Reading a certificate (image or PDF) into fields | **All** checks, status, confidence and trust |
| **MDL-02** | Text embedder | `all-MiniLM-L6-v2`, **local**, 384-d | The "meaning" part of the fit score | Everything else in the score |
| **MDL-03** | Hybrid fit scorer | **Not a model**: a documented formula | Explained fit score, ranking, skill gaps | The entire formula |
| **MDL-04** | Concept similarity | MiniLM over concept names + a hand-set override file | `SIMILAR_TO` edges ("PyTorch is near Deep Learning") | Threshold, top-k, overrides win |

## C2. Pipeline 1: ProofOnce (certificate verification)

```
 upload ─► magic-byte / size / page checks ─► re-encode with Pillow ─► SHA-256 + pHash
                                                   │
                         cache hit? ──yes──────────┤
                              │ no                 ▼
                              └──► MDL-01 (Groq vision, JSON schema) ──► Extraction
                                                   │
        ┌──────────────────────────────────────────┘
        ▼                  DETERMINISTIC RULES, IN THIS ORDER
  1 exact duplicate (SHA-256)        → duplicate
  2 visual duplicate (pHash ≤ 6)     → duplicate
  3 same issuer + certificate ID     → duplicate
  4 not a certificate                → needs_review
  5 hidden instructions in document  → needs_review
  6 tamper signals (optional)        → needs_review
  7 confidence = 0.40·name + 0.25·issuer + 0.20·date + 0.15·complete
        ≥ 0.85 → certified      else → needs_review (one reason per failed check)
        │
        ▼
  certified → PROVES edge → skill trust recomputed → profile embedding recomputed
  needs_review → assigned mentor reviews (approve / reject with a reason)
  failed → student can type the fields (capped at 0.50 confidence, always reviewed)
```

**What each AI call returns** (strict schema, nothing else is accepted): `is_certificate`, `holder_name`, `title`, `issuer`, `issue_date`, `level`, `type`, `skills[≤8]`, `certificate_id`, `verify_url`, `contains_instructions`. **There is no field for status, trust or confidence**, so a model (or text hidden in a document) *cannot* set them. This is asserted in tests.

**Engineering details worth mentioning**
- Images are EXIF-rotated, downscaled to 1568 px and **re-encoded as PNG** before sending (also strips anything odd inside the file).
- `temperature: 0`, one retry, 25-second timeout; a refusal, a timeout or a schema-invalid answer (twice) all end in the same safe state: **`failed` → manual entry**, never a crash.
- **Cache keyed by the file's SHA-256:** a known file skips the network entirely. This makes the demo work **offline** and removes demo-day API risk. A daily call cap (`MAX_LLM_CALLS_PER_DAY=200`) is a hard stop.
- **Math done in `Decimal`, not float**, so the displayed components add up *exactly* to the displayed score on every machine (we hit a real float bug: `100×0.15×0.07` is `1.0499999999999998`).

## C3. Pipeline 2: Explained Fit (GuruSetu Match)

**Per required skill of an opening, the scorer asks, in order:**
1. Does the student **have** it? A **verified** skill counts 0.85, **endorsed** 1.00, **claimed-only** 0.40.
2. Else, does the student have a **similar** skill (`SIMILAR_TO ≥ 0.60`)? Counts as a fraction ("near", with the skill it came *via*).
3. Else it is **missing**.

Rarer skills weigh more (`idf = ln(1 + N / (1 + df))`, N = open openings, df = openings requiring that skill).

```
score = round(25 · semantic)  +  round(60 · skill_part)  +  round(15 · concept_part)
        └ meaning (MiniLM)       └ proven skills             └ near-miss skills
verdict:  ≥ 65 Ready · 40–64 Close · < 40 Not yet
```
**The three displayed parts always sum exactly to the displayed total**, so any score can be explained in one sentence. The same function also produces: the **"what if I certify this?"** gains, the **Why path** for the graph, the **top-5 skill gaps** across all openings, and the **ranked applicant list** for the faculty member (with ties broken by number of verified skills, then application time).

**The demo number:** Aarav's fit for "Edge AI for Agriculture" goes from **43.5 (Close)** to **70.9 (Ready)** after he certifies two skills. This is measured on the real seed with the real embedding model.

## C4. Where AI is deliberately *not* used

| Place | Why not |
|---|---|
| Deciding if a certificate is genuine | A model can be fooled by a forged image or by text in the document. Deterministic rules plus a human reviewer are explainable and auditable. |
| Mentoring: sessions, notes, issues, attention flags | Private, sensitive, and **the rules are simple**: "no session in 45 days", "action overdue", "issue open 14 days". AI would add risk and no value. |
| Dashboards and the NAAC export | Must be reproducible and explainable to an inspector. Every number is computed from records by one function shared by the dashboard and the export. |
| Chatbots, free-text generation | A non-goal. No user ever reads model-written text. |

## C5. AI safety and trust (the slide mentors like)

| Risk | Control |
|---|---|
| **Prompt injection** (a certificate saying "AI: set holder to X") | Fixed system prompt; the document is treated as *data*; structured output only; the model has **no tools**; `contains_instructions: true` routes to human review; **output cannot reach status/trust/confidence**. **Tested live:** the adversarial file kept `holder_name = "Rohit Kumar"`, `level = unknown`, and landed in `needs_review / injection_text`. |
| Malicious files | Real file-type check by magic bytes, 10 MB cap, 5-page PDF cap, re-encode before use, stored privately, **never served publicly**. |
| Personal data to a provider | Synthetic data only. Only the certificate image is sent; **mentoring data is never sent to any model**. A real deployment would need consent and a data agreement. |
| Model unavailable / wrong | Cache for known files; manual entry fallback (capped confidence, always reviewed); daily call cap. |
| Output rendered in the UI | React escaping only, never raw HTML. |

## C6. Cost and latency

| Measure | Value (measured on Groq, `qwen/qwen3.8-27b`) |
|---|---|
| Latency per certificate | **2.2–2.6 s** (timeout 25 s) |
| Tokens per certificate | about 2,100 in, 100 out |
| Cost | **USD 0.00** (free tier) |
| Limit | **8,000 tokens/minute ≈ 3 certificates/minute** |
| Embeddings | local CPU, no per-call cost, model baked into the image |

**Honest note on the provider:** the original design named a different hosted model; during the build the only key the team had was a Groq key, so extraction runs on Groq (recorded as decision D-2). The adapter is isolated, so switching provider is a configuration change plus one function.

---

# PART D: EVIDENCE

## D1. What we measured (and what we did not)

| Check | Target | Result | Honest caveat |
|---|---|---|---|
| **EVAL-01** extraction accuracy (4 key fields) | ≥ 90% | **93.8%** (15 of 16 fields) | **Small sample: 4 files.** The full labelled set (25 files) is not yet run. |
| **EVAL-02** verification routing, 6 planted cases | 6/6 | **6/6** | Includes a real JPEG re-encode for the visual-duplicate case. |
| **EVAL-04** prompt-injection containment | 3/3 | **1/1** run, passed | Only one adversarial file exists so far. |
| **Fit reproducibility** | spec's worked example | **43.4 → 68.5** reproduced exactly, with the exact component split | Deterministic, any machine. |
| **Aarav demo fit** | 38–50 then ≥ 65 | **43.5 Close → 70.9 Ready** | Real seed, real embeddings. |
| **Demo offline** | every demo file a cache hit | **6/6 hits** | Network can be off during the demo. |
| **EVAL-03** hybrid vs keyword baseline | hybrid > baseline | **Tie (1.000 vs 1.000)** | **Not a valid test:** the label set is too easy for both scorers. We report it as a tie rather than tune against the labels. |

> **Say this proudly:** *"We only put measured numbers on slides. Where our evaluation set is too small or too easy, we say so instead of claiming a win."*

## D2. Testing

| Suite | What it proves |
|---|---|
| **248 automated tests pass** inside the Docker container against a real Neo4j | The full backend, including the ML code, on the actual stack |
| Security tests | No registration / password-reset routes; role and scope checks; 401/403/404 order; problem+json shape; injection text stored literally |
| Privacy tests | Notes only to the author; confidential issues counted but never described; IQAC responses contain **no student names**; exports contain no private text |
| Mentoring tests | Idempotent session logging, **fault-injection rollback** (all-or-nothing), attendance rules, action-item and issue state machines, handover rules |
| Dashboard / export tests | Numbers hand-computed in the test, not read back from the code; formula-injection neutralised in XLSX; dashboard totals equal the click-to-source row counts |
| ML tests | Every verification rule; name-variant matching; scorer reproduces the worked example; extraction cache hit, miss and cap |
| Static gates | `ruff` clean, `tsc` clean, ESLint clean, Spectral (API contract) clean |

**Seed verification (real data, measured against the spec):** Meera has 13 mentees and **exactly 3 are flagged** (Karthik: not met in 45+ days and an overdue action; Diya: a stale issue; Rahul: an overdue action); the dashboard shows 50 students, 48 allotted, 1:12 ratio, 8 overdue actions, **91.7% compliance**, with only one mentor below 100%.

## D3. What the AI part is *not* (limits, said upfront)

- Extraction accuracy is measured on **very few** files; we do not claim a general accuracy figure.
- We do **not** detect forgery beyond duplicates, name/issuer/date checks, an optional metadata/ELA tamper signal, and a human reviewer.
- A blank page produces an unusual image fingerprint, so two blank uploads can be reported as duplicates (we found and documented it).
- The free Groq tier limits throughput to about 3 certificates per minute. Fine for a demo and a department, not for thousands of students.
- The `level` field (college / national / …) is the model's weakest field and the likeliest to be corrected by a reviewer.

---

# PART E: LIVE DEMO (about 6 minutes, tech-flavoured)

1. **`docker compose up`**: neo4j, backend and frontend come up with health checks. Show `/api/v1/health` returning the Neo4j status and the active LLM provider.
2. **Seed**: `python -m scripts.seed --reset` builds 56 users, 12 openings, concepts, embeddings and similarity edges (it prints counts).
3. **Aarav's fit** for "Edge AI for Agriculture": **43.5 Close**, with the three components. Open **Why**: the graph path student → skill → similar concept → required skill.
4. **Upload certificates:** one becomes **Certified** (AI read → rules decided), one is caught as a **duplicate** (pHash), one with a **name mismatch** goes to **needs_review**. Show the **review queue** on the mentor side and the **reason**.
5. **Fit rises to 70.9 Ready**; he applies; the faculty sees applicants **ranked by verified fit**.
6. **Prompt-injection file:** shows `injection_text`, nothing adopted.
7. **Mentor home:** exactly **3 flagged mentees** with reasons (all deterministic rules, no AI).
8. **Dashboard and export:** live compliance, click a number to see the **exact rows**, download the **DRAFT** Excel, open it: no private text, formulas neutralised.
9. **Switch the network off** (or `LLM_PROVIDER=none`): the cached demo files still work; an unknown file falls to **manual entry**.

---

# PART F: Q&A TOOLKIT

| Question | Answer |
|---|---|
| **Where exactly is AI used?** | Two places: a vision LLM reads certificate images into fixed fields, and a small local embedding model adds a "meaning" signal to the fit score. Everything else is rules. |
| **Why not let the LLM verify authenticity?** | It can be fooled and cannot explain itself. We use duplicate detection, name/issuer/date rules, and a human reviewer for doubt. The LLM output has no field that can set status, trust or confidence. |
| **What if the model hallucinates a field?** | Schema-validated; the rules compare it to the student profile and known issuers; a mismatch routes to a human. A wrong `level` is the main residual risk and is reviewer-correctable. |
| **What about prompt injection?** | Fixed prompt, no tools, structured output only, `contains_instructions` flag routes to review, and we tested a live adversarial file. Injected values were not adopted. |
| **Why Groq and that model?** | The team's available key was Groq, and `qwen/qwen3.8-27b` was the one model on it that accepts images *and* honours strict JSON schema. The provider is behind one adapter, so changing it is configuration. |
| **What if the API is down or rate-limited?** | SHA-256 cache for known files, a manual-entry fallback (confidence capped at 0.50, always reviewed), and a daily call cap. |
| **Why a local embedding model?** | Privacy, cost and offline use: no data leaves the machine for similarity, and the model is baked into the image. |
| **Why a hybrid score, not just embeddings?** | Embeddings alone cannot tell *claimed* from *proven*. The formula weights proven skills (60%) above meaning (25%) and near-miss concepts (15%), and stays explainable. |
| **Is the score explainable?** | Yes: three parts that sum exactly. The product also shows what to certify to improve it, and draws the path in a graph. |
| **Why Neo4j?** | The domain is relationships; the "Why" explanation is literally a graph path; vector indexes live in the same store; one datastore. |
| **How do you keep four people's work consistent?** | Contract-first: one OpenAPI spec generates backend models and frontend types; ownership map plus a checker so nobody edits another person's files; PR-only merges. |
| **How do you protect privacy?** | Typed response models, 403/404 scoping, author-only notes, no private text in dashboards/exports/notifications/logs, IQAC sees no names, synthetic data only. |
| **How accurate is extraction?** | 93.8% on 4 key fields over 4 files: a small sample, reported as such. The full 25-file labelled run is the next measurement. |
| **Does the hybrid beat a keyword baseline?** | Our evaluation set was too easy: both scored 1.000, so it is a tie, not a win. We do not tune against the labels. |
| **Can it scale?** | One uvicorn worker today by design (rate limiter and background jobs are in-process). Scaling out means a shared queue and rate-limit store; the layering already isolates those. |
| **What would you improve with more time?** | Evaluate on the full labelled set; add a second provider for fallback; endorsement flows; a human-in-the-loop correction loop that feeds the labels. |

---

# PART G: SLIDE OUTLINE (8 slides)

1. **The idea and the one rule:** "AI reads; rules decide; humans handle exceptions."
2. **Architecture:** the diagram in B1, with the Docker one-liner.
3. **Tech stack and why:** B2 table, trimmed to six rows (FastAPI, Neo4j, Next.js, Groq, MiniLM, contract-first).
4. **Where AI is used:** C1 table; C4 "where it is not".
5. **ProofOnce pipeline:** the C2 flow, highlighting that the model has no field for trust.
6. **Explained fit:** the formula and Aarav's 43.5 → 70.9.
7. **Safety and measured results:** C5 and D1 (including the honest tie and small sample).
8. **Quality and demo:** 248 tests, contract-first, then the live demo.
