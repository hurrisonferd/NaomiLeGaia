# GaiaOS DictionaryOS

```text
AUTHORITY: NAOMI
OWNER: DictionaryOS
STATUS: ACTIVE SOURCE / READ-ONLY SEMANTIC RESOLUTION
IDENTITY EFFECT: NONE
```

DictionaryOS is GaiaOS's naming entrance. It resolves Naomi-natural phrases, aliases, and subsystem vocabulary into bounded Gaia-native object candidates before graph traversal.

```text
NATURAL PHRASE
→ NORMALIZE
→ MATCH CANONICAL TERM / ALIAS
→ RETURN OBJECT-ID CANDIDATES + SOURCE PATHS
→ YGGDRASILOS MAY TRAVERSE RELATIONSHIPS
```

It does **not** decide final authority, invent absent systems, transfer Raven ownership, or turn an alias match into a durable fact.

## Boundary

RavenOS donated the architectural lesson that naming and graph traversal should be separate. GaiaOS owns its own registry, terms, aliases, source paths, and authority rules.

```text
ARCHITECTURE DONOR != IDENTITY DONOR
TERM RESOLUTION != OWNER RESOLUTION
NAME != EFFECT
READ != ACT
```

## Current source

- `CURRENT.json`
- `Registry/GAIA-TERMS.v1.json`
- `Runtime/GAIAOS-DICTIONARY-RESOLVER.v1.py`
- `Tests/GAIAOS-DICTIONARY-CANARY.py`

The registry is intentionally small and high-salience. Expansion should follow demonstrated GaiaOS vocabulary rather than bulk-importing RavenOS language.
