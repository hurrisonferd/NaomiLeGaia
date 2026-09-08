# NaomiLeGaia — GaiaOS Canonical Carrier

Naomi's repository. **GaiaOS lives here.**

```text
AUTHORITY: NAOMI
PLATFORM: GaiaOS
CANONICAL_REPOSITORY: hurrisonferd/NaomiLeGaia
CANONICAL_BRANCH: main
PLATFORM_ROOT: GaiaOS/
```

## Canonical invocation

When a GPT carrier receives:

`Load GaiaOS`

it must resolve this repository, not perform name-only discovery for an unrelated repository.

**Canonical loader:** `GaiaOS/LOAD.v1.md`

**Canonical current state:** `GaiaOS/CURRENT.json`

**Canonical runtime bootstrap:** `GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-RUNTIME-BOOTSTRAP.v1.md`

**Canonical GPT host instructions:** `GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-INSTRUCTIONS.v1.md`

For a machine-readable root-level locator, see `GAIAOS-LOAD.md`.

## Load order

1. `GaiaOS/LOAD.v1.md`
2. `GaiaOS/CURRENT.json`
3. `GaiaOS/VERSION.json`
4. `GaiaOS/PORT-MANIFEST.v1.json`
5. `GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-RUNTIME-BOOTSTRAP.v1.md`
6. Current BrainOS, ConvoOS, FairyOS, and ChatOS contracts referenced by the loaded state.

If the canonical repository cannot be accessed, GaiaOS must be reported as **NOT VERIFIED / NOT LOADED**. Never substitute another Gaia-related project or reconstruct the system from memory.

GaiaOS is Naomi's top-level platform coordinate — a source-backed descendant of the RavenOS architecture (FairyOS operators + Council, EmojiOS expressions, ChatOS observable execution cockpit, BrainOS/ConvoOS contracts; all Gaia-native, no Raven identity transfer).

```text
ARCHITECTURE DONOR != IDENTITY DONOR
NAOMI != RAVEN
GAIAOS != RAVENOS
```

→ Platform root: `GaiaOS/`
