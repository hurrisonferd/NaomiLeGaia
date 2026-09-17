# GaiaOS Wave 8 FastMCP startup repair

```text
AUTHORITY: NAOMI
STATUS: SOURCE_REPAIRED / CI_AND_LIVE_REDEPLOY_PENDING
REPAIR_COMMIT: 0b3a2e7136d0747435b14fbb5c840eaa7b563218
FAILED_RENDER_DEPLOY: dep-dalkecu1egvs73etrbdg
FAILED_DEPLOY_SOURCE: 7d689855fed942f3cab6e3af525a47f853a8d9e5
```

## Failure observed

Render successfully built the Wave 8 carrier but the new instance failed during application import with:

`AttributeError: property 'instructions' of 'FastMCP' object has no setter`

The existing healthy GaiaOS instance remained live.

## Repair

FastMCP 1.30 accepts server instructions at `FastMCP(...)` construction and exposes `instructions` as read-only afterward.

The repair therefore:

- moves GaiaOS `PRIMARY FRONT DOOR` host guidance into the `FastMCP(...)` constructor in `api/gaiaos_api.py`;
- removes the illegal `mcp.instructions = ...` assignment from `api/gaiaos_app.py`;
- preserves carrier 1.6.0, `gaia()`, `gaia_selftest()`, the Wave 8 single-front-door policy, and all prior proof boundaries;
- passed Python compilation for both carrier modules before source commit.

## Proof ceiling

```text
SOURCE REPAIR != LIVE REDEPLOY
COMPILE PASS != RUNTIME STARTUP PASS
OLD HEALTHY INSTANCE REMAINED LIVE
NEXT REQUIRED: NORMAL GAIAOS CANARY -> RENDER REDEPLOY -> EXTERNAL HTTP/MCP FRONT-DOOR ACCEPTANCE
```
