# GALAXY Stage 9Z: separately signed exact LOCAL rollback

AUTHORITY: NAOMI / LIGEIA. STATUS: STACKED DRAFT SOURCE ONLY. Depends on Stage 9Y #100 and all predecessor draft PRs back through Stage 9R #93. No live Turso staging, production connection, source merge, deployment, credentials, E-LANE mutation or BIGBANG activation is authorized here.

## What this tests

Stage 9Y stages strictly approved *new* MemoryOS history into a locally pre-provisioned file-backed SQLite test database with canonical memory_records columns, a Stage 9V-shaped staging UUID/canary marker, held status, source provenance fingerprints, a signed original import manifest, per-record receipt rows and a batch HMAC receipt. Stage 9Z adds an independent, separately signed LOCAL rollback to verify those exact new rows can be removed without losing the original import receipts or introducing unreviewed state changes.

The Stage 9Z code is in api/galaxy_stage9z_local_rollback.py. It contains **no remote libSQL driver, remote connector, production MemconOS dependency, HTTP endpoint, secret-loading operator CLI or implicit schema creation**. The only accepted database is the native sqlite3 file under a separately supplied fixture directory outside the original repository, with no attached databases or open transaction. HMAC keys in tests are NOT actual Naomi authentication and no live deployment is tested.

### Required evidence and strict source scope

The offline test caller must provide the original EXACT Stage 9Y signed manifest, original HMAC signature and separate original test key. Stage 9Z verifies the original manifest against the stored original batch/source/export fingerprints and validates the original batch receipt and its HMAC before considering deletion. It then requires a DIFFERENT independent 32+-byte test key and signed Stage 9Z rollback manifest. That manifest binds a unique rollback ID, original approval and batch receipt hashes, canonical staging and production endpoint hashes (no URLs are connected), staging UUID, original exact canary run ID and complete-row canary hash, and every original newly inserted record ID, source key and full staged-row fingerprint. Three separate local confirmation flags are required.

Before any deletion, the fixture must have **exactly** the six expected tables: unchanged canonical memory_records, Stage 9V's staging identity and canary tables, Stage 9Y's original batch and item ledgers and a separately PRE-PROVISIONED Stage 9Z rollback ledger. Unknown graph, lifecycle, gravity, other dependent tables, views or triggers cause a HOLD rather than risk orphaning downstream state. This deliberately restrictive fixture schema is not sufficient to roll back an actual full MemoryOS installation. Stage 9Z also rechecks staging marker and exact same-database canary within its write transaction. Neither UUID nor URL hashes establish genuine provider-control-plane database separation.

Once all original records and original append-only receipts match exactly, a single BEGIN IMMEDIATE transaction removes ONLY the newly imported records in the signed batch and marks its original batch ledger ROLLED_BACK_LOCAL_FIXTURE. Original item receipts and the full original HMAC-signed batch receipt are retained. A new immutable rollback receipt and independent HMAC bind exact deleted row digests, original receipt hash and retained-ledger status. Both original and rollback receipts are checked before commit and again from a FRESH file connection after commit. A lost commit acknowledgement or failed fresh readback is a HOLD with unknown outcome, requiring the **same** signed rollback attempt for reconciliation rather than a new ID. An exact already-rolled-back replay reads and verifies but performs **zero** additional writes.

Stage 9Y's local historical importer is also changed to reject any new approval that would silently re-import a source key already recorded in a rolled-back Stage 9Z batch. A later intentional reactivation requires its own separately designed, signed and reviewed protocol, not just a new approval ID.

### Fixture-only schema for this added ledger

Pre-provision only in the disposable local test fixture, never in original production Turso:

\`\`\`sql
CREATE TABLE galaxy_stage9z_rollbacks (
  rollback_id TEXT PRIMARY KEY,
  import_approval_id TEXT NOT NULL UNIQUE,
  rollback_manifest_sha256 TEXT NOT NULL,
  import_receipt_sha256 TEXT NOT NULL,
  receipt_json TEXT NOT NULL,
  receipt_hmac_sha256 TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);
\`\`\`

All original Stage 9V and Stage 9Y fixture tables and their original rows remain intact except the exact held Stage 9Y row deletions and original batch status update. This stage does not attempt to reset owner importance, lifecycle, graph, independently authored E-LANES, source content or ordinary chat routing.

## Safety and proof boundaries

Local CI covers a successful signed rollback, strict original and separate rollback signatures, schema/dependency and marker/canary holds, tampered original and rollback ledgers, atomic rollback when a statement fails after deleting rows, fresh-connection failure and exact zero-write reconciliation, source-resurrection refusal, original unrelated row preservation, and no unauthorized imported statement/provenance text in stdout. Prior Stage 9S/9T/9Y regression suites remain protected.

**A local signed rollback is not a remotely authorized rollback.** The next actual release gate still requires Naomi's independent owner-controlled staging Turso provisioning and control-plane identity/alias attestation, separate narrowly scoped credentials, real Stage 9V/9X remote canary evidence, a separately reviewed actual remote historical importer and rollback model, durable restart/replica proof, representative historical calibration and full six independent E-LANE, //PW:PRESERVE//, CANDIPULL/MEMSAV and HEATDEATH/BIGBANG ordinary-browser invariants. All draft PRs remain unmerged and release-locked pending explicit Naomi approval. Phylactery to SOVREP-Core stays separate.
