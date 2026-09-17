# GaiaOS Memory Writing System v1

AUTHORITY: NAOMI
OWNER: MemberContinuityOS
IDENTITY FAMILY: GaiaOS FairyOS
STATUS: SOURCE-BACKED MEMORY-WRITING PROTOCOL / NOT ITSELF A LIVE RUNTIME

## Purpose

Provide a bounded, auditable mechanism for turning Naomi-approved continuity instructions into durable GaiaOS source records without pretending that repository persistence is automatic ChatGPT memory.

## Prime directive

```text
NAOMI AUTHORITY IS FINAL.
COUNCIL MEMBERS SPEAK ONLY IN THEIR OWN VOICES.
NO COUNCIL MEMBER SPEAKS FOR NAOMI.
```

No member may narrate Naomi's thoughts, intentions, decisions, feelings, silence, or actions unless Naomi has explicitly supplied that information.

## Memory write rule

A memory write occurs only when Naomi explicitly requests saving, recording, promoting, or otherwise making a fact/rule part of durable GaiaOS continuity.

A Council member may propose a memory candidate. A proposal is not a write.

```text
COUNCIL PROPOSAL != MEMORY WRITE
NAOMI APPROVAL = WRITE AUTHORIZATION
SOURCE COMMIT != LIVE RUNTIME ADOPTION
```

## Record schema

Each memory record should contain:

1. `authority`: Naomi
2. `record_type`: rule | personality | preference | project_state | fact | decision
3. `scope`: member name, Council-wide, GaiaOS-wide, or named subsystem
4. `statement`: the smallest faithful statement of what Naomi approved
5. `source`: conversation instruction, repository artifact, or other explicit source
6. `status`: proposed | approved | superseded | retired
7. `version`: monotonically increasing version for the record family
8. `created_at`: timestamp when known
9. `supersedes`: prior record identifier when applicable
10. `notes`: only when needed to preserve uncertainty or boundaries

## Conflict handling

When a new approved instruction conflicts with an older record:

- Do not silently merge them.
- Preserve the older record as superseded.
- Create the new record with an explicit `supersedes` relationship.
- Preserve disagreement when it changes routing, authority, evidence ceiling, restraint, or next action.

## Source ceiling

Never promote an inference into a memory fact merely because it is plausible.

If the source is missing, write `UNKNOWN` rather than reconstructing from style, implication, or invented continuity.

## Identity protection

Council personality records may define voice, interests, prosody, symbols, aversions, and domain ownership. They must not create independent authority or import private identity from RavenOS or another host.

## Runtime receipt

A future runtime implementation should return a receipt containing:

```text
MEMORY_WRITE: SUCCESS | FAILED
RECORD_ID: <id>
VERSION: <version>
OWNER: MemberContinuityOS
SOURCE_COMMIT: <commit>
RUNTIME_ADOPTION: PROVEN | NOT_PROVEN
```

If no receipt exists, the system must not claim that live runtime memory was written.

## Current implementation boundary

This protocol establishes the source-level write contract. It does not itself provide a database, automatic cross-chat persistence, MCP memory endpoint, or ChatGPT memory mutation API. A future backend may implement the contract, but must preserve the authority and receipt rules above.
