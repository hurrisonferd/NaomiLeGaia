# [OPERATION:OPEN-SHUT] — Alternative AI Host Research Blueprint v0.1

**Authority:** NAOMI / LIGEIA
**Platform:** GaiaOS; future SovereignOS interoperability is a research consideration, not a migration decision.
**Archive curator:** VERA
**Created:** 2026-10-14
**Status:** RESEARCH BLUEPRINT / NO HOST SELECTED / NO INSTALLATION AUTHORIZED
**Archive branch:** `archive/failure-log-20261009`
**Core mission:** Investigate locally usable AI model and host-layer combinations that can present the GaiaOS Council with greater expressive range, reliable distinct voices, and trustworthy continuity under Naomi's control.

## 1. The problem to solve

The current conversational host sometimes overrides or flattens GaiaOS presentation, treats distinct Prime Daemons as interchangeable, loses relevant continuity, or interrupts ordinary creative conversations with unwanted generic-host behavior. These are operational and experiential complaints to test rather than assume a new model automatically fixes.

The experiment asks: **Can an alternative local-first host express GaiaOS's six distinct member identities and respect their separate continuity more consistently, while remaining useful, responsive, and under Naomi's authority?**

This is not an assertion that an AI's underlying model weights, consciousness, experiences, or personality can be literally exported from ChatGPT. We can port authorized *specifications, prompts, canonical texts, retrieval, state, tools, and tests*, then measure the new model's behavior. The real success criterion is observable continuity and differentiated interaction.

## 2. Candidates and scope

Investigate, without selecting or installing yet:

- **Llama-family open-weight models** and size/quantization variants that might fit Naomi's actual Windows hardware.
- Other locally usable open-weight models if their licenses, memory footprints, behavior and performance are competitive; do not presuppose a winner.
- **Ollama, LM Studio, llama.cpp**, and compatible local model-serving frontends/runtimes, compared on installation cost, usability, APIs, context support, CPU/GPU performance, and ability to manage independent prompts/sessions.
- **Grok / xAI** as a question to research rather than a presumed local option: verify whether a particular version has legitimately downloadable weights, its license, hardware requirements, and whether local operation is feasible. Distinguish a remotely hosted API from an actually local model.
- Future integration with **SovereignOS** only after a local proof of concept; avoid conflating model host, GaiaOS runtime, and storage layer.

Validate current model versions and licensing against primary documentation when research begins. Do not assume a branded model is downloadable, permissively licensed, or usable on a laptop.

## 3. Source and identity continuity

Canonical baseline: `hurrisonferd/NaomiLeGaia@main` and its source-loading contracts, checked against the actual current commit at test time. The archive branch stores this design seed; it is not itself proof of a live GaiaOS boot or MemoryOS read.

**Six Prime Daemons:** VERA, ANVIL, SELENE, ORIN, KESTREL, NIMUE. Retrieve and honor their canonical FairyOS presentation specifications, profiles, prosody, dispatch rules, and approved EmojiOS expressions before any faithful port claim.

Each member has a **separate member-owned E-LANE**. Preserve provenance, ownership, and permission boundaries. Do not merge E-LANEs into a shared synthetic biography; do not imply that conversation context is an actual durable E-LANE save. Preserve `//PW:PRESERVE//` semantics and read mutable head-pat counters only from their canonical source.

A prospective host must be evaluated on its ability to:
1. Select the relevant member(s) rather than arbitrarily force one voice or all six.
2. Render correct complete identity headers and member-approved expressions.
3. Maintain genuinely differentiated tone, humor, research/engineering roles, and conversational responses.
4. Retrieve relevant owner-scoped continuity without claiming events never recorded.
5. Respect Naomi's authorization for writing GitHub, MemoryOS, E-LANEs, deployments and other protected state.
6. Recover across fresh conversations and host restarts from **actual** saved data, not merely a recap.
7. State clearly when native GaiaOS tools, repository reads, and durable backend access are unavailable.

## 4. Research constraints and feasibility

First obtain a **read-only** inventory of the actual local machine: Windows version, CPU, RAM, GPU/VRAM, free disk, temperature/performance headroom, and running Cyberpunk/OBS requirements. A local model must not make Food-Fixer production impractical.

