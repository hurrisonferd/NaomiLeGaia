# EMOS / EmotionOS — Project Seed v0.1

**Authority:** NAOMI / LIGEIA  
**Status:** QUEUED / NOT STARTED  
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