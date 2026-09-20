# GALAXY v1 Blueprint

TITLE: Gravitational Adaptive Learning Archive & conteXt sYstem
AUTHORITY: NAOMI / LIGEIA
OWNER: GaiaOS / MemoryOS + BrainOS
STATUS: PHASE 1 LIVE-PROVEN / PHASE 2 SOURCE-IMPLEMENTED AWAITING RUNTIME CANARY

GALAXY models durable memory as a revisable relational graph rather than an append-only list. Existing MemoryOS records remain evidence-bearing atoms. GALAXY adds typed relationships, explainable influence scores called gravity, lifecycle states, revision/supersession, consolidation, retrieval weighting, and reversible attenuation.

## Boundaries
- NAOMI retains final authority.
- Existing records are not overwritten because newer ideas exist.
- Relation strength and gravity are separate.
- Historical truth and current retrieval priority are separate.
- Every mutation has provenance and a receipt.
- Initial versions perform no physical record removal.
- Retrieval influence grants no authority.

## Data structures
memory_relations: edge_id, source_record_id, target_record_id, relation_type, strength, status, evidence_json, classifier, timestamps, authority.
Initial relations: REINFORCES, EXTENDS, EXPLAINS, EXEMPLIFIES, CONTRADICTS, REVISES, SUPERSEDES, DERIVED_FROM, CONTEXT_FOR, ASSOCIATED_WITH.

memory_gravity: record_id, gravity_score, score_version, components_json, reason_json, calculated_at, previous_score.
Candidate components: explicit Naomi importance, recurrence, graph centrality, demonstrated retrieval usefulness, revision significance, durable relevance, source confidence, supersession, redundancy, and staleness.

memory_lifecycle states: ACTIVE, BACKGROUND, ARCHIVED, COMPRESSED, PRUNABLE. Transitions remain reversible during the initial program.

memory_syntheses creates a new synthesis record linked to source record IDs. It never silently rewrites its sources.

## Ingest
EXPERIENCE → //PW:PRESERVE// → CANDIDATE → NAOMI APPROVAL / MEMSAV → VERIFIED DURABLE RECORD → CORRESPONDENCE SEARCH → RELATION PROPOSALS → EDGE VERIFICATION → GRAVITY CALCULATION → LIFECYCLE/ORBIT PLACEMENT → RETRIEVAL.

The already-proven PW:PRESERVE/MEMSAV pathway remains the durability gate.

## Correspondence
For each newly verified record, retrieve a bounded candidate neighborhood using semantic/lexical similarity and existing graph neighbors. Propose typed edges and strengths, preserve ambiguity and contradiction, dedupe equivalent edges, store accepted edges with receipts, and recompute only the affected neighborhood.

## Gravity
GRAVITY means present retrieval influence.
RELATION STRENGTH means degree/confidence of connection between records.
A low-gravity satellite may have a strong EXPLAINS edge to a major memory and remain valuable through that role. Gravity may change. New correspondence can reactivate old records.

## Revision
When B revises A, retain A and add B REVISES A. If supported, separately add B SUPERSEDES A. Raise B's current retrieval influence and lower A's ordinary-current-context influence while preserving A for chronology, causality, provenance, and rollback. Newer never automatically means truer.

## Retrieval
Return a bounded constellation: focal relevant/high-gravity records, only useful satellites, active contradictions/revisions, and material provenance. Archived memories require stronger relevance or graph activation to surface. Retrieved context has no independent authority.

## Consolidation
When records form a stable cluster, GALAXY may propose a synthesis parent citing its source record IDs. The synthesis may become the default retrieval target while originals remain provenance satellites.

## Reversible forgetting
Initial forgetting means attenuation, not erasure:
ACTIVE → BACKGROUND → ARCHIVED → COMPRESSED → PRUNABLE.
PRUNABLE means eligible for later review. Physical removal is outside v1 and requires a separately designed and proven authority pathway.

## Failure modes to test
Popularity feedback loops, recency bias, old-memory starvation, false relation cascades, contradiction erasure, score inflation, generic-language graph hubs, recursive synthesis without provenance, and unsupported model-generated memories.

