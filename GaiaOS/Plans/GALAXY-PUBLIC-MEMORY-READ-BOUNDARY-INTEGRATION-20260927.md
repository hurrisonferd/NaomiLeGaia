# GALAXY real public-memory read integration repair

SOURCE-ONLY STACKED DRAFT on real Render bridge integration PR #110. No live Turso read/write, real credentials, merge, deployment, BIGBANG activation or SOS cutover.

## Source audit: an actual alternate read bypass

Earlier Stage 9AE/9AF barriers guard the normal read gateway and hosted-model context against unreleased archived records and even forged ACTIVE records retaining an archive source. However, the Render app also exposes authenticated direct HTTP and MCP MemconOS search/read endpoints returning raw MemconOS payloads without this check. The independent legacy GALAXY preview directly returned status/source/lifecycle for ungraduated archives, and browser ORBIT/GRAVITY direct inspection also bypassed the gateway. An accidental staging alias misconfiguration could expose imported HOLD records through these paths, regardless of BIGBANG being disabled. The controlled staging import is not yet real-authorized, so this is a source-level risk established by code inspection and synthetic regression, not a report of a real exposure.

## Exact repair

The new pure public archive guard has no optional GALAXY imports, no database, no secrets and no mode control. The existing independent HEATDEATH gateway reuses the same guard; all direct authenticated MemconOS HTTP/MCP read/search routes validate the full result before serialization. An unreleased record requested by ID is indistinguishable from unknown, while mixed clean+HOLD searches return only a redacted HOLD without any partial statement, archive source or record identifiers. Valid clean native responses remain exactly unchanged. The opt-in legacy preview validates original search rows and separately reread neighborhood rows to prevent time-of-check/time-of-use and fake CURRENT-state leaks. The actual Render browser ORBIT/GRAVITY inspections refuse an unreleased record. Existing host bootstrap and MemoryOS retrieval continue to use the gateway and their legacy HOLD behavior. Owner-local archive inspection stays a separate future authorized surface, not an ordinary read.

Actual Render Dockerfile now packages this pure guard and deliberately excludes owner-local import/export, signing, rollback and migration scripts. Invariants: no data writes or promotions, no stage status upgrades, no mode changes, no identity claims, BIGBANG remains locked, preserve all six individual E-LANES and the //PW:PRESERVE// command.

## Proof and remaining requirements

CI uses the REAL Render bridge app and REAL disposable local SQLite records: one safe ACTIVE, one explicit STAGED_HISTORICAL_HOLD, and one forged ACTIVE archive-source record. It tests authenticated HTTP/MCP exact ID and search, no-partial-leak mixed batches, unchanged native clean returns, HTTP denied before DB access, host bootstrap and existing gateway HOLDS, preview reread changes and served-browser direct ORBIT/GRAVITY denial, plus the existing real Render bridge and HEATDEATH regressions. CI builds the exact Render Docker image and checks the guard in a network-disabled container with no secrets. These synthetic checks cannot prove remote Turso identity, actual live memory safety, real Render SHA or authorized enhanced recall.

The overall project still needs independently reviewed and authorized stacked-source merge, actual deployment readback, real owner-controlled staging and source verification, full original MemconOS/Turso graph and lifecycle data migration, independent private SovereignOS source and six-lane restoration, and a separately owner-authorized BIGBANG release gate after live evidence. A successful source test is not deployed functionality. The existing original deployment and both user-created SOVMEM databases are untouched by this draft.
