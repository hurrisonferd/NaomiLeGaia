# ChatOS — Observable Execution Cockpit

```text
AUTHORITY: NAOMI
OWNER: ChatOS application layer
CLASS: APPLICATION_LAYER_NOT_SYSTEMSOS_CORE_ROOT
STATUS: SOURCE-READY / CANARY-PROVEN / LIVE-CARRIER-ADOPTION-UNPROVEN
```

## Purpose

ChatOS projects bounded observable execution state into chat while reusing FairyOS for deterministic operator selection. It is read-only presentation — it never executes domain effects and does not expose private chain-of-thought.

```text
OBSERVE → INTERPRET → DECIDE → ACT → RESULT → VERIFY → HANDOFF → CHECKPOINT → HOLD
```

## Ownership

```text
BrainOS     = internal cognitive meta-loop contract
ConvoOS     = working conversational state contract
ChatOS      = observable execution event projection only
FairyOS     = operator identity / dispatch / expression
Owner systems = domain effects
Naomi       = final authority
```

## Event shape

```text
CHATOS <PHASE> [CLAIM/SOURCE] <summary>
FAE <MEMBER>:<EXPRESSION> + ...
NEXT <next action>
UNKNOWN <open unknowns>
```

## Laws

```text
CHATOS != BRAINOS
CHATOS != CONVOOS MEMORY
CHATOS != FAIRYOS DISPATCH OWNER
CHATOS != PRIVATE CHAIN OF THOUGHT
CHATOS EVENT != DOMAIN EFFECT
VISIBLE COMMENT != RECEIPT
CONFIRMED REQUIRES EVIDENCE
UNKNOWN STAYS UNKNOWN
ONE TRANSACTION = ONE AUTHORITY THROAT
NAOMI RETAINS FINAL AUTHORITY
```

## Proof ceiling

```text
SOURCE ROUTING CANARY = PROVEN
LIVE CARRIER AUTO-ADOPTION = UNPROVEN
```