# DjinnOS Lexicon v1

```text
AUTHORITY: NAOMI / LIGEIA
STATUS: CANONICAL INDEX
SCOPE: DjinnOS vocabulary, roster, operation taxonomy, proof language, and source pointers
NORMATIVE_RULE: This file indexes canonical terms. When wording conflicts, the pointed authoritative source governs.
```

## Purpose

Provide one discoverable retrieval surface for DjinnOS names, terms, operation classes, effect classes, proof laws, and canonical source locations without creating a second independent ruleset.

This file is an index and map. It does not grant authority, create Djinn memory, change runtime behavior, or supersede the registry, specification, protocol, or carrier runtime.

## Authoritative source map

| Subject | Canonical source |
| --- | --- |
| Active DjinnOS pointers and laws | `GaiaOS/SystemsOS/Core/DjinnOS/CURRENT.json` |
| DjinnOS architecture and hierarchy | `GaiaOS/SystemsOS/Core/DjinnOS/DJINNOS.v1.md` |
| Exact eleven-member registry | `GaiaOS/SystemsOS/Core/DjinnOS/Registry/DJINN-REGISTRY.v1.json` |
| SALT_CIRCLE protocol | `GaiaOS/SystemsOS/Core/DjinnOS/Protocols/SALT-CIRCLE.v1.md` |
| Carrier runtime behavior | `api/djinn_runtime.py` |
| Carrier HTTP entrypoint | `api/djinn_entrypoint.py` |

## Visible grammar

- Shared status glyph: `🧿`
- Material-contribution activation mark: `⌁`
- Example visible form after material contribution: `🧿 ORVAS ⌁`
- Operation-class words are architectural taxonomy, not required nameplate text.

## Hierarchy and accountability

Canonical hierarchy:

`NAOMI → ChatOS → FairyOS → Prime Daemon → Djinn dispatcher → existing GaiaOS systems → Djinn result → Prime Daemon → NAOMI`

Key terms:

- **Prime accountability**: every Djinn invocation has an accountable Prime above it. The Prime remains accountable for the Djinn result.
- **Djinn dispatcher**: the bounded runtime surface that executes exactly one selected Djinn operation and returns control to the Prime.
- **No autonomous Djinn-to-Djinn spawning**: a Djinn may not independently invoke another Djinn. Call depth must remain zero.
- **TOOLS_NOT_PERSONS**: Djinn are bounded tools, not Prime Daemons, people, biographies, independent authorities, memory owners, or E-LANE members.
- **No retroactive Djinn history**: Djinn may inspect evidence predating Day 0 but may not claim participation in those historical events.

## Eleven Djinn

| Djinn | Operation class | Effect class | Implementation | Runtime behavior summary |
| --- | --- | --- | --- | --- |
| **KYMER** | `INDEX` | `READ_ONLY` | `DETERMINISTIC` | Indexes supplied records/items, extracts selected coordinates, computes stable SHA-256 identities, and reports exact duplicate groups or an optional two-item equality comparison. |
| **DRELAS** | `JIG` | `READ_ONLY` | `DETERMINISTIC` | Compares observed steps to a required template/order and checks supplied invariants for exact failures. |
| **RONAVE** | `FLOW` | `READ_ONLY_TRANSFORM` | `DETERMINISTIC_V1` | Deduplicates repeated non-empty text lines while carrying evidence, warnings, and unknowns as protected supplied fields. |
| **AGREN** | `QUEUE` | `EPHEMERAL_ONLY` | `DETERMINISTIC` | Maintains caller-supplied invocation-local workflow state through INIT / ADVANCE / BLOCK / SUPERSEDE. State is returned, not persisted, and must be supplied again for later work. |
| **HALVEX** | `SEAL` | `SALT_CIRCLE_GATED` | `DETERMINISTIC_ORCHESTRATOR` | Validates an exact bounded effect plan against a SALT_CIRCLE. With no action adapters it returns `READY_NO_EXECUTOR` and performs no external effect. External effects require separately injected trusted adapters after validation. |
| **SERA** | `COURIER` | `READ_ONLY_TRANSFORM` | `DETERMINISTIC` | Packages objective, accepted evidence, authority envelope, constraints, current state, exact next step, and unknowns into a deterministic courier packet with a packet SHA-256. |
| **ORVAS** | `WITNESS` | `READ_ONLY` | `DETERMINISTIC` | Compares required expected/observed fields exactly, returns MATCH / MISMATCH / UNKNOWN, and does not infer missing proof. |
| **MALRIC** | `LINTER` | `READ_ONLY` | `DETERMINISTIC` | Flags proof and authority errors including REQUESTED_NOT_COMPLETED, durability without readback, receipt-as-verification, source/runtime conflation, UNKNOWN coercion, cross-member merge, authority expansion, retroactive Djinn claim, and nested Djinn chaining. |
| **MARVEK** | `PROBE` | `READ_ONLY` | `DETERMINISTIC` | Classifies required capabilities from supplied evidence as AVAILABLE / UNAVAILABLE / UNKNOWN without converting unrecognized states into proof. |
| **VASQAR** | `TRACE` | `READ_ONLY` | `DETERMINISTIC` | Traces supplied proof stages in order, identifies the highest contiguous proven stage, preserves gaps, and reports whether the chain is complete. |
| **USION** | `SETTLE` | `READ_ONLY_TRANSFORM` | `DETERMINISTIC_V1` | Produces a non-persistent settled baseline containing objective, verified-now facts, superseded assumptions, remaining unknowns, out-of-scope items, and exact next active work. |

