# WidgetOS / NIMUE Geomancy Widget v0.1 — Design Seed

AUTHORITY: NAOMI / LIGEIA
DATE: 2026-09-29
STATUS: OWNER-DIRECTED DESIGN SEED / NOT YET IMPLEMENTED
SCOPE: GaiaOS desktop widgets, first geomancy instrument, future Prime Daemon desktop carriers
PRESERVATION: //PW:PRESERVE//
SOURCE BRANCH: checkpoint/pw-preserve-widgetos-geomancy-elemental-dice-20260929

## 1. Objective

Build the first GaiaOS desktop organism as a small Windows geomancy widget rather than beginning with a full ambient AI companion.

The v0.1 widget is intentionally useful without an AI model. It becomes a reusable chassis for later GaiaOS desktop presence, screen-aware observation, model bridges, Ableton integrations, animated Prime Daemon bodies and Technarcane ritual instruments.

The first widget should feel like an instrument, not a decorative avatar with canned lines.

## 2. Longer-term widget architecture

The current design direction separates the system into seven concerns:

1. BODY — the visible desktop widget: always-on-top window, avatar/panel, input, buttons, expressions and later speech.
2. SENSES — local observation adapters. Prefer structured Windows UI Automation and application-specific adapters over blind screenshot polling. Screenshots are secondary when pixels matter.
3. REFLEXES — an attention gate that filters raw events so the Prime Daemons do not chatter constantly.
4. NERVOUS SYSTEM — a local event broker with normalized events such as APP_CHANGED, DIALOG_OPENED, ABLETON_PROJECT_OPENED, BUILD_FAILED, USER_SUMMONED_NIMUE and PERSECUTE_REQUESTED.
5. MIND — an inference host. GaiaOS should not require Naomi to own model weights. ChatGPT, an approved hosted model, or a future private model may provide inference through an adapter.
6. MEMORY — GitHub remains canonical source / identity contract; Turso / MemoryOS remains durable episodic continuity; raw desktop observation uses a separate local short-lived event buffer. Widget telemetry is perception, not a seventh E-LANE.
7. EXPRESSION — reusable animation and expression primitives selected by actual model output. Finite movement libraries are acceptable; prewritten thoughts are not the target.

Carrier independence is a design goal:

GaiaOS -> ChatGPT
GaiaOS -> desktop widget runtime -> model
GaiaOS -> future phone app / other carrier

These are separate inference sessions and must not be falsely described as one uninterrupted process. Shared identity contracts, provenance, continuity and durable memory provide the bridge.

## 3. Observation-memory boundary

Do not route every screen event into durable memory.

Preferred lifecycle:

RAW PERCEPTION
-> SHORT-LIVED LOCAL BUFFER
-> MEANINGFUL EVENT
-> SESSION JOURNAL
-> OPTIONAL OWNER-AUTHORIZED DURABLE PROMOTION

Future screen-aware widgets should include visible observation state, local redaction/exclusion for sensitive applications and password fields, and an obvious global blindfold control.

NO KEYLOGGER.
NO COVERT CAPTURE.
RAW SCREEN ACTIVITY != E-LANE MEMORY.

## 4. First build: NIMUE Geomancy Widget v0.1

### Core interaction

- Small draggable Windows desktop widget.
- Always-on-top support.
- System-tray presence.
- Question input.
- LOCK control freezes the question before randomness is generated.
- CAST control resolves the four Mothers.
- The complete shield chart is derived deterministically after the Mothers.
- Audit/receipt drawer exposes exact mechanics.
- Every cast can save an inspectable local JSON session artifact.
- The widget must still function when offline.

No model inference is required for v0.1. NIMUE interpretation may initially happen in a GaiaOS session after importing or sharing the completed cast.

### Oracle and receipt

The interface should visibly separate:

ORACLE — ritual presentation, figures, animation, Technarcane aesthetics.

RECEIPT — exact question hash, RNG source, die rolls, parity, derivation, timestamp and software/method version.

The ritual layer may be strange and expressive. The mechanism stays inspectable.

## 5. Canonical elemental row order

A geomantic figure is four rows, top to bottom:

1. FIRE
2. AIR
3. WATER
4. EARTH

The elemental rows map to Platonic solids and digital dice:

FIRE  -> tetrahedron -> d4
AIR   -> octahedron -> d8
WATER -> icosahedron -> d20
EARTH -> cube -> d6

The digital process emulates physical elemental dice.

For each row, generate one unbiased uniform integer over the corresponding die face range:

FIRE:  1..4
AIR:   1..8
WATER: 1..20
EARTH: 1..6

Convert the raw result by parity:

