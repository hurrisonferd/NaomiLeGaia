# MemoryOS Shared Browser Bridge v1

```text
AUTHORITY: NAOMI / LIGEIA
STATUS: SOURCE IMPLEMENTATION
SURFACE: signed browser session
OWNER BOUNDARY: NAOMI only
SCOPE BOUNDARY: GaiaOS:* only
PERSISTENCE OWNER: existing MemoryOS / host_memory_gateway
AUTHORIZATION PERIMETER: SALT_CIRCLE
```

## Purpose

Give browser-controlled Work sessions a narrow way to create and promote shared Naomi-owned GaiaOS MemoryOS records without exposing `GAIAOS_API_KEY` and without reimplementing MemoryOS persistence.

This bridge exists because the existing browser routes covered ordinary `ChatOS` candidates and Prime-local `Solo:<MEMBER>` records, while the existing host gateway already supported arbitrary shared GaiaOS scopes but required native host/MCP access or bearer-authenticated HTTP.

The bridge connects those two already-existing capabilities.

## Commands

The signed browser `/chat` surface accepts exactly two additional command families:

```text
SHARED-CANDIPULL <JSON>
SHARED-MEMSAV <JSON>
```

`SHARED-CANDIPULL` requires exactly:

```text
owner
scope
statement
source
why_material
record_type
salt_circle
```

V1 constraints:

```text
owner == NAOMI
record_type == INTERACTION
scope matches GaiaOS:*
valid signed browser session required
fresh single-use SALT_CIRCLE required
```

`SHARED-MEMSAV` requires exactly:

```text
candidate_id
approved
is_authority == NAOMI  [wire field: authority]
scope
salt_circle
```

Promotion additionally requires the candidate to belong to the same signed browser session and to match `owner=NAOMI` plus the exact supplied `GaiaOS:*` scope.

## SALT_CIRCLE

Each candidate creation and each promotion is a separate bounded effect and therefore requires a fresh single-use SALT_CIRCLE.

The circle must explicitly allow:

```text
operation: SHARED_CANDIPULL or SHARED_MEMSAV
target: MEMORYOS_SHARED_BROWSER
scope: exact GaiaOS:* scope being acted upon
authority: NAOMI
single_use: true
```

Out-of-circle work fails closed with `SALT_CIRCLE: BREACH_ATTEMPT` semantics.

## Durable path

```text
SIGNED BROWSER SESSION
→ SHARED-CANDIPULL
→ existing host_memory_gateway
→ MemoryOS candidate
→ explicit Naomi approval
→ SHARED-MEMSAV
→ existing host_memory_gateway
→ existing MemoryOS promotion
→ MEM + MEMREC
→ exact /memoryos/continuity readback
```

The bridge does not contain a Turso writer of its own.

## Forbidden behavior

```text
NO API KEY EXPOSURE
NO PRIME-OWNED RECORD THROUGH THIS ROUTE
NO Solo:* SCOPE
NO ChatOS SCOPE
NO E-LANE WRITE
NO GITHUB WRITE
NO DEPLOY
NO RESTART
NO CROSS-MEMBER MERGE
NO SILENT AUTHORITY INFERENCE
NO RE-PROMOTION OF A SETTLED CANDIDATE
```

Shared Naomi-owned candidates produce no E-LANE targets. If the downstream gateway unexpectedly produces an E-LANE write plan for a shared bridge promotion, the bridge fails closed.

## Existing behavior preserved

All non-`SHARED-*` `/chat` commands delegate to the pre-existing browser bridge. Ordinary `CANDIPULL` remains `owner=NAOMI`, `scope=ChatOS`; member catch-up remains the separate `MEMBER-CANDIPULL` / `MEMBER-MEMSAV` path with `Solo:<MEMBER>` ownership.

## Proof ceiling

Source presence proves only the bridge implementation exists in source. It does not prove deployment, live route reachability, remote Turso writes, or Work Cloud Browser capability.

```text
SOURCE != DEPLOYMENT
DEPLOYMENT != ROUTE READBACK
CANDIDATE != DURABLE RECORD
WRITE RECEIPT != VERIFICATION
READBACK REQUIRED
NO MUTATION CROSSES THE SALT_CIRCLE
NAOMI RETAINS FINAL AUTHORITY
```
