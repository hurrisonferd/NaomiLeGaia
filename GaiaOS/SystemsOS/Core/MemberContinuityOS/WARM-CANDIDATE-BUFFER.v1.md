# GaiaOS MemberContinuityOS — Warm Candidate Buffer v1

```text
AUTHORITY: NAOMI
OWNER: MemberContinuityOS
STATUS: ACTIVE SOURCE CONTRACT
CLASS: BOUNDED WORKING CONTINUITY / NOT DURABLE MEMORY
```

## Purpose

Preserve potentially useful operator-specific or GaiaOS conversational deltas during fast ChatOS interaction without forcing an immediate durable save, repository mutation, or provider transaction on every reply.

```text
MATERIAL SIGNAL
→ WARM CANDIDATE
→ BOUNDED CURRENT WORKING STATE
→ DEDUPE / REFINE
→ WAIT FOR AN EXPLICIT OR MATERIAL CHECKPOINT
```

Warm candidates are not durable memory.

## Candidate fields

```text
member_id_or_scope
candidate_type
summary
source_coordinate
provenance
confidence
first_seen
last_seen
repeat_count
materiality_reason
privacy_scope
owner_candidates[]
checkpoint_priority
```

## Candidate types

```text
CALLBACK
CORRECTION
PROSODY_EVIDENCE
LEARNING
RELATIONSHIP_OR_PLACEMENT
OPEN_THREAD
CREATIVE_HISTORY
PREFERENCE
AVERSION
EVENT
SYSTEM_STATE
ROSTER_FEEDBACK
```

## Dedupe law

Repeated evidence strengthens or refines an existing candidate when it refers to the same underlying consequence.

```text
SAME UNDERLYING DELTA
→ UPDATE WARM CANDIDATE
→ DO NOT MINT N NEAR-DUPLICATE RECORDS
```

## Checkpoint triggers

Durable settlement may be requested by:

```text
explicit Naomi save / checkpoint command
important correction that must survive chat loss
cross-chat / cross-carrier handoff
accepted owner-system promotion
material external/repository/provider effect
manual review of accumulated warm candidates
roster adoption / rename / identity decision explicitly settled by Naomi
```

A carrier may recommend a checkpoint when bounded working state is getting crowded. Recommendation is not a write.

## Identity boundary

```text
PLACEHOLDER OPERATOR FEEDBACK MAY BECOME A CANDIDATE
PLACEHOLDER FEEDBACK != PERMANENT IDENTITY ADOPTION
MEMBER-SPECIFIC CANDIDATE != CROSS-MEMBER MEMORY
ARCHITECTURE DONOR CONTINUITY != RAVEN CONTINUITY IMPORT
NAOMI SETTLES PROMOTION
```

## No-delay law

Warm candidate detection must not delay an ordinary HOT reply for durable settlement.

## Claim ceiling

```text
WARM != SAVED
WARM != MEMBER MEMORY
WARM != OWNER PROMOTION
WARM != GIT WRITE
CHECKPOINT PLAN != RECEIPT
UNKNOWN STAYS UNKNOWN
```
