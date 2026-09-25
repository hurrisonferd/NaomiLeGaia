# Stage 9F: Reconnect AUGURY semantics to bounded GALAXY retrieval

AUTHORITY: NAOMI / LIGEIA
LEAD: 58 · ANVIL
STATUS: LIVE DEPLOYED / PUBLIC HEALTH PASS / ONE BOUNDED SEMANTIC SHADOW AUTHORIZED / BIGBANG LOCKED
SCOPE: MemoryOS, current owner-approved technical GALAXY records only
MODE: HEATDEATH release-locked
PRODUCTION EFFECT: NONE
MODEL COST: ZERO UNTIL OWNER INVOKES OPTIONAL BROWSER TEST

## Why Stage 9F exists

On September 25, owner-supplied live Stage 9C receipts showed three prepared
general GALAXY topic questions failing to retrieve their two intended, existing
technical memory records. Stage 9D diagnosed 1/4, 1/3, and 1/5 statement concept
matches, below the existing two-concept / 2/3 coverage requirement. Both
negative controls passed, and native HEATDEATH baseline stayed exactly equal.
Stage 9E then live-proved literal read-back of both approved records (2/2),
with exact legacy parity. That rules out basic literal retrieval wiring, but
does not validate natural-language semantic understanding.

Phase 3J's statement-first concept bridge was already verified on controlled
fixtures; current production can use its limited vocabulary but that is not a
general semantic resolver. AUGURY/RITUAL Phase 1 has a canonical GAIA semantic
unit schema and an exact compiler with a live-observed bounded SUPERSEDES
propose/verify/revoke cycle. It explicitly DOES NOT supply a general natural
language AUGURY parser. It must not be represented as though it already did.

## Isolated Stage 9F flow

Owner opens the existing private five-case console. A separate opt-in consent
box expressly authorizes sending exactly two current owner-approved technical
memory statements and five fixed staged questions to the already configured
OpenAI API, with store=false and a single request without retries. API usage
may incur charges. No model calls occur from import, startup, /health,
preflight, legacy reads, prior literal tests, normal chat or page load.
There is no scheduler, canary or new background workflow.

The model serves ONLY as an untrusted, non-effectful AUGURY interpreter. It
must distinguish RESOLVED, COLLISION, UNKNOWN for each case and, for a unique
resolution, return one of two statement slots plus an exact contiguous source
quote. Typed GAIA_SEMANTIC_UNIT required fields are assembled privately;
semantic intent is QUESTION, inferred context grants zero effect authority.
Unknown and collision never resolve by rank, importance, gravity or guess.

A deterministic exact READ_ONLY shadow Ritual then verifies the copied quote
against the selected saved statement, compiles exactly two distinct concepts
FROM THE VERIFIED QUOTE and sends those concepts through GALAXY's EXISTING
Phase 3J/Phase 3 Exit statement-first admission and operational read-back.
It checks actual chosen record ID, real MemoryOS scope, source provenance,
CURRENT governing state, and both legacy retrieval and control-state parity.
It never weakens the existing two-concept / 2/3 coverage threshold, invents
source text, synthesizes supersession, marks history verified, or reinterprets
Ritual consent.

The optional five-case result is redacted to safe status booleans and labels.
No IDs, statements, queries, quotes, secrets, notes or model text are returned.
Even an isolated PASS_SHADOW_SAMPLE_ONLY does not independently verify model
entailment, prove general semantic coverage, repair the three prior ordinary
production misses, pass the original Stage 7 six-case gate, or enable BIGBANG.
Absent authentic verified technical historical SUPERSEDES evidence, FULL HOLD
is mandatory. Separate source review and real owner-invoked tests are needed.

## Source-hardening receipts through 2026-09-25

The Stage 9F source path is now hardened through small isolated PRs before any live deployment:

- PR #46: missing provider key fails closed before review or SDK construction. CI run 36172116571 PASS.
- PR #47: built normal carrier image must import Stage 9F and register the owner-only semantic-shadow POST route. CI run 36175639343 PASS.
- PR #48: public /health exposes only a non-secret boolean proving Stage 9F route registration. CI run 36182108184 PASS.
- PR #49: blank or whitespace-only provider keys cannot report configured. CI run 36182255384 PASS.
- PR #50: blank or whitespace-only model names fail closed before SDK construction; /health exposes non-secret model-name readiness. Final Stage 7 semantic-safety run 36182421936 PASS, Stage 8 deployment-parity run 36182422061 PASS, and HEATDEATH route-regression run 36182421947 PASS.
- PR #52: whitespace-only provider keys are rejected by the Stage 9F route itself before SDK construction; the console wording now correctly states three questions spanning two approved memories. Stage 7 run 36183592466 PASS and HEATDEATH route-regression run 36183592601 PASS.
- PR #54: Render source policy explicitly disables auto-deploy; provider key and model name normalize accidental outer whitespace before Stage 9F SDK use; /health reports non-secret normalization state; deployment-parity CI now gates render.yaml. Stage 8 run 36187357336 PASS and Stage 7 run 36187357347 PASS.
- PR #56: adds `api/gaiaos_stage9f_deployment_verify.py`, a no-secret public-health-only live verifier. It requires the exact intended deployed commit plus owner-key/provider/model readiness and Stage 7/Stage 9F route registration, returns redacted PASS/HOLD only, and performs no memory read, model call, write or BIGBANG action. Stage 8 run 36187951587 PASS.

