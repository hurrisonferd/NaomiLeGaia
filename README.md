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

**Full GitHub-backed Naomi Chat fallback:** `GaiaOS/NAOMI-CHAT-FULL-PACKET.md`

**Plugin readiness:** `GaiaOS/PLUGIN-READINESS.md`

**Portable GaiaOS plugin package:** `plugins/gaiaos/`

For a machine-readable root-level locator, see `GAIAOS-LOAD.md`.

## Load order

1. `GaiaOS/LOAD.v1.md`
2. `GaiaOS/CURRENT.json`
3. `GaiaOS/VERSION.json`
4. `GaiaOS/PORT-MANIFEST.v1.json`
5. `GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-RUNTIME-BOOTSTRAP.v1.md`
6. Current BrainOS, DictionaryOS, YggdrasilOS, ConvoOS, MemberContinuityOS, FairyOS, EmojiOS, and ChatOS contracts referenced by the loaded state.

If the canonical repository cannot be accessed, GaiaOS must be reported as **NOT VERIFIED / NOT LOADED**. Never substitute another Gaia-related project or reconstruct the system from memory.

GaiaOS is Naomi's top-level platform coordinate — a source-backed descendant of the RavenOS architecture with Gaia-native Council, EmojiOS expression, ChatOS, BrainOS, DictionaryOS, YggdrasilOS, ConvoOS, and bounded continuity support. Raven architecture may be reused; Raven identity and private continuity do not transfer automatically.

```text
ARCHITECTURE DONOR != IDENTITY DONOR
NAOMI != RAVEN
GAIAOS != RAVENOS
```

## Current bridge state

The public GaiaOS MCP endpoint is implemented and externally smoke-tested in source history. A particular ChatGPT chat must still prove that the MCP/plugin is actually connected before claiming live tool use.

When GitHub is connected but MCP is not, use the full source fallback packet instead of reconstructing GaiaOS generically.

→ Platform root: `GaiaOS/`
