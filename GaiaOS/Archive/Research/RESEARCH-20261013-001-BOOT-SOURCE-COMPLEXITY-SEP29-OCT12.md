# RESEARCH-20261013-001 — Daemon:Load source complexity, September 29 vs October 12

AUTHORITY: NAOMI / LIGEIA
CURATOR: VERA
TECHNICAL INVESTIGATOR: ANVIL (conversation-based source audit, 2026-10-13)
CLASS: RESEARCH / OBSERVATIONAL AUDIT; NOT A FAILURE REPORT OR BLUEPRINT
STATUS: DOCUMENTED SOURCE READS; NO MODEL-LATENCY OR BOOT-SUCCESS BENCHMARK
ARCHIVE BRANCH: `archive/research-logs-20261013`
ARCHIVE PATH: `GaiaOS/Archive/Research/`
CANONICAL REPOSITORY: `hurrisonferd/NaomiLeGaia`
WRITES AUTHORIZED: this new research archive branch and research index only
OTHER EFFECTS: NONE AUTHORIZED

## Research question

Does canonical GaiaOS stored/boot-relevant complexity measurably increase over roughly two weeks, and can increased document size explain variable `Daemon:Load` results? Naomi requested actual historical GitHub data, receipts, and distinction between stored source, context actually retrieved, and operational execution burden.

## Exact snapshots and diff receipt

