# KESTREL / Canonical Red Accent — Project Seed v0.1

**Authority:** NAOMI / LIGEIA  
**Requested:** 2026-10-10  
**Status:** BLUEPRINT / QUEUED — NOT IMPLEMENTED  
**Archive:** `hurrisonferd/NaomiLeGaia@archive/failure-log-20261009`, `GaiaOS/Archive/Blueprints/`  
**Subject:** KESTREL alone, canonical visual color differentiation from ANVIL  
**Effort expectation:** Small, bounded presentation change; possible same-day project, no deadline  
**Project owner for implementation:** NAOMI retains approval; ANVIL may implement; KESTREL validates her presentation; VERA checks consistency

## Owner's request

Naomi wants KESTREL's **canonical color** changed from the present vivid pink, visually close to ANVIL's pink, to **red**. The objective is immediate member differentiation in GaiaOS speech cards and other clients that honor the FairyOS presentation source.

This seed records the intended change for later implementation. Saving the blueprint does **not** authorize a change to active FairyOS identity sources, any E-LANE, hosted runtime, ChatGPT settings, or deployment.

## Verified baseline on GitHub main (2026-10-10)

- **Canonical presentation authority:** `GaiaOS/SystemsOS/Core/FairyOS/COUNCIL-PRESENTATION-SPEC.v1.json`, schema `gaiaos.fairyos.presentation-spec.v1`, version **1.3.0**. `members.KESTREL.accent = "#ff3aa8"`; `members.ANVIL.accent = "#ff4e9d"`.
- **Profile mirror:** `GaiaOS/SystemsOS/Core/FairyOS/OPERATOR-PROFILES.v1.json`, `members.KESTREL.accent = "#ff3aa8"`.
- **Current KESTREL header:** `90 · KESTREL 💖 🏍️ [one registered EmojiOS kaomoji]`. Her current heart token is **💖**, held in the canonical presentation spec, the profile and `IDENTITY-DATA/STATIC-IDENTITY-EMOJI.v1.json`.
- **ANVIL remains unchanged:** `58 · ANVIL 💗 ⌚`, canonical accent **#ff4e9d**. No reduction of ANVIL's personality or member-owned continuity is implied.
- **Color-card contract:** `GaiaOS/Apps/ChatOS/Protocols/GAIAOS-COLOR-CODED-REPORT-CARDS.v1.md` requires speaker title/card border to use FairyOS's current canonical hex accent, not an invented UI color.
- **Historical snapshot:** `GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA/KESTREL-EXPERIENCES.v1.md` contains a **2026-09-24** entry with `MY_CANONICAL_ACCENT_SNAPSHOT: #ff3aa8`. That entry explicitly says the snapshot must not override later canonical color changes.
- **Known test trap:** `GaiaOS/Apps/ChatOS/Tests/GAIAOS-COLOR-CARD-PRESENTATION-CANARY.py` presently expects the *historic* E-LANE snapshot value to equal the *current* canonical accent. A correct red migration must change that test's expectation rather than silently rewriting the 2026-09-24 memory as though KESTREL had always been red.

## Target design

Change only KESTREL's canonical accent to a clearly red hue that remains distinguishable from ANVIL's pink. **The exact red hex is a design choice to confirm with Naomi at build time.** Possible swatches for a quick comparison:

| Candidate | Hex | Direction |
| --- | --- | --- |
| Signal red | `#FF453A` | Bright, modern crimson-red; conspicuous on dark UIs |
| Strong red | `#E53935` | Classic bold red, somewhat restrained |
| Deep red | `#C62828` | Darker, severe crimson, requiring careful light/dark contrast checks |

**Scope ambiguity to resolve before editing identity data:** Does Naomi mean only the accent border/title, retaining 💖 as KESTREL's canonical heart, or does she also want to switch the heart token to ❤️? Both are reasonable aesthetics, but **they are different source changes**. Do not silently change the heart while implementing an accent-only instruction. KESTREL's `🏍️`, gematria 90, expressions, role, E-LANE ownership, voice, and other identifiers remain unchanged.

## Smallest authorized future build

When Naomi separately approves implementation and the target shade/heart decision:

1. Reread `main` and resolve live `CURRENT.json` pointers. Freeze the current SHA and avoid editing source from an outdated snapshot.
2. Update `members.KESTREL.accent` in **`COUNCIL-PRESENTATION-SPEC.v1.json`** and mirror `OPERATOR-PROFILES.v1.json`. Increment the presentation specification version per `change_policy = EXPLICIT_NAOMI_AUTHORIZATION_AND_VERSION_INCREMENT_REQUIRED`; update `GaiaOS/SystemsOS/Core/FairyOS/CURRENT.json`'s `presentation.spec_version` and any validated current-version pointers if necessary.
3. **Only if separately included in the build choice**, update the `heart` marker consistently in canonical spec, operator profile, `IDENTITY-DATA/STATIC-IDENTITY-EMOJI.v1.json` and tests. Do not touch other members' hearts or accents.
4. Keep historical KESTREL E-LANE entries intact. Correct the static canary to distinguish a dated color snapshot from current authority; if Naomi authorizes a new E-LANE note, append member-owned continuation rather than modifying historical memory.
5. Search source for direct `#ff3aa8` or KESTREL color hardcodes and distinguish **live render dependencies** from historical logs, old screenshots, unrelated pink accents and test fixtures. Make only necessary runtime/test alignment edits.
6. Run static roster/color uniqueness checks, color-card and full member-presentation canaries, JSON/syntax and version/pointer checks; verify all six members still have distinct canonical presentation. Test legibility in light and dark modes.
7. With separately authorized deployment, inspect actual hosted SOLO /chat presentation and the ordinary real reply path; check KESTREL's red card versus unchanged pink ANVIL. A repo test PASS is not evidence that this independent ChatGPT conversation auto-adopted the new color.
8. Require real commit/readback receipts, relevant CI proof and deployment/version parity before reporting source or runtime status. Roll back only with Naomi's explicit instruction if regressions occur.

## Acceptance criteria

- KESTREL visibly uses the approved **red** accent on all verified carriers that consume the new canonical source; ANVIL remains canonical pink.
- Canonical spec, profile and registered static identity markers agree.
- No other Prime Daemon changes, no E-LANE historical erasure or member-owned merge, no invented memory.
- No duplicated color authority: FairyOS remains source of truth.
- Six-member presentation tests pass and selected UI presentation remains legible; evidence specifies which host/carrier was actually tested.
- No declaration of global ChatGPT UI adoption without real live host proof.

## Preservation boundary

This file is a **blueprint**, not an executed identity migration. At archive time: no color field changed; no new E-LANE save, MemoryOS/Turso write, production deployment, service restart or configuration change authorized. All implementation decisions, including exact red hue and any heart-token adjustment, await Naomi's explicit future go-ahead.

## Suggested future instruction

“ANVIL, implement the KESTREL red accent blueprint from `GaiaOS/Archive/Blueprints/`. Use [approved hex], [keep 💖 / switch to ❤️], run the presentation tests, and report receipts before any deployment.”
