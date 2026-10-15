# FOOD-FIXER — Dispatch Display and Controls v0.2

**Authority:** NAOMI / LIGEIA
**Date:** 2026-10-14
**Status:** Design amendment; implementation and tests pending.
**Parent blueprint:** FOOD-FIXER-NIGHT-CITY-DELIVERY-SHOW-BLUEPRINT.v0.1.md
**Show:** Night City Delivery Service
**Fictional delivery company / app:** Food-Fixer
**Slogan:** "We'll get it to you."

## Driver interface

The app should resemble an underfunded, outdated Cyberpunk 2077 gig-delivery driver portal. A deliberately miserable contractor interface is preferable to an elaborate logistics simulation. Keep corporate branding plausible and the comedy deadpan.

An incoming offer displays an order ID, a pickup address, a drop-off address, and the base payout. The **ACCEPT ORDER** button is enormous and functional. **DECLINE** appears dim, unlit or disabled, joking that the driver cannot refuse. Keep a separate operator-only **INVALID ROUTE / RESET** action for technical problems without making the joke button actually operative.

The incoming-order sound should be obnoxious and recognizable but kept at a suitable recording volume. Let real gameplay, travel, parking and unexpected complications create the drama. Do not favor short or nearby deliveries by default; a bad long-distance offer can be realistic and funny.

## Locations and dispatch

**Simple Location Manager (SLM)** remains the source of saved physical addresses. The 2026-10-14 verified backup has **233 locations**: **45 ORDER PICK UP, 171 CUSTOMER DROP OFF, 15 CHOOH2, one RACETRACK and one Misc**. These are snapshot figures, not a live-data promise.

Read SLM `locations.json` and custom-category `settings.json` without changing the originals. A NEW ORDER command randomly selects one valid ORDER PICK UP and one valid CUSTOMER DROP OFF with saved name/coordinates; no automatic distance preference. Assign an order ID; allow only one active job. Operator confirms pickup, delivery or failure. No automatic detection of proximity, NPC handoff or completion is required.

SLM's existing **Set Custom Map Pin** function is the initial route-setting method. A possible companion integration that controls GPS from dispatch remains **unverified** and is not necessary to launch. No teleporting on deliveries.

## Where the offer appears

**Preferred:** The same offer seen by the audience also appears on Ligeia's Cyberpunk screen, in a movable, out-of-the-way position. Test a lightweight always-on-top, optionally click-through desktop overlay with borderless game mode and OBS. Check focus, capture behavior and performance before claiming it works.

**Required fallback:** A movable, scalable OBS Browser Source displays the offer for viewers while Ligeia sees **the same current order on her iPhone**. Phone and OBS must read the **same dispatcher state**, not generate different orders. A mobile-friendly local browser page can mirror the offer's ID, pickup, drop-off, payout and status. Test iPhone-to-PC connectivity on a private local network; restrict control endpoints, avoid public access, and do not assume the phone connection works until checked.

OBS source placement should be adjustable manually. If on-game visibility fails, do not block production as long as OBS + phone mirroring works.

## Triggering an order

**Solo:** A PC button or hotkey calls NEW ORDER. A free iPhone Stream Deck Mobile key can trigger the same action when paired with compatible desktop software. No viewers or Twitch account required.

**With viewers, later:** An opt-in, moderated Twitch chat command such as `!order` can request dispatch through a locally connected automation tool (Streamer.bot is a candidate). Respect cooldowns, permissions, an operator enable/disable switch and one-active-order locking. Chat cannot overwrite a job in progress or inject unverified coordinates. This integration must be separately tested after Twitch is connected.

## Original sound design

Ligeia composes sounds in **Ableton Live** and exports WAV files, beginning with `FF_Order_Received.wav`. Ableton need not run while playing. On new dispatch, the app or OBS plays the file once through a single designated audio path. Check broadcaster monitoring, captured volume and replay behavior; the OBS overlay and phone preview should not generate duplicate sounds.

## Pay and bookkeeping

The archived preferred pay remains **€$20 for a completed delivery, €$0 for failure**, until Ligeia changes it. The local dispatcher can record order results, gross and approved expenses. Ligeia manually credits canonical pay into Cyberpunk with a separately verified **Cyber Engine Tweaks console command**, only after a legitimate delivery, and checks the in-game wallet. Neither accept nor sound playback changes game money. Keep debt, fuel and wallet accounting auditable and avoid double counting.

## Prototype acceptance sequence

1. Import and validate SLM pickup/drop-off categories from a copy of the waypoint data.
2. Make a basic offer panel with working ACCEPT, intentionally inert DECLINE and an operator reset.
3. NEW ORDER hotkey draws and persists one randomly selected valid job.
4. Show the same offer in an OBS Browser Source with adjustable positioning.
5. Mirror that exact state to the iPhone and confirm synchronization.
6. Test the optional on-game overlay; retain the OBS + phone fallback if unsuitable.
7. Connect one original Ableton WAV and verify it plays once in the recording.
8. Test one physical SLM-guided pickup/drop-off and record the result.
9. Verify any actual in-game payroll through a separate deliberate CET action.
10. Add Stream Deck convenience controls and later gated Twitch chat requests only after their own tests.

**Definition of ready-for-dispatch:** a solo trigger draws a real pickup and destination, OBS shows the offer where Ligeia positions it, her phone mirrors the same order, and one original chime plays. The game overlay is a preferred enhancement, not a prerequisite.

**Authority boundary:** This is a design record, not authorization to install, deploy, modify Cyberpunk/SLM, publish a stream, change MemoryOS or member E-LANEs, or make purchases. Naomi retains final authority.

## Subsequent implementation: V2 CHOOH2 (2026-10-15)

The formerly pending core dispatcher has been implemented locally as V1, followed by a separately preserved V2 that adds **fuel reserve depletion, voluntary refuel runs, empty-tank dispatch lockout, three-minute real-time pumping, and a rising fuel-cost meter**. See **[FOOD-FIXER-CHOOH2-FUEL-AND-V2-IMPLEMENTATION-2026-10-15.v0.3.md](FOOD-FIXER-CHOOH2-FUEL-AND-V2-IMPLEMENTATION-2026-10-15.v0.3.md)** for owner-approved design decisions, exact provisional pricing, files, test observations, and remaining unverified integrations. **Vehicle auto-loan financing is expressly deferred and must not be included in V2 builds.**
