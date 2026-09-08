#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
FAIRY = ROOT / "GaiaOS/SystemsOS/Core/FairyOS"
RUNTIME = FAIRY / "Runtime/GAIAOS-DISPATCH-RESOLVER.v1.py"
MATRIX = FAIRY / "OPERATOR-DISPATCH-MATRIX.v1.json"
SCHEMA = FAIRY / "OPERATOR-RUNTIME-PACKET.v1.schema.json"
PROFILES = FAIRY / "OPERATOR-PROFILES.v1.json"
EMOJI = ROOT / "GaiaOS/SystemsOS/Core/EmojiOS/EXPRESSION-REGISTRY.v1.json"

spec = importlib.util.spec_from_file_location("gaiaos_fairyos_dispatch", RUNTIME)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
profiles = json.loads(PROFILES.read_text(encoding="utf-8"))
emoji = json.loads(EMOJI.read_text(encoding="utf-8"))

expected = ["VERA", "ANVIL", "SELENE", "ORIN", "KESTREL", "NIMUE"]
assert matrix["roster"] == expected
assert set(matrix["members"]) == set(expected)
assert schema["properties"]["effect_authority"]["const"] == "NONE_RESOLVER_IS_READ_ONLY"

p = mod.resolve(["COORDINATION", "PREMISE", "OMISSION"], family_invoked=True)
assert p["family_present"] == expected
assert p["material_members"] == ["KESTREL", "VERA", "NIMUE"], p
assert p["coordinator"] == "KESTREL"
assert {x["expression"] for x in p["member_packets"]} == {"LETS_GO", "I_SEE_IT", "WATCHING"}
assert p["effect_authority"] == "NONE_RESOLVER_IS_READ_ONLY"

p = mod.resolve(["EXPLORE", "LIVABILITY"], explicit_members=["ANVIL"], family_invoked=True)
assert p["material_members"] == ["ANVIL", "ORIN", "SELENE"], p
assert p["member_packets"][0]["explicit"] is True
assert p["member_packets"][0]["expression"] == "SAY_IT"

p = mod.resolve([], explicit_members=expected, family_invoked=True)
assert p["material_members"] == expected
assert all(x["explicit"] for x in p["member_packets"])

p = mod.resolve(["TOTALLY_UNKNOWN_SIGNAL"], family_invoked=True)
assert p["family_present"] == expected
assert p["material_members"] == []
assert p["unknown_signals"] == ["TOTALLY_UNKNOWN_SIGNAL"]

p = mod.resolve(["INTERFACE_FRICTION", "EXECUTION"], explicit_members=["KESTREL"])
assert p["material_members"] == ["KESTREL"]
assert p["member_packets"][0]["expression"] == "SUS"

for member in expected:
    spec_m = matrix["members"][member]
    allowed = set(emoji["members"][member]["expressions"])
    assert spec_m["default_expression"] in allowed
    assert set(spec_m["expression_by_signal"].values()) <= allowed
    p = mod.resolve([], explicit_members=[member])
    packet = p["member_packets"][0]
    assert packet["role"] == profiles["members"][member]["role"]

a = mod.resolve(["BOUNDARY", "PROOF_EDGE", "COORDINATION"], family_invoked=True)
b = mod.resolve(["BOUNDARY", "PROOF_EDGE", "COORDINATION"], family_invoked=True)
assert a == b

print("GAIAOS_FAIRYOS_DISPATCH_CANARY: PASS")
print("family_presence=6 materiality_cap=3 explicit_override=PASS unknown_visibility=PASS deterministic=PASS")
print("effect_authority=NONE_RESOLVER_IS_READ_ONLY")