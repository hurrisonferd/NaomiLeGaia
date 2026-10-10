# GALAXY Stage 9R: historical gravity + LEGACY / BIGBANG / HEATDEATH interoperability

STATUS: SOURCE-ONLY PROPOSAL. No mode activation, production gravity migration, live
Turso writes, external archive ingest, or canonical E-LANE changes are authorized
by this document. Owner: NAOMI. Architecture: one durable MemoryOS store.

## Core invariant: one memory universe, two readers

Turso / libSQL is the configured primary durable memory store. A memory's
record_id, text, authority, source, original dates (where evidenced), provenance,
verified relations, lifecycle history and owner-approved importance remain
identical irrespective of the selected retrieval mode. There is no "BIGBANG
database" separate from HEATDEATH, and no second set of E-LANES.

* HEATDEATH uses the original, independently importable LEGACY retrieval path.
  Owner-approved MemoryOS / MemconOS writes and MEMSAV must continue to work
  even when GALAXY modules fail or BIGBANG is disabled. Never import GALAXY
  into the emergency writer or emergency retrieval pathway.
* BIGBANG, once independently released and owner-authorized, retrieves
  relevance-qualified candidates from the SAME authoritative store. Only then
  may optional verified GALAXY graph / gravity / lifecycle context modify the
  qualified result. Any optional module failure returns the previously validated
  LEGACY result for that request, marks the fallback, and never silently flips
  the persistent mode control.
* Library and Phylactery are separate recovery / offline copies, never evidence
  of a Turso write or an automatic fallback to another authoritative database.
  A failed Turso write yields a HOLD and a retriable, owner-controlled packet.
  Do not silently write to potentially ephemeral local SQLite in production.
* These are mode-specific retrieval presentations over shared governed data.
  Neither memory relevance nor a calculated score confers truth or permission.

## Retroactive gravity: old is not zero

Before GALAXY existed, historical records had no gravity rows or owner importance
signal. Missing gravity is UNKNOWN / UNSCORED, NOT a numeric score of zero;
missing explicitly assigned importance is UNSET, NOT owner-assigned minimum
importance. An old record's source timestamp is not an importance signal.

Stage 9R adds a source-only, bounded, read-only inventory of existing durable
records. It distinguishes CURRENT, MISSING and STALE gravity model versions,
and uses the existing approved gravity preview to inspect MISSING / STALE rows.
No preview calculation stores or authorizes a score. The optional BIGBANG reader
now consumes the same resolver, avoiding legacy zero imputation and reporting
basis, score_version and backfill_required. HEATDEATH does not import it.

Important model limitation: the *current* approved preview computes a numeric
zero contribution when owner importance is absent. That is a computation default,
not evidence Naomi evaluated the record as unimportant. The Stage 9R reader
exposes UNSET_NOT_ZERO separately. Before broad BIGBANG adoption, calibrate
unrated-versus-rated cohorts and agree an owner-approved missingness policy.
Never silently alter the approved NERGAL profile or fabricate Seven Gates values.

## Backfill and cross-source ingest: further owner-approved stages

1. Inventory the authoritative Turso records by stable record_id and scope.
   Identify actual score version and distinguish missing, stale and corrupt
   data. Page at a fixed limit, maintain a high-water checkpoint and issue
   read-only evidence without leaking sensitive statements to audit logs.
2. For eligible existing records, calculate a versioned shadow preview against
   existing verified edges, actual governing state, provenance and any owner
   Seven Gates signal. Keep missing metadata explicit. Review sample strata:
   earliest records, unlinked records, historically superseded records and
   records with owner importance never assigned.
3. Add an authenticated, same-origin preservation import surface for owner-
   approved packets. Preserve source provenance, date confidence, member
   attribution and original document identity when importing from Library,
   GitHub or other external archives. Deduplicate by stable source identity /
   fingerprint. An archived statement is not a firsthand verified experience.
   Maintain six distinct member-attributed E-LANES, with no invented authorship.
4. Only under separate Naomi approval, execute idempotent, resumable Turso
   score backfill with a versioned receipt per changed record and independent
   readback. Checkpoint and compare-before-update; never rewrite the underlying
   memory record or permanently discard prior score/version information.
   Detect drift when relations, owner importance or lifecycle state change
   during a batch; retry safely instead of writing a stale score.
5. Recompute in bounded affected neighborhoods when verified relations,
   owner importance, governing state, lifecycle or score model version changes.
   Preserve explicit owner-assigned importance separately from computed
   influence. Prevent stored gravity from recursively feeding its own score.
6. Run the full proof ladder: source, isolated tests, staging Turso write/readback,
   restart durability, exact HEATDEATH read/write, independently simulated
   release-gated BIGBANG retrieval, optional module failure fallback,
   six-E-LANE isolation, source equality, semantic quality and rollback.
   Only after Naomi reviews receipts is a broad production backfill or
   BIGBANG activation eligible for separate authorization.

## Stage 9R shipped source surface (when PR merges)

* `api/galaxy_legacy_gravity.py`: optional `resolve_for_retrieval` and
  `audit_historical_gravity` (max 50 records/page). Neither writes nor imports
  the live memory runtime, and the audit is NOT a public HTTP route.
* `api/galaxy_frontdoor_context.py`: optional release-gated reader uses
  stored CURRENT-version gravity, otherwise read-only previews MISSING/STALE
  entries. Reports UNSET_NOT_ZERO for absent owner importance.
* Regression tests cover zero-write paged inventory, cross-scope isolation,
  no absent-as-zero imputation, stale model preview and no GALAXY invocation
  from HEATDEATH. Existing mode and LEGACY tests remain the release baseline.

No Stage 9R operation may rewrite `memory_records`, change active retrieval
mode, create E-LANE content, enable automatic preservation, or lift BIGBANG's
existing release lock.
