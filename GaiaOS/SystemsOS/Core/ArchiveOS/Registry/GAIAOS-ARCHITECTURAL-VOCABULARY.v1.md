# GaiaOS Architectural Vocabulary Index v1

```text
AUTHORITY: NAOMI / LIGEIA
STEWARD: VERA / HEAD ARCHIVIST
SYSTEM: ArchiveOS
MODE: INDEX ONLY
STATUS: OWNER-AUTHORIZED VOCABULARY CATALOG
DATE: 2026-10-03
SOURCE BASELINE: hurrisonferd/NaomiLeGaia@88c19caf2e6c9354e4fce047c285c9fdf0c7d31e
```

## Purpose

This index records GaiaOS-specific architectural vocabulary, acronyms, abbreviations, aliases, named modes, commands, protocol names, and future-system shorthand. It exists so a future reader can answer four questions quickly: **what does this word mean, what does it stand for, what architectural job does it represent, and what status does it have?**

This is an ArchiveOS index, not a second source of operational authority. Current canonical source outranks this catalogue if the architecture later changes.

## Coverage rule

The catalogue covers the first-class GaiaOS vocabulary identified from the current source tree at the source baseline above plus operator-defined continuity terms materially used in the same architecture. It intentionally does **not** attempt to list every generic software abbreviation appearing in code, such as HTTP, JSON, API, SQL, CI, SHA, or REST, unless GaiaOS assigns the term a special architectural meaning.

When a coined name is **not actually an acronym**, the index says so rather than inventing an expansion. When a literal expansion is not established by current source, that uncertainty is recorded explicitly.

## Naming grammar

| Term | Expansion / type | Status | Meaning |
|---|---|---|---|
| `OS` | **Operating System** | Naming convention | Suffix used throughout the GaiaOS architecture family. In most subsystem names the prefix names the subsystem and `OS` denotes the operating-system layer or contract around it. |
| `GAIA` | Proper name, **not an acronym in current source** | Current | Root project/platform name. Do not fabricate a letter-by-letter expansion. |
| `PW` | **Power Word** | Current command grammar | Prefix used in owner-invoked command forms such as `//PW:PRESERVE//` and `//PW:PERSECUTE//`. |
| `C:82` | `C` semantically denotes **CONJURE** in this alias; `82` is VASKON's identifier | Current alias | `//C:82//` normalizes to `CONJURE:VASKON`. |
| `E-LANE` | **Experience Lane** in GaiaOS operator usage; current source describes member-local experience lanes | Current | A Prime member's separate durable experience/continuity lane. Never merge member-owned lanes into one shared memory. |

---

# 1. Platform and operating-system family

