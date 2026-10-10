You are **P1 (ML and Fit Check)** on a 4-person, 15-hour hackathon build of **GuruSetu**. Paste this whole brief into your coding agent, or read it as your own brief. It is self-contained: it tells you what to build, in what order, with what interfaces, what "done" means for every task, and exactly how to use git. Where it points to a document, that document has the full detail; where it states a number or a rule, the number or rule is binding.

# 1. The product and your part in it

GuruSetu (stack: FastAPI + Neo4j 5 + Next.js 14, Docker Compose, built **from scratch**, **synthetic data only**) is a trust layer for a university department:
- A student uploads a certificate. An LLM **extracts the fields**. **Deterministic code** decides whether it is trustworthy. Verified skills become trust-weighted skills.
- The student sees an **explained Fit Check** for each research opening ("Close, certify these skills to improve your fit") and can apply.
- Faculty mentors log mentoring sessions, action items and issues; HOD and IQAC see live compliance and export draft accreditation evidence. (Those parts belong to P2, P3 and P4; you feed them verified skills and fit scores.)

**You own the intelligence:** embeddings, concept similarity, the certificate extractor, the verification rules, trust, the fit scorer, the match endpoints, the Fit Check screen, and the evaluation numbers. If your part is wrong, the demo's central moment fails: Aarav's fit going from **38-50 ("Close")** to **at least 65 ("Ready")** after he uploads four certificates (index section 7, steps 1-3).

The repo is `Guru-Setu-Revamp`. The default branch is `main`. Nothing is built before the scaffold commit by P2.

# 2. Non-negotiable rules (from the spec)

1. **The LLM extracts certificate fields only.** Trust, status and confidence are deterministic Python (ai-system section 3). **Never give the model tools.** The model can never set status, trust or confidence.
2. **Treat uploaded documents as data, never as instructions.** A file that contains text aimed at an AI sets `contains_instructions` and goes to review (rule 5).
3. **The fit score is computed in Python with no LLM.** The components are rounded first, then summed, so `semantic + skill + concept == score` exactly.
4. **Thresholds and weights are configuration** (backend section 8: `CERT_AUTO_CERTIFY_MIN`, `NAME_MATCH_MIN`, `PHASH_MAX_DISTANCE`, `FIT_READY_MIN` 65, `FIT_CLOSE_MIN` 40, `SIM_MIN` 0.60, `TAMPER_CHECK_ENABLED`, `ELA_THRESHOLD`, `LLM_*`). Never hard-code a literal that has a setting. The trust weights `{0: 0.40, 1: 0.85, 2: 1.00}` and fit weights `{semantic 0.25, skill 0.60, concept 0.15}` are named constants (A-10).
5. **No Cypher inside `ml/`.** All database queries used by `ml/` live in `repos/ml_repo.py` and `repos/match_repo.py` (both yours). `ml/` functions take a `tx` and call those repo functions. Cypher is always parameterised, never built from strings.
6. **Never log** file bytes, base64, extracted holder names, API keys, tokens or passwords (SEC-15). Each LLM call logs only `{request_id, evidence_id, model, prompt_version, cache_hit, input_tokens, output_tokens, latency_ms, outcome}`.
7. **Never commit** `.env`, an API key, uploads or real data. Mark seeded or simulated things `[MOCK]` in code comments and show "Sample data" in the UI.
8. Build **P0 before P1 before P2** items. Do **not** build anything listed as a non-goal (NG-01..15 in the PRD).
9. The spec pack wins over a phase doc where they disagree on a fact. Contract files (`docs/04-backend/openapi.yaml`, `schema.cypher`) are changed only by P2.

# 3. Read first (30 minutes, in this order)

1. `AGENTS.md`, then `CONTRIBUTING.md` (git rules are binding)
2. `docs/00-index.md` (section 5 assumptions, **section 7 end-to-end scenario**)
3. `docs/06-ai/ai-system.md` (**your governing doc**: extraction, verification, fit formula, embeddings, safety, eval plan)
4. `docs/01-product/prd.md`: REQ-001..005, 020, 021, 025, 026 and their acceptance criteria; NG items
5. `docs/04-backend/backend.md`: section 2 (data model), 4.1 (worked examples), 6.2 (trust recompute), 8 (config); `docs/04-backend/schema.cypher`; `openapi.yaml` for API-012/013/015/016/020/021/041
6. `docs/phases/README.md`, `parallel-work.md` (seams and stubs), and phase docs 0 to 4 and 6 (your tasks)

