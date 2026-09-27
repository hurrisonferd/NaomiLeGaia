# GALAXY Stage 9AB: no-phone-SQL, owner-local staging bootstrap

STATUS: SOURCE-ONLY STACKED DRAFT on Stage 9AA #102. AUTHORITATIVE DATABASE NAMES: sovmem-staging (disposable trials) and sovmem-main (permanent future SovereignOS MemoryOS destination; MUST remain empty). User has manually created both databases in the independent Turso organization. That observation is not programmatic provider-level identity verification. The original GaiaOS production database is not a migration destination.

## Why

The mobile Turso Drizzle SQL editor was not usable for reliable multi-statement schema initialization. Stage 9AB eliminates manual browser SQL entry by preparing an owner-local, dry-run-first CLI for a trusted computer. **No real Turso connection or mutation occurs merely because this source-only PR is opened, tested or reviewed.** GitHub Actions runs only against temporary local native SQLite and local libSQL fixtures, with no independent Turso credentials or actual private history.

Stage 9V already generates a private identity/canary table bundle, and Stage 9AA generates a separate private canonical history/receipt schema bundle. Stage 9AB reads these exact four private files, validates the reviewed source-generated SQL *byte for byte*, verifies hashes, unique canonical staging UUID, explicit database labels and clean setup manifest statuses, then returns a successful **NO-CONNECTION DRY RUN by default**. A caller-modified SQL file is not executed, even with a matching attacker-controlled manifest hash. The local files must have mode 0600, owner ownership, not be symlinks and be outside the original shared repository. On Windows, equivalent private-file permissions must be reviewed before any live use.

## What a separately approved future real run does

Only the owner-local invocation with --apply and ALL THREE additional acknowledgments (independently reviewed database identities, staging-only target, and main untouched) is allowed to connect. It requires independently inspected provider database identities and a *staging-only* credential passed at runtime, never saved to this source repository or CI. It allows only distinct canonical remote libSQL hostnames whose configured database-name prefixes match sovmem-staging and sovmem-main. The main URL is compared offline for inequality and host label but **never connected**; no main/production token is accepted. Hostnames/UUID and button acknowledgments are not provider-level alias separation or real human authentication: the report remains explicit about that evidence gap.

After verifying an entirely empty remote staging schema namespace through read-only metadata, the runner opens BEGIN IMMEDIATE, rechecks emptiness within that write transaction, executes only the seven statically reviewed commands from the Stage 9V and 9AA generators (six CREATE TABLEs and ONE fixed staging UUID marker INSERT), checks exact known tables/column order, a single ACTIVE STAGING_ONLY identity and ZERO memory, canary, batch, item or rollback rows, then commits. It closes and opens a separate fresh connection and confirms the same post-image. If ACK or fresh readback fails, report HOLD with unknown staging outcome; next exact operator-run reconciliation may be SELECT-only if the marker/schema and zero-row state exactly match, and never uses CREATE IF NOT EXISTS to mask partial failure. A nonempty/partial/unknown schema, table/view/trigger, existing test canary, secret mismatch, unknown URL or owner-approval flag mismatch causes HOLD, not an automatic repair.

**Operationally this is a staging schema installer, not an archive importer, remote rollback, source merger, replica durability proof or BIGBANG release switch.** Real libSQL remote DDL/transaction behavior and provider-controlled distinct database IDs must be independently validated before relying on it. Any live trial remains separately authorized by Naomi. Real production/main remain untouched.

## Exact PC handoff, only after owner approval and source review

ONE reviewed prep command invokes both existing private generators and verifies their matching source hashes, marker and exact output. On a Unix-like PC, the PRIVATE FILE-ONLY prep is:

    mkdir -p "$HOME/private"
    chmod 700 "$HOME/private"

    python api/galaxy_stage9ab_prepare_private_bundle.py \
      --destination "$HOME/private/sovmem-staging-init" \
      --confirm-local-only

It creates exactly four mode-0600 files in two private subfolders and NO database connection. It refuses existing output to avoid silently regenerating a second marker for an already-initialized database. Retain the original bundle until the independent migration and restore are completed. No raw UUID, credentials or paths are logged to GitHub or chat.

Then, while still offline, dry-run the entire reviewed source bundle using a SINGLE directory path:

    python api/galaxy_stage9ab_owner_local_bootstrap.py \
      --bundle-dir "$HOME/private/sovmem-staging-init"

This command is a dry-run even if private Turso environment variables happen to exist. At the LIVE gate, after Naomi independently reviews the staging/main Turso provider identities, appropriate staging-only access, SQL, source-commit and rollback risks, an explicitly authorized owner-local run sets the standard four GAIAOS_STAGE9V_* variables privately and repeats the command with --apply --confirm-provider-ids-reviewed --confirm-staging-only --confirm-main-untouched. The GAIAOS_STAGE9V_PRODUCTION_URL comparison value for this specific bootstrap must identify sovmem-main (not the original GaiaOS production). This runner connects ONLY to the staging URL, not either other database. Nothing is submitted to ChatGPT or to GitHub Actions. If on Windows PowerShell, use Windows-appropriate private folder permissions and line-continuation syntax rather than running the above bash commands as-is; operator-specific exact steps can be supplied later.

After any verified staging bootstrap and separate live single-canary proof, Stage 9AA's strict read-only canary/empty history pre-import checks may run. Real historical data import and remote rollback are separate unimplemented/unauthorized gates.

## Always retain these invariants

Six independently attributed E-LANES, VASKON reporting identity, //PW:PRESERVE//, signed proof receipts, original source/provenance, HEATDEATH fallback and locked BIGBANG stay intact. SOVMEM-main remains untouched until independent Phylactery migration review and Naomi's explicit production cutover authorization. The original shared GaiaOS repo, its GitHub Actions, original Render deployment and original production database must never receive the new account's staging/main credentials.
