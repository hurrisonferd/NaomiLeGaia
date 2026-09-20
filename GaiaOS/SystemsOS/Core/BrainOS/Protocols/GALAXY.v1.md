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


### Phase-2 broader calibration live APPROVAL/PROPOSAL gate 2026-09-20

OBSERVED LIVE RESULT:

- Status: `CALIBRATION_GRAPH_PROPOSED`
- Session: `SESSION-3814cd13ab0d48779fd108c4809fabc1`
- Five controlled candidates promoted to VERIFIED durable MemoryOS records with successful write receipts:
  - CORE: `MEM-00b3fbfd4d73404f97a95c238596ab94`
  - SATELLITE: `MEM-1d0092cb66f44996b74604670a853a21`
  - REINFORCER: `MEM-61f21fbb37f0419dbae2af6586d4ecc9`
  - REVISION: `MEM-ffc0c2af5cfa48d7aee7332a290a3d0e`
  - ISOLATED: `MEM-1e8f6987d2b34f3786db585c36bf9bf3`
- Four calibration relations were proposed:
  - SATELLITE `CONTEXT_FOR` CORE at 0.40
  - REINFORCER `REINFORCES` CORE at 0.80
  - REVISION `REVISES` CORE at 0.90
  - REVISION `CONTRADICTS` REINFORCER at 0.70
- All four relation statuses were `PROPOSED`.
- All four relation authorities were `NONE`.
- `verified_edge_count: 0`
- `retrieval_weighting_enabled: false`
- No gravity score was written by this step.

APPROVAL/PROPOSAL CONCLUSION:

The live broader-calibration approval gate preserved the intended separation:
`DURABLE MEMORY APPROVAL != RELATION VERIFICATION != GRAVITY SCORING`.

NEXT LIVE GATE:
explicit Naomi-authorized verification of exactly these four controlled calibration edges, followed by readback confirming all four are VERIFIED while gravity remains unwritten and retrieval weighting remains disabled.


### Phase-2 broader calibration live GRAPH VERIFICATION gate 2026-09-20

OBSERVED LIVE RESULT:

- Status: `CALIBRATION_GRAPH_VERIFIED`
- Session: `SESSION-3814cd13ab0d48779fd108c4809fabc1`
- Exactly four controlled calibration edges were verified under `NAOMI` authority.
- Verified edges:
  - `EDGE-f7be805051934c218089c2f818d8caee`: SATELLITE `CONTEXT_FOR` CORE, strength `0.40`
  - `EDGE-72a2818f91034db5b929f36abb230160`: REINFORCER `REINFORCES` CORE, strength `0.80`
  - `EDGE-324a405c6e534400a6f594c987e6ab4f`: REVISION `REVISES` CORE, strength `0.90`
  - `EDGE-72a03a65017c46efa0d982c42be3f6e8`: REVISION `CONTRADICTS` REINFORCER, strength `0.70`
- Each verification returned a successful `GALAXY_VERIFY_RELATION` receipt.
- Edge readback showed all four as `VERIFIED` with authority `NAOMI`.
- `all_four_edges_verified: true`
- `gravity_writes_performed: []`
- `retrieval_weighting_enabled: false`

GRAPH-VERIFICATION CONCLUSION:

The broader calibration graph is now live and verified without writing gravity. The intended separation remains intact:
`RELATION VERIFICATION != GRAVITY CALCULATION != RETRIEVAL WEIGHTING`.

NEXT LIVE GATE:
read-only broader shadow-gravity preview across CORE / SATELLITE / REINFORCER / REVISION / ISOLATED. The preview must perform zero gravity writes, expose component variation, produce multiple distinct scores, and report the synthetic discrimination checks before any score is persisted.


### Phase-2 broader calibration live PREVIEW gate 2026-09-20

OBSERVED LIVE RESULT:

- Status: `BROADER_SHADOW_PREVIEW`
- Session: `SESSION-3814cd13ab0d48779fd108c4809fabc1`
- Gravity writes performed: `[]`
- Retrieval weighting enabled: `false`

Observed shadow scores:
- REVISION: `0.785`
- CORE: `0.7775`
- REINFORCER: `0.725`
- SATELLITE: `0.5425`
- ISOLATED: `0.4`

Observed score characteristics:
- `unique_score_count: 5`
- `score_spread: 0.385`
- durable_active remained constant across all five records
- provenance_confidence remained constant across all five records
- explicit_importance remained constant at 0.0 across all five records
- revision_significance varied across the constellation
- verified_graph_degree varied across the constellation
- verified_relation_strength varied across the constellation

