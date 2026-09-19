# GALAXY v1 Blueprint

TITLE: Gravitational Adaptive Learning Archive & conteXt sYstem
AUTHORITY: NAOMI / LIGEIA
OWNER: GaiaOS / MemoryOS + BrainOS
STATUS: SOURCE BLUEPRINT / IMPLEMENTATION NOT YET PROVEN

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
