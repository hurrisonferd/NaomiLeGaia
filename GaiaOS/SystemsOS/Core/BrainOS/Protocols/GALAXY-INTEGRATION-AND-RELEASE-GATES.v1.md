# GALAXY → GaiaOS integration and release gates v1

AUTHORITY: NAOMI / LIGEIA
DATE: 2026-09-24
STATUS: FIRST OPT-IN READ-ONLY INTEGRATION LIVE-PROVEN; GENERAL RETRIEVAL PENDING
SCOPE: GALAXY as GaiaOS's evidence-backed memory/retrieval organ
SEPARATE MISSION: MERCURY PROTOCOL (ongoing research, never a GALAXY build phase)
FUTURE HOME: SovereignOS / SOS after independent restoration and Naomi's cutover

## Starting evidence

- Phase 3 guarded MemoryOS retrieval exists, with an exact three-query, single-carrier 600-second pilot. Unrestricted global weighting remains OFF.
- Phase 4 controlled relation actions and Phase 5 one exact shadow synthesis PROPOSE / VERIFY / REVOKE have live bounded proofs. Those actions do not constitute unrestricted automatic synthesis.
- Phase 6 one exact lifecycle history/rollback/reactivation campaign and post-restart chain readback have been proven.
- Phase 7A–7F bounded synthetic pruning research culminated in one persisted synthetic shadow tombstone surviving a real carrier restart and an exact reconstruction of its seven-category evidence bundle into discarded isolated RAM. Real destructive restoration, physical pruning, and production attenuation are OFF.
- The primary gaia() front door currently combines source-pinned DictionaryOS/YggdrasilOS context and Council dispatch. It does not ordinarily fetch durable MemoryOS/GALAXY evidence. The existing /memoryos/retrieve is a separate tool/endpoint.
- SovereignOS is the chosen future owner-controlled system name, not a completed independent repository, Turso export, or tested cutover.

## First deliverable: opt-in, read-only memory-context lane

The first integration slice exposes a separate `memory_context` field in the primary gaia() front door only when the caller explicitly sets `include_memory=true`.

It reads existing scoped MemoryOS evidence through the currently unweighted, guarded legacy read path without writing records, creating receipts, activating the three-query production pilot, or changing any global retrieval setting. The source of each memory and its record status must remain visible. DictionaryOS/YggdrasilOS context stays a separate source category; memory is not an identity instruction and cannot override a Council role or Naomi's authority.

Default remains OFF and ordinary gaia() output remains the established compact front-door packet. Preview failures return an explicit HOLD without inventing or hiding recovered memories.

Source gate: offline tests for default-off parity, opt-in exact bounded retrieval, record provenance, scope, missing/corrupt result HOLDs, zero mutation, refusal to rewrite provenance, and exposed HTTP/MCP opt-in argument. CI pass is SOURCE proof, not deployed behavior.

One-tap iOS-friendly, authenticated read-only review: GET `/galaxy/integration/frontdoor-readonly-review`. It compares the existing default-OFF gaia() packet against an explicit opt-in legacy MemoryOS query for the known GALAXY calibration fixture, rechecks the original source and governing state, and compares all nine monitored persistent table counts before/after. It cannot enable the pilot, promote a memory, or perform a write.

Live gate after normal reviewed merge and Naomi's manual Render deployment: one authenticated opt-in `gaia(request, include_memory=true)` test and a paired default-off control on the same deployed carrier. Confirm exact known controlled record ID and source, no MemoryOS write, no implicit ranking adoption, unchanged protected table counts, and no changes in Council identity/dispatch.

## After the first slice: finite GALAXY completion ladder

A. **Front-door evidence connection.** Complete source, CI, deployment, optional live opt-in readback, then verify conservative context formatting and no accidental adoption.