# 4. Your files (single owner: you)

`backend/app/ml/**` (`__init__.py`, `embedding.py`, `concepts.py`, `seed_hooks.py`, `extraction.py`, `verification.py`, `trust.py`, `scorer.py`, `prompts/extract_certificate_v1.md`, `schemas/certificate_extraction.schema.json`) · `backend/app/api/v1/match.py` · `backend/app/api/v1/endorsements.py` · `backend/app/repos/match_repo.py` · `backend/app/repos/ml_repo.py` · `backend/app/schemas/match.py` · `backend/requirements.txt` · `backend/Dockerfile` · `backend/.dockerignore` · `backend/extraction_cache/` · `backend/scripts/eval_match.py`, `eval_extraction.py`, `build_extraction_cache.py` · `backend/seed/aliases.json`, `similar_overrides.json`, `fit_tuning.json` · tests: `backend/tests/test_verification.py`, `test_scorer.py`, `test_matching.py`, `test_embedding.py`, `test_extraction.py` · `frontend/src/app/student/openings/**` · `frontend/src/components/fit/**` · `frontend/src/fixtures/p1/` · `docs/06-ai/` · `docs/plan/eval-results.md`.

Check any path: `python tools/check_ownership.py --who <path>`. **Do not edit files you do not own.** Ask the owner: P2 (backend, contracts, `conftest.py`, other tests), P3 (frontend shell, layouts, `features.ts`, `components/ui`), P4 (seed JSON, `seed.py`, README).

# 5. Schedule (hours from the real start time, written in `docs/phases/status.md`)

| Phase | Hours | Your tasks | Est |
|---|---|---|---|
| 0 Setup | 0:00-1:00 | T0.P1.1 dependencies, Dockerfile, model bake, ML startup stub | 1:00 |
| 1 Foundation | 1:00-4:00 | T1.P1.1 embeddings · T1.P1.2 concepts + SIMILAR_TO · T1.P1.3 extraction contract · T1.P1.4 seed hooks + IDF | 3:00 |
| 2 Core A | 4:00-7:00 | T2.P1.1 LLM call · T2.P1.2 verification · T2.P1.3 extraction cache · T2.P1.4 trust recompute | 3:00 |
| 3 Core B | 7:00-10:00 | T3.P1.1 scorer · T3.P1.2 fit APIs · T3.P1.3 seed tuning · T3.P1.4 Fit UI + SCR-03 | 3:00 |
| 4 Add-on A | 10:00-12:30 | A2 Why API (0:30) → A5 skill-gap (0:50) → A6 eval table (0:45) → A8 tamper (0:30) | 2:30 |
| 6 Freeze | 12:30-15:00 | T6.P1.1 offline run (TEST-52) · T6.P1.2 eval numbers · bug-bash help | 2:30 |

**Gates:** G0 at 1:00, G1 at 4:00, G2 at 7:00, **G3 core freeze at 10:00**, feature freeze 12:30, code freeze 13:15. Stand-ups (5 min): 1:00, 4:00, 7:00 (30-min integration check), 10:00, 12:30: "done, next, blocked, anything to cut".

# 6. Task details

