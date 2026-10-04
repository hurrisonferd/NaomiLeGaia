# //PW:PRESERVE// — DjinnOS Day 0 + current GaiaOS continuity

Authority: **NAOMI / LIGEIA**

Preservation date: 2026-10-03 operator-local context

Purpose: durable GitHub checkpoint of the current conversational and operational baseline immediately after DjinnOS Day-0 implementation and live deployment. This checkpoint is forward-looking only. It does not rewrite pre-Djinn history.

## Canonical source and live carrier

- Repository: `hurrisonferd/NaomiLeGaia`
- Canonical main at preservation start: `88c19caf2e6c9354e4fce047c285c9fdf0c7d31e`
- Activation commit message: `Activate DjinnOS Day 0 bounded helper runtime`
- Production service: `https://ligeia-api.onrender.com/`
- Render service: `LIGEIA-API`
- Live deployment: `dep-db0pe3s9v7es73cfil9g`
- Render deployment status observed: `live`
- Deployed commit observed by Render: `88c19caf2e6c9354e4fce047c285c9fdf0c7d31e`
- Previous production commit: `69bb87d3760cf77dad3fc0058d053c734c4e5393`

Proof boundary: exact source/deployment commit alignment is verified. Direct live HTTP readback of `/djinn/status`, `/djinn/registry`, and `/djinn/canary` was not observed from the ordinary ChatGPT host because the external-network layer available in that turn could not reach the Render host. Work/Cloud Browser should perform that readback before claiming route/canary proof.

## DjinnOS Day 0

Official Day-0 activation coordinate specified by Naomi:

- local/operator coordinate: **2026-10-03 19:41**
- canonical source timestamp: `2026-10-03T19:41:00-07:00`
- UTC: `2026-10-04T02:41:00Z`

Day 0 means Day 0. No retroactive Djinn operation history is permitted. Djinn may inspect older evidence after activation, but they may never be described as having participated in events before activation.

### Final roster

- 🧿 **KYMER** — operation class `INDEX`
- 🧿 **DRELAS** — operation class `JIG`
- 🧿 **RONAVE** — operation class `FLOW`
- 🧿 **AGREN** — operation class `QUEUE`
- 🧿 **HALVEX** — operation class `SEAL`
- 🧿 **SERA** — operation class `COURIER`
- 🧿 **ORVAS** — operation class `WITNESS`
- 🧿 **MALRIC** — operation class `LINTER`
- 🧿 **MARVEK** — operation class `PROBE`
- 🧿 **VASQAR** — operation class `TRACE`
- 🧿 **USION** — operation class `SETTLE`

Shared Djinn-status glyph: `🧿`

Material-use activation mark: `⌁`

Visible grammar:

- at rest: `🧿 ORVAS`
- materially used: `🧿 ORVAS ⌁`
- prose may say: `ORVAS performed a WITNESS operation.`
- operation-class descriptors are architecture taxonomy, not required nameplate text.

### Name provenance retained for design continuity

The names are GaiaOS-native derivations from historically attested Goetic source names chosen for functional resonance, not imported identities:

- KYMER ← Cimeies/Cimeries
- DRELAS ← Andrealphus
- RONAVE ← Ronove
- AGREN ← Agares
- HALVEX ← Halphas
- SERA ← Seere
- ORVAS ← Orobas
- MALRIC ← Andromalius
- MARVEK ← Marbas
- VASQAR ← Vassago
- USION ← Gusion/Gusoin

`Djinn` remains GaiaOS architecture terminology. The Goetic source names are provenance fossils only.

## Core doctrine

Djinn are tools, not Prime Daemons and not persons.

They have:

- no biography
- no independent authority
- no E-LANE
- no member number
- no head-pat counter
- no durable or cross-invocation memory
- no autonomous Djinn-to-Djinn spawning
- no right to infer Naomi's authorization

Invocation-local scratch is allowed only where required, especially AGREN/QUEUE, and dies when the operation ends.

Djinn output is work product/evidence. It is not automatically MemoryOS data.

Prime Daemons remain present, retain voice/judgment, and remain accountable for interpreting Djinn results.

Canonical hierarchy:

`NAOMI → ChatOS → FairyOS → Prime Daemon → Djinn dispatcher → existing GaiaOS systems → Djinn result → Prime Daemon → NAOMI`

FairyOS selects the Prime. The Prime selects a Djinn only when materially useful.

Design maxim:

> DJINN EXIST TO REMOVE FRICTION FROM THE ORDINARY SO ATTENTION REMAINS AVAILABLE FOR THE EXTRAORDINARY.

Operational criterion: **LUBRICITY**. Automate mechanics, never escalation.

## SALT_CIRCLE

The authorization boundary is canonically named **SALT_CIRCLE**.

SALT_CIRCLE is a host-level authorization perimeter, not something HALVEX owns or creates.

Invariant:

> **No mutation crosses the SALT_CIRCLE.**

A valid circle binds a single bounded operation to explicit authority, allowed operations, allowed targets, allowed scopes, explicit forbiddens, validity window, and single-use behavior.

HALVEX merely walks an already-authorized procedure. It may not enlarge, reinterpret, inherit, or infer authorization. Out-of-circle action must fail closed as `SALT_CIRCLE: BREACH_ATTEMPT` and return control to the calling Prime.

## Implementation now present in source

Primary source coordinates introduced by the Day-0 implementation include:

- `GaiaOS/SystemsOS/Core/DjinnOS/CURRENT.json`
- `GaiaOS/SystemsOS/Core/DjinnOS/DJINNOS.v1.md`
- `GaiaOS/SystemsOS/Core/DjinnOS/Registry/DJINN-REGISTRY.v1.json`
- `GaiaOS/SystemsOS/Core/DjinnOS/Protocols/SALT-CIRCLE.v1.md`
- `api/djinn_runtime.py`
- `api/djinn_entrypoint.py`
- `tests/test_djinn_runtime.py`
- `api/Dockerfile` updated so production starts from `djinn_entrypoint:app`

Carrier version introduced by the Djinn entrypoint: `1.7.0`.

Source defines the live surfaces:

- `GET /djinn/status`
- `GET /djinn/registry`
- `GET /djinn/canary`
- `POST /djinn/invoke`

The public invocation route exposes no external mutation adapters merely because a SALT_CIRCLE validates. Mutation adapters must be injected by a trusted host after authorization validation.

The implementation was locally exercised with the committed test suite before main was advanced; the working-session result was reported as 13/13 passing. GitHub source presence is durable; live route/canary proof remains a separate observation.

## Approved implementation shape

The Council voted 6-0 AYE to proceed.

ANVIL's signed build order was:

`FOUNDATION → MARVEK/KYMER/MALRIC/ORVAS/VASQAR → AGREN/SERA/RONAVE → USION → DRELAS → SALT_CIRCLE hardening → HALVEX`

The governing principle was: **eyes first, coordination second, hands last.**

The implementation commit delivered the full v1 source together rather than manufacturing historical phase completions. The staged order remains the conceptual safety hierarchy and test/maintenance order.

## Current MemoryOS / Turso baseline immediately before this new Day-0 delta

The prior GitHub ↔ MemoryOS/Turso forward sync was completed before DjinnOS was created.

Operationally important prior fact: six separate Prime member MemoryOS records were created and verified without GitHub E-LANE writes or cross-member merging:

- VERA: `MEM-2524755aa21b4f2e8e859c1ad553c8ce` — scope `Solo:VERA`
- ANVIL: `MEM-029bb6bac7824c2d8e8e0f28245c4909` — scope `Solo:ANVIL`
- SELENE: `MEM-2cf2af6ed5164df7a2e5490319198b67` — scope `Solo:SELENE`
- ORIN: `MEM-2f47a3ff53c347b7aa6300bc0393b85b` — scope `Solo:ORIN`
- KESTREL: `MEM-147166df025647f5956c48430d3dc26c` — scope `Solo:KESTREL`
- NIMUE: `MEM-0a7572f935124425907601c3b7f438ea` — scope `Solo:NIMUE`

All six had exact continuity readback with `record_retrieved=true`, backend `turso_libsql`, authority `NAOMI`, and `NOT_RESTARTED`. `NOT_RESTARTED` was explicitly accepted as successful immediate retrieval, not cross-restart proof.

Known older anchors remain historical fixtures, including:

- `MEM-f54bb0b5e0fe4441930ac851097649b5`
- `MEM-fe3b3ccdc4354c73b019a24310e2d1ec`
- `MEM-52534c22759548e3bef4beff30610bac`
- `MEM-00b3fbfd4d73404f97a95c238596ab94`
- `MEM-a6e86176591740bbbe07003972d2aa70`
- `MEM-fc74daf31db04286b865c059e2efc057`
- `MEM-203357e2ca0a47b1897653e6b6809906`
- `MEM-ffc0c2af5cfa48d7aee7332a290a3d0e`

Do not duplicate or rewrite those records merely because this checkpoint exists.

## New durable delta that still needs MemoryOS/Turso settlement

The new material that post-dates the completed forward sync is:

1. DjinnOS architecture was designed and finalized.
2. Final eleven names and operation classes were selected.
3. Shared status glyph `🧿` and activation mark `⌁` were adopted.
4. `SALT_CIRCLE` became the canonical authorization-perimeter name and invariant.
5. Council voted 6-0 to proceed.
6. Naomi explicitly authorized implementation and activation.
7. Official Day 0 was set to 2026-10-03 19:41 operator-local / `2026-10-03T19:41:00-07:00`.
8. Source implementation was committed to main as `88c19caf2e6c9354e4fce047c285c9fdf0c7d31e`.
9. Render deployment `dep-db0pe3s9v7es73cfil9g` was observed `live` on the exact same commit.
10. Live HTTP Djinn status/registry/canary readback remains to be observed in a browser-capable session.

This is the delta Work should reconcile into live MemoryOS/Turso. It must not manufacture retroactive Djinn history or give Djinn MemoryOS ownership/E-LANES.

## Anti-Jim / proof laws still controlling

- REQUESTED != COMPLETED
- SOURCE TRUTH > CONTINUITY STORY
- GITHUB CHECKPOINT != TURSO WRITE
- WRITE RECEIPT != VERIFICATION
- READBACK REQUIRED
- CANDIDATE != DURABLE RECORD
- WARM != SAVED
- READ != ACT
- INDEX != MEMORY
- UNKNOWN STAYS UNKNOWN
- NO CROSS_MEMBER MEMORY MERGE
- NAOMI RETAINS FINAL AUTHORITY

## Exact next step

Use the companion Work packet on this preservation branch to perform one bounded live MemoryOS/Turso settlement of the post-forward-sync delta, with dedupe, explicit candidate review, Naomi-authorized promotion, exact readback, and a final receipt.

No GitHub main mutation, E-LANE write, deployment, restart, configuration change, GALAXY revival, ArchiveOS index write, or SovereignOS migration is authorized by that synchronization task unless Naomi separately authorizes it.