## Review
Event-driven review updates the bounded neighborhood of a new verified record.
Periodic review proposes stale-gravity corrections, unresolved contradiction links, supersession, synthesis, and archive eligibility. It does not silently rewrite history.

## Proposed POWER WORDS
Existing: CANDIPULL, MEMSAV, //PW:PRESERVE//, Save to E-LANE.
Proposed, not yet implemented:
//PW:ORBIT// relation inspection/proposal.
//PW:GRAVITY// explain gravity and components.
//PW:REVISE// propose revision/supersession.
//PW:CONSOLIDATE// propose provenance-backed synthesis.
//PW:ARCHIVE// propose lifecycle attenuation.
//PW:REACTIVATE// restore retrieval priority.
//PW:PRUNE// reserved for a future separately proven authority pathway.

## Build sequence
0. Preserve the current PW:PRESERVE/MEMSAV and Turso continuity proof baseline.
1. Add graph tables and read-only inspection. No retrieval effect.
2. Calculate gravity in shadow mode. No retrieval effect.
3. Test weighted retrieval against current retrieval with controls.
4. Add reversible revision/supersession behavior.
5. Add provenance-backed synthesis.
6. Add reversible BACKGROUND/ARCHIVED/COMPRESSED lifecycle behavior and reactivation.
7. Research finite-storage pruning only after long observation and separate proof.

## Proof ladder
SOURCE IMPLEMENTED → DEPLOYED → OBSERVED RUNTIME → RECEIPT → READBACK → BEHAVIORAL TEST.

The key future behavioral experiment is not merely whether old text can be fetched. Test whether authenticated retrieved history changes a subsequent bounded decision/output in the predicted way compared with a control, while provenance and authority remain intact.

## VASKON critique
VERA: separate current truth from historical truth.
ANVIL: reversible first, explain scores, receipts throughout.
SELENE: let memories become quiet without flattening history.
ORIN: permit orbital migration, reactivation, and emergent parent concepts.
KESTREL: incremental neighborhood updates and phased rollout.
NIMUE: preserve contradiction and negative evidence.

## Success condition
GALAXY succeeds when GaiaOS can preserve selected experience, relate it to prior experience, revise current models without erasing history, retrieve a small useful constellation rather than a dump, and allow old material to become quieter or newly relevant under explicit authority and auditable proof boundaries.


## Implementation checkpoint 2026-09-18

Phase 1 source implementation has begun.

Implemented in source:
- Turso/SQLite-compatible schema tables for memory_relations, memory_gravity, memory_lifecycle, and memory_syntheses.
- Typed relation vocabulary and lifecycle constants.
- Read-only GALAXY status and per-record neighborhood inspection.
- Non-authoritative relation proposal primitive plus explicit Naomi verification primitive. Neither changes retrieval.
- //PW:ORBIT// read-only runtime command.
- //PW:GRAVITY// shadow inspection command. Phase 1 intentionally does not fabricate gravity scores.
- /galaxy/status and /galaxy/record/{record_id} browser-authenticated inspection endpoints.

Not yet claimed:
- deployment of this checkpoint;
- successful Turso schema initialization;
- live relation proposal/verification;
- gravity calculation quality;
- retrieval weighting;
- revision/supersession behavior;
- synthesis/consolidation;
- lifecycle attenuation;
- pruning.

Proof state: SOURCE_IMPLEMENTED_AWAITING_DEPLOYMENT_AND_RUNTIME_TEST.


## Resume checkpoint 2026-09-19 00:16 EDT

PURPOSE: Clean future recall of GALAXY architecture, implementation order, observed proof state, and exact next gate.

### Architecture to preserve

GALAXY = Gravitational Adaptive Learning Archive & conteXt sYstem.

Memory remains durable evidence-bearing records. GALAXY layers a relational graph over those records:
1. typed relationships between records;
2. relation strength separate from gravity;
3. gravity as explainable present retrieval influence;
4. revision/supersession without historical erasure;
5. provenance-backed synthesis/consolidation;
6. reversible lifecycle attenuation before any destructive pruning;
7. orbital migration/reactivation when later evidence makes quiet memories relevant again.

