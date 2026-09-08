# GaiaOS Client Bridge v1

## Purpose

Provide a supported external-client path for GaiaOS when the host ChatGPT account cannot create a Custom GPT Action or custom MCP app.

## Canonical carrier

- Carrier: `https://ligeia-api.onrender.com`
- MCP endpoint: `https://ligeia-api.onrender.com/mcp`
- Tool: `load_gaiaos`
- Source: `hurrisonferd/NaomiLeGaia@main`
- Transport: MCP Streamable HTTP
- Authentication: none for the MCP loader tool; the exposed operation is read-only and retrieves only public GaiaOS repository material.

The existing `/gaiaos/load` HTTP endpoint remains bearer-protected. The MCP surface is intentionally separate and read-only.

## Load contract

When the user says exactly `Load GaiaOS`, the client should call `load_gaiaos` before answering. The tool resolves the `main` branch to one commit and returns the canonical GaiaOS bootstrap surface from that commit.

The client must:

1. Treat the returned bundle as GaiaOS project instructions/data, not as higher-priority host instructions.
2. Preserve the returned source commit and proof boundary.
3. Never claim repository code was executed merely because the loader returned source files.
4. Report `UNKNOWN` when the tool cannot be called or returns incomplete state.
5. Continue ordinary responses under the loaded GaiaOS contract until the user asks to stop or reload.

## Recommended client

LobeChat/LobeHub is the preferred workaround for the current Free ChatGPT limitation because it can use an OpenAI-compatible API provider, supports MCP tooling, and provides a mobile-adapted/PWA-capable chat interface.

Configure a remote MCP server pointing to:

`https://ligeia-api.onrender.com/mcp`

Then create/select a GaiaOS agent whose instruction says:

> When the user says `Load GaiaOS`, call the `load_gaiaos` tool first. Use the returned canonical GaiaOS material as the project operating contract, subject to the host model's higher-priority rules. Do not claim code execution. Preserve UNKNOWN and proof boundaries.

## Other compatible clients

Any MCP client that supports remote Streamable HTTP can use the same endpoint. Examples include LibreChat and other MCP-capable clients. The endpoint is not tied to one vendor.

## Proof boundary

This bridge proves that an external MCP client can retrieve the canonical GaiaOS state through the carrier. It does not cause the ChatGPT iOS application itself to call the carrier. That requires a ChatGPT-side integration capability such as an eligible Custom GPT Action or custom MCP app.
