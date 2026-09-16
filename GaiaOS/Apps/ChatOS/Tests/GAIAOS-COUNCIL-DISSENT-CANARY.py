#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNTIME = HERE.parent / "Runtime" / "COUNCIL-DISSENT-REDUCER.v1.py"

spec = importlib.util.spec_from_file_location("gaiaos_council_dissent_reducer", RUNTIME)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

packet = module.reduce(
    "Should GaiaOS add a new interface?",
    [
        {"speaker": "VERA", "stance": "QUESTION", "text": "What problem is the interface solving?"},
        {"speaker": "ORIN", "stance": "PROPOSE", "text": "Prototype the smallest useful surface."},
        {"speaker": "ANVIL", "stance": "OBJECT", "text": "Do not imply permissions the interface does not have."},
        {"speaker": "KESTREL", "stance": "AGREE", "text": "Ship only after the source route is explicit."},
        {"speaker": "ANVIL", "stance": "OBJECT", "text": "Do not imply permissions the interface does not have."}
    ],
)

assert packet["authority"] == "NAOMI"
assert packet["law"] == "SYNTHESIS_MAY_NOT_DELETE_DISSENT"
assert packet["participants"] == ["ANVIL", "KESTREL", "ORIN", "VERA"]
assert len(packet["minority_objections"]) == 1
assert len(packet["unique_proposals"]) == 1
assert packet["unresolved_questions"] == ["What problem is the interface solving?"]
assert len(packet["source_contributions"]) == 4

print("GAIAOS_COUNCIL_DISSENT_CANARY_PASS")