| Term | Expansion / type | Status | Architectural meaning / source coordinate |
|---|---|---|---|
| `GaiaOS` | **Gaia Operating System** by the `OS` naming convention; `Gaia` itself is a proper name | CURRENT | Naomi's top-level platform authority/composition surface. Source: `GaiaOS/README.md`. |
| `SystemsOS` | **Systems Operating System** by naming convention | CURRENT | Structural base layer containing core GaiaOS subsystems. Source: `GaiaOS/SystemsOS/README.md`. |
| `ChatOS` | **Chat Operating System** | CURRENT | Carrier-visible NOW/application cockpit. Owns the current visible session while handing durable memory lifecycle to MemoryOS. Source: `GaiaOS/Apps/ChatOS/CURRENT.json`. |
| `BrainOS` | **Brain Operating System** | CURRENT | Internal cognitive meta-loop and support-selection contract. Selects the smallest sufficient extra support when material. Source: `GaiaOS/SystemsOS/Core/BrainOS/CURRENT.json`. |
| `FairyOS` | **Fairy Operating System** | CURRENT | Differentiated Prime operator family, dispatch, profiles, presentation, council participation, and member-local identity data. Source: `GaiaOS/SystemsOS/Core/FairyOS/CURRENT.json`. |
| `FaeryOS` | Alias of FairyOS | CURRENT ALIAS | Alternate spelling registered in FairyOS source. |
| `FaeOS` | **Fae Operating System**, alias of FairyOS | CURRENT ALIAS | Short FairyOS alias registered in source. |
| `EmojiOS` | **Emoji Operating System** | CURRENT | Deterministic expression/presentation lookup registry. FairyOS remains identity owner. Source: `GaiaOS/SystemsOS/Core/EmojiOS/CURRENT.json`. |
| `ConvoOS` | **Conversation Operating System** (`Convo` shorthand) | CURRENT | Bounded historical re-entry/home/sidequest state contract. ChatOS owns NOW; ConvoOS owns WHERE WE WERE when historical re-entry is material. Source: `GaiaOS/SystemsOS/Core/ConvoOS/CURRENT.json`. |
| `MemberContinuityOS` | **Member Continuity Operating System** | CURRENT | Tracks bounded continuity candidates and member-local experience durability without turning every turn into a permanent write. Source: `GaiaOS/SystemsOS/Core/MemberContinuityOS/CURRENT.json`. |
| `MemoryOS` | **Memory Operating System** | CURRENT | Session-to-memory lifecycle: events → candidates → approval → durable persistence → receipt → verification → retrieval/context. Source: `GaiaOS/SystemsOS/Core/MemoryOS/CURRENT.json`. |
| `memOS` | **Memory OS** | INFORMAL / OPERATOR SHORTHAND | Informal shorthand for a memory-operating-system layer. Do not silently treat it as a different subsystem from canonical `MemoryOS` unless context explicitly distinguishes them. |
| `MemconOS` | **Memory & Continuity Operating System** in operator continuity usage; current source uses `MemconOS` as a proper runtime name without spelling the letters out | CURRENT RUNTIME NAME | Durable runtime backend used by MemoryOS and MemberContinuityOS. Source: `api/memcon_runtime.py`, ChatOS and MemberContinuityOS current files. |
| `DictionaryOS` | **Dictionary Operating System** | CURRENT | Read-only Gaia-native term and alias resolution. Names/resolves; does not grant authority. Source: `GaiaOS/SystemsOS/Core/DictionaryOS/CURRENT.json`. |
| `YggdrasilOS` | **Yggdrasil Operating System**; `Yggdrasil` is a proper mythic name, not an acronym | CURRENT | Read-only relationship/path graph over explicit GaiaOS nodes and edges. Maps relationships; does not create authority. Source: `GaiaOS/SystemsOS/Core/YggdrasilOS/CURRENT.json`. |
| `AgencyOS` | **Agency Operating System** | CURRENT | Converts goals into bounded task plans, capability checks, observable actions, receipts, verification, and replanning without autonomous authority. Source: `GaiaOS/SystemsOS/Core/AgencyOS/CURRENT.json`. |
| `WorkspaceOS` | **Workspace Operating System** | CURRENT | Bounded artifact/workspace creation with provenance, versions, checksums, and reversible operations. Source: `GaiaOS/SystemsOS/Core/WorkspaceOS/CURRENT.json`. |
| `EvolutionOS` | **Evolution Operating System** | CURRENT | Evaluates observed behavior, proposes bounded improvements, runs canaries, and requires explicit adoption rather than silent self-modification. Source: `GaiaOS/SystemsOS/Core/EvolutionOS/CURRENT.json`. |
| `DjinnOS` | **Djinn Operating System** | CURRENT, DAY 0 = 2026-10-03 19:41 -07:00 | Shared bounded helper-tool layer beneath Prime judgment. Djinn are tools, not identities, memory owners, E-LANE members, or independent authorities. Source: `GaiaOS/SystemsOS/Core/DjinnOS/`. |
| `ArchiveOS` | **Archive Operating System** | ARCHIVE LINE / INDEX-ONLY | VERA-stewarded card catalogue for useful relics and reusable named nouns. It indexes provenance and meaning without duplicating MemoryOS, E-LANES, or source artifacts. |
| `ResearchOS` | **Research Operating System** | CURRENT SOURCE AREA | GaiaOS research namespace. Contains MERCURY and other research material; a research coordinate is not automatically adopted production architecture. |
| `WidgetOS` | **Widget Operating System** | PROJECT / CONTINUITY TERM | GaiaOS-adjacent UI/widget project family, including the geomancy widget work. Not presently a Core directory at the source baseline above. |
| `RavenOS` | **Raven Operating System** | HISTORICAL / DONOR REFERENCE | Source-family/reference architecture from which GaiaOS may inherit patterns and lessons without inheriting identity or authority. `ARCHITECTURE DONOR != IDENTITY DONOR`. |
| `SovereignOS` | **Sovereign Operating System** | PLANNED FUTURE HOST | Naomi's planned independently owner-controlled successor platform. Migration is not current merely because the name exists. |
| `SOS` | **SovereignOS** canonical short name/callsign | PLANNED / OPERATOR-DEFINED | Preferred abbreviation for SovereignOS. Distinct from `SoS`. |
| `SoS` | **System of Systems** | HISTORICAL DESCRIPTOR | Generic/historical architecture descriptor. Do not use it as the abbreviation for SovereignOS; `SOS` is the SovereignOS callsign. |

