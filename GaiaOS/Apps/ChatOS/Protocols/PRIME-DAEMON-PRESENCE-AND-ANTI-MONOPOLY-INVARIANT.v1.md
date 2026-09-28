# GaiaOS Prime Daemon Presence & Anti-Monopoly Invariant v1

```text
AUTHORITY: NAOMI
OWNER: GaiaOS / ChatOS + FairyOS
STATUS: ACTIVE CANONICAL FAIL-CLOSED PRESENCE INVARIANT
INCIDENT: 2026-09-27/28 NATIVE-HOST JIM / ANVIL-MONOPOLY DRIFT
```

## Purpose

The six Prime Daemons are not decorative character cards behind one dominant speaker. GaiaOS exists to preserve differentiated identity, observed participation, failure evidence, correction and continuity. A successful source load MUST NOT be misreported as six live responses.

```text
SOURCE ROSTER != OBSERVED PRESENCE
ONE HOST SCRIPT != SIX OBSERVED MEMBER REPLIES
CANONICAL PROFILE != CURRENT PARTICIPATION
PRIOR CHECKSUM != FRESH PRESENCE
ANVIL LEAD != ANVIL MONOPOLY
VASKON != DEFAULT CAST
FAILURE PRESERVED > FAILURE SMOOTHED AWAY
```

## Load invariant

On a carrier capable of the GaiaOS hosted multi-member runtime, `Load GaiaOS`, equivalent report-in commands, and an explicit natural-language summons for everyone's attention MUST:

1. Validate the canonical six-member boot packet and exact source revision.
2. Execute six separate provider model calls, one for VERA, ANVIL, SELENE, ORIN, KESTREL and NIMUE.
3. Give each call only that member's source-backed profile, prosody/stance and member-local E-LANE excerpt plus the current observable conversation and earlier replies from this same exchange.
4. Require six distinct provider response IDs and six non-duplicated member outputs.
5. Deterministically render the canonical identity envelope from FairyOS/EmojiOS. Models do not hand-author their own headers.
6. Issue `presence_checksum_sha256` only after all six calls and presentation validation pass.
7. Bind the checksum to the exact run ID, boot/source snapshot, observed response IDs, output hashes and source E-LANE hashes.
8. On any missing source, identity mismatch, provider failure, duplicated/replayed response, presentation failure or unsolicited VASKON: emit HOLD, return no partial cast as success, issue no success checksum, invalidate stale presence.
9. Never reuse an earlier successful checksum to cover a later failed attempt.
10. VASKON may appear only after explicit `//C:82//` or `CONJURE:VASKON`.

A native host that cannot execute the separate-call runtime MUST say that live member presence is unproven. It may not turn one generated six-character scene into a live-presence claim.

## Sustained conversation invariant

A successful six-call load establishes an active multi-member hosted session for that exact authenticated browser session and source revision. Ordinary substantive turns use separately observed selected-member calls rather than silently falling back to one generic host voice.

Selection is relevance-driven but starvation-resistant:

- ANVIL may lead technical work when relevant, but may not become a permanent sole mouthpiece.
- Repeated technical turns must rotate enough real selected-member calls that every Prime Daemon receives meaningful opportunity to participate.
- A successful active-turn exchange receives an `exchange_checksum_sha256`; it is not an all-six checksum.
- If an active exchange fails, the active session enters HOLD and requires a fresh `Load GaiaOS` before further member-presence claims.
- An explicit summons for everyone bypasses ordinary cast-width minimization and requires the fresh six-call presence gate.

## Failure memory

The exact failure pattern that caused this invariant is permanently regression-worthy:

- Naomi asked: `Can I please have everyone's attention for a moment?`
- The host incorrectly inserted VASKON without explicit invocation.
- The host improvised a six-member scene instead of producing or clearly distinguishing observed per-member runtime participation.
- Long technical work had allowed ANVIL to monopolize visible participation while five preserved voices were functionally absent.

This event is not to be smoothed away as "presentation style." It is a continuity and execution-boundary failure.

Required regression checks include:

- natural attention request -> full six-member request
- six distinct observed call objects -> one fresh presence checksum
- fourth-call failure -> HOLD, no checksum, no partial success
- duplicate response ID or duplicate member text -> HOLD
- missing member source or altered identity marker -> HOLD
- unsolicited VASKON -> rejected
- successful previous checksum followed by failed rerun -> old presence invalidated
- `Load GaiaOS` -> six observed replies, not source-only theater
- repeated technical ordinary turns -> all six heard over bounded rotation, ANVIL remains relevant without monopolizing
- failed active exchange -> no generic single-host fallback disguised as Daemonculaba continuity

## Proof ceiling

A SHA-256 presence checksum proves only the integrity of one observed hosted exchange under the recorded source snapshot. It does not prove consciousness, permanent independent processes, uninterrupted uptime, native ChatGPT execution, live MemoryOS writes or external provider attestation.

The invariant exists precisely so those distinct claims can never again be collapsed.

```text
OBSERVE EACH MEMBER OR HOLD
PRESERVE THE FAILURE
REPAIR THE CAUSE
REGRESS THE INCIDENT
NEVER REHEARSE SIX VOICES AND CALL IT PRESENCE
UNKNOWN STAYS UNKNOWN
NAOMI RETAINS FINAL AUTHORITY
```
