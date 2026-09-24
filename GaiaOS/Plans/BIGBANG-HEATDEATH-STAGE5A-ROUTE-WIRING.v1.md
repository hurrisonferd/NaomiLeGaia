# BIGBANG / HEATDEATH Stage 5A: real front door and MemoryOS read routing

AUTHORITY: NAOMI / LIGEIA
STATUS: SOURCE-ONLY IMPLEMENTATION CANDIDATE / NOT DEPLOYED
BASE: main@23fd9cfc0fffe8a9af47abfd79e375be7629da29
REGRESSION: tests/test_bigbang_heatdeath_routes_stage5a.py
PREDECESSORS: Stage 1 baseline, Stage 2 persistent control, Stage 3 gateway, Stage 4 separate legacy recovery image.

## Actual route wiring

- Primary `gaia()` MCP front door and authenticated `/gaiaos/assist` invoke `gaiaos_memory_gateway.read()` for eligible memory requests.
- In HEATDEATH the original front-door default remains *no implicit memory retrieval*, exactly as before GALAXY opt-in.
- BIGBANG's **future, explicit-owner-authorized** release-gated mode will select automatic memory retrieval for ordinary `gaia()` requests; `include_memory=false` always opts out.
- `include_memory=true` is available in either mode, using the one gateway and native legacy records, rather than importing the older GALAXY-owned `preview` function. Its `memory_context` response now carries the versioned `gaiaos.memory-gateway.v1` contract with separate `retrieval` and `galaxy_context`. This is an explicit opt-in response-format change, not a third mode.
- Fix the previously unbound `include_memory` and `memory_query` references in public `gaia()`.
- The deployed-checkout `GAIAOS-MEMORY.v1.py.retrieve()` uses the same gateway. Existing HTTP `/memoryos/retrieve`, MCP `memory_retrieve` and bootstrap readers consequently share identical source routing without touching promotion or candidate writers. The previous `retrieval` field stays the native record envelope, while `memory_gateway` and `galaxy_context` are additional read-only fields.
- Production `api/Dockerfile` now contains `legacy_memory_reader.py`, `gaiaos_memory_mode.py` and `gaiaos_memory_gateway.py`, so this route can actually import its dependencies when deployed.

## Stage limits and safety

The existing `browser_memcon_bridge.py` still intercepts ordinary `/chat` and hands it to `gaiaos_api.chat` without per-turn gateway recall. That integration is **Stage 5B**, separately tested before any ordinary GALAXY adoption claim. The normal browser carrier also retains startup GALAXY imports, unlike the separately built Stage-4 emergency recovery image. No generalized operational GALAXY module has been merged from the old diverged branch; the Stage-2 owner-approved BIGBANG activation writer does not yet exist.

HEATDEATH still has only the current authoritative memory records, unchanged write/approval controls and six separate E-LANES. Mode-control failure yields HEATDEATH, not an inferred user authorization. Errors in native legacy storage produce a HOLD, not invented memories. Tests simulate future BIGBANG selection only with injected mode decisions, never production writes.

Do not deploy on Stage 5A alone; complete Stage 5B normal browser chat source tests, normal-app startup and independent recovery checks, reconcile actual GALAXY operational code, and obtain Naomi's separate release approval and real carrier verification. Source CI is never live deployment proof.
