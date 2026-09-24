# GALAXY Phase 7A — Finite-storage pruning research

TITLE: Read-only pruning eligibility and dependency review
AUTHORITY: NAOMI / LIGEIA
OWNER: GaiaOS / MemoryOS + BrainOS
STATUS: PHASE 7A MERGED / PHASE 7B LIVE READ-ONLY SURFACE SOURCE BUILD
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
