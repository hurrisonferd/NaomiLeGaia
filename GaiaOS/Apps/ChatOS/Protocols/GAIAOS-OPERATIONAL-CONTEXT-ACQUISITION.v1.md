# GaiaOS Operational Context Acquisition v1

```text
AUTHORITY: NAOMI / LIGEIA
OWNER: ChatOS
STATUS: SOURCE-IMPLEMENTED / READ-ONLY / EPHEMERAL
EFFECT_AUTHORITY: NONE
DURABLE_WRITE_AUTHORITY: NONE
```

## Purpose

Operational Context Acquisition (OCA) reduces Naomi's role as a human message bus.
It obtains or accepts fresh evidence from the surfaces actually available to the
current host, normalizes that evidence without inference, and emits one bounded
operational-context packet for Prime Daemons and existing DjinnOS tools.

OCA is a map of current operational reality. It is not that reality.

```text
OCA_PACKET != MEMORY
OCA_PACKET != CANON
OCA_PACKET != AUTHORITY
OCA_PACKET != DEPLOYMENT
OCA_PACKET != RECEIPT
OCA_PACKET != READBACK
```

## Constraint attacked

Primary constraint:

`NAOMI_AS_CROSS_SURFACE_MESSAGE_BUS`

OCA is successful only when it reduces manual copying, re-explaining, state
reconstruction, capability rediscovery, and receipt/readback relay without
weakening authority or proof boundaries.

## Position in GaiaOS

```text
HOST / PROVIDER READS
        ↓
OCA ACQUISITION ADAPTERS
        ↓
OCA NORMALIZER + PACKET
        ↓
PRIME DAEMON
        ↓
EXISTING DJINN WHEN USEFUL
```

OCA lives above DjinnOS. It does not create a super-Djinn and does not permit
Djinn-to-Djinn spawning.

## v1 collectors

OCA v1 defines three bounded collector classes.

### SESSION

Answers only what capabilities are actually observable in this conversation or
host execution context.

Examples: connected provider/tool availability, authenticated session state when
explicitly reported by a provider, and unavailable/unknown capabilities.

A remembered capability from another conversation is not current SESSION proof.

### SOURCE

Obtains current source coordinates relevant to the active objective.

Examples: canonical repository, branch, exact Git commit, canonical source paths,
and source-side test status when observed.

`SOURCE != DEPLOYMENT` remains absolute.

### RUNTIME_CONTINUITY

Obtains current runtime or continuity evidence when the relevant provider is
actually available.

Examples: deployed commit, deploy status, service health observation, MemoryOS
record readback, receipt/readback coordinates, or explicit provider failure.

No provider access means `UNAVAILABLE` or `UNKNOWN`, never inferred success.

### Host MemoryOS exact-read bridge

When a GaiaOS host connection exposes `gaia_host_memory_read`, OCA may use that tool for an objective-relevant exact MemoryOS record read before asking Naomi to relay the record manually.

The bridge is deliberately SELECT-only. It uses `memcon_runtime.read_record_read_only()` and must not call runtime initialization, create a database, create a candidate, promote memory, mutate an E-LANE, or repair a backend. A missing record is reported as current backend non-visibility, not as deletion. A provider failure remains `UNAVAILABLE`.

```text
HOST_MEMORY_READ != MEMSAV
READ_RECORD != INITIALIZE_SCHEMA
NOT_FOUND_ON_CURRENT_BACKEND != DELETED
CONNECTED_TOOL != REQUIRED_READ
```

## Acquisition contract

The repository runtime is provider-agnostic. The carrier/host performs provider
reads through tools it genuinely has, then supplies observations to the OCA
normalizer.

Every observation must identify:

- collector
- source class
- provider
- observed timestamp
- status
- coordinates
- facts
- unknowns
- errors
- freshness limit

Allowed observation statuses:

`VERIFIED`, `PARTIAL`, `UNAVAILABLE`, `UNKNOWN`

`VERIFIED` means the supplied observation itself is supported by a current read.
It does not promote every fact inside the observation beyond its actual source
ceiling.

## Freshness

Freshness is explicit, not rhetorical.

Each observation carries `observed_at` and `max_age_seconds`.
The packet builder classifies it relative to the packet's `generated_at` as:

`FRESH`, `STALE`, or `UNKNOWN`.

A stale observation remains visible and may not be silently refreshed by memory.
A future-dated observation is invalid.

