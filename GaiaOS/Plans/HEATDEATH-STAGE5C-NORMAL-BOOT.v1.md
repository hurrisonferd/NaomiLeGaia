# HEATDEATH Stage 5C: boot-safe ordinary legacy carrier

AUTHORITY: NAOMI / LIGEIA
STATUS: SOURCE-ONLY CANDIDATE / NO PRODUCTION DEPLOYMENT
DEPENDENCIES: Stages 1 through 5B merged on main
FILES: api/gaiaos_lazy_diagnostics.py, api/browser_memcon_bridge.py, api/Dockerfile
TESTS: tests/test_heatdeath_stage5c_normal_boot.py

## The defect

Even with the persistent HEATDEATH controller and independent Stage-4 emergency
read-only image, the ordinary browser carrier previously imported twelve
GALAXY research modules and AUGURY at Python module load time. AUGURY itself
imports GALAXY Phase 4. A broken diagnostic import could prevent ordinary
legacy chat, Council boot and existing owner-preservation commands from
starting. The Stage-4 backup is intentionally a limited read-only path,
so this was an ordinary-carrier continuity gap.

## Stage-5C implementation

The browser bridge now uses allowlisted deferred diagnostic modules. They
import ONLY after a caller explicitly invokes the corresponding research
route or handler. A broken import produces an explicit authenticated
diagnostic 503, not a failed ordinary carrier boot or fake proof of success.
Ordinary chat, six-member GaiaOS source boot and HEATDEATH's native MemoryOS
read path do not depend on those modules. Stage-3 GALAXY retrieval is
separately lazily imported behind a future approved BIGBANG release gate.
The normal Docker image includes the new adapter.

The existing authenticated research/debug endpoints remain present.
This stage is startup isolation, NOT a complete policy gate for legacy-mode
diagnostics. Do not interpret a successful boot as permission to run
GALAXY mutation controls during HEATDEATH; separate command safety/review
and owner authorization checks remain release requirements.

## Source verification

- Tests sabotage ALL optional GALAXY and AUGURY imports before the full
  normal browser carrier is imported in a fresh Python process.
- Then they exercise the original browser ordinary-text chat path (mocked
  external OpenAI network call), validate actual six-member source boot,
  create a CI-only SQLite fixture using the existing explicit approved
  MemoryOS write path, and retrieve it through the HEATDEATH gateway with
  no GALAXY imports.
- Tests also check that optional research commands report an explicit
  HOLD/503 when the corresponding optional module cannot load.
- Repeat Stage-5B browser, Stage-5A HTTP/MCP, Stage-4 independent recovery
  and Stages-1-3 regression suites on each change.
- Build normal GaiaOS Docker image, sabotage GALAXY imports from inside
  the image, and prove the normal app still imports.
- Rebuild and import the independent read-only recovery image.

## Remaining before BIGBANG release

Operational GALAXY reader must be ported and reviewed against the current
main without replacing legacy defaults or loosening candidate/writer gates.
HEATDEATH mode must disable unsafe GALAXY mutation routes, persist through
the real Turso carrier and be observable across restarts and instances.
A verified owner-authorized BIGBANG activation interface, actual live
normal chat/MCP evidence, full-source/recovery images pinned by digest,
negative control and realistic phrase/coverage tests remain required.
Only source/image CI is evidenced by this stage. No production deployment,
remote persistence or general GPT-host adoption is implied.
