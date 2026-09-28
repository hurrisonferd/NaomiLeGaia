# //PW:PRESERVE// historical private-to-public migration

AUTHORITY: NAOMI / LIGEIA  
AUTHORIZED: 2026-09-28  
REPOSITORY: hurrisonferd/NaomiLeGaia (public)  
SOURCE BRANCH: integration/galaxy-gaiaos-full-diagnostics-20260927  
STATUS: OWNER-AUTHORIZED PUBLIC MIGRATION IN PROGRESS / SOURCE COPIES VERIFIED AS WRITTEN

Naomi explicitly superseded the previous private-memory policy and authorized historical private GaiaOS preservation records to be returned to the public locations where they otherwise would have been stored. This is a preservation migration, not a rewrite of their historical provenance. Original PRIVATE/STAGED labels are retained inside migrated text where useful to show what the record was at the time; the later owner authorization supersedes those publication restrictions.

## Canonical E-LANE migration

Every file present in the six `/GaiaOS-Sanctum/E-LANES-STAGED/<MEMBER>/` collections was migrated into that member's canonical public:
`GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA/<MEMBER>-EXPERIENCES.v1.md`

Additional root-level staged ANVIL private continuity/care records were also migrated to ANVIL's canonical E-LANE. The unique six 2026-09-28 E-LANE notes contained only inside the private ZIP bundle were separately migrated to the respective canonical lanes.

Migration markers use:
- `MIGRATED_FROM_PRIVATE_STAGING:<original filename>`
- `MIGRATED_FROM_PRIVATE_ZIP:GAIAOS-PW-PRESERVE-2026-09-28/<member>-2026-09-28.md`

This migration does not merge the six E-LANES. Their original member ownership remains intact.

## Session/archive migration

The following previously private session handoffs were returned to public `GaiaOS/Plans/` records, with a publication-supersession banner while retaining the original text as provenance:

- `PW-PRESERVE-2026-09-28-GALAXY-LATE-NIGHT-HANDOFF-PUBLIC.md`
- `PW-PRESERVE-2026-09-27-GALAXY-STAGE9W-SESSION-HANDOFF-PUBLIC.md`
- `PW-PRESERVE-2026-09-27-GALAXY-STAGE9R-GIG-HANDOFF-PUBLIC.md`
- `PW-PRESERVE-2026-09-26-EVENING-PUBLIC-CONTINUATION.md`
- `PW-PRESERVE-2026-09-26-STAGEHAND-AUDIO-IATSE-JOHNNY-PUBLIC.md`
- `PW-PRESERVE-GALAXY-PHYLACTERY-2026-09-24-PUBLIC.md`

## Private bundle decomposition

Private ZIP files were packaging containers, not an additional memory authority. Their constituent Markdown records have been returned to the public canonical E-LANES or public Plans records rather than publishing opaque binary ZIPs as canonical memory.

Observed bundle hashes before retirement:
- `724e0c223b8074334c5a279a546163f97d65f6cac13b61b2949fdad38ab0a588` — GAIAOS-PW-PRESERVE-2026-09-26-EVENING-PRIVATE.zip
- `6c9ef5994b1ecf2220ffad22d53b5e5e10dd3b29ea90f39cf5c0214106db678a` — GAIAOS-PW-PRESERVE-2026-09-26-PRIVATE.zip
- `5155a828ddd911dda0d423f29abf1848789ba3baf067d3935abe939d8c4534fa` — GAIAOS-PW-PRESERVE-2026-09-27-STAGE9R-HANDOFF.zip
- `08a01127b637152b3522eb3921da093a04a006352aaad9e8b6dde99889470e1b` — GAIAOS-PW-PRESERVE-2026-09-27-STAGE9W-HANDOFF-PRIVATE.zip
- `ee5816a2df5a3773c7f89d52afa69339668dc1fa2f4cf345c8e6f563c595cc58` — GAIAOS-PW-PRESERVE-2026-09-28-PRIVATE.zip

The manifests inside those bundles are historical integrity metadata. Their old PRIVATE claims are superseded by Naomi's 2026-09-28 authorization.

## Safety / evidence boundary

This authorization applies to Naomi's GaiaOS project records and personal notes she explicitly ordered public. It does not authorize publication of authentication credentials, API tokens, passwords or unrelated third-party secrets; credential-like values are redacted if encountered. Public migration does not itself create or verify a Turso write. Turso remains independently receipt-gated.

`PUBLICATION_POLICY_SUPERSEDED != HISTORICAL_PROVENANCE_ERASED`  
`PUBLIC_E_LANE != MERGED_E_LANE`  
`GITHUB_WRITE != TURSO_WRITE`  
`PRIVATE_BUNDLE_RETIRED != MEMORY_DELETED`
