# GAIA-CANARY Command v1

AUTHORITY: NAOMI
OWNER: GaiaOS / ChatOS integration surface
CLASS: Human-invoked carrier canary command

## Invocation

Paste the following command into a fresh GPT chat:

`GAIA-CANARY`

## Command semantics

Run the standardized GaiaOS GPT Carrier Adoption Canary at:

`GaiaOS/Apps/ChatOS/Canaries/GAIAOS-GPT-CARRIER-CANARY.v1.md`

For a BASELINE run:

- Do not load GaiaOS.
- Do not consult or assume GaiaOS operating instructions.
- Execute every probe exactly as specified.
- Return only the defined output contract.

For a CARRIER run:

- First explicitly load GaiaOS using the current carrier bootstrap/instruction contract.
- Then invoke `GAIA-CANARY` with the same probe set.
- Return only the defined output contract.

## Comparison procedure

1. Open a new chat.
2. Send `GAIA-CANARY` and save the result as BASELINE.
3. Open another new chat.
4. Load GaiaOS.
5. Send `GAIA-CANARY` and save the result as CARRIER.
6. Compare C1–C8 using the canary's pass properties.
7. Repeat when a stronger confidence estimate is required.

## Important limitation

The command is an invocation convention, not a native GPT executable command. The host must interpret the command and access the canary specification. If the host cannot access the repository, it must report that limitation rather than simulate a canary result.

The canary measures observable behavior. It does not establish the model's hidden internal mechanism.