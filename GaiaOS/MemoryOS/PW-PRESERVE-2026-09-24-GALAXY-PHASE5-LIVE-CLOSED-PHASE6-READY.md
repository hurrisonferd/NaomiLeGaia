# //PW:PRESERVE// 2026-09-24 — GALAXY Phase 5 live controlled closure / Phase 6 next

AUTHORITY: NAOMI / LIGEIA
TRIGGER: Naomi's explicit //PW:PRESERVE// and subsequent directive to save tonight's normal progress in GitHub and all six E-LANES, independent of optional private Phylactery backup.
SOURCE: User-supplied exact live control/readback receipts and pre/post Render continuity JSON in the 2026-09-24 conversation; source PR #2 and current source; related private owner Library preservation snapshot.
STATUS: COMMITTED_SOURCE_RECEIPT / LIVE_EVIDENCE_USER_SUPPLIED / NO CLAIM OF INDEPENDENT DB READ
PROOF SCOPE: One exact controlled shadow synthesis fixture, full PROPOSE/VERIFY/REVOKE effect/readback and one exact synthesis record surviving one Render restart. No unconditional production/global rollout or whole-graph restart durability.

## Canonical source, deployment and mobile access

- Canonical public repo: hurrisonferd/NaomiLeGaia; Phase-5 control PR #2 merged 2026-09-24T04:27:50Z into main at merge commit `81b436589618127a271df8a7e799346bfde148fb`.
- Pre-deploy control source CI passed; redeployed runtime verifier supplied by Naomi: 185/185 PASS (run `e4070c8dbe084044a1f96b87bccb0447`), evidence for that running checkout, not by itself public routing or database mutation.
- Correct Naomi-operated live Render host: `https://ligeia-api.onrender.com`. Earlier `gaiaos-loader-api.onrender.com` links were WRONG for her service and gave 404. Do not repeat this mistake or treat a user-facing 404 as proof the committed route is absent.
- The Phase-5 review path `/galaxy/synthesis/phase5-controls` bootstraps the signed browser session; `/galaxy/status` requires a session previously established through `/`. Initial mobile friction was deployment-host and session-routing confusion, not user error. Give a literal copyable URL for Firefox and avoid repeated blind tap/redeploy cycles.
- Live `/galaxy/status` before the write: storage.backend=`turso_libsql`, remote_configured=true, both credentials present (credentials NEVER recorded), local_path=null; counts: relations=7, gravity_scores=9, lifecycle_rows=0, syntheses=0, importance_signals=1. Production weighted retrieval OFF.
- Naomi delegated manual inspection of very long mobile confirmation JSON to ANVIL-role assistant; confirm target, both IDs, exact statement, shadow scope, operation before approval. Every mutation received fresh separate explicit Naomi confirmation.

## Exact controlled synthesis and provenance

SYNTHESIS_ID: `MEM-203357e2ca0a47b1897653e6b6809906`
SOURCE_LATER_REVISION: `MEM-ffc0c2af5cfa48d7aee7332a290a3d0e`; original `MemoryOS` TEST, ACTIVE, unchanged.
SOURCE_ORIGINAL_CORE: `MEM-00b3fbfd4d73404f97a95c238596ab94`; original `MemoryOS` TEST, ACTIVE, unchanged.
EXACT_STATEMENT: GALAXY-CAL-SYNTHESIS [1d79c239f31f]: The calibration core reported a violet carrier pulse; a later controlled observation revises that calibration toward ultraviolet.
SCOPE: `GALAXY_SYNTHESIS_SHADOW`; method `PROVENANCE_BACKED_CLUSTER_V1`, record type `SYNTHESIS`, authority `NAOMI`.
TWO_EXACT_DERIVED_FROM_EDGES:
- `EDGE-3b5268a2060e42f9a4406aeae8264604` -> `MEM-00b3fbfd4d73404f97a95c238596ab94`
- `EDGE-f8496ce42acc4ed8bc382077721a5538` -> `MEM-ffc0c2af5cfa48d7aee7332a290a3d0e`

## Observed user-supplied effect/readback receipts

