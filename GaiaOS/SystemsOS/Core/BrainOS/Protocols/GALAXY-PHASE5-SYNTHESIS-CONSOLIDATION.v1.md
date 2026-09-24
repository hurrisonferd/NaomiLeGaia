# GALAXY Phase 5 — Provenance-Backed Synthesis / Consolidation v1

AUTHORITY: NAOMI / LIGEIA
OWNER: GaiaOS / MemoryOS + BrainOS
STATUS: SOURCE DESIGN / READ-ONLY FIRST
VERSION: galaxy.phase5.synthesis-consolidation.v1

## Purpose

Phase 5 allows a stable cluster of durable MemoryOS records to become eligible for a new synthesis record without rewriting, deleting, or laundering the source records.

A synthesis is a new evidence-bearing record with explicit provenance. It is never a silent edit of its parents.

## Laws

`SYNTHESIS != SOURCE REWRITE`

`SYNTHESIS != AUTHORITY`

`CONSOLIDATION != DELETION`

`SOURCE HISTORY != SYNTHESIS SUMMARY`

`PROVENANCE COMPLETE OR HOLD`

`CONTRADICTION SURFACED != CONTRADICTION FLATTENED`

`PROPOSED DEFAULT TARGET != PRODUCTION RETRIEVAL CHANGE`

`NEW SYNTHESIS != AUTOMATICALLY TRUER`

## Initial bounded slice

The first Phase-5 slice is deliberately read-only.

A cluster review may inspect 2 through 6 distinct durable records. Initial eligibility requires:

- every source record exists;
- every source is in the same scope;
- at least one VERIFIED internal GALAXY relation joins members of the cluster;
- no VERIFIED internal CONTRADICTS edge remains unresolved;
- no source record is itself a synthesis in the initial non-recursive slice;
- at least one source remains eligible for ordinary current context;
- source statements and governing-state evidence remain inspectable;
- no MemoryOS write occurs;
- no production retrieval behavior changes.

The first controlled fixture reuses the live-proven Phase-4 revision pair:

- REVISION: `MEM-ffc0c2af5cfa48d7aee7332a290a3d0e`
- CORE: `MEM-00b3fbfd4d73404f97a95c238596ab94`

Their VERIFIED REVISES relation provides the bounded internal graph connection. The previously tested SUPERSEDES edge may remain historically visible as REVOKED and does not become current governing evidence.

## Candidate envelope

Read-only review produces a synthesis candidate envelope only. It does not invent or manifest final prose.

The envelope contains:

- exact ordered source record IDs;
- source scope;
- source statements as provenance snapshots;
- governing-state snapshots;
- VERIFIED internal relations;
- non-governing historical internal relations;
- method `PROVENANCE_BACKED_CLUSTER_V1`;
- an explicit requirement that a final synthesis statement be supplied and separately reviewed before any write.

The read-only review must report `synthesis_statement_generated=false`.

## Retrieval boundary

Phase 5 source/read-only work does not:

- create a synthesis record;
- insert into `memory_syntheses`;
- create DERIVED_FROM edges;
- change gravity;
- change lifecycle state;
- change ordinary retrieval;
- enable unrestricted/global weighting.

Any future synthesis becoming a default retrieval target requires a separate explicit Naomi-authorized mutation and a later retrieval-effect proof.

## Future mutation gate

After source deployment and live read-only PASS, a later bounded mutation design may:

1. accept an exact synthesis statement;
2. re-run cluster eligibility;
3. dedupe equivalent source sets;
4. create one new MemoryOS SYNTHESIS record;
5. write one `memory_syntheses` provenance row;
6. create explicit DERIVED_FROM edges from synthesis to every source;
7. return a receipt and exact readback;
8. preserve every source record unchanged;
9. leave production retrieval unchanged until separately authorized.

That mutation path is not implemented by this source-first checkpoint.

## Proof ladder

`SOURCE -> CI -> DEPLOY -> READ-ONLY LIVE FIXTURE -> EXPLICIT MUTATION AUTHORIZATION -> PROPOSAL -> READBACK -> RETRIEVAL EFFECT TEST`

## Current next gate

Deploy the read-only Phase-5 source, run `/verify`, then run:

`GET /galaxy/synthesis/phase5-fixture-review`

Stop and inspect before implementing any synthesis mutation route.


## Authorized mutation design checkpoint — 2026-09-23

Naomi explicitly authorized Phase-5 synthesis mutation **design** after the live read-only fixture PASS.

Authorization scope is bounded:
- design and implement source for the controlled mutation lifecycle;
- add offline tests and a read-only mutation-design review surface;
- do **not** expose an effectful browser mutation route yet;
- do **not** manifest a synthesis yet;
- do **not** promote any synthesis into ordinary MemoryOS retrieval.

### Controlled shadow lifecycle

