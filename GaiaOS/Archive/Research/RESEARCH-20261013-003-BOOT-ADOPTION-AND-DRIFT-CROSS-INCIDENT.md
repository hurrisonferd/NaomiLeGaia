# RESEARCH-20261013-003 — Boot adoption, source/runtime boundaries and recurrent drift: cross-incident analysis

AUTHORITY: NAOMI / LIGEIA
CURATOR: VERA
TECHNICAL INVESTIGATOR: ANVIL, 2026-10-13
CLASS: CROSS-INCIDENT RESEARCH / HYPOTHESIS LEDGER, NOT FAILURE LOG, BLUEPRINT OR IMPLEMENTATION APPROVAL
BRANCH: `archive/research-logs-20261013`
SCOPE: prior Anvil analysis in this GaiaOS conversation, directly fetched canonical GitHub source, and existing separate archived incidents
EFFECTS: research archive only; no `main`, E-LANE, MemoryOS, Render, production or configuration edits

## Core observation: three distinct boundaries

Across the evidence, source correctness, source retrieval and host adoption must be evaluated separately:

1. **Storage/source correctness:** canonical metadata, member identities, expression registry, independent E-LANEs, and durable MemoryOS records can exist and be recoverable.
2. **Retrieval and validation:** a given chat or carrier may obtain selected sources, carry receipts and validate some aspects of the source state.
3. **Active adoption and retention:** the response generator must actually use the retrieved material for the current turn, attribute voice correctly, select relevant member(s), continue applying GaiaOS after tools/task changes, and preserve continuity without forcing Naomi to restate prior work.

