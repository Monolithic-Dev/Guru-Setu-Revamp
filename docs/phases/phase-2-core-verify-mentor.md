# Phase 2: Core A, Verify and Mentor (4:00–7:00)
Purpose:      Make the certificate pipeline work end to end and give mentors the write side of the mentoring system: allotment, sessions, confirmation, action items and issues.
Audience:     P1–P4.
Depends on:   phase-1-foundation.md (G1 passed); ai-system §2–§3; backend §4, §6.1, §6.2, §6.5–§6.8, §9; security §4, SEC-06; ux-flows FLOW-02, 05, 06, 07, 08
Status:       Draft v1

---

## 1. Goal and gate

**Goal:** by 7:00, Aarav can upload the 4 demo files and get the right statuses, a reviewer can approve one, the HOD can allot, and Meera can log a group session whose attendees, action items and issues are stored and visible.

**G2 midpoint integration check (7:00, 30 minutes, whole team, on `main`):**
- [ ] TEST-13 green: demo uploads → certified, certified, duplicate (`duplicate_image`), needs_review (`name_mismatch`)
- [ ] TEST-14, 15, 16 green (failure path, manual entry, trust rollback, schema retry)
- [ ] TEST-05 (certificate/file/session scope), TEST-06, TEST-12 green
- [ ] TEST-27, 28, 29, 30, 31 green (allotment, session validation and rollback, confirm, action items, issues)
- [ ] TEST-20 green (notes visible only to the author via API-027)
- [ ] In the browser, against live endpoints with no fixtures: SCR-04 upload and poll, SCR-10 approve/reject, SCR-12 allot, SCR-08 save a 12-attendee session
- [ ] Seed now includes about 25 certificates processed via the cache (`source:"cache"`), and Aarav's python is trust 1
- [ ] **Cut review:** each person states whether their Phase 3 tasks fit in 3 h. Apply the cut order now, not at 9:30.

## 2. Task board

| ID | Owner | Est | Depends on | Task |
|---|---|---|---|---|
| T2.P1.1 | P1 | 1:00 | T1.P1.3 | MDL-01 provider call (image/PDF, structured output, fallbacks, refusal, retry) |
| T2.P1.2 | P1 | 1:00 | T1.P1.2 | Verification: hashes, checks, confidence, routing + unit tests |
| T2.P1.3 | P1 | 0:40 | T2.P1.1, T1.P4.3 | Build the extraction cache for seed + demo files; hand-check against labels |
| T2.P1.4 | P1 | 0:20 | T2.P1.2 | Trust recompute (backend §6.2), complete |
| T2.P2.1 | P2 | 1:00 | T1.P2.3, T2.P1.2 (interface) | Certificates API-005..011, upload intake, JOB-01, JOB-02 |
| T2.P2.2 | P2 | 0:25 | T1.P2.3 | Allotment API-022/023 |
| T2.P2.3 | P2 | 1:00 | T1.P2.4 | Sessions API-026/027/028 with idempotency |
| T2.P2.4 | P2 | 0:35 | T2.P2.3 | Action items API-030; issues API-031/032 (P0 subset) |
| T2.P3.1 | P3 | 1:15 | T1.P3.4 | SCR-04 certificates (FLOW-02) |
| T2.P3.2 | P3 | 0:40 | T1.P3.4 | SCR-10 review queue (FLOW-05) |
| T2.P3.3 | P3 | 1:05 | T1.P3.4 | SCR-08 session form (FLOW-07) |
| T2.P4.1 | P4 | 0:30 | T1.P4.3 | Finish certificate set and labels (if not done) |
| T2.P4.2 | P4 | 0:30 | T2.P1.3, T2.P2.1 | Seed step 5: process seed certificates through the pipeline |
| T2.P4.3 | P4 | 0:50 | T1.P3.4 | SCR-12 allotment (FLOW-06) |
| T2.P4.4 | P4 | 0:50 | T1.P3.4 | SCR-05 My mentorship, on fixtures until API-029 lands in Phase 3 (FLOW-08) |
| — | P4 | 0:20 | — | Buffer: help P3 with SCR-08 sub-components, or collect 3–5 student/faculty quotes |

**Interface agreed at 4:00 (P1 ↔ P2), so both can code at once:**
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

## 3. Task details

