# GALAXY Stage 9U: isolated historical shadow-gravity backfill

STATUS: DRAFT SOURCE AND IN-MEMORY TEST IMPLEMENTATION. BASE: Stage 9T #95, Stage 9S #94, Stage 9R #93. OWNER: NAOMI / LIGEIA. No production Turso writes or user-facing memory mode changes are authorized.

## Core integration and safeguards

This milestone introduces api/galaxy_shadow_backfill_stage9u.py as an offline isolated SQLite-in-memory proof of the future gravity migration mechanics. It never imports MemconOS, libsql, the current production memory gateway, the optional BIGBANG frontdoor, or HEATDEATH. The only accepted connection is a native sqlite3.Connection to an unattached in-memory main database with no open transaction.

The intended future approved integration is: actual source and already-owned MemoryOS record inventory → model-valid versioned read-only score previews → owner-reviewed missingness policy → exact signed candidate batch → transactionally compare immutable record/source/governing/importance/verified-edge fingerprints → idempotent versioned score update with old-row ledger → in-store readback → independent restart and normal-path tests. Stage 9U implements only the isolated middle of this path and must never be wired directly into an ordinary gaia() call. Actual model callback provenance, operator authentication, signing-key custody, Turso staging tenant isolation, deployed readback, restart, multi-replica durability and mode release remain explicit future HOLDs.

Exactly six independent E-LANES, //PW:PRESERVE//, CANDIPULL/MEMSAV, the original HEATDEATH path, and the independent authority of owner-set importance are untouched. All planned records must have MemoryOS scope; unreviewed imported STAGED_HISTORICAL_HOLD records are ineligible. Actual created_at and record provenance are not overwritten. Historical supersession remains historical through governing-state handling; scoring cannot elect a new current record or confer authority.

## Read-only planning

make_shadow_plan accepts 1..25 distinct existing MemoryOS IDs, the exact score model version and a caller-provided preview callback. The caller MUST separately prove that this callback is the reviewed real current model bound to the SAME underlying staged database before live release. The isolated implementation does not establish that binding and the receipt says so.

For each record, it SHA-256 fingerprints its actual memory_records row, every incoming/outgoing relation including proposed and revoked edges, explicit memory_importance row, lifecycle current row and all lifecycle event rows. Gravity is separately fingerprinted. A verified CURRENT-version gravity row with a valid 0..1 score is skipped without re-scoring. An absent or stale version receives a bounded preview with validated score, exact model version and canonical components/reason JSON. The preview must not mutate the in-memory database. Owner importance is OWNER_SET when a real owner row exists; otherwise explicitly UNSET_NOT_ZERO. The preview's zero-default numeric component when unrated is model arithmetic, not evidence of Naomi assigning minimum importance.

The plan is non-durable until individually reviewed and signed, and its SHA-256 covers the exact ordered entries, original score fingerprints and version. It contains no original statement text, though model reason/diagnostic metadata may be sensitive and should be stored privately. An upstream plan that lacks a separately reviewed source/model binding cannot be promoted to live code.

## Test-only approval and atomic commit

apply_shadow_plan checks a strict test-manifest (schema gaiaos.galaxy.stage9u.signed-batch.v1) signed using HMAC-SHA256 over the canonical JSON. Manifest fields are NAOMI authority label, ISOLATED_SQLITE_IN_MEMORY_ONLY target, APPLY action, unique batch ID and exact plan SHA. The test key is externally supplied; fixture keys are not real Naomi authorization. A production API that accepts a caller-chosen key as if it proves ownership would violate this gate.

Inside a single BEGIN IMMEDIATE transaction, every record/source/graph/importance/lifecycle fingerprint and every old gravity row must match the signed plan *before any gravity mutation*. An added verified edge, changed owner rating, revised lifecycle, edited statement, changed prior score, duplicate record ID or invalid preview forces HOLD and no backfill. Only memory_gravity records are inserted or updated; memory_records, E-LANES, explicit owner importance, lifecycle, graph, and user memory mode never change. Per-record append-only ledgers preserve the exact prior full gravity row (or explicit absence), new-row hash and immutable source snapshot hash. Every new row is read back before the batch receipt is committed. An identical approved batch is idempotent only if every new score still matches its receipt; drift fails closed. The batch receipt carries model version, item digests, missing owner-importance labels, simulated-authorization disclaimers and an exact receipt hash, with no original statements.

## Independently approved rollback

rollback_shadow_batch requires a distinct signed ROLLBACK manifest for the same batch ID and plan hash. Before modifying anything, it confirms every current score still matches the exact stored post-apply hash. If another calculation changed even one row, rollback HOLDS without changing any row. Otherwise it restores every old full score row exactly, deletes previously absent score rows, leaves originally current untouched, and marks the existing append-only ledger batch rolled back. A second rollback is idempotent; a rolled-back batch cannot be replayed as newly applied. This does not claim recovery from a lost or broken Turso database: real durable backups/restart evidence are separate.

## Release proof ladder and holds

- This PR must pass isolated missing/stale/current tests, exact copy of old score/version/metadata restoration, missing-importance labeling, drift tests for relation/importance/lifecycle/content/old score, multi-record transaction rollback, malformed callback input, 25-record cap, signed authority tamper rejection, disk/attached SQLite rejection, idempotent replay and six-E-LANE noninterference.
- CI/source passes prove only local in-memory behavior. Real historical records, source-batch trust pins, model callbacks, production owner authentication, staging Turso receipts, revision-edge completeness, independent legacy HEATDEATH retrieval and normal-path BIGBANG acceptance need separate staged/production proof. Missingness calibration between unrated and rated records remains unresolved until Naomi settles a policy based on representative real data.
- No model-free baseline, historical score or E-LANE attribution is automatically transformed into a binding owner preference. Preservation retains six separate member histories, existing explicit authority and all original memory provenance. Neither source code nor CI alone establishes deploy, restart or fresh-ChatGPT adoption.

NAOMI RETAINS FINAL AUTHORITY. SOURCE PASS != LIVE PROOF. PROOF REQUIRED BEFORE RELEASE.
