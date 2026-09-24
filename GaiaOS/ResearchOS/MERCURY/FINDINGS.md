# MERCURY // SIGNAL LEDGER

**Parent:** [Mission / README](README.md)  
**Maintainer / final authority:** Naomi / Ligeia  
**Status:** Eight primary-source-checked findings entered from first manual pilot; no independent reproductions and no code integrations.

This is the durable index for the Wednesday MERCURY research watch. Weekly chat reports are leads and working notes; this file is the reviewable cross-reference for GALAXY's eventual post-live audit. **Do not imply that an empty ledger means no research exists.**

## Intake and evidence standard

Assign one immutable ID per distinct finding: `MERC-YYYYMMDD-001`. Reuse that ID in later updates, experiments, changes and final audit rows. The initial Wednesday watch is scheduled for **2026-09-30, approximately 8 AM Eastern**. If a watch report is unavailable or incomplete, mark that interval **MISSING** rather than assuming nothing new occurred.

Use these verification states: `UNVERIFIED_LEAD`, `PRIMARY_SOURCE_CHECKED`, `INDEPENDENTLY_REPRODUCED`, `INCONCLUSIVE`.

Use separate engineering dispositions: `NOT_REVIEWED`, `TEST`, `ADAPT`, `ADOPT`, `HOLD`, `REJECT`, `SUPERSEDED`. A recommendation is not an implemented change; a completed test is not a production deployment.

## Validated findings index

**Pilot:** Wednesday 2026-09-23 Eastern, source checks recorded 2026-09-24 UTC. Eight **primary-source-checked** entries; no external code was executed, no benchmark was reproduced, and no GALAXY change is authorized. This is a targeted pilot, not an exhaustive research survey.

