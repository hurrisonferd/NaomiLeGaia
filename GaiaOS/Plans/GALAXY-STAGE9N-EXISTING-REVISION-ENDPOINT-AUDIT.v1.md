# GALAXY Stage 9N: Existing revision endpoint eligibility diagnosis

**Authority:** NAOMI/LIGEIA. **Engineering:** 58 · ANVIL. **Mode:** owner-invoked, SELECT-only, release-locked. **No new button.**

## Why

Naomi's live Stage 9M one-click report on `d783fa4be8eab0dfef6a7cb24f3bc9ac611bb258` reported that both current records still pass literal retrieval with unchanged HEATDEATH parity. The complete bounded owner-technical history window contained three approved records, **no verified owner SUPERSEDES**, and **one verified owner REVISES** edge connecting **zero eligible technical pairs**. No old-version markers were evaluated because the pair-eligibility prerequisite failed first.

A VERIFIED REVISES edge establishes a documented revision relationship, **not** supersession. We must not convert it, invent an older memory or reduce the admission threshold merely to clear a dashboard HOLD.

## Read-only source classification

When the existing one-click report already says `NO_VERIFIED_OWNER_SUPERSEDES_IN_WINDOW` and the Stage 9M revision scan independently confirms `NO_APPROVED_OWNER_REVISES_PAIR`, Stage 9N adds one **nested** diagnostic inside the same historical-evidence card.

`api/gaiaos_revision_endpoint_audit.py` rereads the existing Stage 7 maximum-100 MemoryOS technical window and maximum-100 verified REVISES edges under unchanged configured remote Turso and HEATDEATH control. It requires parent aggregate counts to agree. For at most ten owner-authorized edges, it issues at most twenty **parameterized SELECT-only record lookups**, and only for endpoint IDs absent from that existing window. It does not broaden production retrieval or call another model.

The owner receives **aggregate categories for the older and newer sides**, never actual IDs, statements, sources, version markers or queries:

- A source record cannot be found, falls outside MemoryOS or lacks the owner's authority.
- The record is excluded by the existing fixture/canary/synthetic/calibration/test provenance rule.
- The record lacks an approved technical topic, or falls outside the bounded window.
- The alleged revision is self-referential, or one/both endpoints meet all existing eligibility rules.

A complete classification may say, for example, that the old side is calibration-origin and the new side is eligible. That is **not** evidence that the old record ought to become historical. It tells Naomi which documented evidence is missing and whether a future genuine version transition is appropriate. An unresolved missing record, more than ten owner edges, a 101-row window, unexpectedly eligible endpoints or changed parent counts returns HOLD with no claim of eligibility or historical readiness. Two separate bounded scans can establish compatible counts, not an atomic cross-scan snapshot identity; if underlying data changed without altering counts, repeat read-only verification before any later owner-authorized relationship action.

## Integration and non-negotiable safeguards

The existing `/gaiaos/memory/one-click-readiness` POST and `/gaiaos/memory/one-click-console` remain the **only UI action**. A new finite `endpoint_diagnostic` object appears only under `historical_evidence.revision_leads` when the parent source filters genuinely require it. The browser validates that parent, exact reason and numeric shape before showing a simple explanation and copying a redacted report.

No new API key exchange, POST, notification, canary, scheduled search, memory relation, persistent write, provider call or automatic BIGBANG release is created. Old/new categories are count-only; the number of six top-level one-click checks stays unchanged. The actual Stage 9M live receipt remains preserved at `GaiaOS/Proof/STAGE9M-LIVE-REVISION-SCOUT-OWNER-RELAY-REDACTED-2026-09-25.json`, as owner-relayed evidence rather than independent server attestation.

The isolated Stage 9N unit suite tests distinct exclusion reasons, targeted lookups, malformed/self-referential edges, count drift, 101-row overflow, a limit of ten edges and unchanged release control. An actual-served JavaScript simulation exercises the same existing button, strict nested redaction and copy denial. Existing Stage 7, Stage 8, HEATDEATH and independent recovery gates remain mandatory. **Source CI does not constitute a Render deployment or production-data finding.** Full historical retrieval and general semantic accuracy still require separate evidence, and any actual relationship change requires Naomi's explicit informed authorization.
