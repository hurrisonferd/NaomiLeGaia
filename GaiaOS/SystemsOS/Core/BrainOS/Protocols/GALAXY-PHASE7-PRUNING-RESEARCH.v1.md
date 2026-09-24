# GALAXY Phase 7A — Finite-storage pruning research

TITLE: Read-only pruning eligibility and dependency review
AUTHORITY: NAOMI / LIGEIA
OWNER: GaiaOS / MemoryOS + BrainOS
STATUS: PHASE 7B LIVE ZERO-WRITE PROVEN / PHASE 7C LIVE POSITIVE CANARY PROVEN / PHASE 7D LIVE TOMBSTONE CONTRACT PROVEN / PHASE 7E LIVE SHADOW WRITE+READBACK PROVEN / RESTART PERSISTENCE PENDING
VERSION: galaxy.phase7.pruning-research.v1

## Purpose

Phase 7 begins by studying which durable records could become candidates for a future finite-storage policy without granting deletion authority.

This slice is intentionally read-only. It may classify a record as a PRUNABLE_RESEARCH_ONLY candidate. It may not:
- set lifecycle state PRUNABLE;
- delete or rewrite a memory record;
- remove relations, lifecycle history, receipts, gravity, importance, or synthesis provenance;
- attenuate production retrieval;
- expose a destructive endpoint;
- infer Naomi authorization from research eligibility.

PRUNABLE_RESEARCH_ONLY != PRUNABLE lifecycle state != permission to delete.

## Candidate research conditions

A record is eligible for the bounded research-candidate label only when all current conditions are true:
1. the durable record exists in MemoryOS and remains ACTIVE at the MemoryOS record layer;
2. its GALAXY lifecycle state is COMPRESSED;
3. its governing state is not ordinary-current-context eligible;
4. it does not itself govern another record through a VERIFIED outgoing REVISES or SUPERSEDES edge;
5. it is not required as a source by a recorded synthesis;
6. it is not itself a synthesis record requiring a separate provenance policy.

Incoming VERIFIED SUPERSEDES evidence may support the historical/non-current classification. It is preserved and never treated as deletion permission.

## Destructive gate

Even a research candidate remains NOT destructively eligible.

The following gates are deliberately false in Phase 7A:
- tombstone protocol implemented: false
- destructive rollback / restore proof: false
- destructive canary proof: false
- explicit Naomi destructive policy authorization: false
- physical pruning enabled: false
- production retrieval attenuation enabled: false

A later phase may research these gates separately. None is authorized by this document.

## Output contract

The read-only reviewer returns:
- record and lifecycle state;
- governing-state evidence;
- verified relation dependencies;
- synthesis provenance dependencies;
- research hold reasons;
- whether the record qualifies only for PRUNABLE_RESEARCH_ONLY study;
- destructive gate state;
- explicit writes_performed: [];
- explicit physical_delete: false;
- explicit production_retrieval_changed: false.

## Proof boundary

Source and offline tests can prove that this implementation performs read-only classification against the tested runtime schema. They do not prove live carrier deployment, long-horizon storage economics, safe destructive pruning, or a restoration path.

## Next gate

After source CI passes, Phase 7B may add a bounded live read-only review endpoint or controlled fixture review. It must still perform zero destructive effects. Tombstones, actual PRUNABLE transitions, physical deletion, and production attenuation remain separately gated.


## Phase 7B — bounded live read-only surface

Phase 7B exposes exactly one initial carrier surface:

`GET /galaxy/pruning/phase7-fixture-review`

Properties:
- browser-session authentication is required;
- the route accepts no mutation body and exposes no POST pair;
- it reviews only the exact controlled Phase-6 fixture ID at this stage;
- it executes the Phase-7 reviewer between deterministic before/after evidence snapshots;
- it compares monitored table counts plus the controlled record, lifecycle row, lifecycle history, related edges, synthesis rows and record receipts;
- it returns `PASS_ZERO_WRITE_READBACK` only if every observed before/after check is unchanged;
- classification may still be HOLD. Zero-write proof and pruning eligibility are deliberately independent.

The Phase-6 fixture currently ended its proven campaign ACTIVE. Therefore a live Phase-7B fixture review is expected to HOLD pruning eligibility unless its state has separately changed, while still proving zero observed writes if the surface is behaving correctly.

No generic record mutation route, PRUNABLE transition, physical delete, production attenuation or destructive authorization is added by Phase 7B.

### Phase 7B proof ladder

SOURCE -> CI -> DEPLOY MAIN -> AUTHENTICATED GET -> ZERO-WRITE READBACK -> PRESERVE RECEIPT.

A successful source gate does not prove deployment. A successful live GET does not prove destructive pruning safety.


## Phase 7B live proof observed 2026-09-24

