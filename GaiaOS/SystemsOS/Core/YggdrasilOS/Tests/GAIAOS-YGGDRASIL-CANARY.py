from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
RUNTIME = ROOT / "GaiaOS/SystemsOS/Core/YggdrasilOS/Runtime/GAIAOS-YGGDRASIL-QUERY.v1.py"

spec = importlib.util.spec_from_file_location("gaia_yggdrasil", RUNTIME)
if spec is None or spec.loader is None:
    raise SystemExit("GAIAOS_YGGDRASIL_CANARY_FAIL import")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def main() -> None:
    packet = module.query_graph(ROOT, ["gaia.system.dictionaryos"], depth=2, limit=20)
    node_ids = {node["id"] for node in packet.get("nodes", [])}
    if "gaia.system.yggdrasilos" not in node_ids or "gaia.feature.context_compass" not in node_ids:
        raise SystemExit(f"GAIAOS_YGGDRASIL_CANARY_FAIL navigation chain missing: {sorted(node_ids)}")
    if packet.get("effect_authority") != "NONE_READ_ONLY":
        raise SystemExit("GAIAOS_YGGDRASIL_CANARY_FAIL authority drift")

    unknown = module.query_graph(ROOT, ["gaia.object.does-not-exist"], depth=1)
    if "gaia.object.does-not-exist" not in unknown.get("unknown_object_ids", []):
        raise SystemExit("GAIAOS_YGGDRASIL_CANARY_FAIL unknown collapsed")

    brain = module.query_graph(ROOT, ["gaia.system.brainos"], depth=1)
    if "GaiaOS/SystemsOS/Core/BrainOS/CURRENT.json" not in brain.get("source_paths", []):
        raise SystemExit("GAIAOS_YGGDRASIL_CANARY_FAIL source path missing")

    print("GAIAOS_YGGDRASIL_CANARY_PASS")


if __name__ == "__main__":
    main()
