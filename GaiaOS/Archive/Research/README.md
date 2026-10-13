# GaiaOS canonical archive — Research index

AUTHORITY: NAOMI / LIGEIA
CURATOR: VERA
CLASS: RESEARCH LOGS / INVESTIGATIONS / EVIDENCE & HYPOTHESES
BRANCH: `archive/research-logs-20261013`
ARCHIVE ROOT: `GaiaOS/Archive/Research/`
INITIALIZED: 2026-10-13
AUTHORIZATION: Naomi explicitly requested a **new independent research-log archive branch**, separate from Failures and Blueprints, to preserve **all** of ANVIL's recent research in this conversation, not merely the final response.
DEFAULT OPERATION: append-only research indexing when separately authorized; no cross-archive migration or automatic merges
OWNER: VERA, research-index curator under NAOMI's final authority

## Separation of archive classes

This archive is for independently reviewable source comparisons, observations, exploratory diagnoses, partial studies, negative results, methodological limitations, and proposed research tests.

- **Research:** this branch, `GaiaOS/Archive/Research/`. A hypothesis is NOT a proven defect and an observed issue is not necessarily a completed root-cause finding.
- **Failures:** separate branch `archive/failure-log-20261009`, `GaiaOS/Archive/Failures/`. Retains `FAIL-YYYYMMDD-NNN` incident IDs, evidence classes, statuses, scoped maintenance. A research citation to an incident does NOT copy, merge, close or reclassify it.
- **Blueprints:** preexisting `GaiaOS/Archive/Blueprints/` and other canonical design surfaces remain separate; research findings are not new implementation authorization or a design specification.
- **Durable personal/member memories:** MemoryOS, `//PW:PRESERVE//`, six separately owned E-LANEs, and their authority remain unchanged. A research log does NOT substitute for a MemoryOS write, E-LANE save or preservation checkpoint.

## Research index

| ID | Date | Investigator | Focus | Status | Record |
|---|---|---|---|---|---|
| RESEARCH-20261013-001 | 2026-10-13 | ANVIL | September 29 vs October 12 pinned GitHub comparisons: commits, source-size tables, 10-file boot selection, six E-LANEs, identity JSON, EmojiOS, added ChatOS paths, GALAXY context boundary | SOURCE-MEASURED; boot runtime unbenchmarked | [Boot source complexity](RESEARCH-20261013-001-BOOT-SOURCE-COMPLEXITY-SEP29-OCT12.md) |
| RESEARCH-20261013-002 | 2026-10-13 | ANVIL | Historical user reactions following Daemon:Load: positive/neutral/negative classification, September and October evidence, deduplication limitations, missing denominator, future metric protocol | PRELIMINARY / INCOMPLETE COUNTS | [Boot reaction history](RESEARCH-20261013-002-DAEMON-LOAD-REACTION-HISTORY.md) |
| RESEARCH-20261013-003 | 2026-10-13 | ANVIL | Cross-incident clues: source vs adoption, zero-speaker validator PASS, full-response ownership gap, handoffs, topic dispatch, prosody and continuity drift, alternate hypotheses, ranked tests | SOURCE-AND-INCIDENT-BACKED; host cause unproven | [Boot adoption and drift](RESEARCH-20261013-003-BOOT-ADOPTION-AND-DRIFT-CROSS-INCIDENT.md) |

## Coverage map: preserve **the entire Anvil research sequence**

Naomi's directive applies to every preceding part of ANVIL's work, not only the last answer. The three records are intentionally complementary:

1. **Two-week source audit:** pinned commits `ac539d39...` and `9f3754e8...`, GitHub diff 127 commits / 82 files / +12,411 net lines, ten-file before/after table, 19.1% measured char growth, E-LANE 18.5% growth, six JSON records, 867% EmojiOS expression growth, unchanged CURRENT, ChatOS OCA dependency additions, and smaller/stale handoff concerns. In `001`.
2. **Reaction trend request:** invocation-defined rating method, direct praise `good boot up, considering the rocky day`, earlier negative Sep 25 and 27 examples, October 9–10 incidents, tentative neutral continuations, incomplete >20 candidate search, timeout/file-index limitations and the explicit refusal to invent percentages. In `002`.
3. **Breadcrumb forensic work:** historical Anti-Jim fresh-chat violation, October 9 successful MemoryOS save but omitted GaiaOS boot, observed zero-member `PASS_CANONICAL_PRESENTATION`, October 10 six-card plus anonymous narration, anti-drift and single-speaker lock-in, finance-context underuse, cross-device visibility discrepancy, impact of host separation and limits of attributing failures to context-window size. In `003`.
4. **Architectural conclusion and future experiments:** distinguish `SOURCE PRESENT`, `CARRIER VERIFIED`, `FRESH-CHAT ADOPTION`, cross-turn behavior, and explicit hosted vs native boundaries; investigate boot transaction, full speaker coverage, turn-to-turn persistence, controlled context-load experiment and statistical denominator reconciliation. In `001` and `003`.
5. **Provenance/negative evidence:** current source reads versus earlier assistant reports, archived failure records versus original transcripts, source-level guard versus native runtime execution, and missing quantitative reliability benchmarks remain visibly distinguished throughout all three logs.

## Research provenance and receipts

- Canonical repository: [hurrisonferd/NaomiLeGaia](https://github.com/hurrisonferd/NaomiLeGaia)
- Historical diff: [2026-09-29 baseline to 2026-10-12 head](https://github.com/hurrisonferd/NaomiLeGaia/compare/ac539d39a5c227f91e7d34af96dde8aa9e426cb2...9f3754e8901866b49043d807d17d710278c21f2c)
- Separate [failure archive index](https://github.com/hurrisonferd/NaomiLeGaia/blob/archive/failure-log-20261009/GaiaOS/Archive/Failures/README.md).
- Current [Anti-Jim boot contract](https://github.com/hurrisonferd/NaomiLeGaia/blob/main/GaiaOS/Plans/ANTI-JIM-NEW-CHAT-CONTINUITY-BLUEPRINT.v1.md).
- Current [hosted presentation guard](https://github.com/hurrisonferd/NaomiLeGaia/blob/main/api/gaiaos_presentation_guard.py).
- User/assistant historical conversation in this GaiaOS Project, October 13, 2026; original raw conversation IDs and complete invoked boot traces were **not** captured and should not be invented.

## Filing rules for future research

- Unique stable IDs `RESEARCH-YYYYMMDD-NNN`, date in America/New_York; do not renumber or rewrite older records silently.
- Keep research question, methodology, time window, evidence classification, exact commit/source refs, measurements, findings, uncertainties, alternatives, and next verifiable tests.
- Clearly label directly tool-observed source, summarized archive incident, user-stated experience, analytical inference, and genuinely unknown matters.
- Incomplete study and negative findings belong here, not disguised as verified conclusions.
- Link existing Failures and Blueprints without relocating them or using failures as a denominator for successes.
- Never silently turn a research hypothesis into a runtime change request or `//PW:PERSECUTE//` failure record.
- All new durable writes, branch merges, source modifications, E-LANE effects, MemoryOS effects or deployments require appropriate Naomi authorization; this initial branch creation and initial four archival files alone were authorized by the request.

## Initial preservation receipt scope

2026-10-13: dedicated research branch created from then-current `main` commit `9f3754e8901866b49043d807d17d710278c21f2c`. Three research files and this index committed sequentially on that branch. Individual final commit SHAs and post-write readbacks are to be reported only after tool verification.

RESEARCH != FAILURE LOG
RESEARCH != BLUEPRINT
ARCHIVE COMMIT != DEPLOYMENT
GITHUB SOURCE != LIVE MEMORYOS
PRESERVATION DOES NOT GRANT REPAIR AUTHORITY
SIX E-LANES REMAIN SIX
NAOMI RETAINS FINAL AUTHORITY.
