# GALAXY Stage 9AC: full synthetic, offline migration rehearsal

AUTHORITY: NAOMI / LIGEIA. STATUS: SOURCE-ONLY STACKED DRAFT on Stage 9AB #103, itself stacked on #102 and prior drafts. Nothing merged, deployed or connected to Turso. This is a new **end-to-end integration test**, not another manual chore for the owner.

## Why now

The separate new Turso databases sovmem-staging and sovmem-main have been created manually in the owner's account. sovmem-main replaces the earlier deleted sovmem database and is the *permanent future memory destination*. sovmem-staging is the disposable live experiment target. Both remain untouched by this milestone. The mobile Turso SQL editor proved unsuitable for repeated setup, so Stage 9AB prepared a guarded PC-local initializer. Stage 9AC uses these ACTUAL predecessor modules together on fresh disposable local files, not separate isolated tests that could miss integration bugs.

## One-command developer/CI reproduction

Run on a trusted Python 3.12+ developer environment with only the checked-out source:

    python api/galaxy_stage9ac_full_local_rehearsal.py --local-fixture-only --driver native

Optional actual libSQL-driver LOCAL compatibility check, after installing the public libsql Python wheel:

    python api/galaxy_stage9ac_full_local_rehearsal.py --local-fixture-only --driver libsql

Both commands ALWAYS allocate new isolated local temporary SQLite files, one for synthetic staging and two distinct unchanged sentinels representing sovmem-main and original GaiaOS. The libsql connector, where used, is explicitly injected and bound to the ephemeral LOCAL staging file; no remote .turso.io connection is made, despite realistic synthetic URL strings in the signing envelope. The CLI has no option to pass a real database URL, credential, owner transcript or source record. Without --local-fixture-only it refuses to start. Each run deletes temporary files after returning and reports only predeclared synthetic statuses, counts and proof limitations; no source statements, document locations, tokens, marker UUIDs, raw URLs or local paths are printed.

## What the chain proves on the LOCAL fixture

1. Invoke 9AB's ONE-COMMAND private bundle preparation (9V staging marker/canary SQL and 9AA canonical memory plus receipt/rollback SQL). Read and verify all four privately generated files, then assert 9AB DRY RUN opens **zero connections**.
2. 9AB checks distinct synthetic staging/main URL names, applies exactly the six reviewed tables plus unique staging marker to a **new empty LOCAL staging file** under a guarded transaction, and proves exact schema and emptiness from a fresh independent local connection.
3. 9X's existing independently signed-one-canary mechanics run with a SYNTHETIC test HMAC key and injected LOCAL connector. It must return HOLD_LOCAL_FIXTURE_NOT_REMOTE, even after the underlying 9V canary successfully commits and reopens; "local" cannot be mislabeled "real Turso".
4. 9AA's two-connection, strictly SELECT-only pre-import check verifies the exact reviewed marker, previous canary digest, all six table layouts and empty memory/import/rollback ledgers, again returning LOCAL evidence only.
5. 9S/9T independently verify synthetic pinned source/export bytes and MemoryOS-only provenance. 9Y independently signs the exact 2-record import manifest, atomically imports **two synthetic historical HOLD records** into that SAME local staged fixture, creates per-item and signed batch receipts, and proves fresh connection readback. Its exact replay must make zero writes. 9AA must now refuse the nonempty staging database.
6. 9Z uses a DIFFERENT synthetic HMAC key to sign an independently bound exact rollback manifest, deletes only the two new HOLD records under atomic rollback, retains both original import item receipts and the original signed batch receipt, writes its separately signed rollback receipt, and proves fresh connection readback. Exact rollback replay must perform zero writes.
7. A new signed approval for the same two source fingerprints MUST HOLD with PREVIOUSLY_ROLLED_BACK_SOURCE, not silently reintroduce rolled-back memory. 9AA must continue reporting nonempty pre-import ledgers after rollback, and 9AB must refuse bootstrap reentry once the canary exists.
8. Independently compare the FULL BYTES of the initial and final synthetic sovmem-main and original GaiaOS files. They must remain byte-identical. The final staging file must have 0 memory rows, 1 canary, 1 retained import batch, 2 item receipts and 1 rollback receipt.

GitHub CI exercises this full integration with both native sqlite3 and the ACTUAL public libSQL driver against temporary **LOCAL** files. Negative tests inject false remote statuses, malformed driver selections, stage rollback failure and private-error strings. No actual archived conversation data, live user credentials, uploaded file, Turso instance or independently authenticated human approval is ever used.

## Proof boundary and next actual owner gate

Even a successful full local rehearsal is NOT real Turso behavior evidence, provider-level database separation, durable restart/replica persistence, an approved authenticated remote importer or rollback, calibrated old/current historical gravity, production GALAXY activation or Phylactery/SOVREP cutover. Live SOVMEM staging initialization remains a separately reviewed owner action with appropriate isolated staging-only credentials and verified provider database identity; production sovmem-main stays clean pending the future independently proven migration.

All six E-LANES, //PW:PRESERVE//, CANDIPULL/MEMSAV, individual operator provenance, HEATDEATH fallback and BIGBANG LOCKED remain unaffected. The original shared hurrisonferd repository is for source/tests ONLY and MUST NEVER contain the independent Turso tokens, real archived statements or future sovereign restore material.
