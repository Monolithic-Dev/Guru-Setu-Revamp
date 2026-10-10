# Decisions Log

The phase-0 decision gate (T0.ALL.1) and any later decision that changes the
plan. One row per decision, with the date and the evidence behind it.

| ID | Decision | Answer | Date |
|---|---|---|---|
| D-1 | Reuse the old GuruSetu code? | No - build from scratch (A-05). Reuse of the earlier project's concept and name still to confirm against the Genesis rules. | 2026-10-10 |
| D-2 | Is LLM use allowed, and is a key available? | **Groq only.** No Anthropic key exists, so MDL-01 changed provider: `qwen/qwen3.8-27b` on Groq through the `groq` SDK. Of the 11 models on the account it is the only one that both accepts an image and honours strict `json_schema` output, which the extraction contract needs. Verified with live calls - a clean certificate read correctly in 2.6 s, and an injected footer was flagged and not obeyed. Free tier: USD 0.00 per upload, but 8,000 tokens/minute caps throughput at about 3 certificates/minute. Details in ai-system 2.1; measurements in plan/eval-results.md. | 2026-10-10 |
| D-3 | Who is P1/P2/P3/P4? | Four lanes as in the phase plan. | 2026-10-10 |
| D-4 | Local Docker Neo4j for the demo? | Yes, `neo4j:5.26-community` under compose. | 2026-10-10 |
| D-5 | Is a submission URL required? | Not decided. The local stack (ENV-02) is what works today. | - |
| D-6 | Real start time | Not recorded. | - |

## Later decisions

| # | Decision | Reasoning | Date |
|---|---|---|---|
| L-1 | The fit components are computed in `Decimal`, not float | The ai-system 4 worked example requires `100 x 0.15 x 0.07` to round to 1.1. In binary that product is 1.0499999999999998 and rounds to 1.0, which contradicts the spec *and* breaks AC-004.2's rule that the three displayed components sum to the displayed score. Decimal also makes the demo's headline numbers identical on every machine instead of subject to float jitter. | 2026-10-10 |
| L-2 | Neo4j **driver** pinned to 5.28.7, not 6.x | Keeps the driver major aligned with the 5.26 Community server. | 2026-10-10 |
| L-3 | `email-validator` added to `requirements.txt` | `pydantic`'s `EmailStr`, used by the auth schemas, needs it at runtime. It is a dependency of a pydantic feature rather than an import, so it does not appear in an import scan - it surfaces as an `ImportError` at app startup. | 2026-10-10 |
| L-4 | Trust is derived from `Evidence`, never read back off the `HAS_SKILL` edge | backend 6.2 defines `cert_ids` as the ids of *certified Evidence that PROVES the concept*. Reading `h.evidence_ids` back instead would keep a skill certified after its only certificate was rejected, which is exactly what TEST-15 forbids. One test fixture had faked the certified state by setting edge properties with no Evidence node behind them; the fixture now creates the Evidence, and asserts the same behaviour against a state that can actually occur. | 2026-10-10 |
| L-5 | Stay on Next 14 despite open advisories | `npm audit` reports three Next advisories covering all of Next 14 (DoS via Image Optimizer `remotePatterns`, DoS via insecure RSC deserialization, request smuggling in rewrites); the fix is Next 15.5.13+ or 16. This build uses none of those features and is a local-only demo, and a frontend major-version change is a team decision rather than a unilateral one. **Revisit before any hosted deployment.** | 2026-10-10 |
| L-6 | Seed certificate templates must be visually distinct, and the generator asserts it | pHash keys on where the dark areas of an image sit, not on the words. A first version of the generator drew every certificate with one layout; their hashes landed within Hamming distance 2 and three unrelated certificates were flagged `duplicate_image`, failing TEST-13 2/4. Unrelated pairs now sit 24-38 apart while the intended re-photographed copy sits at 2. Any certificate added to the seed has to keep that separation. | 2026-10-10 |
| L-7 | Tamper check (A8) runs on the EXIF Software tag only; `ELA_THRESHOLD=0` turns ELA off | Tuned on the 25-file seed set, the six demo uploads and one planted edit (a name pasted over a JPEG and re-saved with a Photoshop Software tag). The planted file's whole-image ELA mean was 0.185, inside the range of the 31 genuine files (0.045 to 1.088, the highest a fee receipt), so no threshold separates them: the edit is small against a mostly white page. The EXIF signal is false on all 31 genuine files and true on the planted one, so `TAMPER_CHECK_ENABLED=true` is safe with ELA off. A real deployment needs a regional ELA (per block, not a whole-image mean) before ELA can be trusted. | 2026-10-11 |
| L-8 | The test suite wipes the database it runs against | By design (A-23, `tests/conftest.py`): pytest reseeds and then edits the compose Neo4j. Running `pytest`, even one file, leaves its own small graph behind (9 users, 1 opening). Always run `python -m scripts.seed --reset` after tests and before a demo or a rehearsal. | 2026-10-11 |

| L-9 | Richer profile text moves the demo fit slightly: Aarav's Edge AI score is now 43.5 close to 70.9 ready (was 42.7 to 70.0) | The embedding text gains programme, year, headline and project titles on the student side, and the faculty member's research areas, subjects and preferred skills on the opening side (plan section 4.3). Only the 25 percent meaning part moves; the formula, weights and cut-offs are untouched, and the numbers stay inside A-16 (38 to 50, then 65 or more). | 2026-10-11 |
| L-10 | A project completion record is Evidence certified by the guide, and the guide endorses the skills they vouch for (no new trust level) | REQ-027 already means "a named faculty vouches for a skill after working with the student", so completing guided work reuses it: the record is `Evidence` (kind `project_record`, no file) that PROVES the skills, and the guide is added to each skill's `endorsed_by`, so trust stays derived (L-4) and shows "Faculty-verified · Dr. X". The guide can vouch only for skills the opening required or the student already lists, so a record cannot invent a skill. There is no grade field, and the summary text is kept out of exports. Completing without a record is now a 422. | 2026-10-11 |

## Contract changes

| Change | Why | Regenerated |
|---|---|---|
| `Health.llm_provider` enum gains `groq` (openapi.yaml) | D-2. Additive: no field renamed or removed, so no client breaks. Without it the health route returned 500 on response validation. | `backend/app/schemas/generated.py` re-run through `datamodel-codegen` |
| `MenteeOverview.attention_details` added (optional) | REQ-029: the service already put it in the overview, but the response model dropped it, so Mentee 360 could not show the suggested-at-risk detail. Additive and optional. | `generated.py` re-run; P3 regenerates `types.ts` after merge |
