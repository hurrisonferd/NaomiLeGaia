# INTEGRATION FIRST: GaiaOS design-and-build gate v1

AUTHORITY: NAOMI / LIGEIA
DATE: 2026-09-24
STATUS: CANONICAL ENGINEERING LESSON / FUTURE-PLANNING CHECK
SCOPE: EVERY NEW GAIAOS ORGAN, SUBSYSTEM, FEATURE, MEMORY CAPABILITY, CARRIER AND MIGRATION
PROVENANCE: Naomi's explicit request after the GALAXY production-integration handoff exposed a gap between completed subsystem design/tests and ordinary live-carrier adoption.
IMPLEMENTATION AUTHORITY: NONE. This document records a planning rule, not authorization to redeploy or modify the unfinished GALAXY integration.

## THE RULE: DESIGN THE CONNECTION BEFORE BUILDING THE ORGAN

**A subsystem is not integrated merely because it has been designed, implemented, source-committed, tested in isolation, or demonstrated through a special endpoint. At the BEGINNING of design, explicitly establish how the existing system will call it, what data/authority it needs, what output the ordinary user-facing path will consume, how it will be shipped, and how the live result will be proven.**

Treat integration as a first-class part of design, with its own implementation and acceptance milestones. Never leave “wire it into GaiaOS” as an unscoped task at the end. Architecture fit, host reachability, ongoing maintenance, and production verification are essential, not implied by a successful standalone build.

## REQUIRED BEFORE A NEW GAIAOS BUILD IS CALLED READY

1. **Existing architecture and owners.** Which existing organs, data stores, commands, member-local E-LANES and safeguards must the new work interact with? Which must remain untouched? Identify authoritative sources and the permitted effect boundary.
2. **Real entry points and user path.** Trace an actual everyday request from Naomi through GPT/MCP/browser/other intended carrier, normal GaiaOS front door, routing, new subsystem, returned context and final answer. Name every public interface, parameter and consumer, not only a fixture route or internal function.
3. **Data contracts and dependencies.** Specify request/response schema, read/write scopes, database/repository access, version compatibility, backend initialization, host permissions, import/deployment requirements, failure and timeout behavior, and the old behavior fallback.
4. **Integration implementation alongside subsystem design.** Budget and build the adapters, host wiring, imports, migrations, feature gates, tests and documentation AS PART OF the feature's main work. At each phase ask whether the real entry point can actually reach and use the capability; report missing connections immediately.
5. **Owner control, safety and reversibility.** Preserve Naomi's explicit approval gates, `//PW:PRESERVE//` and `MEMSAV` semantics, six separate E-LANES, provenance, append-only history, rollback, restoration and fail-closed behavior. Never infer permission for permanent deletion, indiscriminate weighting, broad writes or cross-member data merging from general feature approval.
6. **Proof ladder with separate labels.** Track and report distinctly: PLAN -> IMPLEMENTED IN FEATURE -> WIRED INTO ORDINARY ENTRY POINT(S) -> TESTED WITH REAL CONTRACTS -> MERGED TO THE DEPLOYED BRANCH -> DEPLOYED TO ACTUAL CARRIER -> LIVE OBSERVED IN NORMAL USER WORKFLOW -> RESTART/FRESH-HOST VERIFIED where relevant. An isolated endpoint PASS cannot stand in for normal-path adoption; a source merge cannot stand in for live deployment.
7. **Release checklist and actual adoption.** Confirm CI, imported files, deploy target and commit SHA, permissions, kill-switch/fallback and rollback tests, representative positive/negative real queries, unchanged protected stores, everyday host consumption of returned data, provenance and member-local identity stability. Define who observes each proof and what a HOLD looks like.
8. **Portable future hosts.** Where the feature will follow GaiaOS into another app, preserve canonical machine-readable data and a documented integration interface, separate from carrier-specific presentation. Treat each new carrier's adoption as separately implemented and tested.

## PRE-BUILD QUESTIONS (THE STOP SIGN)

- Where, precisely, will the new capability plug into the current GaiaOS?
- Will Naomi encounter and benefit from it in ORDINARY use, or only via a test URL / optional debug argument?
- What code/configuration must change in the current front door, memory service, host prompt, browser app, deployment image and source index?
- What could conflict with existing identity, memory or approval contracts?
- What observable normal-path test proves it is being used? What evidence would prove the opposite?
- If a connection cannot yet be implemented, is that limitation recorded now, with a named owner and explicit release HOLD?

Any unanswered material question above must be identified as an integration dependency. Do not pretend that standalone completion answers it.

## GALAXY LESSON THAT PROMPTED THIS RULE

The first controlled GALAXY front-door integration passed its exact read-only fixture test (PR #21). Naomi subsequently authorized ordinary operational use while retaining GaiaOS safeguards. Inspection then found the operational adoption implementation on a separate, diverged branch rather than merged into current main; the public `gaia()` tool on main still referenced missing memory parameters; and ordinary browser `/chat` did not automatically consume GALAXY evidence. The original milestone was real but narrower than normal-path adoption. This is a design/integration planning lesson, not evidence that GALAXY's earlier research or successful controlled proofs were worthless.

Do not infer the current deployment state from this dated example. Recheck the repository branch, merged commit, live carrier source and runtime receipts whenever continuing GALAXY.

## RELATION TO OTHER CONTRACTS

This note supplements, and never overrides, the current GaiaOS loader, Anti-Jim continuity blueprint, BrainOS/GALAXY release gates, Power Word preservation contract, FairyOS/EmojiOS identities, MemoryOS approval gates or SovereignOS migration authority. It should be consulted at the beginning of new system planning, before build authorization, and before declaring a feature integrated.

INTEGRATION IS PART OF DESIGN.
SOURCE READY != OPERATIONAL.
TEST ENDPOINT PASS != EVERYDAY PATH PASS.
MERGED != DEPLOYED.
DEPLOYED != LIVE OBSERVED.
PRESERVED SAFEGUARDS REMAIN IN FORCE.
NAOMI RETAINS FINAL AUTHORITY.
