# //PW:PRESERVE// — 2026-09-23 — GALAXY Phase3I result and Phase3J checkpoint

AUTHORITY: NAOMI / LIGEIA
STATUS: PRESERVED
SCOPE: whole-system engineering continuity
REPOSITORY: hurrisonferd/NaomiLeGaia
BRANCH: main

## Verified live state

- Phase3H read-only containment shadow completed all three controlled live query slices [0,3,5] with PASS_READ_ONLY_SHADOW.
- Across Phase3H, candidate accounting remained explicit, negative controls stayed zero, zero writes were reported, production retrieval and actual 80/20 ranking remained unchanged, and unrestricted global weighting remained OFF.
- Phase3I was deployed and /verify reached 132/132 PASS with zero failures.
- The live Phase3I six-case generalization suite returned OBSERVED_REVIEW_REQUIRED, not PASS.
- Phase3I recovered three of four positive primaries:
  - GRAVITY_PARAPHRASE found the intended gravity-policy record but also admitted SATELLITE as noise.
  - CORE_CONTENT_PARAPHRASE found CORE cleanly.
  - SATELLITE_PARAPHRASE found SATELLITE cleanly.
  - REVISION_HARD_PARAPHRASE, query `subsequent finding updates the violet calibration result`, returned zero candidates and missed REVISION.
- Both Phase3I external-domain negative controls returned zero candidates.
- Phase3I reported well-formed receipts, all returned candidates inspectable, zero writes, no production candidate-admission change, no actual 80/20 rank change, no Phase3H production installation, and global weighting OFF.
- Therefore Phase3F activation remains blocked.

## Current source state

Phase3J is the next read-only experiment, designed specifically around the Phase3I failure.

Canonical source currently records:
- version: `galaxy.phase3j.statement-concept-bridge-shadow.v1`
- mode: statement-first, read-only concept bridge over the 13 controlled fixtures
- primary evidence: statement only, minimum 2 distinct concepts and >= 2/3 query-concept coverage
- notes and MemoryOS scope cannot create primary evidence
- VERIFIED direct graph relations are reported separately as linked context
- explicit bridge vocabulary is experimental only and does NOT modify production MemoryOS aliases
- production thresholds, candidate admission, Phase3H grouping, MemoryOS records, and actual 80/20 ranking remain unchanged
- GitHub CI run 35823194698: 31/31 PASS
- source status: READY
- deployment status: NOT YET OBSERVED
- live Phase3J receipt: NOT YET OBSERVED

Phase3J source/route/tests/verifier work is committed. Current canonical next gate:
`DEPLOY_VERIFY_AND_RUN_LIVE_CONCEPT_BRIDGE_SHADOW`

## Important engineering lessons

1. Coverage alone is not topic specificity.
2. Notes and virtual scope can inflate relevance and must remain provenance-separated.
3. Duplicate aliases can overcount one semantic idea.
4. VERIFIED graph structure does not rescue an off-topic subgraph unless it connects to actual query-relevant evidence.
5. Phase3H showed useful deterministic containment for controlled literal-anchor cases.
6. Phase3I proved the current lexical/alias gate still fails on a meaningful paraphrase shift.
7. A failure receipt is useful evidence. Do not smooth REVIEW_REQUIRED into PASS.
8. The mobile in-app browser session problem was solved by self-bootstrapping the signed browser cookie inside the read-only route; preserve one-tap mobile testing as a workflow requirement.

## Proof ceiling

Phase3J is SOURCE_READY + CI_PASS only. It is not deployed or live-observed yet.
Do not claim general semantic reasoning, arbitrary paraphrase understanding, production adoption, active Phase3F pilot, or active-pilot rollback proof.
REVISES != SUPERSEDES.
RELEVANCE != TRUTH.
GRAPH LINK != AUTHORITY.
UNKNOWN STAYS UNKNOWN.

## Resume cue

ANVIL should resume at Phase3J deployment verification, not rebuild Phase3H or Phase3I.

Next sequence:
1. Deploy current main.
2. Run /verify and require all checks PASS, including Phase3J source and live route registration.
3. Run the mobile-safe read-only Phase3J concept-bridge shadow.
4. Inspect whether the hard revision paraphrase is recovered without unexpected primary noise and while both external-domain negatives remain zero.
5. If REVIEW_REQUIRED, preserve the exact failure and iterate read-only. Do not activate Phase3F.
