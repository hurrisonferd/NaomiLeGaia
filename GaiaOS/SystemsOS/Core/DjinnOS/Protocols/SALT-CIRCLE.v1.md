# SALT_CIRCLE v1

SALT_CIRCLE is a host-level authorization perimeter used by mutation-capable Djinn choreography. It is not owned by HALVEX and is not a source of authority.

A valid circle binds one operation ID to:
- authority
- allowed operations
- allowed targets
- allowed scopes
- explicit forbiddens
- validity window
- single-use behavior

Rules:
1. Authority must be explicit. V1 accepts `NAOMI` only.
2. Allowed operations, targets, and scopes are exact allowlists.
3. Explicit forbiddens override every allowlist.
4. HALVEX may not enlarge, reinterpret, inherit, or infer the circle.
5. Expired circles fail closed.
6. Replayed operation IDs fail closed for the lifetime of the carrier process. Durable cross-restart replay prevention remains a host concern and is not falsely claimed by DjinnOS.
7. Any out-of-circle step returns `SALT_CIRCLE: BREACH_ATTEMPT`, halts the operation, and returns control to the calling Prime.
8. Passing validation is permission only for the explicitly bounded steps; it is not blanket permission for neighboring actions.
9. External effect adapters are dependency-injected by the trusted host. Public Djinn HTTP invocation never gains a mutation adapter merely because a circle validates.

Invariant: **No mutation crosses the SALT_CIRCLE.**