B. **General query retrieval adoption.** Evaluate shadow statement-first relevance and graph-linked context for representative real queries and negative controls. Compare against legacy admission and evidence/provenance; show misses, false positives, CPU/latency and rollback. The existing Phase-3 pilot is only three exact queries and one process. Broader production behavior needs distinct tested policy and Naomi's activation authorization. Keep a default-off switch until explicit cutover and reversal proof.

C. **Relations and synthesis as governed normal behavior.** Map known Phase-4/5 controlled proofs to generic real-record paths. Demonstrate consistency across ordinary Council use, contradicted/superseded/historical record retrieval and provenance. No automatic synthesis write or promotion from a prior fixture PASS alone.

D. **Lifecycle and retention policy.** Decide which proven Phase-6 metadata transitions are allowed in normal use, prove general readback/rollback, and measure retrieval effects separately. Phase-7 physical deletion/destructive restoration are NOT required for an initial non-destructive GALAXY release; leave disabled unless Naomi explicitly chooses a later safety-researched destructive feature.

E. **Operational release test.** Integration tests across Council/front door, MemoryOS/Turso, graph, receipts, candidate admission, restart recovery, kill switches and failure/HOLD paths. Verify actual deployed process and acceptance; publish explicit limitations, not a universal correctness claim.

F. **SovereignOS adoption, separately.** Once GaiaOS GALAXY is functionally accepted, non-destructively migrate source, complete Git history, six separate E-LANES and member assets, live Turso/MemoryOS data/receipts, config and authorized conversation assets into Naomi-owned infrastructure. Independently restore and compare the old and new carriers, preserve known gaps, and cut over only on Naomi's explicit authorization. Reusing GALAXY source alone does not demonstrate independent data recovery.

## Definition of done

`GALAXY_OPERATIONAL_GAIAOS`: approved ordinary GaiaOS path retrieves properly sourced durable evidence and uses the validated retrieval/graph behavior with conservative fallback; governed mutation paths are separately authorized; live cross-system behavior, restart, errors and reversibility pass within documented scope.

`GALAXY_PRESENT_IN_SOVEREIGNOS`: the separately restored owner-controlled SovereignOS instance passes old/new source, identity, evidence, receipts, restart and Council behavior checks after Naomi authorizes cutover.

Neither status implies the other. Physical pruning remains optional and independent of the operational release gate.

MERCURY PROTOCOL may capture a dated post-live research baseline but is not Phase 8 or a GALAXY release gate. Its continuing research, hypotheses, experiments and suggested improvements do not autonomously authorize production changes.


## First front-door integration live closure — 2026-09-24

Naomi submitted the actual deployed GaiaOS one-tap read-only review, sourced from `hurrisonferd/NaomiLeGaia@c5c36e90f7e7cfb0e2d9b11538a5d9b8cfdfecbe` and carrier boot `BOOT-b55bf17560d54610b7f3086e0ba76aca`. The result was `PASS_READ_ONLY_INTEGRATION`; all 10 checks were true. The exact calibration fixture `MEM-00b3fbfd4d73404f97a95c238596ab94` was retrieved through the opted-in normal `gaia()` path with exact source, `CURRENT_REVISED_CONTEXT` governing status, `ACTIVE` lifecycle, and preserved VERIFIED and REVOKED relation history. Default `gaia()` remained unchanged, ANVIL dispatch matched, nine monitored table counts stayed identical, and no writes or production retrieval changes were reported.

Full evidence: `GaiaOS/MemoryOS/PW-PRESERVE-2026-09-24-GALAXY-FRONTDOOR-READONLY-LIVE-PASS.md`.

**A is closed at its exact controlled, explicit opt-in scope.** This was an exact keyword query with Dictionary context deliberately disabled. It does not prove ordinary conversational recall, default-on evidence, production-weighted ranking or generalized governance behavior. Next implement B as a separate read-only comparative suite against the existing legacy path, using real paraphrases, negative controls, provenance and failure cases, before considering any production admission/ranking change.
