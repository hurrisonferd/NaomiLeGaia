# BIGBANG / HEATDEATH Stage 3: independent unified memory read gateway

AUTHORITY: NAOMI / LIGEIA
STATUS: SOURCE-ONLY GATEWAY / BIGBANG REMAINS LOCKED / ORDINARY ROUTES NOT YET WIRED
PREDECESSOR: GaiaOS/Plans/BIGBANG-HEATDEATH-LEGACY-BASELINE.v1.md
CORE: api/gaiaos_memory_gateway.py
MODE AUTHORITY: api/gaiaos_memory_mode.py
INDEPENDENT LEGACY: api/legacy_memory_reader.py
BASELINE: legacy/source-snapshot-pre-bigbang-20260924
RELEASE: NONE. No Render deployment or production database mutation is authorized by this source.

## One stable gateway, two operating modes

The gateway returns `gaiaos.memory-gateway.v1` and reads the Stage-2 shared mode status on **every request**. It verifies and retains an unmodified native `memcon_runtime.search_records` envelope under `retrieval`, including record order, existing scope behavior, term filtering, historical visibility, and existing write/approval boundaries. It never imports GALAXY before an authorized BIGBANG decision. HEATDEATH returns the original legacy evidence immediately with `galaxy_context=null` and `galaxy_applied=false`.

BIGBANG is intentionally **not executable yet** because the Stage-2 mode authority always returns `bigbang_activation_enabled=false`. When a separately authorized and verified later stage permits BIGBANG, the gateway can lazily call `galaxy_frontdoor_context.operational` for nonempty MemoryOS queries. It validates exact read-only schema, provenance, governing-state and candidate/graph context boundaries before exposing that optional enhancement in a separate `galaxy_context` field. GALAXY cannot rewrite legacy results, silently join non-MemoryOS E-LANES, confer identity authority, trigger capture/promotion or delete history. A safe semantic no-match stays an explicit GALAXY HOLD, never becomes an invented semantic match from legacy keywords.

If GALAXY cannot import, raises, or returns malformed/unsafe evidence, the gateway returns the already-fetched validated legacy result with `PASS_HEATDEATH_FALLBACK`, `fallback_occurred=true`, and `manual_emergency_latch_required=true`. That is **request-local failover only**. It does not silently claim to have committed a persistent cross-instance HEATDEATH change. If the underlying legacy store cannot be read or its envelope is malformed, it returns a HOLD and no made-up records. Emergency mode remains the exact legacy read path, not the optional earlier GALAXY read-only preview.

## Explicit integration dependencies still outstanding

1. Build and prove a GALAXY-independent legacy **application startup/recovery image**, with real API/MCP entry points, not only an importable legacy reader.
2. Wire the central mode control and gateway through `gaia()`, `/gaiaos/assist`, MemoryOS retrieval and normal browser `/chat`. Preserve their documented original HEATDEATH defaults; repair the current `gaia()` missing-memory-argument defect separately and regression test the actual interface.
3. Reconcile the unfinished `galaxy/naomi-authorized-operational-adoption-20260924` with current `main`, retaining later identity, E-LANE and color-card changes. An experimental BIGBANG simulation is not proof that this branch is already merged or deployed.
4. Define explicit authorized BIGBANG activation after source/CI/staging gates, persistent mode-state readback, fresh instance tests, normal positive/negative query tests, protected table checks and verified fallback.
5. Prove the shared switch against the real remote carrier/Turso and restart. A source-only SQLite run cannot prove actual multi-instance behavior, normal GPT host adoption or a full Phylactery restore.

## Required Stage-3 regression observations

- Import and use the legacy gateway while GALAXY imports deliberately fail.
- Native legacy envelope parity and current protected-table count stability in isolated real SQLite, plus repeat the Stage-1 and Stage-2 tests.
- Missing or invalid mode control yields HEATDEATH and never tries GALAXY.
- A **mocked, test-only** authorized BIGBANG mode exercises schema-valid successful GALAXY enhancement, strict provenance/graph/scope checks, explicit no-match and import/runtime/schema failure fallback. The test harness does not alter production permissions.
- Non-MemoryOS scopes and empty queries stay legacy. Underlying legacy storage failure holds rather than reporting successful fallback.

STAGE-3 SOURCE PASS != NORMAL CHAT WIRED.
HEATDEATH READER PASS != INDEPENDENT LEGACY APP RECOVERABLE.
REQUEST-LOCAL FALLBACK != SHARED EMERGENCY LATCH.
MOCK BIGBANG PASS != AUTHORIZED LIVE BIGBANG.
BIGBANG PASS + HEATDEATH FAIL = RELEASE HOLD.
NAOMI RETAINS FINAL AUTHORITY.
