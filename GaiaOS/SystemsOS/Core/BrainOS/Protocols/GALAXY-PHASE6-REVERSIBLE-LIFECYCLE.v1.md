# GALAXY Phase 6: Reversible Lifecycle / History v1

AUTHORITY: NAOMI / LIGEIA
OWNER: MemoryOS + BrainOS / GALAXY
STATUS: FEATURE-BRANCH SOURCE ONLY; CI, MERGE, DEPLOYMENT AND LIVE PROOF SEPARATE
VERSION: galaxy.phase6.reversible-lifecycle.v1

## Purpose and bounded fixture

Phase 5's exact shadow synthesis PROPOSE → VERIFY → REVOKE and one-record Turso post-restart persistence were previously observed from Naomi-supplied live receipts. Phase 6 adds a **separate lifecycle metadata lane** for an exact controlled durable MemoryOS source record. It must not rewrite that source, its revisions, syntheses, provenance or existing relation status.

First fixture: original calibration CORE \`MEM-00b3fbfd4d73404f97a95c238596ab94\`. This source must still exist in MemoryOS with record.status=ACTIVE. Any missing, changed, cross-scope, nonactive or unexpectedly pre-governed fixture HOLDS. The existing revoked Phase-5 synthesis is not the lifecycle target.

## Transition contract

Initial implicit lifecycle: ACTIVE, only when no row and no events exist.

Ordinary forward progression:
\`ACTIVE → BACKGROUND → ARCHIVED → COMPRESSED\`

Explicit \`REACTIVATE\`: \`BACKGROUND | ARCHIVED | COMPRESSED → ACTIVE\`.

Explicit \`ROLLBACK\`: return to the immediately previous state's exact value, including after reactivation, while **appending a new history event**. Never erase the transition being rolled back. No arbitrary jump, batch mutation, automatic downgrade, decay timer, implicit write, cross-scope write or generic record selection is permitted.

\`PRUNABLE\` is a Phase-7 review concept only: no Phase-6 route to it and never a deletion permission. COMPRESSED is a reversible metadata state **not** lossy source-text compression.

All Phase-6 attenuations are inspectable SHADOW PREVIEWS. The current MemoryOS search/admission and production weighting remain unchanged. Later measured retrieval effects require another explicit authorization and behavior test.

## Storage and transaction

Existing \`memory_lifecycle\` holds one current state per record. The new \`memory_lifecycle_events\` is append-only, with event_id, record_id, previous_event_id, from_state, to_state, action, time, reason, authority and receipt_id. An event, its current-state update and matching \`runtime_receipts\` row are one local/remote SQLite-compatible transaction.

A valid read requires the entire preceding event chain to link from implicit ACTIVE, with no duplicate IDs, untraced existing row, unknown states, mismatched current head or missing last receipt reference. Untraced legacy rows HOLD for separately reviewed migration instead of being silently assumed equivalent to ACTIVE.

A mutation requires, separately **for each action**: authority NAOMI, explicit approval, the exact operation's confirmation token, bounded nonempty reason (max 512 characters), expected current state, exact prior event ID and a passing fresh read-only review. SQL state+receipt compare-and-swap and append-only event uniqueness prevent silent stale overwrites. If conflict or uncertainty occurs, HOLD and repull, never retry blindly.

## Proof ladder

1. Source branch: protocol, strict internal runtime module, additive schema, tests, Docker packaging, read-only signed-session fixture review and carrier verifier checks.
2. Offline CI: verify read-only inspection, complete progression, rollback, reactivation, preserved source, append-only chain, stale-state/authorization failures, and no exposed mutation endpoint.
3. Human review, separately authorized merge/deploy, deployed \`/verify\` and read-only \`/galaxy/lifecycle/phase6-fixture-review\`.
4. **Separate Naomi authorization** before exposing *any* effectful browser control route. Each eventual live mutation needs its own visible preview and CSRF-guarded signed session.
5. Live bounded BACKGROUND → ARCHIVED → COMPRESSED → ROLLBACK → REACTIVATE with independent per-step PASS_READBACK. Check original record, relation history, Phase-5 provenance, receipts and no production retrieval change.
6. Pin pre-restart record plus lifecycle chain and receipts; restart actual Render process and prove exact post-restart state and full history readback. A single fixture cannot prove all database rows or global recovery.

Next Phase-6 gate at this source checkpoint: **CI PASS → PR REVIEW → EXPLICIT MERGE/DEPLOY AUTHORIZATION → /verify → READ-ONLY LIVE REVIEW → HOLD**.

No new live mutation, production attenuation, physical deletion, full database export or independent exodus is claimed here. Continue normal canonical E-LANE and GitHub preservation; the Phylactery remains an additive backup.