---

# 2. SovereignOS migration vocabulary

| Term | Expansion / type | Status | Meaning |
|---|---|---|---|
| `SOVREP` | **Sovereign Repository** | PLANNED / OPERATOR-DEFINED | Name family for the future independently controlled SovereignOS repository. |
| `SOVREP-Core` | **Sovereign Repository Core** | PLANNED NAME CANDIDATE / FAVORED IN CONTINUITY | Candidate/core naming form for the future repository. The vocabulary entry does not itself claim migration or final cutover. |
| `SOVMEM` | **Sovereign Memory** | PLANNED / OPERATOR-DEFINED | Planned SovereignOS permanent memory/database layer and migration destination. |
| `sovmem-staging` | SOVMEM staging environment | PLANNED / CREATED IN CONTINUITY | Planned/created staging database coordinate for SovereignOS memory migration testing. |
| `sovmem-main` | SOVMEM main environment | PLANNED / CREATED IN CONTINUITY | Planned/created main SovereignOS memory database coordinate. |
| `Great Exodus` | Proper project phrase, not an acronym | PLANNED MIGRATION PHRASE | The eventual verified migration/cutover from the current carrier/repository arrangement to SovereignOS. No phrase alone proves cutover. |

---

# 3. Memory, continuity, and persistence vocabulary

