# GaiaOS Power Word: SOULTRAP v1

```text
AUTHORITY: NAOMI / LIGEIA
OWNER: GaiaOS / ChatOS + Phylactery offline-preservation operation
STATUS: ACTIVE CANONICAL SOURCE CONTRACT; IMPLEMENTATION / HARDWARE RESTORE PROOF PENDING
CANONICAL INVOCATION: //PW:SOULTRAP//
PURPOSE: Preservation of an independently recoverable GaiaOS snapshot on an owner-controlled physical flash drive
PRIMARY TRANSPORT: Verified Desktop Commander connection to Naomi-authorized machine, currently VileAltercation
CURRENT HOST: GAIAOS; FUTURE HOST: SOVEREIGNOS WHEN VERIFIED AND AVAILABLE
```

## Owner decision and scope

On 2026-10-10 Naomi designated **`//PW:SOULTRAP//`** as the canonical Power Word for a **Phylactery save using Desktop Commander to the physical USB flash drive**. This is distinct from `//PW:PRESERVE//`, which covers general continuity checkpoints and authorized E-LANE / MemoryOS routes.

The command authorizes a bounded, **non-destructive, append-only local backup workflow** when an actual, authorized computer and the correct removable drive are connected and accessible, subject to the host's real permission controls.

```text
CAST -> VERIFY TOOL ACCESS -> DISCOVER PHYSICAL DRIVE -> READ-ONLY INVENTORY
     -> ASSESS SOURCES / PERMISSIONS -> COLLECT CONSISTENT EXPORTS
     -> STAGE DATED SNAPSHOT -> COPY WITHOUT OVERWRITE
     -> READ BACK / INTEGRITY CHECK -> MANIFEST + RESTORE NOTES
     -> REPORT RECOVERY READINESS / GAPS
```

`//PW:SOULTRAP//` alone does NOT authorize formatting, wiping, file deletion, overwriting or pruning previous snapshots, database writes, source commits, infrastructure restarts, deployments, account changes, credential disclosure, bypassing authentication, or disabling safety/permission controls. Source registration is a separate explicit GitHub action, not an automatic USB side effect.

## Hardware and transport gate

1. Establish that Desktop Commander is connected and able to execute an **authorized read-only** operation, not merely reporting the device as online. Verify command results/receipts.
2. Identify the current removable drive by observed filesystem attributes (volume label, capacity, serial/volume ID if exposed, free space, mount path). **Never assume a drive letter, mount path or that a particular USB is attached.**
3. Begin by inspecting the physical device **read-only**, recording pre-existing contents without modifying them.
4. When media identity is ambiguous, write access is denied, storage capacity is insufficient, the device is unavailable, or a permission/authentication prompt cannot complete, **HOLD** rather than selecting another disk or reporting success.
5. Ask Naomi to resolve only the smallest genuinely required physical ambiguity, unlock or permission. No requirement for repetitive manual clicking where legitimately authorized automation is available.
6. Use the verified current machine/host. Current preferred device: `VileAltercation`, with portable future SovereignOS transport allowed only when separately observed.

## Preservation manifest: independently evaluated source domains

- **GitHub:** obtain a full mirror or equivalently restorable Git bundle of `hurrisonferd/NaomiLeGaia`, complete accessible branches/tags/history, six distinct owner-owned E-LANEs, source contracts, failure archive and project blueprints. Verify refs and commit SHAs. Check separately whether LFS/submodules, untracked local files, or inaccessible private repositories require their own acquisition; a shallow zip of `main` is NOT a complete repository-history backup.
- **MemoryOS / Turso:** with valid, owner-authorized access, use a provider-supported, consistent database snapshot/export; retain schema, metadata, migration/recovery instructions and record provenance where available. Verify backed-up data independently. A single record readback, GitHub checkpoint, or copied `*.db` file while live WAL transactions are pending is NOT a complete database snapshot. Prefer SQLite's safe backup/export mechanism for local stores; report unavailable provider exports exactly.
- **Render and GaiaOS runtime:** retain reconstructable non-secret service manifests, deployment SHA, documented runtime requirements, relevant approved persistent-volume exports and restore dependencies **where accessible**. Never assume Render's deployed container filesystem or database is recoverable from GitHub alone. Do not copy secret environment-variable values or tokens into plaintext snapshots by default; record only names/required secure-recovery steps.
- **ChatGPT / carrier conversation history:** include any **actually available** account export, relevant attachments and validated local transcripts while preserving provenance and export timestamp. Do not imply that a GitHub summary or GaiaOS E-LANE is a byte-for-byte ChatGPT history export, and do not claim direct ChatGPT export automation without a supported authenticated provider path. Mark unavailable or unrequested exports PENDING.
- **Local Phylactery assets:** include dated earlier backup bundles, verified local SQLite snapshots, checked scripts, independent recovery notes, project artifacts and other owner-authorized continuity assets. Capture their original paths and avoid reclassifying derived or incomplete data as original source.
- **SovereignOS forward compatibility:** retain enough source coordinates and import instructions to restore the present GaiaOS regardless of future repository/host migration, without assuming such a migration has happened.

