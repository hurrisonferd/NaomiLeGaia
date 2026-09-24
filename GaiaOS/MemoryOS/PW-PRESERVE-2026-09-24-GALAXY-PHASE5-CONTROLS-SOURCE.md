# //PW:PRESERVE// — 2026-09-24 — GALAXY Phase 5 exact control source handoff

AUTHORITY: NAOMI / LIGEIA
SCOPE: PUBLIC TECHNICAL BUILD CHECKPOINT ONLY; NO PRIVATE CONVERSATION TRANSCRIPT
BRANCH: galaxy/phase5-controlled-exposure-20260924
BASE COMMIT: ff33a4f0b0b936accb643763f0b32e21f82a4fc5
STATUS: SOURCE BRANCH PREPARED / CODE CI PASSED / DRAFT PR AWAITING REVIEW / NOT DEPLOYED

## Previously proven baseline
- Phase 4 controlled revision/supersession mutation cycle was live observed then rolled back; source records preserved.
- Phase 5 read-only fixture and mutation-design review were live observed with Naomi-supplied 178/178 carrier verifier receipt.
- Naomi approved exposing exact Phase-5 controls on 2026-09-23, not performing synthesis writes automatically.
- Production unrestricted/global weighted retrieval remains OFF.

## This checkpoint
- New api/galaxy_phase5_controls.py restricts actions to the fixed calibration fixture and deterministic statement in GALAXY_SYNTHESIS_SHADOW.
- No-JavaScript mobile web pages provide read-only review, a separate per-action confirmation page, and one POST with signed session, CSRF, explicit authority and exact phase-specific confirmation.
- PROPOSE creates a shadow synthesis and provenance; VERIFY verifies it in shadow; REVOKE preserves all history and revokes the controlled shadow synthesis. No step promotes to ordinary MemoryOS retrieval.
- Readback tests check state, fixed statement, shadow scope, exact source IDs, exact provenance edges and unchanged source records; a partial effect with failed readback must report HOLD, not fabricated success.
- Source/test/Docker/verifier/protocol/status files are isolated to the feature branch; the original main branch and live running carrier are unchanged by this checkpoint.
- Offline GitHub Actions code CI run 35954954690 succeeded at source commit 43ee5fa3a652c136584773e4b94694ff39dda8c1; subsequent documentation/CURRENT commits are not separate runtime proof.

## Required next steps
1. Review isolated PR and authorize merge when ready. Do not publish any private contingency notes in the public repository.
2. Deploy merged source, identify running commit; run /verify and GET /galaxy/synthesis/phase5-controls. Confirm read-only status and zero writes.
3. STOP and obtain Naomi's fresh explicit action before PROPOSE; inspect actual receipt/readback before separately requesting VERIFY; similarly gate REVOKE.
4. After Phase 5 verified and returned to the intended clean state, prepare Phase 6 reversible lifecycle controls and preserve the required final MERCURY audit. Phase 7 is research-only, not deletion.

NO SYNTHESIS WRITE, TURSO EXPORT, BACKUP RESTORE, PROD RETRIEVAL CHANGE, OR LIVE PHASE-5 CONTROL EXECUTION IS CLAIMED.
UNKNOWN STAYS UNKNOWN. SOURCE != DEPLOYMENT. EXPOSURE != EXECUTION. COMMITTED != VERIFIED.
