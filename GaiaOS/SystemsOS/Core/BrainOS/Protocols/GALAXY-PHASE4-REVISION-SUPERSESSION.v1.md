# GALAXY Phase 4 — Revision / Supersession v1

AUTHORITY: NAOMI / LIGEIA
OWNER: GaiaOS / BrainOS + MemoryOS
STATUS: SOURCE DESIGN
VERSION: galaxy.phase4.revision-supersession.v1
PRODUCTION EFFECT: NONE UNTIL SEPARATELY AUTHORIZED AND LIVE-PROVEN

## Core laws

`REVISES != SUPERSEDES`

`NEWER != TRUER`

`HISTORY_PRESERVED != HISTORY_GOVERNS_PRESENT`

`SUPERSEDED != ERASED`

`REVOCATION != DELETION`

`CURRENT GOVERNING STATE != AUTHORITY`

Canonical edge direction:
`B REVISES/SUPERSEDES A => source=B, target=A`.

A revision relation says later evidence changes how an earlier record should be interpreted in current context. It does not by itself remove A from ordinary-current eligibility.

A supersession relation is a stronger governing-state transition. It may remove A from ordinary-current default eligibility, but A remains durable, historically retrievable, provenance-bearing, and inspectable.

## VASKON synthesis

82 · VASKON 🖤 ✴️ (◉‿◉)

46 · VERA 💚 🦋 (˘‿˘)
Revision is an epistemic relationship, not a rewrite operation. Preserve the old proposition and the reason the new proposition changes its interpretation.

58 · ANVIL 💗 ⌚ (¬‿¬)
Supersession requires a stronger proof boundary than revision. Phase 4 uses a two-step ladder: a VERIFIED REVISES edge must exist before the same pair may advance to SUPERSEDES. Every mutation requires explicit Naomi authority and a receipt. Reversal changes edge state; it never deletes the edge or either memory.

60 · SELENE 💛 🎧 (˶ᵔ ᵕ ᵔ˶)
Old material may become quieter in ordinary-current retrieval without being made inaccessible. Historical retrieval remains available, and rollback must restore the prior governing posture.

56 · ORIN 🩵 🪐 (☆▽☆)
Revision history is a graph, not necessarily a single chain. Preserve branching evidence and later reactivation. Do not force every disagreement into supersession.

90 · KESTREL 💖 🏍️ (•̀ᴗ•́)و
Keep the path finite: REVIEW → PROPOSE REVISES → VERIFY → OBSERVE → OPTIONAL PROPOSE SUPERSEDES → VERIFY → ROLLBACK TEST → ADOPTION DECISION. No silent transition and no phase-letter treadmill.

62 · NIMUE 💙 🍄 (－‸ლ)
Watch the negative space. Reverse edges, competing successors, hidden contradictions, and history that disappears from the default surface are all failure modes. HOLD on cycles or competing supersession rather than guessing.

### VASKON result

Phase 4 adopts a **Revision Ladder**:

1. Read-only pair review.
2. REVISES may be proposed.
3. REVISES may be verified only under explicit Naomi authority.
4. SUPERSEDES is not eligible until the same source→target pair already has VERIFIED REVISES.
5. Direct reverse revision/supersession edges fail closed as a cycle risk.
6. A target with a different VERIFIED superseding source fails closed as a competing-governor conflict.
7. Verified Phase-4 edges may be REVOKED under explicit Naomi authority with a reason. Revocation changes edge state and preserves the edge, evidence, original verification timestamp, both durable records, and history.
8. Revocation restores governance by recomputing from remaining VERIFIED edges. It does not fabricate a previous record snapshot.

## Governing-state semantics

For an ACTIVE target record A:

- no incoming VERIFIED revision/supersession: `CURRENT`
- incoming VERIFIED REVISES only: `CURRENT_REVISED_CONTEXT`
- incoming VERIFIED SUPERSEDES: `HISTORICAL_SUPERSEDED`

For a non-ACTIVE target:
- `NONACTIVE_HISTORICAL`

Historical retrieval eligibility remains true in every state.

The source record B does not gain truth or authority merely by being the source of a revision edge.

## Initial source slice

The first Phase-4 implementation is intentionally narrow:

- module: `api/galaxy_phase4.py`
- read-only pair review and deterministic projected-state preview
- exact REVISES / SUPERSEDES semantics only
- same-scope pair requirement for the initial slice
- direct-cycle detection
- competing-supersession detection
- SUPERSEDES prerequisite: VERIFIED REVISES for the same pair
- explicit mutation wrappers exist in source but no browser mutation route is exposed in this first slice
- reversible edge revocation primitive is added to MemoryOS runtime
- controlled fixture review route is read-only
- no production retrieval wiring is changed
- unrestricted global weighted retrieval remains OFF

## Initial live gate

After deployment:

1. `/verify` must prove source packaging, syntax, route registration, Phase-3-closed state, and Phase-4 no-production-effect boundary.
2. Run the read-only controlled Phase-4 fixture review.
3. Inspect projected REVISES and SUPERSEDES semantics, cycle/conflict guards, history-preservation fields, and zero writes.
4. Stop and review.
5. Any relation proposal/verification requires a later explicit Naomi authorization and a separately exposed guarded mutation route.

## Proof boundary

Source design, offline tests, deployment, read-only live review, relation proposal, relation verification, governing-state behavior, rollback/revocation, and production retrieval adoption are separate proof layers. Never collapse them.
