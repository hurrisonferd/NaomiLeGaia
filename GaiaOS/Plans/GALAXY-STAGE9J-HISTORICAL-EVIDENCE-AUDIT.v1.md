# GALAXY Stage 9J: Historical-evidence gap audit · v1

**Authority:** NAOMI/LIGEIA. **Engineering:** 58 · ANVIL. **Execution:** owner-only, read-only, no inference. **Release:** HEATDEATH locked.

## Why this milestone exists

Naomi's first signed Stage 9I live receipts report a bounded dual-source retrieval PASS for case 2, with zero model calls, zero memory writes and exact legacy parity. That proves that two approved source records were independently retrievable, but not that both semantically entail the question. **The historical Stage 7 release prerequisite is still missing.** Synthetic Phase 7 restoration canaries do not qualify as real historical-memory coverage. The Stage 9F model call authorization has already been consumed.

The existing technical preflight groups several independent failure modes under `NO_VERIFIED_DISTINCT_TECHNICAL_SUPERSEDES`. Repeating the same browser tests cannot diagnose which prerequisite is absent, and manufacturing a fictitious revision to pass the gate would be unacceptable.

## New bounded audit

`api/gaiaos_historical_evidence_audit.py` executes SELECT-only reconnaissance inside the configured owner-controlled MemoryOS backend, under independently checked HEATDEATH control. It uses the **same restricted 100-record / 100-verified-SUPERSEDES window, same technical-source eligibility filter and same distinctive old-version marker rule** as the existing Stage 7 source preflight. If either scan returns 101 rows, the audit stops with `BOUNDED_WINDOW_INCOMPLETE` rather than claiming a complete inventory. Synthetic, fixture, canary, calibration and test sources remain excluded.

It classifies which prerequisite is currently missing:

- no verified owner-authorized, directed SUPERSEDES edge in the bounded window;
- no edge connecting two approved technical records in that window;
- no ACTIVE approved successor;
- no genuine older-version marker that is absent from all eligible current statements;
- historical governing state does not show old-context exclusion and current-successor eligibility;
- real evidence exists, but the normal Stage 7 six-case preparer still cannot construct a valid full sample.

A matched candidate must also pass the *existing* Stage 7 preparer's six-case shape validation. A successful audit is only `CANDIDATE_PRESENT_UNTESTED`, never proof that historical GALAXY retrieval works. Genuine history may be ACTIVE-but-superseded or archived; an archived superseded memory may remain historically retrievable. The audit never makes a speculative relation, adjusts statuses, changes thresholds, or alters read paths.

## Privacy and owner control

The authenticated route `POST /gaiaos/memory/historical-evidence-audit` requires the existing bearer key and returns only finite diagnostic reason codes, bounded counts and general next actions. It never returns record identifiers, source names, statements, version markers, SQL errors or private keys. There is **no new browser button**, recurring canary, scheduled reminder, OpenAI call or active retrieval review. Code/CI proof is not a claim that the new route is live on Render. When the user chooses to deploy, normal exact public health-commit verification still applies.

The isolated regression suite exercises approved synthetic histories and all relevant failure modes: revoked or REVISES edges, unapproved sources, inactive successor, missing/shared markers, absent or broken governing state, an eligible archived old record, a valid but untested historical candidate, too few current cases, an incomplete 101-record window, emergency BIGBANG control and missing bearer authorization. The mandatory Stage 7 and independent HEATDEATH PR gates retain their existing tests, normal-image build and recovery-image isolation.

## Evidence boundary

The first live Stage 9I receipts remain preserved at `GaiaOS/Proof/STAGE9I-LIVE-OWNER-ORACLE-OWNER-RELAY-REDACTED-2026-09-25.json` and `GaiaOS/Proof/STAGE9I-LIVE-TWO-SOURCE-OWNER-RELAY-REDACTED-2026-09-25.json`. They are owner-relayed, not independently MAC-validated in this source-only milestone. Historical retrieval quality, representative semantic accuracy, restart/Turso proof and BIGBANG cutover require their own evidence and independent owner authorization. Preserve `//PW:PRESERVE//`, the six separate E-LANES and the independent HEATDEATH recovery path.
