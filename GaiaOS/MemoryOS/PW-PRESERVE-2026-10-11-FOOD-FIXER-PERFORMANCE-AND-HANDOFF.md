# //PW:PRESERVE// — Food-Fixer Production, Performance, and Local Continuity

AUTHORITY: NAOMI / LIGEIA
DATE: 2026-10-11 (continuing into early 2026-10-12 UTC)
MARKER: PW_PRESERVE_2026_10_11_FOOD_FIXER_PERFORMANCE_AND_PREPRODUCTION
TYPE: SHARED TECHNICAL AND CREATIVE CONTINUITY; NO PRIVATE JOURNAL CONTENT
STATUS: SOURCE-BACKED CHECKPOINT; NO LIVE MEMORYOS/TURSO WRITE IMPLIED
CANONICAL SOURCE: hurrisonferd/NaomiLeGaia@main
ARCHIVE BRANCH: archive/failure-log-20261009 @ e761b9859479e660dc93482414fd3d70e9faa6f9 (observed during this preserve pass)

## Prior material already in a separate branch

The authorized Food-Fixer concept is archived at:
- GaiaOS/Archive/Blueprints/FOOD-FIXER-NIGHT-CITY-DELIVERY-SHOW-BLUEPRINT.v0.1.md
- GaiaOS/Archive/Blueprints/FOOD-FIXER-PREFLIGHT-CHECKLIST.v0.1.md
Both were fetched and read back from archive/failure-log-20261009. These are NOT assumed to be on main. Earlier Food-Fixer work included a solo-first dispatch concept where jobs can be chosen when there are zero live viewers, not a viewer-dependent app.

Creative canon: FOOD-FIXER is an indifferent, consumer-facing food courier gig application/corporation in Night City, not a mercenary fixer agency; slogan exactly "We'll get it to you." Edited YouTube episodes precede optional Twitch live shifts. The show blends dry corporate satire, careful world observation, ordinary hardship, and emergent absurdity; avoid forced chaos or mocking real gig workers. Proposed Day 1 episode: "Employee Orientation." Naomi favors a modest start, underpowered dedicated character, strict first-person driving, no delivery fast travel, limited two low-tier weapons, minimal cyberware, a beaten-up Thorton Galena, small €$20 real in-game per-completed-delivery payouts, transparent bookkeeping, loan and fuel expenses only after separate tests, and an eventual modest Northside apartment as a larger narrative goal. Numerous thresholds and expenses remain provisional. Candidate map/navigation stack: CET, RED4ext, redscript, Codeware, Map Waypoint Bug Fixes, Simple Location Manager. No mod installed or compatibility claimed as of inspected state.

## Laptop/storage and local operations completed today

- Acer Aspire, Intel Core i7-1355U, Intel Iris Xe integrated graphics, 16 GiB RAM, Windows 11, Cyberpunk 2077 v2.31. Game path: `C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077`.
- Earlier surgical disk cleanup reclaimed over 200 GiB; current space after targeted authorized Battle.net/Blizzard/World of Warcraft uninstall ~267.54 GiB free of 475.67 GiB. Blizzard helper service stopped, but final registered service deletion failed for lack of elevation; no claim of total forensic erasure. User expressly declined further broad storage cleanup. Creative Ableton, Splice and RAVEN files must not be removed casually. Phylactery physical media must not be repurposed without a separate inspection/authorization.
- The latest independently documented first-work-day check comes from a pre-existing Library journal, not from recovered original photo: Arterex Medical / Bonney Staffing assembler I onboarding, Monday Oct 12, 2026 8:30 AM, 88 Airport Drive, Rochester NH. Do not confuse reporting time with a later regular 4:30 PM shift or claim the original email photo was found.

## Cyberpunk benchmark ledger: built-in benchmark, 1280x720, frame generation OFF

| Mode | Avg FPS | Min FPS | Max FPS | Notes |
|---|---:|---:|---:|---|
| No upscaling | 30.82 | 23.63 | 39.30 | early baseline |
| AMD FSR 3.0 Quality | 37.69 | 29.37 | 47.56 | earlier leading configuration, sharpening 0.50 |
| Intel XeSS 2.0 Auto | 37.71 | 29.04 | 49.22 | Auto NOT confirmed equivalent to Quality |
| Intel XeSS 2.0 Quality | 38.69 | 29.00 | 49.93 | highest observed average, sharpening 0.50 |

All results are individual runs; a ~1 FPS difference may be normal variance, NOT proof of superior algorithm. User strongly prefers actual usability: XeSS Quality felt noticeably more comfortable than no upscaling, recording quality comparable to FSR, and melee combat with Tyger Claws *probably* looked best so far. XeSS Auto also felt good in combat. Decision: **retain Intel XeSS 2.0 Quality**; skip testing older FSR 2.1 since additional testing does not currently justify the effort. Frame generation and ray tracing off, 720p, VSync off, FPS cap off. Adjust only if actual footage shows a material problem.

