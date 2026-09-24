# MERCURY // SIGNAL LEDGER

**Parent:** [Mission / README](README.md)  
**Maintainer / final authority:** Naomi / Ligeia  
**Status:** Ledger scaffold. No independently verified external findings have been entered yet.

This is the durable index for the Wednesday MERCURY research watch. Weekly chat reports are leads and working notes; this file is the reviewable cross-reference for GALAXY's eventual post-live audit. **Do not imply that an empty ledger means no research exists.**

## Intake and evidence standard

Assign one immutable ID per distinct finding: `MERC-YYYYMMDD-001`. Reuse that ID in later updates, experiments, changes and final audit rows. The initial Wednesday watch is scheduled for **2026-09-30, approximately 8 AM Eastern**. If a watch report is unavailable or incomplete, mark that interval **MISSING** rather than assuming nothing new occurred.

Use these verification states: `UNVERIFIED_LEAD`, `PRIMARY_SOURCE_CHECKED`, `INDEPENDENTLY_REPRODUCED`, `INCONCLUSIVE`.

Use separate engineering dispositions: `NOT_REVIEWED`, `TEST`, `ADAPT`, `ADOPT`, `HOLD`, `REJECT`, `SUPERSEDED`. A recommendation is not an implemented change; a completed test is not a production deployment.

## Validated findings index

| ID | Topic | Primary source | Checked (UTC) | Evidence state | Disposition | GALAXY area | Follow-up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| *No validated entries yet* | | | | | | | |

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

## Leads mentioned in earlier discussion, NOT yet validated

These names are **search targets**, not evidence of any feature, license, performance or existence. Independently confirm every claim before moving an item into the validated index:

- Mem0
- Letta
- MemoryLACE
- Engram
- MOOSEDev
- LangGraph human-interrupt/checkpoint workflows
- OpenAI agent approval/guardrail workflows

Prior conversation comparisons are insufficient on their own. A broken URL, inaccessible codebase or unverifiable name is a finding about **verification failure**, not permission to invent missing documentation.

## Wednesday watch coverage log

| Watch date (Eastern) | Report reference | Coverage | Imported IDs | Notes |
| --- | --- | --- | --- | --- |
| 2026-09-30 | PENDING | NOT RUN | NONE | First scheduled watch; record actual execution once observed. |

## GALAXY post-live audit register

At the first stable post-implementation cutoff, freeze a **dated snapshot** of this index, reconcile it against all weekly watch reports, and record a disposition for **every** finding before marking the audit complete. Rejected, superseded and inconclusive findings remain in scope. Record source freshness, actual license, measured hardware/API cost, compatibility with explicit authority and reversible provenance, existing implementation overlap, and the exact code/test/readback evidence for any adoption.

**Audit snapshot:** NOT STARTED  
**Core GALAXY general-live status:** NOT CLAIMED BY THIS LEDGER  
**Findings reconciliation:** PENDING  
**Autonomous repository writes from the weekly watch:** NOT ENABLED OR CLAIMED

Later findings join the next audit cycle. No quiet omissions, no retroactive invention.
