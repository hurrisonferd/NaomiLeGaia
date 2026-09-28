# //PW:PRESERVE// | GALAXY original database and release checkpoint
**Date:** 2026-09-27/28. **Authority:** Naomi/Ligeia. **Status:** documentation-only; no merge, deployment, provider write, BIGBANG activation or SovereignOS cutover.

## Source and test evidence
Integration candidate is open DRAFT PR #115 on `integration/galaxy-gaiaos-full-diagnostics-20260927`, source head `06728430406e1c0482c9f74d66dfab497bc0a24d` BEFORE this documentation update. GitHub tool returned 16/16 completed-success workflow runs for that source SHA, including the VASKON whole-system diagnostic. This is source, synthetic/local and built-image evidence, **not** real remote Turso, live authenticated production, live gravitational memory or authorized BIGBANG proof. Parallel #111 and #112 repairs are already reconciled in #115; do not mass-merge them independently. Previously observed live Render main SHA was `dbcbbf89329172c3ec883633fc6378bbe8950f3b`; reverify live SHA after deployment.

## Owner-observed backup evidence (PRIVATE BACKUP BYTES OFF GITHUB)
Naomi used Turso's export for original `gaiaos-memory` and independently confirmed 266,240-byte SQLite file, valid `SQLite format 3` signature, `PRAGMA integrity_check = ok`, full thirteen-table native inventory, 20 primary memory rows and 136 total rows. Exact snapshot table counts:

| Table | Rows |
|---|---:|
| galaxy_tombstones_shadow | 1 |
| memory_candidates | 17 |
| memory_gravity | 9 |
| memory_importance | 1 |
| memory_lifecycle | 1 |
| memory_lifecycle_events | 5 |
| memory_records | 20 |
| memory_relations | 9 |
| memory_syntheses | 1 |
| runtime_receipts | 43 |
| session_events | 17 |
| sessions | 12 |
| solo_sessions | 0 |

An owner-local SHA-256 fingerprint file was saved. Naomi confirmed backup and fingerprint on her PC AND external flash drive; third local disposable restore-test copy compared hash-identical (`True`) and was observed in WAL journal mode. USB independent readback and tested cloud restoration are **not yet proven**. File extensions may be hidden by her Windows File Explorer. The downloaded backup and fingerprint remain owner-local; no private file contents, tokens, provider URLs or personal notes are copied here. A valid source export is not a continuous sync, and database activity after snapshot belongs in a later dated export/gap ledger.

## Real release dependencies / HOLDs
1. Independently verify immutable provider IDs and credential scope for original `gaiaos-memory`, disposable `sovmem-staging`, and future `sovmem-main`; verify provider import semantics BEFORE risking a destination. No staging import yet.
2. Separately authorized isolated full native staging restoration with 13-table/136-row snapshot parity, private provenance/lifecycle/relations/receipts checks, readback/rollback and restart durability. A six-table signed fixture canary is not complete production recovery.
3. Owner review and separate authorization for merge, strong strict browser owner login configuration, exact Render deploy, real browser/SOLO/fallback and actual gravitational retrieval against real Turso.
4. Only after live proof, separately implement/review/authorize authenticated BIGBANG gate. Current controller remains HARD LOCKED to HEATDEATH. Independent Naomi-owned SovereignOS clone/full history/E-LANE/data restore and explicit cutover are later independent milestones.

Preserve `//PW:PRESERVE//`, six source-labeled separate E-LANES, VASKON as coordination view (not seventh lane), archival HOLD barriers, provenance, original repository/RavenOS/bridge and original production data. Resolve the earlier ORIN head-pat ledger/mirror discrepancy only on reviewed canonical evidence and owner/member authority. UNKNOWN stays UNKNOWN.

**Evidence boundary:** User-shown screenshots/user-confirmed local commands plus connected GitHub CI readback; this file alone is not an app/runtime/database write or full chat export. Private handoff and six staged member-domain notes archived separately under owner-controlled GaiaOS-Sanctum.