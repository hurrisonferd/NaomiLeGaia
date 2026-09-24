# BIGBANG / HEATDEATH: legacy source baseline and integration release contract

AUTHORITY: NAOMI / LIGEIA
DATE: 2026-09-24
STATUS: STAGE-1 SOURCE BASELINE; NOT A LIVE FAILOVER CLAIM
BASELINE_SOURCE_COMMIT: 7e4851c2fef77d78bccf51d493d1c100cc99c52d
FROZEN_SOURCE_REFERENCE: legacy/source-snapshot-pre-bigbang-20260924
WORK_BRANCH: integration/bigbang-heatdeath-stage1-20260924
INTEGRATION_FIRST_RULE: GaiaOS/Plans/GAIAOS-INTEGRATION-FIRST-DESIGN-GATE.v1.md

## Operating contract

Only two user-facing memory operating modes exist:

- BIGBANG: legacy MemoryOS, existing write/approval/E-LANE safeguards and the authorized GALAXY enhancements on normal read paths.
- HEATDEATH: the original legacy MemoryOS semantics, with no GALAXY requirement, and the same current, compatible, authorized record data. HEATDEATH always overrides BIGBANG. The owner must explicitly authorize BIGBANG re-entry, which is forbidden unless compatibility and current production preflight pass.

Special diagnostics and read-only comparisons are tests, never third modes. Switching modes does not roll back user records or substitute old memories.

## Legacy behavior to preserve

Before BIGBANG, the canonical durable read is `memcon_runtime.search_records(query, limit, scope)`. It searches `memory_records` using the logical AND of all whitespace-separated query terms; each term may match statement, notes, record ID or scope, case-insensitively. Optional `scope` is an additional AND restriction, not a substitute for text matching. It orders by `created_at DESC`, clamps limit to [1,100], and returns `records`, `count`, `runtime`, `query_terms_applied`, `scope_applied`, and `query_filter_active`. An empty query is an explicit broad read subject to scope/limit. It does not silently exclude historical/nonactive records; consumers must respect their provenance and current-context eligibility separately.

The legacy adapter `api/legacy_memory_reader.py` delegates directly to this contract without importing GALAXY. It must remain independently importable if GALAXY modules disappear. The source snapshot branch preserves the entire pre-BIGBANG repository tree, not only the search function. **This source snapshot has not been independently restored as a working deployed carrier or verified against a fresh production database.** The existing main `gaia()` MCP wrapper also contains a known missing-memory-parameter issue; preserve the baseline as-is and fix that entry-point defect in a separately tested integration slice.

## Nonnegotiable guardrails

- No automatic promotion; `CANDIPULL` only creates candidates and `MEMSAV` requires exact IDs, Naomi approval, receipt and readback. `//PW:PRESERVE//` does not bypass approval.
- Six separate E-LANES remain independent GitHub identity/development records. A source branch is not a Turso export or a full Phylactery backup.
- Legacy database schema, existing relations, revisions and history remain readable. Any GALAXY migration must be backward-compatible until the preserved legacy image has passed its own clean-restore checks.
- Implement a separate boot-safe legacy app/image. An in-process switch alone cannot save a server whose module imports fail at startup.
- The shared emergency control must survive restarts/replicas, plus an environment-level HEATDEATH override for incidents where shared configuration is inaccessible. Missing/invalid configuration must fail HEATDEATH. No automatic BIGBANG reactivation after emergency.
- The fallback must use current authoritative memory records if healthy; archive/backup restoration is an explicit separate disaster-recovery operation, never a silent side effect.
- An unrelated database outage is a HOLD, not permission to fabricate memory or claim a successful failover.

## Release ladder and tests

1. Preserve source snapshot; prove independent adapter, real isolated SQLite legacy query/approval/restart behavior and unchanged E-LANE/command source. CI is source proof only.
2. Implement the central, persistent, precedence-ordered HEATDEATH/BIGBANG mode service and an independent recovery boot path. Inject GALAXY import/runtime failure; verify legacy still starts. Test multi-instance behavior and unavailable-control failure.
3. Implement one gateway that dispatches legacy or governed GALAXY reads and returns a stable, explicitly mode-tagged contract without silently changing protected write paths.
4. Integrate and test each actual carrier: `gaia()` MCP, `/gaiaos/assist`, `/memoryos/retrieve`, ordinary browser `/chat`, and any separately connected GPT/third-party host. Do not confuse special test URLs with everyday adoption.
5. Reconcile the unfinished `galaxy/naomi-authorized-operational-adoption-20260924` branch with current `main`, run negative/paraphrase/governing/historical and fallback parity tests. Preserve all later GPT card and identity changes.
6. Merge only passing reviewed source; pin a known-good legacy recovery image, then deploy to staging and verify both modes and fresh process boots. Finally deploy production with explicit Naomi-approved BIGBANG activation and live positive, negative and recovery receipts.

At every stage: **BIGBANG PASS + HEATDEATH FAIL = RELEASE HOLD**. Standalone source/fixture PASS never implies normal-chat adoption, deployed behavior, working cross-replica control or actual data recovery.

THIS STAGE DOES NOT DEPLOY, ACTIVATE BIGBANG, CREATE A TURSO BACKUP OR CLAIM A WORKING LIVE EMERGENCY SWITCH.