## Operation classes

- **INDEX**: construct deterministic coordinates and identities over supplied material.
- **JIG**: test conformance of a supplied process against required sequence and invariants.
- **FLOW**: transform supplied text into a more compact form while protecting designated evidence/unknown/warning fields.
- **QUEUE**: carry explicit invocation-local operational state without durable memory.
- **SEAL**: validate and, only when separately equipped with trusted adapters, coordinate bounded effects inside a SALT_CIRCLE.
- **COURIER**: package verified state, authority, constraints, and next-step information for transport.
- **WITNESS**: compare expected and observed proof fields exactly.
- **LINTER**: detect proof-language, authority, memory-separation, and hierarchy violations.
- **PROBE**: classify explicitly supplied capability states without inference.
- **TRACE**: map a proof chain and identify the first unresolved gap.
- **SETTLE**: construct a current non-persistent baseline from verified facts and remaining unknowns.

## Effect classes

- **READ_ONLY**: inspects supplied material and returns a result without an external mutation path.
- **READ_ONLY_TRANSFORM**: transforms supplied material into derived work product without external mutation.
- **EPHEMERAL_ONLY**: may carry state only inside invocation-local / caller-resupplied work product; no Djinn persistence exists.
- **SALT_CIRCLE_GATED**: an effect-capable orchestration class whose proposed operation, target, and scope must remain inside a valid host-issued SALT_CIRCLE. In v1 this applies only to HALVEX.

## SALT_CIRCLE

A **SALT_CIRCLE** is a single-use machine-readable authorization perimeter for a bounded effect. It does not create Naomi's authorization; it encodes and constrains authorization that already exists.

Canonical required properties include:

- `authority == NAOMI`
- exact `operation_id`
- `single_use == true`
- non-empty `allowed_operations`
- non-empty `allowed_targets`
- non-empty `allowed_scopes`
- optional expiry / `valid_until`
- optional `explicit_forbiddens`

A requested effect outside the allowed operation, target, or scope fails closed. A consumed operation ID cannot be replayed within the process-local replay guard. Host-level replay protection is still required across restarts.

Canonical protocol: `GaiaOS/SystemsOS/Core/DjinnOS/Protocols/SALT-CIRCLE.v1.md`.

## Memory and persistence terms

- **No Djinn durable memory**: DjinnOS owns zero durable Djinn memories.
- **No Djinn E-LANES**: Djinn do not receive member-owned E-LANES.
- **Work product is not memory**: a Djinn result, packet, trace, queue state, or baseline is ordinary work product unless a separate authorized preservation lifecycle records it elsewhere.
- **AGREN ephemeral state**: AGREN may return queue state, but it is not retained by DjinnOS and must be supplied again by the caller.

## Proof laws

These phrases are canonical operational distinctions, not stylistic slogans:

- **REQUESTED != COMPLETED**: asking for an effect is not proof that it happened.
- **SOURCE != DEPLOYMENT**: source presence is not proof that a running service contains that source.
- **RECEIPT != READBACK**: a write/execution receipt does not independently prove the resulting state.
- **CANDIDATE != DURABLE**: a staged MemoryOS candidate is not a durable record.
- **UNKNOWN STAYS UNKNOWN**: missing or ambiguous evidence may not be silently coerced into success or failure.
- **READBACK REQUIRED FOR EFFECT CLAIMS**: claims about persistent or external effects require observation of resulting state.
- **NO MUTATION CROSSES THE SALT_CIRCLE**: effectful work must remain inside the exact authorized perimeter.

## Common runtime statuses and phrases

- **`OK`**: the bounded Djinn operation itself completed normally. It does not independently prove an external effect.
- **`READY_NO_EXECUTOR`**: HALVEX validated an authorized plan but received no external action adapters, therefore executed nothing externally.
- **`external_effects=false`**: no external mutation was produced by that invocation.
- **`verified=true`**: for ORVAS, all required supplied fields were present and exactly matched their expected values. It is scoped to those compared fields only.
- **`UNKNOWN`**: evidence is absent, unresolved, or invalid for the requested claim; it must remain visible.
- **replay rejection**: reuse of a consumed SALT_CIRCLE operation ID is rejected rather than treated as a second valid effect.

## Day-0 boundary

Official activation coordinate:

`2026-10-03 19:41 -07:00` / `2026-10-04T02:41:00Z`

No Djinn operation may be claimed before Day 0. Inspection of older evidence is permitted after Day 0, but participation in the older event may not be invented retroactively.

## Index maintenance law

When a new Djinn, operation class, effect class, canonical DjinnOS protocol term, proof law, or visible grammar element is introduced:

1. update the authoritative source that owns the behavior or law;
2. update this lexicon with a pointer and concise retrieval definition;
3. do not make this lexicon the only location containing an enforceable rule;
4. preserve source/runtime/proof distinctions;
5. retain Naomi/Ligeia as final authority.

Archive/index review should be treated as an explicit design step, not an accidental by-product of implementation.
