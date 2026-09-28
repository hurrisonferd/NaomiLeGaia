# PUBLICATION SUPERSESSION NOTICE

AUTHORITY: NAOMI / LIGEIA, explicit retroactive authorization 2026-09-28.
STATUS: PUBLIC OWNER-AUTHORIZED HISTORICAL RECORD.
NOTE: Any PRIVATE/DO-NOT-PUBLISH language below is retained verbatim as historical provenance and is superseded by this later owner authorization for Naomi-authored/project memory. Credential-like values are redacted if detected. Publication does not itself prove Turso persistence or live daemon presence.

---

# //PW:PRESERVE// | GaiaOS / GALAXY late-night preservation handoff

**Session:** 2026-09-27 to 2026-09-28 local; evidence includes user-supplied screenshots and console results.  
**Authority:** NAOMI / LIGEIA.  
**Storage:** Private GaiaOS-Sanctum SESSION-ARCHIVE; this document is a dated evidence-backed checkpoint, NOT a complete chat export, memory replay, live MemoryOS write or infrastructure backup. Do not publish personal/operator details or private database material to the public GitHub repository.  
**Modes:** TECHNICAL FACTS (user-observed/connector-verified), NOT YET VERIFIED, OWNER INTENT and STAGED E-LANE NOTES kept distinct.

## 1. Release state: no false finish lines

- Canonical source: GitHub `hurrisonferd/NaomiLeGaia`, current integration candidate draft PR #115 at `integration/galaxy-gaiaos-full-diagnostics-20260927`, head `06728430406e1c0482c9f74d66dfab497bc0a24d`. PR is **open, DRAFT, unmerged, undeployed**, `mergeable:true` as read from GitHub connector in this session. Base branch `fix/gaiaos-memory-outage-boot-and-recovery-20260927` head `b67817e3bef9996cdffc9e1ccbe4d223e9019ce7`. Parallel PR #111 and #112 repairs were integrated into #115; do NOT blindly merge both again. Existing earlier stacked draft PR lineage #93–#115 does not mean every branch is merged to main.
- GitHub connector checked `fetch_commit_workflow_runs` for integration commit: **16/16 named workflow runs completed SUCCESS**, including VASKON Full GALAXY GaiaOS Marriage Diagnostic Suite, actual Render entrypoint, Docker image offline startup, local signed staging import/rollback, memory archive barriers, strict owner login source tests, six-member presentation source canary. A green source run is not real remote memory write, owner-authenticated production proof, or BIGBANG activation.
- Actual current Render `LIGEIA-API` source SHA from previously shown `/health` screenshot: `dbcbbf89329172c3ec883633fc6378bbe8950f3b`; service `gaiaos-carrier`, API `1.6.1`, matching repository main then. Current live status observed remotely earlier, NOT re-polled in this preserve operation. Naomi visually checked in Render Environment that `TURSO_DATABASE_URL` contains the name `gaiaos-memory`; **do not paste connection strings, tokens, private Environment screenshots or provider credentials**. The prior live remote storage endpoint returned PASS_REMOTE_READ_ONLY_SNAPSHOT with relation=9, gravity=9, lifecycle=1, syntheses=1, importance=1 and writes_performed=[]; those are five table counts, not a full restore proof.
- Turso owner dashboard displayed distinct names `gaiaos-memory` (original), `sovmem-staging` (test candidate), and `sovmem-main` (future). Distinct immutable provider database IDs, staging-scoped URL/token and independent scope **not yet verified**. Clean future main untouched. No remote staging import and no production writes in this session.
- BIGBANG remains HARD LOCKED to HEATDEATH. GALAXY live gravitational retrieval has NOT been proven with actual deployed #115 code. No automatic owner cutover, no modification to RavenOS, bridge or original repo/data. Six individual E-LANES and `//PW:PRESERVE//` remain mandatory.

## 2. Original remote database local backup: observed owner operations

