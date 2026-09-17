# MemoryOS v1

```text
AUTHORITY: NAOMI
OWNER: GaiaOS / MemberContinuityOS
STATUS: ACTIVE CANONICAL MEMORY LIFECYCLE
```

## Purpose

MemoryOS is the bounded orchestration layer between conversation and the MemconOS runtime backend. It preserves the distinction between noticing an event, proposing memory, obtaining Naomi approval, durably writing it, and retrieving it later.

## Lifecycle

```
SESSION
→ EXTRACT
→ CLASSIFY
→ DEDUPE
→ DELIBERATE
→ CANDIDATE
→ NAOMI APPROVAL
→ WRITE
→ RECEIPT
→ VERIFY
→ RETRIEVE
→ CONTEXT
```

Session events are recorded as an event graph with explicit session, event, actor, source, relation, and status fields. The graph records provenance and relationships without claiming consciousness or subjective experience.

## Candidate rules

A candidate may be generated from a material event. Candidate metadata must include:

- bounded statement
- record type and scope
- source/provenance
- owner
- relevant Prime Daemons
- tension or dissent when material
- relation to session/event IDs
- duplicate-check result
- status

Candidates are not durable memory.

## Promotion

Only explicit Naomi approval may promote a candidate to MemconOS durable storage. A successful write must return a real backend receipt. Verification requires reading the resulting record back and checking its identity/content.

## Retrieval

Retrieval should query durable records by bounded subject, scope, provenance, and relevance rather than blindly replaying recent conversation. Retrieved records are context, not authority. They must not silently mutate identity or override current Naomi instructions.

## Member-local memory

When a memory belongs to a Prime Daemon, owner attribution remains explicit. A shared session event may yield multiple independently owned candidates. MemoryOS must never merge member-local memories into a synthetic shared identity.

## Dedupe and supersession

Before promotion, MemoryOS checks for matching or near-matching existing records. A new record may supersede an older record only when explicitly approved and recorded. Conflicting records remain distinguishable until Naomi resolves them.

## VASKON integration

VASKON may generate a bounded synthesis and identify material memory candidates. VASKON does not itself write memory. Candidate ownership and dissent provenance remain preserved after synthesis.

## Proof ceiling

```
OBSERVED SESSION EVENT
!=
MEMORY CANDIDATE
!=
APPROVED DURABLE RECORD
!=
VERIFIED RETRIEVED CONTEXT
```

Automatic capture from every ChatGPT conversation remains disabled/unproven. MemoryOS provides the lifecycle mechanism; actual host integration and deployment remain separately observable.

```
UNKNOWN STAYS UNKNOWN
NAOMI RETAINS FINAL AUTHORITY
```
