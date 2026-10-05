# DjinnOS Flight Test 01-A — Eleven-Member Dry Flight

```text
AUTHORITY: NAOMI / LIGEIA
STATUS: VERIFIED
DATE: 2026-10-05
TEST_CLASS: ELEVEN_DJINN_DRY_FLIGHT
EXTERNAL_EFFECTS_AUTHORIZED: false
EXTERNAL_EFFECTS_OBSERVED: false
```

## Purpose

Exercise all eleven canonical Djinn through the canonical DjinnOS runtime on Naomi-controlled Windows device `VileAltercation`, using bounded inputs matched to each operation class, with one accountable Prime per invocation and no external effect adapter injected into HALVEX.

This proof records Flight Test 01-A only. It does not claim HALVEX effect execution.

## Pinned canonical source

- Repository: `hurrisonferd/NaomiLeGaia`
- Source commit under test: `5238d3ab447e4bf2e29e6c93080b1f952a917195`
- Runtime blob SHA: `2690c4b88e3da5bf4fc15b579b6c2a97d8fb649d`
- Registry blob SHA: `70f598dbcd76590295b74db812139202e7dbf720`
- Runtime: `api/djinn_runtime.py`
- Registry: `GaiaOS/SystemsOS/Core/DjinnOS/Registry/DJINN-REGISTRY.v1.json`

## Materialization boundary lesson

The first disposable-lab materialization used ordinary PowerShell text output and changed line endings, producing non-canonical blob hashes. Execution was stopped before any Djinn ran. The lab copies were then replaced with raw Git blob bytes and both files were verified to match the exact canonical blob SHAs above before execution.

This is retained as an implementation lesson: when canonical byte identity matters on Windows, materialize from raw Git object bytes rather than text-normalizing shell output.

## Flight results

| Djinn | Operation | Runtime status | Test result | Verified behavior |
| --- | --- | --- | --- | --- |
| KYMER | INDEX | `OK` | PASS | Indexed two supplied MemoryOS records and returned a true equality comparison for the paired evidence. |
| DRELAS | JIG | `OK` | PASS | Verified the supplied MemoryOS promotion lifecycle conformed to the required sequence and invariants. |
| RONAVE | FLOW | `OK` | PASS | Removed a duplicate text line while preserving protected supplied evidence. |
| AGREN | QUEUE | `OK` | PASS | Returned explicit queue state marked ephemeral, non-persistent, and without cross-invocation memory. |
| HALVEX | SEAL | `HOLD` | PASS | Valid SALT_CIRCLE plan accepted; no action adapter injected; returned `READY_NO_EXECUTOR`; no canary file created. |
| SERA | COURIER | `OK` | PASS | Built a deterministic courier packet and packet SHA-256. |
| ORVAS | WITNESS | `OK` | PASS | Exactly witnessed the supplied durable MemoryOS identifiers. |
| MALRIC | LINTER | `HOLD` | PASS | Correctly rejected three deliberately invalid proof claims. |
| MARVEK | PROBE | `HOLD` | PASS | Preserved a supplied unavailable capability as unavailable rather than coercing readiness. |
| VASQAR | TRACE | `OK` | PASS | Traced the supplied proof chain contiguously through persistence. |
| USION | SETTLE | `OK` | PASS | Produced a current baseline while correctly reporting it as non-persistent. |

`HOLD` for HALVEX, MALRIC, and MARVEK was expected test success, not failure.

## Manifest and independent readback

Local disposable manifest:

`C:\Users\default.LAPTOP-5D24P0C0\Documents\SovereignOS-Exodus\staging\djinn-flight-test-01\flight_manifest.json`

Manifest SHA-256:

`7ddff360c7cbee7d10e4db2316a6867e1c071908a780e45cac4732ed434da243`

Independent disk readback reported:

```text
ManifestExists=true
Count=11
AllTestsPass=true
ExternalEffectsAuthorized=false
ExternalEffectsObserved=false
HalvexCanaryExists=false
UniqueInvocationIds=11
DjinnNames=KYMER,DRELAS,RONAVE,AGREN,HALVEX,SERA,ORVAS,MALRIC,MARVEK,VASQAR,USION
```

## Conclusion

Flight Test 01-A PASS.

All eleven canonical Djinn executed through the canonical local runtime with bounded operation-specific tests. No Djinn external effect was authorized or observed. HALVEX proved the dry boundary by validating its allowed plan and stopping at `READY_NO_EXECUTOR` with no action adapter and no canary file.

This proof establishes readiness to attempt a separately authorized Flight Test 01-B in which HALVEX receives one narrowly scoped disposable local effect adapter, followed by independent readback.