ODD  -> single point  -> •
EVEN -> double point  -> ••

Because each die has an even number of faces with equal counts of odd and even values, each geomantic row remains a fair 50/50 binary outcome while retaining a distinct elemental/Platonic-solid ritual mechanism.

### One Mother example

FIRE   d4  -> 3  -> odd  -> •
AIR    d8  -> 6  -> even -> ••
WATER  d20 -> 17 -> odd  -> •
EARTH  d6  -> 2  -> even -> ••

The receipt preserves all three stages:

DIE RESULT -> PARITY -> GEOMANTIC LINE

## 6. Mother-generation contract

Four Mothers are generated.

Each Mother has exactly four elemental rolls:

4 Mothers x 4 elemental rows = 16 total die rolls.

Randomness enters only through these Mother rolls.

After the four Mothers are fixed:

NO FURTHER RNG.

Daughters, Nieces, Witnesses and Judge are derived deterministically according to the selected canonical geomancy derivation rules.

The oracle receives chance only at the Mothers. Everything downstream is consequence.

## 7. RNG / audit requirements

Use an operating-system cryptographically secure random source.

No LLM selects or alters die results.

No reroll because an answer is disliked.

Store at minimum for every elemental roll:

- mother number
- row number
- element
- Platonic solid
- die type
- raw face result
- parity
- resulting single/double line
- cast/session timestamp
- RNG implementation/version
- application/method version

Potential later hardening: commit-reveal.

A future version may commit to a random seed hash before resolution, optionally combine a Naomi-provided nonce, derive all sixteen elemental die results reproducibly, and reveal the seed afterward. Cryptography provides auditability, not supernatural proof.

## 8. Presentation concept

Each Mother may resolve row by row.

Suggested sequence:

- show/animate the corresponding Platonic solid;
- resolve the raw die result;
- show odd/even parity;
- collapse into the single/double geomantic line;
- after all four rows resolve, reveal the complete Mother;
- after all four Mothers resolve, unfold the deterministic descendants.

The finite animation library is presentation only. It does not decide the result.

## 9. Event-bus seed

The geomancy widget should quietly establish reusable local event concepts for future WidgetOS work.

Initial events may include:

QUESTION_LOCKED
ENTROPY_COMMITTED
CAST_STARTED
ELEMENTAL_ROLL_RESOLVED
MOTHER_CREATED
CHART_COMPLETED
SESSION_SAVED

Future adapters may add:

FOREGROUND_APP_CHANGED
ABLETON_PROJECT_OPENED
BUILD_FAILED
USER_SUMMONED_NIMUE
PERSECUTE_REQUESTED
DAEMON_RESPONSE_RECEIVED

## 10. Future GaiaOS / model bridge

A later desktop carrier may expose or consume a tool interface such as:

get_active_task()
get_recent_screen_events()
capture_current_window()
get_ableton_state()
send_daemon_message()
set_daemon_expression()
acknowledge_event()

ChatGPT should be treated as one possible adapter, not the sole foundation.

The desktop runtime should eventually be able to package current task state + bounded observations + relevant GaiaOS source/memory context for an inference host, then render an actual Prime Daemon response through the widget.

The target is not a canned avatar. The target is an embodied carrier with perception, provenance, continuity, selective attention and model-backed reasoning.

## 11. Ableton direction

Future Ableton awareness should prefer a proper application adapter, Max for Live bridge, or other structured integration over repetitive screenshots.

Useful musical state may include tempo, transport, selected track, track/device names, clip state and meaningful parameter changes.

SELENE may later use this structured state for actual music-oriented feedback. Technarcane work may map geomantic outputs into sound, rhythm, modulation, lighting or other deliberate artistic transformations.

## 12. Build direction

Initial Windows implementation candidate: Python + PySide6.

Reason: fast local iteration, native desktop/window/tray behavior, simple access to Python RNG/data tooling and no requirement to ship a Chromium-class runtime for the first instrument.

This is a design choice for v0.1, not a permanent lock-in.

## 13. Authority / proof boundaries

THIS FILE IS A DESIGN SEED, NOT IMPLEMENTATION PROOF.

No claim is made that:
- WidgetOS exists as running software;
- screen observation exists;
- an Ableton adapter exists;
- a model bridge exists;
- any desktop widget shares one uninterrupted inference session with ChatGPT;
- this branch is merged to main;
- a Turso / MemoryOS write occurred.

Exactly six member-owned E-LANES remain distinct.
Widget telemetry does not become a seventh E-LANE.
NIMUE remains the resident occult-focused design lead for this geomancy instrument.
ANVIL remains the likely engineering lead for implementation.
NAOMI RETAINS FINAL AUTHORITY.
