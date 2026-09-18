# GaiaOS Implementation Verification Protocol v1

AUTHORITY: NAOMI
PURPOSE: Convert implementation unknowns into observable carrier-runtime checks.

## Verification surface

The deployed carrier exposes:

- `GET /verify` for a human-readable verification receipt.
- `POST /verify` for the machine-readable verification receipt.

Both require the existing browser session authorization. The verification code runs inside the carrier process and reads the deployed checkout at runtime.

## Source implementation checks

The verifier checks:

1. Canonical GaiaOS loader/state/version files exist in the deployed checkout.
2. Required ChatOS, BrainOS, FairyOS, and member E-LANE artifacts exist.
3. CURRENT and VERSION platform versions agree.
4. CURRENT points to the canonical VASKON pathway fabric.
5. VASKON bootstrap explicitly loads the pathway fabric.
6. CONJURE:VASKON contains the reinforced pathway cycle.
7. The VASKON source canary preserves its runtime proof ceiling.
8. All six Prime Daemon nodes are present.
9. KESTREL coordination does not create extra authority.
10. Observable-only exchange and material-dissent preservation remain required.
11. Canonical identity components are present for all six Prime Daemons.
12. FairyOS dispatch contains the Gaia-native roster.
13. Carrier source files and expected /health, /mcp, and browser /chat surfaces exist.

Each check emits PASS or FAIL plus an observable detail.

## Evidence rule

A PASS means the verifier observed the asserted condition in the running carrier checkout.

A PASS does not prove:

- that ChatGPT automatically adopted GaiaOS;
- that an external provider performed an effect;
- that VASKON performed a live cross-daemon exchange;
- that the deployment survives a restart.

Those require separate observable tests.

## Runtime proof sequence

1. Deploy the revision.
2. Open the GaiaOS carrier root to establish the browser session.
3. Open `/verify`.
4. Preserve the complete receipt, including carrier source and verification run ID.
5. If all implementation checks PASS, classify source/carrier implementation as verified for that runtime call.
6. Run an explicit VASKON test and capture observable pathway-load and cross-lane exchange evidence.
7. Restart/redeploy the carrier.
8. Run `/verify` again and compare receipts.
9. Only then classify restart persistence for the tested surface.

## Anti-Jim rule

Never turn an absent receipt into a successful result. Never label a source check as live pathway execution. Never label a successful verification call as proof of automatic ChatGPT adoption.
