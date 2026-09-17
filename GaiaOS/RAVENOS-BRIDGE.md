# RavenOS → GaiaOS Bridge

```text
AUTHORITY: NAOMI inside GaiaOS
HOST / TRANSPORT: RavenOS
STATUS: LIVE BRIDGE OBSERVED
```

RavenOS now has a live read-only bridge to GaiaOS.

```text
RAVENOS HOST
→ RavenOS/GaiaOSBridge
→ GaiaOS Streamable HTTP MCP
→ GaiaOS front door / Council / BrainOS / context
→ NAOMI AUTHORITY
```

## Live RavenOS gateway

`https://ravenos-gaiaos-bridge.onrender.com`

Preferred human/request front door:

```text
POST /gaiaos
{"request":"<Naomi's natural request>"}
```

Other bounded routes:

```text
GET  /health
GET  /gaiaos/tools
GET  /gaiaos/selftest
POST /gaiaos/call
POST /gaiaos/dispatch
POST /gaiaos/context
```

## Current bridge tool surface

```text
gaia
gaia_selftest
load_gaiaos
gaia_council
gaia_dispatch
gaia_operator
gaia_brain
gaia_context
```

Observed bridge proof included real external MCP initialize, tool discovery, GaiaOS self-test, Gaia front-door routing, context navigation, and deterministic Council dispatch while GaiaOS continued to report `authority=NAOMI`.

## Important boundary

```text
RAVENOS HOST != NAOMI AUTHORITY
RAVENOS BRIDGE != GAIAOS IDENTITY
TRANSPORT ACCESS != AUTHORITY TRANSFER
GAIAOS != RAVENOS
ARCHITECTURE DONOR != IDENTITY DONOR
```

The bridge does not expose Jarvis-Private or Raven private continuity to GaiaOS. It is a read-only transport/client surface into GaiaOS's own public carrier.

## Naomi Chat behavior

If Naomi Chat can only access GitHub and cannot directly invoke arbitrary HTTP/MCP calls, this file proves the external bridge exists but does **not** imply that the current ChatGPT tab is attached to it.

In that case continue using:

`GaiaOS/NAOMI-CHAT-FULL-PACKET.md`

for rich GitHub-backed GaiaOS operation, while treating RavenOSBridge as a separately proven runtime doorway.

```text
BRIDGE LIVE != THIS CHAT ATTACHED
FULL SOURCE MODE != FAKE MCP MODE
UNKNOWN STAYS UNKNOWN
```
