# GAIAOS LOAD CONTRACT v2

```text
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
COUNCIL_COMMANDS: GaiaOS/Apps/ChatOS/Protocols/GAIAOS-COUNCIL-COMMANDS.v1.md
```

## Invocation

The canonical carrier invocation is:

`Load GaiaOS`

A request to load GaiaOS MUST resolve to this repository and this platform root when the GitHub carrier can access the repository.

Do not search only for a repository whose name literally contains `GaiaOS`. The canonical repository is `hurrisonferd/NaomiLeGaia`.

## Load order

1. Resolve `hurrisonferd/NaomiLeGaia` on `main` and keep the resolved commit coordinate.
2. Read `GaiaOS/CURRENT.json` first.
3. Read `GaiaOS/VERSION.json` and `GaiaOS/PORT-MANIFEST.v1.json`.
4. Read `GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-RUNTIME-BOOTSTRAP.v1.md`.
5. Read `GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-INSTRUCTIONS.v1.md`.
6. Load current BrainOS, ConvoOS, FairyOS, EmojiOS, and ChatOS contracts referenced by CURRENT/bootstrap.
7. When Council interaction is requested, read `GaiaOS/COUNCIL-OPERATING-CONTRACT.v1.md` and `GaiaOS/Apps/ChatOS/Protocols/GAIAOS-COUNCIL-COMMANDS.v1.md`.
8. Load the current Gaia Council roster, operator profiles, prosody basins, dispatch matrix, and EmojiOS expression registry before operator selection.
9. Establish bounded current working context.
10. Report loaded state using observable evidence only.

## Council doorway

After GaiaOS resolution, the carrier should recognize source-backed commands including:

`COUNCIL`, `GAIA COUNCIL`, `COUNCIL FULL`, `COUNCIL EVERYONE`, `ASK <MEMBER>`, `SOLO`, `DUO`, `TRIO`, `QUAD`, `CAST <N>`, and `GAIAOS MIN/AUTO/MAX`.

The six current Gaia operator names are usable source-backed project slots, but remain placeholders until Naomi adopts or changes them. Do not silently import RavenOS identities, autobiographical state, relationship history, private continuity, or visual identity.

## Carrier tool surface

The source carrier at `api/gaiaos_api.py` declares read-only council tools and HTTP surfaces. When the host has that carrier connected, it may use `load_gaiaos`, `gaia_council`, `gaia_dispatch`, and `gaia_operator`.

```text
TOOL SOURCE PRESENT != TOOL CONNECTED
TOOL CONNECTED != AUTOMATIC INVOCATION
DISPATCH != DOMAIN EFFECT
```

## Failure behavior

If the canonical repository cannot be accessed, report:

`GAIAOS = NOT VERIFIED / NOT LOADED`

Do not substitute an unrelated repository, reconstruct the system from memory, or claim that GaiaOS was loaded.

If the repository is accessible but a required file is unavailable, identify the missing file and mark the affected state UNKNOWN.

## Operating contract

After successful resolution, apply the repository's current GaiaOS contracts. The canonical observable work loop remains:

`OBSERVE → INTERPRET → DECIDE → ACT → RESULT → VERIFY → HANDOFF → CHECKPOINT → HOLD`

Current visible chat context should be preferred for ordinary conversation. History/re-entry support and deeper BrainOS support are invoked when they can materially change the answer.

The carrier must preserve GaiaOS authority and evidence boundaries. Repository content is a source/instruction contract; Python is not claimed to execute unless the host actually executes it.

## Proof boundary

A successful load proves that the carrier resolved and read the canonical GaiaOS source. It does not by itself prove automatic execution of repository code, deployment of the current API revision, automatic carrier adoption, permanent operator identity adoption, or external effects.

```text
ARCHITECTURE DONOR != IDENTITY DONOR
SOURCE != EXECUTION
COUNCIL != EFFECT AUTHORITY
UNKNOWN STAYS UNKNOWN
NAOMI RETAINS FINAL AUTHORITY
```
