# GALAXY Stage 9V: separate staging Turso identity and one-canary readback

AUTHORITY: NAOMI / LIGEIA
STATUS: SOURCE IMPLEMENTATION AND MOCKED-CONNECTION CI ONLY. No live staging Turso was provisioned or accessed by this PR. NO production activation, production Turso writes, history import, gravity backfill, mode change, E-LANE mutation, automatic capture or HTTP route is authorized here.

Stacked after Stage 9U (#96), Stage 9T (#95), Stage 9S (#94) and Stage 9R (#93). Existing ownership, preservation and integration-first design gates remain authoritative. This milestone takes the next step beyond in-memory-only proofs WITHOUT passing a live production connection to an importer.

## Actual entry point and purpose

The explicitly invoked offline function api/galaxy_stage9v_staging_turso.py::prove_staging_turso_canary() accepts the owner's separately provisioned staging Turso endpoint/token, the existing production Turso endpoint URL for comparison, a manually pinned staging database UUID, a distinct signed one-canary approval manifest, and a distinct staging run ID and nonce hash.

In live use, it calls the repository's already-pinned libsql Python driver (libsql.connect(database=URL, auth_token=TOKEN)). It does not read tokens from the existing production runtime module, does not import that module, does not call the normal GaiaOS front door, and NEVER reads/writes memory_records, memory_gravity, memory_importance, lifecycle tables or any Prime Daemon E-LANE. It writes ONLY one row to the pre-provisioned galaxy_stage9v_canaries table. The write is followed by closing the connection, opening a NEW connection to the same staging URL, re-verifying database identity and reading back the exact canary. An exact replay is read-only; an existing run ID with a different nonce or identity is a HOLD.

This is a staging TARGET PROOF only. It does not yet test actual owner-approved memory import or full historical-gravity backfill over remote libSQL. The connector-injected CI suite uses a separate local SQLite file to model two connections; those tests deliberately report staging_turso_verified=false and cannot stand in for remote proof.

A second Stage 9V CI suite installs the repository's real Python libsql driver and uses it against a disposable LOCAL libSQL database. It executes the same identity SELECT, BEGIN IMMEDIATE, INSERT, commit, connection close/reopen, exact readback, replay, conflict HOLD, and revoked-marker HOLD via that driver. It also verifies the live connector's database/auth_token call signature without opening a remote connection. This eliminates a mocked-driver compatibility gap, but still deliberately injects the local connector, returns staging_turso_verified=false and never uses a real Turso credential. A local driver PASS must not be promoted to remote staging proof.

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

## One-time owner provisioning of a physically separate staging database

This is a manual OWNER TASK, not a performed action of the Stage 9V source build. Use Naomi's own Turso account or a deliberately authorized isolated staging environment, not the old production database, not a production clone and not credentials taken from the existing Render carrier. From an authenticated Turso CLI in a trusted terminal, choose an unused name and run:

    turso db create gaiaos-galaxy-stage9v --wait
    turso db show --url gaiaos-galaxy-stage9v
    turso db tokens create gaiaos-galaxy-stage9v --read-only --expiration 1d

The first command creates an empty independent target. The second gives the staging URL. The third creates a SHORT-LIVED, READ-ONLY token sufficient for the operator preflight. Keep its output PRIVATE. Never put either this token or the later write token in ChatGPT, a PR, screenshots or GitHub Actions logs. Confirm the new database's provider identity and alias separation independently in Turso administration; distinct URL strings alone are not enough. If the chosen name is unavailable, use another distinct staging name consistently.

Generate a fresh random UUID v4 privately and use the STAGING-ONLY SQL from the previous section, either in the Turso dashboard's SQL console or through the authenticated command turso db shell gaiaos-galaxy-stage9v. Install the exact single staging identity row and the separate stage9v_canaries table into the NEW database only. Do not use --from-db for this isolation proof; that would copy production data into staging and increase unnecessary exposure.

After that, privately set the four GAIAOS_STAGE9V_* variables below and execute only the read-only readiness CLI. This action does not require a write-capable database token. The one-canary write requires a second, separately approved staging-only token, signed manifest and exact owner authorization; do not repurpose the read-only token or assume preflight PASS authorizes a write.

Official CLI references: https://docs.turso.tech/cli/db/create ; https://docs.turso.tech/cli/db/tokens/create ; https://docs.turso.tech/cli/db/shell .

## Owner-local zero-credential provisioning bundle

Before provisioning or touching any remote database, Naomi may generate an exact two-file setup bundle LOCALLY, outside both the original and future Git repositories. This is OPTIONAL source-only preparation, not creation of a Turso database. Review the source before executing it with private environment access.

On Naomi's own trusted workstation, after reviewing the committed generator:

    mkdir -p "$HOME/private"
    chmod 700 "$HOME/private"
    python api/galaxy_stage9v_setup_bundle.py \
      --destination "$HOME/private/gaiaos-stage9v-setup" \
      --database-name gaiaos-galaxy-stage9v \
      --confirm-local-only

The destination must be a NEW directory that does not exist yet; no script overwrites an existing identity. The generator performs NO database connection, NO shell execution and NO source-repo mutation. It creates mode-0600 stage9v-new-staging-identity.sql and stage9v-local-setup-manifest.json in a private mode-0700 directory. The SQL creates ONLY the two approved staging identity/canary tables and inserts a freshly generated UUIDv4 owner marker. The manifest includes that UUID, staging-name LABEL and the SQL SHA-256 for Naomi's own inspection. No database URL, token or production content is needed. The CLI stdout includes only bounded statuses and the non-secret SQL digest; the UUID remains in the private local files.

After independently creating an EMPTY staging Turso database under Naomi's authority, inspect the provider-level database identity and source code, and manually apply ONLY the generated SQL to the NEW staging database via the trusted Turso SQL console or shell. Never point the SQL at the old production database. The generated UUID is a marker for future preflight, NOT standalone proof that the provider targets differ. Use a short-lived READ-ONLY token for the next stage. If Naomi has not yet created a wholly owned GitHub repository, she can run the reviewed Python preflight locally, keeping every token on her workstation. Do not install new staging credentials into hurrisonferd/NaomiLeGaia. The optional credential-bearing GitHub workflow remains disabled there even if its source is merged.

## Read-only operator preflight: no tokens in chats or Git

Before signing or running the single canary, use the explicit read-only operator CLI, api/galaxy_stage9v_operator_preflight.py. It requires four separately supplied PRIVATE environment variables:

- GAIAOS_STAGE9V_STAGING_URL: newly provisioned staging Turso endpoint, never the current MemoryOS production URL.
- GAIAOS_STAGE9V_STAGING_TOKEN: a staging-only credential kept in the operator's secure environment; never paste into ChatGPT, GitHub comments, commits, CI logs or screenshots.
- GAIAOS_STAGE9V_PRODUCTION_URL: the existing production endpoint URL used ONLY for identity comparison. The probe never accepts or uses the production token.
- GAIAOS_STAGE9V_STAGING_UUID: a fresh v4 UUID already installed in exactly one manually provisioned staging identity marker.

The exact command, after setting those variables privately, is:

    python api/galaxy_stage9v_operator_preflight.py --confirm-read-only

No environment is mutated by this command. The CLI refuses missing variables, identical staging/production URLs, invalid URL formats or UUIDs. It opens ONLY the staging endpoint, SELECTs the identity marker, verifies the read-only SELECT contract of the preprovisioned canary table and closes the connection. It NEVER inserts even a canary. Its JSON output contains only statuses, query counts and one-way endpoint/identity hashes, not URLs, tokens, source memory or stored content. A PASS proves read access to the supplied staging marker and canary table, NOT owner authentication, Turso control-plane identity or provider-level alias separation.

This preflight is source-only until the branch is reviewed, merged and deliberately installed in the owner's own authorized operator environment. Do NOT run arbitrary code from an unreviewed PR with live credentials. Keep the manual one-canary signed-approval step separate: read-only readiness is not write authorization.

## Manual-only remote-readiness receipt (new, unexecuted against real Turso)

The companion workflow .github/workflows/galaxy-stage9v-real-staging-readonly.yml is a SOURCE-ONLY PORTABLE TEMPLATE for Naomi's FUTURE OWNED repository. It has only a workflow_dispatch trigger. Its exact owner guard github.repository_owner == 'Ligeia621' plus explicit exclusion github.repository != 'hurrisonferd/NaomiLeGaia' make the credential-bearing job INERT in the current hurrisonferd-owned repository, even if a source-only copy is merged there. In the future owner-controlled repository it also requires refs/heads/main, both the original actor and triggering actor Ligeia621, run_attempt=1 and the STAGING_READ_ONLY choice; it requests contents: read. Failed attempts require a new owner-started manual dispatch. NO push/PR/schedule trigger, production database token or automatic secret transfer. Do not install independent staging secrets in the original repository. Review and port this code into Naomi's own repository only after independently verifying repo ownership; merely opening the PR or merging source in the original repository cannot authorize this workflow to run. A push/PR only runs MOCKED regression tests in the separate galaxy-stage9v-staging-turso-probe.yml workflow.

The manual job references a GitHub environment named gaiaos-stage9v-read-only, to be created IN NAOMI'S OWN REPOSITORY ONLY. Naomi must configure access/branch restrictions, any supported environment review protections, and exactly four staging-readiness secrets on that owned repository after independent source review. An environment name in YAML is NOT a protection rule. Required reviewer availability varies by repository privacy and GitHub plan, so do not claim review enforcement without checking actual settings. NEVER put an independent staging URL/token/UUID or any future SovereignOS credentials in the original hurrisonferd-owned repository: its administrator controls workflows and secrets. Never submit the production database token, and never disclose secret tokens in chat, PRs, tests, logs or screenshots. A separate staging read-only credential, a provider-confirmed independent DB and pre-provisioned marker/table are prerequisites. Until the owned repository is ready, use the reviewed local read-only operator CLI privately rather than a credentialed workflow in the old repository.

On a genuinely provisioned target, the workflow invokes ONLY the read-only staging operator preflight, checks its exit status, and passes the resulting PRIVATE JSON file to api/galaxy_stage9v_readiness_receipt.py. The emitter allowlists metadata, rejects unexpected fields (including accidentally copied tokens or archived statements), requires two successful staging SELECTs and distinct valid hashed endpoint fingerprints, and writes an artifact containing NO URLs, tokens, SQL results, archives or original report. The shell deletes the private report on exit, uploads ONLY the allowlisted receipt for 7 days, and logs only concise redacted status and checksum. Local synthetic CI tests assert the explicit actor/main/choice restrictions, workflow_dispatch-only policy, four secret names, no write call, no production credentials, redaction and negative report cases.

A PASS_REMOTE_STAGING_READ_ONLY artifact means the manually triggered runner observed the supplied staging marker and canary table through its libSQL connection. It is NOT a proof of independently verified provider database identity or aliases, a real owner authentication attestation, any SQL write or a successful production release. There is NO actual remote Turso run until a separate staging database is provisioned and the owner explicitly executes the workflow.

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
