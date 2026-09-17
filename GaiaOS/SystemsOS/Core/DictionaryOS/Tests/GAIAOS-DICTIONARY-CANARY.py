from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
RUNTIME = ROOT / "GaiaOS/SystemsOS/Core/DictionaryOS/Runtime/GAIAOS-DICTIONARY-RESOLVER.v1.py"

spec = importlib.util.spec_from_file_location("gaia_dictionary", RUNTIME)
if spec is None or spec.loader is None:
    raise SystemExit("GAIAOS_DICTIONARY_CANARY_FAIL import")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def require(subject: str, expected_id: str) -> None:
    packet = module.resolve_terms(ROOT, subject, 5)
    ids = [item["id"] for item in packet.get("candidates", [])]
    if expected_id not in ids:
        raise SystemExit(f"GAIAOS_DICTIONARY_CANARY_FAIL {subject!r} -> {ids}")
    if packet.get("effect_authority") != "NONE_READ_ONLY":
        raise SystemExit("GAIAOS_DICTIONARY_CANARY_FAIL authority drift")


def main() -> None:
    require("council room", "gaia.feature.council")
    require("where were we resume", "gaia.system.convoos")
    require("find context compass", "gaia.feature.context_compass")
    unknown = module.resolve_terms(ROOT, "qzxv totally absent phrase", 5)
    if not unknown.get("unknown"):
        raise SystemExit("GAIAOS_DICTIONARY_CANARY_FAIL unknown collapsed")
    print("GAIAOS_DICTIONARY_CANARY_PASS")


if __name__ == "__main__":
    main()