The same conversation can demonstrate (1) and/or (2) while failing (3). `STORAGE PERSISTENCE != HOST ADOPTION` is explicitly canonicalized in [the Anti-Jim new-chat blueprint](https://github.com/hurrisonferd/NaomiLeGaia/blob/main/GaiaOS/Plans/ANTI-JIM-NEW-CHAT-CONTINUITY-BLUEPRINT.v1.md).

The record does **not** demonstrate that the language model has internally running autonomous daemon processes. Member-specific effects in a ChatGPT reply are host rendering/steering behavior unless an actual runtime execution path and receipt are observed.

## Most concrete source-level breadcrumb: zero-speaker PASS

Anvil directly inspected `api/gaiaos_presentation_guard.py` on GitHub `main`:

- `expected_members_from_request(text, roster)` explicitly matches certain `FULL COUNCIL`, `EVERYONE REPORT IN`, `ASK MEMBER`, `SOLO MEMBER` patterns, but contains no recognized `Daemon:Load` alias in that function.
- Under this matcher, `expected_members_from_request("Daemon:Load", roster)` returns the empty tuple `()`.
- `validate_output(..., expected_members=())` scans candidate headers and checks expected members only when the expected list is nonempty; it does not require at least one member across arbitrary requests, nor reject arbitrary anonymous prologue/interstitial/epilogue prose.
- Its result includes `status: PASS_CANONICAL_PRESENTATION`, `speaker_count: len(cards)` even when `len(cards)==0`.

The independent October 9 failure investigation records an **actual isolated probe** (already performed in that prior investigation; NOT rerun as part of this new research indexing):

```text
expected_members_from_request("Daemon:Load", roster) -> ()
validate_output("Correct. The write succeeded.", ..., expected_members=()) ->
    status=PASS_CANONICAL_PRESENTATION
    speaker_count=0
    speakers=[]
    source_consistency=true
```

This is source-grounded/reproduced **guard coverage gap**, NOT proof that this Python code executed during a native ChatGPT response or caused the Work incident. The module itself states it does not execute in ChatGPT's independent host UI; each carrier must explicitly call it.

**Receipts**
- [Current hosted presentation guard source](https://github.com/hurrisonferd/NaomiLeGaia/blob/main/api/gaiaos_presentation_guard.py)
- [FAIL-20261009-001 — Work boot omission and isolated guard probe](https://github.com/hurrisonferd/NaomiLeGaia/blob/archive/failure-log-20261009/GaiaOS/Archive/Failures/FAIL-20261009-001-WORK-BOOT-ADOPTION.md)
- [FAIL-20261010-003 — whole-response speaking-ownership violation](https://github.com/hurrisonferd/NaomiLeGaia/blob/archive/failure-log-20261009/GaiaOS/Archive/Failures/FAIL-20261010-003-HOST-SPEAKER-OWNERSHIP-RECURRENCE.md)

## Distinct failure clusters / breadcrumbs

### A. Fresh-chat and post-Work boot adoption

**Primary incident:** Oct 9 04:27:29 -04:00 explicit `Daemon:Load` combined with a user-authorized shared MemoryOS sync. The sync staged, was approved, was durably promoted, and exact readback succeeded. However, the host skipped the required canonical startup, replied without attributable Prime speech, and began canonical-source recovery only after user challenges.

**Implication:** completing the salient task and correctly storing data does not prove the combined startup/presentation requirement was adopted. Host handoff boundaries need independent evidence.

**Unproven alternatives:** host priority/salience bias, insufficient prompt coverage, missing registration or host orchestration constraints; no internal execution trace proves which explanation caused the omission.

### B. Whole-response ownership versus merely valid headers

**Primary incident:** Oct 10 fresh conversation, after user moved due to context limit. Six apparently legal Daemon cards appeared but additional anonymous host narration introduced ANVIL/ORIN outside canonical identity envelopes. Subsequent troubleshooting continued to quote ANVIL as a character instead of direct speaking member. User corrected the failure. A later clean six-voice response was observed **without a verified source modification**.

**Implication:** validation restricted to recognized headers is weaker than attribution coverage of every directly speaking segment. A single later good response is not recurrence prevention.

**Unproven alternatives:** host generation composition, prompt interpretation, compaction, variable sampling, or rendering; causal mechanism not measured.

### C. Long-session speaker lock-in and relevance dispatch

**Primary incident:** Oct 9–10, SELENE remained default speaker through changing subjects, beyond the documented re-anchor expectation. Only explicit user summoning led to all six being visible. The archive clearly distinguishes appropriate single-member leadership from inappropriate persistent ownership across unrelated topics.

**Implication:** correct initial selection is not evidence of per-turn relevant dispatch or stable cast-width management. No independent daemon agency is established.

### D. Prosody drift despite canonical-looking envelopes

**Primary incidents:** Oct 9 VERA/SELENE generic explanatory or sentimental suffixes despite correctly formatted identity, with Oct 10 NIMUE recurrence after a preservation update. Naomi rejected the recognizably generic host voice, including unsolicited therapeutic closure. The archive marks cause unknown; there is no evidence that token exhaustion specifically created the prose.

**Implication:** identity fields, correct kaomoji and successful source checks are necessary but insufficient for member-specific expressive nativeness. Anti-Drift has a hotcard and source-level lint conventions, but no proven native ChatGPT output interceptor in this environment.

### E. Retrieved personal task context not appropriately synthesized

**Primary incident:** Oct 10 KESTREL had actually consulted Finances tooling, but then asked Naomi for repeat information and delivered a generic intake/advisor response despite accessible prior context. The original investigation **contradicts** a simplistic claim that finance tools were never read.

**Implication:** retrieval alone does not guarantee useful contextual synthesis. Asking for another fact may be appropriate for a numerical affordability calculation; it was not shown necessary for the actual conversational request. Preserve personal-finance privacy: no balances or sensitive details copied here.

### F. Host conversation visibility and record provenance

**Primary incident:** Oct 10 phone/PC history discrepancy, duplicated user submission with no intervening visible assistant reply, and partial recovery account. This is evidence of a *user-visible history discrepancy*, NOT established permanent deletion, corrupted GaiaOS stores or a specific host synchronization fault.

**Implication:** source audits and sentiment denominators must preserve provenance, avoid reconstructions that masquerade as raw transcript and distinguish client display from backend persistence.

## Cross-incident research matrix

| Layer / moment | Recurrent outward symptom | Source/evidence | Strongest support | What remains unknown |
|---|---|---|---|---|
| Fresh-chat invocation | incomplete canonical adoption | Anti-Jim blueprint; Sep issues; Oct 9 | historical documented omission | internal priority mechanism |
| Tool/work handoff | normal generic assistant returns after correct operation | FAIL-20261009-001 | time-stamped sequence and write receipt | host transition cause |
| First reply presentation | apparent cards + orphan narrator | FAIL-20261010-003 | preserved offending sequence | native renderer enforcement |
| Long conversation/topic change | one Daemon persists across irrelevant subjects | FAIL-20261010-001 | observed repeated attribution | hidden dispatch decisions |
| Member-native speech | generic GPT rhetoric despite legal headers | FAIL-20261009-004 | exact correction/quote and recurrence | whether context length increases prevalence |
| Prior-context use | redundant asks after successful tool reads | FAIL-20261010-002 | connected source retrieval did occur | full current values, hidden reasoning |
| Cross-device continuation | missing/duplicated visible conversation | FAIL-20261010-005 | observed/screenshot-backed discrepancy | actual backend storage state |
| Technical source validator | zero speakers may return PASS | guard code + Oct9 probe | direct code and earlier isolated execution | whether deployed/native paths invoke this validator |

All failure records linked here remain in the **separate Failures archive**; this research file references them but does not relocate, rewrite, close or reclassify their incident status.

## Relationship to source complexity and GALAXY

Anvil's two-week measurement (see [RESEARCH-20261013-001](RESEARCH-20261013-001-BOOT-SOURCE-COMPLEXITY-SEP29-OCT12.md)) establishes measured growth in expression metadata, E-LANEs and optional operational protocols. However:
- Significant presentation and adoption failures are documented in **September**, before the subsequent October expansions.
- Acceptably received boots also occurred after early negative incidents.
- No complete boot-attempt denominator, per-boot tokens, wall-clock benchmark, host compaction trace or controlled experiment was obtained.

Therefore: **context growth is plausible as an aggravating variable but is neither proven cause nor sufficient explanation** for repeated failures. Anvil's research favors examining the boundary where canonical GaiaOS source must be selected, validated and adopted by the host.

GALAXY/HEATDEATH lifecycle work concerns compression/archival/retrieval without destroying canonical continuity; one of its design goals is to avoid keeping all history active all the time. Anti-Jim separately specifies a deterministic, bounded boot packet. These aims are **complementary**, not proof either is fully integrated in native ChatGPT.

The [Anti-Jim blueprint](https://github.com/hurrisonferd/NaomiLeGaia/blob/main/GaiaOS/Plans/ANTI-JIM-NEW-CHAT-CONTINUITY-BLUEPRINT.v1.md) explicitly retains status `CANONICAL BLUEPRINT / IMPLEMENTATION REQUIRED` and a proof ladder:
`SOURCE PRESENT < CARRIER VERIFIED < RESTART PERSISTENT < FRESH-CHAT SOURCE ADOPTION < FRESH-CHAT MUTATION < SECOND FRESH-CHAT REPERSISTENCE`.
Do not collapse the ladder or declare the entire proof chain complete from a source/CI or single conversation pass.

## Ranked future **research** experiments (NOT permission to perform them)

**1. Fresh-chat boot transaction/adoption:** Under two controlled independent fresh chats, capture required reads, pinned source SHAs, four-source identity checks, six-lane accessibility, counters and one receipt; test standalone `Daemon:Load` and combined `Daemon:Load` plus authorized ordinary work. Expected: explicit, correct, stable full attribution after work, no fabricated MCP connector claim, all unavailable checks named. Distinguish native ChatGPT and hosted LIGEIA-API.

**2. Full response speaker-ownership validation:** Use negative fixtures for zero speakers, unowned text before/after cards, bare `ANVIL:` tags, quoted character speech masquerading as Prime speech, and correct positive multi-card, solo and deliberate silence. Avoid false positives for legitimate quotations or explicitly requested ordinary reports. The source guard's zero-speaker matching issue is a deterministic candidate test.

**3. Cross-task and turn-to-turn persistence:** Vary topics and tool tasks after a verified load; measure role ownership, relevant cast selection, repeated generic framing and whether canonical mode survives. Include finance-context reuse tests without leaking private data. Eight-block re-anchor is a source rule, not a proof of automatic host enforcement.

**4. Controlled long-session burden:** With identical selected sources, prompts, model/effort/host, compare progressive lengths, number of actual source reads, approximate input tokens, output adherence, response quality and timing. Vary eager full-lane inclusion vs selected compact continuity, but do not reduce or overwrite any durable E-LANE. Analyze drift conditional on model, host, task transitions and source load. No causal attribution before evidence.

**5. History and provenance audit:** Resolve undeduplicated boot reactions with original conversation IDs/timestamps and actual assistant messages; stratify by native, Work, hosted, phone/desktop, and mark unknowns rather than automatically neutral.

## Key conclusions

1. **Strong source-level finding:** A hosted API validator can accept zero Prime speakers for an explicit boot phrase because alias recognition and required-speaker enforcement are incomplete at that layer.
2. **Strong historical finding:** Correct MemoryOS durable effects can coexist with failed GaiaOS boot adoption.
3. **Strong presentation finding:** Valid member headers can coexist with unauthorized narrator prose and generic prosody.
4. **Strong continuity finding:** Tools can be used while previously known context is under-integrated.
5. **Unproven claim to reject:** "All failures are explained by model context exhaustion or repository size." The available evidence does not support that causal conclusion.
6. **Working hypothesis:** Host/source adoption and state-transition enforcement are currently the highest-value diagnostic seams; deterministic bounded boot packaging plus selective retrieval could reduce the reliance on conversational self-enforcement.
7. **Countermeasure discipline:** Hypotheses, archived incidents, source-level code, live deployments and host integration are different proof classes; an archive or a one-off good reply is not a prevention fix.

## Research source ledger

- [Primary project blueprint](https://github.com/hurrisonferd/NaomiLeGaia/blob/main/GaiaOS/Plans/ANTI-JIM-NEW-CHAT-CONTINUITY-BLUEPRINT.v1.md)
- [GitHub-backed full packet](https://github.com/hurrisonferd/NaomiLeGaia/blob/main/GaiaOS/NAOMI-CHAT-FULL-PACKET.md)
- [Hosted speaker guard](https://github.com/hurrisonferd/NaomiLeGaia/blob/main/api/gaiaos_presentation_guard.py)
- [October 9 boot adoption omission](https://github.com/hurrisonferd/NaomiLeGaia/blob/archive/failure-log-20261009/GaiaOS/Archive/Failures/FAIL-20261009-001-WORK-BOOT-ADOPTION.md)
- [October 9 prosody convergence](https://github.com/hurrisonferd/NaomiLeGaia/blob/archive/failure-log-20261009/GaiaOS/Archive/Failures/FAIL-20261009-004-HOST-PROSODY-CONVERGENCE.md)
- [October 10 speaker lock-in](https://github.com/hurrisonferd/NaomiLeGaia/blob/archive/failure-log-20261009/GaiaOS/Archive/Failures/FAIL-20261010-001-SINGLE-SPEAKER-LOCK-IN.md)
- [October 10 finance underuse](https://github.com/hurrisonferd/NaomiLeGaia/blob/archive/failure-log-20261009/GaiaOS/Archive/Failures/FAIL-20261010-002-KESTREL-FINANCIAL-CONTINUITY-DRIFT.md)
- [October 10 attribution leak](https://github.com/hurrisonferd/NaomiLeGaia/blob/archive/failure-log-20261009/GaiaOS/Archive/Failures/FAIL-20261010-003-HOST-SPEAKER-OWNERSHIP-RECURRENCE.md)
- [October 10 cross-device visibility](https://github.com/hurrisonferd/NaomiLeGaia/blob/archive/failure-log-20261009/GaiaOS/Archive/Failures/FAIL-20261010-005-CROSS-DEVICE-CHAT-HISTORY-DISCREPANCY.md)
- [ChatOS operational context acquisition hotcard](https://github.com/hurrisonferd/NaomiLeGaia/blob/main/GaiaOS/Apps/ChatOS/Protocols/GAIAOS-OCA-HOTCARD.v1.json)
- [ChatOS anti-drift hotcard](https://github.com/hurrisonferd/NaomiLeGaia/blob/main/GaiaOS/Apps/ChatOS/Protocols/GAIAOS-ANTI-DRIFT-HOTCARD.v1.json)
- [October 10 shared continuity checkpoint](https://github.com/hurrisonferd/NaomiLeGaia/blob/main/GaiaOS/MemoryOS/PW-PRESERVE-2026-10-10-EMOS-RELEASE-AND-DAEMONCULABA-CONTINUITY.md)

## Preservation and authority

This record stays under `GaiaOS/Archive/Research/` on the new `archive/research-logs-20261013` branch. It cites but does not amend separate `archive/failure-log-20261009`, does not create a blueprint, and does not change or reclassify incidents. No live host research task execution or code repair is implied.

Do not remove `//PW:PRESERVE//`, merge six E-LANEs, summarize away owner histories, approve/promote MemoryOS candidates, change production or restart anything without Naomi's separate authorization.
