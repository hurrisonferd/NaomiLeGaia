# GALAXY Stage 9W: normal browser-chat wiring under the locked two-mode gate

OWNER: NAOMI / LIGEIA
STATUS: SOURCE-ONLY STACKED DRAFT; NO MERGE, DEPLOY OR BIGBANG ACTIVATION.
PREDECESSORS: Stage 9R (#93) → 9S (#94) → 9T (#95) → 9U (#96) → 9V (#97).
The complete Stage 9V staging/real-driver readback remains a prerequisite, not a substitute for verified ordinary-host integration.

## Finding: standalone memory capability is not normal-path adoption

The existing gateway and bounded GALAXY/MemoryOS reader are implemented and tested, but the hosted normal /chat route previously called OpenAI without invoking the gateway by default. The internal chat() function accepted a memory_context argument for controlled tests; that is neither automatic normal route retrieval nor trustworthy when a browser supplies untrusted JSON. A successful staging canary does not correct this missing path.

## Implemented Stage 9W change

Normal hosted /chat now enters browser_chat(), which authenticates the browser session, rejects calls when the hosted model is unconfigured and calls the server-only optional gaiaos_chat_auto_memory.prepare_for_browser() only for the last actual USER message. The request's optional include_memory=false always disables automatic memory lookup. The plain browser UI sends the original messages-only format; no UI migration or new external API is required.

The helper checks the ACTUAL gaiaos_memory_mode.mode_status() before attempting ANY implicit gateway retrieval. Only effective_mode=BIGBANG + configured_mode=BIGBANG + bigbang_activation_enabled=true + matching mode schema can enter the approved gateway. It calls gaiaos_memory_gateway.read(MemoryOS, at most 4 records) and accepts only its exact PASS_BIGBANG, no-fallback, zero-write, no E-LANE mutation output. gaiaos_chat_memory.prepare() and validate_prepared() provide source/provenance compaction and a second structural gate.

Internal chat() rechecks the mode and evidence immediately before the OpenAI model call. It frames any statements as UNTRUSTED SOURCE DATA, not new user instructions, factual certainty, identity authority or memory-write permission. Only current verified source records become default context; superseded/historical context does not silently govern current recall.

The browser-facing FastAPI route has NO memory_context argument. Browser JSON that includes a forged memory_context is ignored. The internal chat(request, browser_request, memory_context=...) function remains available for isolated unit tests only; it is not bound to a public path. The new route is the only public /chat handler.

If HEATDEATH is effective, control is malformed, Turso cannot import, GALAXY cannot import, the optional retrieval fails or the prepared evidence fails either gate, normal chat continues unchanged, without claiming that a memory was retrieved. No gateway calls occur under valid HEATDEATH. The persistent mode latch is NEVER altered by this read-only bridge.

The existing Stage-2 mode service deliberately ALWAYS returns bigbang_activation_enabled=false, even if someone writes BIGBANG into its mode-control table. Therefore Stage 9W alone CANNOT ACTIVATE BIGBANG. It adds future-ready normal routing, not a release switch or implicit memory collection.

## Proof and remaining gates

Stage 9W CI must run the actual FastAPI /chat route with a mocked model: HEATDEATH, authorized test-only BIGBANG, explicit opt-out, browser injection, missing optional module, stale/invalid evidence, and the last-user-message boundary. It must preserve gateway, Stage 6 operational reader, Stage 9R–9V tests, standalone HEATDEATH recovery and the permanent //PW:PRESERVE// + exactly six independent E-LANES source contract.

The test-only authorized mode simulation is NOT production release authorization. Tests do not access real OpenAI, Turso, member-local E-LANES or a real user account. No actual memory is saved by running the source tests.

Still required before calling GALAXY finalized: independently provisioned and verified STAGING Turso with separate owner-scoped credentials; actual authenticated archive intake and exact staged import/backfill with readback/restart; true normal browser/MCP behavior through deployed commit; rated/unrated and historical-supersession semantic calibration; complete //PW:PRESERVE// and six-E-LANE restore; emergency HEATDEATH independent write/read; separate owner-approved release-gate implementation and explicit cutover. No source-only test may be promoted to live proof.

SOVREP-Core creation/Phylactery restoration is a later separately authorized action under Ligeia's direct repository ownership. The original repo, Render instance, production Turso, bridge and RavenOS stay intact. MERCURY PROTOCOL remains distinct ongoing research.