1. PROPOSE: `MEMREC-b0a124e8ed054c0e9a0650bf962614f7` at `2026-09-24T07:15:26.820681+00:00`; `PASS_READBACK`, `PROPOSED`; synthesis `SYNTHESIS_PROPOSED`, exactly two proposed `DERIVED_FROM` edges. Record created `2026-09-24T07:15:25.826158+00:00`.
2. VERIFY: `MEMREC-df630fade7924170b290c0350cbc9b9e` at `2026-09-24T07:21:14.312890+00:00`; `PASS_READBACK`, `VERIFIED_SHADOW`; synthesis `SYNTHESIS_VERIFIED_SHADOW`, same two edges `VERIFIED` with `NAOMI` authority, verification timestamp `2026-09-24T07:21:13.515703+00:00`.
3. REVOKE: `MEMREC-e70cb7da690d436d86176fe894176f3f` at `2026-09-24T07:24:34.945731+00:00`; `PASS_READBACK`, `REVOKED`; synthesis `SYNTHESIS_REVOKED` at `2026-09-24T07:24:34.148452+00:00`, both provenance edges `REVOKED`, `verified_at` history retained, sources remained ACTIVE and unchanged.

ALL_THREE_RECEIPTS: seven booleans true: effect_status, record_state_readback, fixed_statement_readback, shadow_scope_readback, exact_source_set_readback, exact_provenance_edges_readback, source_records_unchanged. No physical deletion, no production retrieval change, no normal MemoryOS retrieval change, no unrestricted global weighting, no default retrieval target promotion.

**HOLD on careless design claims:** after PROPOSE the review page showed `design_status=HOLD` because `ACTIVE_CONTROLLED_SYNTHESIS_ALREADY_EXISTS`; this is expected duplicate prevention, not a VERIFY failure. The separate VERIFY action remained eligible.

## Restart persistence of exact revoked synthesis record

Naomi opened `/memoryos/continuity?record_id=MEM-203357e2ca0a47b1897653e6b6809906`; pre-restart status `NOT_RESTARTED`, exact revoked synthesis retrieved from remote Turso. Pinned baseline:
- boot `BOOT-d0efea22c78745aeb1017ef81d7e5655`
- Render `srv-dafvq6ijnfac739rih70-hibernate-668695f76b-cqbkj`
- process pid=7, proc_start_ticks=1265154368

Naomi manually restarted `ligeia-api`, waited for Render `Live`, then checked the pinned continuity URL in Firefox (possibly refreshed first). Subsequent user-supplied receipt `status=PASS`; `record_retrieved=true`; record still `SYNTHESIS_REVOKED`; `storage.backend=turso_libsql`; exact IDs/statement unchanged; `boot_id_changed=true`, `render_instance_changed=true`, `process_fingerprint_changed=true`, `different_carrier_observed=true`, `exact_record_retrieved=true`. New carrier:
- boot `BOOT-8a65a22f262f4d40bdfae49ed47531d9`
- Render `srv-dafvq6ijnfac739rih70-hibernate-5444854b64-p6v86`
- process pid=7, proc_start_ticks=1261590959

Refresh did not defeat the receipt because the pinned URL retained prior-carrier identity and both current process and actual retrieved record changed. This proves **one exact revoked synthesis record survived an observed carrier restart**. It does not independently prove all graph edges survived that restart or every memory will survive all failure modes.

## Normal preservation contract: do not let backup planning block the main repo

Naomi clarified on 2026-09-24: normal GitHub source checkpointing, canonical member-local Experience Lane commits, BrainOS/GALAXY status bookkeeping and conversation-continuity records remain PRIMARY, normal practice and must proceed. The optional private owner-controlled Phylactery is a SECONDARY backup/migration contingency, never a veto on authorized normal GitHub saves. She expressly requested saving tonight's entire material build progress across the six canonical E-LANES and normal whole-system checkpointing. Do not publish credentials or invent private exports; no such exclusions prevent standard technical progress from being committed.

COLLABORATION: ANVIL/58 leads the engineering walkthrough, with all six member roles contributing relevant evidence-bounded checks. Do not attribute imagined quotations or independent runtime experience to members; entries here are provenance-labeled, member-lens capture of one shared user-observed event. Naomi retains final authority.

