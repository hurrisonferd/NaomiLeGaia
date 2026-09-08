# GaiaOS ↔ GPT Integration Surface

The GPT integration consists of three layers:

1. `GAIAOS-GPT-RUNTIME-BOOTSTRAP.v1.md` — canonical runtime contract.
2. `GAIAOS-GPT-INSTRUCTIONS.v1.md` — compact host-instruction profile suitable for a Custom GPT or equivalent instruction field.
3. `GAIAOS-GPT-SESSION.v1.md` — operational procedure for starting, running, verifying, and handing off a GaiaOS session.

These documents intentionally do not claim that GPT executes repository Python automatically. The host must either apply the contracts behaviorally or provide an execution environment for the runtime code.

Canonical runtime implementations remain in:

- `GaiaOS/SystemsOS/Core/FairyOS/Runtime/GAIAOS-DISPATCH-RESOLVER.v1.py`
- `GaiaOS/Apps/ChatOS/Runtime/CHATOS-EVENT-COMPILER.v1.py`

The GPT-facing layer consumes their declared semantics and uses their outputs as evidence only when those runtimes are actually executed.

## Recommended carrier setup

For a Custom GPT or other instruction-capable GPT surface, copy the contents of `GAIAOS-GPT-INSTRUCTIONS.v1.md` into the host's instruction field and provide this repository as the authoritative knowledge/source surface where supported.

For a tool-enabled runtime, additionally expose repository reads and the appropriate execution/tool interfaces. Do not grant ChatOS domain-effect authority merely because it can observe or dispatch.

## Adoption test

A carrier should be considered GaiaOS-adopting only after observable tests demonstrate:

- current-coordinate loading;
- bounded ConvoOS working-state behavior;
- deterministic FairyOS routing;
- explicit-member honoring;
- unknown-signal preservation;
- evidence-aware ChatOS claims;
- separation of presentation from external effects;
- no fabricated provider results;
- conflict reporting rather than silent reconciliation.

Passing repository canaries alone is insufficient to prove carrier adoption.
