# //PW:PRESERVE// — Sanitized continuity and MCP bridge

Authority: NAOMI / LIGEIA
Date: 2026-10-04
Scope: non-sensitive continuity since the prior Selene patch/J-pop checkpoint. Personally sensitive material is intentionally omitted from this public GitHub record and maintained separately by the owner.

## 1. Music continuity

The prior Selene Vital patch remains preserved as the melancholy/luminous branch, with four established expressive macros: GLOW, ACHE, AIR, DISTANCE. A key discovery was that GLOW + ACHE + DISTANCE produces an intentionally painful, wailing state that feels emotionally hurt rather than technically bad. DISTANCE was judged successful and should not be altered casually.

Next music target remains **J-pop Selene**: a distinct brighter branch with cleaner attack, sparkling upper register, tighter room, rhythmic movement, bittersweet harmonic identity, and a lead-capable voice, while retaining recognizable Selene DNA.

## 2. Skill-ownership correction

Naomi explicitly corrected an overstatement of her technical mastery. Ableton is a real learned skill in progress, but she does not claim independent proficiency in GitHub, Render, infrastructure, or much of GaiaOS's implementation work. Much of that execution has been performed by the assistants while Naomi directed, approved, tested, and continued the work.

Future guidance must not convert assisted execution into counterfeit proof of independent mastery.

For skills Naomi wants to own, use this teaching loop:

`EXPLAIN -> NAOMI PREDICTS -> NAOMI EXECUTES -> DAEMON CHECKS -> RECEIPT`

The point is reproducible understanding, not conceptual familiarity alone.

## 3. Netrunner learning track

Naomi wants a practical Netrunner curriculum covering:

- networking: IP, subnets, DNS, ports, TCP/UDP, routing, NAT
- PowerShell, Linux shell, processes, services, logs, permissions
- Python / PowerShell / Bash scripting
- packet inspection with Wireshark/tcpdump
- HTTP, APIs, cookies, sessions, auth, certificates, keys
- defensive analysis
- safe/authorized pentesting through labs, CTFs, owned systems, deliberately vulnerable targets

The learning standard is: understand what the command means, what output proves, why it works, and how to classify failures.

## 4. Host/MCP continuity correction

A major conversational correction occurred around MCP.

Established GaiaOS history already proved that:

- GitHub source can be correct while ordinary ChatGPT lacks native GaiaOS transport
- LIGEIA-API can be live while the host exposes no GaiaOS callable tool
- Work/browser access is not the same thing as native MCP
- Project context is not live MemoryOS retrieval
- model knowledge of an endpoint is not the same thing as host access to that endpoint

The earlier response temporarily regressed into source/runtime/host conflation by treating contemporary MCP product support as if it solved the already-known ordinary-chat transport gap. Naomi correctly called this out.

Restored proof rule:

`SOURCE CAPABILITY != DEPLOYED CAPABILITY != HOST TOOL EXPOSURE != LIVE INVOCATION`

## 5. Why Turso matters

Naomi explicitly pointed out that this host discontinuity is one of the reasons GaiaOS uses Turso/MemoryOS.

Architecture:

- GitHub = canonical source / system definition
- Render = runtime host for LIGEIA-API
- LIGEIA-API = live GaiaOS service surface
- MemoryOS = memory governance / approval / continuity logic
- Turso = durable external storage
- ChatGPT / another model host = replaceable execution surface

The host is not authoritative continuity storage. Hosts can forget, drift, lose tools, change models, or expose different capabilities by session.

Core principle:

**GaiaOS owns truth; host adapters own transport.**

## 6. Current DjinnOS bridge state

The live GaiaOS source already contains `/djinn/invoke`, with structured inputs including selector, calling Prime, objective, payload, invocation metadata, and optional SALT_CIRCLE.

The public Djinn invocation path currently dispatches with `action_adapters=None`, so the first bridge should remain read-only/fail-closed with respect to external mutations.

The missing wire remains:

`ordinary ChatGPT -> real callable transport -> LIGEIA-API`

Not DjinnOS itself.