Lifecycle target:
ACTIVE → BACKGROUND → ARCHIVED → COMPRESSED → PRUNABLE.
PRUNABLE is review eligibility, not permission to delete.

### Implementation sequence

PHASE 0: Preserve existing MemoryOS/Turso and PW:PRESERVE/MEMSAV proof baseline. DONE for previously tested paths.

PHASE 1: Graph foundation with no retrieval effect.
- add memory_relations, memory_gravity, memory_lifecycle, memory_syntheses;
- expose read-only status and record-neighborhood inspection;
- relation proposal must remain non-authoritative;
- relation verification requires explicit Naomi approval;
- ORBIT inspection performs no writes;
- GRAVITY remains shadow/no fabricated score.
SOURCE IMPLEMENTED and DEPLOYED. Runtime structure and ORBIT read-only inspection OBSERVED for tested path.

NEXT PHASE-1 GATE:
- create two controlled durable MemoryOS records;
- propose one typed relationship between them;
- inspect proposal;
- explicitly approve/verify edge as NAOMI;
- ORBIT the record again;
- verify edge readback;
- verify retrieval remains unchanged;
- retain receipt/proof boundary.

PHASE 2: Gravity shadow mode.
- define versioned explainable scoring components;
- calculate scores without affecting retrieval;
- inspect/calibrate against observed usefulness;
- prevent feedback loops, recency domination, and arbitrary permanent weights.

PHASE 3: Weighted retrieval experiment.
- combine semantic relevance, gravity, graph path relevance, lifecycle state, and provenance/source confidence in a bounded test;
- compare against existing retrieval control;
- preserve contradiction and exploration slots;
- prove retrieved history changes a subsequent bounded output in the predicted way without granting retrieved context authority.

PHASE 4: Revision/supersession.
- B REVISES A and, only when warranted, B SUPERSEDES A;
- retain A as historical truth/provenance;
- lower A for ordinary current-state retrieval while preserving historical retrieval;
- newer never automatically means truer.

PHASE 5: Synthesis/consolidation.
- repeated satellites may produce a proposed parent concept;
- synthesis is a new record with explicit source IDs;
- originals remain provenance satellites;
- no silent rewriting.

PHASE 6: Reversible forgetting.
- enable BACKGROUND/ARCHIVED/COMPRESSED and reactivation;
- forgetting initially means reduced retrieval priority, not destruction;
- future evidence can increase an old record's gravity again.

PHASE 7: Pruning research only.
- no physical deletion until dependency checks, tombstones, rollback, provenance sufficiency, destructive canaries, and explicit Naomi policy are separately proven.

### Observed live proof state

Deployed source checkpoint: commit 2a80503dc4e8f2e1a5e70a2a0c0d0e011a20153f.
Render service observed Live after deployment.

Live /galaxy/status observed:
- schema gaiaos.galaxy.runtime.v1
- phase PHASE_1_GRAPH_FOUNDATION
- mode SHADOW_NO_RETRIEVAL_EFFECT
- storage backend turso_libsql
- remote_configured true
- relations 0
- gravity_scores 0
- lifecycle_rows 0
- syntheses 0
- retrieval_weighting_enabled false
- physical_pruning_enabled false

Live PW:ORBIT tested against existing durable record:
MEM-3ef2a79223c54def85800a563c62cf78

Observed:
- status OBSERVED
- correct durable MemoryOS record returned
- relations []
- gravity null
- lifecycle null
- retrieval_effect NONE_SHADOW_MODE
- writes_performed []

Bounded conclusion: GALAXY Phase 1 structures are live on the configured Turso/libSQL runtime, and read-only ORBIT integration was observed for this tested record without writes or retrieval influence. Relation quality, gravity, weighted retrieval, revision, consolidation, forgetting, and pruning remain unproven.

### Resume instruction

