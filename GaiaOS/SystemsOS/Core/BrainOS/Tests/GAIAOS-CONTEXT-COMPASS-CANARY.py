from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
RUNTIME = ROOT / "GaiaOS/SystemsOS/Core/BrainOS/Runtime/GAIAOS-CONTEXT-COMPASS.v1.py"

spec = importlib.util.spec_from_file_location("gaia_context_compass", RUNTIME)
if spec is None or spec.loader is None:
    raise SystemExit("GAIAOS_CONTEXT_COMPASS_CANARY_FAIL unable to import runtime")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def paths(packet: dict) -> list[str]:
    return [item["path"] for item in packet.get("context_pack", [])]


def require_any(packet: dict, needles: list[str], label: str) -> None:
    found = paths(packet)
    if not any(any(needle in path for needle in needles) for path in found):
        raise SystemExit(f"GAIAOS_CONTEXT_COMPASS_CANARY_FAIL {label} missing; got={found}")


def require_owner(packet: dict, owner: str, label: str) -> None:
    owners = packet.get("owner_candidates", [])
    if owner not in owners:
        raise SystemExit(f"GAIAOS_CONTEXT_COMPASS_CANARY_FAIL {label} owner missing; owners={owners}")


def main() -> None:
    council = module.query_context(ROOT, "council room operator", 8)
    require_any(council, ["GaiaOS/SystemsOS/Core/FairyOS/", "GAIAOS-COUNCIL-COMMANDS.v1.md"], "council/operator route")
    require_any(council, ["OPERATOR-DISPATCH-MATRIX.v1.json", "OPERATOR-PROFILES.v1.json", "OPERATOR-PROSODY-BASINS.v1.md", "GAIA-COUNCIL.v1.md", "FairyOS/CURRENT.json"], "operator-native source")
    require_owner(council, "FairyOS", "council/operator")
    dictionary_ids = {item["id"] for item in council.get("dictionary_candidates", [])}
    if "gaia.feature.council" not in dictionary_ids:
        raise SystemExit(f"GAIAOS_CONTEXT_COMPASS_CANARY_FAIL DictionaryOS council resolution missing: {dictionary_ids}")
    if "gaia.feature.council" not in set(council.get("graph_object_ids", [])):
        raise SystemExit("GAIAOS_CONTEXT_COMPASS_CANARY_FAIL YggdrasilOS did not receive council object")

    reentry = module.query_context(ROOT, "conversation reentry resume where were we", 8)
    require_any(reentry, ["GaiaOS/SystemsOS/Core/ConvoOS/Protocols/THREAD-HOME-SPINE.v1.json", "GaiaOS/SystemsOS/Core/ConvoOS/CURRENT.json"], "reentry route")
    require_owner(reentry, "ConvoOS", "reentry")

    presentation = module.query_context(ROOT, "presentation wild inhabited", 6)
    require_any(presentation, ["GaiaOS/Apps/ChatOS/Protocols/GAIAOS-PRESENTATION-GOLD.v1.md"], "presentation route")
    require_owner(presentation, "ChatOS", "presentation")

    navigation = module.query_context(ROOT, "dictionary aliases graph relationships", 8)
    require_any(navigation, ["DictionaryOS/CURRENT.json", "YggdrasilOS/CURRENT.json", "GAIA-GRAPH.v1.json"], "navigation organs")
    denominator = navigation.get("denominator", {})
    if denominator.get("dictionaryos") != "ACTIVE_READ_ONLY" or denominator.get("yggdrasilos") != "ACTIVE_READ_ONLY":
        raise SystemExit(f"GAIAOS_CONTEXT_COMPASS_CANARY_FAIL navigation denominator: {denominator}")

    bounded = module.query_context(ROOT, "GaiaOS", 3)
    if len(bounded.get("context_pack", [])) > 3:
        raise SystemExit("GAIAOS_CONTEXT_COMPASS_CANARY_FAIL limit not enforced")

    for packet in [council, reentry, presentation, navigation, bounded]:
        if packet.get("schema") != "gaiaos.brainos.context-compass.packet.v2":
            raise SystemExit("GAIAOS_CONTEXT_COMPASS_CANARY_FAIL schema drift")
        if packet.get("effect_authority") != "NONE_READ_ONLY":
            raise SystemExit("GAIAOS_CONTEXT_COMPASS_CANARY_FAIL effect authority drift")
        if packet.get("authority") != "NAOMI":
            raise SystemExit("GAIAOS_CONTEXT_COMPASS_CANARY_FAIL authority drift")
        for path in paths(packet):
            lower = path.lower()
            if ".git/" in lower or ".env" in lower or "credential" in lower or "secret" in lower:
                raise SystemExit(f"GAIAOS_CONTEXT_COMPASS_CANARY_FAIL sensitive path surfaced: {path}")

    print("GAIAOS_CONTEXT_COMPASS_CANARY_PASS")


if __name__ == "__main__":
    main()