The first mutation design is deliberately isolated from ordinary MemoryOS retrieval:

`SYNTHESIS_PROPOSED -> SYNTHESIS_VERIFIED_SHADOW -> SYNTHESIS_REVOKED`

The synthesis record is created only in scope:

`GALAXY_SYNTHESIS_SHADOW`

It therefore does not become a MemoryOS candidate merely by existing.

Exact controlled source set:
- `MEM-ffc0c2af5cfa48d7aee7332a290a3d0e`
- `MEM-00b3fbfd4d73404f97a95c238596ab94`

Exact controlled synthesis statement:

`GALAXY-CAL-SYNTHESIS [1d79c239f31f]: The calibration core reported a violet carrier pulse; a later controlled observation revises that calibration toward ultraviolet.`

This statement is fixed in source before any manifestation. It is not generated at click time.

### Proposal effect

A future separately authorized proposal action may atomically create:
- one durable `SYNTHESIS` memory record in `GALAXY_SYNTHESIS_SHADOW`;
- one `memory_syntheses` provenance row containing the exact source IDs;
- one PROPOSED `DERIVED_FROM` edge from the synthesis to each source.

Proposal does not:
- verify provenance;
- move the synthesis into MemoryOS;
- select it as a default retrieval target;
- alter source records;
- delete anything.

### Verification effect

A future separately authorized verification action may:
- verify the exact expected `DERIVED_FROM` edges;
- change the synthesis status to `SYNTHESIS_VERIFIED_SHADOW`.

Verification still does not:
- move the synthesis into MemoryOS;
- select it as a default retrieval target;
- alter production retrieval.

### Revocation effect

A future separately authorized revocation action may:
- mark the synthesis `SYNTHESIS_REVOKED`;
- mark its `DERIVED_FROM` edges `REVOKED`;
- preserve the synthesis record, `memory_syntheses` row, source records, edge records, timestamps and evidence.

No physical delete is permitted.

### Atomicity and fail-closed behavior

The proposal primitive writes the synthesis envelope, provenance row and proposed provenance edges in one database transaction. Missing sources, duplicate source IDs, cross-scope sources, empty statements, invalid confidence or an existing non-revoked synthesis over the same source set must fail closed.

Verification requires the exact source set, exact fixed statement, shadow scope and exact proposed provenance edge set.

Revocation requires the exact controlled synthesis and a non-empty reason.

### Current exposure boundary

The effectful source primitives exist only as internal source capability. No Phase-5 mutation browser route or Ritual Grimoire entry is authorized by this design checkpoint.

The only newly permitted live surface is read-only:

`GET /galaxy/synthesis/phase5-mutation-design-review`

Next proof gate:

`SOURCE + CI -> DEPLOY -> /verify -> READ-ONLY MUTATION-DESIGN REVIEW -> STOP`

Only after that live receipt is reviewed may Naomi separately authorize exposing controlled Phase-5 mutation controls.


## Exact controlled exposure implementation checkpoint — 2026-09-24

At Naomi's previously recorded 2026-09-23 authorization, the **control surface source** was prepared in the isolated feature branch \`galaxy/phase5-controlled-exposure-20260924\`. This does **not** authorize the assistant to execute a synthesis operation; each operation still requires Naomi's own separate signed, CSRF-protected confirmation.

Source:
- \`api/galaxy_phase5_controls.py\`: exact read-only inspection, PROPOSE / VERIFY / REVOKE dispatch, fixed fixture IDs and statement, source-unchanged and provenance readback.
- \`GET /galaxy/synthesis/phase5-controls\`: read-only, signed-session, no-JavaScript mobile review page.
- \`GET /galaxy/synthesis/phase5-controls/confirm/{kind}\`: read-only per-step effect preview, no write.
- \`POST /galaxy/synthesis/phase5-controls/manifest\`: signed session, CSRF, exact confirmation, explicit Naomi approval and stage/target checks. No GET operation can mutate.
- All effects stay in \`GALAXY_SYNTHESIS_SHADOW\`. A control reply can say PASS_READBACK only when its exact state, statement, scope, source set, provenance edge set and untouched sources have been read back. A returned HOLD may still follow a partially executed effect, so inspect the actual store before retrying.

**Proof and authority ceiling:** GitHub branch preparation and offline CI do not mean Render deployed the code. No live mutation was executed as part of this source checkpoint. Production retrieval, unrestricted weighting, general AUGURY interpretation, physical pruning and migration remain outside this authorization.

**Finite next gate:** review the draft change; merge/deploy only when authorized; run deployed \`/verify\` and the read-only control page; stop and inspect. Only Naomi may subsequently choose each of PROPOSE, VERIFY and REVOKE as separate explicit actions, inspecting receipts between them. Do not infer permission to press the next button from a prior button.