Naomi supplied the authenticated live route response after redeploying main.

Observed:
- status HOLD
- hold reasons: LIFECYCLE_NOT_COMPRESSED, CURRENT_DEFAULT_ELIGIBLE, SYNTHESIS_PROVENANCE_DEPENDENCY
- readback_status PASS_ZERO_WRITE_READBACK
- zero_write_readback true
- every readback check true
- writes_performed []
- physical_delete false
- production_retrieval_changed false
- destructive_eligibility false
- monitored database counts exactly unchanged before/after

Canonical receipt:
GaiaOS/MemoryOS/PW-PRESERVE-2026-09-24-GALAXY-PHASE7B-LIVE-ZERO-WRITE-PROVEN.md

This closes Phase 7B for the bounded exact-fixture read-only proof surface.

## Phase 7C — synthetic positive research-candidate canary

Purpose: prove that the positive PRUNABLE_RESEARCH_ONLY classification branch executes on the deployed carrier without creating a disposable production memory.

Design:
- extract the Phase-7 candidate locks into one shared evaluator used by real-record review;
- feed that evaluator a deterministic synthetic historical evidence packet;
- synthetic evidence models an ACTIVE MemoryOS-shaped record with lifecycle COMPRESSED, historical superseded governance, no outgoing governing dependency and no synthesis provenance dependency;
- expose authenticated GET /galaxy/pruning/phase7-positive-canary;
- the canary accepts no runtime object and performs no production database access;
- PASS requires research_candidate=true and proposed_research_label=PRUNABLE_RESEARCH_ONLY while all destructive gates remain false.

This proves the positive classifier branch only. It does not prove a live durable record should be pruned and grants no destructive authority.


## Phase 7C live proof observed 2026-09-24

Naomi supplied the authenticated live positive-canary response after deploying main fa1cb860a83875c2bbbc36662fab492158f89cc5.

Observed:
- PASS_SYNTHETIC_POSITIVE_CANARY
- synthetic_only true
- production_database_access false
- research_candidate true
- proposed_research_label PRUNABLE_RESEARCH_ONLY
- zero research hold reasons
- every positive-canary check true
- every destructive gate remained false
- writes_performed []
- physical_delete false
- production_retrieval_changed false

Canonical receipt:
GaiaOS/MemoryOS/PW-PRESERVE-2026-09-24-GALAXY-PHASE7C-LIVE-POSITIVE-CANARY-PROVEN.md

Phase 7B and 7C together prove both classifier directions at the bounded research layer while preserving the separation between candidate classification and destructive authority.

### Source-truth repair before Phase 7D

During Phase-7D preparation, source inspection found that the real-record review and synthetic positive canary contained equivalent eligibility rules but the real-record path still held a duplicated rule block rather than invoking the shared helper directly.

This did not change the observed Phase-7B or Phase-7C outcomes. It did mean the earlier phrase "same evaluator" was too strong.

Phase 7D preparation repairs this by routing the real review through the shared eligibility helper and adds a test that substitutes a sentinel helper result to prove that the real review actually calls it.

## Phase 7D — synthetic tombstone and restore contract research

Purpose: determine the minimum evidence contract required for hypothetical reversible pruning without deleting or attenuating any production data.

Implementation:
- module: api/galaxy_phase7_tombstone.py
- authenticated GET: /galaxy/pruning/phase7-tombstone-contract-canary
- synthetic evidence only
- no runtime database object
- no database import
- no durable tombstone write
- no physical deletion
- no production attenuation

The canary:
1. constructs a synthetic evidence bundle containing record, lifecycle, governing state, relations, synthesis dependencies, lifecycle history and receipt evidence;
2. builds a manifest containing the exact bundle and canonical SHA-256 integrity digest;
3. validates schema, field completeness, record identity and digest integrity;
4. reconstructs the bundle entirely in memory;
5. requires exact structural and hash round-trip equality;
6. deliberately corrupts a manifest in tests and requires restore refusal.

Even on PASS:
- tombstone_protocol_implemented remains false;
- destructive_restore_proven remains false;
- physical_pruning_enabled remains false;
- production_attenuation_enabled remains false;
- destructive_eligibility remains false.

A synthetic exact round trip is evidence for contract adequacy research only. It is not evidence that a durable tombstone survives restart, that a production record can be deleted safely, or that Naomi has authorized destructive pruning.


### Phase 7D source gate

Observed on PR #13 head:
- Phase 7A-7D source gate run 36027838867: SUCCESS
- compile Phase 7A-7D: PASS
- pruning/positive/tombstone contract tests: PASS
- formatting guard: PASS
- Phase-6 regression run 36027838636: SUCCESS

Source proof includes the shared-evaluator repair test and the corrupted-manifest fail-closed test.

