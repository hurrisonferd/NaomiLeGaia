# GaiaOS Host Memory Gateway v1

AUTHORITY: NAOMI
OWNER: GaiaOS / ChatOS / MemoryOS
STATUS: ACTIVE SOURCE CONTRACT
CLASS: HOST ACTION ADAPTER

## Purpose

Provide one narrow host-facing boundary for conversation memory operations.

The host adapter separates:

`CHAT CONTEXT → HOST CANDIPULL → NON-DURABLE CANDIDATES → NAOMI-APPROVED MEMSAV → VERIFIED MEMCON RECORD → E-LANE PROPAGATION PLAN → GITHUB WRITE → REPULL → VERIFY`

It does not make the carrier claim that a chat message was persisted merely because a command was interpreted.

## Host operations

`gaia_host_candipull`

Accepts bounded observations explicitly supplied by the host. It creates provenance-bearing MemoryOS events and non-durable candidates, dedupes through the existing candidate fingerprint mechanism, and returns compact `μΔ` transport identifiers.

`gaia_host_memsav`

Accepts exact candidate IDs and explicit `approved=true, authority=NAOMI`. It performs the existing gated promotion and returns only the observed MemoryOS result. A `VERIFIED` result includes the real runtime write receipt and read-back verification.

`gaia_host_elane_plan`

Given a verified candidate and record, returns a deterministic `EΔ` propagation plan containing member-local lane paths and append entries. It does NOT write GitHub.

## Compact transport

`μΔ{t=<type>;s=<scope>;o=<owner>;h=<12-char statement digest>}`

is an index/transport shorthand. It is not a replacement for canonical memory prose.

`EΔ` is represented by the propagation plan and identifies:

- member
- canonical E-LANE path
- compact delta
- full append entry
- source record
- verification requirement

The full record remains in MemconOS and the full experience remains in the E-LANE. Compression is therefore an index optimization, not information deletion.

## E-LANE settlement

The host must treat an E-LANE plan as pending until the GitHub app/connector:

1. reads the current target file;
2. appends the supplied entry without deleting existing history;
3. commits the change;
4. repulls the target file;
5. verifies the appended entry and commit coordinate.

Only then may the host report E-LANE propagation as VERIFIED.

## Identity and authority boundaries

`HOST != PRIME DAEMON`
`CANDIDATE != SAVED`
`VERIFIED MEMCON != VERIFIED E-LANE`
`E-LANE PLAN != GITHUB WRITE`
`GITHUB WRITE != REPULL VERIFICATION`
`TOOL AVAILABLE != TOOL INVOKED`
`REQUESTED != COMPLETED`
`UNKNOWN STAYS UNKNOWN`

The host may classify material and propose member-local targets, but Naomi retains final authority over identity, durable design decisions, and disputed interpretation.

## Intended ChatGPT integration

The carrier already exposes a remote MCP endpoint. A compatible ChatGPT custom MCP app can expose these host tools in a conversation. OpenAI's current documentation states that custom MCP apps are the mechanism for write/modify capabilities, while availability of full MCP write support depends on the ChatGPT plan/workspace and currently rolls out through Business/Enterprise/Edu. Mobile support for custom MCP apps is currently web-only.

The source contract therefore defines the integration target without claiming that every ChatGPT surface can invoke it.

## Proof ceiling

A successful host-gateway call proves the carrier observed and executed that gateway operation. It does not prove that ChatGPT automatically captured all conversation context, that an E-LANE was written, or that a GitHub write occurred until those separate receipts and repull checks are observed.