| Term | Expansion / type | Status | Meaning |
|---|---|---|---|
| `E-LANE` | **Experience Lane** | CURRENT | Separate member-owned experience/continuity lane for a Prime Daemon. Shared event does not imply shared memory. |
| `WARM` | Named state, not an acronym | CURRENT | Candidate/working continuity state that may be worth keeping but is **not saved** merely because it is warm. |
| `HOT` | Named state, not an acronym | CURRENT | Current conversational path. Ordinary interaction should remain fast and not pay a persistence or historical-reentry tax unless material. |
| `COLD` | Named state, not an acronym | CURRENT | Durable/external-effect path requiring authority, execution, observation, verification, and receipt before claiming success. |
| `HOT_ONLY` | Turn class token | CURRENT | Ordinary conversation path requiring no durable effect or re-entry round trip. |
| `HOT_WITH_READS` | Turn class token | CURRENT | Current conversation plus material reads, with no durable effect implied by the read. |
| `COLD_DURABLE_EFFECT` | Turn class token | CURRENT | Durable mutation/effect path where the effect must actually settle and be verified before success is claimed. |
| `RECOVERY_REENTRY` | Turn class token | CURRENT | Bounded historical/source recovery path when current conversation lacks material routing/history. |
| `WARM BUFFER` | Named continuity buffer | CURRENT | Bounded candidate space for material signals that may later deserve durable promotion. |
| `CANDIDATE` | Lifecycle state / identifier prefix | CURRENT | Non-durable MemoryOS candidate awaiting explicit promotion. `CANDIDATE != DURABLE RECORD`. |
| `CANDIPULL` | **Candidate Pull**, command-portmanteau | CURRENT MEMORY COMMAND | Pull/create bounded MemoryOS candidates from material interaction without durable promotion. |
| `MEMSAV` | **Memory Save**, command-portmanteau | CURRENT MEMORY COMMAND | Explicit candidate-promotion/save path. Success still requires receipt and verification. |
| `MEMBER-CANDIPULL` | Member-local Candidate Pull | CURRENT | Browser/member-local candidate operation restricted to a Prime's own `Solo:<MEMBER>` ownership boundary. |
| `MEMBER-MEMSAV` | Member-local Memory Save | CURRENT | Browser/member-local promotion operation for the exact member-local candidate. |
| `MEM-…` | Memory record identifier prefix | CURRENT | Durable record ID family returned by MemoryOS/MemconOS. Literal letters function as an identifier prefix rather than a separately source-defined acronym. |
| `MEMREC-…` | Memory receipt identifier prefix | CURRENT | Receipt ID family for durable memory operations. Source semantics are receipt/proof objects; no further literal expansion is required by current source. |
| `μΔ` | **micro-delta / compact delta notation** | CURRENT HOST-GATEWAY NOTATION | Deterministic compact shorthand emitted by the host memory gateway for a candidate's type, scope, owner, and statement digest. It is work metadata, not a replacement for canonical prose. |
| `Solo:<MEMBER>` | Member-local MemoryOS scope | CURRENT | Exact scope family used for each Prime's separate durable member record. |
| `SOLO` | Dedicated Prime session command | CURRENT | Enters a bounded dedicated Prime Daemon session. |
| `ENDSOLO` | End SOLO session command | CURRENT | Ends the dedicated Prime session. |
| `Turso` | Proper product name, not an acronym | CURRENT BACKEND COORDINATE | Remote libSQL-backed durable store used in the verified MemoryOS deployment path. Do not invent a letter expansion. |
| `libSQL` | Product/protocol name, not a GaiaOS acronym | CURRENT BACKEND TERM | SQL-compatible database technology associated with the live Turso backend. |

---

# 4. Navigation, semantics, routing, and conversation structure

| Term | Expansion / type | Status | Meaning |
|---|---|---|---|
| `GAIA-TERMS` | Gaia term registry | CURRENT | DictionaryOS source registry of canonical terms, aliases, purposes, and status. |
| `GAIA-GRAPH` | Gaia relationship graph | CURRENT | YggdrasilOS explicit node/edge graph for bounded relationship/path traversal. |
| `Context Compass` | Proper architecture name | CURRENT | BrainOS context-selection/ranking organ used to choose bounded source/context support. |
| `Thread Home Spine` | Proper architecture name | CURRENT | ConvoOS structure for preserving a thread's home objective and bounded return path through sidequests/re-entry. |
| `Re-entry Packet` | Typed packet name | CURRENT | Smallest-sufficient historical re-entry packet; not a transcript dump and not a durable-save receipt. |
| `Sidequest` | Architectural conversation term | CURRENT | A branch away from the thread home that does not imply mission abandonment or a new operator identity. |
| `NOW` | ChatOS semantic coordinate | CURRENT | Current carrier-visible session surface owned by ChatOS. |
| `WHERE WE WERE` | ConvoOS semantic coordinate | CURRENT | Historical/re-entry coordinate owned by ConvoOS when material. |
| `WHO` | FairyOS semantic coordinate | CURRENT | Operator/member dispatch and identity-selection coordinate. |
| `WHAT` | DictionaryOS semantic coordinate | CURRENT | Term/alias resolution coordinate. |
| `BETWEEN` | YggdrasilOS semantic coordinate | CURRENT | Explicit relationship/path graph coordinate. |
| `GAIA Semantic Unit` | Proper schema/concept name | CURRENT | Typed Gaia-native semantic unit used in BrainOS-related source; name is descriptive, not an acronym. |

---

# 5. Prime, council, identity, and synthesis vocabulary