Live carrier deployment of the Phase-7D canary is not yet claimed.


## Phase 7D live proof observed 2026-09-24

Naomi supplied the deployed Phase-7D canary response from main c882a2af599abe207db6952b3bb82132da2ed4ae.

Observed:
- PASS_SYNTHETIC_TOMBSTONE_CONTRACT_CANARY
- PASS_MANIFEST_VALID
- PASS_IN_MEMORY_RESTORE
- restored true
- expected SHA-256 == actual SHA-256:
  397528e5182ac3cea8183d678b6c910ffb8f73c1ea932593dc8f18b77c82b083
- round_trip_exact true
- round_trip_hash_exact true
- writes_performed []
- physical_delete false
- production_retrieval_changed false
- destructive_eligibility false
- all destructive gates remained false

Canonical receipt:
GaiaOS/MemoryOS/PW-PRESERVE-2026-09-24-GALAXY-PHASE7D-LIVE-TOMBSTONE-CONTRACT-PROVEN.md

This closes Phase 7D for the synthetic in-memory contract.

## Phase 7E — durable shadow tombstone persistence

Purpose: prove that one exact synthetic tombstone manifest can be durably stored and read back from the configured runtime store without mutating MemoryOS evidence.

Source design:
- dedicated table: galaxy_tombstones_shadow
- exact tombstone: TOMB-P7E-SYNTHETIC-HISTORICAL-V1
- exact subject identity: SYNTHETIC-P7D-HISTORICAL
- no foreign key to memory_records
- one shadow manifest row plus one runtime receipt only
- readback validates the exact Phase-7D manifest and evidence digest
- protected MemoryOS table counts must be identical before and after the shadow write
- duplicate write fails closed
- corrupted manifest readback HOLDs
- no delete route
- no MemoryOS restore route
- no production attenuation

Browser control:
- GET /galaxy/pruning/phase7-tombstone-shadow-review is read-only
- GET /galaxy/pruning/phase7-tombstone-shadow-controls is read-only
- GET /galaxy/pruning/phase7-tombstone-shadow-controls/confirm previews the one effect
- POST /galaxy/pruning/phase7-tombstone-shadow-controls/manifest requires signed session, CSRF, authority=NAOMI, approved=true and exact confirmation

Exposure does not itself authorize the shadow write. The live write remains a separate explicit Naomi action.

Even if immediate live readback passes:
- tombstone_protocol_implemented remains false until restart persistence is separately proven;
- destructive_restore_proven remains false;
- physical_pruning_enabled remains false;
- production_attenuation_enabled remains false.


### Phase 7E source gate

Corrected executable head: 0c676bd4080f0c4b616940fccc69ab3469f57bf0

Observed:
- Phase 7A-7E source gate run 36029157725: SUCCESS
- Phase-6 regression run 36029157892: SUCCESS
- production guardrails run 36029157883: SUCCESS

An earlier Phase-7E run failed because two legacy route tests used over-wide source slices and a new test incorrectly required runtime_receipts to remain unchanged despite the explicit one-receipt contract. Tests were repaired to the intended boundary:
- old GET-only routes are checked only within their own route blocks;
- protected MemoryOS tables must remain unchanged;
- exactly one Phase-7E runtime receipt is expected for the explicit shadow write.

No live Phase-7E shadow write is claimed yet.


## Phase 7E live immediate write/readback observed 2026-09-24

Naomi explicitly confirmed the exact Phase-7E shadow write on deployed main e57264d86a0a99e82de29868046b1b997b31d4c0.

Observed:
- PASS_READBACK
- tombstone TOMB-P7E-SYNTHETIC-HISTORICAL-V1
- subject SYNTHETIC-P7D-HISTORICAL
- receipt MEMREC-630a376a932741c0b8243681f550b4f3
- evidence SHA-256 397528e5182ac3cea8183d678b6c910ffb8f73c1ea932593dc8f18b77c82b083
- immediate readback PASS_DURABLE_SHADOW_READBACK
- exact manifest validation PASS
- exact manifest equality PASS
- receipt readback PASS
- protected MemoryOS counts identical before and after
- memoryos_mutation false
- physical_delete false
- production_retrieval_changed false
- destructive_eligibility false

Canonical receipt:
GaiaOS/MemoryOS/PW-PRESERVE-2026-09-24-GALAXY-PHASE7E-LIVE-SHADOW-WRITE-READBACK-PROVEN.md

This proves one exact shadow write and immediate durable readback only.

Next gate: manually restart the currently deployed carrier, then call the read-only /galaxy/pruning/phase7-tombstone-shadow-review route. Restart PASS requires the same tombstone ID, subject ID, digest, receipt ID, exact manifest and PASS_DURABLE_SHADOW_READBACK.

