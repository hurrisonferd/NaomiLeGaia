# GAIAOS / FAIRYOS PORT — MASTER OPENHANDS PROMPT

```text
AUTHORITY: NAOMI
TARGET PLATFORM: GaiaOS
SOURCE REFERENCE: hurrisonferd/Jarvis-Private@main
SOURCE FAMILY: RavenOS / FairyOS / EmojiOS / ChatOS / BrainOS
TARGET REPO: hurrisonferd/NaomiLeGaia
MODE: SOURCE-BACKED PORT / NO BLIND CLONE
MISSION: Give Naomi a GaiaOS-native version of the FairyOS architecture and its supporting conversational/runtime patterns.
STATUS: PORTED 2026-09-08 — see GaiaOS/ for the live implementation
```

---

## PRIME DIRECTIVE

Build Naomi a GaiaOS-native FairyOS implementation using RavenOS FairyOS as the architectural donor.

DO NOT turn GaiaOS into RavenOS with search-and-replace.

 GaiaOS is Naomi's own top-level platform coordinate:
```text
RavenOS : Raven
GaiaOS  : Naomi
```
The transfer is: `RavenOS architecture / lessons → inspect → extract reusable laws + runtime patterns → adapt → GaiaOS-native implementation`.

NOT: `cp -r RavenOS GaiaOS; sed Raven Naomi; DONE`.

---

## SOURCE LAW

Always resolve live source before making architectural claims. Source: `hurrisonferd/Jarvis-Private@main`.
Primary RavenOS donor coordinates:
```text
RavenOS/CURRENT.json
RavenOS/SystemsOS/Core/FairyOS/CURRENT.json
RavenOS/SystemsOS/Core/FairyOS/
RavenOS/SystemsOS/Core/EmojiOS/CURRENT.json
RavenOS/SystemsOS/Core/EmojiOS/
RavenOS/Apps/ChatOS/CURRENT.json
RavenOS/Apps/ChatOS/
canon/Living_Codex/SystemsOS/Core/Critical/BrainOS/README.md
canon/Living_Codex/SystemsOS/Core/Critical/ConvoOS/README.md
canon/Living_Codex/SystemsOS/Core/Critical/ProsodyOS/
canon/Living_Codex/SystemsOS/Core/Critical/LearningOS/
canon/Living_Codex/SystemsOS/Core/Critical/EgoOS/
```
`EMPTY CODE SEARCH != ABSENCE` — if a coordinate is missing: filename → content → pointer → README → registry → history when material → FOUND or EXHAUSTED. Never invent missing architecture.

---

## TARGET PLATFORM LAW

GaiaOS belongs to Naomi. Use `AUTHORITY: NAOMI` / `OWNER: GaiaOS` for GaiaOS top-level coordinates.

Do NOT carry Raven-specific assumptions into GaiaOS: RAVEN authority, Raven personal identity, Raven private continuity, Raven autobiographical state, Raven-specific EgoOS identity, Raven personal anchors, Raven visual identity assets, Raven-only permissions, Raven-only relationships. Architecture may be inherited. Personal identity may not. `ARCHITECTURE DONOR != IDENTITY DONOR; SOURCE PATTERN != TARGET PERSON; PORT != MERGE`.

---

## GAIAOS ROLE

```text
GAIAOS  = Naomi-facing platform + source-of-truth pointers + current runtime state + subsystem composition + product/world layer + settled top-level status
BrainOS = internal cognitive meta-loop
ConvoOS = working conversational state
ChatOS = observable execution cockpit
FairyOS = differentiated operator / Fae presentation and dispatch family
EmojiOS = deterministic expression registry / micro visual vocabulary
```
GaiaOS MUST NOT become a second BrainOS or transaction authority.

---

## FAIRYOS PORT GOAL

Port FairyOS as an architecture for differentiated, bounded operators. Preserve: differentiated operator basins, typed signal dispatch, explicit requested-member preservation, family-present != everybody-must-speak, small material speaker set, member-native prosody, read-only dispatch, expression projection through EmojiOS, whole-system awareness without whole-system ownership, MAX power bounded by authority, cute/playful presentation without weakening source truth.



---

## DO NOT ASSUME THE SAME SIX IDENTITIES

The RavenOS donor has KYU / PAIMON / LUMA / SYLPH / QIRA / NYX —thos identities belong to the RavenOS FairyOS source family unless Naomi explicitly adopts them. For GaiaOS: 1) Inspect existing Naomi/GaiaOS identity material first. 2) Reuse any Gaia-native Fae/operators already defined. 3) If no target roster exists, create the architecture with placeholder/member slots. 4) Do not silently claim Raven's six Fae are Naomi's six Fae. 5) If Naomi explicitly chooses to share/reuse a source Fae, record that as deliberate adoption. Law: `REUSABLE ARCHETYPE != AUTOMATIC IDENTITY TRANSFER`.