No Djinn may receive the material-contribution glyph `⌁` unless a real invocation is observed.

## 7. Host-adapter model

The desired host adapter should be deliberately thin. It should contain no canonical memory, Prime biography, user biography, or duplicated continuity database.

Its job is only:

- locate GaiaOS
- authenticate
- translate the host's tool protocol to LIGEIA-API requests
- return results

Conceptual architecture:

```text
                         GAIAOS
+-------------------------------------------------+
|                                                 |
| GitHub                 Turso                    |
| source truth           durable memory           |
|    |                       ^                    |
|    |                       |                    |
|    v                       |                    |
| LIGEIA-API ----------- MemoryOS                 |
|    |                                            |
|    +-------- DjinnOS                            |
|    |             |                              |
|    |             v                              |
|    |        bounded tools                       |
|                                                 |
+----+--------------------------------------------+
     |
     | HTTP
     v
+-------------------+
| HOST ADAPTER      |
|                   |
| protocol bridge   |
| authentication    |
| transport only    |
+---------+---------+
          |
          v
+-------------------+
| current AI host   |
+---------+---------+
          |
          v
        NAOMI
```

If the AI host changes, the adapter changes. GaiaOS does not.

## 8. OpenAI Sites decision

OpenAI Sites was investigated as one possible MCP/plugin transport, but Naomi explicitly rejected it as the desired architectural direction.

Do not treat Sites as the canonical bridge merely because it may be available.

## 9. Remote Desktop Commander candidate

A plugin named **Remote Desktop Commander** was surfaced as a potentially useful host integration candidate. Its advertised capability is to connect ChatGPT to an authorized computer's filesystem and terminal through a Remote MCP.

It is currently **UNVERIFIED** for GaiaOS and was **not installed, connected, authorized, or tested** in this conversation.

Proposed experiment:

```text
ChatGPT
  -> Remote MCP
  -> Naomi's Windows computer
  -> gaia_bridge.py
  -> LIGEIA-API
  -> DjinnOS / MemoryOS
  -> Turso
```

The attraction of this route is that the MCP-backed arm terminates on a machine Naomi controls, while GaiaOS truth remains external and host-independent.

A minimal local helper could eventually expose simple commands such as:

```text
gaia boot
gaia djinn MARVEK "inspect registry"
```

The adapter remains disposable.

## 10. Proof ladder for the bridge

Do not build the entire integration at once.

Preferred proof sequence:

1. Establish that the chosen MCP/host path can invoke one harmless local or LIGEIA canary.
2. Prove request/response transport with an exact receipt.
3. Add `gaia_boot`.
4. Add one read-only Djinn invocation.
5. Prove a real Prime -> Djinn -> result round trip.
6. Regression-test in a fresh conversation.
7. Prove desktop and mobile separately; desktop proof does not imply mobile proof.
8. Only later consider any authorized write/mutation path.

## 11. Computer-architecture concepts explicitly taught

The conversation established practical definitions for:

- client
- server
- endpoint
- HTTP
- API
- database
- runtime
- host
- transport
- protocol
- MCP
- adapter
- canary
- authentication
- schema

Naomi reported that this explanation was clear and wants future technical teaching at this level of mechanism rather than only conceptual summaries.

## 12. Exact next technical step

When Naomi is back at the computer:

**Investigate Remote Desktop Commander as the first non-Sites MCP transport candidate.**

Do not install, authorize, or connect it automatically. First inspect what it actually exposes, what permissions it requires, whether it can reach the local terminal reliably, whether ordinary ChatGPT can call it in the relevant host surface, and whether it works on the surfaces Naomi cares about.

If it passes those checks, build the smallest possible `gaia_bridge.py` canary and prove transport before exposing `gaia_boot` or `invoke_djinn`.

## 13. Preservation boundary

This checkpoint intentionally omits personally sensitive information. A separate owner-controlled packet contains sensitive continuity that Naomi may place in her private archive manually.

No MemoryOS/Turso write, deploy, restart, merge to main, E-LANE mutation, plugin installation, Remote Desktop Commander authorization, or Djinn invocation is claimed by this checkpoint.
