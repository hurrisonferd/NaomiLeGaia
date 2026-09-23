# //PW:PRESERVE// — 2026-09-23 — GALAXY Phase-3 Exit Integration source-ready bedtime checkpoint

AUTHORITY: NAOMI / LIGEIA
TRIGGER: //PW:PRESERVE//
STATUS: COMMITTED
SCOPE: whole-system GALAXY continuity

## Current milestone

Phase3J live review is complete and passed with `PASS_READ_ONLY_CONCEPT_BRIDGE`. The exact hard REVISION paraphrase missed by Phase3I was recovered, the previous SATELLITE primary noise was removed, both external negative controls stayed at zero, all 13 fixtures were present, and the run remained read-only with zero MemoryOS writes and no production alias/threshold/admission/rank/global-weighting changes.

No Phase3K will be created. Remaining Phase-3 work is canonically named **Phase-3 Exit Integration**.

## Phase-3 Exit Integration build

Source is built and committed:
- module: `api/galaxy_phase3_exit.py`
- version: `galaxy.phase3-exit-integration.v1`
- exact bounded pilot allowlist: query indexes `[0,3,5]`
- primary admission: statement-first, reusing the live-validated Phase3J concept bridge
- minimum primary evidence: >=2 distinct statement concepts and >=2/3 query-concept coverage
- notes and virtual scope cannot create primary membership
- VERIFIED direct graph context is a separate linked-context lane and never enters weighted records
- primary cap: 4
- linked-context cap: 2
- external-domain disambiguators, missing primary, primary overflow, wrong scope, or wrong bounded limit fail closed
- singleton primary pools may pass guards without falsely claiming rerank
- full three-query switch suite still requires at least one actual rerank
- no MemoryOS write path added
- unrestricted global weighting remains OFF
- guarded pilot remains startup-OFF and requires explicit Naomi authorization for activation

Read-only preflight route:
`/galaxy/retrieval/phase3-exit-integration-review`

## CI evidence

Initial expanded CI run `35838026305` failed. Two implementation/test-harness defects were exposed:
1. false-valued safety invariants were incorrectly folded through `all(checks.values())`;
2. the production-test patch passed the runtime argument into the fake candidate-pool builder with the wrong signature.

Both were diagnosed and repaired rather than ignored.

Final GitHub Actions run:
- run id: `35838119652`
- conclusion: SUCCESS
- tests: **37/37 PASS**
- compile checks passed for production pilot, quality evaluator, Phase-3 Exit module, browser bridge, verifier and MemoryOS adapter

## Canonical state

Current canonical phase state:
`PHASE3_EXIT_INTEGRATION_SOURCE_READY_DEPLOY_PENDING`

Latest observed main head at preserve time:
`c420a0e67287fc1e8d3fd822f7282ea7896e3210`

The Phase3F active pilot remains unobserved/inactive. Global weighted retrieval remains OFF. Phase 3 is not closed.

## Tomorrow resume sequence

1. Deploy current main to Ligeia API.
2. Run `/verify` once and require a clean receipt.
3. Run the read-only Phase-3 Exit Integration preflight once.
4. If preflight passes, run a fresh guarded switch test.
5. Stop and review.
6. Do not activate the live pilot until Naomi explicitly authorizes that next step.
7. After explicit authorization: observe active-pilot retrieval, execute live rollback proof, require exact restoration, zero writes, no cross-relevance-tier inversion, and mode OFF.
8. If all required receipts pass, close Phase 3 and proceed to Phase 4 Revision/Supersession.

## Proof boundary

SOURCE_READY + OFFLINE_CI_PASS only for the new Exit Integration. Deployment and live behavior are still unobserved. Do not narrate deployment, preflight, switch-test, pilot activation, rollback, or Phase-3 closure as complete until corresponding runtime receipts exist.