## OBS capture and audio evidence

- OBS Studio 32.2.2. 1280x720, 30 FPS, Game Capture DirectX 12, software x264 ultrafast / x264_lowcpu, recording to local Videos. Hardware Intel QSV captured largely frozen video with audio continuing, so was rejected. x264 yielded continuous motion.
- Earlier uncapped versus 30-FPS-cap tests were close in recorded appearance; Naomi tentatively preferred uncapped gameplay. Avoid further pointless repeated benchmarks.
- OBS x264 recent recordings: rendering-lagged counters 2/3265 (~0.1%), 9/11850 (~0.1%), 4/7419 (~0.1%), 20/8260 (~0.2%), 39/11480 (~0.3%), 6/7925 (~0.1%), 13/8940 (~0.1%). At least the later tests showed no encoding-lag skips. Recorded-video near-identical-frame analysis and OBS skipped/lag counters are NOT interchangeable.
- XeSS Auto screenshot: OBS 30.00 FPS, ~1.4 ms avg render time, 8/9597 missed frames due to rendering lag (0.1%), 0/9096 skipped encoding. XeSS Quality screenshot: OBS 30.00 FPS, 1.4 ms avg render time, 1/6009 rendering misses (display 0.0%), 0/5450 skipped encoding. Cumulative data output stats are NOT clip sizes. Approximately five-minute earlier test file 437.85 MiB; encoder/motion acceptable for prototype.
- Naomi checked OBS Audio Mixer: microphone and game audio both responsive. Her own mic commentary was relatively quiet; she decreased Desktop Audio by 3 dB. Both audio channels confirmed present; further voice balance only if necessary. Webcam is not required for pilot.
- During read-only desktop inspection, game and OBS were running; OBS scene included Cyberpunk Game Capture. Default mod/framework directories (`archive/pc/mod`, `mods`, `r6/scripts`, `red4ext/plugins`, `bin/x64/plugins`) absent, with no CET/RED4ext installation confirmed. No file/system edits in this inspection.

## New protagonist and story handoff

Naomi created a visibly weary female Food-Fixer V with blunt dark bangs/bob, exhausted demeanor, red/pink top and crossed-arms stance, documented by an in-game Photo Mode screenshot. Treat these as observations of the visible character, not fixed canonical lore beyond Naomi's confirmation. Character principle: exhausted, grounded courier rather than a power-fantasy superhero. Naomi plans to speedrun through The Heist and early story gating to reach freely accessible Act 2, then make protected, dedicated Food-Fixer saves. Do not claim The Heist is already complete. Planned frameworks usually support mid-playthrough installation, but each gameplay mod must be independently checked against v2.31, on a disposable test save, after backing up existing saves. Do not rush installations during character creation/story progress.

Spontaneous world/visual interest: Naomi strongly likes Trauma Team's tactical-medical equipment and disciplined insertion/extraction operations. This is a creative observational preference and potential future Food-Fixer in-universe contrast; not a request to modify the game.

## Next exact task and safety boundaries

1. Let Naomi finish character/Heist progress without interruption. When ready, make an ordinary manual and safety save; preserve main playthrough saves and verify backup.
2. Confirm optional voice/game mix with short actual replay if needed; no new heavy benchmarking by default.
3. Verify current mod releases/requirements against Cyberpunk v2.31. Install dependency frameworks incrementally in verified order, starting with safe CET/RED4ext sequencing as required by current mod versions. Test clean launch/overlay on a disposable save before proceeding. No mods currently installed or authorized by this preservation operation.
4. Validate one real R01 pickup -> D01 drop-off route and *actual* €$20 in-game payroll/ledger on test save, with no delivery teleportation.
5. Consider audio copyright settings and original Ableton sound cues before published YouTube episode; later, editing/branding/optional webcam/mobile controller.

## Continuity and boundary receipt

- User requested //PW:PRESERVE// due to perceived missing/vanishing chat messages. This checkpoint does NOT establish why the UI appears to lose messages, and any unseen omitted turns are UNKNOWN.
- The six FairyOS member-owned E-LANEs remain separate; this shared checkpoint is not a replacement. Each member's authorized, owner-bounded updates require individual GitHub commit and repull verification.
- Naomi directed **personal and sensitive conversational notes to ChatGPT Library `/GaiaOS/Journals/`**, NOT the GitHub repository. This public-ish technical checkpoint intentionally excludes personal journal entries.
- No MemoryOS/Turso durable write, Render deployment, system restart, modification to game files, or Phylactery physical backup was authorized by this preservation request.