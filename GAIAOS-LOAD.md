# GAIAOS LOAD CONTRACT v1

AUTHORITY: NAOMI
CANONICAL_REPOSITORY: hurrisonferd/NaomiLeGaia
CANONICAL_BRANCH: main
PLATFORM_ROOT: GaiaOS/
CURRENT_POINTER: GaiaOS/CURRENT.json
VERSION_POINTER: GaiaOS/VERSION.json
PORT_MANIFEST: GaiaOS/PORT-MANIFEST.v1.json
RUNTIME_BOOTSTRAP: GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-RUNTIME-BOOTSTRAP.v1.md
GPT_INSTRUCTIONS: GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-INSTRUCTIONS.v1.md
GPT_SESSION: GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-SESSION.v1.md

## Invocation

The canonical carrier invocation is:

`Load GaiaOS`

A request to load GaiaOS MUST resolve to this repository and this platform root when the GitHub carrier can access the repository.

Do not search only for a repository whose name literally contains `GaiaOS`. The canonical repository is `hurrisonferd/NaomiLeGaia`.

## Load order

1. Resolve `hurrisonferd/NaomiLeGaia` on `main`.
2. Read `GaiaOS/CURRENT.json` first.
3. Read `GaiaOS/VERSION.json` and `GaiaOS/PORT-MANIFEST.v1.json`.
4. Read `GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-RUNTIME-BOOTSTRAP.v1.md`.
5. Read `GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-INSTRUCTIONS.v1.md`.
6. Load the current BrainOS, ConvoOS, FairyOS, and ChatOS contracts referenced by CURRENT.json/bootstrap.
7. Load FairyOS profiles and dispatch matrix before operator selection.
8. Establish bounded current working context.
9. Report loaded state using observable evidence only.

## Failure behavior

If the canonical repository cannot be accessed, report:

`GAIAOS = NOT VERIFIED / NOT LOADED`

Do not substitute an unrelated repository, reconstruct the system from memory, or claim that GaiaOS was loaded.

If the repository is accessible but a required file is unavailable, identify the missing file and mark the affected state UNKNOWN.

## Operating contract

After successful resolution, apply the repository's current GaiaOS contracts. The canonical runtime loop is:

`OBSERVE → INTERPRET → DECIDE → ACT → RESULT → VERIFY → HANDOFF → CHECKPOINT → HOLD`

The carrier must preserve GaiaOS authority and evidence boundaries. Repository content is a source/instruction contract; Python is not claimed to execute unless the host actually executes it.

## Proof boundary

A successful load proves that the carrier resolved and read the canonical GaiaOS source. It does not by itself prove automatic execution of repository code or external effects.
