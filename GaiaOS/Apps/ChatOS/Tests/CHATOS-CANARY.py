#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CHATOS = ROOT / "GaiaOS/Apps/ChatOS"
COMPILER_PATH = CHATOS / "Runtime/CHATOS-EVENT-COMPILER.v1.py"
SCHEMA_PATH = CHATOS / "Schemas/CHATOS-EVENT.v1.schema.json"
BRIDGE_PATH = CHATOS / "Protocols/CHATOS-BRAINOS-FAIRYOS-BRIDGE.v1.json"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)


def load_module():
    spec = importlib.util.spec_from_file_location("gaiaos_chatos_event_compiler_v1", COMPILER_PATH)
    require(spec is not None and spec.loader is not None, "compiler import spec failed")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


C = load_module()
schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
bridge = json.loads(BRIDGE_PATH.read_text(encoding="utf-8"))

require(schema["$id"] == "gaiaos.chatos.event.v1", "event schema id drift")
require(bridge["schema"] == "gaiaos.chatos.brainos-fairyos-bridge.v1", "bridge schema drift")
for rel in bridge["sources"].values():
    require((ROOT / rel).exists(), f"bridge source missing: {rel}")

stale = C.compile_event(
    phase="OBSERVE",
    claim_class="CONFIRMED",
    source_class="SOURCE_READ",
    summary="GaiaOS top-level pointer needs reconciliation against the freshly settled Naomi source.",
    signals=["STALE_STATE", "PROOF_EDGE"],
    source_main="TEST_MAIN",
    evidence_refs=["GaiaOS/CURRENT.json", "GaiaOS/SystemsOS/Core/FairyOS/CURRENT.json"],
    next_action="Reconcile GaiaOS runtime truth after ChatOS source canary passes.",
)
require(stale["schema"] == "gaiaos.chatos.event.v1", "event schema drift")
require(stale["effect_authority"] == "NONE_CHATOS_PRESENTATION_ONLY", "ChatOS authority regression")
require(stale["fairyos_dispatch"]["effect_authority"] == "NONE_RESOLVER_IS_READ_ONLY", "FairyOS authority regression")
require(stale["fairyos_dispatch"]["material_members"] == ["ANVIL", "NIMUE"], stale["fairyos_dispatch"])
require([p["expression"] for p in stale["fairyos_dispatch"]["member_packets"]] == ["REAL_TALK", "NOTED"], stale["fairyos_dispatch"])

again = C.compile_event(
    phase="OBSERVE",
    claim_class="CONFIRMED",
    source_class="SOURCE_READ",
    summary="GaiaOS top-level pointer needs reconciliation against the freshly settled Naomi source.",
    signals=["STALE_STATE", "PROOF_EDGE"],
    source_main="TEST_MAIN",
    evidence_refs=["GaiaOS/CURRENT.json", "GaiaOS/SystemsOS/Core/FairyOS/CURRENT.json"],
    next_action="Reconcile GaiaOS runtime truth after ChatOS source canary passes.",
)
require(stale["event_id"] == again["event_id"], "identical event inputs must produce stable event ids")

coordinator = C.compile_event(
    phase="DECIDE",
    claim_class="INFERRED",
    source_class="DERIVED",
    summary="The smallest next move is one bounded implementation step.",
    signals=["EXECUTION", "NEXT_STEP"],
    next_action="Run one bounded owner-native canary.",
)
require(coordinator["fairyos_dispatch"]["material_members"] == ["KESTREL"], coordinator["fairyos_dispatch"])
require(coordinator["fairyos_dispatch"]["member_packets"][0]["expression"] == "ON_IT", coordinator["fairyos_dispatch"])

explicit = C.compile_event(
    phase="HANDOFF",
    claim_class="INFERRED",
    source_class="DERIVED",
    summary="Explicit Orin exploration handoff.",
    explicit_members=["ORIN"],
)
require(explicit["fairyos_dispatch"]["material_members"] == ["ORIN"], explicit["fairyos_dispatch"])
require(explicit["fairyos_dispatch"]["member_packets"][0]["explicit"] is True, explicit["fairyos_dispatch"])

unknown = C.compile_event(
    phase="OBSERVE",
    claim_class="UNKNOWN",
    source_class="UNKNOWN",
    summary="A deliberately unknown signal must remain visible.",
    signals=["NOT_A_REAL_SIGNAL"],
    unknowns=["No owner-native interpretation exists for this signal."],
)
require(unknown["fairyos_dispatch"]["material_members"] == [], unknown["fairyos_dispatch"])
require(unknown["fairyos_dispatch"]["unknown_signals"] == ["NOT_A_REAL_SIGNAL"], unknown["fairyos_dispatch"])

account = C.compile_event(
    phase="OBSERVE",
    claim_class="ACCOUNT",
    source_class="USER_ACCOUNT",
    summary="Naomi reports that the visible tool chain feels stuck.",
    signals=["INTERFACE_FRICTION"],
)
require(account["claim_class"] == "ACCOUNT", "account evidence class changed")
require(account["fairyos_dispatch"]["material_members"] == ["KESTREL"], account["fairyos_dispatch"])

try:
    C.compile_event(
        phase="VERIFY",
        claim_class="CONFIRMED",
        source_class="TEST_RESULT",
        summary="This should fail because the evidence reference is missing.",
        signals=["PROOF_EDGE"],
    )
except ValueError as exc:
    require("evidence_ref" in str(exc), f"wrong missing-evidence error: {exc}")
else:
    raise AssertionError("CONFIRMED event without evidence_ref must fail")

render = C.render_checkpoint(stale)

require(any(line.startswith("CHATOS OBSERVE") for line in render), "checkpoint render missing phase line")
require(any(line.startswith("FAE ") for line in render), "checkpoint render missing operator projection")

print("GAIAOS_CHATOS_CANARY: PASS")
print("deterministic_event_ids=PASS claim/source validation=PASS fairyos_dispatch_reuse=PASS")
print("effect_authority=NONE_CHATOS_PRESENTATION_ONLY")