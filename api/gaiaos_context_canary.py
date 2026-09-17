from __future__ import annotations

import json
from pathlib import Path

from gaiaos_context_runtime import build_context_packet

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "GaiaOS/SystemsOS/Core/DictionaryOS/Registry/GAIA-TERMS.v1.json"
GRAPH = ROOT / "GaiaOS/SystemsOS/Core/YggdrasilOS/Graph/GAIA-GRAPH.v1.json"


def main() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))

    council = build_context_packet(
        registry,
        graph,
        "council room operator",
        source="canary@local",
        limit=8,
        depth=1,
    )
    ids = {item["id"] for item in council.get("dictionary_candidates", [])}
    if "gaia.feature.council" not in ids:
        raise SystemExit(f"GAIAOS_CONTEXT_CARRIER_CANARY_FAIL dictionary route: {ids}")
    if "gaia.feature.council" not in council.get("graph", {}).get("known_object_ids", []):
        raise SystemExit("GAIAOS_CONTEXT_CARRIER_CANARY_FAIL graph route")
    paths = {item["path"] for item in council.get("context_pack", [])}
    if not any("COUNCIL" in path.upper() or "FAIRYOS" in path.upper() for path in paths):
        raise SystemExit(f"GAIAOS_CONTEXT_CARRIER_CANARY_FAIL context pack: {sorted(paths)}")

    unknown = build_context_packet(
        registry,
        graph,
        "qzxv absent subject",
        source="canary@local",
        limit=5,
        depth=1,
    )
    if not unknown.get("unknowns"):
        raise SystemExit("GAIAOS_CONTEXT_CARRIER_CANARY_FAIL unknown collapsed")

    for packet in [council, unknown]:
        if packet.get("authority") != "NAOMI":
            raise SystemExit("GAIAOS_CONTEXT_CARRIER_CANARY_FAIL authority drift")
        if packet.get("effect_authority") != "NONE_READ_ONLY":
            raise SystemExit("GAIAOS_CONTEXT_CARRIER_CANARY_FAIL effect authority drift")
        if packet.get("mode") != "SOURCE_PINNED_DICTIONARY_GRAPH_READ_ONLY":
            raise SystemExit("GAIAOS_CONTEXT_CARRIER_CANARY_FAIL mode drift")

    print("GAIAOS_CONTEXT_CARRIER_CANARY_PASS")


if __name__ == "__main__":
    main()