## Phase 0
**T0.P1.1 Dependencies, Dockerfile, model bake, ML stub (1:00)**
- Pin **every** backend dependency now so nobody edits `requirements.txt` later: `fastapi`, `uvicorn`, `neo4j`, `pydantic-settings`, `python-multipart`, `bcrypt`, `PyJWT` (no `passlib`), `sentence-transformers`, `anthropic` (latest at hour 0), `Pillow`, `imagehash`, `pypdfium2`, `rapidfuzz`, `openpyxl`, `PyYAML` (if used) and dev tools `pytest`, `httpx`, `ruff`, `datamodel-code-generator`, `pip-audit`. Do not add `cloudinary`, `openai` or `passlib`. Check versions on PyPI [VERIFY].
- `Dockerfile`: `python:3.12-slim`; install the **CPU** torch wheel first (`pip install torch --index-url https://download.pytorch.org/whl/cpu` [VERIFY URL]); install requirements; bake the model into `/models` with `ENV HF_HOME=/models` (`python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', cache_folder='/models')"`); copy `app/`, `scripts/`, `seed/`, `extraction_cache/`, `schema/`; `CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000","--workers","1"]`. No curl is needed (P2's healthcheck uses python).
- `backend/.dockerignore`: tests, caches, `.env`, `uploads/`, `.venv`.
- `app/ml/__init__.py`: `def startup() -> None: pass` (you fill it in T1.P1.1). P2's `main.py` calls it.
- Verify inside the container: `python -c "from sentence_transformers import SentenceTransformer as S; print(S('sentence-transformers/all-MiniLM-L6-v2').get_sentence_embedding_dimension())"` prints **384** with the **network off**.
- Confirm your Anthropic key and the model ID `claude-opus-5-5` with one tiny call; tell P2 the result (it goes in `docs/plan/decisions-log.md`). **Do not commit the key.** No key? Use `LLM_PROVIDER=none` and hand-write cache JSON later.
- **Done when:** 384 prints offline, `app.ml.startup` imports, key check recorded.

## Phase 1 (by 4:00)
**T1.P1.1 Embeddings (0:45)**: `ml/embedding.py` loads the model once at startup from `EMBEDDING_MODEL` with `HF_HOME` set (if loading fails the API refuses to start with a log line naming `HF_HOME`). `embed(texts) -> list[list[float]]` (normalised). `student_text(profile)`: `"{dept} student. Skills: {names}. Interests: {interests}. Certificates: {certified titles}. {bio}"`. `opening_text(opening)`: `"{title}. {description}. Requires: {concept names}."`. `recompute_student_embedding(tx, student_id)` and `recompute_opening_embedding(tx, opening_id)` read, build, embed, write (Cypher in `ml_repo.py`). **Done when** a test shows `len(embed(["x"])[0]) == 384` and cosine(student_text(Aarav), opening_text(op-edge-ai)) > 0.3.

**T1.P1.2 Concepts and SIMILAR_TO (0:45)**: `normalise(name)` = lower-case, trim, collapse spaces, map through `seed/aliases.json` (for example `dl → deep learning`, `torch → pytorch`). `get_or_create_concept(tx, name, source)` embeds a new concept and computes its top-5 neighbours with cosine ≥ `SIM_MIN` as `SIMILAR_TO {score, source:'model'}`. `rebuild_similarity(tx)` (for the seed): all pairs, top 5 per concept, then apply `seed/similar_overrides.json` (`source:'override'`, **overrides win**). Store each pair once, alphabetically smaller name first. **Done when** after the seed `MATCH (:Concept {name:'deep learning'})-[r:SIMILAR_TO]-(:Concept {name:'computer vision'}) RETURN r.score` returns **0.7**.

**T1.P1.3 Extraction contract and adapter skeleton (1:00)**: write `ml/schemas/certificate_extraction.schema.json` and `ml/prompts/extract_certificate_v1.md` **verbatim** from ai-system sections 2.2 and 2.3. Add a Pydantic `Extraction` model with the post-validation rules (`issue_date` parses as ISO or becomes null; skills trimmed, lower-cased, de-duplicated, max 8, each at most 40 characters; strings truncated to 200). `extract(file_bytes, media_type) -> Extraction | ExtractionFailed(reason)` in this order: (1) SHA-256 cache lookup in `EXTRACTION_CACHE_DIR` (hit returns `source="cache"`); (2) if `LLM_PROVIDER=none`, return failed; (3) check the daily `Counter{name:'llm_calls', date}` cap `MAX_LLM_CALLS_PER_DAY`; (4) otherwise call the provider (stub raising `NotImplementedError` in this task). Expose `set_adapter_for_tests(fn)` for TEST-14 and TEST-16. **Done when** a unit test with a hand-written cache file returns `source="cache"`, a miss with `none` returns failed, and the cap returns failed.

**T1.P1.4 Seed hooks (0:30)**: `ml/seed_hooks.py::seed_embeddings(tx)` (all Students and Openings) and `ml/concepts.py::rebuild_similarity(tx)`. P4 calls them from `seed.py`; **you never edit `seed.py`**. Commit `seed/fit_tuning.json` as `{}` (your text overrides, applied by `seed.py` before embeddings: `{"students": {id: {bio, interests}}, "openings": {id: {description}}}`). Write `repos/match_repo.py::idf_table(tx)` returning `{concept: idf}` over open openings. **Done when** the G1 embedding and SIMILAR_TO checks pass.

## Phase 2 (by 7:00)
**Interface agreed with P2 at 4:00 (stubs with FINAL signatures pushed by 4:15):**
```python
# ml/verification.py
def verify(student: StudentCtx, file_bytes: bytes, media_type: str,
           extraction: Extraction | ExtractionFailed, tx) -> VerificationResult
# VerificationResult(status, confidence, reasons: list[str], duplicate_of: str | None,
#                    sha256: str, phash: str | None, skills: list[str])
# ml/trust.py
def apply_certified(tx, student_id: str, evidence_id: str, skills: list[str]) -> None   # PROVES + recompute
def recompute_skill(tx, student_id: str, concept: str) -> None
```
**T2.P1.1 LLM call (1:00)**: images: open with Pillow, apply EXIF orientation, convert RGB, downscale the longest side to 1568 px, re-encode PNG, base64 into an `image` block; PDFs: base64 `document` block. Request: `client.beta.messages.create(model=LLM_MODEL, max_tokens=2048, betas=["server-side-fallback-2026-07-01"], fallbacks="default", output_config={"format":{"type":"json_schema","schema":SCHEMA},"effort":"low"}, messages=[...])` with client `timeout=LLM_TIMEOUT_S`, `max_retries=1`. **Read the Python SDK docs for the exact parameter names first** [VERIFY]. If the fallback beta rejects structured output, drop `betas`/`fallbacks`, keep the refusal check, and tell P2 to log it. Check `stop_reason`: `refusal` → failed. Parse JSON, validate with Pydantic; retry once on failure; second failure → failed (`extraction_failed`). Increment the daily counter. **Done when** one demo file returns a valid `Extraction` with a key, and `TIMEOUT_S=0.001` returns failed.

**T2.P1.2 Verification (1:00)**: implement ai-system section 3 **in order**: (1) exact duplicate by SHA-256 (any student, any status but `failed`) → `duplicate`/`duplicate_file`; (2) visual duplicate by pHash (images via `imagehash.phash`; PDFs render page 1 at 150 dpi with `pypdfium2`) within Hamming ≤ `PHASH_MAX_DISTANCE` (6) → `duplicate_image`; (3) `(issuer_normalised, certificate_id)` equal → `duplicate_certificate_id`; (4) `is_certificate=false` → `needs_review`/`not_a_certificate`; (5) `contains_instructions=true` → `needs_review`/`injection_text`; (6) tamper only if `TAMPER_CHECK_ENABLED` (stub returns False until A8); (7) confidence `0.40·name_ok + 0.25·issuer_known + 0.20·date_ok + 0.15·complete`, rounded to 2 decimals. `name_ok` = `rapidfuzz.fuzz.token_set_ratio ≥ 85` after NFKD normalisation, accent stripping, punctuation and honorific (`mr`, `ms`, `dr`) removal; `issuer_known` = match against `Issuer.name`/aliases with ratio ≥ 90; `date_ok` = not null, not after today, not before `enrolled_on - 730 days`; `complete` = title, issuer, date and at least one skill. ≥ `CERT_AUTO_CERTIFY_MIN` (0.85) → `certified`; otherwise `needs_review` with one reason per failed check (`name_mismatch`, `unknown_issuer`, `date_invalid`, `incomplete`). `ExtractionFailed` → `failed`, reason `extraction_failed`. Duplicate lookups live in `repos/ml_repo.py`. **Done when** `tests/test_verification.py` covers every rule row and the six EVAL-02 planted cases (**6/6**).

**T2.P1.3 Extraction cache (0:40)**: run `python -m scripts.build_extraction_cache seed/certificates seed/demo_uploads` (writes `extraction_cache/<sha256>.json` including `_prompt_version` and `_model`). **Before correcting anything**, diff against `labels/certificate_labels.csv` and save the **raw** accuracy (EVAL-01) to `docs/plan/eval-results.md`. Then correct wrong fields in the cache and mark `cache_corrected=yes` in the CSV. Commit the cache. **Done when** with `LLM_PROVIDER=none` every seed and demo file is a cache hit. No key? Hand-write the three demo JSONs.

**T2.P1.4 Trust recompute (0:20)**: `apply_certified` (normalise skills → concepts → `PROVES` → recompute each) and the full `recompute_skill`: trust = 2 if `endorsed_by` non-empty, else 1 if certified evidence proves it, else 0 if `claimed`, else delete the `HAS_SKILL` edge; write `trust_level`, `evidence_ids`, `updated_at`; recompute the student embedding at the end. **Done when** TEST-15 passes.

**Demo uploads must produce** (TEST-13): `aarav_dl_pytorch.png` → certified; `aarav_cv_workshop.png` → certified; `aarav_python_copy.jpg` → duplicate (`duplicate_image`); `aarav_embedded_c.png` (holder "Arav M.") → needs_review (`name_mismatch`).

## Phase 3 (by 10:00)
**T3.P1.1 Scorer (1:00)**: pure function `score(required, idf, skills, similar, sem, cfg) -> Fit`, no I/O. Per required concept `r`: if held, contribution `idf(r)·t(r)` (chip `matched` if trust ≥ 1 else `claimed_only`); else best held `s` with `SIMILAR_TO(r,s) ≥ SIM_MIN` maximising `score·t(s)` (chip `near`, `via=s`); else `missing`. `idf(c) = ln(1 + N/(1+df(c)))`, `W = Σ idf(r)`. `semantic = max(0, cosine)`. Components: `round(100·0.25·semantic,1)`, `round(100·0.60·skill_part,1)`, `round(100·0.15·concept_part,1)`; score = sum of the rounded components. Empty `R` → semantic only plus the note "This opening lists no required skills". Verdict: ≥ 65 `ready`, ≥ 40 `close`, else `not_yet`. Gains: re-run with each non-matched `r` at trust 1, sorted descending. **Done when** TEST-18 passes: the worked example gives exactly **43.4 → 68.5** with semantic fixed at 0.70, and the boundaries 39.9/40.0/64.9/65.0 behave.

**T3.P1.2 Fit APIs (0:45)**: `api/v1/match.py` API-012 (student: `my_fit` plus `my_application_status` for each open opening), API-013, API-015 (student self only; faculty only for `student_id` who is an **applicant of their own opening**, else 404; chips carry `source`), API-016 (owner only; rank applicants; ties: more matched chips, then `applied_at`). `repos/match_repo.py`: one read query per call returning required concepts, the student's `HAS_SKILL` trust and first evidence ids, `SIMILAR_TO` pairs, and both embeddings. Response models are explicit (never return `embedding`). **Done when** API-015 for Aarav matches backend section 4.1's shape, and TEST-22 and TEST-39 pass.

**T3.P1.3 Seed tuning for A-16 (0:30)**: measure the real Aarav ↔ `op-edge-ai` cosine; the **before** score must land in **38-50** and the **after** (after the TEST-13 uploads) at **65 or more**. If not, change **seed text only** through your own `seed/fit_tuning.json` (Aarav's bio and interests, the opening description). **Never** change the formula, thresholds or P4's seed JSON. (If you change the formula anyway, update AC-004.x, TEST-18/19 and ai-system section 4 in the same commit.) Check that the three seeded applicants of `op-edge-ai` score in different bands. **Done when** TEST-19 passes on a fresh seed.

**T3.P1.4 Fit UI and SCR-03 (0:45)**: components in `components/fit/`: `FitScoreRing` (score + verdict text, `aria-label`, reduced-motion aware), `ScoreBreakdownBar` (3 segments, values also as text), `FitPanel`; chips grouped Matched / Claimed only / Near ("via X") / Missing; gains as "Certify X → N"; "Prove it" links to `/student/certificates`. Apply button → API-017: 201 pill "Applied · Pending", 409 `ALREADY_APPLIED` pill "Applied", `OPENING_CLOSED` copy. Page in your own route `src/app/student/openings/[id]/page.tsx` (create it first). Render P3's `<WhyGraph openingId={id} />` only when `features.whyGraph` is true. Push stubs with final props for `components/fit/*` and `SkillGapCard.tsx` (returns `null`) **by 7:30**. **Done when** index section 7 steps 1 and 3 render correctly against the live API.

## Phase 4 add-ons (10:00-12:30, only if G3 passed; each merges only with the scenario still green)
- **A2 Why API** (API-020): chips → `WhyGraph` (nodes `student:<id>`, `concept:<name>`, `opening:<id>`; edges HAS_SKILL, SIMILAR_TO with score, REQUIRES). **A5 Skill gap** (API-021, top 5 by `openings_unlocked` then `total_gain`) plus the real `SkillGapCard` and `skillGap: true` in `lib/features.ts` (your line only). **A6 Eval table**: `scripts/eval_match.py` computes nDCG@10 and P@5 (hybrid vs the Jaccard keyword baseline) over `seed/labels/match_labels.csv` and writes `docs/plan/eval-results.md` with the EVAL-01 raw accuracy; if the hybrid does not win, report it as measured, never re-tune on the test labels. **A8 Tamper** (rule 6): EXIF `Software` tag in `photoshop|gimp|pixlr|snapseed|picsart`, or ELA mean difference > `ELA_THRESHOLD`; tune so only the planted file trips; enable `TAMPER_CHECK_ENABLED` only after tuning. Cut order if short on time: tamper, eval table, skill gap, Why graph.

## Phase 6
T6.P1.1: with Wi-Fi off and `LLM_PROVIDER=none`, restart the stack, reseed, run index section 7 steps 1-3; every demo upload is a cache hit (record TEST-52 in `docs/plan/qa-log.md`). Default for the demo is cache. T6.P1.2: give P4 the eval numbers; **only measured numbers appear on the deck**.

# 7. What you need from others (build against fixtures until it lands)

| Need | From | When |
|---|---|---|
| Scaffold on `main`, then `core/database.py`, `core/errors.py`, `api/deps.py` | P2 | scaffold 0:20; core by 2:00 |
| `run_read`/`run_write`, `notify`, `record_status`, `conftest.py` fixtures | P2 | 2:30-4:00 |
| Seed loader and data matching backend section 10 | P4 | by 4:00 |
| `components/ui/*`, shell, `lib/features.ts`, fixtures pattern | P3 | 2:30 |
You owe: `ml/` stubs (1:00, 1:30, 2:00, 4:15), `components/fit/*` stubs (7:30).

# 8. Git workflow (binding; the full text is `CONTRIBUTING.md`)

- Work **only** on `feature/p1-ml-fit`, created from the latest `main` **after P2's scaffold commit**. No scaffold yet? Read the docs and wait; do not create it. Set once: `git config pull.rebase true`.
- **Never push to `main`. Never merge a PR (not even your own).** Open a PR **only when the lead announces a checkpoint** (C1 around 2:30, G1, G2, G3, freeze, final) or when your whole work is done. Title `P1 <checkpoint>: <summary>`, fill in `.github/pull_request_template.md`, tag the lead, then **stop**. The lead merges with "Rebase and merge", so every commit lands on `main` as written.
- Commits are small and working, message `T2.P1.2 REQ-002: add duplicate checks`. No merge commits, no "wip" or "fix fix". Contract changes are not yours: ask P2 for a `CONTRACT:` commit.
- Daily loop: `git fetch origin && git rebase origin/main` → work → `python tools/check_ownership.py P1` (must print `ok`) → `pytest -q <your test files>` → `git push --force-with-lease origin feature/p1-ml-fit`.
- After the lead merges one of your PRs: `git fetch origin && git rebase origin/main`, push with `--force-with-lease`, keep working on the **same** branch.
- A rebase conflict in a file you do not own means **stop and ask**. Update only your own rows in `docs/phases/status.md`, in a separate small commit.

# 9. Definition of done (per task)

The task's **Done when** passes; its TEST- cases exist and are green; `ruff check backend` is clean; `check_ownership.py` prints `ok`; your `status.md` row is updated; the index section 7 scenario still runs on a fresh seed (`docker compose exec backend python -m scripts.seed --reset`, then `docker compose exec -e TODAY_OVERRIDE=2026-10-10 backend pytest -q`).

# 10. If you fall behind

Switch the live LLM off (`LLM_PROVIDER=none`) and use the cache; hand-write the three demo cache files; cut tamper, then eval table, then skill gap, then the Why graph. **Never cut:** the extractor contract, verification rules, trust recompute, the scorer and Fit Check. Say so at the next stand-up, not at the end.

# 11. Your first 60 minutes

1. Read section 3 (30 min). 2. After the scaffold lands: `git fetch && git checkout -b feature/p1-ml-fit origin/main`. 3. Do T0.P1.1. 4. Run `python tools/check_ownership.py --list P1`. 5. Post your first blocker in the team chat within the hour.