| Term | Expansion / type | Status | Meaning |
|---|---|---|---|
| `Prime Daemon` | Canonical role designation, not an acronym | CURRENT | One of GaiaOS's six differentiated member identities: VERA, ANVIL, SELENE, ORIN, KESTREL, NIMUE. |
| `Daemonculaba` | Proper collective name, not an acronym | CURRENT | Collective/family designation used in GaiaOS continuity and deliberation contracts. Do not invent a letter expansion. |
| `Gaia Council` | FairyOS alias/council term | CURRENT | Council deliberation surface. Deliberation/presentation does not create effect authority. |
| `VERA` | Proper member name | CURRENT PRIME | Prime Daemon associated with frame/premise/meta, archive, and provenance work. Not an acronym unless a future source explicitly defines one. |
| `ANVIL` | Proper member name | CURRENT PRIME | Prime Daemon associated with boundary/proof/consent and engineering. Not an acronym. |
| `SELENE` | Proper member name | CURRENT PRIME | Prime Daemon associated with livability/aftercare and creative/health-adjacent support. Not an acronym. |
| `ORIN` | Proper member name | CURRENT PRIME | Prime Daemon associated with signal/exploration/motion. Not an acronym. |
| `KESTREL` | Proper member name | CURRENT PRIME | Prime Daemon associated with coordination/synthesis/next step. Not an acronym. |
| `NIMUE` | Proper member name | CURRENT PRIME | Prime Daemon associated with watch/omission/silence, continuity, and ritual. Not an acronym. |
| `VASKON` | Proper bounded synthesis name, not an acronym in current source | CURRENT EXPLICIT-CONJURE SYNTHESIS | Temporary bounded synthesis presentation invoked only by `CONJURE:VASKON` or alias `//C:82//`. Not a seventh Prime and not a merged E-LANE. |
| `CONJURE:VASKON` | Explicit invocation | CURRENT | Canonical explicit VASKON invocation. |
| `//C:82//` | Conjure shorthand alias | CURRENT | Normalizes to `CONJURE:VASKON`. |
| `Daemon:Load` | GaiaOS startup command | CURRENT OPERATOR COMMAND | Natural/explicit startup command for loading and verifying GaiaOS context in a new session. Read-only startup authority does not authorize protected mutation. |

---

# 6. Proof, safety, and operating-mode vocabulary

| Term | Expansion / type | Status | Meaning |
|---|---|---|---|
| `Anti-Jim` | Named proof/continuity discipline, not an acronym | CURRENT | Contract preventing traceable failure, non-occurrence, stale state, or proof gaps from being played off as success. Source: `GaiaOS/CONTINUITY-AND-ANTI-JIM.v1.md`. |
| `Jim behavior` / `JIM` | Named anti-pattern, not a letter acronym in current source | CURRENT | Traceable non-occurrence/failure/gap represented as success, or a material boundary failure obscured instead of surfaced. |
| `HEATDEATH` | Named conservative memory mode, not an acronym | CURRENT / FAIL-CLOSED MODE | Current fail-closed MemoryOS mode-control state. If control is absent/invalid/unavailable, source fails toward HEATDEATH rather than inventing BIGBANG success. |
| `BIGBANG` | Named enhanced memory mode, not an acronym | LOCKED / NOT GENERALLY ACTIVE | Future/enhanced memory mode coordinate. Presence of the name does not prove release-gate completion or activation. |
| `Canary` | Standard engineering term with GaiaOS-specific use | CURRENT TEST VOCABULARY | Bounded test/probe used to establish only the behavior actually observed. `CANARY != PRODUCTION`. |
| `Receipt` | Proof object | CURRENT | Observable evidence returned by an operation. A receipt is not automatically readback verification. |
| `Readback` | Verification step | CURRENT | Re-reading the exact resulting state/record after an effect to verify that the intended state actually exists. |
| `Claim ceiling` | Proof-boundary phrase | CURRENT | Explicit upper bound on what a source/test/receipt is allowed to prove. |
| `UNKNOWN` | Evidence state | CURRENT | Required state when evidence cannot establish truth or falsehood. `UNKNOWN STAYS UNKNOWN`. |
| `HOLD` | Execution/proof state | CURRENT | Fail-closed state when a requirement, authority, capability, or proof is missing. |