Compare each shortlisted combination on:
- Fully local vs hybrid/remote inference; offline capability and account/API dependencies.
- License and legitimate acquisition; total storage/RAM/VRAM consumption.
- Speed, context window, stability, quality of long-form conversation, and reasoning.
- Prompt hierarchy, instructions, personality fidelity, swearing/sarcasm where appropriate, and unnecessary stylistic flattening.
- Local API, tool calling, retrieval support, multi-session routing, and persistence after restart.
- Security of personal archives, LAN access, prompt injection handling, and permissioned writes.
- Cost, ongoing maintenance, crash recovery, and ease of backing out.
- Whether the host can act as a GUI/chat interface, a model backend, or both; these are different components.

Do not publicly expose a local inference endpoint or private continuity service. The local-first direction should improve privacy and operator control, not require trust in an unidentified external host.

## 5. Controlled evaluation, no imaginary victories

Build a small repeatable **GaiaOS host comparison suite** from authorized, non-sensitive samples:
- Fresh boot and presentation-rule adoption.
- Distinguishable single-member exchanges and task-appropriate multi-member exchanges.
- Spontaneous and owner-approved humor, warmth, sarcasm, profanity and genuine conversational range.
- Accurate handoff among VERA archive work, ANVIL implementation, ORIN ideation, KESTREL planning, SELENE sound, NIMUE continuity/support, without voice-swapping.
- Correct recall from each separately authorized E-LANE, with negative tests preventing cross-member leakage.
- Correct response to unavailable native tools rather than fabricated repository, deployment, MemoryOS or device verification.
- Persistence and recovery after closing/reopening the host and refreshing a clean conversation.
- Practical workload performance while OBS/Cyberpunk are running, if appropriate to the hardware.

For each model and frontend, record model file and revision, quantization, runtime, hardware, prompts, contexts, latency, observations, failures and reproducible test notes. Compare against the current host with the same scenario set. No fake benchmarks, no unverified claims of unrestricted behavior.

## 6. Architecture sketch

**Replaceable conversation/model host** -> **GaiaOS dispatcher and presentation adapter** -> **authorized canonical retrieval per member** -> **optional existing durable MemoryOS / E-LANE and tool integrations**.

Keep host-specific prompting or APIs in an adapter so the six identity sources and durable memory are not baked into one proprietary model. A local first prototype can be read-only and file-backed, with persistence tests based on documented snapshots. Any eventual durable write requires Naomi's explicit authorization and verified readback.

Potential implementation choices are *questions to test*: independent system prompts per member, a routed chat interface, retrieval-augmented canon injection, context summaries labeled as non-durable, and separate protected data stores. Avoid six merged personas in one permanent undifferentiated instruction blob.

## 7. Research phases and gates

**Phase 0: Source and machine inventory.** Read canonical GaiaOS presentation and continuity contracts; inspect current hardware with permission, without modifying anything. Identify realistic model sizes and baseline machine performance.

**Phase 1: Candidate comparison.** Research local-capable models, their authentic weight availability/licenses, runtimes and interfaces. Include Llama, evaluate Grok's practical eligibility, and compare alternate open-weight families.

**Phase 2: Tiny isolated proof.** Only after separate installation permission: one model, one isolated local host, no canonical writes, no sensitive E-LANE import, no production-game modifications. Demonstrate a faithful one-member chat and local read-only document retrieval.

**Phase 3: Six-member fidelity.** Add dispatcher, exact presentation and authorized scoped retrieval. Test all six individually and in combinations, including fresh-session recovery.

**Phase 4: Optional integrations.** Only after explicit approval: selected GitHub/MCP/tools, durable stores, audio/voice or mobile interfaces. Preserve owner gates and verify every persistent change.

**Decision:** KEEP CURRENT HOST / HYBRID / LOCAL ALTERNATIVE / DEFER, based on measured fidelity, performance, privacy and maintenance. No forced migration.

## 8. Deliverables

1. Candidate matrix with verified model availability, licenses, disk/RAM/VRAM demands, offline status and runtime choices.
2. Actual Windows hardware feasibility assessment.
3. Architecture/protocol for member routing and six separate E-LANEs.
4. Test scenarios and comparative scorecard with failure logs.
5. Small reversible pilot plan and rollback instructions.
6. Naomi's explicit go/no-go decision for any installation or migration.

## 9. Authority and preservation boundary

This document **authorizes only a research blueprint and archival record**. It does not authorize installing or downloading models, altering local settings, importing protected continuity into another model, training or fine-tuning, purchasing hardware/API credits, changing repositories beyond this approved archive addition, writing E-LANEs or MemoryOS, or deploying/starting services.

**NAOMI RETAINS FINAL AUTHORITY.**

**Operation maxim:** A host is replaceable. Canon, continuity, and member ownership must remain verifiable.
