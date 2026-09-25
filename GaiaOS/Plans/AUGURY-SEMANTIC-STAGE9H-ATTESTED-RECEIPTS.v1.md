# Stage 9H: Attested Owner-vs-AUGURY Comparison · v1

**Authority:** NAOMI/LIGEIA. **Engineering steward:** 58 · ANVIL. **Mode:** HEATDEATH / read-only / BIGBANG locked.

## Why

Stage 9G added an owner-keyed `sf1_` sample fingerprint, but a copied or fabricated receipt can still claim any fingerprint. An identical text label by itself does not authenticate the reported owner judgment or the model result. The first 2026-09-25 Stage 9F receipts are unsigned and do not share a fingerprint; **do not retroactively certify them**.

## Bounded implementation

`api/augury_semantic_receipts.py` constructs strict allowlisted redacted payloads and domain-separated owner-key HMAC-SHA256 receipt attestations (`ra1_`). Signatures are validated with constant-time comparison. Each attestation covers its role, case results and exact Stage 9G sample fingerprint. The private owner key is never copied to a receipt, transmitted to OpenAI, logged, persisted or returned. Owner-key rotation invalidates these attestations.

The new owner-only `POST /gaiaos/memory/augury-semantic-owner-oracle-finalize` accepts **only** three A/B/COLLISION/UNKNOWN decisions and the preview fingerprint. It performs another bounded **model-free read** of the approved two-record/five-case sample. Changed or unavailable material fails closed before signing. The server computes the generator target and support set from canonical questions; the browser cannot appoint itself the ground-truth source for expected slots. The receipt contains no statements, IDs, questions or sources. COLLISION means supported slots `[0,1]`, with no unique correct record; UNKNOWN means `[]`.

The existing explicitly owner-consented semantic-shadow route now signs only a bounded, structurally valid result whose exact quotes and GALAXY readbacks have been checked and whose sample fingerprint was computed from the real approved read. Early/unbound/failed-source HOLD results are **unsigned**. No extra model calls or token budget are introduced.

`POST /gaiaos/memory/augury-semantic-compare` requires owner bearer authentication and accepts only two short, separately attested redacted receipts. It validates both roles and signatures, checks unchanged exact fingerprint, parity/negative controls and source readback, then invokes the pre-existing pure category-aware comparator. Tampered, oversized, extra-field, old unsigned or cross-key receipts fail closed. **No MemoryOS read, model call, background process, state write or E-LANE mutation** occurs in this compare route.

The authenticated browser console lets Naomi finalize judgments, copy the signed owner receipt, retain/paste a separately consented signed AUGURY receipt, and compare them through one explicit **no-model-call** button. Mandatory `tests/test_gaiaos_console_browser_contract.py` parses the *served* JavaScript, verifies every button is wired, and replays the broken-newline negative control.

## Interpreting outcomes

Agreement on a **uniquely** supported record is distinct from the model selecting one valid record but **missing COLLISION**. Even a matching owner/model COLLISION is an agreement on ambiguity, not independent proof that each record entails the query. Fully matching results are labeled `AGREEMENT_ON_BOUNDED_SAMPLE_ONLY` and leave general semantics, historical coverage, and BIGBANG activation at HOLD. The original full Stage 7, real historical supersession, restart/Turso and final owner cutover requirements remain unchanged.

## Release/deployment boundary

The user's prior Stage 9G deployment is user-reported, not independently certified by this source change. Render auto-deployment stays OFF. Stage 9H source CI passing does **not** prove a live deployment; verify the actual deployed commit via the public `/health` receipt after any separately owner-controlled manual deployment. No new model invocation is authorized in this milestone. Stage 9F's first one-call consent has already been consumed. Preserve the existing `//PW:PRESERVE//` workflow, six separate E-LANES, owner authority, and HEATDEATH fail-safe.