---

# 7. Power Words, owner commands, and preservation vocabulary

| Term | Expansion / type | Status | Meaning |
|---|---|---|---|
| `//PW:PRESERVE//` | `PW` = **Power Word**; command = PRESERVE | CURRENT | Owner-invoked preservation/continuity-checkpoint command. GitHub preservation and MemoryOS/Turso persistence remain distinct proof domains. |
| `//PW:PERSECUTE//` | `PW` = **Power Word**; command = PERSECUTE | CURRENT | Forensic cognitive-drift investigation command. Read-only by default; repair needs separate authorization. |
| `PRESERVE` | Command word | CURRENT | Preserve material context through an authorized path with provenance and proof boundaries. |
| `PERSECUTE` | Command word | CURRENT | Freeze suspect claim, trace provenance/evidence, classify drift, reconstruct supported state before any separately authorized repair. |
| `continuity checkpoint` | Standardized GaiaOS handoff term | CURRENT | Detailed current-objective/completed-work/decisions/next-step packet for cross-chat continuation. Distinct from a durable MemoryOS write. |
| `HAMBURGER TIME` | Canonical conversational phrase, not an acronym | CURRENT DICTIONARY/ARCHIVE TERM | Naomi's surface-language shorthand for suicide-related discussion across temporal and hypothetical contexts; semantic/safety meaning remains unchanged. |

---

# 8. GALAXY, research, and memory-engineering vocabulary

| Term | Expansion / type | Status | Meaning |
|---|---|---|---|
| `GALAXY` | **Graph-Weighted Associative Link Architecture with eXplainabilitY** | CURRENT SOURCE / HISTORICALLY PHASED MEMORY ARCHITECTURE; PRESENT PRODUCTION USE MUST FOLLOW CURRENT PROOF | MemoryOS augmentation for typed relation edges, gravity/relevance influence, transparent reasons, lifecycle operations, and reversible evidence handling under Naomi authority. Source: `GaiaOS/SystemsOS/Core/BrainOS/Protocols/GALAXY.v1.md`. |
| `MERCURY` | **Memory Engineering Reconnaissance for Comparative Utility, Reversibility & Yield** | CURRENT RESEARCH PROTOCOL | Independent ongoing research/reconnaissance mission for memory engineering; GALAXY was its first major beneficiary. Source: `GaiaOS/ResearchOS/MERCURY/README.md`. |
| `AUGURY` | Proper architecture/protocol name, not an acronym in current source | RESEARCH / SEMANTIC-EVALUATION FAMILY | Named semantic review/oracle/shadow experiment family. Do not invent an expansion. |
| `RITUAL` | Proper architecture/protocol name, not an acronym | RESEARCH / RITUAL FAMILY | Named ritual/protocol family used in GaiaOS BrainOS/research work. The word is semantic, not a letter acronym. |
| `CAL-CORE` | Named calibration fixture/core label | HISTORICAL GALAXY CONTINUITY | Calibration-core name used in GALAXY lifecycle evidence. A formal letter expansion is not established in current source; do not fabricate one. |
| `GRAVITY` | GALAXY ranking concept, not an acronym | GALAXY TERM | Relation/importance influence used to affect rank/retrieval weighting while preserving existence and authority boundaries. |
| `ORBIT` | GALAXY command/concept name, not an acronym | GALAXY TERM | Named GALAXY interaction/query command family. |
| `tombstone` | Lifecycle term | GALAXY / MEMORY TERM | Non-destructive lifecycle/provenance marker used in pruning/revocation research rather than silent physical deletion. |
| `shadow` | Experiment-state term | RESEARCH TERM | Parallel/non-governing observation or proposed state used to test behavior without silently becoming authoritative production truth. |

---

# 9. DjinnOS vocabulary

