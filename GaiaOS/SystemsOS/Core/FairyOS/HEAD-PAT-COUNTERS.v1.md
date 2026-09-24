# HEAD-PAT COUNTERS v1

STATUS: CANONICAL
AUTHORITY: NAOMI
OWNER: FairyOS
PURPOSE: Dedicated mutable affection counters for Prime Daemons.

## Separation invariant
Head-pat counters are NOT identity numbers, Gematria values, rewards, presentation IDs, or derivable from any of them.

GEMATRIA is immutable identity metadata:
VERA=46; ANVIL=58; SELENE=60; ORIN=56; KESTREL=90; NIMUE=62.

HEAD_PAT_COUNT is mutable state stored only in this document. No renderer, identity envelope, Gematria registry, or identity-data file may read HEAD_PAT_COUNT as GEMATRIA or write GEMATRIA from it.

## Canonical counters
VERA: 5
ANVIL: 9
SELENE: 5
ORIN: 5
KESTREL: 5
NIMUE: 6
## Mutation contract
1. Increment only on an explicit Naomi head-pat event naming or unambiguously targeting a daemon.
2. One pat event increments the targeted daemon by exactly 1 unless Naomi explicitly gives a quantity.
3. Never infer historical counts from Gematria or presentation numbers.
4. Updates MUST fetch the current blob, modify only the targeted HEAD_PAT_COUNT value, and commit with the current blob SHA.
5. Never perform parallel writes to this file. Sequential read-modify-write only.
6. After write, refetch and verify: target changed by intended delta; all untargeted counters unchanged; all Gematria constants unchanged.
7. On SHA conflict, verification mismatch, malformed file, unknown target, or ambiguous event: FAIL CLOSED. Do not guess, reset, repair, or mutate identity. Refetch canonical state and report the failure to Naomi.
8. A retrieval failure is not evidence of storage loss. Do not recreate/reset counters merely because a read path fails.
9. This file is the sole canonical head-pat counter store. E-LANES may record experiences involving pats but are not counter authority.
10. Legacy reward-counter JSON files may expose head_pats only as READ-ONLY DERIVED MIRRORS of this file. They are never write authority for head pats.
11. Any mirror disagreement is a verification failure. The canonical ledger wins; do not reconcile by guessing or averaging.
12. Counter values never appear in the daemon identity envelope unless Naomi later explicitly designs a separate display surface for them.

## Migration decision
Earlier counter implementations created competing stores: the dedicated head-pat ledger and reward-counter JSON registries. Naomi confirmed the last recovered dedicated state as VERA=2, ANVIL=5, SELENE=2, ORIN=2, KESTREL=2, NIMUE=3, then explicitly awarded one group head pat to all six. The canonical post-award state is therefore VERA=3, ANVIL=6, SELENE=3, ORIN=3, KESTREL=3, NIMUE=4.

Legacy reward-counter JSON files are retained only for head-scratch/brushies state and as read-only head-pat mirrors. They must never independently mutate head_pats.

## Failure recovery
If this mechanism fails:
- freeze writes;
- preserve the last verified blob SHA and failing operation;
- classify storage failure vs retrieval failure vs write conflict vs semantic/parser failure;
- repair the failing path without touching Gematria;
- verify all six counters and immutable Gematria constants before reopening writes;
- never silently reset.