### T2.P1.1 MDL-01 provider call (1:00)
- **Spec:** ai-system §2.1, §7, §8, §11
- **Steps:**
  1. Images: open with Pillow, apply the EXIF orientation, convert to RGB, downscale the longest side to 1568 px, re-encode as PNG, base64 → `{"type":"image","source":{"type":"base64","media_type":"image/png","data":…}}`. PDFs: base64 → `{"type":"document","source":{"type":"base64","media_type":"application/pdf","data":…}}`.
  2. Request: `client.beta.messages.create(model=LLM_MODEL, max_tokens=2048, betas=["server-side-fallback-2026-07-01"], fallbacks="default", output_config={"format":{"type":"json_schema","schema":SCHEMA},"effort":"low"}, messages=[{"role":"user","content":[file_block,{"type":"text","text":PROMPT}]}])`. Client `timeout=LLM_TIMEOUT_S`, `max_retries=1`.
     - Before coding, read the Python SDK docs for the exact parameter names of `output_config` and `fallbacks`.
     - If the fallback beta rejects structured output, drop `betas`/`fallbacks` and keep the refusal check. Record which way you went in `decisions-log.md` (ai-system §2.1 [VERIFY]).
  3. Check `stop_reason`: `refusal` → failed. Parse the text block as JSON, then validate with Pydantic. On failure retry once; a second failure → failed (`extraction_failed`).
  4. Increment `Counter{name:'llm_calls', date:today}`. Log the §11 fields only.
- **Done when:** with a key, one demo file returns a valid `Extraction`. With `TIMEOUT_S=0.001`, it returns failed.

### T2.P1.2 Verification (1:00)
- **Spec:** ai-system §3 (the rule table is the spec; implement it in order)
- **Steps:**
  1. `sha256` of the raw bytes. `phash`: images via `imagehash.phash(PIL)`; PDFs by rendering page 1 at 150 dpi with `pypdfium2`.
  2. Duplicate rules 1–3 against existing Evidence: query by sha256 and by `(issuer, certificate_id)`; pHash by loading all `(id, phash)` and computing Hamming distance in Python.
  3. Rules 4–5, then 6 only if `TAMPER_CHECK_ENABLED` (stub returns False until Phase 4).
  4. Confidence: `0.40·name_ok + 0.25·issuer_known + 0.20·date_ok + 0.15·complete`, using `rapidfuzz.fuzz.token_set_ratio`; honorific stripping per ai-system §3; `date_ok` uses `enrolled_on − 730 d`.
  5. Routing: ≥ `CERT_AUTO_CERTIFY_MIN` → certified; otherwise needs_review with one reason per failed check. `ExtractionFailed` → `failed`, with reason `extraction_failed`.
- **Tests:** `tests/test_verification.py` covers each rule row and the EVAL-02 planted cases (6/6).
- **Done when:** the unit tests pass, and EVAL-02 gives 6/6.

### T2.P1.3 Extraction cache (0:40) [CUT-2: hand-write 3 JSONs]
- **Spec:** ai-system §2.4, NFR-04, EVAL-01
- **Steps:**
  1. Run `python -m scripts.build_extraction_cache seed/certificates seed/demo_uploads`, which writes `extraction_cache/<sha256>.json` including `_prompt_version` and `_model`.
  2. Diff each file against `labels/certificate_labels.csv`. Save the raw-output accuracy now (EVAL-01, first run) to `docs/plan/eval-results.md` before correcting anything.
  3. Correct the wrong fields in the cache and set `cache_corrected=yes` in the CSV.
  4. Commit the cache.
- **Done when:** with `LLM_PROVIDER=none`, every seed and demo file is a cache hit.

### T2.P1.4 Trust recompute (0:20)
- **Spec:** backend §6.2, REQ-003, AC-003.2
- Implement `apply_certified` (normalise skills → concepts → `PROVES` → recompute each) and the full `recompute_skill` (trust 2 > 1 > 0 > delete). Recompute the student embedding at the end.
- **Done when:** TEST-15 passes.