Until that post-restart observation:
- phase7e_restart_persistence_proven remains false;
- tombstone_protocol_implemented remains false;
- destructive_restore_proven remains false;
- physical pruning remains disabled;
- production attenuation remains disabled.


## Phase 7E live restart-persistence closure — 2026-09-24

Following the explicitly approved Phase-7E exact synthetic shadow write and PASS immediate readback, Naomi manually restarted the Render carrier. The pinned MemoryOS continuity test independently returned PASS with changed boot ID, Render instance ID and process fingerprint while recovering the exact controlled durable record. On the restarted carrier, authenticated read-only /galaxy/pruning/phase7-tombstone-shadow-review returned PASS_DURABLE_SHADOW_READBACK, unchanged exact synthetic tombstone ID, unchanged subject ID, unchanged evidence SHA-256, original linked runtime receipt, valid and exact manifest, and all ten review checks true. No new write, source-record mutation, deletion or production retrieval change occurred in this review.

Canonical receipt: GaiaOS/MemoryOS/PW-PRESERVE-2026-09-24-GALAXY-PHASE7E-LIVE-RESTART-PERSISTENCE-PROVEN.md

PHASE7E_RESTART_PERSISTENCE_PROVEN: true, bounded to this one exact synthetic shadow tombstone and one observed carrier restart.

The inner Phase-7D manifest's durable_tombstone_written=false describes its earlier synthetic in-memory contract. The distinct outer Phase-7E table row has now been durably written and survived restart. This does **not** implement destructive pruning, production restore or general disaster recovery. All destructive gates remain false.


## Phase 7F — isolated reconstruction from the exact durable Phase-7E shadow

2026-09-24 source implementation. Phase 7E's bounded post-restart persistence proof is canonized at
GaiaOS/MemoryOS/PW-PRESERVE-2026-09-24-GALAXY-PHASE7E-LIVE-RESTART-PERSISTENCE-PROVEN.md.

Purpose: reconstitute **the exact saved Phase-7D synthetic evidence bundle from the one real Phase-7E shadow table row into an unattached SQLite `:memory:` connection**, read each evidence category back, compare structural equality and SHA-256 digest, then discard the isolated database.

Source:
- module: api/galaxy_phase7_isolated_restore.py
- authenticated GET-only review: /galaxy/pruning/phase7-isolated-restore-review
- test: tests/test_galaxy_phase7.py
- CI: .github/workflows/galaxy-phase7-pruning-research.yml

Runtime procedure:
1. SELECT the counts of seven protected MemoryOS evidence tables, the isolated shadow tombstone table and runtime receipts. Do not modify them.
2. Read and revalidate the exact Phase-7E durable shadow row and its original successful write receipt. Require the exact Phase-7D manifest, authority NAOMI and known SHA-256; refuse missing or corrupted data.
3. Construct a **new, unattached, disposable SQLite RAM database** containing one isolated manifest row and isolated evidence rows for record, lifecycle, governing state, relations, synthesis dependencies, lifecycle events and receipts.
4. Reconstruct the seven evidence categories exclusively from this isolated RAM database. Compare exact structural equality, row counts and the reconstructed digest to the shadow manifest.
5. Close the RAM connection. SELECT source counts and the original shadow receipt again, fail closed on any mismatch.
6. Return either PASS_ISOLATED_RESTORE or HOLD. Never elevate a HOLD to restoration proof.

Non-authority:
- no new Phase-7E shadow write;
- no MemoryOS source-record, relation, lifecycle, gravity, synthesis or receipt mutation;
- no materialization back into production MemoryOS;
- no physical deletion;
- no production retrieval or attenuation changes;
- no change to tombstone_protocol_implemented, destructive_restore_proven, or destructive_eligibility.

**Proof boundary:** even live PASS establishes only that this single synthetic research bundle can be read from the persisted shadow row and reconstructed in isolated ephemeral RAM. It does not prove restoration to operational MemoryOS, deletability of any real record, full disaster recovery, or a general production protocol.

Source/CI is separately gated. Live deployment and authenticated GET readback must be observed before Phase-7F is closed.


### Phase 7F source and regression gates

On PR #17 head f234ccea807ea69b48a2f1f6b0a3c2628b0b2f9d, GitHub Actions observed:
- GALAXY Phase 7A-7F source gate run 36037574012: SUCCESS; compile, isolated-restore test suite and formatting guard passed.
- GALAXY Phase 6 regression run 36037574299: SUCCESS; compile, reversible lifecycle tests and formatting guard passed.

The source gate proves test behavior only. Live Phase 7F remains pending Render redeployment and a fresh authenticated read-only GET /galaxy/pruning/phase7-isolated-restore-review. Do not mark it live from CI.
