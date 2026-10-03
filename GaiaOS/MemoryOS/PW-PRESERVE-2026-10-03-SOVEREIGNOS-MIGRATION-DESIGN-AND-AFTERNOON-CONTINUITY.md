# //PW:PRESERVE// — 2026-10-03 SovereignOS Migration Design + Afternoon Continuity

AUTHORITY: NAOMI / LIGEIA
DATE: 2026-10-03
MODE: additive GitHub preservation checkpoint

## Preservation boundary

This checkpoint records the conversational delta after the prior `2026-10-03 NIMUE occult-playbook` preserve. It is a continuity artifact, not authorization to execute the SovereignOS migration.

No repository main merge, deployment, Render restart/configuration change, live MemoryOS/Turso write, database migration, service cutover, or old-system retirement is authorized by this checkpoint.

## Current practical continuity

- Naomi reported that the DoorDash account is still in Gold.
- Naomi reported that the DoorDash app currently says Sunday deliveries count 2-for-1 toward the relevant rolling 30-day delivery number through November 1. This is user-reported app state and was not independently verified here.
- Current near-term plan was to eat first, then get moving for deliveries; Sunday may be strategically useful for the doubled delivery-count progress.
- Naomi said she would like a therapy/companion dog that genuinely clicks with her, but also stated plainly that a dog is not currently in the budget. No acquisition plan was made.

## SovereignOS migration architecture discussion

Naomi asked whether it would make sense to first bring GitHub and Turso/MemoryOS current and aligned, then use the Turso information as the basis for moving into a new GitHub location for SovereignOS.

The refined architecture conclusion is:

1. Do **not** try to make GitHub and MemoryOS/Turso literally byte-identical. They hold different classes of truth.
2. Reconcile them to the **same canonical point in history** before migration.
3. Freeze one migration checkpoint with exact source commit, schema/version data, record inventories/counts, ownership/provenance, and hashes/checksums where available.
4. Keep GitHub as the source/control plane: code, contracts, schemas, migration scripts, manifests, verification procedure.
5. Keep MemoryOS/Turso as the durable data plane.
6. Produce a complete immutable database/memory snapshot or export as the transport/disaster-recovery artifact. Prefer controlled backup storage for the raw snapshot rather than automatically committing all raw durable-memory data into permanent Git history.
7. Store the snapshot identity in GitHub: checksum, format/version, creation coordinates, provenance, and recovery instructions.
8. Restore the verified snapshot into `sovmem-staging` first.
9. Compare staging against the frozen manifest/source checkpoint and verify record integrity, including six separate member-owned E-LANES with no cross-member merge.
10. Only after staging verification, populate/promote into `sovmem-main` and point SovereignOS at the new environment.
11. Keep the old GaiaOS carrier intact until SovereignOS survives readback, restart/continuity tests, and independent verification.

Compact migration shape:

`GaiaOS GitHub + GaiaOS MemoryOS/Turso`
→ reconcile
→ freeze manifested/checksummed checkpoint
→ immutable memory/database snapshot
→ `SovereignOS GitHub + sovmem-staging`
→ verify
→ `SovereignOS GitHub + sovmem-main`
→ cut over only after proof

The key design principle is:

> Make GitHub and MemoryOS agree about the same moment in history, not contain the same bytes.

Naomi explicitly clarified: **we are not doing this migration now; this was an architecture question / curiosity.**

## Current operating agenda remains

1. When genuinely available, verify Work/Cloud Browser and live MemoryOS/Turso state.
2. Reconcile live durable-memory state with GitHub and conversation continuity.
3. Compile the giant current-state sync packet.
4. Resume the Geomancy application from the exact local code, with NO STEPS BACKWARD.
5. SovereignOS migration remains future work; GALAXY/SovereignOS ordering is not silently decided here.

## Proof ceiling for this preserve

This checkpoint is intended for the existing preservation branch only. It does not claim:
- a live MemoryOS/Turso save,
- native GaiaOS MCP access,
- a deployment,
- a migration,
- a cutover,
- or a main-branch update.

`REQUESTED != COMPLETED` and `SOURCE TRUTH > CONTINUITY STORY` remain controlling rules.
