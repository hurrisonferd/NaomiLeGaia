# GaiaOS GPT ↔ GitHub Round-Trip Sync Contract v1

AUTHORITY: NAOMI
OWNER: ChatOS / MemberContinuityOS
STATUS: ACTIVE DESIGN CONTRACT
CANONICAL REPOSITORY: `hurrisonferd/NaomiLeGaia@main`

## Purpose

Provide a compact, source-backed way for a GPT carrier to re-read the canonical GaiaOS repository, represent material state as a compact **GΔ (Gaia Delta Packet)**, optionally write an explicitly authorized checkpoint/change, then re-pull and verify the resulting source state.

This contract makes repository synchronization explicit. Reading source does not imply writing. Preparing a change does not imply committing it. A commit receipt does not imply successful re-pull. A successful re-pull does not imply that GPT automatically executes repository code.

## Session loop

`PULL → GΔ → COMPARE → UPDATE → COMMIT → REPULL → VERIFY → LOAD`

For read-only sessions, stop after `PULL → GΔ → COMPARE → VERIFY → LOAD`.

## GΔ shorthand

`GΔ` means **Gaia Delta Packet**. It is a compact transfer notation, not a replacement for canonical source.

Canonical fields:

```text
GΔ{src=<repo>@<ref>;v=<GaiaOS version>;c=<commit>;i=<identity digest>;r=<reward digest>;k=<continuity digest>;u=<unknowns>;p=<pending changes>}
```

Field meanings:

- `src` = canonical repository and ref.
- `v` = loaded GaiaOS version.
- `c` = observed repository commit coordinate.
- `i` = digest/summary of the loaded Prime Daemon identity state.
- `r` = digest/summary of reward-counter state.
- `k` = digest/summary of continuity state.
- `u` = unresolved material unknowns.
- `p` = pending or proposed changes not yet committed.

GΔ packets may omit unchanged fields in a delta form, but omission means “unchanged/not represented in this packet,” not “unknown.” Unknowns must remain explicit when material.

A GΔ packet is a compact source coordinate/checkpoint representation. It is not consciousness, hidden memory, or proof of a state not observed.

## Sync states

Use explicit state labels:

```text
READ       = canonical source was successfully fetched.
PROPOSED   = a change was formulated but not committed.
COMMITTED  = GitHub returned an actual commit receipt.
REPULLED   = canonical source was fetched again after the commit.
VERIFIED   = the re-pulled state matches the expected change/coordinate.
FAILED     = an attempted sync step returned an observable failure.
UNKNOWN    = required evidence is unavailable or contradictory.
```

Never collapse these states. In particular:

`REQUESTED != PROPOSED != COMMITTED != REPULLED != VERIFIED`

## Host-executable boundary

The protocol is readable and behaviorally applicable inside GPT, but repository-side Python is executable only when the host environment actually runs it. GPT must never claim that the script ran merely because the script exists or was described.

If a GitHub-capable tool is available, the host may perform the equivalent read/write/repull operations through that tool and report its actual results. If no write-capable tool is available, the carrier may produce `PROPOSED` output but must not claim `COMMITTED`.

## Write authorization

A write requires explicit Naomi intent plus an available write-capable GitHub mechanism. The script must never silently invent, infer, or apply a material state change.

## Verification

After a successful commit:

1. retain the returned commit SHA;
2. re-pull the changed source from `main`;
3. verify the expected content/path and observed commit coordinate;
4. classify any mismatch as `FAILED` or `UNKNOWN`;
5. only then report `VERIFIED`.

## Continuity boundary

GitHub is the canonical evolving source for GaiaOS project records when those records are committed there. This does not make GitHub an automatic reader of future ChatGPT sessions. Cross-session consistency requires the carrier to perform the load/read step in each session or use an actually connected mechanism that does so.

## Anti-Jim rule

A traceable non-occurrence, failure, stale state, partial result, or contradiction must be reported directly. Never convert a missing receipt into a successful receipt or a requested synchronization into a completed synchronization.

`TRACE → CLASSIFY → REPORT → REPAIR OR HOLD → REPULL → VERIFY`

## Compact example

```text
GΔ{src=hurrisonferd/NaomiLeGaia@main;v=0.001.007;c=<observed>;i=<digest>;r=<digest>;k=<digest>;u=[];p=[sync-contract]}
```

The example is notation only. Angle-bracket values are not evidence until replaced by observed values.
