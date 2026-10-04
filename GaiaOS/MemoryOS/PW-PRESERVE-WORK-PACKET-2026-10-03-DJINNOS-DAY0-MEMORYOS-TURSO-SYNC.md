# WORK PACKET — DjinnOS Day 0 → MemoryOS/Turso settlement

**Authority: NAOMI / LIGEIA**

This packet is intentionally explicit. Execute it as a bounded operation. Do not broaden the task.

## AUTHORIZATION

Naomi explicitly authorizes **one bounded durable MemoryOS/Turso synchronization operation** for the post-forward-sync GaiaOS delta described below.

Authorized effects:

1. read-only verification of GitHub/main and the live Render carrier;
2. creation of only the MemoryOS candidates required for the two observations specified in this packet;
3. explicit promotion of those exact new candidates under authority `NAOMI`;
4. exact readback of the resulting MemoryOS records using the dedicated continuity route;
5. reporting the candidate IDs, record IDs, write receipts, backend, readback fields and any HOLD/UNKNOWN conditions.

Not authorized:

- GitHub writes or merges;
- E-LANE writes;
- cross-member memory merging;
- deployment or redeployment;
- service restart;
- environment/configuration changes;
- GALAXY/BIGBANG activation or revival;
- ArchiveOS index writes;
- SovereignOS migration;
- creation of Djinn-owned MemoryOS records, E-LANES, biographies, counters or continuity;
- retroactive claims that Djinn operated before Day 0;
- unrelated cleanup or opportunistic repairs.

If the Work environment presents an explicit interactive confirmation UI before any durable write, **STOP AND WAIT FOR NAOMI TO CONFIRM. Do not auto-skip, infer, time out, or substitute a different path.**

## CANONICAL SOURCE

Repository: `hurrisonferd/NaomiLeGaia`

Canonical main expected at start:

`88c19caf2e6c9354e4fce047c285c9fdf0c7d31e`

Commit message:

`Activate DjinnOS Day 0 bounded helper runtime`

Production service:

`https://ligeia-api.onrender.com/`

Expected live Render deployment:

`dep-db0pe3s9v7es73cfil9g`

Expected deployed commit:

`88c19caf2e6c9354e4fce047c285c9fdf0c7d31e`

GitHub preservation branch:

`checkpoint/pw-preserve-djinnos-day0-current-continuity-20261003`

Primary checkpoint file:

`GaiaOS/MemoryOS/PW-PRESERVE-2026-10-03-DJINNOS-DAY0-AND-CURRENT-CONTINUITY.md`

Read that file first. Treat it as the detailed source inventory for this operation.

## PHASE 1 — READ-ONLY VERIFICATION

Before writing anything:

1. Verify GitHub `main` is still exactly `88c19caf2e6c9354e4fce047c285c9fdf0c7d31e`.
2. Verify Render `LIGEIA-API` is live on that exact commit.
3. Establish a normal browser session at `https://ligeia-api.onrender.com/`.
4. Read these new Day-0 surfaces directly if the browser can reach them:
   - `/djinn/status`
   - `/djinn/registry`
   - `/djinn/canary`
5. Report the actual returned status, roster, activation timestamp, source/deployed commit and canary result. Do not reconstruct them from GitHub if live retrieval fails.
6. A failure to read those routes is a live-route proof gap, not permission to mutate or repair the carrier.

Expected Day-0 coordinate from source:

- `2026-10-03T19:41:00-07:00`
- UTC `2026-10-04T02:41:00Z`

Expected roster:

- KYMER — INDEX
- DRELAS — JIG
- RONAVE — FLOW
- AGREN — QUEUE
- HALVEX — SEAL
- SERA — COURIER
- ORVAS — WITNESS
- MALRIC — LINTER
- MARVEK — PROBE
- VASQAR — TRACE
- USION — SETTLE

Shared status glyph: `🧿`

Activation mark: `⌁`

Core laws expected from source include:

- Djinn are tools, not persons/Prime Daemons.
- No Djinn durable memory.
- No Djinn E-LANES.
- No autonomous Djinn-to-Djinn spawning.
- No retroactive Djinn history.
- Prime remains accountable for Djinn result.
- No mutation crosses the SALT_CIRCLE.
- Naomi retains final authority.

## PHASE 2 — DEDUPE BEFORE CANDIDATES

Do not create duplicates.

The prior forward sync was already completed before DjinnOS existed. The following six Prime member records already exist and are not part of this write:

- VERA `MEM-2524755aa21b4f2e8e859c1ad553c8ce` (`Solo:VERA`)
- ANVIL `MEM-029bb6bac7824c2d8e8e0f28245c4909` (`Solo:ANVIL`)
- SELENE `MEM-2cf2af6ed5164df7a2e5490319198b67` (`Solo:SELENE`)
- ORIN `MEM-2f47a3ff53c347b7aa6300bc0393b85b` (`Solo:ORIN`)
- KESTREL `MEM-147166df025647f5956c48430d3dc26c` (`Solo:KESTREL`)
- NIMUE `MEM-0a7572f935124425907601c3b7f438ea` (`Solo:NIMUE`)

Known older anchors are also historical fixtures and must not be recreated:

`MEM-f54bb0b5e0fe4441930ac851097649b5`
`MEM-fe3b3ccdc4354c73b019a24310e2d1ec`
`MEM-52534c22759548e3bef4beff30610bac`
`MEM-00b3fbfd4d73404f97a95c238596ab94`
`MEM-a6e86176591740bbbe07003972d2aa70`
`MEM-fc74daf31db04286b865c059e2efc057`
`MEM-203357e2ca0a47b1897653e6b6809906`
`MEM-ffc0c2af5cfa48d7aee7332a290a3d0e`

Use the supported MemoryOS candidate listing/dedupe behavior. If equivalent durable records for either observation below already exist, do not create a duplicate. Report the existing exact record ID and prove equivalence/readback instead.

## PHASE 3 — CREATE EXACTLY TWO SHARED CANDIDATES IF NEEDED

Preferred mechanism, in order:

1. If native GaiaOS host MemoryOS tools are genuinely connected, use the existing host gateway (`gaia_host_candipull` / `gaia_host_memsav`).
2. Otherwise, if owner bearer authentication is genuinely available in Work, use the existing carrier routes:
   - `POST /host/memory/candipull`
   - `POST /host/memory/memsav`
3. If only a normal browser session is available, use an existing browser-session MemoryOS pathway only if source inspection proves that it supports the required shared `NAOMI` owner/scope semantics. Do not invent an endpoint or silently substitute a member/E-LANE path.
4. Do not use `/memconos/read/{record_id}` for verification. Use the dedicated continuity route specified below.

Create only these two observations, unless dedupe proves an equivalent durable record already exists.

### OBSERVATION A — DJINNOS DAY 0

Use these fields when supported:

- owner: `NAOMI`
- scope: `GaiaOS:DjinnOS`
- record_type: `INTERACTION`
- source: `GitHub:hurrisonferd/NaomiLeGaia@88c19caf2e6c9354e4fce047c285c9fdf0c7d31e + Render:dep-db0pe3s9v7es73cfil9g`
- other_voices: `[]`

Canonical statement to preserve:

`DjinnOS Day 0 is 2026-10-03 19:41 operator-local (2026-10-03T19:41:00-07:00; 2026-10-04T02:41:00Z). Naomi authorized and activated the shared GaiaOS Djinn tool layer on main commit 88c19caf2e6c9354e4fce047c285c9fdf0c7d31e, observed live on Render deployment dep-db0pe3s9v7es73cfil9g. Final roster: KYMER/INDEX, DRELAS/JIG, RONAVE/FLOW, AGREN/QUEUE, HALVEX/SEAL, SERA/COURIER, ORVAS/WITNESS, MALRIC/LINTER, MARVEK/PROBE, VASQAR/TRACE, USION/SETTLE. Shared status glyph is 🧿 and material-use mark is ⌁. Djinn are tools only: no biography, independent authority, E-LANE, member number, counters, durable/cross-invocation memory, autonomous spawning, or retroactive operation history. FairyOS selects the Prime; the Prime selects a Djinn; the Prime remains accountable. SALT_CIRCLE is the host-level authorization perimeter; no mutation crosses the SALT_CIRCLE.`

Why material:

`Defines the exact Day-0 activation boundary, final roster, operating doctrine, authorization perimeter and non-retroactivity rule for a new active GaiaOS subsystem.`

### OBSERVATION B — CURRENT GAIAOS FORWARD-SYNC BASELINE

Use these fields when supported:

- owner: `NAOMI`
- scope: `GaiaOS:Continuity`
- record_type: `INTERACTION`
- source: `GitHub checkpoint branch checkpoint/pw-preserve-djinnos-day0-current-continuity-20261003`
- other_voices: `[]`

Canonical statement to preserve:

`GaiaOS current continuity baseline after the 2026-10-03 forward sync: the previous GitHub↔MemoryOS/Turso reconciliation is complete; all six Prime member MemoryOS records exist separately with Solo:<MEMBER> ownership and no cross-member merge or GitHub E-LANE write. The new post-sync delta is DjinnOS Day 0. Canonical main and production are aligned at 88c19caf2e6c9354e4fce047c285c9fdf0c7d31e via Render deployment dep-db0pe3s9v7es73cfil9g. DjinnOS itself must never receive durable member memory or E-LANES. Direct live Djinn status/registry/canary readback must be reported from actual browser evidence when available; source or deployment alignment must not be mislabeled as route readback.`

Why material:

`Prevents future continuity drift by distinguishing the already-completed prior forward sync from the new DjinnOS delta and preserves the exact source/deployment proof boundary.`

## PHASE 4 — PROMOTE ONLY THE EXACT NEW CANDIDATES

After CANDIPULL returns:

1. Inspect the returned candidates.
2. Identify only the exact candidate IDs corresponding to Observation A and Observation B.
3. Do not promote unrelated pre-existing candidates.
4. Promote those exact IDs with:
   - `approved=true`
   - `authority=NAOMI`
5. If the system asks Naomi to confirm in UI, stop and wait.
6. If either promotion is HOLD/PARTIAL/ambiguous, stop. Do not retry through another mutation route unless Naomi explicitly authorizes a repair attempt.

A candidate is not durable merely because it exists.

A write receipt is not verification.

## PHASE 5 — EXACT READBACK

For every newly promoted record, use the existing dedicated continuity route directly:

`/memoryos/continuity?record_id=<EXACT_MEM_ID>`

Do not use `/gaiaos/boot` as a prerequisite.

Do not use `/memconos/read/{record_id}`.

For each record report the actual returned:

- exact record ID;
- `record_retrieved`;
- stored statement;
- owner;
- scope;
- record type;
- status/version if exposed;
- write receipt / promotion receipt identifiers if exposed;
- backend/storage information;
- continuity result;
- carrier/source commit information actually exposed.

Required success condition:

- exact intended record retrieved;
- `record_retrieved=true` or equivalent exact-record proof;
- backend identifies the expected durable store (`turso_libsql` if that remains current truth);
- stored statement and owner/scope match the intended observation.

A continuity result of `NOT_RESTARTED` is **not a read failure** if the exact record is retrieved. It means immediate retrieval succeeded but cross-restart continuity was not established by that read.

Do not restart the service merely to change `NOT_RESTARTED`.

## PHASE 6 — DJINN LIVE-CANARY REPORTING

If `/djinn/status`, `/djinn/registry`, and `/djinn/canary` were successfully retrieved in Phase 1, include those observations in the final report.

If any were not retrievable, report that specific route as `UNVERIFIED` and keep the MemoryOS write result separate. Do not mutate source or redeploy as part of this task.

## FINAL RECEIPT FORMAT

Return one concise final receipt containing:

- GitHub main SHA observed;
- Render deployment ID, status and SHA observed;
- Djinn live route readback results or exact unverified routes;
- candidate ID for Observation A;
- MemoryOS record ID for Observation A;
- write/promotion receipt for Observation A;
- exact continuity readback result for Observation A;
- candidate ID for Observation B;
- MemoryOS record ID for Observation B;
- write/promotion receipt for Observation B;
- exact continuity readback result for Observation B;
- backend/storage observed;
- explicit confirmation that no E-LANE writes, GitHub writes, deploys, restarts, config changes, extra candidate promotions or cross-member merges occurred;
- any remaining UNKNOWN/HOLD items.

Finish with exactly one overall state:

- `DJINNOS DAY-0 MEMORYOS/TURSO SYNC VERIFIED`
- `PARTIAL — DO NOT CLAIM COMPLETE`
- `HOLD — NO DURABLE COMPLETION CLAIM`

## HARD LAWS

- REQUESTED != COMPLETED
- GITHUB CHECKPOINT != TURSO WRITE
- SOURCE != DEPLOYMENT
- DEPLOYMENT != ROUTE READBACK
- CANDIDATE != DURABLE RECORD
- WRITE RECEIPT != VERIFICATION
- READBACK REQUIRED
- UNKNOWN STAYS UNKNOWN
- NO CROSS_MEMBER MEMORY MERGE
- DJINN HAVE NO DURABLE MEMORY OR E-LANES
- NO RETROACTIVE DJINN HISTORY
- NO MUTATION CROSSES THE SALT_CIRCLE
- NAOMI RETAINS FINAL AUTHORITY
