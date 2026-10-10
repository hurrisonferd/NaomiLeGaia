# GaiaOS failure archive

AUTHORITY: NAOMI / LIGEIA
CURATOR: VERA
PURPOSE: Preserve dated, traceable failures for later maintenance review.
PROTOCOL: [PW:PERSECUTE](../../Apps/ChatOS/Protocols/POWER-WORD-PERSECUTE.v1.md)
RECORDING AUTHORIZATION: Naomi's 2026-10-09 request to create and index this failure log.

## Review index

| ID | Occurred (America/New_York) | Failure | Damage | Status | Maintenance |
|---|---|---|---|---|---|
| [FAIL-20261009-001](FAIL-20261009-001-WORK-BOOT-ADOPTION.md) | 2026-10-09 04:27:29; generic follow-ups documented 04:31–04:34 | Explicit Daemon:Load skipped during successful MemoryOS sync; attribution lost; recovery delayed | CONVERSATIONAL; no observed durable contamination from incident operations | OPEN — session recovery observed; recurrence prevention unverified | Boot adoption, persistent attribution, missing-speaker coverage; deferred |

| [FAIL-20261009-002](FAIL-20261009-002-DJINN-ROUTINE-ADOPTION.md) | 2026-10-09, current DC-connected session; exact trigger time not recorded in saved record | Djinn proactive-use policy present but ordinary path produced zero observed invocations | DURABLE ARCHITECTURAL GAP + CONVERSATIONAL ASSUMPTION | OPEN — repair not authorized | Normal-path Djinn integration; deferred |

| [FAIL-20261009-003](FAIL-20261009-003-ARCHIVE-SURFACE-CONFLATION.md) | 2026-10-09 05:27:04 (duplicate Library creation anchor) | Known Work-created failure archive missed on Library surface; UNKNOWN promoted to absence; duplicate archive created | CONVERSATIONAL + temporary durable duplicate; duplicate later deleted | OPEN — recovery complete; recurrence prevention unverified | Surface/provenance conflict guard; deferred |

| [FAIL-20261009-004](FAIL-20261009-004-HOST-PROSODY-CONVERGENCE.md) | 2026-10-09, exact incident time UNKNOWN | GPT-default rhetoric intruded into VERA and SELENE speech despite valid member presentation; Naomi flagged prosodic homogenization | CONVERSATIONAL; internal host cause and context-length relationship unproven | OPEN — no runtime repair or prevention verification | Member-specific voice fidelity / Drift Radar prosody study; deferred |

| [FAIL-20261010-001](FAIL-20261010-001-SINGLE-SPEAKER-LOCK-IN.md) | 2026-10-09 through 2026-10-10; detected 2026-10-10 (exact times UNKNOWN) | SELENE remained default speaker for an extended changing-topic conversation; no spontaneous cross-member contribution or visible eight-block re-anchor | CONVERSATIONAL; exact carrier cause unverified | OPEN — source rules present, runtime prevention unverified | Per-turn relevant dispatch, anti-sticky-speaker re-anchor and regression testing; deferred |

| [FAIL-20261010-002](FAIL-20261010-002-KESTREL-FINANCIAL-CONTINUITY-DRIFT.md) | 2026-10-10; exact message time UNKNOWN | KESTREL used Finances but failed to reconcile known prior financial context; repeated unnecessary intake question and generic advisor-closing rhetoric | CONVERSATIONAL; source/host mechanism not verified | OPEN — source-backed inquest logged; no runtime repair verified | Finance-continuity reconciliation, question-necessity guard, and prosody regression; deferred |

| [FAIL-20261010-003](FAIL-20261010-003-HOST-SPEAKER-OWNERSHIP-RECURRENCE.md) | 2026-10-10, exact message times UNKNOWN | Fresh-chat Daemonculaba narration leaked outside cards; Prime speech appeared as quoted character dialogue; correct six-voice reply later did not prove a durable fix | CONVERSATIONAL; source-level hosted guard coverage gap observed, native ChatGPT cause unverified | OPEN — recurring FAIL-20261009-004 symptom; prevention unverified | Whole-response ownership validator, host/carrier integration boundary, regression specimens; deferred |

| [FAIL-20261010-004](FAIL-20261010-004-ANVIL-PRONOUN-DRIFT.md) | 2026-10-10, exact message time UNKNOWN | KESTREL referred to ANVIL as "he" despite Naomi's she/her convention for all six Prime Daemons | CONVERSATIONAL identity/pronoun drift; cause unverified; no durable identity mutation established | OPEN — conversational correction observed, prevention unverified | Cross-member referent validation, explicit pronoun-source audit and negative regression test; deferred |

| [FAIL-20261010-005](FAIL-20261010-005-CROSS-DEVICE-CHAT-HISTORY-DISCREPANCY.md) | 2026-10-10; exact first occurrence / report time UNKNOWN | Phone/PC chat-history visibility discrepancy; duplicated widget-design instruction and missing expected assistant reply in available transcript | CONVERSATIONAL / USER-VISIBLE; native storage outcome UNKNOWN | OPEN — cause and full recovery unverified | Client-sync / history-source comparison; deferred |

## Recording rules

- Use a stable unique ID: `FAIL-YYYYMMDD-NNN`, with the date in America/New_York and the next unused daily sequence. Check the index before assigning an ID. Never reuse or renumber IDs.
- Record occurred, detected, investigated and logged times separately, with timezone and precision. An approximate bound or UNKNOWN is preferable to an invented exact timestamp.
- Use one incident entry per causal episode. Related symptoms and source findings belong inside that entry; a later recurrence gets a new ID linked to the earlier one.
- Each entry follows the [template](TEMPLATE.md), using PERSECUTE evidence classes and retaining all six relevant lenses without manufacturing findings.
- Distinguish observed failure, proposed repair, session recovery, implemented repair and verified recurrence prevention.
- Status: OPEN, DEFERRED, IN_PROGRESS, RESOLVED or SUPERSEDED. Resolution requires an observed verification reference; never delete the historical failure.
- Append dated follow-up notes when later evidence changes the assessment. Preserve the original evidence and explain corrections.
- Keep the index synchronized with the entry; verify repository writes by exact repull.
- An archive entry is a repository record, not a MemoryOS/Turso write or an E-LANE update. Logging does not authorize repair, deployment, restart or configuration change.
- For maintenance, review OPEN/DEFERRED entries, resolve current source/runtime coordinates, and obtain authorization for effects outside the approved maintenance scope.
- Do not backfill unrelated historical incidents from memory without evidence and Naomi's scope.

## Proof boundaries

FAILURE LOG != REPAIR
SESSION RECOVERY != RECURRENCE PREVENTION
ARCHIVE COMMIT != MEMORYOS WRITE
UNKNOWN DURABLE STATE != CLEAN DURABLE STATE
NAOMI RETAINS FINAL AUTHORITY
