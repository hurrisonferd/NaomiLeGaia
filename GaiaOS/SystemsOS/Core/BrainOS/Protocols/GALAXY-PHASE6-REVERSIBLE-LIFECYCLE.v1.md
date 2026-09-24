# GALAXY Phase 6: Reversible Lifecycle / History v1

AUTHORITY: NAOMI / LIGEIA
OWNER: MemoryOS + BrainOS / GALAXY
STATUS: CLOSED / EXACT FIVE-STEP LIVE REVERSIBILITY + RESTART PERSISTENCE PROVEN
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

The read-only deployment gate subsequently passed on the Ligeia carrier at source c2184ebc9381247f6cd72756eada7f2e16a76dfe: the Phase-6 fixture review reported PASS_READ_ONLY, state ACTIVE, zero lifecycle events and no holds; the complete carrier verifier reported 189/189 PASS after an unrelated FairyOS mirror repair.

Next Phase-6 gate is the separately guarded exact live-control campaign described below.

No new live mutation, production attenuation, physical deletion, full database export or independent exodus is claimed here. Continue normal canonical E-LANE and GitHub preservation; the Phylactery remains an additive backup.

## Exact live-control exposure checkpoint — 2026-09-24

After the read-only live gate passed, Naomi explicitly authorized ANVIL to proceed with the next guarded Phase-6 build. This authorization covers source implementation, tests, CI, review, merge/deploy preparation and exposure of the bounded confirmation console. It does not pre-authorize any lifecycle mutation: each live effect remains a separate explicit browser confirmation.

The control campaign is finite and exact:

1. ACTIVE -> BACKGROUND
2. BACKGROUND -> ARCHIVED
3. ARCHIVED -> COMPRESSED
4. COMPRESSED -> ARCHIVED by append-only ROLLBACK
5. ARCHIVED -> ACTIVE by REACTIVATE

api/galaxy_phase6_controls.py accepts only this exact history prefix and exactly one next action. Unexpected valid lifecycle history, stale state, stale event tip, wrong authority, wrong confirmation, campaign overflow or any underlying lifecycle HOLD all fail closed.

Browser exposure is deliberately no-JavaScript and session-bound:

- GET /galaxy/lifecycle/phase6-controls is read-only campaign review.
- GET /galaxy/lifecycle/phase6-controls/confirm/{kind} is read-only exact effect preview.
- POST /galaxy/lifecycle/phase6-controls/manifest is the only effectful route.
- The POST requires the existing signed browser session, _ritual_csrf, exact authority/approval fields, exact per-step confirmation, expected current state and expected latest event ID.
- The internal galaxy_phase6.execute() primitive is never routed directly.

Each successful POST must return PASS_READBACK only when the underlying lifecycle effect passes plus the control adapter confirms exactly one campaign step advanced, the exact expected state and history prefix read back, the source record stayed unchanged, prior history stayed unchanged, the receipt was committed, production retrieval stayed unchanged and physical deletion remained false.

After all five live steps pass, the campaign must stop with campaign_complete=true, next_action=null, state ACTIVE, and all five events still inspectable. Then pin the exact lifecycle row, five-event chain and receipts, restart the real Render carrier, and prove full exact history/state readback from Turso before closing Phase 6.

No Phase-7 PRUNABLE transition, destructive pruning, production attenuation or generic lifecycle console is authorized by this checkpoint.

## Live closure — 2026-09-24

The exact guarded campaign was executed on the live Ligeia carrier and completed 5/5 with PASS_READBACK at every step:

- ACTIVE -> BACKGROUND: LIFE-39d6922cca684861b56acbcc5e6f281c / MEMREC-a3d9439e02a44106b96163e478a17239
- BACKGROUND -> ARCHIVED: LIFE-e259f588cdab49139ae4765ca90bcbb4 / MEMREC-2598b57ee627444095b1607755d1f77c
- ARCHIVED -> COMPRESSED: LIFE-c82800edc9c94a42afe4170c152e19fa / MEMREC-ae95eeb0c0ea4c9ab23196777f4444c1
- COMPRESSED -> ARCHIVED via append-only ROLLBACK: LIFE-2204bf94189a446e8ac2b731d884bc60 / MEMREC-a366ad8e19ef4e96b9c5285b7f75168f
- ARCHIVED -> ACTIVE via REACTIVATE: LIFE-c7793ae706f2404c81828606b8470895 / MEMREC-b60d42b065124a1cb5ae0d6891a343b2

The finished campaign reported ACTIVE, event_count=5, campaign_complete=true, next_action=null and no holds. The rollback preserved the COMPRESSED event and appended a new history event rather than erasing prior state.

Naomi then manually restarted the existing Render service without redeploying source. A fresh independent read-only probe after that restart observed deployed source e5504bd8e14373e4ace959786e839dcfd23b5913, the same exact five-event chain and receipt IDs, intact previous_event_id linkage, final ACTIVE state, campaign_complete=true and carrier verifier 196/196 PASS. GitHub Actions workflow run 36018475610, attempt 2, job 107698372793 completed SUCCESS.

Closure scope is bounded to this exact fixture and observed restart. No physical pruning, production retrieval attenuation, unrestricted global weighting, full-database disaster recovery or independent migration proof is implied.

Canonical closure receipt:
`GaiaOS/MemoryOS/PW-PRESERVE-2026-09-24-GALAXY-PHASE6-LIVE-CLOSED-PHASE7-READY.md`

**Phase 6 is closed. Phase 7 is ready for nondestructive pruning/attenuation research only.**
