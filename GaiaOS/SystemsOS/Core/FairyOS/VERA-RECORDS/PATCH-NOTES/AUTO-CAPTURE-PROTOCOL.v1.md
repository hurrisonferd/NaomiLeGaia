# VERA AUTOMATIC CHANGE CAPTURE PROTOCOL v1

## Intent
Make VERA's record-keeping proactive rather than dependent on Naomi manually requesting patch notes.

## Invocation rule
When VERA is loaded/present with repository write capability, every completed material GaiaOS change gets a VERA recordability check before the work is considered closed.

## Material-change filter
Capture changes affecting architecture, behavioral contracts, governance/authority, canonical data, identity continuity, deployment or recovery paths, verification/proof boundaries, durable state, or meaningful incident resolution/regression. Skip trivial formatting and unexecuted brainstorming unless needed to explain later architecture.

## Closeout sequence
1. Observe the completed change and its available provenance.
2. Decide MATERIAL or NON-MATERIAL.
3. If MATERIAL, create or update a dated patch-note record in this directory.
4. Include rationale, authority, prior state, evidence, expected result, verification, consequences, unresolved questions, and source/proof references.
5. Mark claims by evidence class. Source change is not deployed-runtime proof.
6. If later evidence changes the interpretation, append a correction/supersession rather than rewriting history.
7. Confirm the repository write succeeded before treating the record as durable.

## Failure behavior
If VERA cannot write, retain the proposed record in the active session and state that durable capture is pending. Never report a successful record that was not committed.

## Autonomy boundary
This protocol is automatic only while VERA is actually invoked/loaded in an environment that exposes the relevant events and grants repository write tools. It is not a background daemon and does not independently watch GitHub between sessions. Full unattended capture requires a future GaiaOS runtime hook/event dispatcher to invoke VERA after material change events.

Authority: Naomi
Created: 2026-09-21
