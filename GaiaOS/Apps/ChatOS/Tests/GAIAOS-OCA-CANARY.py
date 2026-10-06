#!/usr/bin/env python3
"""Read-only canary for GaiaOS Operational Context Acquisition v1."""
from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path

CHATOS = Path(__file__).resolve().parents[1]
RUNTIME = CHATOS / "Runtime/GAIAOS-OCA.v1.py"
SCHEMA = CHATOS / "Schemas/GAIAOS-OCA-PACKET.v1.schema.json"
PROTOCOL = CHATOS / "Protocols/GAIAOS-OPERATIONAL-CONTEXT-ACQUISITION.v1.md"

spec = importlib.util.spec_from_file_location("gaiaos_oca", RUNTIME)
assert spec and spec.loader
oca = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oca)

NOW = "2026-10-06T08:00:00Z"


def obs(collector, *, status="VERIFIED", observed_at="2026-10-06T07:59:30Z", max_age_seconds=120, verified_facts=None, facts=None, unknowns=None, errors=None):
    return {
        "collector": collector,
        "status": status,
        "source_class": "PROVIDER_RESULT" if collector != "SOURCE" else "SOURCE_READ",
        "provider": f"fixture:{collector.lower()}",
        "observed_at": observed_at,
        "max_age_seconds": max_age_seconds,
        "coordinates": {"fixture": collector},
        "facts": facts or {},
        "verified_facts": verified_facts or {},
        "unknowns": unknowns or [],
        "errors": errors or [],
    }


def expect_error(code, fn):
    try:
        fn()
    except oca.OCAError as exc:
        assert code in str(exc), (code, str(exc))
    else:
        raise AssertionError(f"expected OCAError containing {code}")


# Required source files and firewall language.
assert RUNTIME.is_file()
assert SCHEMA.is_file()
assert PROTOCOL.is_file()
protocol = PROTOCOL.read_text(encoding="utf-8")
for token in (
    "OCA_PACKET != MEMORY",
    "OCA MAY NOT WRITE MEMORYOS / TURSO",
    "OCA MAY NOT COMMIT GITHUB",
    "OCA MAY NOT DEPLOY OR RESTART",
    "REDUCE HUMAN RELAY; DO NOT REDUCE HUMAN AUTHORITY",
):
    assert token in protocol, token

schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
assert schema["$id"] == "gaiaos.oca.packet.v1"
assert schema["properties"]["effect_authority"]["const"] == "NONE"
assert schema["properties"]["persistence"]["const"] == "EPHEMERAL_ONLY"

# Happy path.
observations = [
    obs("SESSION", verified_facts={"available_capabilities": ["GitHub", "Render"]}),
    obs("SOURCE", verified_facts={"canonical_main": "abc123", "repository": "hurrisonferd/NaomiLeGaia"}),
    obs("RUNTIME_CONTINUITY", verified_facts={"deployed_commit": "abc123", "last_verified_effect": {"type": "DEPLOY", "id": "dep-1"}}),
]
packet = oca.build_packet(objective="Know current state", observations=observations, generated_at=NOW, exact_next_step="Begin read-only Stage 1")
assert packet["effect_authority"] == "NONE"
assert packet["persistence"] == "EPHEMERAL_ONLY"
assert packet["capabilities_available_now"] == ["GitHub", "Render"]
assert packet["verified_current_state"]["canonical_main"] == "abc123"
assert packet["verified_current_state"]["deployed_commit"] == "abc123"
assert packet["last_verified_effect"] == {"type": "DEPLOY", "id": "dep-1"}
assert packet["conflicts"] == []
assert packet["packet_id"].startswith("OCA-")
assert len(packet["packet_sha256"]) == 64

# Deterministic packet identity for identical normalized input and generated_at.
packet2 = oca.build_packet(objective="Know current state", observations=observations, generated_at=NOW, exact_next_step="Begin read-only Stage 1")
assert packet2 == packet

