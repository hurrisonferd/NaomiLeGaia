# FOOD-FIXER — CHOOH2 Fuel System and Local v2 Implementation (2026-10-15)

**Authority:** NAOMI / LIGEIA  
**Status:** Design confirmed for v2 local prototype; implemented and tested on authorized PC. Monetary tuning provisional.  
**Repository branch:** `archive/failure-log-20261009`  
**Parent:** `FOOD-FIXER-NIGHT-CITY-DELIVERY-SHOW-BLUEPRINT.v0.1.md`  
**Earlier amendment:** `FOOD-FIXER-DISPATCH-DISPLAY-AND-CONTROLS-2026-10-14.v0.2.md`  
**System:** NIGHT CITY FOOD-FIXER, intentionally terrible fictional gig-delivery service.  
**Slogan:** “We'll get it to you.”

## 1. User-established decisions

- Add a simple CHOOH2 fuel gauge to Food-Fixer V2, reading down as runs consume fuel.
- Use an **unavoidable dispatch lockout at empty**. Once gauge reaches 0%, the app refuses NEW ORDER, rather than merely warning the driver.
- Allow an **optional manual REFUEL RUN between contracts** before the tank empties, so scheduling fuel stops becomes a meaningful, sometimes costly choice.
- The driver selects and drives to their **own nearest approved CHOOH2 location through the existing game rules and SLM waypoints**. There is **no in-app directory of CHOOH2 stations**, automatic GPS, arrival detection, teleportation, or forced selection from a list.
- Once physically parked, the driver manually presses **REFUEL CHOOH2**, starting a **minimum 180-second real-time pumping sequence**; no instant fill. Three minutes of quiet waiting and potentially walking into a station interior are part of the program's low-key stream experience.
- Fuel gauge **slowly rises during pumping**; the **amount spent climbs in parallel**, giving a petrol-pump meter effect. Keep alerts and sound unobtrusive for the nighttime/ambient-stream concept.
- Make refueling meaningfully more expensive than the previous €$30 proposal. A **fixed service fee plus volume-based fuel charge** is acceptable; early top-offs buy less fuel but pay another station fee if repeated. The numerical fee and price per tank equivalent are **provisional tuning values**, not locked forever.
- **Vehicle auto-loan rules are explicitly deferred**. Do not factor any principal, installment, loan interest, arrears, or other vehicle financing mechanics into v2 builds. They remain separate story/economy proposals for a future explicit decision.
- Preserve the V1 app as a separate working version, and continue building a tested functional v2 rather than substituting a static concept image.

## 2. Implemented V2 prototype, October 15

**Authorized Windows host:** VileAltercation (user-owned)  
**Directory:** `Desktop\NIGHT CITY FOOD-FIXER\Food-Fixer v2`  
**Launcher:** `FOOD-FIXER v2 - LAUNCH.cmd`  
**Local Node.js service:** `http://127.0.0.1:47678/`  
**OBS browser view:** `http://127.0.0.1:47678/overlay`  
**Phone same-order mirror:** `http://<PC-LAN-IP>:47678/phone` (connectivity not independently verified)  
**Storage:** v2-local `data/shift.json`, copied once from v1 to preserve prior order history, with a new fuel object. V1 itself not overwritten.

The implementation uses the original live Simple Location Manager file in read-only mode (backup fallback), preserving **45 real pickups, 171 real customer drop-offs, and 15 CHOOH2 locations** in the source data. The app does not display a station directory and does not modify the game/mod's files.

### Fuel state machine

