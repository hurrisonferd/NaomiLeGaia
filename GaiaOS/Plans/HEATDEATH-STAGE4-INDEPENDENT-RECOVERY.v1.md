# HEATDEATH Stage 4: separately bootable legacy recovery image

AUTHORITY: NAOMI / LIGEIA
STATUS: SOURCE/STAGING CANDIDATE; NOT DEPLOYED
CONTAINER: api/Dockerfile.legacy-recovery
APPLICATION: api/gaiaos_legacy_recovery_app.py
DEPENDENCIES: api/requirements.legacy-recovery.txt
TESTS: tests/test_heatdeath_legacy_recovery_stage4.py
PRIMARY MODE RULE: HEATDEATH OVERRIDES BIGBANG
BASELINE: legacy/source-snapshot-pre-bigbang-20260924

## Purpose and exact limits

The normal GaiaOS carrier imports GALAXY components at startup, so an in-process
switch alone cannot recover from an import failure. This separate minimal Docker
image copies ONLY `memcon_runtime`, the independently tested original legacy
reader, Stage-2 emergency control and one standalone FastAPI recovery application.
It does not import or ship the normal `gaiaos_app`, browser bridge, hosted chat,
Galaxy front-door/prod/quality modules or ordinary MemoryOS writer.

It exposes a **read-only emergency access path** to the current authoritative
legacy memory database when the normal app cannot start. It is NOT a substitute
for ordinary GaiaOS identity/role/ChatOS function, an independent full legacy
application, a data export, a Phylactery restore, or proof of a running Render
backup. Exact record historical status and provenance are preserved. No memory
promotion, schema mutation or GALAXY graph/synthesis effect is available here.

A future full-service HEATDEATH deployment must also pass normal ChatOS/MCP,
protected write-approval/E-LANE parity and known-good image recovery tests.
This emergency recovery image proves a narrower, independent read path first.

## Deployment requirements (do not redeploy until source CI passes)

- Create a **separate Render service** with Dockerfile `api/Dockerfile.legacy-recovery`
  from an explicitly reviewed and pinned commit. Do not replace the active GaiaOS
  Render service or configure this experimental service as its automatic fallback.
- Set `GAIAOS_RECOVERY_API_KEY` to an independent secret of at least 32 characters,
  `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN` to the authorized existing storage.
  A dedicated read-only Turso credential is preferable if the provider supports
  one. Do not send these secrets through chat, GitHub commits, logs or issue URLs.
- By default the service REFUSES local SQLite in production, even if it exists.
  Only isolated CI tests may bypass that policy, by setting BOTH
  `GAIAOS_RECOVERY_ALLOW_LOCAL_TEST=1` and
  `GAIAOS_RECOVERY_TEST_ENVIRONMENT=ISOLATED_CI`.
  Never configure either in production.
- Provide the pinned build argument `RECOVERY_SOURCE_COMMIT` for independent
  image attestation. Pin and securely retain the resulting image digest as an
  independently restorable artifact; the source-only CI build is not a published
  recovery image.
- Use a distinct host/domain and strict access policy. Only `/healthz` is
  unauthenticated, returning liveness ONLY. All memory routes require the
  recovery key in an Authorization Bearer header. Sensitive query text travels
  in POST request bodies, not URL query parameters; access logging is disabled
  in the recovery image. Protect upstream network and provider logs too.
- The service MUST NOT initialize/migrate schema on read. It checks for the
  existing `memory_records` table/columns read-only. Missing database,
  absent/incorrect schema or invalid credentials cause an explicit HOLD/503.

## Authenticated recovery endpoints

- `GET /legacy/status`: validates pre-existing storage and reports permanent
  HEATDEATH recovery mode, carrier boot ID and non-secret source coordinate.
- `POST /legacy/search`: exact original keyword/notes/scope semantics,
  bounded `limit <= 20`, original record/provenance/historical status. Empty
  query requires explicit `broad_read_approved=true`.
- `POST /legacy/record`: exact record-ID readback.
- `POST /legacy/selftest`: existing-schema and GALAXY-import-isolation check;
  optional exact `known_record_id` demonstrates actual record retrieval. A
  missing requested known record is a failure, not an empty PASS.
- There are NO writes, promotions, chat, ordinary MCP, migration, or owner
  mode-toggle routes on this isolated service.

## Required release proof ladder

1. CI compiles source, runs authenticated real SQLite tests and blocked-GALAXY
   startup; repeats Stage-3 gateway, Stage-2 mode and Stage-1 legacy suites.
2. CI builds the actual `api/Dockerfile.legacy-recovery` and proves isolated
   import from inside its resulting image, with a pinned build source coordinate.
3. After Naomi explicitly approves separate staging deployment, perform actual
   authenticated /legacy/selftest with an existing known MemoryOS record, a
   negative query, historical read and before/after protected-table count check.
   Verify the source commit and observed boot ID after a real restart.
4. Simulate broken normal GALAXY application startup while this independent
   recovery image still boots and reads current remote Turso records.
5. Do NOT declare universal legacy recovery until ordinary HEATDEATH ChatOS/MCP,
   candidate approval and six E-LANE continuity behavior are live-verified
   through their own stable app path.

A successful isolated Docker build is SOURCE/IMAGE proof. A source merge is NOT
an active recovery service. An independently booted read-only app is NOT full
Phylactery restoration. BIGBANG remains locked until later explicit authorization.