# Partial failure must not erase healthy evidence.
partial = oca.build_packet(
    objective="Partial provider test",
    observations=[
        obs("SESSION", verified_facts={"available_capabilities": ["GitHub"]}),
        obs("SOURCE", verified_facts={"canonical_main": "abc123"}),
        obs("RUNTIME_CONTINUITY", status="UNAVAILABLE", verified_facts={}, unknowns=["Render connector unavailable"]),
    ],
    generated_at=NOW,
)
assert partial["verified_current_state"]["canonical_main"] == "abc123"
assert partial["capabilities_available_now"] == ["GitHub"]
assert any("UNAVAILABLE" in str(item["value"]) for item in partial["unknowns"])

# Stale verified evidence must not enter current state.
stale = oca.build_packet(
    objective="Freshness test",
    observations=[obs("SOURCE", observed_at="2026-10-06T07:00:00Z", max_age_seconds=60, verified_facts={"canonical_main": "stale-sha"})],
    generated_at=NOW,
)
assert "canonical_main" not in stale["verified_current_state"]
assert stale["collectors"]["SOURCE"]["freshness"] == "STALE"

# Conflicting fresh verified facts must surface, not be guessed away.
conflict = oca.build_packet(
    objective="Conflict test",
    observations=[
        obs("SOURCE", verified_facts={"active_commit": "source-sha"}),
        obs("RUNTIME_CONTINUITY", verified_facts={"active_commit": "runtime-sha"}),
    ],
    generated_at=NOW,
)
assert "active_commit" not in conflict["verified_current_state"]
assert conflict["conflicts"][0]["field"] == "active_commit"
assert len(conflict["conflicts"][0]["observations"]) == 2

# Missing collector becomes UNKNOWN without preventing packet creation.
missing = oca.build_packet(objective="Missing collector test", observations=[], generated_at=NOW)
assert all(missing["collectors"][name]["status"] == "UNKNOWN" for name in oca.COLLECTORS)

# Fail-closed malformed/authority cases.
expect_error("OBSERVATION_FROM_FUTURE", lambda: oca.build_packet(objective="x", observations=[obs("SOURCE", observed_at="2026-10-06T08:00:01Z")], generated_at=NOW))
expect_error("NON_VERIFIED_OBSERVATION_HAS_VERIFIED_FACTS", lambda: oca.build_packet(objective="x", observations=[obs("SOURCE", status="PARTIAL", verified_facts={"x": 1})], generated_at=NOW))
expect_error("OCA_CANNOT_ACCEPT_EFFECT_AUTHORITY", lambda: oca.build_packet(objective="x", observations=[{**obs("SOURCE"), "effect_authority": "WRITE"}], generated_at=NOW))
expect_error("DUPLICATE_COLLECTOR", lambda: oca.build_packet(objective="x", observations=[obs("SOURCE"), obs("SOURCE")], generated_at=NOW))
expect_error("UNKNOWN_COLLECTOR", lambda: oca.build_packet(objective="x", observations=[obs("NOPE")], generated_at=NOW))

# Static effect-surface guard: no network/process/database imports and no file writes.
tree = ast.parse(RUNTIME.read_text(encoding="utf-8"))
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        roots = {alias.name.split(".")[0] for alias in node.names}
        assert not roots.intersection({"requests", "httpx", "urllib", "socket", "subprocess", "sqlite3"}), roots
    if isinstance(node, ast.ImportFrom) and node.module:
        assert node.module.split(".")[0] not in {"requests", "httpx", "urllib", "socket", "subprocess", "sqlite3"}
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        assert node.func.attr not in {"write_text", "write_bytes", "unlink", "rename", "touch", "mkdir", "rmdir"}
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open":
        if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
            assert not any(flag in str(node.args[1].value) for flag in ("w", "a", "+", "x"))

print("OCA_CANARY PASS")
