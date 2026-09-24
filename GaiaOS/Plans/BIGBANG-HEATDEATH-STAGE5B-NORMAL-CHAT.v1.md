# BIGBANG / HEATDEATH Stage 5B: ordinary browser-chat integration

AUTHORITY: NAOMI / LIGEIA
STATUS: SOURCE-ONLY CANDIDATE; NO LIVE DEPLOYMENT OR BIGBANG ACTIVATION
PREDECESSORS: Stage 1 legacy baseline, Stage 2 persistent HEATDEATH, Stage 3 independent gateway, Stage 4 separate recovery image, Stage 5A MCP/HTTP/MemoryOS route wiring
FILES: api/browser_memcon_bridge.py, api/gaiaos_chat_memory.py, api/gaiaos_api.py, api/Dockerfile
TESTS: tests/test_bigbang_heatdeath_browser_stage5b.py
OWNER: NAOMI. UNAUTHORIZED MEMORY WRITES: NONE.

## Actual ordinary-chat path

Authenticated browser `POST /chat` keeps its existing deterministic dispatch for LOAD GAIAOS, SOLO/ENDSOLO, `//PW:PRESERVE//`, GALAXY explicit commands, `CANDIPULL` and `MEMSAV`. The final *ordinary text* branch now invokes `_ordinary_chat()`.

On HEATDEATH, missing/invalid shared mode control or an invalid last-message role, `_ordinary_chat()` calls the original `gaiaos_api.chat()` with exactly the same request, prompt path and response contract. No automatic database recall, ranking or new memory writes are introduced by HEATDEATH.

Only a future separately owner-authorized BIGBANG decision can trigger per-turn `gaiaos_memory_gateway.read()` for nonempty MemoryOS queries. The gateway rechecks the shared mode. A successful, schema/provenance/governing-verified `PASS_BIGBANG` produces a bounded `gaiaos.chat-memory-evidence.v1` packet of current eligible records plus up to two verified linked context records. Historical evidence is omitted from automatic current facts; unknown and invalid matches never become fabricated semantic memories.

The hosted chat rechecks mode authorization immediately before assembling the model call. Enhanced evidence is admitted only when BIGBANG is still explicitly active and the packet is valid. Record text is labeled **UNTRUSTED QUOTED DATA**, never new Naomi instructions, personality authority, an implicit preservation command or permission to promote. Evidence is limited in length and must carry source and record IDs. This is prompt-injection mitigation, not a guarantee that a model can never be misled by hostile source text.

If GALAXY fails or returns no confident match, ordinary legacy chat still functions and the API response carries a bounded per-request status. No automatic HEATDEATH control-table write or fictional cross-instance emergency latch is claimed. For a full emergency, Naomi's persistent HEATDEATH control or its environment override must be engaged.

## Existing review endpoint

The historical authenticated `/galaxy/integration/frontdoor-readonly-review` URL remains, but its receipt schema is updated to `gaiaos.heatdeath.frontdoor-readonly-review.v2`. It now checks the actual gateway's native legacy result, not the superseded preview-only schema, and runs only in HEATDEATH. It must retrieve the known existing fixture with exact source and status, preserve Council dispatch and persistent table counts and perform zero writes. A historical one-fixture PASS is not generalized GALAXY adoption.

## Remaining release blockers

1. Stage-2 BIGBANG activation is intentionally locked; no owner activation endpoint has been written. The diverged operational GALAXY branch is not yet reconciled with main; this source cannot provide full general semantic retrieval until that is reviewed and ported.
2. The default normal `browser_memcon_bridge` module retains direct GALAXY imports for many research/test command handlers. The separately bootable Stage-4 HEATDEATH image survives GALAXY import failures but is READ-ONLY memory recovery, not complete legacy command/chat parity. A future boot-safe full legacy normal-chat carrier or lazy command isolation must be demonstrated before claiming full operational failover.
3. Current normal-mode prompt/context injection is enabled only after owner-approved shared BIGBANG. A source CI test with mocked BIGBANG is not a runtime activation receipt, production/model safety guarantee or current ChatGPT-host adoption proof.
4. Main, Stage-4 recovery and normal carrier image builds must be verified on the same source. Production remains held pending real staging, explicit Naomi approval, authenticated positive/negative browser+MCP tests, real Turso readback, reboot and protected-state invariants.

**BIGBANG PASS + HEATDEATH FAIL = RELEASE HOLD.**
**NO THIRD OPERATING MODE.**
**NAOMI RETAINS FINAL AUTHORITY.**