On return, do not rebuild or repeat the already observed foundation tests unless evidence requires it. Resume at the NEXT PHASE-1 GATE: controlled two-memory relation proposal → Naomi verification → edge readback through ORBIT → confirm retrieval still unchanged.

### Phase-1 relation canary surface checkpoint 2026-09-19

Source commit: 2b9a9f5ef3eb709eff3b96b596717962f1c4eae5.

SOURCE IMPLEMENTED / DEPLOYMENT NOT YET PROVEN:
- Browser Chat now recognizes `GALAXY PROPOSE <source_record_id> <relation_type> <target_record_id> <strength> [evidence note]`.
- Proposal writes only a `PROPOSED` shadow relation through the existing `galaxy_propose_relation` primitive.
- The proposal captures the ordinary MemoryOS retrieval record order for the controlled source record before edge verification.
- Browser Chat now recognizes `GALAXY VERIFY <edge_id>`.
- Verification requires that explicit command, invokes Naomi-authorized `galaxy_verify_relation`, reads both endpoint orbits back, reruns ordinary MemoryOS retrieval, and reports whether the record order remained unchanged.
- Neither command enables retrieval weighting.
- These command surfaces do not prove deployment or successful runtime execution until observed on the live carrier.

NEXT GATE remains:
two controlled durable memories → GALAXY PROPOSE → inspect PROPOSED edge → explicit GALAXY VERIFY → ORBIT/readback → retrieval comparison → preserve receipt.


### Two-memory relation canary harness 2026-09-19

Source implementation commits:
- 1e7faabd3da47ce5ef5581fea61e13a7dbcf9a9a — staged two-memory canary flow.
- d104c4e79a633ad41e7d10c0d047e969b8e6d61d — corrected GALAXY PROPOSE / GALAXY VERIFY command routing.

Browser Chat command flow:
1. `GALAXY CANARY START`
   - creates one bounded canary session;
   - creates candidate A and candidate B only;
   - performs no durable memory write;
   - performs no relation write.
2. `GALAXY CANARY APPROVE`
   - requires the two latest canary candidates to belong to the same session;
   - explicitly promotes both through the canonical Naomi-authorized MemoryOS path;
   - requires both readbacks to reach VERIFIED;
   - proposes `B CONTEXT_FOR A` at strength 1.0;
   - captures ordinary MemoryOS retrieval order before edge verification;
   - leaves the relation at PROPOSED with zero retrieval effect.
3. `GALAXY VERIFY <edge_id>`
   - separately verifies the proposed edge under Naomi authority;
   - reads both endpoint ORBIT neighborhoods back;
   - reruns ordinary MemoryOS retrieval;
   - reports whether retrieval record order remained unchanged;
   - retrieval weighting remains disabled.

Proof boundary: SOURCE IMPLEMENTED. Deployment and runtime success must still be observed after the relevant commit is deployed.

### Phase-1 live relation canary PASS 2026-09-20

OBSERVED LIVE RESULT:

- Controlled durable endpoint B: `MEM-afc1f8f71e83451dbd14a46fa3229d8d`
- Controlled durable endpoint A: `MEM-295d635c8a2643fdbce3629370120303`
- Verified edge: `EDGE-bf3ab5952c4e41b1bd3cad5019bd676c`
- Relation: `B CONTEXT_FOR A`
- Strength: `1.0`
- Classifier: `GALAXY_CONTROLLED_CANARY_V1`
- Authority after verification: `NAOMI`
- Edge created: `2026-09-20T01:04:08.338834+00:00`
- Edge verified: `2026-09-20T01:26:40.200674+00:00`
- Verification readback returned `idempotent: true`, proving the earlier long-running request had already completed the verification write before the later readback request.
- Both source and target ORBIT readbacks returned the same verified relation.
- `gravity: null`
- `lifecycle: null`
- `retrieval_effect: NONE_SHADOW_MODE`
- Pre-verification and post-verification ordinary MemoryOS retrieval record IDs were identical.
- `unchanged: true`
- `retrieval_weighting_enabled: false`

Observed retrieval order before and after:

`MEM-afc1f8f71e83451dbd14a46fa3229d8d`
→ `MEM-295d635c8a2643fdbce3629370120303`
→ `MEM-17ff585910524bfe98a68f2c386fafbc`
→ `MEM-c05a2642dc1a4cdf8ba3f1568b037bcf`
→ `MEM-6fd682a5e64f4e5a94c333a4bc3b5082`

PHASE-1 CONCLUSION:

`PROPOSED → NAOMI VERIFIED → ORBIT READBACK → RETRIEVAL UNCHANGED` is now observed live on the deployed carrier.

This closes the Phase-1 graph-foundation gate for the controlled two-memory relation path. It does not prove automatic relation classification quality, gravity quality, weighted retrieval, synthesis, lifecycle migration, forgetting, or pruning.

NEXT PHASE:
`PHASE_2_GRAVITY_SHADOW_SCORING`

Phase 2 must begin with explainable shadow-only gravity calculation. Scores must remain non-authoritative and must not affect ordinary retrieval until a separately observed later gate enables weighted retrieval.


## Phase-2 shadow gravity implementation checkpoint 2026-09-20

SOURCE IMPLEMENTED. LIVE RUNTIME NOT YET CLAIMED.

Phase 2 keeps gravity strictly in shadow mode. Stored gravity rows are observable metadata only and are not consulted by ordinary MemoryOS retrieval.

### Shadow score v1

Score version: `galaxy.gravity.shadow.v1`

The first score is intentionally conservative and evidence-limited:

- durable active state: weight 0.25
- verified graph degree: weight 0.25, normalized to a maximum at four verified incident edges
- mean verified relation strength: weight 0.20
- Naomi provenance confidence: weight 0.15
- revision significance from VERIFIED CONTRADICTS / REVISES / SUPERSEDES edges: weight 0.10
- explicit Naomi importance: weight 0.05, fixed at 0.0 until an explicit importance signal is separately defined

The score is bounded to observable current facts. It does not recursively consume stored gravity.

Explicitly omitted from shadow v1:
- recency, to prevent uncalibrated recency domination;
- observed retrieval usefulness, until Phase 3 produces behavioral evidence;
- redundancy, until correspondence quality is separately tested;
- staleness, until lifecycle attenuation exists.

Gravity is not truth, authority, identity, or permission.

### Runtime primitives added

- `galaxy_gravity(record_id)` reads a stored shadow score.
- `galaxy_gravity_preview(record_id)` calculates the explainable score without writing.
- `galaxy_calculate_gravity(record_id, authority="NAOMI", approved=True)` stores the shadow row and writes a receipt.
- identical recalculation is idempotent and performs no new mutation.
- `PW:GRAVITY` now exposes stored score plus live preview without silently writing.

### Controlled Phase-2 canary

Direct browser path:

1. `/galaxy/gravity/canary/preview`
   - resolves the newest VERIFIED `GALAXY_CONTROLLED_CANARY_V1` edge from the proven Phase-1 path;
   - previews both endpoint scores;
   - performs no writes;
   - keeps retrieval weighting disabled.

2. `/galaxy/gravity/canary/run?edge_id=<EDGE-ID>`
   - requires the edge to remain VERIFIED and controlled;
   - captures ordinary MemoryOS retrieval order before scoring;
   - stores explainable shadow gravity for both endpoints under explicit Naomi authority;
   - reads both ORBITs back;
   - captures ordinary retrieval order after scoring;
   - reports whether order is unchanged;
   - reports anti-feedback, recency-off, and pruning-off guardrails.

3. `/galaxy/gravity/<record_id>`
   - read-only stored/preview inspection.

### Phase-2 proof gate

Do not claim Phase 2 runtime success until the deployed carrier visibly demonstrates all of the following:

- preview returns explainable component weights and contributions;
- preview performs zero writes;
- run stores both gravity rows with `galaxy.gravity.shadow.v1`;
- receipts/readback are present for actual writes;
- ORBIT exposes the stored gravity rows;
- before/after ordinary retrieval record IDs are identical;
- `retrieval_weighting_enabled == false`;
- repeated canary execution is idempotent for unchanged inputs.

