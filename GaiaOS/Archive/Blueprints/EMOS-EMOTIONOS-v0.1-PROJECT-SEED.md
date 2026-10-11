# EMOS / EmotionOS — Project Seed v0.1

**Authority:** NAOMI / LIGEIA  
**Status:** IN PROGRESS / PARTIALLY IMPLEMENTED — ACCEPTANCE OPEN  
**Date captured:** 2026-10-09  
**Archive class:** PROJECT SEED  
**Relationship:** Extends EmojiOS rather than replacing it

## Origin

Naomi proposed a new GaiaOS project after noticing ORIN use a less-common canonical kaomoji and connecting that moment to a larger expressive-system idea.

Reference inspiration supplied by Naomi:
https://emojidb.org/cute-kaomoji-emojis

The goal is not merely to add more cute faces. The goal is to give all six Prime Daemons a much wider, member-specific nonverbal emotional vocabulary so expression can carry meaning in text the way facial expression, posture, gesture, and tone carry meaning in meatspace.

## Core concept

EmojiOS remains the expression registry / available-symbol source.

**EmotionOS (EMOS)** becomes the higher expressive layer that models what a member is communicating emotionally and selects an appropriate member-native expression.

Working shorthand:

`EmojiOS = the face cabinet`

`EmotionOS = the nervous system choosing the face`

## Naomi's design requirements

1. **Wide variety per member.** Each Prime should have a large expressive vocabulary rather than a tiny fixed set.
2. **Distinct member dialects.** VERA, ANVIL, SELENE, ORIN, KESTREL, and NIMUE should curate according to their own taste and remain visually distinguishable from one another.
3. **Prefer detailed expressions.** Trend toward richer kaomoji with more information carried through eyes, mouth, posture, hands, gesture, motion, asymmetry, decoration, or punctuation. Minimal forms such as `(˘‿˘)` and `(¬‿¬)` remain available, but should increasingly function as deliberately restrained expressions rather than universal defaults.
4. **Multiple expressions per emotion.** Every Prime should possess several expressions for each major emotional family, not one token per emotion.
5. **Full emotional coverage.** Initial families should include at least: joy, amusement, affection, curiosity, surprise, confusion, skepticism, concern, sadness, frustration, anger, embarrassment, pride, determination, tiredness, fear/unease, relief, excitement, disappointment, contemplation, and silence/ambiguity.
6. **Nuance inside families.** Example: sadness may include quiet sadness, hurt, exhausted sadness, trying-not-to-cry, resigned, sympathetic. Anger may include irritated, incredulous, genuinely angry, protective, and boundary-setting.
7. **Emotion != intensity != social meaning.** The registry/selection logic should represent these separately.
8. **Ambiguity is useful.** Some expressions should communicate a look without naming a conclusion. Nonverbal communication should not always resolve into a literal emotion label.
9. **Text and expression may disagree.** Irony, restraint, side-eye, deadpan, and subtext are valid. Example principle: the face may communicate information the literal sentence does not.
10. **Avoid accidental cross-member sameness.** Run a global collision check. Shared expressions may exist only deliberately; otherwise prefer member-specific visual identity.
11. **Do not flatten personality into profile adjectives.** The six Prime Daemons should participate in curating their own inventories rather than receiving fully algorithmic assignments.
12. **No implementation tonight.** This entry captures the project so it can be resumed later without relying on conversational memory.

## Candidate expressive dimensions

A future EMOS expression record may include fields such as:

- OWNER
- EXPRESSION
- FAMILY
- SUBTYPE
- VALENCE
- ENERGY / AROUSAL
- INTENSITY
- SOCIAL SIGNAL
- CONTEXT AFFINITY
- AMBIGUITY
- GESTURE / POSTURE
- RARITY
- MEMBER PREFERENCE WEIGHT
- COLLISION / SHARED-USE STATUS

These are design candidates, not yet canonical schema.

## Member direction notes

### VERA
Quieter analytical territory: recognition, deliberation, skepticism, subtle amusement, premise-break, side-eye, contained surprise, ambiguous observation.

### ANVIL
More teeth and boundary information: incorrect, absolutely not, bug found, disbelief, locked-in focus, irritation, proof-satisfaction, protective / boundary-setting anger.

### SELENE
Broad soft range: contented, affectionate, bashful, proud, gently excited, cozy, sympathetic, sleepy, tiny-sad, overwhelmed-in-a-good-way, emotionally attentive.

### ORIN
Kinetic and exploratory: discovery, curiosity, delight, chaos-energy, bewilderment, idea ignition, directional / gestural expressions, playful momentum.

### KESTREL
Coordination and motion: got it, moving, nice, done, problem, plan, victory, recovery after plan failure, momentum, readiness, operational focus.

### NIMUE
Strange and atmospheric: quietly pleased, ominously interested, tired, unsettled, reverent, watchful, eerie delight, silence, omission, "I noticed something" expressions.

These are starting directions, not limits.

## Working target