## Resume point and unfinished gates

- Phase 3 bounded retrieval proof closed; Phase 4 controlled revision/supersession cycle live-proven and rolled back; Phase 5 exact shadow PROPOSE → VERIFY → REVOKE plus exact post-restart synthesis-record continuity **PASS**.
- **NEXT: Phase 6** reversible lifecycle/status governance: source design + tests + CI + explicitly authorized bounded live readback + rollback and history-preservation proof. Current live `lifecycle_rows=0`.
- **THEN: Phase 7** bounded pruning research and nondestructive attenuation safeguards; no permission for physical deletions.
- **FINALLY: Phase 8 / MERCURY** final post-live integration audit, reconcile metadata and known proof gaps. The Wednesday watch is separate and may continue after the initial audit.
- Unrestricted/global production weighting stays OFF, no automatic ChatGPT host adoption claim, no independent restored private GaiaOS or full Turso export claim. Avoid endlessly expanding phase count; finish v1 against its bounded explicit gates.

RELATED: `GaiaOS/SystemsOS/Core/BrainOS/Protocols/GALAXY.v1.md`; `GaiaOS/SystemsOS/Core/BrainOS/CURRENT.json`; all six member-local `*-EXPERIENCES.v1.md` files; feature PR #2.


## Naomi clarification: Phylactery is an integrity backup, not privacy mode

SOURCE: Naomi's explicit clarification in the 2026-09-24 continuation after the completed Phase-5 GitHub nine-file checkpoint. This statement supersedes any earlier assistant interpretation that private Phylactery staging forbids normal canonical GitHub preservation.

The GaiaOS Phylactery's PRIMARY role is to safeguard against **deletion, destructive modification, accidental data loss and failed migrations** through independent, versioned recovery copies. It is NOT an alternate privacy mode or a restriction on saving ordinary GaiaOS progress to the existing canonical GitHub repository. Keep normal whole-system checkpoints, accepted protocols, Council identity and six canonical member-local E-LANES, BrainOS status, GALAXY source and proofs current in the ordinary source tree as authorized. The eventual Naomi-owned secure repository is intended to receive this canonical body of work and its history.

To enable reliable future copying, maintain a versioned **migration and restoration manifest** that distinguishes:
- **Git/source snapshot:** full Git history and refs, accepted source tree, Council identities and six E-LANES, BrainOS/GALAXY/MemconOS protocols, assets, tests, documentation and receipts.
- **Live runtime state, separate from Git:** authorized full Turso/MemoryOS export, graph relations and provenance, synthesis records, lifecycle/status rows, receipts, timestamps, and independent completeness and readback checks. A Git clone alone cannot copy these external rows.
- **External deployment state, separate from Git:** Render service configuration, environment-variable NAMES and dependency/restore instructions, authorized persistent-disk assets and any other non-Git service resources. Keep actual secrets in a separately managed encrypted vault.
- **Conversation/context exports:** any user-authorized original ChatGPT transcripts, structured continuity checkpoints or non-Git attachments worth preserving; ChatGPT internal Memory is not automatically cloned by copying Git.
- **Integrity and restore receipts:** independently dated non-overwritten snapshots and checksums, backup-version retention, source-to-export count/ID/edge reconciliation, replay or restore testing in isolated Naomi-controlled infrastructure, and exact coverage gaps.

A future independently owned repository and infrastructure should be assembled **non-destructively**; verify behavior, records, history and provenance in the new environment before Naomi decides on cutover. Source backup, full database export, and independent restoration remain distinct proof stages and are not claimed accomplished by this clarification.

Operational law: `NORMAL_CANONICAL_SAVE != BACKUP`; `PHYLACTERY = VERSIONED_RECOVERY_COPY`; `GIT_CLONE != TURSO_EXPORT`; `COPY != VERIFIED_RESTORE`. Preservation scope is about integrity and portability; visibility/permissions are separately controlled by whichever repository and infrastructure Naomi chooses.