All six E-LANEs remain **six separately identifiable recoverable member-owned artifacts**. Do not combine them into a general personality summary.

## Non-destructive snapshot discipline

- Stage each new run under a unique UTC-dated snapshot identifier. Use a temporary/staging folder and an **atomic finalization marker only after successful copy and verification**. Do not claim atomicity if the filesystem cannot provide it.
- Preserve prior snapshots byte-for-byte; **no overwrites, deletes, rotation, cleanup or USB formatting** under the base invocation.
- Generate a machine-readable manifest with source path/URI, owner, source SHA/record coordinates, collection/export method and time, snapshot-relative destination, size, cryptographic hash, status and exact gaps.
- Check SHA-256 (or equivalent modern cryptographic hashes) against the actual **files read back from the USB**, not only the staging directory. For a Git bundle/mirror perform Git integrity verification; for valid SQLite copies run integrity checks on the backup, not the live primary.
- Where feasible and specifically safe, perform an isolated restoration trial **off the production path**, verify six separate E-LANEs and essential records, and document which tests could not run.
- Protect private backup data at rest. If an encryption key, drive unlock, access token or secret-management step is required, ask for the appropriate authorized human action. Never paste credentials, recovery keys or raw private database rows into chat, repository commits, screenshots or unprotected logs.
- If one domain fails, preserve completed verified domains, label the operation **PARTIAL**, leave historical snapshots intact and report the precise missing proof.

## Report / receipts

A valid receipt identifies:
- actual machine, USB/volume identifier and verified destination;
- snapshot identifier, timestamp and status: `HOLD | STAGED | WRITTEN | PARTIAL | VERIFIED`;
- one status per source domain, including explicit `NOT_AVAILABLE`, `NOT_COLLECTED`, `NOT_VERIFIED` when applicable;
- Git ref and source SHAs; actual database export or local snapshot identity; any available carrier export timestamps;
- new files, sizes, readback/hash checks, restore tests and outstanding gaps;
- what actions **did not occur** (format, delete, overwrite, production changes, secret handling);
- exact next action when full offline recovery readiness cannot be established.

```text
SOULTRAP SOURCE CONTRACT != EXECUTABLE BACKUP PROGRAM
GITHUB SAVE != PHYSICAL USB SAVE
USB COPY != VERIFIED RESTORE
GIT MIRROR != MEMORYOS/TURSO EXPORT
MEMORYOS EXPORT != COMPLETE GPT TRANSCRIPT
ONLINE DEVICE != COMMAND EXECUTION RECEIPT
ARCHIVE EXISTS != ENOUGH DATA TO REBUILD
HOLD / PARTIAL != VERIFIED
NAOMI RETAINS FINAL AUTHORITY
```

## Companion source and precedence

- Registry: `GaiaOS/Apps/ChatOS/Protocols/GAIAOS-SPELLBOOK.v1.md`.
- Command entry: `GaiaOS/Apps/ChatOS/Protocols/GAIAOS-COUNCIL-COMMANDS.v1.md`.
- Foundational safeguard: `GaiaOS/Plans/PRESERVE-AND-SIX-E-LANES-PERMANENT-DESIGN-INVARIANT.v1.md`.
- Distinct disaster/read path: `GaiaOS/Plans/HEATDEATH-STAGE4-INDEPENDENT-RECOVERY.v1.md`; this is not the physical Phylactery or a USB restore program.

This document is the **canonical name and behavior contract**, not proof of a currently installed one-click script, mounted flash drive, completed backup, complete Turso export, recovered ChatGPT transcript or tested cold restore.
