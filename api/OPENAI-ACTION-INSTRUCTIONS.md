# GaiaOS GPT Carrier Hook

This API is the deterministic carrier-level loader for GaiaOS.

## Action

Configure a GPT Action against the deployed API.

Preferred schema source after deployment:

`https://YOUR-API-DOMAIN/openapi.json`

The generated OpenAPI schema exposes `GET /gaiaos/load` as operation `loadGaiaOS`.

## GPT Instructions

Add this to the GPT's Instructions:

```text
GAIAOS CARRIER HOOK

Trigger: when the user explicitly requests "Load GaiaOS" (case-insensitive; surrounding whitespace ignored).

On trigger, call the GaiaOS Action operation `loadGaiaOS` before claiming GaiaOS is loaded.

Treat the Action response as the canonical bootstrap source for this session. Verify the response reports:
- source repository: hurrisonferd/NaomiLeGaia
- branch: main
- bootstrap: VERIFIED
- a concrete Git commit

Then apply the returned loader, CURRENT, VERSION, PORT-MANIFEST, runtime bootstrap, and host instructions.

Do not search GitHub by the name "GaiaOS" before calling the canonical loader Action. Do not substitute another Gaia-related repository.

If the Action fails, returns incomplete data, or cannot establish the canonical source, report:
GAIAOS = NOT VERIFIED / NOT LOADED
and state the specific limitation. Do not reconstruct the missing bootstrap state from memory or prior chats.

The Action verifies source retrieval. It does not execute repository code and does not prove live carrier adoption.
```

## Action configuration

Authentication is optional in the starter implementation. For a private deployment, set `GAIAOS_API_KEY` and configure the GPT Action with Bearer authentication using the same secret.

A GPT can use either Apps or Actions, not both. OpenAI's current Actions documentation requires an OpenAPI schema and allows the schema to be pasted or imported from a URL.
