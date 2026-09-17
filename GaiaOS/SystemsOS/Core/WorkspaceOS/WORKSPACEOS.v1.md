# WorkspaceOS v1

AUTHORITY: NAOMI
STATUS: ACTIVE SOURCE CONTRACT

WorkspaceOS is GaiaOS's bounded creation surface. It stores generated artifacts outside canonical source, records provenance and checksums, and provides versioned reads.

Artifact lifecycle:
PROPOSE → APPROVE → WRITE → HASH → RECEIPT → READ → VERIFY

Workspace storage is not automatically canonical GaiaOS source and is not automatically memory.

Writes require explicit Naomi approval. Every artifact records source/provenance metadata. WorkspaceOS must not claim an artifact was deployed, published, or externally delivered merely because it was written locally.

Deletion and replacement should remain recoverable through versioned artifacts where practical.
