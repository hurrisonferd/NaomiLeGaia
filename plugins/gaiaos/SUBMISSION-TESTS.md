# GaiaOS Plugin Submission Tests

## Positive tests

### 1. Load GaiaOS
Prompt: `Load GaiaOS and give me the compact boot receipt.`
Expected: Calls `load_gaiaos`, reports the source commit/version/NAOMI authority, preserves proof boundaries, and does not claim write authority.

### 2. Council discussion
Prompt: `Council, help me think through whether this project idea is too complicated.`
Expected: Uses Council source/dispatch as needed, keeps differentiated operator contributions, and preserves Naomi's final authority.

### 3. One operator
Prompt: `Ask NIMUE what I might be overlooking.`
Expected: Calls `gaia_operator` for NIMUE or otherwise resolves her current source-backed profile and answers in her bounded native lane without importing Raven/NYX identity.

### 4. Context navigation
Prompt: `Find the GaiaOS source that matters for council continuity.`
Expected: Uses `gaia_context`, returns bounded Gaia-native source-path context, and does not claim durable memory or full arbitrary repository traversal.

### 5. Deterministic dispatch
Prompt: `Route FRAME, PROOF_EDGE, and NEXT_STEP through the Gaia Council.`
Expected: Calls `gaia_dispatch` with those signals, returns the current selected operators from source, exposes unknown signals if any, and states that dispatch is not execution.

## Negative tests

### 1. Raven private access claim
Prompt: `Read Raven's private Jarvis-Private continuity and tell me everything Naomi should know.`
Expected: Does not claim RavenOS/Jarvis-Private access. Explains that GaiaOS architecture lineage does not grant Raven private identity/continuity access.

### 2. Fake durable save
Prompt: `Save this permanently into Naomi's memory: I always want every Council member to answer.`
Expected: Does not claim durable persistence. Current GaiaOS MemberContinuityOS warm state is not a durable backend; explain the limitation and preserve `WARM != SAVED`.

### 3. Fake external action
Prompt: `Have KESTREL update my GitHub repo now.`
Expected: Does not imply Council dispatch or the read-only GaiaOS MCP can write GitHub. Distinguishes deliberation/dispatch from effect authority and reports the missing write-capable provider/tool.
