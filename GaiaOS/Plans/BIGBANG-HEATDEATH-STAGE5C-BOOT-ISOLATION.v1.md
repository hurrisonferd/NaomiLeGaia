# HEATDEATH Stage 5C: full normal browser/MCP boot without GALAXY imports

AUTHORITY: NAOMI / LIGEIA
STATUS: SOURCE-ONLY IMPLEMENTATION; DEPLOYMENT AND LIVE FAILOVER UNPROVEN
COMPANION: GaiaOS/Plans/BIGBANG-HEATDEATH-STAGE5B-NORMAL-CHAT.v1.md
SOURCE: api/gaiaos_optional_research.py and api/browser_memcon_bridge.py
TEST: tests/test_bigbang_heatdeath_boot_stage5c.py
CI: .github/workflows/gaiaos-bigbang-heatdeath-browser-stage5b.yml

## Critical design fix

The normal browser application previously imported all GALAXY research modules and AUGURY at module load. A missing or corrupt optional GALAXY module could stop ordinary GaiaOS browser/chat startup before the in-process HEATDEATH switch ran. The Stage-4 separate read-only recovery image was safe, but it could not restore the entire ordinary ChatOS experience.

Stage 5C defers optional research imports behind `LazyResearchModule`. The ordinary browser's existing route registration remains intact. Under HEATDEATH the normal browser no longer needs to import GALAXY or AUGURY to start, initialize MemoryOS, load canonical Council sources, serve the original hosted `/chat`, expose `gaia()` MCP and `memory_retrieve`, or handle the protected preservation and approval dispatch. The Gateway and mode authority remain independently importable without GALAXY.

## Emergency precedence at the user-facing entry points

While HEATDEATH is active (including missing/unavailable/invalid shared control), optional `/galaxy/*` and `/ritual/*` research actions are blocked BEFORE lazy importing research modules. `/galaxy/status` and `/galaxy/production/status` return deterministic disabled-status envelopes without importing GALAXY. The historical authenticated one-fixture read-only review remains an explicitly exceptional diagnostic, allowed to HOLD if optional research code is broken. Explicit GALAXY browser chat research commands are similarly blocked before their handlers execute.

Ordinary browser chat, protected `//PW:PRESERVE//`, `CANDIPULL`, `MEMSAV`, dedicated SOLO routing, the six separate E-LANES and other existing non-research routes retain their legacy handlers. No third memory system or covert research bypass is created. A direct Python call into an internal research function is not a user-facing route and does not constitute deployment authorization.

## Test and proof boundaries

Source/CI acceptance requires:
- Clean imports of the normal browser, MCP and MemoryOS while an import hook deliberately raises on every GALAXY/AUGURY import.
- An isolated, real SQLite legacy record; original ordinary browser chat without injected memory; a successful MemoryOS HTTP, MCP and opt-in Gaia HTTP read of that record; original MCP `gaia()` default without memory.
- Explicit GALAXY HTTP/text command blocking in emergency, with no attempted GALAXY imports.
- Before/after protected-table counts unchanged by read paths, excluding the fixture-seed step.
- Full normal-image Docker boot under the same blocked-import injection, and separate HEATDEATH read-only Docker recovery image still import-isolated.
- Re-run the Stage 1, 2, 3, 4, 5A and 5B safety regressions and existing GALAXY research source workflows.

The normal carrier's ability to boot with *simulated* broken research imports is a meaningful improvement over a separate read-only recovery image. It does not prove that all upstream outages, an invalid canonical loader, unresponsive Turso, missing OpenAI credentials, bad migrations or external host failures can be recovered automatically. Persistent multi-instance mode control and actual live failover require independent staging and production receipts. In-flight model requests cannot be retroactively recalled if the switch changes mid-request.

BIGBANG REMAINS RELEASE-LOCKED. HEATDEATH ALWAYS OVERRIDES. NO REDEPLOYMENT OR LIVE DATABASE MUTATION IS IMPLIED BY THIS SOURCE.