Canonical source-hardening merge receipt: `eb50733a3873cb9354f825b2d2889602f16b8e1f`.

These receipts prove source behavior and built-image wiring only. They do not prove the live Render carrier is on this revision or that the configured model resolves the five owner-approved cases correctly.

## Exact live acceptance sequence

The next boundary is intentionally linear and must not be collapsed into one opaque operation:

1. Source policy requires manual deployment (`render.yaml` sets `autoDeployTrigger: off`). Owner explicitly authorizes deployment of current `main` to the normal GaiaOS carrier. Deployment itself is a separate authority event and is not implied by ordinary source/test work or the hammer shorthand.
2. After deployment, run the source-controlled verifier from an environment with ordinary outbound HTTPS access:
   `python api/gaiaos_stage9f_deployment_verify.py --expected-commit <DEPLOYED_MAIN_SHA>`
   It performs one public `GET /health` only and returns `PASS_LIVE_HEALTH_PRECONDITIONS` or `HOLD`. No GaiaOS bearer key is accepted or needed.
3. The verifier requires all of the following before any semantic model call:
   - `status == "ok"`
   - `deployment_proof.source_commit` equals the intended deployed `main` commit
   - `deployment_proof.source_commit_verified == true`
   - `authorization_config.api_key_loaded == true`
   - `openai_configured == true`
   - `openai_model_configured == true`
   - `deployment_proof.stage7_readiness_route_registered == true`
   - `deployment_proof.stage9f_semantic_shadow_route_registered == true`
4. Stop on any mismatch. Do not substitute repository state, a browser cookie, a guessed environment value, or an older live receipt for the failed live check.
5. Only after a clean health receipt, owner separately authorizes the one bounded Stage 9F semantic-shadow invocation. That invocation requires the private bearer credential plus fresh `explicit_semantic_shadow_consent=true`, sends only the two approved current technical statements and five fixed staged questions, uses `store=false`, and performs no retries.
6. Record only the redacted result. Never paste bearer credentials, statements, quotes, record IDs, raw model text, database URLs, or private notes into ChatGPT, GitHub logs, screenshots, or public receipts.
7. A `PASS_SHADOW_SAMPLE_ONLY` closes only the bounded current-record semantic question. It does not authorize BIGBANG. A collision, unknown, source mismatch, read-back mismatch, legacy parity mismatch, unexpected write, or provider error remains HOLD.

After a Stage 9F live PASS, the broader BIGBANG release still requires the original representative Stage 7 real-store gate, authentic technical historical SUPERSEDES evidence, independent HEATDEATH recovery parity, Turso/restart and multi-replica control proof, ordinary browser-chat and MCP consumption checks, and a separate explicit Naomi activation decision with immediate rollback proven.

## Preserve

Never change //PW:PRESERVE//, six independent E-LANES, approved candidate
promotion rules, canonical release flags, native HEATDEATH memory retrieval,
the legacy fallback artifact, or the original Stage 7 release validator.
No writes are performed by this shadow. Private memory may only be sent to
the model after owner Bearer authentication and a fresh explicit consent
checkbox; never expose a key in chat, logs, receipts or screenshots.

## Live deployment receipt and owner authorization

On 2026-09-25 Naomi reported the live public `/health` receipt for deployed commit `a4b77cf83efa4e1f8501b185cf5d0d5779da8e8c`. It passed the Stage 9F live-health preconditions: source commit exact match and verified, owner API key loaded without disclosure, OpenAI key/model configured, and both Stage 7 readiness and Stage 9F semantic-shadow routes registered. Canonical redacted receipt: `GaiaOS/Proof/STAGE9F-LIVE-HEALTH-PRECONDITIONS-2026-09-25.json`.

Naomi then explicitly authorized the single bounded Stage 9F AUGURY semantic-shadow invocation. Authorization does not waive the existing bearer-auth requirement, fresh consent checkbox, one-request/no-retry limit, `store=false`, redaction contract, HEATDEATH parity check, historical HOLD, or BIGBANG release lock. The live semantic result remains unobserved until the authenticated operator console returns its redacted receipt.