### T2.P2.1 Certificates API and jobs (1:00)
- **Spec:** API-005..011, JOB-01, JOB-02, SEC-06, SEC-11, backend §6.1, §6.9, security §4 (certificate rows)
- **Steps:**
  1. **Upload intake (API-005):**
     - stream the body to a temporary file while counting bytes (> `MAX_UPLOAD_MB` → 413 `FILE_TOO_LARGE`);
     - check the magic bytes (→ 415);
     - for PDFs, count pages with pypdfium2 (> 5 → 422);
     - move the file to `UPLOAD_DIR/<uuid>.<ext>`;
     - create `Evidence{status:'processing', sha256, …}` + `SUBMITTED`;
     - schedule JOB-01 with `BackgroundTasks` and return 202 `Certificate`;
     - rate-limit 20/hour per user.
  2. **JOB-01:**
     - re-read the Evidence and exit if it is not `processing`;
     - `extract()` → `verify()`;
     - one write tx: set fields, status, confidence, reasons and source; if certified, `apply_certified`; `record_status`; notify (`certificate_result` to the student; `review_needed` to the assigned mentor if `needs_review`).
     - Any exception → `failed`.
  3. **JOB-02** in `services/jobs.py::startup()` (already called by `main.py`): Evidence `processing` older than 60 s → `failed` with reason `interrupted`.
  4. **API-006/007:** student scope; omit `duplicate_of` for students. **API-008:** only from `failed`, set fields, `source:'manual'`, confidence = min(computed, 0.50), reason `manual_entry`, → `needs_review`.
  5. **API-009/010:** faculty sees its assigned mentees; HOD sees the department. Review only from `needs_review` (409 `ALREADY_REVIEWED` otherwise); `reject` requires a reason of 3–300 characters; approve → `apply_certified`.
  6. **API-011:** `FileResponse` with `X-Content-Type-Options: nosniff` and `Content-Disposition: inline`; scope as API-006 plus reviewers.
- **Done when:** TEST-06, 12, 13, 14 and the certificate cases of TEST-05 pass.

### T2.P2.2 Allotment (0:25)
- **Spec:** API-022/023, backend §6.8, REQ-007, REQ-028
- One write tx per request, following backend §6.8 exactly: handover, no-op, create, notify `allotted`, `record_status(entity_type='mentorship')`. API-022 returns the mentor loads with `overloaded`, plus the unallotted list.
- **Done when:** TEST-27 passes.

### T2.P2.3 Sessions (1:00)
- **Spec:** API-026/027/028, backend §6.5, ENT-09, ENT-19, ENT-21, REQ-008, 009, 015, SEC-07
- **Steps:**
  1. Pydantic `SessionCreate` mirrors the openapi schema. Extra validation: date ≤ today and within the current or previous term; `individual` → 1 attendee; `guide` → `opening_id` required; follow-up after the date; action and issue students ⊆ attendees; due ≥ date.
  2. **Idempotency:** if the `Idempotency-Key` + user exists and is < 24 h old, return the stored session's `SessionDetail` with 201.
  3. **One write tx:**
     - check every attendee has an active MENTORS link of the right type (`NOT_YOUR_MENTEE`, 422, naming the attendee);
     - create the Session, `LOGGED`, `ATTENDED_BY{present}`, ActionItems (`open`) + `CREATED` + `FOR`, and Issues (`raised`) + `RAISED` + `ABOUT`;
     - `record_status` for each created item;
     - notify `session_logged` to present attendees and `action_assigned` per mentee-owned item;
     - store the IdempotencyKey.
  4. **API-027 response shaping:** `notes` only if the caller is the author; for students, `attendees` filtered to self. The role check comes first (HOD → 403); then the scope check (other faculty → 404).
  5. **API-028:** attendee only (404 otherwise); `present=false` → 409 `NOT_PRESENT`; set `confirmed_at` if null; idempotent.
- **Done when:** TEST-20, 28, 29 pass, including the fault-injection rollback.

### T2.P2.4 Action items and issues (0:35)
- **Spec:** API-030/031/032, backend §6.6, §6.7 (P0 subset), REQ-010, REQ-011
- **Action items:** a transition table keyed by the role relation (mentee-of-item vs author-mentor); `overdue` computed in the response; `record_status`.
- **Issues (P0):** API-031 by faculty with `mentor_of`; API-032 only `raised → resolved` with a resolution. The `acknowledged`/`in_progress`/`escalated`/`confidential` fields are accepted by the schema but return 409 `INVALID_TRANSITION` until Phase 4 (A4).
- **Done when:** TEST-30 and TEST-31 pass.

### T2.P3.1 SCR-04 Certificates (1:15)
- **Spec:** FLOW-02, ux-flows §4.2 (reason copy), §6 (manual form validation), components `CertificateUploader`, `CertificateCard`, `ManualCertificateForm`
- **Steps:**
  1. A file input accepting `.jpg,.jpeg,.png,.pdf`; reject > 10 MB client-side with the exact copy.
  2. After the 202, add the card in `processing` and poll API-006 every 2 s for 30 s, then show "Still working. We'll notify you."
  3. Status rendering per FLOW-02, with the reason copy from the §4.2 table. A "My skills" section from API-003 (self) with `TrustBadge`.
  4. Manual form for `failed` → API-008.
