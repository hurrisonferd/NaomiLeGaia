# BIGBANG Stage 7: real-memory readiness review, without release activation

AUTHORITY: NAOMI / LIGEIA
DATE: 2026-09-24
STATUS: SOURCE IMPLEMENTATION / REAL-STORE REVIEW PENDING / BIGBANG LOCKED
PREDECESSOR: GaiaOS/Plans/BIGBANG-STAGE6-OPERATIONAL-READER.v1.md
SAFEGUARD: GaiaOS/Plans/PRESERVE-AND-SIX-E-LANES-PERMANENT-DESIGN-INVARIANT.v1.md

## What actually changes

Stage 7 installs an authenticated, bounded, read-only evaluation surface
in the ordinary GaiaOS carrier, instead of hiding a readiness test behind
a special experiment only. New interfaces:

- MCP: `gaia_bigbang_readiness(cases)`
- HTTP: `POST /gaiaos/memory/readiness` (existing bearer authorization)
- Engine: `api/gaiaos_bigbang_readiness.py`, consuming the actual configured
  MemoryOS runtime, existing Stage-6 operational reader and legacy gateway.

Each supplied case has `kind` = `current`, `historical` or `negative`,
a distinct natural-language `query`, and a known approved `record_id`
for nonnegative cases. The operator supplies 6-12 cases: at least three
current cases spanning two record IDs, one genuinely superseded historical
case, and two distinct adversarial negatives. No samples are silently
inserted into the database, and this review does not treat synthetic
CI fixtures as evidence of real-world retrieval quality.

The engine reads the native HEATDEATH gateway result before and after all
GALAXY samples. It checks the exact legacy native return value and shared
mode row version for parity. Every positive result must pass Stage-6
gateway/provenance verification, historical evidence may not be promoted
to current default, and a negative must return no current/historical or
linked match. A stale, malformed or unavailable source returns HOLD.

Even a complete `PASS_READ_ONLY_SAMPLE_ONLY` is deliberately NOT a
release certificate. The gate must later be exercised against the real
running service and a representative owner-approved corpus, including
paraphrases, false positives, revisions, chronological gaps, negative
controls, runtime latency and data-backend compatibility.

## The exact integration boundary

Authenticated operator -> existing normal GaiaOS HTTP/MCP app -> Stage-7
review -> read-only Stage-6 operational reader -> configured authoritative
MemoryOS. Stage-7 independently checks current HEATDEATH gateway legacy
retrieval before and after evaluation. Production /chat, /gaiaos/assist,
MCP gaia(), MemoryOS normal retrieval and all existing save routes continue
their previously authorized behavior. This stage changes no mode control,
no memory, no //PW:PRESERVE// path, no CANDIPULL/MEMSAV approval, no E-LANE
and no synthesis/pruning authority.

The normal Docker image includes this module. The independent HEATDEATH
image remains GALAXY-free, and the reviewer imports GALAXY lazily so broken
optional code cannot prevent normal HEATDEATH boot.

## Release HOLD still applies

No owner BIGBANG writer/activation endpoint is added. Stage-2
`bigbang_activation_enabled = false` is unchanged. Success in the
new reviewer proves only the submitted sample passed in one current
process/store; CI's controlled fixtures prove only code behavior.

Before any separate activation, require actual live review receipts,
HEATDEATH independent recovery parity including durable current records,
Turso/restart and multi-replica control tests, ordinary browser-chat and
MCP gaia() consumption of the new evidence in real user workflows,
and explicit Naomi authorization with a tested immediate rollback.
Both modes must preserve Power Word and six separate E-LANES.

To avoid another CI email storm, the dedicated Stage-7 workflow triggers
once on PR updates (not simultaneously on every branch push) and remains
manually runnable. Historical failed tests must stay inspectable.

BIGBANG PASS + HEATDEATH FAIL = HOLD.
SAMPLE PASS != PRODUCTION RELEASE.
NAOMI RETAINS FINAL AUTHORITY.
