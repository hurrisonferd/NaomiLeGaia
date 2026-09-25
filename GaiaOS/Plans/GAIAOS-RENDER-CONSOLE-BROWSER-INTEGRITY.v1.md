# GaiaOS Render Console Browser Integrity Contract · v1

**Authority:** NAOMI / LIGEIA. **Engineering steward:** 58 · ANVIL.

**Incident:** On 2026-09-25, a newly added Stage 9F owner-review button appeared in the Render console but did nothing. Python triple-quoted HTML consumed a JavaScript `\\n` string escape, generating an actual newline inside a browser JavaScript string literal. The GET page returned HTTP 200 and Python compilation passed, but the browser rejected the whole inline script before registering any button callbacks. The source repair was PR #63. A source-text assertion alone is not an adequate regression.

## Permanent pre-merge rule

Any change that adds or modifies an interactive button, inline JavaScript, or console HTML in the Render carrier must pass the **served-console browser contract** before merge:

1. Obtain the **actual HTTP GET HTML** from a local FastAPI TestClient running the proposed checkout. Do not substitute the Python template string.
2. Extract and parse the served inline JavaScript with **mandatory Node.js `node --check`**. No optional skips in CI; raw newlines, malformed quotes, incomplete scripts or incorrect escaping must fail the gate.
3. Boot the script inside an offline, network-blocked JavaScript VM with a fixture DOM that knows only the IDs in the served HTML. Reject absent/duplicate IDs, missing click handlers, and unexpected requests during initialization. Every `type="button"` control must register a click handler. Test the private owner oracle button's missing-key path to prove it gives feedback without contacting the server.
4. Keep the owner bearer key out of test fixtures, responses, screenshots, logs and GitHub Actions. No authenticated POSTs, OpenAI calls, MemoryOS mutation, production canaries or BIGBANG activation in this gate.
5. For any new GaiaOS console, register its safe, static GET route in `CONSOLE_ROUTES` in `tests/test_gaiaos_console_browser_contract.py`. New HTMLResponse GET routes whose path contains `console` are automatically discovered and **fail CI if unregistered**. For other Render operator pages with interactive controls, register an explicit route, provide safe offline fixtures, and extend the same suite before adding the button. External scripts or multi-script pages require explicit test support before shipping.
6. Add one focused simulated click-path regression for each **new owner action** beyond the general listener/parse gate. For authenticated actions, test the missing-key/denied path using inert fixtures rather than sending credentials or effects. A green compile/route-health result must not be described as proof that all downstream authenticated operations work.

**CI wiring:** existing PR-only `.github/workflows/gaiaos-bigbang-stage7-readiness.yml` and `.github/workflows/gaiaos-stage8-deployment-parity.yml` run this test when their relevant carrier surfaces or the contract change. Reuse existing workflow notifications; do not add a periodic canary, push-triggered duplicate, or deployment. The suite has two negative controls: it must reject the original raw-newline JavaScript syntax error and an inert button without a listener.

**Operations boundary:** this rule applies to source builds, not as a claim that Render automatically deployed. `render.yaml` keeps explicit owner deployment. Following a manual deploy, verify the exact live `/health` commit before testing new owner controls. A console wiring fix does not consume another model-call authorization or change the HEATDEATH/BIGBANG release lock.