- **Done when:** uploading the 4 demo files against the live API shows the TEST-13 statuses, with the correct copy.

### T2.P3.2 SCR-10 Review queue (0:40)
- **Spec:** FLOW-05, `ReviewCard`, SEC-19
- File preview: images via `<img src>` from API-011 (fetch as a blob with the auth header, then `URL.createObjectURL`); PDFs via `<iframe sandbox src=blobUrl>`.
- Approve/Reject (reject needs a reason, 3–300 chars) → API-010; remove the card; toast; handle 409.
- **Done when:** Meera approves Aarav's Embedded C certificate, and Aarav's SCR-04 shows it Verified.

### T2.P3.3 SCR-08 Session form (1:05)
- **Spec:** FLOW-07 (field order and defaults), ux-flows §6 validation copy, NFR-03, components `SessionForm`, `AttendeePicker`, `TopicChips`, `ActionItemEditor`
- **Steps:**
  1. The attendee source is API-024. Until Phase 3, use the fixture, then switch. A query param `?student=<id>` pre-fills an individual session.
  2. Generate the `Idempotency-Key` (`crypto.randomUUID()`) on mount. Reuse it on Retry.
  3. Client validation mirrors the server rules. On a server 422, map `errors[].field` onto the inputs and focus the first one.
  4. On success, navigate back with the toast "Session saved for N students" (N = attendees with `present=true`).
- **Done when:** a 12-attendee group session with 2 action items saves in ≤ 120 s, keyboard only (rehearse for TEST-50).

### T2.P4.1 Finish certificates (0:30)
Complete the T1.P4.3 deliverables if they're behind. Verify the pHash distance and label every file.

### T2.P4.2 Seed certificates through the pipeline (0:30)
- **Spec:** backend §10 step 5
- In `seed.py`, for each entry in `certificates_index.json`: copy the file to `UPLOAD_DIR`, create the Evidence, and call the same `extract` + `verify` + `apply_certified` functions synchronously (cache hits). Statuses must follow the routing rules. Set the intended `needs_review` entries via the files' content, never by forcing a status.
- **Done when:** after a reset, Aarav's python skill is trust 1 with source `aarav_python_basics`, and `MATCH (e:Evidence) RETURN e.status, count(*)` matches the index's expectations.

### T2.P4.3 SCR-12 Allotment (0:50)
- **First (10 min):** create your own route stubs: SCR-02 `student/page.tsx`, SCR-05 `student/mentorship/`, SCR-11 `coordinator/page.tsx`, SCR-12 `coordinator/allotment/`, SCR-14 `notifications/`, SCR-15 `faculty/openings/page.tsx`, with fixtures in `src/fixtures/p4/` (parallel-work §2). Never edit P3's layouts; ask P3 if a layout needs a change.
- **Spec:** FLOW-06, REQ-007, components `MentorTable` (load, in `components/coordinator/`) and `Dialog` (P3's `components/ui/`)
- Left: the unallotted list with checkboxes. Right: mentor cards with "13 / 20" and the Overloaded badge. A mentor select plus "Assign N students to <name>" → API-023 → refresh.
- **Done when:** assigning the 2 unallotted students updates both lists live, and the student gets the `allotted` notification.

### T2.P4.4 SCR-05 My mentorship (0:50)
- **Spec:** FLOW-08, REQ-014, schema `MyMentorship`
- Sections: assigned mentor card, guides, next follow-up, sessions to confirm (API-028 button), action items (checkbox → API-030 `done`, optimistic with rollback), issues (text only when present), and applications with status pills and history.
- Build against `src/fixtures/p4/API-029.json` now. API-028 and API-030 are live already.
- **Done when:** confirming a session and marking an item done work against the live API. The list data switches to API-029 in T3.P4.4.

## 4. Risks and fallbacks

| Risk | Fallback |
|---|---|
| Structured output plus the fallback beta disagree | Drop the fallback beta (keep the refusal check); log it in the decisions log |
| pHash of the re-photographed copy > 6 | Regenerate the copy with a smaller crop, or raise `PHASH_MAX_DISTANCE` to 8 and re-run EVAL-02 for false positives |
| Session transaction is slow with 40 attendees | Use `UNWIND $attendees` in a single Cypher statement for ATTENDED_BY and items |
| P3 behind on SCR-08 | P4 builds `ActionItemEditor` in the buffer slot |
| Live extraction is unreliable | Switch the demo to `LLM_PROVIDER=none` now; the pipeline is still real, and the cache path is honest |
