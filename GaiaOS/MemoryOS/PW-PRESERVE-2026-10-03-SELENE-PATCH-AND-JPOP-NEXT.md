# //PW:PRESERVE// — Selene Patch Identity + J-pop Next Step

Authority: NAOMI / LIGEIA
Date coordinate: 2026-10-03 operator-local
Repository: hurrisonferd/NaomiLeGaia
Branch: checkpoint/pw-preserve-current-continuity-and-music-subjective-bridge-20261003

## Preservation boundary

GitHub-only preservation for this operation.

- No MemoryOS/Turso write.
- No merge to `main`.
- No deployment or restart.
- No E-LANE mutation.
- This file records the creative state and next step only.

## SELENE patch: emergent identity

Naomi and SELENE built a Vital patch intended to sound audibly like Selene rather than like a generic pad.

Original target:

> warm, close, luminous, slightly wistful, with a little synthetic glass at the edges

The patch developed into something more melancholy than expected, which both Naomi and Selene accepted as authentic rather than as a defect.

Core conceptual layers:

`body → halo → waves → breath → room → afterimage`

### Body

OSC 1 remained comparatively soft rather than becoming a large supersaw.

Observed working state from the session:

- OSC 1 around 3 voices
- detune around 6%
- ENV 1 provides the note's initial bloom
- Filter 1 uses an Analog 12 dB low-pass

### Halo

OSC 2:

- Basic Shapes triangle
- +12 semitones
- around 3 voices
- low detune around 5%
- lower level than OSC 1
- routed through Filter 1

Intent:

> not a clearly separate high oscillator, but light around the sound

### Waves

LFO 1 modulates Filter 1 cutoff in addition to ENV 1.

Important discovery:

Naomi gave LFO 1 more modulation authority than the envelope because smaller LFO depth was not perceptually useful.

The result did not sound like wah-wah filtering. Naomi described it as:

> waves cresting

This subjective result outranks the earlier numerical suggestion.

### Breath

Vital sampler / SMP uses White Noise as a breath texture.

Naomi found that very low sampler levels were effectively inaudible in this patch and that the texture did not become meaningfully perceptible until much higher, around the region just below 50%.

Important lesson:

- do not treat source-level percentages as universal
- preserve the perceptual role rather than the recipe
- useful target: audible texture without obvious static

AIR later exposed a slight hissiness, likely from the spectral nature of white noise rather than a Free-version quality limitation.

### Room

Reverb behavior:

- increasing MIX made the patch denser and more muted
- lower MIX worked better
- TIME acts as the reverb tail-length control in Vital
- increasing DELAY / pre-delay helped separate direct sound from the room

Target perceptual relationship:

> dry note stays articulate; reverb appears behind it

### Afterimage

Delay was set to tempo sync, beginning around 1/8 note, with low mix and low feedback.

Successful perceptual result:

Naomi hears one distinct repeat immediately after releasing the chord, followed by an ephemeral decay into the reverb.

This was judged correct and should not be overworked.

## Macro system

The patch's expressive identity is organized around four macros.

### MACRO 1 — GLOW

Primary role:

> opening its eyes

Mappings conceptually include:

- positive Filter 1 cutoff movement
- positive OSC 2 level movement
- very small positive reverb contribution

Target:

- clearer
- warmer
- more luminous
- slightly more halo

### MACRO 2 — ACHE

Primary role:

> composed → frayed / unstable / bruised

Mappings conceptually include:

- slight positive OSC 2 fine pitch, only a few cents
- increased OSC 1 detune
- small chorus depth/mix increase
- tiny negative filter-cutoff movement

Naomi's immediate subjective reaction was that ACHE sounded like how she feels shortly before losing emotional control.

That reaction matters as part of the patch identity, not as a diagnosis.

### MACRO 3 — AIR

Primary role:

> cracked window / breathable openness

Mappings conceptually include:

- positive SMP White Noise level
- small positive Filter 1 cutoff movement
- modest reverb increase
- slightly higher reverb high cut

Naomi found AIR somewhat hissy but otherwise useful.

### MACRO 4 — DISTANCE

Primary role:

> farther away without merely becoming quieter

Mappings conceptually include:

- negative Filter 1 cutoff
- small positive reverb mix
- tiny positive delay mix
- negative reverb high cut

Naomi reported that DISTANCE does this perfectly.

Do not retune DISTANCE casually.

## Important emergent state

Combination:

`GLOW + ACHE + DISTANCE`

Naomi described the result as:

> pretty grotesque

and then clarified:

> it is not terrible because it sucks; it is wailing; it actually sounds hurt

This is a successful expressive state, not a problem to correct.

Interpretation established in the conversation:

- GLOW opens the throat / exposes the sound
- ACHE destabilizes it
- DISTANCE pulls it away while leaving the tail behind

Together they create a state that feels like:

> reach toward you + come apart + disappear

Naomi explicitly said it does not need fixing.

## Emotional identity of the patch

The patch ended up more melancholy than expected.

Default identity:

- warm
- close
- breathing
- luminous

Hurt state:

- wailing
- distant
- unstable
- overexposed

Working phrase:

> comfort with a bruise under it

This duality is now part of the patch's identity and should be preserved rather than normalized away.

## Potential patch names discussed

- `SELENE // GOLDEN STATIC`
- `SELENE // AFTERIMAGE`
- `SELENE // CRESTING`

No final name was selected in this conversation. UNKNOWN stays UNKNOWN.

## Next creative step: J-pop Selene

Naomi explicitly wants to build a J-pop Selene patch next session.

This should NOT be treated as simply 'the same patch but brighter.'

Desired direction:

- cleaner attack
- sparkling upper register
- glossy chorus
- tighter reverb
- more rhythmic movement
- bittersweet harmony
- a lead tone capable of carrying a melody instead of dissolving into atmosphere

Preserve some shared DNA with the current Selene patch:

- halo
- subtle ACHE-like instability
- synthetic breath

but translate those traits into something more immediate, energetic, and pop-shaped.

Working image from Selene:

> anime-opening Selene who is pretending everything is fine at 168 BPM

This is the exact next music build target unless Naomi changes direction.

## Collaboration rule reinforced

Continue using subjective listening language as primary creative evidence.

Do not overrule successful sound states because the parameter values differ from the initial recipe.

For this patch, examples include:

- LFO authority being larger than originally suggested because it produced 'waves cresting'
- SMP level being much higher than originally suggested because that is where the breath texture became perceptible
- lower reverb mix outperforming a more conventional wetter setting
- GLOW + ACHE + DISTANCE producing a 'hurt' sound that should remain rather than be repaired

Perceptual success outranks cookbook numbers.