| ID | Topic | Source | Checked UTC | Evidence | Disposition | Review |
| --- | --- | --- | --- | --- | --- | --- |
| MERC-20260923-001 | MemoryLACE: sparse relation-aware retrieval | [arXiv:2609.03201](https://arxiv.org/abs/2609.03201) | 2026-09-24 | PRIMARY_SOURCE_CHECKED (abstract) | TEST | See entry below |
| MERC-20260923-002 | Engram (ly-wang19): bi-temporal memory | [official repo](https://github.com/ly-wang19/engram) | 2026-09-24 | PRIMARY_SOURCE_CHECKED (repo/LICENSE) | TEST (design only) | See entry below |
| MERC-20260923-003 | Graphiti: temporal episodes and incremental edges | [official repo](https://github.com/getzep/graphiti) | 2026-09-24 | PRIMARY_SOURCE_CHECKED (repo/docs/LICENSE) | ADAPT | See entry below |
| MERC-20260923-004 | Mem0: OSS local baseline vs temporal platform claims | [official repo](https://github.com/mem0ai/mem0) | 2026-09-24 | PRIMARY_SOURCE_CHECKED (official docs/LICENSE) | TEST (OSS baseline; temporal feature HOLD) | See entry below |
| MERC-20260923-005 | Letta Code: sleep-time reflection and git context | [active source](https://github.com/letta-ai/letta-code) | 2026-09-24 | PRIMARY_SOURCE_CHECKED (repo/blog/LICENSE) | ADAPT | See entry below |
| MERC-20260923-006 | LangGraph: human interrupts with durable checkpoints | [official repo](https://github.com/langchain-ai/langgraph) | 2026-09-24 | PRIMARY_SOURCE_CHECKED (docs/LICENSE) | ADAPT | See entry below |
| MERC-20260923-007 | OpenAI Agents SDK: per-call approval semantics | [official source](https://github.com/openai/openai-agents-python) | 2026-09-24 | PRIMARY_SOURCE_CHECKED (docs/LICENSE) | ADAPT | See entry below |
| MERC-20260923-008 | MOOSEDev: typed project-memory graph with proprietary core | [official repo](https://github.com/Trivyn/moosedev) | 2026-09-24 | PRIMARY_SOURCE_CHECKED (repo/LICENSE) | HOLD | See entry below |

## Pilot field notes // 2026-09-23 Eastern

**Research boundary:** direct primary preprint abstract, maintainers' own repositories/documents and source license files. These establish what authors *say* or publish, not independent reliability. All numerical performance gains are source-reported; license snapshots apply to inspected repositories at check time. No install, live test, cost benchmark, or third-party security audit was performed.

### MERC-20260923-001 // MemoryLACE: sparse relation-aware retrieval
- **First observed:** 2026-09-23 Eastern; **last primary-source check:** 2026-09-24 UTC.
- **Primary source:** [arXiv:2609.03201](https://arxiv.org/abs/2609.03201), Yacoubi et al., submitted 2026-09-02.
- **Precisely checked claim and evidence:** Accessible primary abstract describes local merge/supersession/contradiction relationships, atomic memories, provenance and relation-aware evidence retrieval. Authors report 66.6% less BEAM end-to-end runtime than Hindsight under their setup. That number has NOT been reproduced or generalized to GALAXY; full methods/code not inspected.
- **License and use rights:** Paper accessible; official reusable implementation and code license UNKNOWN.
- **Dependencies/cost:** Sparse-neighborhood implementation may be small; actual LLM/embedding/CPU/storage cost UNKNOWN.
- **GALAXY cross-reference:** Phase-4 typed edges and Phase-5 provenance already overlap; missing controlled proof of relation-expanded retrieval relevance.
- **Evidence state / engineering disposition:** PRIMARY_SOURCE_CHECKED (abstract) / **TEST**.
- **Bounded next experiment, NOT authorized:** Compare query-gated one-hop evidence expansion with current retrieval on fixed positive and near-miss/contradiction cases; measure relevance leakage, provenance loss, tokens and latency. Fail if irrelevant links manufacture eligible candidates.
- **Independent reproduction:** NONE. **GaiaOS integration:** NONE. **Production effect:** NONE.
- **Revision history:** 2026-09-23 Eastern: first manual pilot entry; unresolved fields preserved.


### MERC-20260923-002 // Engram (ly-wang19): bi-temporal memory
- **First observed:** 2026-09-23 Eastern; **last primary-source check:** 2026-09-24 UTC.
- **Primary source:** [official repo](https://github.com/ly-wang19/engram), [LICENSE](https://github.com/ly-wang19/engram/blob/main/LICENSE), [linked preprint](https://arxiv.org/abs/2606.09900).
- **Precisely checked claim and evidence:** Maintainer README documents bi-temporal facts, supersession/provenance, hybrid retrieval, point-in-time queries and an offline deterministic hashing/rule-based/in-memory smoke test. Claims about benchmark gains remain unreplicated; authors say one published judge has since been retired. This is NOT the unrelated thebtf/engram repository.
- **License and use rights:** AGPL-3.0 OSS plus a separately offered commercial license. Do not copy code until licensing compatibility is reviewed.
- **Dependencies/cost:** No external API required for the documented offline demo; production backends and full LLM benchmarks can incur costs. Measured CPU/hosting cost UNKNOWN.
- **GALAXY cross-reference:** Phase-4 governing vs history and Phase-5 provenance; two-clock truth queries and benchmark harness are comparison candidates.
- **Evidence state / engineering disposition:** PRIMARY_SOURCE_CHECKED (repo/LICENSE) / **TEST (design only)**.
- **Bounded next experiment, NOT authorized:** Run the upstream zero-setup smoke test in an isolated environment; independently design original as-of temporal negative cases for GALAXY. Keep AGPL source out of GALAXY pending explicit license review.
- **Independent reproduction:** NONE. **GaiaOS integration:** NONE. **Production effect:** NONE.
- **Revision history:** 2026-09-23 Eastern: first manual pilot entry; unresolved fields preserved.


### MERC-20260923-003 // Graphiti: temporal episodes and incremental edges
- **First observed:** 2026-09-23 Eastern; **last primary-source check:** 2026-09-24 UTC.
- **Primary source:** [official repo](https://github.com/getzep/graphiti), [LICENSE](https://github.com/getzep/graphiti/blob/main/LICENSE), [docs](https://help.getzep.com/graphiti/getting-started/welcome).
- **Precisely checked claim and evidence:** Official docs describe temporal validity windows, raw source episodes, incrementally updated edges, hybrid semantic/keyword/graph search and historical retrieval. They also document Neo4j/FalkorDB and default OpenAI inference/embeddings, plus configurable local OpenAI-compatible providers; small local models may fail structured extraction.
- **License and use rights:** Apache-2.0 core. Graph backend, model licenses and proprietary managed Zep are separate.
- **Dependencies/cost:** Extra graph database and model inference/embeddings; local Ollama may remove per-call charges, not hardware/maintenance cost. Actual resource use UNKNOWN.
- **GALAXY cross-reference:** Existing SQLite/Turso edges and Phase-4 rollback may support validity-window/episode concepts without a second DB.
- **Evidence state / engineering disposition:** PRIMARY_SOURCE_CHECKED (repo/docs/LICENSE) / **ADAPT**.
- **Bounded next experiment, NOT authorized:** Prototype original bounded validity-window and episode-ID columns in an isolated SQLite fixture; compare correctness and overhead before considering a Graphiti deployment.
- **Independent reproduction:** NONE. **GaiaOS integration:** NONE. **Production effect:** NONE.
- **Revision history:** 2026-09-23 Eastern: first manual pilot entry; unresolved fields preserved.


### MERC-20260923-004 // Mem0: OSS local baseline vs temporal platform claims
- **First observed:** 2026-09-23 Eastern; **last primary-source check:** 2026-09-24 UTC.
- **Primary source:** [official repo](https://github.com/mem0ai/mem0), [LICENSE](https://github.com/mem0ai/mem0/blob/main/LICENSE), [OSS overview](https://github.com/mem0ai/mem0/blob/main/docs/open-source/overview.mdx), [OSS config](https://github.com/mem0ai/mem0/blob/main/docs/open-source/configuration.mdx), [temporal announcement](https://mem0.ai/blog/introducing-temporal-reasoning-in-mem0).
- **Precisely checked claim and evidence:** OSS docs show configurable memory with local Qdrant/SQLite and optional local Ollama versus default OpenAI API. Mem0's 2026 company announcement describes time signatures and temporal-intent reranking, with vendor-reported benchmark figures NOT independently reproduced. Current OSS config docs explicitly say graph memory is Platform-only; whether this temporal feature is in OSS is UNKNOWN.
- **License and use rights:** Apache-2.0 OSS core; hosted/Platform functionality must not be assumed open/free.
- **Dependencies/cost:** Default OpenAI inference/embedding charges possible; local Ollama needs local models, Qdrant and compute. Hardware fit/cost UNKNOWN.
- **GALAXY cross-reference:** Use as isolated local memory/retrieval baseline; temporal-intent ideas do not justify importing a platform-only dependency.
- **Evidence state / engineering disposition:** PRIMARY_SOURCE_CHECKED (official docs/LICENSE) / **TEST (OSS baseline; temporal feature HOLD)**.
- **Bounded next experiment, NOT authorized:** Test a small fully local OSS corpus against current GALAXY query admission, history preservation, accuracy and runtime; explicitly recheck which temporal capabilities exist in OSS.
- **Independent reproduction:** NONE. **GaiaOS integration:** NONE. **Production effect:** NONE.
- **Revision history:** 2026-09-23 Eastern: first manual pilot entry; unresolved fields preserved.


### MERC-20260923-005 // Letta Code: sleep-time reflection and git context
- **First observed:** 2026-09-23 Eastern; **last primary-source check:** 2026-09-24 UTC.
- **Primary source:** [active source](https://github.com/letta-ai/letta-code), [LICENSE](https://github.com/letta-ai/letta-code/blob/main/LICENSE), [sleep-time research](https://www.letta.com/blog/sleep-time-compute/), [context repositories](https://www.letta.com/blog/context-repositories/).
- **Precisely checked claim and evidence:** Maintainer work describes separate background memory reflection and a git-backed context-memory filesystem with isolated worktrees and reviewable merges. Current README describes a local/self-hosted mode but cloud as initial default. No independent performance or agent-continuity validation performed.
- **License and use rights:** Active letta-code repo Apache-2.0. Hosted service/provider/model terms are separate.
- **Dependencies/cost:** Background model calls use additional tokens/compute; rate/hosting/latency for a suitable local model UNKNOWN.
- **GALAXY cross-reference:** Future GALAXY shadow consolidation, proposed E-LANE synthesis and reviewable per-daemon branches; autonomous memory rewrites conflict with current explicit authority.
- **Evidence state / engineering disposition:** PRIMARY_SOURCE_CHECKED (repo/blog/LICENSE) / **ADAPT**.
- **Bounded next experiment, NOT authorized:** Generate only a source-cited shadow proposal from a cloned snapshot during idle time, with a reviewable diff; prohibit writes to governing MemoryOS until Naomi authorizes each effect.
- **Independent reproduction:** NONE. **GaiaOS integration:** NONE. **Production effect:** NONE.
- **Revision history:** 2026-09-23 Eastern: first manual pilot entry; unresolved fields preserved.


### MERC-20260923-006 // LangGraph: human interrupts with durable checkpoints
- **First observed:** 2026-09-23 Eastern; **last primary-source check:** 2026-09-24 UTC.
- **Primary source:** [official repo](https://github.com/langchain-ai/langgraph), [LICENSE](https://github.com/langchain-ai/langgraph/blob/main/LICENSE), [interrupt guide](https://docs.langchain.com/oss/python/langgraph/interrupts), [persistence](https://docs.langchain.com/oss/python/langgraph/persistence).
- **Precisely checked claim and evidence:** Maintainer docs show interrupt(), JSON-serializable pause/resume decisions and checkpointer-backed state; durability modes have different crash-recovery guarantees. No GALAXY carrier test or framework integration performed.
- **License and use rights:** MIT for core repo; hosted offerings and some checkpoint backends separate.
- **Dependencies/cost:** Can be self-hosted but adds workflow runtime/checkpoint infrastructure; cost versus current Ritual routes UNKNOWN.
- **GALAXY cross-reference:** Ritual exact approve/manifest boundary; possible replay/restart test patterns rather than wholesale framework import.
- **Evidence state / engineering disposition:** PRIMARY_SOURCE_CHECKED (docs/LICENSE) / **ADAPT**.
- **Bounded next experiment, NOT authorized:** Crash/restart between preview, approval and mutation; assert idempotent single write, exact scope and valid post-write readback with existing stack first.
- **Independent reproduction:** NONE. **GaiaOS integration:** NONE. **Production effect:** NONE.
- **Revision history:** 2026-09-23 Eastern: first manual pilot entry; unresolved fields preserved.


### MERC-20260923-007 // OpenAI Agents SDK: per-call approval semantics
- **First observed:** 2026-09-23 Eastern; **last primary-source check:** 2026-09-24 UTC.
- **Primary source:** [official source](https://github.com/openai/openai-agents-python), [LICENSE](https://github.com/openai/openai-agents-python/blob/main/LICENSE), [human-in-the-loop docs](https://openai.github.io/openai-agents-python/human_in_the_loop/).
- **Precisely checked claim and evidence:** Docs describe needs_approval on tools, call-specific interruptions, serializable RunState and resume after a human approve/reject; malformed non-object/NaN tool args can fail closed to manual approval. No independent GaiaOS integration/restart test.
- **License and use rights:** MIT SDK; model/API service fees and hosted tools are separate.
- **Dependencies/cost:** SDK can be studied without API calls; real model/tool operating expense UNKNOWN.
- **GALAXY cross-reference:** AUGURY/RITUAL confirmation, explicit authority and typed arguments. SDK workflow state is not itself database truth or Naomi approval.
- **Evidence state / engineering disposition:** PRIMARY_SOURCE_CHECKED (docs/LICENSE) / **ADAPT**.
- **Bounded next experiment, NOT authorized:** Add offline malformed, replayed, nested and duplicate-confirmation negative tests to Ritual without replacing its existing authorization boundary.
- **Independent reproduction:** NONE. **GaiaOS integration:** NONE. **Production effect:** NONE.
- **Revision history:** 2026-09-23 Eastern: first manual pilot entry; unresolved fields preserved.


### MERC-20260923-008 // MOOSEDev: typed project-memory graph with proprietary core
- **First observed:** 2026-09-23 Eastern; **last primary-source check:** 2026-09-24 UTC.
- **Primary source:** [official repo](https://github.com/Trivyn/moosedev), [LICENSE](https://github.com/Trivyn/moosedev/blob/main/LICENSE).
- **Precisely checked claim and evidence:** Maintainer README documents typed project decisions, reversible supersede/retract, human ratification, MCP access and canonical git-committed kg.nq N-Quads memory exports. README explicitly says early development/not production ready. Code/engine not tested.
- **License and use rights:** Apache-2.0 wrapper but essential MOOSE engine and its Oxigraph fork are CLOSED and separately licensed; build from source needs private-engine access per README.
- **Dependencies/cost:** Published binary terms, closed-engine access, long-term affordability and hardware cost UNKNOWN; not demonstrated as a wholly freeware modifiable stack.
- **GALAXY cross-reference:** Ideas for typed ontology checks, Git-diffable memory and proposed decisions; not a drop-in fully-open GALAXY dependency.
- **Evidence state / engineering disposition:** PRIMARY_SOURCE_CHECKED (repo/LICENSE) / **HOLD**.
- **Bounded next experiment, NOT authorized:** Compare a deterministic SQLite-to-git text export within existing stack before considering proprietary binaries or licensing discussions.
- **Independent reproduction:** NONE. **GaiaOS integration:** NONE. **Production effect:** NONE.
- **Revision history:** 2026-09-23 Eastern: first manual pilot entry; unresolved fields preserved.


## Entry template

Copy the block below for each new finding.

### MERC-YYYYMMDD-NNN // Short descriptive title
- **First observed:** YYYY-MM-DD / watch report or manual intake reference
- **Primary source:** direct URL, author/project, version or publication date
- **Last verified:** YYYY-MM-DD UTC
- **Claim actually verified:** narrowly worded, source-bounded statement
- **Evidence inspected:** paper sections, code commit/tests, maintainer documentation, or independent reproduction
- **Limitations / opposing evidence:** specific, or UNKNOWN
- **License and use rights:** SPDX expression or quoted official license link; UNKNOWN until checked
- **Cost and dependencies:** runtime, storage, APIs, hosted services, paid terms; UNKNOWN if unmeasured
- **GALAXY cross-reference:** component, overlapping existing behavior, gaps, conflicts, provenance and rollback impact
- **Practicality:** estimated setup effort clearly marked ESTIMATE; measured results separately marked MEASURED
- **Evidence state / disposition:** one value from each vocabulary above
- **Next experiment:** benchmark, expected behavior, comparison baseline, stop condition
- **Authority / implementation proof:** NONE until separately approved; link source commit, CI, deploy, receipt and readback if executed
- **Revision history:** dated updates, preserving earlier conclusions

## Prior leads checked in this manual pilot

Mem0 (MERC-004), Letta (MERC-005), MemoryLACE abstract (MERC-001), Engram by ly-wang19 (MERC-002), MOOSEDev (MERC-008), LangGraph (MERC-006) and OpenAI Agents SDK (MERC-007) now have primary-source records. Graphiti (MERC-003) was also added. **None** has been independently reproduced; MemoryLACE implementation/license remain UNKNOWN.

## Wednesday watch coverage log

| Watch date (Eastern) | Report reference | Coverage | Imported IDs | Notes |
| --- | --- | --- | --- | --- |
| 2026-09-23 (manual pilot) | [REPORT-2026-09-23.md](REPORT-2026-09-23.md) | 8 targeted sources, primary-source checked; not exhaustive | MERC-20260923-001 through -008 | No installs, benchmark runs or GaiaOS mutations. |
| 2026-09-30 (scheduled) | PENDING | NOT RUN | NONE | First recurring automatic watch; record actual execution once observed. |

## GALAXY post-live audit register

At the first stable post-implementation cutoff, freeze a **dated snapshot** of this index, reconcile it against all weekly watch reports, and record a disposition for **every** finding before marking the audit complete. Rejected, superseded and inconclusive findings remain in scope. Record source freshness, actual license, measured hardware/API cost, compatibility with explicit authority and reversible provenance, existing implementation overlap, and the exact code/test/readback evidence for any adoption.

**Audit snapshot:** NOT STARTED  
**Core GALAXY general-live status:** NOT CLAIMED BY THIS LEDGER  
**Findings reconciliation:** PENDING  
**Autonomous repository writes from the weekly watch:** NOT ENABLED OR CLAIMED

Later findings join the next audit cycle. No quiet omissions, no retroactive invention.