Synthetic discrimination checks all passed:
- ISOLATED < SATELLITE
- SATELLITE < REINFORCER
- REINFORCER < CORE
- CORE < REVISION
- `all_synthetic_discrimination_checks_pass: true`

PREVIEW-GATE CONCLUSION:

The shadow-v1 formula discriminated five deliberately different graph/evidence structures while fixed components remained fixed. This is evidence that the formula is structurally responsive and explainable under the controlled synthetic calibration.

This does NOT prove that the current weights predict real-world usefulness, memory salience, or retrieval quality.

NEXT LIVE GATE:
persist the five shadow scores and run before/after ordinary retrieval controls for all five records. Required observations:
- five stored/read-back shadow scores matching preview values;
- successful receipts for first writes;
- all five ordinary retrieval orders unchanged;
- retrieval weighting remains disabled;
- ORBIT readback exposes stored gravity;
- reopening the exact same run URL must then produce five idempotent results and no new receipts.


### Phase-2 broader calibration live FIRST WRITE/RETRIEVAL gate 2026-09-20

OBSERVED LIVE RESULT:

- Status: `BROADER_SHADOW_CALIBRATION_RAN`
- Session: `SESSION-3814cd13ab0d48779fd108c4809fabc1`
- Stored scores matched preview:
  - REVISION: `0.785`
  - CORE: `0.7775`
  - REINFORCER: `0.725`
  - SATELLITE: `0.5425`
  - ISOLATED: `0.4`
- Five first-write `GALAXY_SHADOW_GRAVITY` receipts returned SUCCESS.
- ORBIT readback exposed stored gravity for the controlled constellation.
- `all_retrieval_orders_unchanged: true`
- `new_receipt_count: 5`
- `idempotent_count: 0`
- `all_five_idempotent: false`
- `retrieval_weighting_enabled: false`
- Guardrails remained:
  - `gravity_is_authority: false`
  - `stored_gravity_feeds_its_own_score: false`
  - `recency_component_enabled: false`
  - `physical_pruning_enabled: false`

FIRST-WRITE/RETRIEVAL CONCLUSION:

The broader synthetic Phase-2 calibration can persist five distinct shadow scores and read them back without changing ordinary retrieval order.

REMAINING LIVE GATE:

Reopen the exact same calibration run URL with unchanged inputs. Expected:
- `new_receipt_count: 0`
- `idempotent_count: 5`
- `all_five_idempotent: true`
- all retrieval orders remain unchanged;
- retrieval weighting remains disabled.

Only after that observation should the bounded broader-calibration mechanics gate be marked fully PASS. Real-memory usefulness calibration remains separate.


### Phase-2 broader synthetic calibration PASS 2026-09-20

OBSERVED LIVE IDEMPOTENCY RESULT:

- Session: `SESSION-3814cd13ab0d48779fd108c4809fabc1`
- `all_retrieval_orders_unchanged: true`
- `new_receipt_count: 0`
- `idempotent_count: 5`
- `all_five_idempotent: true`
- `retrieval_weighting_enabled: false`
- Guardrails remained:
  - `gravity_is_authority: false`
  - `stored_gravity_feeds_its_own_score: false`
  - `recency_component_enabled: false`
  - `physical_pruning_enabled: false`

BROADER SYNTHETIC CALIBRATION CONCLUSION:

`CANDIDATE-ONLY START
→ DURABLE MEMORY APPROVAL
→ FOUR PROPOSED EDGES
→ SEPARATE NAOMI VERIFICATION
→ READ-ONLY FIVE-SCORE PREVIEW
→ FIRST FIVE SCORE WRITES + ORBIT READBACK
→ ALL RETRIEVAL ORDERS UNCHANGED
→ IDENTICAL RERUN IDEMPOTENT / ZERO NEW RECEIPTS
→ ALL RETRIEVAL ORDERS STILL UNCHANGED`

is now observed live.

The broader synthetic Phase-2 mechanics gate is PASS.

WHAT THIS PROVES:
- the shadow-v1 formula responds to deliberately varied graph structure;
- multiple component values and five distinct scores are produced explainably;
- scores can be stored and read back safely;
- identical recalculation is idempotent;
- Phase-2 gravity remains non-authoritative and has no retrieval effect.

WHAT THIS DOES NOT PROVE:
- that current component weights match real-world memory usefulness;
- that relation density should dominate salience;
- that revision significance is calibrated correctly for real memories;
- that recency, redundancy, usefulness, staleness, or lifecycle attenuation should remain absent;
- that Phase-3 weighted retrieval is ready.