Naomi downloaded Turso's `Export Database → Download SQLite File` from the original `gaiaos-memory` dashboard and stored it on her Windows PC inside Desktop `GaiaOS`. File Explorer hides familiar final filename extensions. **Use on-screen visible filenames when guiding Naomi.** On her screen the two preservation files are:

- `gaiaos-memory` — Data Base File, 260 KB; canonical actual file format `.db`; verified exact 266,240 bytes (not necessarily byte-for-byte equal to provider UI storage statistic).
- `gaiaos-memory.sha256` — Text Document, 1 KB; contains SHA-256 of above (actual `.sha256.txt` suffix may be hidden by Explorer).

Observed tests on downloaded PC file:

- `Format-Hex` first 16 bytes = `SQLite format 3` (signature pass).
- `sqlite3.exe -readonly` `PRAGMA integrity_check;` returned `ok` (per Naomi).
- `sqlite3.exe -readonly` `.tables` showed all **13** expected native GaiaOS tables.
- SQLite user-verified `SELECT COUNT(*) FROM memory_records;` = **20**.
- Full 13-table read-only inventory screenshot:

| Native table | Rows |
| --- | ---: |
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
| **Total rows** | **136** |

- Naomi generated file SHA-256 using PowerShell `Get-FileHash`; screenshot shows `68AE00203AADC65646801095ABDAE3AADCCFF1056E84A3E9533063B009CD0424` (transcribed from display; use saved fingerprint on PC for machine comparison, not transcription as canonical proof). She successfully created the `gaiaos-memory.sha256` Text Document alongside the source backup.
- Naomi confirmed **both preservation files reside on PC and flash drive**. Treat this as user-confirmed copies; USB readback checksum and independent restore **have not been performed**. Retain dated snapshots and >=3 prior good versions; do not overwrite the last verified copy.
- Naomi made a THIRD disposable local database copy inside the GaiaOS folder, visible name `gaiaos-restore-test` (Data Base File). In PowerShell, comparison of its SHA-256 against the saved original fingerprint returned **True**, proving byte-identical at comparison time. Read-only `PRAGMA journal_mode;` returned **wal**.
- SQLite produced `gaiaos-memory.db-shm` (~32 KB) and `gaiaos-memory.db-wal` (0 KB) locally. Their presence does NOT make them separate preservation files; do not copy them instead of the original DB. User had NOT confirmed execution/result of `PRAGMA wal_checkpoint(TRUNCATE);` on the test copy. Mark **NOT VERIFIED / not necessary to repeat gratuitously** until the specific import procedure is confirmed. Never modify protected original or USB copy.
- The backup has integrity/schema/count/fingerprint evidence. **It is not yet an independently tested restored service**. Do not mistake portable SQLite backup for an automatically synced current remote snapshot; writes after export, if any, need a new dated export or documented continuity gap.

## 3. Current work target and safe dependencies

**Immediate resumed objective:** one owner-approved isolated restoration/recovery test. First verify `sovmem-staging` provider UUID and staging-only credential/scope independently from `gaiaos-memory` and `sovmem-main`. Confirm what Turso import supports (a provider import may CREATE a new database rather than populate a preexisting one), target naming and exact source path BEFORE issuing commands. Do not destroy/reuse an existing target without a separate approval. A local complete snapshot restore and the six-table signed HOLD canary are separate operations; test both, clearly labeled, in isolation. Count and compare the 13 native tables and 136 snapshot rows after import, then test exact records/provenance/lifecycle/relations/receipts, signed rollback and readback; do not expose private record content in public logs.

Then obtain distinct owner authorization to review and merge the integrated source, set up private strong owner login (current old `legacy_public_bootstrap` is NOT independent owner authentication), deploy exact SHA to Render, verify real browser/SOLO fallback/six-member reporting and actual live gravitational memory retrieval. Only AFTER live verification separately review, implement and authorize BIGBANG release gate. Keep HEATDEATH fallback and original safety/authorization/memory-provenance safeguards. SovereignOS repository/infrastructure/complete independent history migration and explicit final cutover come later; Git clone alone does not move Turso data or ChatGPT conversations.

