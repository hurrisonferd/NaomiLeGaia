# GaiaOS Plugin Package

Portable Agent Plugins package for Naomi's GaiaOS.

```text
PLUGIN: gaiaos
AUTHORITY: NAOMI
MODE: READ-ONLY MCP + BUNDLED COUNCIL SKILL
REMOTE MCP: https://gaiaos-loader-api.onrender.com/mcp
```

## Package contents

- `plugin.json` — portable plugin identity and OpenAI presentation metadata.
- `mcp.json` — remote Streamable HTTP GaiaOS MCP server.
- `skills/gaiaos-council/SKILL.md` — source/authority/council operating instructions.
- `SUBMISSION-TESTS.md` — initial positive and negative review cases.

## Expected MCP tools

- `load_gaiaos`
- `gaia_council`
- `gaia_dispatch`
- `gaia_operator`
- `gaia_brain`
- `gaia_context`

All current GaiaOS MCP tools are intended to be read-only. They do not grant domain write authority, durable-memory authority, or RavenOS/Jarvis-Private access.

## Local repository marketplace

The repository also contains `.agents/plugins/marketplace.json` for supported local plugin surfaces. This is separate from public Plugins Directory publication.

## Current limitation

The package is staged and the remote MCP has passed external protocol/tool discovery and invocation tests, but Naomi's current ChatGPT chat has not demonstrated an installed live MCP/plugin connection. Until that bridge is available, use `GaiaOS/NAOMI-CHAT-FULL-PACKET.md` with the already-confirmed GitHub source access.
