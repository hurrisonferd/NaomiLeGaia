# GALAXY / AUGURY Stage 9G: Bound Sample and Collision Semantics

**Authority:** NAOMI / LIGEIA. **Engineering:** 58 · ANVIL. **Mode:** HEATDEATH release-locked, read-only shadow. **Production activation:** NONE.

## Why this exists

The first live Stage 9F semantic result had three RESOLVED cases with exact quotes, strict read-only ritual compilation and GALAXY readback, but all three mismatched the generator's mechanically assigned "expected" record. Naomi's subsequent independent local owner review judged B, A and COLLISION (both A and B) against generator A, B and A. The original two redacted receipts did **not** share a sample identity, so apparent overlap is conditional. For COLLISION, the owner's old redacted `generator_expected_supported=false` came from encoding a null unique `owner_slot`, not proof that A was unsupported.

## New source contract

`api/augury_semantic_sample.py` produces `sf1_<32 hex>`: an HMAC-SHA256 fingerprint, domain separated and keyed by GaiaOS's existing **private owner bearer key**. Its preimage is the exact ordered two approved record IDs, their complete approved statements and source-provenance fields, and five ordered staged questions including original generator slots. The key and preimage never appear in the redacted receipts or OpenAI request. Different record order, source text, source provenance, questions, generator mapping, or owner key produces a different fingerprint. Owner-key rotation intentionally makes older fingerprints incomparable.

The authenticated owner-oracle preview and optional separately authorized AUGURY model shadow compute the fingerprint from their **actual independently read source sample**. The static GaiaOS console now includes it in both **redacted** receipt types, never the raw source. If the owner review is still loaded and the owner separately authorizes the model call, the console sends its fingerprint as a precondition: changed input holds **before any model invocation**. Unbound historical receipts remain unbound; do not backfill their identity.

The corrected owner oracle copy format records:
- `owner_supported_slots=[0]` for A, `[1]` for B, `[0,1]` for COLLISION, or `[]` for UNKNOWN.
- `generator_expected_supported` is membership in that support set, not unique-answer agreement. For COLLISION, either A or B is a supported candidate, while `generator_expected_is_unique_owner_answer=false`.
- The owner choice is independent human adjudication, not automatically verified source entailment.

The model's redacted results report `model_selected_slot` and `model_candidate_slots`. RESOLVED contains one grounded selected slot if its exact quote and GALAXY readback pass. COLLISION explicitly presents candidate slots `[0,1]`, **no selected unique slot**, no quoted proof for both, and remains HOLD pending independently adjudicated support; UNKNOWN has no candidates. The unmodified 2-rare-concept / 2-of-3 literal admission threshold still governs actual readbacks.

`compare_redacted` is a pure, offline, fail-closed function: it rejects absent/mismatched sample fingerprints, failed negatives, missing legacy parity, unexpected writes, fabricated quote/readback evidence, malformed owner support sets, and unknown result shapes. It distinguishes agreement on unique answers, agreement on a claimed collision, and selecting one valid member while **missing a collision**. Even total categorical agreement is `AGREEMENT_ON_BOUNDED_SAMPLE_ONLY`, never general semantic quality or BIGBANG readiness.

## Safety and next gate

This change performs **no second provider/model invocation**. The original one-call authorization is consumed; any future call requires fresh explicit owner authorization and fresh browser consent. Retain the full live Stage 9F HOLD receipt and historical proof gap. Existing `//PW:PRESERVE//`, six individual E-LANES, owner authority, legacy HEATDEATH parity, Turso protections and the BIGBANG release lock remain unchanged. Render stays manual owner-deploy; source CI PASS is not live deployment proof.

This milestone's CI must prove matching fingerprints for the exact same data, mismatch on every material input change, owner-key absence and source drift fail closed, collision support-set semantics, withheld model calls on mismatched preview fingerprints, owner authentication and `store=false`, strict read-only source verification, and the console's mandatory served-JavaScript/button integrity gate.