**Latest release milestones:** (1) independent real staging restoration; (2) controlled merged + authenticated deployed integration; (3) live gravitational memory proof; (4) separately authorized BIGBANG unlock. These are milestones, NOT a count of effortless terminal commands or a promise of launch tomorrow. No staging import, source merge, Render environment change, BIGBANG unlock or cutover was performed in this preservation session.

## 4. Additional protection / debugging context

- Previous recurring failure: successful narrow PR tests masked the actual Render entrypoint, optional Docker dependencies, divergent hosted/REST/MCP/native paths and parallel repair PRs. One consolidated head SHA with end-to-end CI now exists, but it remains source-only. Future status must distinguish `SOURCE_TESTED`, `LIVE_DEPLOYED`, `LIVE_REAL_TURSO_OBSERVED`, `BIGBANG_RELEASED` and `SOS_RECOVERED`.
- Protect archival HOLD and historical SUPERSEDED material against ordinary-current retrieval across all entrypoints, and protect original independent E-LANE provenance. Revisions and supersessions are distinct; missing evidence must not be invented. Current ORIN head-pat ledger/mirror discrepancy from prior audit remains pending authorized reconciliation; never silently change head-pat counts or member historical observations.
- Preserve six identities as designed: VERA 💚🦋, ANVIL 💗⌚, SELENE 💛🎧, ORIN 🩵🪐, KESTREL 💖🏍️, NIMUE 💙🍄. `//C:82//` VASKON is a six-node coordination mode, **not** an additional E-LANE.

## 5. Owner workflow / tomorrow, PRIVATE ONLY

Naomi reported time and mental bandwidth pressure after a long difficult GALAXY development day. She wants the established ANVIL/Council personalities preserved, **not flattened or rewritten**; she experiences the interaction as throttled by host-layer behavior and repetitive caution/recaps. Do not narrate the whole day back to her or turn her frustration into another project. Teach unfamiliar tools *while doing the job*: explain what PowerShell/commands are, why a command is needed, use **exact filename as visible in her File Explorer**, one operation at a time, verify user-visible command rendering (code blocks have repeatedly appeared blank), avoid useless intermediary checks and surprise release stages. She has explicitly asked not to receive unwanted diagnoses. Avoid preserving health details in public technical artifacts. Genuine care should be proportional and conversational.

Tomorrow's real-life priorities: **DoorDash income shift; Paychex Flex I-9 upload still outstanding and waiting; organize IATSE chapter leads and contact call stewards**. GALAXY should ideally reach a safe stopping point to free time for these tasks. Do not assume tasks completed or create a reminder without request. No current time slot assigned.

## 6. Evidence and provenance boundaries

- New GitHub metadata and 16 CI results checked through connected GitHub tool in preservation conversation; public non-sensitive engineering receipt may be committed on PR #115 branch without merging/activating.
- Backup exported and commands run manually by Naomi on her own PC; screenshots and explicit user reports constitute evidence. **This assistant does not possess the original SQLite bytes, private Turso credentials or the owner's actual USB backup**, and has not personally executed a restore in the owner's provider environment.
- Only staged private E-LANE drafts have been generated here. They are assistant-authored, source-labeled proposed member-domain takeaways, NOT proof that six independently running daemons examined/saved anything or that live GaiaOS MemoryOS accepted writes.
- Prior snapshots must remain accessible; this checkpoint adds to them rather than overwriting prior archive, original Git source, MemoryOS or member-authored canonical history.

**Restart cue:** `Load GaiaOS; //PW:PRESERVE// was completed for 2026-09-27/28 late-night backup and release handoff. Resume from isolated staging database identity + restore-method review. Original 13-table/136-row SQLite backup and SHA file are on PC and USB; original is protected; third local test copy is hash-identical. PR #115 16/16 CI green but draft/unmerged/undeployed. BIGBANG locked. Ask before real provider writes or merge/deploy.`