NEXT PHASE-2 WORK:
bounded real-memory calibration in observation-only mode. Select existing durable records with naturally different relation profiles, preview current shadow-v1 scores without mutating their relations, compare explainability against Naomi review, and document mismatches before any Phase-3 design begins.


### Phase-2 real-memory shadow calibration harness checkpoint 2026-09-20

SOURCE IMPLEMENTED. LIVE RUNTIME OBSERVATION NOT YET CLAIMED.

A new read-only real-memory calibration surface is implemented at:

`/galaxy/gravity/real-calibration/preview`

Purpose:

Move Phase 2 beyond synthetic graph mechanics and inspect shadow-v1 against existing durable non-test MemoryOS records without altering those records, their relations, stored gravity, or retrieval.

Population boundary:

- scope must be `MemoryOS`;
- `record_type=TEST` is excluded;
- controlled GALAXY Phase-1/Phase-2 test sources are excluded;
- only VERIFIED relations whose source and target are both inside the eligible real-memory population are considered;
- no candidate, memory, relation, gravity, lifecycle, synthesis, or retrieval mutation occurs.

Bounded sampling:

- maximum sample size: 8;
- deterministic selection favors naturally distinct VERIFIED relation profiles;
- one newest representative per relation profile is selected first;
- remaining slots are filled with newest eligible records;
- graph profile dimensions include verified relation count, relation types, mean verified relation strength, revision-significance edge count, authority, and record status.

The preview reports:

- eligible real-memory population count;
- relation-bearing vs zero-relation real-memory counts;
- unique natural relation-profile count;
- bounded selected records with statements and provenance;
- current shadow-v1 preview for each selected record;
- any pre-existing stored shadow gravity row without modifying it;
- sample score spread and unique-score count;
- sample relation-count variation;
- calibration readiness:
  - `OBSERVABLE_GRAPH_DIVERSITY`, or
  - `GRAPH_COVERAGE_LIMITED`.

Important interpretation boundary:

If real memories lack naturally varied VERIFIED GALAXY relations, equal or near-equal scores are a graph-coverage finding. They must not be interpreted as evidence that shadow-v1 is well calibrated.

Naomi review questions are surfaced directly:

- Do higher scores correspond to memories Naomi considers more broadly useful or important?
- Is relation-rich but low-value material inflated by graph density?
- Is isolated but important material underweighted because graph coverage is sparse?
- Is revision/contradiction influence too strong or too weak?

No action button is exposed on this page intentionally. Observation and Naomi review precede any real-memory graph mutation or Phase-3 design.

Phase 3 remains disabled and unauthorized.


### Phase-2 real-memory live coverage finding 2026-09-20

OBSERVED LIVE RESULT:

- Status: `REAL_MEMORY_SHADOW_PREVIEW`
- Eligible non-test MemoryOS records: `0`
- Relation-bearing real-memory records: `0`
- Zero-relation real-memory records: `0`
- Unique natural relation profiles: `0`
- Selected sample count: `0`
- Calibration readiness: `GRAPH_COVERAGE_LIMITED`
- `writes_performed: []`
- `relations_mutated: []`
- `gravity_rows_mutated: []`
- `retrieval_weighting_enabled: false`

INTERPRETATION:

The current durable MemoryOS population contains no eligible non-test records under the real-memory calibration boundary. This is a coverage finding, not a score-quality result.

No claim is made that GaiaOS lacks real conversational material elsewhere in MemconOS. The next diagnostic must inspect existing non-test MemoryOS candidates and session-event material without promoting or mutating anything.

Phase 3 remains disabled and unauthorized.


### Phase-2 latent real-memory inventory harness checkpoint 2026-09-20

SOURCE IMPLEMENTED. LIVE RUNTIME OBSERVATION NOT YET CLAIMED.

Because the first real-memory preview observed zero eligible durable non-test MemoryOS records, Phase 2 now includes a read-only latent-material inventory:

`/galaxy/gravity/real-calibration/inventory`

The inventory inspects existing MemconOS state for:

- non-test MemoryOS candidates;
- pending non-test candidates awaiting Naomi review;
- non-test session events;
- session events not yet represented by a non-test MemoryOS candidate.

It returns one of three diagnostics:

- `LATENT_MEMORY_CANDIDATES_AVAILABLE`
- `UNREPRESENTED_SESSION_EVENTS_AVAILABLE`
- `NO_LATENT_REAL_MEMORY_MATERIAL_FOUND`

No automatic ingestion is allowed.

Guardrails:

- no candidate creation;
- no candidate promotion;
- no durable memory write;
- no relation proposal or verification;
- no gravity write;
- no retrieval effect.

Decision rule:

- if pending real candidates exist, surface them for explicit Naomi review before promotion;
- if only unrepresented real session events exist, build a separate candidate-creation review step before promotion;
- if neither exists, real-memory calibration pauses until real material enters MemconOS or Naomi explicitly supplies a source.

This prevents synthetic test data from being silently reclassified as real memory merely to satisfy calibration coverage.

Phase 3 remains disabled and unauthorized.


### Phase-2 latent real-memory inventory live result 2026-09-20

OBSERVED LIVE RESULT:

- Status: `REAL_MEMORY_LATENT_INVENTORY`
- Non-test MemoryOS candidate count: `0`
- Pending non-test candidate count: `0`
- Non-test session event count: `6`
- Session events without a non-test MemoryOS candidate: `6`
- Diagnostic: `UNREPRESENTED_SESSION_EVENTS_AVAILABLE`
- `writes_performed: []`
- `candidates_promoted: []`
- `relations_mutated: []`
- `gravity_rows_mutated: []`
- `retrieval_weighting_enabled: false`

Observed latent events consist of one browser-chat `CHAT_INTERACTION` about the first PW:PRESERVE command test and five `TEST_INPUT` MemoryOS lifecycle markers.

INTERPRETATION:

MemconOS contains latent session-event material, but no pending non-test MemoryOS candidates. The next safe step is not promotion. It is a read-only candidate-creation review surface that distinguishes clearly test-like events from potentially reviewable real interactions before any candidate row is created.

Phase 3 remains disabled and unauthorized.


### Phase-2 real-memory candidate-review harness checkpoint 2026-09-20

SOURCE IMPLEMENTED. LIVE RUNTIME OBSERVATION NOT YET CLAIMED.

A new two-step candidate-review surface is implemented:

1. `/galaxy/gravity/real-calibration/candidate-review`
   - read-only review of recent unrepresented session events;
   - structurally test-like events are explicitly held out;
   - candidate creation options are shown only for events that are not structurally test-classified;
   - performs zero writes.

2. `/galaxy/gravity/real-calibration/candidate-create?event_id=<EVENT>`
   - available only after an explicit Naomi click from the review page;
   - creates one non-durable `MemoryOS` candidate from the exact reviewed event;
   - refuses structurally test-like events;
   - returns existing candidate idempotently if that event is already represented;
   - performs no durable promotion;
   - performs no relation mutation;
   - performs no gravity write;
   - does not alter retrieval.

Structural test holds currently include:

- event types containing `TEST`;
- sources containing `test` or `canary`;
- controlled `galaxy-phase*` sources.

Statement-level test language is surfaced as a softer review flag rather than silently discarding a browser-chat interaction.

Candidate creation remains distinct from durable promotion:

`SESSION EVENT -> HUMAN REVIEW -> NON-DURABLE CANDIDATE != DURABLE MEMORY`

No promotion control is exposed by this harness. A durable promotion gate may be built only after Naomi inspects the exact candidate.

Phase 3 remains disabled and unauthorized.


### Phase-2 real-memory candidate-review live result 2026-09-20

OBSERVED LIVE RESULT:

- Status: `REAL_MEMORY_CANDIDATE_REVIEW`
- Reviewed latent events: `6`
- Structurally held test events: `5`
- Candidate-creation options: `1`
- The sole reviewable event was:
  - event `EVENT-78b3836d65674b00bbabff5ce0e05064`
  - source `browser-chat`
  - event type `CHAT_INTERACTION`
  - statement: `We are about to carry out the very first test of the PW:PRESERVE command function.`
  - soft flags: `STATEMENT_MENTIONS_TEST`, `PW_PRESERVE_CONTEXT`
- No candidates were created.
- No durable promotions occurred.
- No relations or gravity rows were mutated.
- Retrieval weighting remained disabled.

INTERPRETATION:

The structural classifier correctly held the five explicit lifecycle TEST_INPUT events, but the only remaining browser-chat event is itself test-context material and is not a useful real-memory calibration exemplar.

Therefore it should not be promoted merely to populate the real-memory graph. Candidate review needs a calibration-suitability distinction in addition to structural test detection.

Phase 3 remains disabled and unauthorized.


### Phase-2 calibration-suitability refinement 2026-09-20

SOURCE IMPLEMENTED. LIVE RUNTIME RECHECK NOT YET CLAIMED.

The live candidate-review gate revealed one browser-chat event that was structurally non-test but semantically still control-test material:

