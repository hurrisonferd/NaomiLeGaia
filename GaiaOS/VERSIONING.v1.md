# GaiaOS Versioning v1

```text
AUTHORITY: NAOMI
STATUS: ACTIVE VERSIONING CONTRACT
```

## Version law

```text
PLATFORM VERSION != SUBSYSTEM VERSION
VERSION != SHA
NEW SHA != NEW VERSION
PLATFORM COMPOSITION != OWNER COLLAPSE
SOURCE SETTLED != RUNTIME PROVEN
```

Subsystems keep their own CURRENT pointers. GaiaOS `CURRENT.json` bumps only when the platform composition coordinate changes materially.

## Promotion rule

Promote a subsystem into GaiaOS `CURRENT.json` only after:

```text
its source coordinates exist
its canary tests pass deterministically
Naomi accepts the roster / identity material
```

## Current

```text
GaiaOS v0.001.000
```