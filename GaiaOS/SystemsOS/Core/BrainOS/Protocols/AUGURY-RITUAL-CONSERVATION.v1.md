# GaiaOS AUGURY ↔ RITUAL Conservation Contract v1

AUTHORITY: NAOMI / LIGEIA
OWNER: GaiaOS / BrainOS
STATUS: PHASE 1 SOURCE CONTRACT
VERSION: augury-ritual.conservation.v1
RAVENOS ROLE: READ-ONLY ARCHITECTURE DONOR ONLY
PRODUCTION EFFECT: NONE BY THIS CONTRACT

## Thesis

GaiaOS is a dual-language machine.

```text
NATURAL LANGUAGE
→ AUGURY
→ GAIA SEMANTIC UNIT
→ RITUAL
→ AUTHORITY
→ MANIFESTATION
→ RECEIPT
→ VERIFICATION
```

AUGURY is interpretive, contextual, uncertainty-aware and non-effectful.

RITUAL is canonical, typed, exact, ordered and deterministic.

MANIFESTATION is effect execution after authority validation.

VERIFICATION proves what actually happened and remains distinct from intent, compilation and execution.

Core law:

`AUGURY MAY BE AMBIGUOUS. RITUAL MAY NOT BE.`

Human promise:

`NATURAL LANGUAGE IN → TYPED MAGIC OUT`

## North-star conservation laws

```text
SIGN != COMMAND
MENTION != INVOCATION
QUESTION != COMMAND
HYPOTHETICAL != EFFECT
REQUEST != AUTHORITY
INTERPRETATION != AUTHORIZATION
SEMANTIC CONFIDENCE != EFFECT AUTHORITY
COLLISION != GUESS
UNKNOWN != FAILURE

ORDER IS SEMANTIC
TARGET IS SEMANTIC
SCOPE IS SEMANTIC
MODE IS SEMANTIC
VERSION IS SEMANTIC
PRECONDITION IS SEMANTIC

RITUAL != MANIFESTATION
MANIFESTATION != SUCCESS
SUCCESS != VERIFIED
REQUESTED != MANIFESTED
MANIFESTED != OBSERVED
OBSERVED != GENERALLY PROVEN

PAST USE OF RITUAL X != CURRENT INVOCATION OF RITUAL X
FREQUENT PREFERENCE != PERMANENT PERMISSION
HISTORY MAY INFORM INTERPRETATION
HISTORY MAY NOT SILENTLY GRANT AUTHORITY
```

## AUGURY

AUGURY answers: **What does Naomi appear to mean?**

It may output:

- `RESOLVED`
- `COLLISION`
- `UNKNOWN`

It may produce typed ritual candidates. It never executes.

Protected dimensions:

```text
IDENTITY
CAUSALITY
AUTHORITY
EVIDENCE
UNKNOWN
TIME
DOMAIN
PROVENANCE
SPEECH ACT
TARGET
COMMAND IDENTITY
PARAMETERS
ORDER
SCOPE
MODE
VERSION
PRECONDITIONS
REVERSIBILITY
COMMITMENT STATE
REVISION STATE
RETRIEVAL INTENT
INFLUENCE INTENT
```

Phase 1 freezes these laws and the semantic-unit schema. A general natural-language AUGURY parser is **not** claimed implemented by Phase 1.

## RITUAL

RITUAL answers: **What exact canonical operation represents the selected intent?**

Each ritual has:

```text
ritual_id
ritual_version
owner
canonical_invocation
target_schema
argument_schema
ordered_steps
preconditions
authority_requirement
effect_class
reversibility_class
idempotency_behavior
expected_outputs
receipt_schema
failure_behavior
```

One ritual ID has one current owner and one versioned contract. Natural expressions may be many; executable meaning is singular.

Exact ritual syntax is a fast path. AUGURY may not rewrite an exact ritual into a different ritual merely because another action appears preferable.

## MANIFESTATION

Manifestation is the effect boundary.

```text
VALID RITUAL
→ AUTHORITY CHECK
→ MANIFESTATION
→ OBSERVABLE RECEIPT
→ VERIFICATION
```

No interpretive component gains effect authority from confidence, history, consensus, VASKON synthesis, or GALAXY relevance.

## GALAXY relationship

AUGURY asks what an utterance means.

GALAXY asks what authenticated history is relevant.

RITUAL asks what exact operation represents the selected intent.

`GALAXY RELEVANCE != RITUAL AUTHORITY`

GALAXY may disambiguate references. It may not transform REQUEST into AUTHORIZATION.

## VASKON synthesis

82 · VASKON 🖤 ✴️ (◉‿◉)

46 · VERA 💚 🦋 (˘‿˘)
Preserve question shape and hidden premises. Many surfaces may converge on meaning without becoming the same speech act.