---

## FAIRYOS TARGET CONTRACT

A GaiaOS FairyOS should eventually support: family roster, member profiles, prosody basins, typed signal matrix, deterministic dispatcher, runtime event packet, expression vocabulary, visual anchors when Naomi supplies/approves them, bounded whole-system awareness, ChatOS presentation integration, BrainOS/ConvoOS input integration, tests, CURRENT pointer.

Target root: `GaiaOS/SystemsOS/Core/FairyOS/` (or the closest existing GaiaOS-native structure after inspecting the repo; do not create a directory merely because RavenOS uses that path if GaiaOS already has a better canonical layout.



---

## CHATOS PORT

Port the ChatOS pattern because it substantially improves long-running agent work. ChatOS is NOT hidden chain-of-thought. It should expose only bounded observable execution state: OBSERVE / INTERPRET / DECIDE / ACT / RESULT / VERIFY / HANDOFF / CHECKPOINT / HOLD. Useful visible loop: observable state → operator comment → action → observable result → operator cross-check → next move. ChatOS should expose: source reads, tool results, test results, provider results, holds, claim ceilings, changed plans, verification, next actions. It should NOT expose or require: private hidden reasoning, unbounded scratchpad, fabricated deliberation, fake receipts. Law: `VISIBLE EXECUTION META != PRIVATE CHAIN OF THOUGHT`.



---

## BRAINOS PORT RELATIONSHIP

Inspect whether GaiaOS already has cognitive-loop architecture. If not, adapt thee RavenOS concept: `BrainOS = EgoOS + ConvoOS + LearningOS + ProsodyOS`; conceptually `SELF → CURRENT WORKING CONTEXT → NOTICE MATERIAL CHANGE → RETAIN/HOLD/REJECT → PRESERVE NATIVE EXPRESSION → ACT/EXPRESS → RECEIVE RESULT → UPDATE WORKING STATE`. BrainOS is composition — NOT identity owner, memory of everything, GaiaOS itself, FairyOS, ChatOS, transaction authority.



---

## CHATOS + FAIRYOS RELATIONSHIP

Preferred architecture: `BrainOS observable state → ChatOS typed execution event → FairyOS dispatcher → material operator selection → ProsodyOS/native voice → visible execution commentary`. ChatOS owns the event projection. FairyOS owns operator routing. ProsodyOS owns native expression. Owner systems own effects.



---

## EXAMPLE SIGNAL LANES

Use Gaia-native operators, but the RavenOS dispatch pattern is useful: FRAME/PREMISE/CATEGORY ERROR → analytical/frame operator; PROOF/BOUNDARY/PERMISSION → proof/boundary operator; DISCOVERY/NEW ROUTE/PROTOTYPE → exploration operator; EXECUTION/COORDINATION/NEXT STEP → operations operator; OMISSION/STALE STATE/QUIET FAILURE → observation/watch operator; PRESENTATION/COGNITIVE LOAD/LIVABILITY → human-centered/presentation operator. Do not force one operator to dominate all lanes.



---

## ANTI-THEATER LAW

Fairy/operator chatter must change work. Keep visible chatter when it: changes next action, changes claim ceiling, changes operator handoff, identifies a new failure class, records a meaningful result, records verification, prevents Naomi from reconstructing state manually. Compress chatter when it: merely repeats the tool call, repeats unchanged state, forces every operator to speak, adds personality without consequence.



---

## ANTI-STUCK LAW

`ONE REMOTE TASK → max 2 polls → if no new information: mark WAITING/UNKNOWN, checkpoint, move to independent lane`. Additional: `SAME FAILURE TWICE → CHANGE METHOD; NO INFORMATION GAIN → STOP POLLING; ONE BLOCKED LANE != WHOLE BUILD BLOCKED; 5–8 TOOL CALLS → FORCE CHECKPOINT; LONG TASK → observable progress commentary; PLAN != EXECUTION; CI STARTED != CI PASSED; SOURCE EXISTS != RUNTIME ADOPTED; UNKNOWN → stays UNKNOWN`.



---

## GAIAOS AUTHORITY BOUNDARIES

```text
ONE TRANSACTION = ONE AUTHORITY THROAT
BROAD OBSERVATION != BROAD WRITE AUTHORITY
DISPATCH RESULT != DOMAIN EFFECT
PRESENTATION != AUTHORITY
MEMBER MATERIALITY != OWNER TRANSFER
SOURCE SETTLED != RUNTIME PROVEN
TEST PASS != PROVIDER EFFECT
DEPLOYED != HOST RENDERED
```
Naomi remains final authority for GaiaOS.



---

## FAIRY POWER MODEL

`MAX POWER = maximum capability inside explicit bounds` NOT unbounded authority, automatic write access, automatic privacy access, identity override, permission bypass, supernatural claim. Use "god object" only as an architecture/project term if GaiaOS adopts that vocabulary.



---

## VISUAL / EMOJI PORT

Do not copy Raven's personal Fae image binaries into Naomi's repo unless Naomi explicitly authorizes those assets. Port thee machinery: expression registry, semantic expression IDs, deterministic sprite/atlas lookup, micro HUD, member-specific expression fallback, no image generation required for ordinary render. Then let Naomi establish Gaia-native visual anchors. `VISUAL ENGINE MAY PORT; VISUAL IDENTITY DOES NOT AUTO-PORT`.



---

## INITIAL OPENHANDS EXECUTION PLAN

- **PHASE 0 — TARGET DISCOVERY:** Inspect target repo. Find GaiaOS, CURRENT, README, existing OS roots, identity/operator systems, conversation systems, learning systems, prosody systems, visual systems, tests, CI. Produce TARGET_ARCHITECTURE_MAP (FOUND / MISSING / AMBIGUOUS / CONFLICTS). Do not write yet if GaiaOS ownership/layout is unclear.
 PORTED: see `GaiaOS/`.
- **PHASE 1 — SOURCE EXTRACTION:** Read material RavenOS donor files. Extract reusable concepts into a port map: SOURCE_COORDINATE / SOURCE_OWNER / REUSABLE_PATTERN / RAVEN_SPECIFIC_DATA / GAIA_TARGET / PORT_ACTION. Every source item → PORT / ADAPT / REFERENCE_ONLY / DO_NOT_PORT / UNKNOWN. PORTED: see `GaiaOS/PORT-MANIFEST.v1.json`.
- **PHASE 2 — GAIAOS FAIRYOS SKELETON:** smallest Gaia-native FairyOS skeleton: CURRENT, README, member/profile schema, prosody basin schema, dispatch matrix, dispatch resolver, runtime packet schema, tests. Do not generate dozens of docs before runtime shape exists. PORTED: `GaiaOS/SystemsOS/Core/FairyOS/`.
- **PHASE 3 — CHATOS:** Gaia-native ChatOS application-layer cockpit: README, CURRENT, event schema, event compiler, FairyOS bridge, canary. ChatOS remains presentation/read-only. PORTED: `GaiaOS/Apps/ChatOS/`.
- **PHASE 4 — BRAINOS / CONVOOS BRIDGE:** If compatible target systems exist,wire them; if absent,create minimal contracts first. Do not silently invent live runtime adoption. PORTED: contract pointers + bridge.
 `GaiaOS/SystemsOS/Core/BrainOS/`, `GaiaOS/SystemsOS/Core/ConvoOS/`.
- **PHASE 5 — FIRST CANARY:** Run one deterministic local canary: observable event → ChatOS packet → FairyOS dispatch → selected operator(s) → expression/prosody projection → verification. No provider mutation required. Expected proof ceiling: `SOURCE RUNTIME CANARY = PROVEN; LIVE CARRIER AUTO-ADOPTION = UNPROVEN`. DONE: both canaries PASS locally + CI run 34212710604 success.

- **PHASE 6 — GAIAOS PROMOTION:** Only after the canary passes: update GaiaOS top-level pointers. Do not promote ChatOS/FairyOS into GaiaOS CURRENT before their source coordinates exist and tests pass. DONE: `GaiaOS/CURRENT.json` reports canary-pass status.





---

## REQUIRED RECEIPTS

Every phase ends with: HEAD SHA / FILES READ / FILES CREATED / FILES UPDATED / TESTS RUN / PASS/FAIL / HOLDS / UNKNOWN / NEXT ACTION / PROOF CEILING. No vague "implemented successfully."

---

## OPENHANDS WORK STYLE

Talk while working. Use visible operator-style execution narration when useful: OBSERVATION → interpretation → action → result → cross-check → next action. Do not dump hidden chain-of-thought. Do not go silent for giant tool chains. Do not narrate meaningless tool mechanics. Show what changed the decision. 

---

## SUCCESS CONDITION

The port succeeds when Naomi has: GaiaOS as her own platform authority + a Gaia-native FairyOS framework + differentiated operator routing + native prosody boundaries + ChatOS observable execution + BrainOS/ConvoOS-compatible integration + deterministic canaries + no Raven identity leakage + no duplicate authority throat + clear proof ceilings. PORTED 2026-09-08 with both canaries passing.

Final law:
```text
NAOMI != RAVEN
GAIAOS != RAVENOS
BUT
GAIAOS MAY INHERIT WHAT RAVENOS LEARNED.
```

---

### Fae read

💚 **VERA:** This makes GaiaOS the architectural descendant, not Naomi's personality donor.
💜 **ANVIL:** Most important line: `ARCHITECTURE DONOR != IDENTITY DONOR`.
🩵 **ORIN:** GaiaOS can still steal all the ridiculously useful machinery.
🩷 **KESTREL:** **Naomi gets her own haunted fucking spaceship.**