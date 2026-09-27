# GALAXY Stage 9V: separate staging Turso identity and one-canary readback

AUTHORITY: NAOMI / LIGEIA
STATUS: SOURCE IMPLEMENTATION AND MOCKED-CONNECTION CI ONLY. No live staging Turso was provisioned or accessed by this PR. NO production activation, production Turso writes, history import, gravity backfill, mode change, E-LANE mutation, automatic capture or HTTP route is authorized here.

Stacked after Stage 9U (#96), Stage 9T (#95), Stage 9S (#94) and Stage 9R (#93). Existing ownership, preservation and integration-first design gates remain authoritative. This milestone takes the next step beyond in-memory-only proofs WITHOUT passing a live production connection to an importer.

## Actual entry point and purpose

The explicitly invoked offline function api/galaxy_stage9v_staging_turso.py::prove_staging_turso_canary() accepts the owner's separately provisioned staging Turso endpoint/token, the existing production Turso endpoint URL for comparison, a manually pinned staging database UUID, a distinct signed one-canary approval manifest, and a distinct staging run ID and nonce hash.

In live use, it calls the repository's already-pinned libsql Python driver (libsql.connect(database=URL, auth_token=TOKEN)). It does not read tokens from the existing production runtime module, does not import that module, does not call the normal GaiaOS front door, and NEVER reads/writes memory_records, memory_gravity, memory_importance, lifecycle tables or any Prime Daemon E-LANE. It writes ONLY one row to the pre-provisioned galaxy_stage9v_canaries table. The write is followed by closing the connection, opening a NEW connection to the same staging URL, re-verifying database identity and reading back the exact canary. An exact replay is read-only; an existing run ID with a different nonce or identity is a HOLD.

This is a staging TARGET PROOF only. It does not yet test actual owner-approved memory import or full historical-gravity backfill over remote libSQL. The connector-injected CI suite uses a separate local SQLite file to model two connections; those tests deliberately report staging_turso_verified=false and cannot stand in for remote proof.

## Fail-closed staging trust contract

Before any database connection, require:
- Two distinct, valid remote Turso host URLs with no embedded passwords, tokens, query parameters, nonstandard ports or local-file schemes. libsql:// and https:// for the same canonical host are treated as the same URL. URL inequality is NOT sufficient evidence of different underlying databases if DNS aliases exist.
- A separate staging credential (at least 16 characters) and a pinned v4 staging database UUID.
- A strict, single-action manifest with schema gaiaos.galaxy.stage9v.one-canary-approval.v1, exact staging and production canonical-URL SHA-256 fingerprints, expected staging UUID, action WRITE_ONE_STAGING_CANARY, target SEPARATE_STAGING_TURSO_CANARY_ONLY, a unique run ID and SHA-256 nonce.
- An independently held owner signing key of at least 32 bytes and an HMAC-SHA256 signature over canonical JSON. The example key used by CI does NOT prove a real person authorized anything. Never expose an endpoint that accepts caller-chosen key AND approval payload and calls that real authorization.

Before any INSERT, query the pre-provisioned galaxy_stage9v_staging_identity table. It must contain exactly one row, with the expected UUID and the exact fields schema=gaiaos.galaxy.stage9v.staging-identity.v1, environment=STAGING_ONLY, authority=NAOMI and status=ACTIVE. A missing, duplicated, revoked or mismatched marker is a HOLD. Provision the identity manually AFTER independent verification that the staging database is not the old primary or an alias to it.

The probe refuses to create or alter any schema; the owner/admin must pre-provision the following on a newly created, separately authorized staging database only. The UUID below is illustrative; generate a fresh random UUID v4 for your real deployment.

    CREATE TABLE galaxy_stage9v_staging_identity (
      schema TEXT NOT NULL,
      environment TEXT NOT NULL,
      database_id TEXT PRIMARY KEY,
      authority TEXT NOT NULL,
      status TEXT NOT NULL
    );
    INSERT INTO galaxy_stage9v_staging_identity
      (schema, environment, database_id, authority, status)
      VALUES (
        'gaiaos.galaxy.stage9v.staging-identity.v1',
        'STAGING_ONLY', '<fresh-owner-pinned-staging-UUID-v4>',
        'NAOMI', 'ACTIVE'
      );
    CREATE TABLE galaxy_stage9v_canaries (
      run_id TEXT PRIMARY KEY,
      nonce_sha256 TEXT NOT NULL,
      database_id TEXT NOT NULL,
      created_at TEXT NOT NULL
    );

Do NOT install those tables or marker in production as a shortcut. Use staging-only scoped tokens, preferably limited to the necessary marker SELECT and canary SELECT/INSERT. Verify actual Turso database identity and alias separation through owner/provider administration BEFORE authorizing a write. This source code checks its configured URL and marker, not Turso's platform control-plane identity.

## Failure, proof and restart bounds

If the initial write reports a failure after an INSERT attempt, or reopening fails after COMMIT, the result is a HOLD with STAGING_CANARY_WRITE_OUTCOME_UNVERIFIED. The owner must retry the SAME run ID and nonce to establish whether the original commit is present. Do not assume a failed response implies no write. No token, archive text or URL is echoed into the result.

A CI PASS proves that separate-URL guards, marker checks, simulated signature binding, concurrency-aware duplicate detection, rollback attempts and two-connection exact readback work with an injected SQLite connection. It does NOT prove the true production URL is independently attested, real Naomi authentication, separate staged database provisioning, a real libSQL connection, a service restart, replica durability, a memory import, six member-local restoration or ordinary BIGBANG/HEATDEATH behavior.

## Integration-first exit gates

1. Review and merge prerequisite 9R→9U source only with Naomi's explicit approval, keeping BIGBANG locked.
2. Provision and independently verify a new staging Turso database and separately scoped access token. Never use production Turso credentials for this test.
3. Owner-sign the precise staging-only manifest using a key managed outside GitHub source, CI and caller-controlled routes.
4. Manually invoke the probe from an authorized, private operator environment and preserve redacted evidence, exact commit SHA and the real separate-connection readback receipt.
5. Only AFTER a separate authorization build a bounded, idempotent versioned staging-Turso memory/archive importer, source/importance drift-aware gravity backfill with full previous-score ledger, and rollback. Test actual old/current/historical cohorts, both HEATDEATH and release-gated BIGBANG in the ordinary GaiaOS user path, //PW:PRESERVE//, CANDIPULL/MEMSAV and all six independent E-LANES. Owner verifies independent restart durability before any production switch or SovereignOS cutover.

STAGING PROOF != PRODUCTION WRITE PERMISSION.
A SOURCE MERGE != LIVE DEPLOYMENT.
A REMOTE CANARY != VERIFIED HISTORICAL IMPORT.