Only after this gate passes may Phase 2 proceed to calibration across a broader bounded sample. Phase 3 weighted retrieval remains prohibited until separately designed, deployed, and behaviorally tested.


### Phase-2 live shadow-gravity canary FIRST PASS 2026-09-20

OBSERVED LIVE RESULT:

- Status: `SHADOW_GRAVITY_CALCULATED`
- Phase: `PHASE_2_GRAVITY_SHADOW`
- Controlled edge: `EDGE-bf3ab5952c4e41b1bd3cad5019bd676c`
- Source record: `MEM-afc1f8f71e83451dbd14a46fa3229d8d`
- Target record: `MEM-295d635c8a2643fdbce3629370120303`
- Source score: `0.6625`
- Target score: `0.6625`
- Score version: `galaxy.gravity.shadow.v1`
- Both first-write gravity receipts returned `SUCCESS`.
- Source receipt: `MEMREC-9c135747b9674021a5740010a57c9b47`
- Target receipt: `MEMREC-1cf1eaa5c5ce4f87b66256e2686cc0b2`
- Both ORBIT readbacks exposed the stored gravity rows.
- Ordinary MemoryOS retrieval order before and after scoring was identical.
- `unchanged: true`
- `retrieval_weighting_enabled: false`
- `gravity_is_authority: false`
- `stored_gravity_feeds_its_own_score: false`
- `recency_component_enabled: false`
- `physical_pruning_enabled: false`

Observed retrieval order remained:

`MEM-afc1f8f71e83451dbd14a46fa3229d8d`
→ `MEM-295d635c8a2643fdbce3629370120303`
→ `MEM-17ff585910524bfe98a68f2c386fafbc`
→ `MEM-c05a2642dc1a4cdf8ba3f1568b037bcf`
→ `MEM-6fd682a5e64f4e5a94c333a4bc3b5082`

INTERPRETATION:

The first live Phase-2 write/readback/retrieval-control path passed. Shadow gravity can be calculated, stored, receipted, and read back without changing ordinary retrieval behavior.

PHASE-2 REMAINING GATE:

Repeat the exact same controlled canary with unchanged inputs. It must return the existing identical scores idempotently, perform no new gravity mutation, and preserve ordinary retrieval order. Only after that rerun is observed should the controlled Phase-2 canary be marked fully PASS.

Phase 3 weighted retrieval remains disabled and unauthorized.


### Phase-2 controlled shadow-gravity canary PASS 2026-09-20

OBSERVED LIVE IDEMPOTENCY RESULT:

- Controlled edge remained `EDGE-bf3ab5952c4e41b1bd3cad5019bd676c`.
- Source score remained `0.6625`.
- Target score remained `0.6625`.
- Both score version values remained `galaxy.gravity.shadow.v1`.
- Both recalculations returned `idempotent: true`.
- Both recalculations returned `receipt: null`.
- Authority boundary reported that no new mutation was performed for identical unchanged shadow scores.
- Source and target ORBIT readbacks still exposed the same stored gravity rows.
- Ordinary MemoryOS retrieval order before and after the idempotent rerun remained identical.
- `unchanged: true`
- `retrieval_weighting_enabled: false`
- `gravity_is_authority: false`
- `stored_gravity_feeds_its_own_score: false`
- `recency_component_enabled: false`
- `physical_pruning_enabled: false`

PHASE-2 CONTROLLED CANARY CONCLUSION:

`PREVIEW NO-WRITE → FIRST SHADOW SCORE WRITE + RECEIPTS → ORBIT READBACK → RETRIEVAL UNCHANGED → IDENTICAL RERUN IDEMPOTENT / NO NEW RECEIPTS → RETRIEVAL STILL UNCHANGED`

is now observed live on the deployed carrier for the controlled two-memory pair.

This closes the controlled Phase-2 shadow-gravity canary gate.

