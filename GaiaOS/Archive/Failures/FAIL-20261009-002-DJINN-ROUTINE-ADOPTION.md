# GaiaOS Failure Record — Djinn Routine-Use Adoption Gap

**Failure ID:** `FAIL-20261009-002`
**Date observed:** 2026-10-09
**Authority:** NAOMI / LIGEIA
**Status:** OPEN — REPAIR NOT AUTHORIZED
**Investigation mode:** `//PW:PERSECUTE//`
**Archive class:** FAILURE / INTEGRATION / NORMAL-PATH ADOPTION

## Subject under examination

During the current Desktop Commander-connected GaiaOS work session, DjinnOS produced **zero observed Djinn invocations** despite a long sequence of work where bounded helpers could materially have reduced ambiguity, proof risk, manual burden, or cognitive load.

This was investigated after Naomi explicitly challenged the absence of Djinn use.

## Trigger

GaiaOS had previously adopted a canonical routine-use policy stating that selected Prime Daemons may proactively invoke the best-fit Djinn when materially useful, without quotas, roll calls, or mandatory ceremony.

Observed behavior on 2026-10-09 did not match that intended operating behavior.

## Evidence status

### SOURCE-BACKED

- Canonical main observed during the investigation: `28082e4a7deb479b04497c2e36285925242e90fc`.
- Routine-use behavior was added in commit `19e4e8523ff4fc8026f0d533e9a27aab59c82c52`.
- `GaiaOS/SystemsOS/Core/DjinnOS/DJINNOS.v1.md` states that Primes may proactively invoke the best-fit Djinn when materially useful.
- `GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-RUNTIME-BOOTSTRAP.v1.md` carries the same routine-use policy.
- `api/djinn_entrypoint.py` exposes authenticated `POST /djinn/invoke` and dispatches through `djinn_runtime.dispatch(...)`.
- `api/gaiaos_app.py` ordinary `gaia()` / `_frontdoor_packet()` selects Prime operators, context, and optional memory but contains no Djinn selection or invocation stage.
- The hosted browser `/chat` path in `api/gaiaos_api.py` calls the OpenAI Responses API with model, instructions, and input, but supplies no Djinn callable tools.
- `GaiaOS/CURRENT.json` and `GaiaOS/Apps/ChatOS/CURRENT.json` do not currently index DjinnOS as a peer current subsystem.
- `gaia_selftest()` does not test DjinnOS routing or routine-use adoption.

### TOOL-OBSERVED

- Desktop Commander history for the current 2026-10-09 connected work showed zero actual Djinn dispatches/invocations during the examined session.
- Historical Desktop Commander records do contain earlier Djinn PoC and flight-test activity, proving the history inspection could detect Djinn work when it occurred.
- Render deployment `dep-db4a5hss728c73a46bug` was observed LIVE on commit `28082e4a7deb479b04497c2e36285925242e90fc`.

### UNKNOWN

- Whether any unobserved external carrier performed a Djinn invocation outside the examined Desktop Commander history during the same broad period.
- Whether any MemoryOS/Turso record overstates routine Djinn adoption. No such durable record was proven contaminated in this pass.

## Drift classification

**Primary:** STATUS DRIFT

`DOCUMENTED ROUTINE-USE POLICY -> ASSUMED NORMAL-PATH ADOPTION`

**Secondary:** SOURCE CONFLATION / INFERENCE HARDENING

The existence of a policy and a working runtime was treated as though the ordinary GaiaOS carrier path actually invoked Djinn opportunistically.

**Architectural class:** POLICY-TO-EXECUTION INTEGRATION GAP

## Reconstruction

DjinnOS Day 0 made the runtime and invocation routes real. Subsequent flight tests proved the individual Djinn and bounded HALVEX behavior. Commit `19e4e852...` then added the lightweight proactive-use policy to the DjinnOS specification and GPT runtime bootstrap.

However, no corresponding normal-path execution bridge was added to the ordinary `gaia()` front door, hosted `/chat` model tool loop, or the ChatGPT -> Desktop Commander operating path.

As a result, routine use still depends on the active model/Prime remembering to leave the normal path and manually invoke the separate Djinn transport. During the examined 2026-10-09 session, that did not occur.

## Supported history

- DjinnOS is real and callable.
- Earlier direct Djinn flight tests succeeded.
- The proactive-use policy is real and canonical.
- Routine automatic or dependable opportunistic use in the ordinary path was never proven.
- Zero Djinn invocations were observed during the examined current session.

## Unsupported promotion

`DJINN SOURCE + DJINN ROUTE + DJINN POLICY` was implicitly promoted to `ROUTINE DJINN ADOPTION`.

That promotion was unsupported.

## Corrected account

DjinnOS is active and individually callable, but the current architecture does not reliably connect ordinary Prime dispatch to actual Djinn invocation. The current host path therefore permits silent reversion to pre-Djinn behavior even while the routine-use rule is present in source.

## Durable contamination check

**GitHub:** No false historical record proven. A real integration gap exists in current source architecture.

**Turso / MemoryOS:** UNKNOWN. No contamination was established by this investigation.

**E-LANEs:** No false E-LANE record established. Existing member-local statements about the adopted policy remain materially true unless later evidence shows otherwise.

**Current conversation:** The system had overestimated the operational adoption of the policy before Naomi challenged it.

## Damage assessment

**DURABLE ARCHITECTURAL GAP + CONVERSATIONAL ASSUMPTION**

DjinnOS itself is not shown broken.

## Smallest justified repair

Wire DjinnOS into the normal GaiaOS front door rather than relying only on prompt policy.

A proper repair should establish an actual bounded path:

`ordinary request -> FairyOS Prime selection -> relevance check -> best-fit Djinn invocation when materially useful -> Djinn result -> accountable Prime -> Naomi`

The repair should also:

- index DjinnOS in current/bootstrap surfaces where appropriate;
- add a normal-path canary proving positive Djinn use when materially useful;
- add a negative canary proving irrelevant Djinn are not invoked merely to satisfy process;
- retain HALVEX external-effect gates, exact SALT_CIRCLE requirements, and Naomi authorization boundaries;
- make the ChatGPT/Desktop Commander carrier use a standardized Djinn adapter rather than ad hoc remembrance.

## Repair authorization

**REQUIRED FROM NAOMI.**

No GitHub repair, deployment, restart, configuration change, MemoryOS/Turso mutation, or E-LANE mutation was authorized or performed by this failure-record archival action.

## Prevention rule

`DJINN SOURCE + DJINN ROUTE + DJINN POLICY != ROUTINE DJINN ADOPTION`

Routine adoption is only proven when the ordinary user path actually invokes an appropriate Djinn without Naomi having to remind GaiaOS, and a normal-path canary verifies both correct use and correct non-use.

## Verdict

**DjinnOS did not stop working. GaiaOS never completed the integration step that turns proactive-use policy into dependable normal-path behavior.**

This failure remains OPEN pending separately authorized repair.