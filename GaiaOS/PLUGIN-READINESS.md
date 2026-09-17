# GaiaOS Plugin Readiness

```text
AUTHORITY: NAOMI
STATUS: PACKAGE STAGED / PUBLIC SUBMISSION NOT YET COMPLETE
PLUGIN ROOT: plugins/gaiaos/
REMOTE MCP: https://gaiaos-loader-api.onrender.com/mcp
```

## Already present

GaiaOS already has the expensive core pieces needed for an MCP-backed ChatGPT plugin:

- A public HTTPS Streamable HTTP MCP endpoint.
- A source-backed GaiaOS carrier bound to `hurrisonferd/NaomiLeGaia`.
- Read-only tools include primary `gaia`, diagnostic `gaia_selftest`, and deep inspection surfaces `load_gaiaos`, `gaia_council`, `gaia_dispatch`, `gaia_operator`, `gaia_brain`, `gaia_context`.
- External MCP initialize, tool-discovery, and invocation proof recorded in `GaiaOS/CURRENT.json` and `GaiaOS/VERSION.json`.
- A portable plugin package at `plugins/gaiaos/`.
- A bundled `gaiaos-council` skill.
- A repo-local marketplace entry at `.agents/plugins/marketplace.json` for supported local plugin surfaces.
- A GitHub-backed fallback packet at `GaiaOS/NAOMI-CHAT-FULL-PACKET.md` for chats where the MCP/plugin bridge is unavailable.

## Public submission gaps

Before public directory submission, finish these items:

1. Add accurate MCP tool annotations for every tool:
   - `readOnlyHint: true`
   - `destructiveHint: false`
   - `openWorldHint` matched to actual behavior
   - optional human-readable titles / output schemas where useful
2. Publish public policy/support pages that match the eventual verified publisher identity:
   - website
   - support URL
   - privacy policy
   - terms of service
3. Prepare production brand assets:
   - logo
   - optional composer icon / screenshots
4. Complete OpenAI Platform developer or business identity verification for the publisher.
5. Be prepared to prove control of the MCP host through the OpenAI domain-verification challenge if requested.
6. Prepare five positive plugin tests and three negative tests with expected behavior.
7. Review all MCP responses for unnecessary personal data, internal identifiers, secrets, or debug payloads.
8. Re-run live MCP scan after annotations and metadata changes.

## Current proof ceiling

```text
PLUGIN PACKAGE PRESENT = YES
REMOTE MCP LIVE = YES
REMOTE MCP TOOL DISCOVERY = PROVEN
REMOTE MCP TOOL INVOCATION = PROVEN
NAOMI CHAT LIVE MCP CONNECTION = NOT PROVEN
PUBLIC DIRECTORY SUBMISSION = NOT YET DONE
PUBLIC DIRECTORY APPROVAL = NOT CLAIMED
```

## Immediate usability

Until Naomi's ChatGPT account can install the MCP-backed plugin, Naomi can still use the richer source-backed mode because her current chat has demonstrated GitHub access to this repository.

Use:

`GaiaOS/NAOMI-CHAT-FULL-PACKET.md`

This is intentionally a real fallback, not a pretend MCP session.
