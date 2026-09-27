# GALAXY Stage 9AA: independently pinned READ-ONLY staging pre-import proof

AUTHORITY: NAOMI / LIGEIA. STATUS: STACKED DRAFT SOURCE ONLY. Depends on Stage 9Z #101, Stage 9Y #100, Stage 9X #99 and previous draft dependencies back through 9R #93. No live Turso use, deployment, source merge, E-LANE mutation, gravity change, database import or BIGBANG activation has been performed by this PR.

## Purpose

Stage 9X supplies signed staging-only single-canary mechanics, and 9Y/9Z provide signed history import and rollback on a native SQLite fixture. The next independent gate is inspecting a truly separate, owner-controlled staging Turso using ONLY SELECT statements. Stage 9AA checks exact staging marker and prior independently pinned canary, six known table layouts and empty pre-import ledgers. Its direct remote path must run ONLY on Naomi's trusted local workstation with a separate read-only staging token after the database is independently provisioned and reviewed. It is never automatically invoked by ordinary chat, tests or deployment.

## Read-only contract

The preflight first runs Stage 9V's existing read-only marker and canary-table checks, closes that connection, then opens a new connection to the independently supplied staging URL. It checks marker identity again and rejects unknown tables, E-LANE tables, views and triggers. It uses SELECT * LIMIT 0 on six fixed, known tables to inspect column names WITHOUT retrieving statements. It verifies the exact SHA-256 of the prior independently pinned canary row and requires exactly one canary and no rows in the four import/rollback tables. It does not create schema, alter data or import private archives. No production token is accepted and no connection to the production URL is opened.

The six expected isolated tables are: Stage 9V identity and canary, canonical memory_records with twelve existing columns, Stage 9Y batch and item ledgers, Stage 9Z rollback ledger. This restricted first-import layout is not full production MemoryOS graph/lifecycle parity. Column matching is not complete DDL or constraint proof, and token read-only permission and provider-level database separation must be independently verified outside this source. A passing local injected-connector or actual LOCAL libSQL driver test is explicitly marked LOCAL, never real Turso evidence.

## Private, NO-EFFECT optional owner-local schema bundle

The companion api/galaxy_stage9aa_local_schema_bundle.py generates two owner-only files outside the source repository: four-table SQL for Stage 9AA's canonical+receipt tables and a separate SQL/checksum manifest. It never connects to Turso, reads credentials or updates GitHub. Use alongside the existing Stage 9V owner-local setup generator, which makes the separate UUID/identity/canary SQL. Both private generators require a NEW destination and explicit local-file-only confirmation. No generated SQL has been applied to any real Turso by this PR.

After separate source review on Naomi's trusted local workstation, the following are PRIVATE FILE CREATION ONLY:

    mkdir -p "$HOME/private"
    chmod 700 "$HOME/private"

    python api/galaxy_stage9v_setup_bundle.py \
      --destination "$HOME/private/stage9v-setup" \
      --database-name gaiaos-galaxy-stage9v \
      --confirm-local-only

    python api/galaxy_stage9aa_local_schema_bundle.py \
      --destination "$HOME/private/stage9aa-schema" \
      --staging-name-label gaiaos-galaxy-stage9v \
      --confirm-local-file-only

The owner then INDEPENDENTLY provisions a NEW EMPTY staging Turso in her own account, reviews provider database IDs and aliases, and only after separate authorization manually applies both reviewed SQL files to that NEW database. Executing SQL on real staging is itself a LIVE write and is NOT authorized by this PR or an ordinary build-hammer shorthand. Never install independent staging/SovereignOS credentials in hurrisonferd/NaomiLeGaia, its GitHub Actions secrets, chat or the old Render carrier. Never apply either SQL file to production.

## Independent evidence handoff before the actual read-only command

First run Stage 9V's owner-private READ-ONLY check on the separately provisioned staging database. Then separately authorize ONE Stage 9X signed canary with a dedicated narrowly scoped staging-only write credential, and preserve its exact run ID, manifest, hashes and successful distinct-connection remote readback independently from the database you will inspect. This source proposal does not execute that canary.

Create a PRIVATE, owner-only mode-0600 JSON file from that previously preserved evidence. The exact field names are schema, run_id, canary_sha256, staging_uuid_sha256, staging_url_sha256 and production_url_sha256. The schema value is gaiaos.galaxy.stage9aa.independent-canary-pin.v1. Canonical URL SHA hashes are taken from the prior reviewed Stage 9X approval rather than regenerated from an untrusted current target; the UUID hash pins Stage 9V's independently retained marker. No token, raw URL, archived statement or signing key belongs in this file or chat.

With the four existing private GAIAOS_STAGE9V_* variables set on Naomi's trusted local environment, use a short-lived STAGING-ONLY READ-ONLY token in GAIAOS_STAGE9V_STAGING_TOKEN (not the canary write token). The production URL is comparison-only; NO production token is needed. The explicit command, only after independent provisioning and review, is:

    python api/galaxy_stage9aa_preimport_readonly.py \
      --pinned-canary-json "$HOME/private/pinned-stage9x-canary.json" \
      --confirm-read-only \
      --confirm-independent-canary-pin

An actual direct live SELECT-only PASS may report staging read access but still deliberately reports false for independent provider database/alias attestation, independent verification of token read-only permissions, real owner authentication, any archival data import, any rollback or production release. The code emits only redacted statuses, fixed count evidence and SHA-256 of static columns. An unknown dependency, mismatched canary, unexpected row, failed SELECT or bad connection-close produces HOLD.

## Remaining release holds

Naomi still needs independent provider-level database identity/alias and token-scope evidence, the owner-run remote read-only preflight and its redacted receipt, a separately reviewed and approved LIVE authenticated historical importer and rollback, durable independent restart/replica proof, real old/current/superseded and rated/unrated calibration, all six independent E-LANES and //PW:PRESERVE// and CANDIPULL/MEMSAV safeguards, HEATDEATH failover and ordinary browser-chat verification and actual deployed source-commit proof. All stacked draft PRs stay unmerged until separate Naomi source approval. BIGBANG remains locked; Phylactery to SOVREP-Core requires separate isolated restoration and explicit final authority.

SOURCE CI != LIVE PROOF. REMOTE READINESS != MIGRATION PERMISSION. STAGING IMPORT != PRODUCTION CUTOVER.
