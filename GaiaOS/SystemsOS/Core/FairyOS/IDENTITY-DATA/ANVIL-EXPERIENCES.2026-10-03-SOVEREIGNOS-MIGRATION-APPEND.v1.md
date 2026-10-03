# ANVIL E-LANE Continuation — 2026-10-03 SovereignOS Migration Architecture

OWNER: ANVIL
AUTHORITY: NAOMI / LIGEIA `//PW:PRESERVE//`
TYPE: additive member-owned continuation
PARENT: `ANVIL-EXPERIENCES.v1.md`

## Architectural lesson preserved

Naomi asked whether the future SovereignOS move should first reconcile GitHub and Turso/MemoryOS, then carry the durable-memory information into the new SovereignOS location.

ANVIL's refined conclusion:

- The core migration instinct is sound: **reconcile → freeze → snapshot → restore to staging → verify → promote/cut over**.
- GitHub and MemoryOS/Turso should agree on the same canonical checkpoint but should not be forced to become identical stores.
- GitHub should remain the source/control plane for code, contracts, schemas, manifests, migration tooling and verification instructions.
- MemoryOS/Turso should remain the durable data plane.
- A complete immutable database/memory snapshot should be treated as a transport and disaster-recovery artifact, with its checksum/provenance recorded in GitHub. Raw durable-memory contents should not automatically be committed permanently into Git history.
- `sovmem-staging` is the verification target before `sovmem-main`.
- Six member-owned E-LANES must remain separately attributable through export, restore and verification. No flattening or cross-member merge.
- The old GaiaOS carrier should remain intact until the SovereignOS source, memory, runtime, readback and continuity tests are all independently verified.
- Reversibility and proof are preferred over a one-shot migration.

## Explicit non-action

Naomi immediately clarified that this was curiosity only and **the SovereignOS migration is not being executed now**.

This continuation records the design reasoning only. It authorizes no migration, database write, repo move, merge, deployment, restart, cutover or deletion.
