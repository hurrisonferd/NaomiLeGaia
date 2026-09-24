# MERCURY // FIELD MANUAL
**Memory Engineering Reconnaissance for Comparative Utility, Reversibility & Yield**

> OPEN CHANNEL. KEEP THE SIGNAL. PRESERVE THE RECEIPTS.

**Parent project:** GALAXY, GaiaOS  
**Authority:** Naomi / Ligeia  
**Cadence:** Wednesday research watch, chosen for Wodin's day and Mercury as project symbolism  
**Document:** Living mission charter, v0.2  
**Status:** First manual pilot completed 2026-09-23 Eastern: eight primary-source-checked findings entered; no independent reproduction, integration or measured performance claim.

## 01 // THE MISSION

MERCURY is GALAXY's external research and engineering reconnaissance project. It watches public work on agent memory, temporal graphs, revision and supersession, contradictions, provenance-backed synthesis, consolidation, reversible state, human-approved execution, and auditable workflows.

We are not collecting fashionable architecture diagrams. We are looking for **verifiable techniques that can make GALAXY more useful, more efficient, cheaper to run, and easier to audit**.

The target is a **freeware-first, low-overhead GaiaOS**. Free to read is not the same as open source. Open source is not the same as free to host. A proposed improvement must disclose its license, actual dependencies, expected operating costs, and measurable performance before we call it economical.

## 02 // THE CITY HAS A MEMORY

Records are evidence, not orders. An old statement may remain historically important after a newer observation revises it. A contradiction must be visible before anyone tries to resolve it. A synthesis must identify its sources; it cannot quietly become its own origin story.

Our working principles:

```text
SOURCE != SYNTHESIS
REVISES != SUPERSEDES
PROVENANCE != AUTHORITY
RETRIEVAL INFLUENCE != PERMISSION
APPROVAL != IMPLEMENTATION
SOURCE COMMIT != DEPLOYMENT != RUNTIME PROOF
FREEWARE TARGET != ZERO OBSERVED OPERATING COST
UNKNOWN STAYS UNKNOWN
```

MERCURY's job is to find useful ideas **without importing their blind spots**. If a paper offers clever retrieval but loses negative evidence, we keep the retrieval idea under review and record the evidence loss. If a tool promises autonomous memory rewriting but lacks a reversible audit trail, that limitation goes in the ledger, not under the rug.

## 03 // FIELD PROCEDURE

The weekly watch produces leads. Leads are not findings until their claims have been checked against attributable sources. Each distinct finding receives a stable ID in [FINDINGS.md](FINDINGS.md) and, when possible:

- the author or project, primary source URL, publication/version and the date we checked it;
- the precise claim, the evidence actually inspected, and relevant limitations;
- license, freeware terms, required paid services, runtime/storage/CPU implications and likely integration effort;
- the GALAXY component it might affect, plus provenance, authority, rollback and retrieval-eligibility compatibility;
- an explicit disposition: **TEST, ADAPT, ADOPT, HOLD, REJECT, or SUPERSEDED**, with reasons and a link to any experiment or code change.

Unsupported claims stay labeled **UNVERIFIED**. Missing cost data stays **UNKNOWN**. Papers, marketing, code, benchmarks and live reproduction are different grades of evidence. No evidence grade grants Naomi's authority.

Do not silently erase rejected findings, negative results, stale links, or earlier interpretations. Amend entries with dated notes and preserve the previous reasoning.

## 04 // THE ZERO-TRUST BUILD FILTER

A candidate technique is not production-ready because it appeared in a paper, earned stars, or worked for someone else's dataset.

Before an integration proposal moves toward code, check: compatible license, reproducible behavior, correctness and source preservation, failure/restart behavior, local-resource requirements, dependency lock-in, reversible effects, and whether a smaller implementation would deliver the same measured benefit.

Prefer standard-library or existing-stack changes when practical. Add a dependency only if its benefit and ongoing maintenance cost justify it. Prefer bounded experiments, shadow modes and feature flags to irreversible migrations. Never bypass the explicit Naomi authorization and receipt gates.

## 05 // LIVE STATE AND PROOF CEILING

**Checkpoint: 2026-09-23, after Naomi's runtime receipts.**

- The deployed GALAXY Phase-5 read-only mutation design passed the observed review. The separate carrier verifier reported **178/178 PASS** for its tested checks.
- The controlled design fixes two source IDs and one synthesis statement, with a planned `GALAXY_SYNTHESIS_SHADOW` proposal/verification/revocation lifecycle.
- No effectful Phase-5 browser mutation route or live synthesis manifestation was proved by those receipts. Naomi has separately authorized **control exposure**, not an automatic synthesis write or production retrieval change.
- Unrestricted global weighting remains OFF. Earlier controlled proofs do not establish general-purpose semantic correctness or a fully launched GALAXY.

Update this section only from a new source, deploy or runtime receipt, identifying which level of proof it provides.

## 06 // THE POST-LIVE MERCURY AUDIT

**This is a mandatory final GALAXY implementation review, not permission to merge experiments.**

After the core GALAXY implementation is live and stable, capture a dated snapshot of **every MERCURY finding recorded up to that cutoff**, including HOLD and REJECT entries. Map each to the live architecture. Recheck source freshness, licensing, operating cost, correctness and reversibility. Propose bounded freeware-first benchmarks for the viable candidates and publish a disposition for every item. Record measured wins and losses, not imagined speedups.

The review closes only when every in-scope finding has an auditable disposition or an explicit **UNKNOWN / awaiting evidence** reason. The research watch continues after the cutoff; future findings enter the next audit rather than delaying the first snapshot indefinitely.

Any code change, synthesis mutation, retention policy, or retrieval promotion gets its own authorization and proof ladder:

`PROPOSAL -> APPROVAL -> SOURCE -> CI -> DEPLOY -> LIVE RECEIPT -> READBACK -> COMPARATIVE TEST`

## 06A // FIRST SIGNAL CAPTURE

The initial manual Wednesday pilot was performed on **2026-09-23 Eastern**, ahead of the first scheduled automated watch on **2026-09-30**. It inspected accessible primary paper metadata/abstract, maintainer repositories, official docs and source LICENSE files for eight targeted leads, then entered eight distinct records in the [Signal Ledger](FINDINGS.md).

**[Read the first field report](REPORT-2026-09-23.md).** It records source-backed claims and their limits, individual license/cost cautions, cross-references to live-proven GALAXY components, and bounded experiments to consider after separate authority gates. None of the eight has been independently reproduced. No automatic GitHub writes are enabled by the research watch; subsequent weekly findings need an explicit review/import step.

## 07 // REVISION DISCIPLINE

This README is a mission outline, not a scientific result or a claim of autonomous operation. Amend it when goals, constraints or actual proof change. Every substantive edit should cite its supporting artifact or runtime receipt, note what changed, and retain decisions that future maintainers need to understand.

**Change log**
- **2026-09-23, v0.2:** Completed first manual Wednesday pilot; primary-source-checked eight leads (not independently reproduced), saved a dated report and populated the canonical ledger. First scheduled automated watch remains 2026-09-30.
- **2026-09-23, v0.1:** Founded MERCURY; defined Wednesday watch, evidence ledger, freeware-first filter and mandatory post-live GALAXY audit. No external findings imported as validated evidence.