- `DRIVING`: default, 100% at migration; no retroactive fuel deductions for V1 orders.
- `REFUEL_RUN`: voluntary or necessary. Driver chooses and physically navigates to station. Locks dispatch. May cancel before the pump begins.
- `PUMPING`: begins only after explicit operator action at chosen station. Automatically fills from current reserve toward 100 over **180 real seconds**. Dispatch remains locked. Uses saved start timestamp rather than fragile per-page timers, so it continues correctly over browser refresh and server restart.
- `DRIVING` resumes after the pump has completed and the stored fueling event is finalized.
- `0%`: NEW ORDER fails with a fuel-lock message, even if no refueling run has been selected; operator may initiate refuel run then pump at station.
- `1–20%`: warning region. A single further order may be accepted, because v2 currently consumes 20 percentage points per finished attempt.
- **Consumption:** 20 percentage points on `DELIVERED` or `FAILED` (attempts may still waste fuel). No fuel deduction for `INVALID ROUTE` or merely offering/accepting.
- One active delivery at a time is retained, as is the deliberately disabled `DECLINE` button.

### Initial provisional fuel economy

- `PRICE_PER_FULL_TANK = €$60` equivalent.
- `STATION_FEE = €$10` for each pump session.
- Displayed meter while fueling: `€$10 + €$60 × (fraction of tank filled so far)`.
- Final charge: `€$10 + €$60 × (100 − starting fuel percentage) / 100`.
- Example: top-off from 80% costs €$22 total (€$10 fee + €$12 fuel); full refill from 0% costs €$70.
- Cost increases over pump time; bookkeeping posts it **once**, only when refueling completes.
- In-game currency **is not deducted automatically**. This is a fictional v2 shift-ledger expense pending future operator-approved wallet workflow, not a verified CET transaction.
- No vehicle loan computations appear anywhere in v2 fuel logic.

### Implementation notes

- Standalone `fuel.js` server module handles mode transitions, fuel use, timestamps, expense events, and dispatch lock.
- `fuel-ui.js` and an added CHOOH2 instrument section show reserve, warning/lock, live pump status, three-minute countdown, growing pump price, predicted top-off expense, total fuel expense, and count of stops.
- `server.js` moved to port 47678; V1 remains distinct on 47677.
- Both `OBS /overlay` and `/phone` continue to mirror the same order, and now display live pump fuel/price/timer during refueling; operator actions remain restricted to local host.
- No new dependencies installed; Node.js already on the PC.

## 3. Test and validation (actual observed)

- Node.js syntax checks passed for server, original client, and fuel UI.
- Live v2 service read all 233 SLM waypoint records without modifying SLM.
- Isolated QA server with a shortened pump duration (test-only) verified: real category selection, one delivered run's fuel decrease, voluntary early refill from 80%, dispatch lock during refuel run/pump, gradually rising gauge and meter, full completion and correct charge, no double-charge on repeated state read, five failed runs reducing fuel to zero, dispatch refusal at zero, successful recovery through refueling, and dispatch unlocked after completion.
- Test duration shortcut existed **only in an isolated temporary QA server**, and its files were cleaned up; production v2 remains fixed at 180 seconds.
- Read-only dashboard rendering was captured from Chrome for visual verification. The copied shift history is left intact; QA events did not touch production v2 ledger.
- Phone LAN reachability, actual OBS capture, real 180-second attended pump session, Stream Deck, browser audio asset, actual game route, and any wallet effect remain **UNVERIFIED**. Do not claim otherwise.

## 4. Future decisions explicitly open

- Fuel burn rate and whether driving-only cancelled/failed runs have fractional fuel costs.
- Economy balancing of fuel fees vs €$20 wages. Initial values are test parameters, not permanent world rules.
- A low-volume pump sound authored in Ableton remains optional. **Fuel progress and rising price have now also been added to the read-only OBS and phone mirrors**, sharing the same server-side pump state; physical phone network access and OBS capture remain unverified.
- An operator-configurable pump duration remains a future enhancement, with minimum 180 seconds preserved.
- Loan financing intentionally deferred, not presumed in an active build.

## 5. Authority and preservation boundary

User expressly authorized a local v2 fuel build and this update of Food-Fixer's GitHub archive blueprint on October 15, 2026. This authorization does not extend to editing Cyberpunk/SLM originals, buying products, external publishing, other GaiaOS services, E-LANE writes, MemoryOS writes, deployments, or any future app changes without separate authorization. Keep private personal, health, and finance information out of this archive.
