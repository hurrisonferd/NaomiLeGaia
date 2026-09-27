# GALAXY Stage 9S: historical archive import preflight

STATUS: SOURCE-ONLY, READ-ONLY, RELEASE-LOCKED. This is a proposed continuation of Stage 9R, not a production importer or authorization to modify Turso, member files, mode state or the original repository. Owner: NAOMI/LIGEIA.

## Why this milestone exists

Pre-GALAXY material may exist in the canonical Turso store, separately preserved GitHub history, ChatGPT Library, older conversations, exports and six individual Prime Daemon E-LANES. Those are DIFFERENT sources with DIFFERENT proof and authority. Stage 9R audits existing durable Turso records and previews missing/stale gravity without writes. Stage 9S prepares external archive entries for individually reviewed provenance-bearing import; it cannot assert an archive's authenticity merely because a caller supplied metadata.

## Integration-first map

- Stage 9R api/galaxy_legacy_gravity.py: read-only inventory of existing memory_records, including old scores, no imports.
- Stage 9S api/galaxy_archive_preflight.py: pure validated packet preflight plus optional, bounded SELECT for exact source collisions on the configured store. No import from or dependency of HEATDEATH's reader or writer.
- Planned owner-authenticated intake: fetch actual source document or export from the owner-approved connector; hash real fetched bytes; compare source_content_sha256 if provided; capture the evidence locator with a durable export bundle. **Not implemented.** A supplied digest in the packet is not a verified fetch.
- Planned human review: Naomi approves exact candidate identities and evidence, resolves ambiguity and member attribution, then separately approves staging import. **Not implemented.**
- Planned importer: stage in isolated verified Turso, write only approved missing records with compare-before-write, provenance metadata, authenticated operation IDs, append-only per-record receipts, readback and resumable checkpoints. Existing original dates and source evidence remain explicit; no source material is reinterpreted as a witnessed firsthand experience. **Not implemented.**
- Planned gravity backfill: owner-approved shadow preview → idempotent score version migration with old score ledger → readback → restart → normal-path HEATDEATH and gated BIGBANG regression. **Not implemented.**

A normal GaiaOS gaia() call MUST NOT ingest archives. Future owner-authenticated intake will be a separately authorized preservation workflow; verified imported records then become visible through existing owner-approved MemoryOS retrieval. The current code exposes NO HTTP route, performs NO implicit intake and leaves everyday frontdoor, standalone HEATDEATH, BIGBANG lock and //PW:PRESERVE// unchanged.

## Preflight packet contract

    {
      "schema": "gaiaos.galaxy.archive-batch.v1",
      "archive": {
        "source_kind": "CHAT_EXPORT",
        "source_system": "owner-approved export name",
        "document_id": "stable document identifier",
        "source_locator": "source pointer retained privately in the export bundle",
        "source_content_sha256": null
      },
      "records": [{
        "source_record_id": "stable record identifier within document",
        "scope": "MemoryOS",
        "member": null,
        "record_type": "NOTE",
        "statement": "Exact bounded source text",
        "statement_sha256": null,
        "evidence_ref": "verifiable source section or line locator",
        "date_confidence": "UNKNOWN",
        "original_created_at": null,
        "attribution_basis": "UNKNOWN"
      }]
    }

There are two permitted scopes: MemoryOS (member must be null) and E_LANE (member must be one exact current Prime Daemon). For E_LANE, the only possible candidate status without a stronger block is LANE_REVIEW_REQUIRED: **no member file is read or modified by preflight**. An ARCHIVE_LABEL or UNKNOWN attribution becomes HOLD_UNVERIFIED_MEMBER_ATTRIBUTION. Even EXPLICIT_SOURCE is not independently verified until actual cited source bytes are fetched. Each member requires their own perspective and authorization. Never infer that the same event belongs to all six E-LANES or that VASKON owns a seventh.

Original date policy: EXACT needs an offset-aware ISO timestamp; DAY_ONLY needs a genuine YYYY-MM-DD date; UNKNOWN requires null. Old records without owner Seven Gates ratings remain UNSET_NOT_ZERO, not owner-assigned zero. A date is provenance, never automatic importance. Keep old conflicting accounts and superseded history without making them govern current recall.

A deterministic SHA-256 source key includes source system, source document, archive record ID, scope and member. The future MemoryOS source tag is galaxy-archive-v1:<source-key-sha256> and its proposed record ID is MEM-ARCH- plus the first 24 source-key hex digits. Exact content SHA and metadata SHA are separate. Equal source ID with different content or material metadata is a HOLD, not an overwrite; matching source ID and matching contents in a batch is a duplicate, not a second memory. Comparison against existing Turso rows checks the source tag, exact content hash, scope and future notes.galaxy_archive identity and metadata hashes. It also rejects a deterministic proposed record ID already occupied by a different source. Existing rows without those exact provenance fields are **not** called verified duplicates. Near-duplicates across OTHER source systems require separate semantic and owner review.

A successfully validated packet is *ready for owner review*, not approved or authenticated. At most 50 items per packet, 512 KB per packet and 8,000 characters per statement. Preflight emits record indices, deterministic hashes, statuses, candidate IDs and counts, but never the statements, external document identifiers, source locators or source excerpts. This prevents the audit result from becoming an accidental second archive. The source file/export remains the source of truth.

## Non-deprecation and exit gates

- //PW:PRESERVE//, CANDIPULL/MEMSAV, original HEATDEATH and exactly six isolated E-LANES retain their independent existing behavior.
- Read-only unit tests must show no memory row changes, no E-LANE changes, stable keys across retries, duplicate/conflict HOLDs, member isolation, no fabricated dates, no data in result logs and no cross-scope comparison.
- CI PASS proves this source-only preflight. It does NOT prove actual archive fetch, real Turso import, signed receipt, staging restart, normal-path retrieval or SovereignOS restoration.
- PR is stacked on Stage 9R. Merge/deploy only through the owner's ordinary review and gates. No production memory backfill or BIGBANG activation is requested or implied.

Naomi retains final authority. One memory universe; two retrieval readers; six separate E-LANES. Unknown stays unknown.