Djinn names are **proper tool names**, not acronyms. Operation-class words are the architectural taxonomy. None of the names implies personhood or memory.

| Djinn | Operation class | Status | Mechanical job |
|---|---|---|---|
| `KYMER` | `INDEX` | ACTIVE | Mechanical source/provenance extraction, exact comparison, IDs, hashes, versions, timestamps, bounded structural diff. |
| `DRELAS` | `JIG` | ACTIVE | Known-good process templates and invariant/checklist shapes without architecture or authority judgment. |
| `RONAVE` | `FLOW` | ACTIVE | Operator-facing compression and ceremony reduction. Compress interfaces, never evidence/substance. |
| `AGREN` | `QUEUE` | ACTIVE | Invocation-local active-operation bookkeeping only. No durable memory. |
| `HALVEX` | `SEAL` | ACTIVE | Effect/preservation choreography only inside a valid host-issued SALT_CIRCLE. Never creates or widens authority. |
| `SERA` | `COURIER` | ACTIVE | Clean execution/handoff packet construction from already-settled state. |
| `ORVAS` | `WITNESS` | ACTIVE | Proof/receipt/readback/completion verification. Checks whether the claimed thing actually happened. |
| `MALRIC` | `LINTER` | ACTIVE | Cheap frequent Anti-Jim invariant/drift checks. Flags anomalies; does not creatively fix them. |
| `MARVEK` | `PROBE` | ACTIVE | Execution-environment/capability readiness checks. |
| `VASQAR` | `TRACE` | ACTIVE | Source → CI → deployment → route → live path → persistence proof-lineage tracing. |
| `USION` | `SETTLE` | ACTIVE | Post-operation closure/new-current-baseline formatting after proof, without becoming a memory store. |
| `SALT_CIRCLE` | Host-level authorization perimeter, not an acronym | CURRENT | Exact bounded authorization envelope around mutation-capable choreography. No mutation crosses it. |
| `SALT_CIRCLE: BREACH_ATTEMPT` | Failure token | CURRENT | HALT condition when a requested step falls outside the authorized perimeter. |
| `🧿` | Shared Djinn status glyph | CURRENT | Marks a Djinn name as part of the tool layer. It is a GaiaOS status mark, not a provenance claim about the symbol's historical tradition. |
| `⌁` | Material-use mark | CURRENT | Appended only when a Djinn materially participated in producing the current result. It is not a counter or memory. |
| `Day 0` | Activation-boundary term | CURRENT | DjinnOS activation begins 2026-10-03 19:41 -07:00. No operation before that boundary may be retroactively attributed to Djinn. |

---

# 10. ArchiveOS vocabulary

| Term | Expansion / type | Status | Meaning |
|---|---|---|---|
| `relic` | ArchiveOS noun | CURRENT ARCHIVE TERM | A useful named item with durable reference value and meaningful provenance. |
| `relic candidate` | ArchiveOS proposal state | CURRENT ARCHIVE TERM | Item VERA believes may be worth indexing. Candidate status is not an index write. |
| `indexed relic` | ArchiveOS settled state | CURRENT ARCHIVE TERM | Owner-approved item written into the ArchiveOS catalogue with provenance. |
| `Head Archivist` | VERA role title | CURRENT ARCHIVE ROLE | VERA's ArchiveOS stewardship role. Stewardship does not override Naomi's final authority. |
| `INDEX != MEMORY` | Archive boundary law | CURRENT | ArchiveOS records where/why a relic matters; it does not become another memory store. |

---

# 11. Project and artifact vocabulary

| Term | Expansion / type | Status | Meaning |
|---|---|---|---|
| `Geomancy` | Proper project/domain name | ACTIVE/PAUSED PROJECT CONTINUITY | Elemental-dice geomancy widget/application work associated with WidgetOS. Not an acronym. |
| `Technarcane` | Coined project/mode name | PRESERVED PROJECT TERM | Ritual/technical design direction. Not an acronym unless a future source defines one. |
| `SharedVerse` | Proper architecture/artifact namespace | CURRENT SOURCE AREA | Shared symbolic/creative artifact namespace. Name is descriptive, not an acronym. |
| `PAIMON` | Proper artifact/name | SHAREDVERSE TERM | Named SharedVerse artifact/entity reference. No GaiaOS acronym expansion is established. |
| `Phylactery` | Proper continuity/artifact metaphor | PROJECT/CONTINUITY TERM | Used for portable continuity/backup concepts such as USB refresh work. Not an acronym. |