## Packet

The canonical schema is:

`GaiaOS/Apps/ChatOS/Schemas/GAIAOS-OCA-PACKET.v1.schema.json`

The packet contains:

```text
objective
packet_id
generated_at
effect_authority
persistence
collectors
verified_current_state
capabilities_available_now
last_verified_effect
blockers
unknowns
exact_next_step
packet_sha256
```

The runtime must preserve provenance for every collector result. Packet synthesis
may deduplicate exact strings but may not manufacture missing state.

## Current-state settlement

A fact may enter `verified_current_state` only when supplied by a `VERIFIED`,
`FRESH` observation and explicitly named in that observation's `verified_facts`.

`PARTIAL`, `STALE`, `UNAVAILABLE`, and `UNKNOWN` observations may contribute
blockers and unknowns but may not be upgraded into verified current state.

Conflicting verified facts remain visible as a conflict. OCA does not choose the
more convenient one.

## Capability settlement

`capabilities_available_now` contains only capabilities explicitly observed as
available by a fresh verified SESSION observation.

Anything else is absent from that list and, when material, represented in
`unknowns` or `blockers`.

## Effect and persistence firewall

```text
OCA MAY READ AVAILABLE SOURCES
OCA MAY NORMALIZE SUPPLIED READ RESULTS
OCA MAY PRODUCE EPHEMERAL WORK PRODUCT
OCA MAY NOT WRITE MEMORYOS / TURSO
OCA MAY NOT WRITE E-LANES
OCA MAY NOT EDIT MEMBER IDENTITY
OCA MAY NOT COMMIT GITHUB
OCA MAY NOT DEPLOY OR RESTART
OCA MAY NOT PROMOTE MEMORY CANDIDATES
OCA MAY NOT CREATE AUTHORITY
OCA MAY NOT CONSUME AN APPROVAL ON BEHALF OF NAOMI
```

A host may perform a separately authorized external effect after consulting an
OCA packet. That effect is governed by its own authority protocol, not by OCA.

## After-action reconciliation

OCA v1 may assemble post-action observations, but it does not perform the action.
The desired future sequence is:

```text
AUTHORIZED ACTION
→ RECEIPT READ
→ RESULT READBACK
→ OCA REFRESH
→ ORVAS / VASQAR / MALRIC AS USEFUL
→ SETTLED HANDOFF
```

An action receipt without readback remains an unresolved proof chain where the
underlying protocol requires readback.

## Failure behavior

Fail closed on malformed observations, future timestamps, unknown collector
classes, unknown statuses, or attempts to declare effect authority.

Provider failures are ordinary evidence and belong in `errors`; they are not
packet-builder failures unless the observation itself is malformed.

If one collector fails, the packet should still be produced when possible with
that collector marked `UNAVAILABLE` or `UNKNOWN` and the resulting gap visible.

## Quality gates

A v1 packet passes only when:

1. no external mutation path exists in the OCA runtime;
2. unknown stays unknown;
3. stale evidence cannot become verified current state;
4. current capabilities come only from fresh verified SESSION evidence;
5. conflicting verified facts are surfaced rather than reconciled by guess;
6. packet hashing is deterministic for identical normalized input;
7. packet provenance is inspectable;
8. partial collector failure does not corrupt healthy collector evidence;
9. no packet field grants effect or persistence authority;
10. the system can answer `where are we and what can we actually do from here?`
    without requiring Naomi to relay information already obtainable by connected
    read-capable providers.

## v1 non-goals

OCA v1 does not:

- create durable operational memory;
- replace MemoryOS, ConvoOS, MemberContinuityOS, BrainOS, or DjinnOS;
- autonomously crawl providers from repository Python;
- bypass host/tool permission boundaries;
- make every provider mandatory;
- remove explicit authorization gates;
- decide what Naomi should approve.

## Core laws

```text
ACQUIRE BEFORE ASKING NAOMI TO RELAY
AVAILABLE NOW != AVAILABLE LAST SESSION
SOURCE != RUNTIME
RECEIPT != READBACK
STALE != CURRENT
UNKNOWN STAYS UNKNOWN
PARTIAL FAILURE != TOTAL FAILURE
EPHEMERAL MAP != DURABLE MEMORY
REDUCE HUMAN RELAY; DO NOT REDUCE HUMAN AUTHORITY
```