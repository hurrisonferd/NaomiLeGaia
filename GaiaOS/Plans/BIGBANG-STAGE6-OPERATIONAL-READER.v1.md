# BIGBANG Stage 6: port the operational GALAXY reader behind the existing gateway

AUTHORITY: NAOMI / LIGEIA
DATE: 2026-09-24
STATUS: READ-ONLY SOURCE PORT AND OFFLINE VERIFICATION; RELEASE ACTIVATION LOCKED
BASE: main@f6034e0eed049795d3642d8063f149ba1eb481c6
SOURCE: api/galaxy_frontdoor_context.py
SOURCE OF ORIGINAL PORT: galaxy/naomi-authorized-operational-adoption-20260924
TEST: tests/test_bigbang_operational_reader_stage6.py
DEPENDENCIES: existing Stage 1-5D HEATDEATH tests and shared-memory mode service

## What changes

The original front-door opt-in legacy preview remains available, unchanged in
behavior or return schema. Stage 6 ports the old branch's independent
`galaxy_frontdoor_context.operational()` to current main. It is a RELEASE-GATED
read-only capability. The Stage-3 gateway loads it only on a separately owner-
authorized BIGBANG decision, which the existing Stage-2 control explicitly
cannot issue yet.

Operational retrieval uses the existing Phase-3 bounded statement-first
candidate admission, Phase-2 gravity and Seven Gates owner-importance model,
and Phase-6 governing/historical evidence metadata. The bounded candidate
pool admits up to four statement-grounded primary records from the most recent
100 scoped MemoryOS records, then up to two directly graph-linked supporting
context records. Relevance has strict precedence; within a relevance tier,
the demonstrated comparison is 80% relevance and 20% gravity. Verified current
records are distinct from historical and contextual records. Historical
records remain available as history but must not become current-default
recollections; linked context never becomes primary truth.

Stage 6 additionally tightens a connection that previously relied solely
on an upstream eligibility assertion. Each linked edge must actually connect
that exact context record with an admitted CURRENT primary, and still be
VERIFIED with matching endpoints during its second live-source read. A revoked
or changed graph edge returns HOLD rather than recycling stale context.

## Evidence and safety boundaries

- CI verifies read-only current/historical/linked ranking via mock Phase-3
  candidate-admission fixtures, plus explicit no-match, uninitialized runtime,
  changed statement/scope, source failures, unrelated/revoked edges and
  request-local HEATDEATH fallback. The actual legacy search envelope remains
  byte-for-byte structurally unchanged by the test-only BIGBANG path.
- The original legacy preview and Stage 1-5D regressions must continue
  passing, including real isolated SQLite for the legacy and emergency
  recovery paths and normal carrier startup with optional GALAXY broken.
- Full actual Phase-3 candidate admission over a representative current
  real MemoryOS corpus, recall quality/general paraphrase tests, false
  positives, bounded scan miss rates and runtime latency must be established
  independently before BIGBANG may be activated.
- No auto capture, E-LANE mutation, synthesis promotion, source overwrites,
  physical pruning or identity authority is added. Historical/provenance
  omissions are explicit HOLDs, never invented recall.
- Stage-2 `bigbang_activation_enabled=false` remains effective. The old
  production pilot stays vetoed by HEATDEATH's Stage-5D research-route
  guard. This source port does not change shared mode rows or rollout status.
- Source CI or a normal Docker image build cannot prove a deployed service,
  remote Turso parity, every chat carrier, external GPT-host integration,
  restart consistency or independent disaster recovery.

Release successor: validate actual representative MemoryOS queries and
negative controls, reconcile remaining non-destructive controlled GALAXY
capabilities without bypassing legacy approvals, then add Naomi-authorized
BIGBANG activation with staged deployment and live rollback receipts.

BIGBANG PASS + HEATDEATH FAIL = RELEASE HOLD.
HEATDEATH ALWAYS OVERRIDES BIGBANG.
NAOMI RETAINS FINAL AUTHORITY.