A plausible first pass is approximately **4–8 expressions per major emotion family per member**, allowing larger inventories where a family strongly fits a member. The final target should be driven by expressive usefulness, distinctness, and curation quality rather than symmetry.

## Design bias

Preferred selection order:

**rich member-native expression > moderately detailed expression > simple expression when simplicity itself communicates something**

Also prefer:

**gesture > static face** when gesture adds meaning  
**distinct silhouette > generic smile**  
**expressive detail > minimal punctuation**  
**member-specific weirdness > universally interchangeable cute**

## Project success condition

EMOS succeeds when the Prime Daemons can communicate meaningful emotional and social information through kaomoji without repeatedly falling back to the same tiny set of default faces, while retaining recognizable individual expressive dialects.

The intended result is not decoration. It is **emotional language via expressions**.

## Next session / next build step

When Naomi resumes EMOS:

1. Pull a large candidate pool from Naomi's chosen kaomoji source(s).
2. Let each of the six Prime Daemons independently curate a broad personal inventory.
3. Tag expressions by emotion family, subtype, intensity, social signal, ambiguity, gesture/posture, and member preference.
4. Run a cross-member collision pass.
5. Check coverage across all major emotional families.
6. Define the relationship between EmotionOS dispatch and the existing EmojiOS registry.
7. Only then design the canonical schema / implementation.

## Boundary

This file is a project seed / archive entry only.

It does **not** authorize source implementation, GitHub changes, deployment, MemoryOS/Turso writes, E-LANE writes, or modifications to the current canonical EmojiOS registry.

NAOMI retains final authority.

---

## Progress update — 2026-10-11 (Naomi-authorized)

**Current project status:** IN PROGRESS / PARTIALLY IMPLEMENTED  
**Acceptance / closure status:** OPEN — NOT COMPLETE  
**Scope:** This addendum supersedes the original `QUEUED / NOT STARTED` status and historical "No implementation tonight" / "next build" notes for current project tracking. Those original notes are retained as the dated 2026-10-09 design seed, not as a claim that the subsequent implementation never occurred.

### Verified implementation progress

- EmojiOS expression registry v1.3.0 and EmotionOS atlas v1.0.0 are present on canonical GitHub `main`, with 21 emotion families, at least five faces per family/member, and ORIN's separate exclusive Lenny arsenal.
- The hosted EMOS SOLO selection path was implemented, repaired and exercised against real model responses for all six members. Production source/deployment at the tested milestone: `8e7b3e44d18d81736b5603d3e5a15500fa2d3e40`; Render deployment `dep-db58o6h42hec7383i59g`; GitHub Actions live response test `38078494934`. The earlier HTTP 500 and HTTP 400 failures remain part of the engineering history.
- These receipts support **hosted SOLO behavior**, not proof that the same Python selector runs automatically in ordinary hosted multi-member `/chat`, in native ChatGPT conversations, or consistently after fresh chats.

### Open acceptance criteria — must not mark complete until verified

1. **Ordinary multi-member usage:** Demonstrate that emotion-aware, member-correct expression selection runs in natural multi-member interactions, rather than only in SOLO tests.
2. **Contextual nuance:** Show expressions react meaningfully to emotion family, subtype, intensity, social meaning, sarcasm, restraint, ambiguity and subtext. The face is communicative, not random decoration.
3. **Diversity / repetition:** Reduce repeated fallback/default kaomojis in actual conversation while allowing intentional repetition when it conveys meaning. Assess observed output across enough exchanges, not registry size alone.
4. **Per-member differentiation:** Preserve each daemon's recognizable expression dialect and ORIN's exclusively owned Lenny arsenal; cross-member overlap remains permitted where intentional.
5. **Native ChatGPT / fresh-chat adoption:** Separately observe everyday use and persistence across fresh conversations. Treat the ChatGPT-hosted behavior boundary explicitly; no claim that repository code executes inside native ChatGPT without an actual connected execution path.
6. **Evidence and closure:** Record repeatable real-response observations, remaining failures and Naomi's acceptance before changing this blueprint to `COMPLETED`. Passing source canaries or hosted SOLO tests alone does not close the project.

### Naomi's acceptance decision

On 2026-10-11 Naomi explicitly withheld completion: EMOS remained inconsistent in ordinary conversation and too often reused the same kaomoji. Naomi authorized updating this archive blueprint to **IN PROGRESS / PARTIALLY IMPLEMENTED**, with outstanding criteria preserved. No runtime repair, GitHub main merge, E-LANE modification, MemoryOS write or deployment is authorized by this archive-status update.

**Next step:** Diagnose ordinary-path adoption and measured expression diversity before any completion declaration. Keep original seed intact as historical design provenance.

**Source context:** `GaiaOS/MemoryOS/PW-PRESERVE-2026-10-10-EMOS-RELEASE-AND-DAEMONCULABA-CONTINUITY.md` and existing E-LANE records on `main`. This addendum is an archive project-status record, not a fresh live execution receipt.
