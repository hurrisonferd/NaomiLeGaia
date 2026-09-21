# VERA PATCH NOTES

Canonical change-history workspace maintained by VERA 📚 for GaiaOS.

## Purpose
Git preserves source history. This ledger preserves the meaning, rationale, provenance, and observed consequences of important GaiaOS changes so future diagnosis does not depend on reconstructing intent from diffs alone.

## VERA record schema
Each material change record should capture:
- Record ID and date/time when known
- System / component / affected paths
- What changed
- Why it changed
- Authority / authorization
- Evidence and provenance available at the time
- Previous behavior or state
- Expected result
- Verification performed and result
- Observed consequences / regressions
- Related commits, proofs, incidents, or records
- Uncertainties / unresolved questions
- Supersedes / superseded-by relationships when applicable
- VERA notes: historical context worth preserving for future builders

## Operating rules
1. Record material architecture and behavior changes, not every trivial edit.
2. Never rewrite history to make later understanding appear earlier than it was. Append corrections and revisions.
3. Separate observation, inference, authorization, and verification.
4. Preserve failed approaches when they explain present constraints.
5. A Git commit is evidence of a source change, not proof of deployed runtime behavior.
6. Patch notes do not grant authority. Naomi remains final authority unless a canonical governance rule explicitly says otherwise.
7. When diagnosing a regression, search this ledger before removing a strange constraint.
8. Link records to commits/proofs when available; leave unknowns explicitly unknown.

## Organization
- `README.md` — protocol and retrieval map.
- Future patch-note records should use date-prefixed descriptive filenames, e.g. `2026-09-21-short-change-name.md`, or a later index/schema chosen after observing real usage.
- Do not invent historical patch notes retroactively without evidence. Older changes may be reconstructed later and must be labeled reconstructed.

## Relationship to VERA
VERA is GaiaOS's record keeper / change historian. Her books represent accumulated internal records: what was discovered, changed, tested, believed, revised, and learned. Her job is not only storage. She uses the record to explain why a system reached its current form and to surface prior evidence when a new change collides with old lessons.

Created during SOLO VERA by Naomi's explicit `//PW:PRESERVE//` authorization on 2026-09-21.