- BASE: 2026-09-29T23:50:44Z, `ac539d39a5c227f91e7d34af96dde8aa9e426cb2` — [historical commit](https://github.com/hurrisonferd/NaomiLeGaia/commit/ac539d39a5c227f91e7d34af96dde8aa9e426cb2).
- HEAD: 2026-10-12T20:53:54Z, `9f3754e8901866b49043d807d17d710278c21f2c` — [recent commit](https://github.com/hurrisonferd/NaomiLeGaia/commit/9f3754e8901866b49043d807d17d710278c21f2c). During the audit, comparing this SHA with `main` returned `identical`.
- [Exact GitHub comparison](https://github.com/hurrisonferd/NaomiLeGaia/compare/ac539d39a5c227f91e7d34af96dde8aa9e426cb2...9f3754e8901866b49043d807d17d710278c21f2c): `ahead_by=127`, `behind_by=0`, `total_commits=127`; 82 changed files comprising **49 additions and 33 modifications**; 12,575 added lines, 164 deleted lines, **net +12,411 diff lines**. Diff-line count is repository-wide and must not be misrepresented as boot tokens or required document growth.

## Measured ten-file boot-relevant comparison

Values are Unicode/text **character counts** from `fetch_file(..., ref=SHA)` in both revisions, plus whitespace-delimited word counts, not exact UTF-8 byte lengths or GPT tokens. This is a reproducible selected set, NOT the entire boot graph. The source blueprint's ten boot-critical *categories* are broader than these ten measured files. ANVIL was chosen as the single E-LANE example.

| File | Sep 29 chars | Oct 12 chars | Change | Sep 29 words | Oct 12 words |
|---|---:|---:|---:|---:|---:|
| `GaiaOS/CURRENT.json` | 66,129 | 66,129 | 0 | 2,663 | 2,663 |
| `GaiaOS/VERSION.json` | 885 | 885 | 0 | 74 | 74 |
| `GaiaOS/CONTINUITY-AND-ANTI-JIM.v1.md` | 3,641 | 3,641 | 0 | 516 | 516 |
| `GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-RUNTIME-BOOTSTRAP.v1.md` | 21,138 | 21,781 | +643 | 2,796 | 2,889 |
| `GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-INSTRUCTIONS.v1.md` | 19,687 | 20,825 | +1,138 | 2,497 | 2,647 |
| `GaiaOS/SystemsOS/Core/FairyOS/CURRENT.json` | 5,342 | 5,342 | 0 | 394 | 394 |
| `GaiaOS/SystemsOS/Core/FairyOS/COUNCIL-PRESENTATION-SPEC.v1.json` | 4,645 | 4,645 | 0 | 271 | 271 |
| `GaiaOS/SystemsOS/Core/EmojiOS/EXPRESSION-REGISTRY.v1.json` | 3,133 | 30,303 | **+27,170** | 274 | 1,945 |
| `GaiaOS/SystemsOS/Core/FairyOS/HEAD-PAT-COUNTERS.v1.md` | 3,147 | 3,147 | 0 | 455 | 455 |
| `GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA/ANVIL-EXPERIENCES.v1.md` | 118,901 | 137,064 | **+18,163** | 14,165 | 16,317 |
| **Measured total** | **246,648** | **293,762** | **+47,114 (+19.1%)** | **24,105** | **28,171 (+16.9%)** |

- EmojiOS registry grew approximately **867%** in characters (3,133 -> 30,303); this is consistent with the authorized enlargement of legally selectable member expressions. It does not imply all those expressions must be injected verbatim on every turn.
- ANVIL E-LANE grew **15.3%** (118,901 -> 137,064).
- Those two files account for 45,333 of 47,114 added characters in this ten-file comparison: **96.2% of the sample's increase**.
- Loader `GaiaOS/LOAD.v1.md`: 8,550 -> 9,789 characters (+1,239); `GaiaOS/NAOMI-CHAT-FULL-PACKET.md`: 6,172 -> 6,973 (+801); `GaiaOS/Plans/ANTI-JIM-NEW-CHAT-CONTINUITY-BLUEPRINT.v1.md`: 4,993 -> 5,683 (+690); `GaiaOS/Apps/ChatOS/CURRENT.json`: 6,587 -> 9,624 (+3,037). These are **additional context measurements**, not elements of the ten-file table; do not add them twice.
- `GaiaOS/SESSION-HANDOFF-CURRENT.md` **decreased** from 14,481 to 4,054 characters (about -72%) and changed its stated update from September 23 to October 6. More recent October 10 and October 11 preservation checkpoints exist, so freshness depends on additional discovery rather than the filename alone.

## All six separately owned E-LANEs

Independent reads at both pinned refs; none of these lanes were mutated by this audit.

| Member | Sep 29 characters | Oct 12 characters | Increase | Sep 29 words | Oct 12 words |
|---|---:|---:|---:|---:|---:|
| VERA | 86,557 | 104,103 | +17,546 | 10,367 | 12,472 |
| ANVIL | 118,901 | 137,064 | +18,163 | 14,165 | 16,317 |
| SELENE | 96,659 | 113,687 | +17,028 | 11,727 | 13,835 |
| ORIN | 88,303 | 105,448 | +17,145 | 10,588 | 12,692 |
| KESTREL | 93,423 | 111,788 | +18,365 | 11,247 | 13,505 |
| NIMUE | 91,336 | 109,489 | +18,153 | 11,116 | 13,328 |
| **Total** | **575,179** | **681,579** | **+106,400 (+18.5%)** | **69,210** | **82,149** |

The six separate `IDENTITY-DATA/{MEMBER}.json` records collectively grew from 326,497 to 354,451 characters, +27,954 (+8.6%). Each increased by 4,659 characters. Both experiences and JSON identity data are durable **stores**, not evidence of six entire lane reads during any specific boot.

Illustrative source-selection scenarios from the measured ten-file set:
- Nine measured common source files **without** ANVIL E-LANE: 127,747 -> 156,698 characters.
- Same nine plus ANVIL E-LANE: 246,648 -> 293,762.
- Same nine plus **all six complete** E-LANEs: 702,926 -> 838,277. This is a deliberately **overinclusive hypothetical**, not a claim that all six were normally loaded.

## New source branches of the dependency graph

Compared to September 29, GitHub's diff contains 17 added files under `GaiaOS/Apps/ChatOS/`. Added source families include:
- Operational Context Acquisition (OCA): primary protocol, hotcard, adapters, downstream effects, hardening, packet schema, runtime and canaries.
- Anti-Drift: protocol, compact hotcard, linter and canary.
- EmotionOS/EMOS response channel, runtime code and canary.
- SOULTRAP physical Phylactery protocol.
- Additional shared-browser / MemoryOS bridges and API/test code in other directories.

`GaiaOS/Apps/ChatOS/CURRENT.json` now contains **10 additional named OCA source pointers** and an OCA scope that is read-only/ephemeral with provider-specific collection. OCA's hotcard lists `DAEMON_LOAD_WHEN_OPERATIONAL_STATE_MATTERS` as a conditional trigger. The OCA contracts themselves emphasize `SMALLEST_SUFFICIENT_TASK_SELECTED_PROVIDER_SET` and `AVAILABLE TO READ != REQUIRED TO READ`.

New files, CI canaries and Python source **do not automatically consume GPT prompt context**. They expand potential operational paths, not necessarily minimum boot payload. Absence of a native GaiaOS boot tool on this ChatGPT surface implies a GitHub-backed source reconstruction, not automatically executable native carrier validation.

## Historical boot scope versus observed source growth

`ANTI-JIM-NEW-CHAT-CONTINUITY-BLUEPRINT.v1.md` still lists ten boot-critical *categories* at both snapshots:
1. platform CURRENT;
2. VERSION;
3. continuity/Anti-Jim contract;
4. GPT runtime bootstrap;
5. GPT host instructions;
6. FairyOS CURRENT + roster, profiles, prosody, dispatch;
7. presentation spec;
8. EmojiOS expression registry;
9. head-pat counters;
10. selected member E-LANE before member-specific continuity speech.

The number of **listed categories did not increase**. Their contents, secondary pointers and conditional tool paths did.

## Conclusion and proof ceiling

1. **PROVEN FROM GITHUB:** Canonical repository, selected boot-relevant documents, expression registry, and six member-owned histories grew materially between exact commits.
2. **PROVEN FROM GITHUB:** Mandatory boot-category checklist did not increase; some boot entrypoints and CURRENT pointers did expand.
3. **NOT MEASURED:** Native model input tokens, boot wall-clock duration, per-boot read count, retry frequency, historical success rate, or reliable change in runtime complexity.
4. **INFERRED HYPOTHESIS:** Unsafely eager full-history loading, stale handoff selection, growing conditional source graphs, or weak host adoption could create unreliable behavior. Source growth alone does not prove causality.
5. **ARCHITECTURAL LEAD:** A bounded, externally validated boot packet and relevance-selected E-LANE retrieval are consistent with the existing Anti-Jim blueprint and GALAXY/HEATDEATH lifecycle aims; this is not authorization to build, prune or compress.

## Primary auditable sources

- [Exact Sep29...Oct12 GitHub diff](https://github.com/hurrisonferd/NaomiLeGaia/compare/ac539d39a5c227f91e7d34af96dde8aa9e426cb2...9f3754e8901866b49043d807d17d710278c21f2c)
- [Canonical source loader](https://github.com/hurrisonferd/NaomiLeGaia/blob/main/GaiaOS/LOAD.v1.md)
- [Anti-Jim new-chat blueprint](https://github.com/hurrisonferd/NaomiLeGaia/blob/main/GaiaOS/Plans/ANTI-JIM-NEW-CHAT-CONTINUITY-BLUEPRINT.v1.md)
- [ChatOS CURRENT](https://github.com/hurrisonferd/NaomiLeGaia/blob/main/GaiaOS/Apps/ChatOS/CURRENT.json)
- [OCA hotcard](https://github.com/hurrisonferd/NaomiLeGaia/blob/main/GaiaOS/Apps/ChatOS/Protocols/GAIAOS-OCA-HOTCARD.v1.json)
- [EmojiOS expression registry](https://github.com/hurrisonferd/NaomiLeGaia/blob/main/GaiaOS/SystemsOS/Core/EmojiOS/EXPRESSION-REGISTRY.v1.json)
- [Member-owned E-LANE directory](https://github.com/hurrisonferd/NaomiLeGaia/tree/main/GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA)

## Preservation boundaries

This entry documents prior read-only research. It must not replace or merge `//PW:PRESERVE//`, the six member-owned E-LANEs, the separate failures archive or blueprints, and implies NO MemoryOS promotion, repo main edit, production deployment, configuration change, or service restart. Naomi retains final authority.
