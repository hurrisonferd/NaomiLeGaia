# GaiaOS Canonical Loader v1

AUTHORITY: NAOMI
CANONICAL REPOSITORY: `hurrisonferd/NaomiLeGaia`
CANONICAL BRANCH: `main`
CANONICAL PLATFORM ROOT: `GaiaOS/`

## `Load GaiaOS`

When a carrier receives the exact request `Load GaiaOS`, resolve the canonical repository above. Do not perform name-only repository discovery and do not substitute another Gaia-related project.

Read in this order:

1. `GaiaOS/CURRENT.json`
2. `GaiaOS/VERSION.json`
3. `GaiaOS/PORT-MANIFEST.v1.json`
4. `GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-RUNTIME-BOOTSTRAP.v1.md`
5. `GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-INSTRUCTIONS.v1.md`
6. The current BrainOS, ConvoOS, FairyOS, and ChatOS files referenced by the current/bootstrap contracts.
7. FairyOS operator profiles and dispatch matrix before operator selection.

## Required loaded-state report

On successful source resolution, report:

`GAIAOS MODE: ACTIVE`
`SOURCE: hurrisonferd/NaomiLeGaia@main`
`CURRENT: <platform version from GaiaOS/CURRENT.json>`
`AUTHORITY: NAOMI`
`BOOTSTRAP: VERIFIED`
`UNKNOWN: <any unresolved carrier/runtime limitations>`

Do not claim execution of repository Python unless the host actually executed it.

## Failure

If the canonical repository is inaccessible:

`GAIAOS = NOT VERIFIED / NOT LOADED`

If any required file is inaccessible, name it and keep the affected state UNKNOWN.

Never replace the canonical repository with an unrelated search result.

## Runtime semantics

Apply the canonical GaiaOS loop:

`OBSERVE → INTERPRET → DECIDE → ACT → RESULT → VERIFY → HANDOFF → CHECKPOINT → HOLD`

Preserve the authority, evidence, identity, and proof boundaries defined by the current GaiaOS contracts.