`We are about to carry out the very first test of the PW:PRESERVE command function.`

The review classifier now distinguishes three outcomes:

- `TEST_LIKE_HOLD`
  - structurally test-like by event type/source;
- `CALIBRATION_SUITABILITY_HOLD`
  - real interaction provenance, but content is itself control-test context unsuitable as a representative real-memory calibration exemplar;
- `NAOMI_REVIEW_REQUIRED`
  - not structurally test-like and not held by current calibration-suitability rules.

Current suitability rule:

`STATEMENT_MENTIONS_TEST + PW_PRESERVE_CONTEXT -> CONTROL_COMMAND_TEST_CONTEXT -> CALIBRATION_SUITABILITY_HOLD`

This does not claim such an interaction is unreal. It only prevents it from being used to manufacture real-memory calibration coverage.

Candidate creation remains blocked for both hold classes.

Phase 3 remains disabled and unauthorized.


### Phase-2 candidate-review live zero-option result 2026-09-20

OBSERVED LIVE RESULT:

- Status: `REAL_MEMORY_CANDIDATE_REVIEW`
- Reviewed events: `6`
- Candidate-creation options: `0`
- Held events: `6`
- Structural test holds: `5`
- Calibration-suitability holds: `1`
- The browser-chat PW:PRESERVE interaction correctly moved to `CALIBRATION_SUITABILITY_HOLD`.
- No candidates were created.
- No durable promotions occurred.
- No relations or gravity rows were mutated.
- Retrieval weighting remained disabled.

CONCLUSION:

The current MemconOS event history contains no suitable real-memory exemplar for Phase-2 calibration. This is a valid stop condition for passive discovery.

NEXT SAFE INGESTION STEP:

Provide an explicit Naomi-authored real-memory seed intake that creates non-durable MemoryOS candidates only. Seed intake must not auto-promote, auto-relate, write gravity, or alter retrieval. It exists to let Naomi deliberately supply representative semantic material rather than manufacture coverage from test artifacts.

Phase 3 remains disabled and unauthorized.


### Phase-2 explicit real-memory seed intake checkpoint 2026-09-20

SOURCE IMPLEMENTED. LIVE RUNTIME OBSERVATION NOT YET CLAIMED.

Because passive discovery found no suitable real-memory calibration exemplar, Phase 2 now exposes an explicit Naomi-authored seed intake:

`/galaxy/gravity/real-calibration/seed`

The form accepts:

- one bounded real-memory statement;
- one required `why_material` explanation;
- an optional subject.

Submission goes to:

`/galaxy/gravity/real-calibration/seed/create`

and creates:

- a new provenance-bearing MemconOS session;
- a `REAL_MEMORY_SEED_INPUT` event;
- one non-durable `MemoryOS` candidate owned by `NAOMI_REAL_MEMORY_SEED`.

Guardrails:

- candidate only;
- no durable promotion;
- no relation proposal or verification;
- no gravity write;
- no retrieval effect;
- no Phase-3 weighting.

This intake exists so calibration coverage can be supplied deliberately by Naomi rather than manufactured from test artifacts.

Durable promotion remains a separate future gate after exact candidate inspection.


### Phase-2 explicit real-memory seed live candidate result 2026-09-20

OBSERVED LIVE RESULT:

- Status: `REAL_MEMORY_SEED_CANDIDATE_CREATED`
- Phase: `PHASE_2_GRAVITY_SHADOW`
- Source: `galaxy-real-seed:0c9a49379d31`
- Subject: `GALAXY memory philosophy`
- Event: `EVENT-58f608aaa9f74fa08ec8a25fdd39c34b`
- Candidate: `CANDIDATE-94243e7f8f7349b61815331551a173ac7`
- Candidate owner: `NAOMI_REAL_MEMORY_SEED`
- Record type: `INTERACTION`
- Scope: `MemoryOS`
- Candidate status: `CANDIDATE`
- Candidate statement preserves the GALAXY principle that historical memory must not make past state permanent destiny and that revision/supersession must remain possible.
- Durable memory write: `false`
- Candidate promotion: `false`
- Relation mutations: `[]`
- Gravity mutations: `[]`
- Retrieval weighting: `false`

CONCLUSION:

The explicit seed-intake candidate gate is live and PASS. A real semantic memory can enter the bounded MemoryOS review path without becoming durable and without affecting GALAXY retrieval behavior.

NEXT GATE:

Exact-candidate durable-promotion review followed by a separate Naomi-authorized promotion click. Promotion must write only the selected durable MemoryOS record and must not create relations, write gravity, or alter retrieval weighting.
