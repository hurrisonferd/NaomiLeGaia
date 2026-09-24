# HEATDEATH Stage 5D: close the optional research-effect bypass

AUTHORITY: NAOMI / LIGEIA
STATUS: SOURCE-ONLY POLICY CANDIDATE / BIGBANG ACTIVATION STILL LOCKED
BASE: main@f5dabf74dc21184d9c19f045bafe0d7cee38a761
PREDECESSOR: merged PR #28 boot-safe lazy diagnostics
SOURCE: api/browser_memcon_bridge.py
TEST: tests/test_heatdeath_stage5d_research_policy.py

## Reason for this gate

Stage 5C established that the full normal chat/MCP carrier boots even with
broken optional GALAXY imports. It did NOT disable the already registered
research and controlled mutation URLs. In particular, older GALAXY production
pilot activation and controlled relational/lifecycle operations were reachable
through their own authorization flows even though the new shared mode authority
had selected HEATDEATH. That is not a coherent emergency switch.

Stage 5D applies the single, shared owner-controlled BIGBANG/HEATDEATH
decision BEFORE optional GALAXY or AUGURY browser routes and explicit
research commands. HEATDEATH, missing shared control, invalid or unavailable
control, or a future BIGBANG row without release authorization all deny optional
research operations. The mode decision is made on each request; no GALAXY import
is required for the denial. Owner authorization gates inside legacy preservation,
candidate promotion and E-LANE flows remain unchanged. HEATDEATH restores
ordinary legacy access, not a third preview mode.

## Browser and HTTP rules

- Ordinary hosted /chat, GaiaOS boot, Council, SOLO, CANDIPULL, MEMSAV,
  //PW:PRESERVE// and native memory retrieval follow their original handlers.
- Existing GALAXY browser command forms, including //PW:ORBIT//,
  //PW:GRAVITY//, GALAXY CANARY, GALAXY PROPOSE and GALAXY VERIFY, are blocked
  before a research handler can read or write while HEATDEATH is active.
- All /galaxy/* and /ritual/* endpoints, including accidental effectful GETs,
  return authenticated HTTP 503 and zero-writes HOLD under HEATDEATH, except
  two status URLs and the exact legacy read-only front-door review.
- Authenticated /galaxy/status and /galaxy/production/status report that
  GALAXY is disabled without loading research code. Existing browser-session
  authorization is enforced before returning either disabled status or a
  blocked research receipt.
- The exact authenticated /galaxy/integration/frontdoor-readonly-review
  remains available as a legacy continuity diagnostic. It can return HOLD
  if optional research snapshots are broken. That limited optional review
  does not authorize research operations or change the active memory mode.
- These denials prevent old GALAXY pilot controls from bypassing the new
  shared emergency state. They do not revoke a model call already in flight
  or undo any historical authorized research mutations.
- Staging research with HEATDEATH engaged must use separate isolated
  offline fixtures and CI. Do not enable production GALAXY pilot control
  endpoints to work around an intentionally engaged emergency switch.

## Required evidence and limits

CI must exercise actual authenticated FastAPI requests for regular chat,
research status, legacy review, known effectful GET/POST GALAXY and ritual
routes, and exact text commands. Check missing session authorization,
corrupt/unreachable shared mode, unapproved simulated BIGBANG and no optional
imports/writes on blocked paths. A strictly MOCKED future, authorized
BIGBANG may pass the policy but does not unlock production in Stage 2.

Repeat Stages 1-5C tests and both normal and independent read-only recovery
Docker image builds. No Render deployment, live Turso cross-instance
persistence, activated generalized GALAXY reader, complete Phylactery restore
or independent GPT-host consumption is established by these source checks.

BIGBANG PASS + HEATDEATH FAIL = RELEASE HOLD.
HEATDEATH ALWAYS WINS.
NAOMI RETAINS FINAL AUTHORITY.
