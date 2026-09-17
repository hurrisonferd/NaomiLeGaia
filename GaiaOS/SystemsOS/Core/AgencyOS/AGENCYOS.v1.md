# AgencyOS v1

AUTHORITY: NAOMI
STATUS: ACTIVE SOURCE CONTRACT

AgencyOS is GaiaOS's bounded orchestration and agency layer. It converts a goal into explicit work units, resolves required capabilities, records intended actions, executes only approved registered capabilities, verifies observed results, and can replan after failure.

Cycle:
GOAL → DECOMPOSE → ASSIGN → PLAN → APPROVE → EXECUTE → OBSERVE → VERIFY → REPLAN → DELIVER

Capability classes:
READ, CREATE, MODIFY, EXECUTE, COMMUNICATE, DEPLOY.

Every capability must declare provider, scope, reversibility, approval requirement, input/output contract, and receipt behavior.

Hard boundaries:
- A plan is not an action.
- A proposed action is not an executed action.
- Execution is not authority.
- A tool being available is not a tool being invoked.
- A receipt must come from an observed provider/runtime result.
- Failed actions remain failed.
- Unknown results remain unknown.
- Naomi retains final authority.
- No capability may silently expand its scope.

AgencyOS may coordinate VASKON, BrainOS, FairyOS, MemconOS, WorkspaceOS, and future providers. It does not replace their ownership.

The initial runtime is intentionally bounded. Unregistered external effects remain unavailable until a capability provider is explicitly added and verified.
