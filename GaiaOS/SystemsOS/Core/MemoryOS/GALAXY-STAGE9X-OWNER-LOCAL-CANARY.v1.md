# GALAXY Stage 9X: signed owner-local staging canary handoff

AUTHORITY: NAOMI / LIGEIA. STATUS: DRAFT SOURCE ONLY, stacked on 9W #98 and 9V #97 down through 9R #93. BIGBANG LOCKED. NO LIVE TURSO CONNECTION OR CREDENTIALS WERE USED BY THIS PR. NO PROD WRITE, MERGE, DEPLOY, DATA IMPORT, E-LANE WRITE OR REPOSITORY MIGRATION AUTHORIZED.

## What this adds

The existing Stage 9V driver already implements a signed ONE-CANARY staging operation and two-connection exact readback, but it lacked a guarded operator-facing invocation path. The Stage 9X module `api/galaxy_stage9x_owner_canary.py` is an explicit OWNER-LOCAL command that requires **three affirmative confirmations, private owner-only approval/signature/key files, an exact signed single-action HMAC manifest, and a fresh READ-ONLY preflight** before the existing canary probe may open its write connection. It does not import the production MemconOS runtime, expose an HTTP route or run automatically. It never receives the production token and can connect ONLY to the supplied staging endpoint. It does not create any database schema or insert any historical records.

In a LOCAL test with an injected connector, the result is always `HOLD_LOCAL_FIXTURE_NOT_REMOTE`, even if the test canary commits/reopens successfully. In a genuine direct libSQL run, a `PASS_REMOTE_STAGING_CANARY_REOPEN` means only that the supplied endpoint passed the preceding marker/canary SELECT and one exact signed staging-only canary was read back on a NEW connection (or an exact prior canary was replayed read-only). The result deliberately says `provider_database_separation_independently_verified=false` and `live_owner_identity_verified=false`; the three local confirmation flags are not independent attestations. A lost COMMIT acknowledgement or lost reopen readback returns a HOLD with unknown write outcome. Retry ONLY the exact same run ID and nonce before considering a new attempt.

All stdout is a bounded allowlisted receipt. No staging/production URL, auth token, raw staging UUID, statement, source archive, signing key or signature is printed; no workflow artifact containing credentials is created. Errors are reduced to fixed statuses. The separate Stage 9X CI workflow runs synthetic/local SQLite fixtures and the Stage 9V real-driver LOCAL contract, never a real Turso operation or operator-dispatch event.

## Prerequisites before any real owner-local invocation

1. Independently provision an EMPTY physically separate staging Turso database in Naomi's own account. Generate the Stage 9V owner-local setup bundle, manually install its staging-only identity marker and canary table in the NEW database only, and verify the new database's control-plane identity and aliases independently. Distinct URLs and a UUID marker are not enough. Do not copy production data or use the original Render/production token.
2. Review this source separately and execute it ONLY from Naomi's trusted workstation or the future owner-controlled SOVREP-Core installation. NEVER install independent staging secrets or HMAC keys in the original `hurrisonferd/NaomiLeGaia` repository, its GitHub Actions secrets or the chat. A source PR or passing CI does not grant live mutation authority.
3. Complete the standalone Stage 9V read-only preflight FIRST using a separate short-lived read-only staging token and preserve its redacted receipt privately. For the signed canary, obtain a separate narrowly scoped STAGING-only token that permits only the marker/canary SELECT and canary INSERT. Verify its actual provider scope independently.
4. Separately review and authorize exactly ONE staging canary. A trusted local signer creates a Stage 9V `gaiaos.galaxy.stage9v.one-canary-approval.v1` JSON file with authority `NAOMI`, target `SEPARATE_STAGING_TURSO_CANARY_ONLY`, action `WRITE_ONE_STAGING_CANARY`, the installed staging UUID, SHA-256 hashes of the canonical staging and production URLs, a unique run ID and the SHA-256 of a privately generated nonce. Sign canonical UTF-8 JSON (`json.dumps(manifest,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False)`) with HMAC-SHA256 using an independently held 32+-byte key. Put the exact manifest, its lowercase 64-hex signature and raw key in THREE DIFFERENT owner-only mode-0600 regular files OUTSIDE any source repository. This signature is a local technical gate, not proof of a person's identity. Owner identity and signing-key custody require separate, independently recorded evidence.
5. Set only `GAIAOS_STAGE9V_STAGING_URL`, `GAIAOS_STAGE9V_STAGING_TOKEN` (the separate STAGING canary token), `GAIAOS_STAGE9V_PRODUCTION_URL` (URL for comparison ONLY; NO production token), and `GAIAOS_STAGE9V_STAGING_UUID` privately. No values should appear in GitHub, chat or logs.

After ALL prerequisites, in an independently reviewed, trusted local checkout, the explicit command is:

```sh
python api/galaxy_stage9x_owner_canary.py \
  --approval-json "$HOME/private/stage9x/approved-canary.json" \
  --signature-file "$HOME/private/stage9x/approved-canary.sig" \
  --key-file "$HOME/private/stage9x/canary-signing.key" \
  --confirm-provider-identity \
  --confirm-separate-owner-approval \
  --confirm-one-staging-canary
```

The program checks the signed action BEFORE connecting, opens only staging for READ-ONLY preflight, then invokes Stage 9V's existing transactional one-canary implementation. Stage 9V rechecks identity before writing and after reopening. Never copy test fixture keys or tokens into the actual owner environment. An independent provider/admin attestation of the actual database IDs and aliases must accompany any real receipt; an operator confirmation flag does not establish it.

## Release HOLDs unchanged

- Live independent staging provision, control-plane database/alias attestation and owner credential/key custody are NOT performed here.
- No real signed staging canary was executed or remotely read back by source CI.
- No authenticated archive intake, canonical-schema staging Turso historical import, transactional durable gravity backfill or rolled-back deployed trial exists yet. Stage 9T/9U in-memory prototypes do NOT safely become remote importers by switching connection strings.
- Independent restart and replica durability, rated-vs-unrated real historic calibration, normal deployed browser/HEATDEATH/BIGBANG fallback, six separate E-LANES, `//PW:PRESERVE//`, CANDIPULL/MEMSAV and governed cutover all remain review gates.
- All stacked PRs stay DRAFT until Naomi separately reviews and approves source merges in dependency order. BIGBANG cannot be activated by this PR or any source-only test. After real GALAXY verification, Phylactery to SOVREP-Core remains an independently authorized migration.

SOURCE PASS != LIVE PROOF. STAGING CANARY != HISTORICAL MIGRATION. NO RELEASE WITHOUT NAOMI'S SEPARATE APPROVAL.
