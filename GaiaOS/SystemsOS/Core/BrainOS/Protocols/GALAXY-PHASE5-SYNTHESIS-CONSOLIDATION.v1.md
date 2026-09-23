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
