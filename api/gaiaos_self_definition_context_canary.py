"""Canary for bounded GaiaOS Council self-definition continuity discovery.

This proves semantic discoverability only. It does not create durable memory,
runtime identity adoption, or automatic loading.
"""

from __future__ import annotations

import json
from pathlib import Path

from gaiaos_context_runtime import build_context_packet

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "GaiaOS/SystemsOS/Core/DictionaryOS/Registry/GAIA-TERMS.v1.json"
GRAPH = ROOT / "GaiaOS/SystemsOS/Core/YggdrasilOS/Graph/GAIA-GRAPH.v1.json"
ARTIFACT = "GaiaOS/SystemsOS/Core/MemberContinuityOS/COUNCIL-SELF-DEFINITION-CONTINUITY.v1.md"
OBJECT_ID = "gaia.feature.council_self_definition_continuity"

registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
graph = json.loads(GRAPH.read_text(encoding="utf-8"))


def paths(packet: dict) -> list[str]:
    return [str(item.get("path", "")) for item in packet.get("context_pack", [])]


relevant = build_context_packet(
    registry,
    graph,
    "How should the Council members preserve identity, native prosody, handoff geometry, disagreement law, and cold-start reconstruction?",
    source="canary",
    limit=10,
    depth=1,
)

assert any(item.get("id") == OBJECT_ID for item in relevant.get("dictionary_candidates", [])), relevant
assert ARTIFACT in paths(relevant), paths(relevant)
assert any(
    edge.get("from") == OBJECT_ID or edge.get("to") == OBJECT_ID
    for edge in relevant.get("graph", {}).get("edges", [])
), relevant.get("graph", {})

unrelated = build_context_packet(
    registry,
    graph,
    "What color should I paint my notebook?",
    source="canary",
    limit=10,
    depth=1,
)

assert ARTIFACT not in paths(unrelated), paths(unrelated)
assert not any(item.get("id") == OBJECT_ID for item in unrelated.get("dictionary_candidates", [])), unrelated

for packet in (relevant, unrelated):
    laws = set(packet.get("laws", []))
    assert "REMOTE CONTEXT PACK != DURABLE MEMORY" in laws
    assert packet.get("effect_authority") == "NONE_READ_ONLY"
    assert packet.get("authority") == "NAOMI"

print("GAIAOS_COUNCIL_SELF_DEFINITION_CONTEXT_CANARY_PASS")
print("RELEVANT_PATH_SELECTED", ARTIFACT in paths(relevant))
print("UNRELATED_PATH_SELECTED", ARTIFACT in paths(unrelated))
