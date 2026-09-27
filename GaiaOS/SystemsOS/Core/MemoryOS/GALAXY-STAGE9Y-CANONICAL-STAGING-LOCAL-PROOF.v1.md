# GALAXY Stage 9Y: canonical staging historical import, LOCAL fixture proof

AUTHORITY: NAOMI / LIGEIA. STATUS: UNMERGED SOURCE PROPOSAL. BASE: Stage 9X #99, then 9W #98 back through 9R #93. This milestone performs **no live Turso query or write**, no production mutation, no migration, no deployed mode activation and no E-LANE change. It does **not** authorize a later live import or substitute for Naomi's independently provisioned staging Turso.

## Contract proven by this source

Stage 9T validates independently pinned exact export JSON bytes and original UTF-8 source bytes, rejects duplicate JSON keys, requires every statement to be literally present in the pinned source, and prepares record-level source/content/metadata fingerprints. Stage 9Y **reuses those exact validators**, refuses any E_LANE entry and caps the first batch at 25 MemoryOS records. No speaker, original timestamp, original lifecycle, E-LANE ownership, explicit owner importance or governing state is invented. The imported records remain `STAGED_HISTORICAL_HOLD`, never ACTIVE.

Stage 9Y adds the missing proposed canonical-schema import sequence against a **native sqlite3 file-backed fixture** in a caller-supplied separate temporary directory. It accepts neither an in-memory-only DB nor an arbitrary or attached production-path DB. It never imports libSQL or the production MemconOS module. To make the remote boundary mechanical, the module has **no live remote connector**. Passing an actual Turso client fails its type gate.

The caller pre-provisions a fresh isolated test database with the exact ordinary MemconOS `memory_records` columns, Stage 9V's one-row `galaxy_stage9v_staging_identity` and `galaxy_stage9v_canaries` tables, and Stage 9Y's append-only fixture receipt tables. Stage 9Y performs **no schema creation**. It requires a Stage 9V canary row whose exact full-row SHA-256 matches the separately supplied, signed and owner-reviewed manifest. This binds the proposed batch to the same marked staging fixture and prior local canary. A remote canary receipt or provider control-plane identity has NOT been proven by a local SQLite row.

The separate Stage 9Y HMAC-SHA256 manifest binds the complete ordered item-hash list, pinned source/export digests, unique approval ID, staged-only target, expected staging UUID, canonical staging and production URL hashes, exact previously observed canary run ID and hash, and the local-only action. Three explicit **fixture** review flags guard execution. The fixture key is NOT a real authentication system. The signed batch is not permission for any real remote write.

After checking schema, identity and canary, Stage 9Y begins one SQLite IMMEDIATE transaction. It re-verifies identity and canary inside the transaction, checks ALL source and proposed record-ID collisions before the first insert, inserts only held MemoryOS records and per-record receipts, stores a complete metadata-only batch receipt and a test-key HMAC, verifies every row and receipt inside the transaction, commits, then opens a **fresh file connection** and checks each saved record/ledger row, same-source uniqueness, identity and canary again. All private statement/locator/provenance text stays **inside the isolated test database**. Returned status and receipts expose only hashes, record IDs, dates and fixed flags.

Exact replay of an unchanged, signed batch performs zero writes and verifies every row on a fresh connection. Replay drift, signature or pin mismatch, source collision, revoked marker, missing canonical table, changed canary, unapproved scope or stale approval ID fail closed. A failed insert rolls back. A failed COMMIT acknowledgment or fresh readback is treated as unknown until exact signed replay reconciles it. This is **local transaction/reopen proof, not independently restarted remote Turso durability**.

## Local-only pre-provisioned fixture schema

The test suite creates the file itself; never apply this SQL to the old production Turso. The only *new* Stage 9Y tables required in a future independent staging database (subject to separate schema review) are:

```sql
CREATE TABLE galaxy_stage9y_batches (
    approval_id TEXT PRIMARY KEY,
    manifest_sha256 TEXT NOT NULL,
    export_sha256 TEXT NOT NULL,
    source_sha256 TEXT NOT NULL,
    canary_sha256 TEXT NOT NULL,
    receipt_json TEXT NOT NULL,
    receipt_hmac_sha256 TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE galaxy_stage9y_items (
    receipt_id TEXT PRIMARY KEY,
    approval_id TEXT NOT NULL,
    record_id TEXT NOT NULL,
    source_key_sha256 TEXT NOT NULL,
    statement_sha256 TEXT NOT NULL,
    metadata_sha256 TEXT NOT NULL,
    row_sha256 TEXT NOT NULL,
    result TEXT NOT NULL,
    UNIQUE(approval_id, source_key_sha256)
);
```

Stage 9Y never constructs these tables itself. The fixture must also have Stage 9V's separate manually installed identity+canary tables and the unchanged canonical `memory_records` columns. Stage 9Y **does not use** the Stage 9T in-memory receipt tables as live tables.

## Observed proof boundary and next gate

The GitHub Actions test suite has no secrets, manual live dispatch, external staging token, deployed browser route or libSQL remote import. Fixture timestamps are import times, not source dates. A test receipt's HMAC demonstrates a local key-bound payload, not a verified person or trusted external archive provenance.

The next real gate remains: **Naomi independently provisions and attests owner-controlled staging Turso, separate scoped credentials and aliases**; privately executes the reviewed Stage 9V/9X signed staging canary after source merge/review and separately preserves redacted proof; then separately authorizes review and adaptation of this LOCAL transaction algorithm to an actual remote libSQL adapter with live owner authentication, durable receipts, independent replica/restart and explicit rollback. A provider-level production database identity check must not be inferred from URL inequality, marker UUID or local HMAC.

Before normal GaiaOS memory activation, verify real old/current/superseded and rated/unrated cohorts, graph/source/lifecycle drift, receipt-backed rollback, zero accidental HEATDEATH changes, all six independently owned E-LANES, //PW:PRESERVE//, CANDIPULL/MEMSAV and ordinary browser chat, deployment SHA and fresh-chat/restart continuity. BIGBANG remains LOCKED and SOVREP-Core cutover requires separate Naomi authorization. This PR is a source prototype, not a production migration.
