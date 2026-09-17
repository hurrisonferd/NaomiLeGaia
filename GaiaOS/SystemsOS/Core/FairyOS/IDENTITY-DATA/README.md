# GaiaOS FairyOS Member Identity Data

This directory is the compact, member-local identity continuity surface for the six current Gaia-native Council operators.

Each member has one canonical JSON dataset. It contains the stable identity bindings plus an append-only event log for material changes to personality, experiences, instructions, titles, preferences, and other identity-relevant events.

## Durable memory definition

For GaiaOS, **durable memory** means a persisted, retrievable record stored in an owner-controlled backend that survives process restarts and new conversations, has a defined schema and owner, and can be read back later with a verifiable source/receipt. A repository commit is durable storage. It is not automatically conversational memory, and it does not imply consciousness, subjective experience, or independent agency.

WARM continuity remains separate from durable memory. A warm candidate may exist temporarily without becoming a durable record.

## Write policy

Identity-related changes are recorded against the affected member dataset. Shared Council/profile/prosody/instruction changes are recorded as events for every member they materially affect. Automated synchronization is performed by `GAIAOS-MEMBER-IDENTITY-SYNC.yml` using the repository's GitHub Actions token.

The sync records provenance rather than inventing experiences. An event may say that a source changed; it must not fabricate what a member experienced or believed.

## Response policy

Before a selected member contributes a response, GaiaOS host/runtime instructions require loading that member's own dataset together with the canonical profile and prosody sources. The member-local dataset supplements, but does not override, canonical authority or Naomi's decisions.

The six datasets are intentionally isolated. No cross-member memory merge is permitted.