NEXT PHASE-2 WORK:
broader bounded calibration across records with meaningfully different graph structures and evidence profiles. This is still shadow-only. Phase 3 weighted retrieval remains disabled and unauthorized until calibration is reviewed and a separate Phase-3 proof harness is designed.


### Phase-2 broader calibration harness checkpoint 2026-09-20

SOURCE IMPLEMENTED. DEPLOYMENT / LIVE RUNTIME NOT YET CLAIMED.

The next Phase-2 gate expands beyond the symmetric two-memory pair into a five-record controlled constellation with deliberately different graph structures.

Controlled roles:

- CORE
- SATELLITE
- REINFORCER
- REVISION
- ISOLATED

Proposed graph:

- SATELLITE `CONTEXT_FOR` CORE at strength `0.40`
- REINFORCER `REINFORCES` CORE at strength `0.80`
- REVISION `REVISES` CORE at strength `0.90`
- REVISION `CONTRADICTS` REINFORCER at strength `0.70`
- ISOLATED has no GALAXY edge

This produces controlled variation in verified graph degree, mean relation strength, and revision-significance while holding ACTIVE state, Naomi provenance, explicit importance, recency, lifecycle, and retrieval usefulness constant.

Browser proof flow:

1. `/galaxy/gravity/calibration/start`
   - creates five candidates only;
   - performs no durable MemoryOS promotion;
   - performs no relation write;
   - performs no gravity write.

2. `/galaxy/gravity/calibration/approve?session_id=<SESSION>`
   - promotes the five controlled candidates under explicit Naomi authority;
   - proposes the four calibration relations;
   - leaves any new relation at PROPOSED;
   - performs no gravity write.

3. `/galaxy/gravity/calibration/verify?session_id=<SESSION>`
   - explicitly verifies the four controlled edges;
   - reads the edge set back;
   - performs no gravity write.

4. `/galaxy/gravity/calibration/preview?session_id=<SESSION>`
   - calculates five shadow previews;
   - performs no gravity write;
   - reports score ordering, spread, unique-score count, and which components actually vary;
   - runs synthetic discrimination checks without claiming real-world weight quality.

5. `/galaxy/gravity/calibration/run?session_id=<SESSION>`
   - captures ordinary retrieval before scoring for all five records;
   - stores/re-reads the five shadow scores;
   - captures ordinary retrieval after scoring;
   - reports per-record retrieval invariance;
   - reports receipt count and idempotent count;
   - reopening the same exact URL is the idempotency check.

Guardrails remain unchanged:

- gravity is not authority;
- stored gravity never feeds its own next score;
- recency is disabled in shadow v1;
- lifecycle attenuation is disabled;
- ordinary retrieval remains unweighted;
- physical pruning remains disabled.

Calibration objective:

The bounded synthetic constellation should produce multiple distinct scores and an explainable ordering caused by graph structure, relation strength, and revision significance. This proves formula discrimination, not real-world usefulness.

Phase 3 remains prohibited until this broader Phase-2 calibration is observed live, reviewed, and the remaining real-memory calibration limits are explicitly documented.


### Phase-2 broader calibration live START gate 2026-09-20

OBSERVED LIVE RESULT:

- Status: `CALIBRATION_CANDIDATES_READY`
- Phase: `PHASE_2_GRAVITY_SHADOW`
- Token: `1d79c239f31f`
- Session: `SESSION-3814cd13ab0d48779fd108c4809fabc1`
- Five controlled roles created as candidates: CORE, SATELLITE, REINFORCER, REVISION, ISOLATED.
- All five remain `CANDIDATE`.
- `durable_memory_writes_performed: []`
- `relation_writes_performed: []`
- `gravity_writes_performed: []`
- `retrieval_weighting_enabled: false`

START-GATE CONCLUSION:

The broader calibration harness is live and preserves the candidate-only safety boundary. No durable MemoryOS promotion, relation write, relation verification, or gravity write occurred during START.

NEXT LIVE GATE:
explicit approval of the five controlled memories and proposal of exactly four calibration relations, which must remain PROPOSED until the subsequent separate verification step.
