# GALAXY Stage 9K · One-button historical audit page

**Owner:** NAOMI / LIGEIA. **Steward:** 58 · ANVIL. **Mode:** HEATDEATH, no inference, no writes.

## Purpose

Stage 9I produced owner-relayed, fingerprint-matched, signed receipts reporting two successful exact-source readbacks on an owner-adjudicated COLLISION. Stage 9J then provided a bounded, read-only diagnosis of authentic historical-memory evidence, but its authenticated POST endpoint is cumbersome to invoke manually on a phone. Stage 9K is strictly a **small owner interface** for that existing diagnostic, not a further inference system, a new historical relation, a release readiness shortcut or another control on the already crowded five-case console.

The standalone page is served at `GET /gaiaos/memory/historical-audit-console`. It has one private password field, one primary button, a plain-English outcome and a copy-redacted-result button. Public GET contains **only static HTML, JavaScript and a unique CSP nonce**, with `Cache-Control: no-store`; it does not read MemoryOS, show a secret or create a server session. Its embedded script makes no request before a user click. The owner enters their existing `GAIAOS_API_KEY` only into that same-origin page and clicks **Check historical evidence**; the browser POSTs to the already owner-bearer-protected Stage 9J route.

The page displays a plain-English interpretation of one bounded status code. It copies **only allowlisted, typed, redacted status and 0–100 aggregate counts**, never private source identifiers, version markers, statements, questions, SQL error details or the bearer key. If the 100-row scan is incomplete, no aggregate counts are copied. Unexpected or unsafe response flags, unknown reasons, malformed counts or a network failure produce HOLD with **no copyable result**. It uses `textContent`, not an HTML interpreter, for every dynamic value.

## Invariants

The Stage 9J historical audit remains the sole source of diagnosis. Neither the page nor this milestone creates historical records or relations, edits status or owner governance, invokes AUGURY/OpenAI, adds an automation, retries noisy canaries, alters E-LANES or changes HEATDEATH/BIGBANG. A report of `CANDIDATE_PRESENT_UNTESTED` remains **untested**, with `historical_retrieval_proven=false` and `general_semantic_quality_proven=false`; every outcome retains the historical and general-semantic HOLD. No Stage 9F model-call authorization is renewed by deploying or opening the page.

## Permanent UI safety proof

The existing `tests/test_gaiaos_console_browser_contract.py` now registers this separate console and tests its **actually served** nonce-bearing HTML, JavaScript syntax, element IDs and all buttons through the no-network initialization harness. The additional Stage 9K suite executes a genuine registered button callback in an isolated JavaScript VM to check missing-key denial, same-origin POST, allowlisted redaction, clipboard copy, rejection of an unexpected private response and denial of falsified safety flags. The existing PR-only Stage 7 gate runs both suites and builds the normal carrier and independent HEATDEATH recovery images. No additional workflow, scheduled check or push-trigger duplicate is introduced.

## Production handoff

The source milestone is not a deployment. Render automatic deploy stays OFF. After Naomi elects to manually deploy the current `main`, verify the live `/health` source commit and visit the new standalone console. The only requested owner result is the **redacted JSON** copied by the new page. If the audit identifies a genuine candidate, the next separate gate is an explicitly owner-authorized, read-only historical-retrieval proof; if prerequisites are missing, document the absence instead of manufacturing a historical memory. Preserve `//PW:PRESERVE//`, all six independent E-LANES and the isolated recovery path.