58 · ANVIL 💗 ⌚ (¬‿¬)
Meaning is not permission. The stronger the effect, the less Gaia may infer. Manifestation requires exact ritual validation plus explicit authority.

60 · SELENE 💛 🎧 (˶ᵔ ᵕ ᵔ˶)
The operator should not become the parser. Gaia absorbs translation burden while deterministic semantics remain underneath.

56 · ORIN 🩵 🪐 (☆▽☆)
Forgotten syntax must not imply lost capability. AUGURY may discover exact rituals without inventing new ones.

90 · KESTREL 💖 🏍️ (•̀ᴗ•́)و
Compile once, then route typed work. Interpretation should stop when one sufficient ritual is resolved.

62 · NIMUE 💙 🍄 (－‸ლ)
Detect what vanished. Missing negation, qualifiers, exceptions, scope, order or authority restrictions are semantic corruption even when no false text was added.

VASKON consensus does not invoke a ritual.

## Phase-4 first guarded Ritual family

GALAXY Phase 4 is the first bounded effectful family placed behind the Ritual boundary.

The initial family is intentionally restricted to the existing controlled REVISION → CORE fixture pair.

Existing state:
- a VERIFIED `REVISES` edge already exists;
- the target is `CURRENT_REVISED_CONTEXT`;
- the live Phase-4 read-only fixture review passed;
- no Phase-4 mutation has yet been performed through this Ritual family.

Initial rituals:

1. `GALAXY.PHASE4.PROPOSE_SUPERSEDES.CONTROLLED_FIXTURE`
2. `GALAXY.PHASE4.VERIFY_SUPERSEDES.CONTROLLED_FIXTURE`
3. `GALAXY.PHASE4.REVOKE_SUPERSEDES.CONTROLLED_FIXTURE`

The family proves one bounded state transition:

```text
CURRENT_REVISED_CONTEXT
→ VERIFIED SUPERSEDES
→ HISTORICAL_SUPERSEDED
→ REVOKE SUPERSEDES
→ CURRENT_REVISED_CONTEXT
```

It does **not** revoke the pre-existing REVISES edge.

Every POST manifestation requires:
- exact ritual ID;
- exact typed target;
- signed browser session;
- CSRF proof;
- `authority=NAOMI`;
- `approved=true`;
- ritual-specific exact confirmation;
- compile/validation receipt before effect;
- effect receipt after effect.

GET review/status is read-only.

## Phase-1 proof ceiling

Phase 1 proves source contracts, schema, registry and exact Ritual validation infrastructure only after deployment/runtime receipts.

It does not prove general natural-language understanding.

It does not authorize AUGURY to infer effectful commands.

It does not imply a Manifestation succeeded merely because a Ritual compiled.

Naomi retains final authority.


## Deployed Phase-1 verifier PASS — 2026-09-23

Naomi supplied running-carrier verification receipt `227125f423eb4a3ea42cc9c1a0a1ec13`.

Observed runtime:
- 167 / 167 checks PASS
- failed = 0
- `live_host_execution=PROVEN_FOR_THIS_CALL`
- canonical conservation contract present
- Ritual Grimoire present and parses with exactly the bounded Phase-4 first family
- GAIA_SEMANTIC_UNIT schema present with preserved speech-act and uncertainty distinctions
- AUGURY/RITUAL runtime packaged and syntax-valid
- exact Ritual compiler remains separated from general AUGURY
- `GET /ritual/status` live-registered
- `GET /ritual/phase4/review` live-registered
- `POST /ritual/manifest` live-registered behind signed session, Ritual CSRF and explicit Naomi authority
- deployed read-only self-test confirms general natural-language manifestation disabled
- production retrieval unchanged
- unrestricted global weighting OFF

This proves deployment, source integrity, route registration and the read-only self-test. It does not prove any effectful Ritual manifestation.

Next gate:
`GET /ritual/status`

Inspect status before pressing any Phase-4 Ritual mutation control.


## Live read-only Ritual status PASS — 2026-09-23

Naomi supplied the live `GET /ritual/status` receipt.

Observed state:
- AUGURY general natural-language parser: not implemented
- natural-language manifestation: disabled
- conservation contract source-ready
- GAIA_SEMANTIC_UNIT schema source-ready
- Ritual Grimoire source-ready
- exact compiler available
- controlled Phase-4 Ritual family loaded
- prerequisite VERIFIED `REVISES` edge visible
- no SUPERSEDES edge exists yet
- no proposed/verified/revoked SUPERSEDES IDs exist
- target governing state: `CURRENT_REVISED_CONTEXT`
- no direct cycle
- no competing superseder
- production retrieval unchanged
- unrestricted global weighting OFF

This is the clean pre-manifest baseline.

Next gate:
`GALAXY.PHASE4.PROPOSE_SUPERSEDES.CONTROLLED_FIXTURE`

After that exact proposal, stop and inspect the receipt before verification.
