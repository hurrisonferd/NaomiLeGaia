# GaiaOS OCA Hardening v1

```text
AUTHORITY: NAOMI / LIGEIA
OWNER: ChatOS
STATUS: ACTIVE READ-ONLY HARDENING CONTRACT
EFFECT_AUTHORITY: NONE
DURABLE_WRITE_AUTHORITY: NONE
```

## Purpose

This contract hardens Operational Context Acquisition against the failure modes
found during OCA v1 promotion review on 2026-10-06.

It does not enlarge OCA authority. It narrows how OCA may describe what it sees.

## Epistemic ceiling

```text
OCA_PACKET != TRUTH
OCA_PACKET != AUTHORITY
OCA_PACKET != CANON
OCA_PACKET != MEMORY
OBSERVED != EXHAUSTIVE
FRESH != INFALLIBLE
```

An OCA packet is a provenance-bearing synthesis of the evidence actually
acquired for the active objective. It may be incomplete even when every included
observation is fresh and verified.

A packet may support a claim only up to the ceiling of the underlying evidence.
No packet-level wording may promote an observation beyond its source.

## Acquisition minimization

OCA must use the smallest sufficient read set for the active objective.

The host selects collector and provider reads because they are materially
relevant to the current question or next authorized step. Provider availability
alone is not sufficient reason to read a provider.

```text
AVAILABLE_TO_READ != REQUIRED_TO_READ
CONNECTED != RELEVANT
MORE_CONTEXT != BETTER_CONTEXT
```

Sensitive or personal provider data must not be acquired merely because a
connector exists. When a task can be answered from source coordinates, OCA
must not read continuity or personal-data surfaces by default.

## Adapter isolation

Every provider adapter must be:

- named and versioned;
- bound to one collector class;
- independently testable;
- provenance preserving;
- read-only inside OCA;
- explicit about accepted read operations;
- explicit about forbidden effects;
- unable to grant authority to another adapter or provider result.

Adding a provider does not authorize expanding another provider's scope.

## Repository downstream-effect accounting

A bounded source diff is not proof of the complete effect surface of a push.
Repository automations may react after the initiating source change.

Before a source promotion whose changed paths can trigger a write-capable
workflow, OCA preflight should identify the known downstream automation surface
from:

`GaiaOS/Apps/ChatOS/Protocols/GAIAOS-OCA-DOWNSTREAM-EFFECTS.v1.json`

After the source effect, observed secondary effects must be distinguished from
those merely expected by configuration.

Use these four classes:

```text
DIRECT_EFFECT
EXPECTED_AUTOMATION
OBSERVED_SECONDARY_EFFECT
UNRESOLVED_DOWNSTREAM_EFFECT
```

Their meanings are strict:

- `DIRECT_EFFECT`: the effect explicitly authorized and directly executed.
- `EXPECTED_AUTOMATION`: a configured automation that current source inspection
  shows can react to the direct effect.
- `OBSERVED_SECONDARY_EFFECT`: a downstream effect actually read back after the
  direct effect.
- `UNRESOLVED_DOWNSTREAM_EFFECT`: a downstream effect that is possible or
  expected but not yet observed, excluded, or disproven.

```text
EXPECTED_AUTOMATION != OBSERVED_SECONDARY_EFFECT
WORKFLOW_PERMISSION != WORKFLOW_EXECUTION
SOURCE_DIFF != TOTAL_EFFECT_SURFACE
```

## Completion claims

When a relevant write-capable automation is expected, completion reporting must
include one of:

1. observed secondary-effect evidence;
2. evidence that the automation did not run or had no material effect; or
3. an explicit unresolved-downstream-effect statement.

Silence is not evidence that nothing happened.

## Identity-sync finding

The workflow:

`.github/workflows/GAIAOS-MEMBER-IDENTITY-SYNC.yml`

is a known write-capable downstream automation. On qualifying pushes to `main`,
it may append `SOURCE_CHANGE_SYNC` provenance events to affected Prime Daemon
`IDENTITY-DATA/*.json` records and update `last_verified`.

That behavior is distinct from an E-LANE experience write and distinct from
inference of member experience or internal state. OCA must report the distinction
rather than collapsing all member-data changes into one category.

## Canary obligation

The OCA canary must inspect `.github/workflows` for the bounded write signals
listed in the downstream-effect inventory. Any discovered workflow carrying a
tracked write signal but absent from the inventory is a canary failure.

The scanner is a tripwire, not a proof that no other mutation mechanism exists.
Its limitation must remain explicit.

## Core laws

```text
MAP != TRUTH
AVAILABLE_TO_READ != REQUIRED_TO_READ
SOURCE_DIFF != TOTAL_EFFECT_SURFACE
EXPECTED_AUTOMATION != OBSERVED_SECONDARY_EFFECT
SILENCE != NO_SECONDARY_EFFECT
ADAPTER_COUNT MUST NOT BECOME CONTEXT_SPRAWL
READ LESS; PROVE ENOUGH
REDUCE HUMAN RELAY; DO NOT REDUCE HUMAN AUTHORITY
```