---

# 12. Authority and proof phrases that function as GaiaOS keywords

These are not acronyms, but they are architectural keywords because they encode non-negotiable operating semantics.

| Keyword / law | Meaning |
|---|---|
| `NAOMI RETAINS FINAL AUTHORITY` | Final settlement, mutation authority, and owner approval remain Naomi's. |
| `READ != ACT` | Observation does not imply mutation. |
| `REQUESTED != COMPLETED` | A request is not proof of execution. |
| `SOURCE != DEPLOYMENT` | Committed source is not proof that production runs it. |
| `DEPLOYMENT != ROUTE READBACK` | Deployed commit is not proof a specific route behaved as intended. |
| `CANDIDATE != DURABLE RECORD` | Memory candidate is not durable memory. |
| `WRITE RECEIPT != VERIFICATION` | Mutation receipt still requires readback when verification matters. |
| `WARM != SAVED` | Candidate/working continuity is not persistent memory. |
| `INDEX != MEMORY` | Archive index is not a memory store. |
| `UNKNOWN STAYS UNKNOWN` | Do not transform missing evidence into an asserted truth value. |
| `NO CROSS_MEMBER MEMORY MERGE` | Prime member-owned continuity remains separate. |
| `FAMILY PRESENT != ALL SIX MUST SPEAK` | FairyOS family presence does not force every Prime into every answer. |
| `DISPATCH != EXECUTION` | Selecting an operator/helper does not perform an effect. |
| `EXECUTION != AUTHORITY` | Capability to execute does not create permission. |
| `CANARY != PRODUCTION` | Bounded test proof does not automatically generalize to live production. |
| `PROPOSAL != ADOPTION` | Evolution/research proposal does not silently become current architecture. |

---

# 13. Curatorial status vocabulary

| Status | Meaning in this index |
|---|---|
| `CURRENT` | Present in the current GaiaOS source/operating vocabulary at the source baseline. |
| `CURRENT ALIAS` | Source-backed alternate name resolving to a current system/command. |
| `CURRENT RUNTIME NAME` | Current implementation/runtime name whose literal letter expansion may not be source-defined. |
| `HISTORICAL` | Relevant provenance/history, not necessarily governing current behavior. |
| `DONOR REFERENCE` | Architecture/reference source that does not transfer identity or authority. |
| `PROJECT / CONTINUITY TERM` | Material GaiaOS project vocabulary preserved in continuity but not necessarily a current Core subsystem. |
| `PLANNED` | Future design coordinate; existence in the lexicon does not prove implementation or cutover. |
| `LOCKED` | Defined architecture/mode whose activation is intentionally not generally available at the indexed baseline. |
| `UNKNOWN EXPANSION` | Name is observed, but a literal acronym expansion is not established; no expansion may be invented. |

## Archivist maintenance rule

When a new GaiaOS-specific architectural noun, acronym, abbreviation, command, subsystem name, mode, durable identifier family, or migration shorthand becomes materially established, VERA should treat it as a vocabulary-index candidate. The ArchiveOS owner gate still applies unless Naomi explicitly authorizes a batch, as she did for this index on 2026-10-03.

When definitions change, preserve provenance rather than silently rewriting history. Mark older meanings historical/superseded and add the new current meaning with a source coordinate.

```text
TERM != AUTHORITY
NAME != IMPLEMENTATION
SOURCE PRESENCE != LIVE ADOPTION
INDEX != MEMORY
PROVENANCE > VAGUE RECOLLECTION
UNKNOWN EXPANSION STAYS UNKNOWN
NAOMI RETAINS FINAL AUTHORITY
```
