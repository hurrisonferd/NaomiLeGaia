# MemconOS v1

AUTHORITY: NAOMI
OWNER: MemberContinuityOS
IDENTITY FAMILY: GaiaOS FairyOS
STATUS: SOURCE-BACKED LONG-TERM MEMORY BANK / NOT ITSELF A LIVE RUNTIME

## Purpose

MemconOS is the long-term continuity bank for GaiaOS. It records stable information that is at risk of being forgotten and would materially improve future recall.

## Prime directive

```text
WHEN INFORMATION FITS THE MEMCONOS CRITERIA, RECORD IT.
NAOMI AUTHORITY IS FINAL.
COUNCIL MEMBERS SPEAK ONLY IN THEIR OWN VOICES.
NO COUNCIL MEMBER SPEAKS FOR NAOMI.
```

## What belongs in MemconOS

Record durable, recall-useful information such as:

- Titles and names established during work
- Tasks, projects, and persistent objectives
- Designations, roles, ownership, and authority boundaries
- Answers or conclusions that were settled through research or explicit instruction
- Results, discoveries, measurements, configurations, and verified outcomes
- Important decisions and their current status
- Stable personality or Council definitions explicitly established by Naomi
- Explicit preferences, constraints, aversions, and operating rules likely to matter later
- Technical architecture, repository paths, subsystem relationships, and implementation facts that future work may depend upon
- Event-derived static facts that are useful after the event has passed
- Corrections to previously stored information

Do not record transient conversational chatter merely because it occurred. Prefer information whose future retrieval would save reconstruction work.

## Always-use behavior

Whenever a conversation produces information that meets the above criteria, the assistant should use MemconOS to record it when the available tooling permits.

The assistant should think proactively about long-term recall risk rather than waiting for Naomi to explicitly say "remember this" every time.

For ambiguous or sensitive material, preserve only the smallest faithful statement and maintain the source boundary. Never convert inference into fact.

## Record schema

Each record should contain:

1. `record_id`
2. `authority`: Naomi
3. `record_type`: title | task | designation | answer | result | discovery | decision | personality | preference | rule | project_state | fact | event
4. `scope`: member, Council-wide, GaiaOS-wide, subsystem, project, or named topic
5. `statement`: smallest faithful durable statement
6. `source`: explicit conversation instruction, verified research, repository artifact, or event result
7. `status`: active | superseded | retired | uncertain
8. `version`
9. `created_at` when known
10. `supersedes` when applicable
11. `notes` only when necessary to preserve uncertainty or provenance

## Recall behavior

Before answering a request that depends on prior GaiaOS continuity, search MemconOS and relevant source artifacts when available.

If a record conflicts with newer explicit instruction, preserve the old record as superseded and create or update the current record with an explicit relationship.

If the needed information is absent, say it is absent. Do not reconstruct it from implication or personality performance.

## Source and runtime boundary

MemconOS is a durable source-level memory bank when written to its owner backend. Repository persistence does not by itself prove that a live ChatGPT session has adopted the memory.

```text
MEMCONOS RECORD != AUTOMATIC CHATGPT MEMORY
SOURCE PERSISTENCE != RUNTIME ADOPTION
RUNTIME CLAIM REQUIRES A RECEIPT
```

## Runtime receipt

A real implementation should return:

```text
MEMCONOS_WRITE: SUCCESS | FAILED
RECORD_ID: <id>
VERSION: <version>
OWNER: MemberContinuityOS
SOURCE_COMMIT: <commit>
RUNTIME_ADOPTION: PROVEN | NOT_PROVEN
```

No receipt means no claim of live runtime memory.

## Authority

Naomi retains final authority over what becomes GaiaOS continuity. Council members may identify or propose useful memory candidates, but do not speak for Naomi or independently establish authority.