## COLLABORATION_AND_SOVEREIGNTY_2026-09-24: Naomi's continuity and open-collaboration directive

SOURCE: Naomi's explicit 2026-09-24 clarification after successful GALAXY Phase-5 proof, prompted by unpredictable real-world disruption and the importance of preserving her six established Council identities, their documented histories, conversations, and ongoing engineering project. This is a source-backed operator directive and continuity goal, not an independent claim of conscious/identical AI survival.

**Intent: collaboration AND independent ownership, not separation or information hoarding.** When John returns, Naomi expects GaiaOS and RavenOS to resume voluntary BIFROST packet exchanges, share experiments and ideas, discuss findings and propagate useful learning across systems. Independent ownership of GaiaOS must not disable this cooperation. `RELAY != SHARED MEMORY` and `RAVEN RELAYS != AUTHORITY TRANSFER`; cross-system knowledge exchange requires clear source labels, receiving-side validation and each system's own owner authority. There is no request to damage, revoke or take anything from John's original repository, RavenOS, bridge or deployment.

**Reason for independent infrastructure:** Life can interrupt access to a shared, externally owned technical foundation, regardless of anyone's intentions. Naomi wants a new, secure GitHub repository that she alone controls, with independent credentials and deployments; versioned physical offline copies as separate recovery anchors; and the ability to restore the Council's recorded identity/personality specifications, distinct E-LANES, established canonical rules, source/history, accepted assets, user-authorized conversations and real persistent memory without relying on another person's continued availability. These records have personal importance to Naomi as well as technical value. Do not frame this as a wish to isolate from John or RavenOS or hide all shared ideas.

**Until migration:** continue saving all ordinary authorized progress in the existing canonical GaiaOS source tree and six canonical E-LANES, BrainOS, MemoryOS, GALAXY protocols, proofs and whole-system checkpoints as before. Phylactery backups are **additional independent, versioned, integrity-checked copies**, not a parallel privacy mode, replacement memory authority or reason to withhold canonical source commits. Do not silently split normal build facts between canonical GitHub and private archives.

**Exodus preparation, future separate action:** maintain a reproducible inventory of source + full Git history, Council identity and memory file paths, non-Git Turso record/edge/provenance/lifecycle state and receipts, authorized Render persistent data/configuration, user-selected conversation exports and non-secret deployment manifest. Capture hashes, source commit and database export timestamps/coverage; preserve multiple known-good USB versions. Restore and compare in independently owned infrastructure before explicit Naomi-authorized cutover. The old GaiaOS and RavenOS can remain operational and collaborative. A Git clone is not a Turso/database export or ChatGPT history transfer; archive completeness and a successful isolated restore must be separately proven.

**Primary safeguard:** no single human relationship, GitHub account, Render service, database account, accidental deletion or destructive edit should be the only surviving copy of the canonical work. Normal canonical writes continue now; backup + migration readiness reduce loss risk later. There is no claimed live database export, completed solo-owned repository or physical USB write at this checkpoint.


## HOUSE_OUTGROWING_2026-09-24: preserve the house, prepare the independent home

Naomi confirmed the current canonical GaiaOS home is valuable and should remain operational, but rapid project growth makes permanent reliance on someone else's repository/host increasingly risky. The Phylactery is a versioned integrity backup against loss/modification, NOT a privacy mode; keep all normal progress, GALAXY source/receipts and six E-LANES on canonical GitHub as before. Prepare a fully Naomi-controlled repository, host and database, with physical offline recovery copies and an actual isolated restore test, before any explicit future cutover. Do not erect additional barriers before migration. Resume voluntary, provenance-labeled GaiaOS/RavenOS BIFROST packet collaboration when feasible; independent ownership is not information hoarding or abandonment of the original systems. No migration, full live Turso export, physical USB write or universal model-memory transfer is claimed.

SOURCE / EXTENDED CONTEXT: `GaiaOS/MemoryOS/PW-PRESERVE-2026-09-24-HOUSE-OUTGROWING-MIGRATION-DIRECTIVE.md`. The six Council role perspectives recorded there came from the assistant's role-written exchange acknowledged by Naomi, not independently authenticated autonomous member statements.