## First live semantic-shadow result

On 2026-09-25 Naomi executed the single authorized live Stage 9F semantic-shadow call. The redacted receipt returned `HOLD` with reason `SEMANTIC_CASE_FAILURE_OR_LEGACY_PARITY`. All three current cases were `RESOLVED`; each returned an exact source quote, compiled an exact read-only ritual, and verified GALAXY read-back. Both negative controls returned `UNKNOWN` and passed. Native HEATDEATH retrieval remained exactly equal before/after. The only failed positive field was `expected_target_supported` on all three current cases.

Canonical receipt: `GaiaOS/Proof/STAGE9F-LIVE-SEMANTIC-SHADOW-HOLD-2026-09-25.json`.

This pattern must not be simplified to “the semantic model failed.” The current case generator assigns an expected record from the topic bucket used to choose that record, while a technical record may satisfy multiple topic buckets and same-topic record pairs are explicitly permitted. Therefore the expected target is not independently proven to be a unique semantic oracle. Until that oracle is repaired or independently adjudicated, the correct state is HOLD with source-grounded semantic mechanics observed and expected-target correctness unresolved. Do not spend another model call merely to repeat this ambiguous oracle.

## Oracle-mismatch repair path

PR #60 (merge `153924f126d699e69661cb6459597ef9a13422ec`, Stage 7 run 36189952828 PASS) keeps the live-shaped expected-target mismatch as HOLD but now distinguishes source-grounded semantic mechanics from expected-target oracle correctness. It does not weaken the pass gate.

PR #61 (merge `55fdfc9656d6cd5ddc74e976f918ae724fb4f0db`, Stage 7 run 36190326581 PASS, HEATDEATH route run 36190326574 PASS) adds an owner-authenticated, no-store, model-free adjudication path at `/gaiaos/memory/augury-semantic-owner-oracle-preview` and a private console panel. Naomi can read the two selected statement excerpts and three current questions locally, judge each as A, B, COLLISION, or UNKNOWN, then copy only a redacted oracle receipt. Record IDs and source fields are not exposed. No OpenAI request is made.

The prior one-call Stage 9F semantic authorization was consumed by the observed live call and MUST NOT be silently reused. A second model call requires a new explicit Naomi authorization after oracle adjudication. Current source is ahead of the live `a4b77cf...` carrier and therefore requires a manual Render deployment before the owner-oracle review control is available live.

## Owner-adjudicated first live sample

On 2026-09-25 Naomi completed the new authenticated, model-free local owner-oracle review and supplied the redacted receipt at `GaiaOS/Proof/STAGE9F-LIVE-OWNER-ORACLE-REDACTED-2026-09-25.json`. Judgments were case 0 = B (generator A), case 1 = A (generator B), and case 2 = COLLISION (generator A). No provider call, writes, private statement/question/ID disclosure, or BIGBANG activation occurred. The redacted owner receipt documents the operator's judgment, not independent entailment certification.

The deployed model's earlier three positives all returned RESOLVED with exact grounded quotes, compiled strict read-only queries and verified GALAXY read-back; all three disagreed with the generator's predetermined slot. **Conditional on both runs selecting the same ordered records and questions**, the model choices would have been B, A, B, aligning with the owner's first two answers but selecting one record for a question the owner judged COLLISION. The two independently redacted receipts lack a shared sample fingerprint, and the corpus could have changed across deployments. Do not claim confirmed agreement, error, or quantitative semantic accuracy across runs without that provenance.

The field `expected_target_supported` in the first model receipt is a **slot-equality test** (`selected_record_id == generator_expected_record_id`), not a source-entailment verdict. The owner's `generator_expected_supported = false` for COLLISION arises mechanically because the owner slot is null; it does not establish that record A is unsupported. A COLLISION is a distinct, non-unique ground-truth class, not an incorrect singleton target.

Next bounded engineering gate: bind a privacy-preserving, keyed sample identity (ordered two source record IDs/content and ordered case queries) to both owner and future semantic-shadow receipts, add redacted model-resolution slot/collision metadata, require an independently adjudicated non-ambiguous sample before scoring semantic success, and preserve COLLISION/UNKNOWN as first-class results. Do not weaken exact quote/provenance checks or the two-rare-concept GALAXY admission threshold. No new model call without separate fresh Naomi authorization; HEATDEATH and the historical release gate remain unchanged.

## Future proof boundary

CI proves import, type contracts, source quote validation, collision/negative
rejection, bounded read-back, unchanged native parity, strict owner/consent,
and absence of unexpected writes using FAKE records and a MOCK model.
CI is not evidence of actual OpenAI model quality, of live Turso read-back, or
of a valid historical supersession. Owner controls eventual Render deploy.
