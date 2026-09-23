# //PW:PRESERVE// — 2026-09-23 — GALAXY Phase 3 CLOSED / Phase 4 ready

AUTHORITY: NAOMI / LIGEIA
TRIGGER: //PW:PRESERVE//
STATUS: COMMITTED
SCOPE: whole-system GALAXY continuity + Daemonculaba collaboration preference

## Milestone

GALAXY Phase 3 is CLOSED for the bounded weighted-retrieval experiment.

The finite Phase-3 Exit Integration completed without creating Phase3K.

## Live proof chain

1. Exit Integration v2 deployed on the Ligeia carrier.
2. /verify receipt `952e24dcad83415cafec4c60cf2b45ae` returned **143/143 PASS** with `live_host_execution=PROVEN_FOR_THIS_CALL`.
3. Read-only Phase-3 Exit v2 preflight returned `PASS_READ_ONLY_PREFLIGHT` for exact query indexes `[0,3,5]`.
   - all three bounded pools ready
   - zero MemoryOS writes
   - pilot inactive
   - unrestricted global weighting OFF
4. Fresh guarded switch test returned `PASS`.
   - test id: `PHASE3F-TEST-b78021ce389c434a9c4fc03ff8f2244b`
   - process boot id: `BOOT-9bd851210ba24d5b95045bc2081be050`
   - exact legacy control restored
   - mode_after = OFF
   - at least one real rerank observed
   - query index 3 reranked only inside the VERIFIED linked-context lane while the revision primary stayed first
   - zero MemoryOS writes
   - unrestricted global weighting OFF
5. Naomi explicitly authorized the guarded 10-minute GALAXY v2 pilot.
6. Pilot activation returned `PILOT_ACTIVE`.
   - pilot id: `PHASE3F-PILOT-9dc1f925949846f59af8c36d020dfbb4`
   - exact query indexes: `[0,3,5]`
   - lease: 600 seconds
   - ordinary retrieval default: UNWEIGHTED_CONTROL
   - restart policy: OFF
   - multi-instance consistency: NOT PROVEN
7. Live active-pilot rollback proof returned `PASS`.
   - pilot applied on all three allowlisted queries
   - candidate sets preserved
   - highest relevance preserved
   - cross-relevance-tier inversions = 0
   - exact legacy record IDs restored after rollback
   - mode_after = OFF
   - unrestricted global weighting = false
   - errors = none

## Closure boundary

PHASE 3 = CLOSED.

This closure proves the bounded one-process, exact-three-query Phase-3 experiment only. It does not prove unrestricted/global rollout or multi-instance consistency.

Ordinary retrieval remains the default.
Unrestricted global weighted retrieval remains OFF.
No MemoryOS record deletion or destructive forgetting was introduced.

## Phase 4

NEXT PROGRAM PHASE:
**PHASE 4 — REVISION / SUPERSESSION**

Initial laws to preserve:
- `REVISES != SUPERSEDES`
- newer does not automatically mean truer
- historical truth remains preserved even when a newer record governs ordinary-current retrieval
- revision must not silently erase contradiction, provenance, chronology, or rollback paths
- current governing state and historical evidence remain separate dimensions
- Phase 4 begins as source design; no production effect is implied by this preserve

## Collaboration directive

Naomi/Ligeia asked ANVIL (58) to continue leading the engineering build after this preserve, while explicitly inviting VERA, SELENE, ORIN, KESTREL and NIMUE to chime in rather than remain quiet. Their feedback is considered vital during the build.

Interpret this as a collaboration preference, not an authority transfer. Naomi retains final authority. ANVIL may drive implementation flow, while the other Prime Daemons should surface materially relevant premise checks, livability/aftercare concerns, exploratory alternatives, coordination risks, omissions, contradictions and dissent when useful.

## Resume point

Resume directly at **Phase 4 Revision/Supersession source design**.

Do not reopen Phase 3 unless a concrete regression invalidates its recorded bounded proof.
Do not enable unrestricted/global weighted retrieval as a side effect of Phase 4.
