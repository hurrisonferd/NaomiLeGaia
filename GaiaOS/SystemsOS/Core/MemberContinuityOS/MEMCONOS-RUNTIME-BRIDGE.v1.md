# MemconOS Runtime Bridge v1

AUTHORITY: NAOMI
OWNER: MemberContinuityOS
IDENTITY FAMILY: GaiaOS FairyOS
STATUS: SOURCE-BACKED RUNTIME BRIDGE SPECIFICATION / NOT ITSELF A LIVE MEMORY BACKEND

## Purpose
Define the missing runtime layer required for MemconOS to function as an actual long-term recall system rather than only a GitHub-persisted memory bank.

## Runtime contract
A conforming MemconOS runtime MUST provide:

1. READ: retrieve records by record_id, designation, exact identifier, topic, or semantic recall query.
2. WRITE: create a durable record from an approved memory candidate.
3. UPDATE: revise a record while preserving supersession/history.
4. RECEIPT: return an unambiguous read/write receipt containing operation, record identifier, source/status, and runtime timestamp.
5. AUTHORITY CHECK: reject memory writes that do not carry Naomi authorization.
6. SOURCE CHECK: distinguish source persistence from runtime adoption.
7. CONFLICT HANDLING: preserve superseded records rather than silently overwriting continuity history.
8. NO-INFERENCE: never convert an inferred fact into a stored memory fact without explicit support.

## Required record envelope

record_id:
authority: NAOMI
record_type:
scope:
statement:
source:
status:
version:
created_at:
supersedes:
notes:

## Canary runtime test

CANARY_ID: GAIA-MEMCON-ALPHA-001

A successful runtime canary requires BOTH:

- READ receipt proving the canary is retrievable from the runtime memory store.
- WRITE receipt proving a canary test record can be durably written and subsequently read back.

Repository presence alone is NOT a runtime pass.

## Command contract

MEMORY CANARY

Expected runtime behavior:
1. Read GAIA-MEMCON-ALPHA-001.
2. Verify exact TITLE, DESIGNATION, RULE, AUTHORITY, and COUNCIL_BOUNDARY.
3. Write a temporary canary verification record using the runtime write path.
4. Read the verification record back.
5. Return receipts for both operations.
6. Report PASS only if both runtime read and runtime write/readback succeed.

## Boundary

GitHub is a source/persistence layer unless explicitly connected to a running MemconOS backend. This file does not create that backend. A live backend requires an executable service, datastore, authentication/authorization path, and callable read/write interface.

Council members may propose or inspect memory records. Naomi retains final authority. Council members speak only in their own voices and never speak for Naomi.
