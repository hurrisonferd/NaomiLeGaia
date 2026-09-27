# GALAXY Stage 9AE: ungraduated historical records MUST NOT leak into ordinary chat

AUTHORITY NAOMI/LIGEIA. SOURCE-ONLY STACKED DRAFT on Stage 9AD #105 and all earlier pending draft branches. BIGBANG remains locked. No credentialed Turso connection, history activation, original GaiaOS or SovereignOS database write, actual model API request, deployment, E-LANE mutation or production release is part of this PR.

## Why this closes a real integration gap

Stage 9AD proved that signed Stage 9Y historical import records with status STAGED_HISTORICAL_HOLD cannot be gravity-scored by Stage 9U's in-memory shadow planner. But read-only gravity exclusion alone cannot prevent a misclassified historical record from entering the normal browser-chat retrieval path: Stage 9W's operational reader trusts a separately computed governing state to mark current vs historical, and its gateway trusts the resulting envelope. A future alias mistake, stale pool, forged CURRENT governing state or source provenance drift could otherwise surface held archive statements even before formal owner-reviewed graduation. Because HOLD is not owner-approved recollection, no ordinary chat path may represent it as current, as a historical reference or as verified linked context.

## Fail-closed read boundaries

Stage 9AE adds THREE independently enforced gates directly into the EXISTING real routes, without introducing an optional dependency into the emergency gateway:

1. Operational GALAXY reader: after each candidate's source, scope and statement are re-read, and BEFORE governing state or gravity scoring, reject if the actual record has STAGED_HISTORICAL_HOLD or the fixed new-archive provenance prefix galaxy-archive-v1:. The same check runs on live linked record readback BEFORE considering live verified edges. Reject the full GALAXY result instead of silently filtering and pretending to have completed a complete search. A fake ACTIVE status plus a canonical ungraduated source is NOT graduation.
2. Memory gateway: independently reject these same two conditions for each PRIMARY, HISTORICAL and VERIFIED-LINKED GALAXY item even if the operational reader returns a syntactically valid forged packet. Separately, if HEATDEATH legacy retrieval itself ever returns a held/archive row (for example due to a misconfigured database alias), return HOLD with NO raw legacy evidence and NO fallback status. Ordinary valid legacy results remain unchanged; the emergency gateway still imports ONLY the legacy reader, emergency mode and standard-library dependencies at startup. It never requires Stage 9Y/9AE modules to perform a HEATDEATH read.
3. Actual browser model-instruction boundary: even after a successfully prepared server-side packet and an independently mocked approved mode, reject an injected/falsely prepared current or linked row if its status or archive source marks it unreleased. The real POST /chat route must still serve the ordinary non-memory response without showing any held statement, source location or private exception; user include_memory=False continues to prevent all memory lookup.

These checks are deliberately source-only while BIGBANG is locked and the new SOVMEM databases remain empty. A future REAL archive graduation must include an independent signed, versioned promotion receipt and a reviewed change to the release guard, not a forged status update or disabling a single condition. This stage does NOT graduate held records, change existing CURRENT or HISTORICAL_SUPERSEDED semantics for legacy records, modify the archived source or grant authority to quoted memory text.

## Synthetic proof and regression coverage

The new tests exercise the actual Stage 9W operational reader against staged HOLD in the primary current lane, historical lane and linked graph lane; an attacker changing HOLD to ACTIVE while retaining canonical archive provenance; an independently forged entire gateway context; an accidental HEATDEATH or BIGBANG legacy read of staged rows; and the actual FastAPI POST /chat with a forged prepared context while a test-only BIGBANG mode is mocked. The model client is mocked; its instructions MUST contain no held record. All tests are synthetic and require no owner tokens or hosted model requests.

Regression CI also runs original Stage 9W served-app browser-session and opt-out tests, verified edge consistency, Stage 3 emergency gateway, Stage 6 gravity preview, Stage 4 independent HEATDEATH recovery, and Stage 9AD/Y/Z historical import and rollback. Six independent E-LANE files and //PW:PRESERVE// remain source-checked. BIGBANG remains locked in actual mode control.

## Current deployment proof boundary

Naomi reported deploying latest main to Render while these changes were still stacked draft PRs. A deployment of main does NOT itself deploy these unmerged source changes or establish which exact commit Render currently serves. Only after separate owner-reviewed dependency-order merges, an observed deployed source SHA, real owner staging trial, durable reopen/restart and ordinary-browser behavior checks can release status change.

The real sovmem-staging and sovmem-main databases remain untouched by this source/test milestone; sovmem-main stays the permanent, clean future SovereignOS memory destination. Distinct real provider database identities, credential scope, remote import/rollback, historical eligibility, model calibration, durable restore and Naomi's explicit production cutover remain separate gates. Preserve all six E-LANES, //PW:PRESERVE//, CANDIPULL/MEMSAV, HEATDEATH and the Phylactery migration approval boundary.
