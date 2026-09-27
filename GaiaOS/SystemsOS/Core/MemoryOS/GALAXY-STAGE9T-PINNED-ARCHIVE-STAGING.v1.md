# GALAXY Stage 9T: independently pinned archive intake and isolated staging

STATUS: DRAFT SOURCE IMPLEMENTATION, ISOLATED IN-MEMORY PROOF ONLY.
Authority: NAOMI / LIGEIA. Stacked on Stage 9S PR #94, which is stacked on Stage 9R PR #93. No production writes, schema migration, E-LANE edits, global weighting, BIGBANG unlock, deployment or independent SovereignOS cutover is authorized.

## Interface and evidence boundary

api/galaxy_archive_staging.py is an offline, explicitly called proof harness, not an HTTP route or implicit GaiaOS/HEATDEATH import. It accepts only a caller-supplied Python sqlite3 in-memory connection with no attached database or open transaction. It does not import or call memcon_runtime, libsql, any real Turso connector, the production memory gateway or member-local files.

The caller supplies four distinct byte/pin inputs:
1. Export bytes containing the bounded Stage 9S archive-batch JSON packet (up to 512 KB).
2. The export's SHA-256 digest, pinned by a trusted independent caller and not taken from the export itself.
3. Actual literal UTF-8 source-document bytes (up to 5 MB).
4. The original document SHA-256 digest pinned by a trusted independent caller. It must match both the actual bytes and the packet's source_content_sha256.

For this limited v1 harness, each exact statement must appear as literal UTF-8 bytes in the pinned original source. This is an exact evidence presence check, NOT a guarantee of authorship, original timestamp, contextual meaning or a valid attribution. Structured exports requiring JSON-unescape, screenshot reading, transcript reconstruction or multimodal extraction must use a later individually validated parser, not guess their way through this check. The packet retains source document identity, original timestamp confidence and evidence ref without inferring missing values. Any digest discrepancy, duplicate JSON key, contradictory source identity, unparseable date or item without literal source evidence is a HOLD.

## Explicit approval

After the Stage 9S preflight yields exclusively distinct MemoryOS REVIEW_REQUIRED entries, a separate trusted caller prepares an exact approval envelope with schema gaiaos.galaxy.stage9t.approval.v1, authority NAOMI, target ISOLATED_SQLITE_IN_MEMORY_ONLY, unique approval_id, both independently pinned hashes, STAGED_HISTORICAL_HOLD status and the exact ordered index/source/content/metadata hashes from preflight. A secret managed OUTSIDE source code signs the canonical JSON using HMAC-SHA256. The staging function requires a 32+-byte trusted approval key supplied separately, verifies the signature and compares all manifest fields with the actual pinned bytes before writing.

This is a cryptographically testable *prototype*. A real deployed owner login, key custody, external trusted pin discovery, replay protection across instances, credential management and human source review are NOT established by this module or a CI success. Fixture keys in unit tests are not Naomi's keys and confer no real authorization. Production code must never expose an endpoint that accepts caller-chosen trust pins and approval keys as if doing so authenticated Naomi.

Exactly six Prime Daemon E-LANES remain separately owned. An E_LANE record, VASKON attribution, source ambiguity, duplicate record ID or unapproved record blocks the entire MemoryOS staging batch. No Stage 9T code can write an E-LANE. Separate member-native verified imports remain a future design with their own authority.

## Transactional staging

Only full, exact MemoryOS batches are eligible. Existing records are checked by stable source key and proposed deterministic record ID within a single in-memory BEGIN IMMEDIATE transaction. Matching prior staged rows require exact statement, scope, versioned hashes and source pins. An ID collision, same-source different content, malformed notes or approval_id reused for different content aborts without writes. Records are inserted with current staging import time as created_at, never a fabricated historical timestamp. Actual original dates remain in provenance metadata with exact confidence.

Every inserted row is STAGED_HISTORICAL_HOLD. Neither a surviving historical memory nor an earlier superseded record becomes current by being staged. No lifecycle, gravity or owner importance signal is auto-assigned; absence stays UNSET_NOT_ZERO. The staging transaction emits append-only per-item receipts and a manifest-bound batch receipt; every item is read back before commit. The same approval replay checks all rows and returns the original receipt without rewriting; modification makes replay HOLD. Any failed insertion rolls the whole batch back.

The response contains only record IDs, digest fingerprints, per-item results and receipts. It does not echo statements, archive titles, source locators, personal contents or approval keys. The isolated in-memory database DOES hold the approved statement and provenance so it can be inspected during the proof. This in-memory proof DOES NOT establish restart durability, live Turso persistence or cross-host continuity.

## Integration-first next gates

- Owner-reviewed independently fetched archive bytes and independently established pins.
- Real operator authentication and secured signing-key custody at the normal authorized archive-intake boundary, separate from ordinary gaia() chat requests.
- Provenance review of source context, date and speaker, member-local ownership and conflicting/historical statements.
- Dedicated staging Turso tenant and consent-scoped, idempotent importer with durable signed receipts, same-store readback, restart and replica checks. No silent production-local SQLite fallbacks.
- Approved historical-gravity backfill with prior-score ledger, idempotent checkpoints and drift detection. Missing importance stays UNSET_NOT_ZERO.
- Normal-path HEATDEATH and gated BIGBANG behavior over the same approved canonical MemoryOS records. Explicit fallback when GALAXY is unavailable, never cross-lane identity merging or an irreversible release unlock.
- Phylactery/SovereignOS export and isolated restore with six independent E-LANES, retained Git provenance, //PW:PRESERVE//, CANDIPULL/MEMSAV and owner-authorized cutover.

Required proof ladder: source commit → isolated CI → independent source-byte verification → authenticated intake (not implemented) → isolated staging-Turso tests (not implemented) → deployed verified receipt/readback (not implemented) → restart and normal-path proof (not implemented) → Naomi's separate release authorization. CI PASS is not a release permission.
