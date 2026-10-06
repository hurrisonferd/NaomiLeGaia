#!/usr/bin/env python3
"""Read-only canary for GaiaOS Operational Context Acquisition v1."""
from __future__ import annotations

import ast
import copy
import importlib.util
import json
from pathlib import Path

CHATOS = Path(__file__).resolve().parents[1]
RUNTIME = CHATOS / "Runtime/GAIAOS-OCA.v1.py"
SCHEMA = CHATOS / "Schemas/GAIAOS-OCA-PACKET.v1.schema.json"
PROTOCOL = CHATOS / "Protocols/GAIAOS-OPERATIONAL-CONTEXT-ACQUISITION.v1.md"
HOTCARD = CHATOS / "Protocols/GAIAOS-OCA-HOTCARD.v1.json"
CURRENT = CHATOS / "CURRENT.json"

spec = importlib.util.spec_from_file_location("gaiaos_oca", RUNTIME)
assert spec and spec.loader
oca = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oca)

NOW = "2026-10-06T08:00:00Z"


def obs(
    collector,
    *,
    provider=None,
    status="VERIFIED",
    observed_at="2026-10-06T07:59:30Z",
    max_age_seconds=120,
    verified_facts=None,
    facts=None,
    unknowns=None,
    errors=None,
):
    return {
        "collector": collector,
        "status": status,
        "source_class": "PROVIDER_RESULT" if collector != "SOURCE" else "SOURCE_READ",
        "provider": provider or f"fixture:{str(collector).lower()}",
        "observed_at": observed_at,
        "max_age_seconds": max_age_seconds,
        "coordinates": {"fixture": collector, "provider": provider or "default"},
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


# Required source files, ChatOS wiring, and firewall language.
for path in (RUNTIME, SCHEMA, PROTOCOL, HOTCARD, CURRENT):
    assert path.is_file(), path
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
assert schema["properties"]["collectors"]["properties"]["RUNTIME_CONTINUITY"]["$ref"].endswith("observationList")
assert set(schema["$defs"]["annotatedValue"]["required"]) == {"collector", "provider", "value"}

hotcard = json.loads(HOTCARD.read_text(encoding="utf-8"))
assert hotcard["schema"] == "gaiaos.oca.hotcard.v1"
assert hotcard["status"] == "ACTIVE_READ_ONLY_HOST_ACQUISITION_PROFILE"
assert hotcard["effect_authority"] == "NONE"
assert hotcard["persistence"] == "EPHEMERAL_ONLY"
assert hotcard["collector_order"] == ["SESSION", "SOURCE", "RUNTIME_CONTINUITY"]
assert hotcard["acquisition_rules"]["attempt_connected_read_before_asking_naomi_to_relay"] is True
assert hotcard["acquisition_rules"]["invent_tool_or_connection"] is False
assert hotcard["acquisition_rules"]["reuse_stale_observation_as_current"] is False
assert hotcard["acquisition_rules"]["cross_chat_capability_assumption"] is False
firewall = hotcard["persistence_firewall"]
for key in (
    "may_write_memoryos_turso",
    "may_write_e_lanes",
    "may_edit_identity",
    "may_commit_github",
    "may_deploy_or_restart",
    "may_promote_memory",
    "may_consume_authorization",
):
    assert firewall[key] is False, key
assert firewall["may_read_sources"] is True
assert firewall["may_normalize_reads"] is True
assert firewall["may_emit_ephemeral_packet"] is True
interrupt_gate = hotcard["naomi_interruption_gate"]
for expected in (
    "COPYING_AN_ID_ALREADY_OBTAINABLE_FROM_CONNECTED_PROVIDER",
    "REPEATING_CURRENT_COMMIT_ALREADY_READABLE_FROM_GITHUB",
    "RELAYING_DEPLOY_STATUS_ALREADY_READABLE_FROM_RENDER",
    "RESTATING_CAPABILITY_AVAILABILITY_ALREADY_OBSERVABLE_IN_SESSION",
):
    assert expected in interrupt_gate["do_not_interrupt_for"], expected

current = json.loads(CURRENT.read_text(encoding="utf-8"))
oca_current = current["operational_context_acquisition"]
assert oca_current["effect_authority"] == "NONE"
assert oca_current["persistence"] == "EPHEMERAL_ONLY"
assert oca_current["collectors"] == ["SESSION", "SOURCE", "RUNTIME_CONTINUITY"]
assert current["sources"]["oca_protocol"].endswith("GAIAOS-OPERATIONAL-CONTEXT-ACQUISITION.v1.md")
assert current["sources"]["oca_hotcard"].endswith("GAIAOS-OCA-HOTCARD.v1.json")
assert current["sources"]["oca_schema"].endswith("GAIAOS-OCA-PACKET.v1.schema.json")
assert current["sources"]["oca_runtime"].endswith("GAIAOS-OCA.v1.py")
assert current["sources"]["oca_canary"].endswith("GAIAOS-OCA-CANARY.py")
assert oca_current["hotcard"].endswith("GAIAOS-OCA-HOTCARD.v1.json")

# Happy path with multiple providers inside the same collector classes.
observations = [
    obs("SESSION", provider="host:tool-inventory", verified_facts={"available_capabilities": ["GitHub"]}),
    obs("SESSION", provider="host:plugin-inventory", verified_facts={"available_capabilities": ["Render"]}),
    obs("SOURCE", provider="github:main", verified_facts={"canonical_main": "abc123", "repository": "hurrisonferd/NaomiLeGaia"}),
    obs("RUNTIME_CONTINUITY", provider="render:deploy", verified_facts={"deployed_commit": "abc123"}),
    obs("RUNTIME_CONTINUITY", provider="memoryos:readback", verified_facts={"last_verified_effect": {"type": "DEPLOY", "id": "dep-1"}}),
]
packet = oca.build_packet(objective="Know current state", observations=observations, generated_at=NOW, exact_next_step="Begin read-only Stage 1")
assert packet["effect_authority"] == "NONE"
assert packet["persistence"] == "EPHEMERAL_ONLY"
assert packet["capabilities_available_now"] == ["GitHub", "Render"]
assert packet["verified_current_state"]["canonical_main"] == "abc123"
assert packet["verified_current_state"]["deployed_commit"] == "abc123"
assert packet["last_verified_effect"] == {"type": "DEPLOY", "id": "dep-1"}
assert len(packet["collectors"]["SESSION"]) == 2
assert len(packet["collectors"]["RUNTIME_CONTINUITY"]) == 2
assert packet["conflicts"] == []
assert packet["packet_id"].startswith("OCA-")
assert len(packet["packet_sha256"]) == 64

# Packet identity is invariant to input observation order and exact duplicate reads.
packet_reversed = oca.build_packet(objective="Know current state", observations=list(reversed(observations)), generated_at=NOW, exact_next_step="Begin read-only Stage 1")
assert packet_reversed == packet
packet_duplicate = oca.build_packet(objective="Know current state", observations=observations + [copy.deepcopy(observations[2])], generated_at=NOW, exact_next_step="Begin read-only Stage 1")
assert packet_duplicate == packet

# Partial provider failure must not erase healthy evidence.
partial = oca.build_packet(
    objective="Partial provider test",
    observations=[
        obs("SESSION", provider="host:tool-inventory", verified_facts={"available_capabilities": ["GitHub"]}),
        obs("SOURCE", provider="github:main", verified_facts={"canonical_main": "abc123"}),
        obs("RUNTIME_CONTINUITY", provider="render", status="UNAVAILABLE", verified_facts={}, unknowns=["Render connector unavailable"]),
    ],
    generated_at=NOW,
)
assert partial["verified_current_state"]["canonical_main"] == "abc123"
assert partial["capabilities_available_now"] == ["GitHub"]
assert any("UNAVAILABLE" in str(item["value"]) for item in partial["unknowns"])
assert any(item["provider"] == "render" for item in partial["unknowns"])

# Stale verified evidence must not enter current state.
stale = oca.build_packet(
    objective="Freshness test",
    observations=[obs("SOURCE", provider="github:stale", observed_at="2026-10-06T07:00:00Z", max_age_seconds=60, verified_facts={"canonical_main": "stale-sha"})],
    generated_at=NOW,
)
assert "canonical_main" not in stale["verified_current_state"]
assert stale["collectors"]["SOURCE"][0]["freshness"] == "STALE"

# Conflicting fresh verified facts from two providers must surface, not be guessed away.
conflict = oca.build_packet(
    objective="Conflict test",
    observations=[
        obs("RUNTIME_CONTINUITY", provider="render:deploy", verified_facts={"active_commit": "render-sha"}),
        obs("RUNTIME_CONTINUITY", provider="live:probe", verified_facts={"active_commit": "probe-sha"}),
    ],
    generated_at=NOW,
)
assert "active_commit" not in conflict["verified_current_state"]
assert conflict["conflicts"][0]["field"] == "active_commit"
assert {item["provider"] for item in conflict["conflicts"][0]["observations"]} == {"render:deploy", "live:probe"}
assert any("conflicting verified fact" in str(item["value"]) for item in conflict["blockers"])

# Missing collectors become explicit UNKNOWN observations without preventing packet creation.
missing = oca.build_packet(objective="Missing collector test", observations=[], generated_at=NOW)
assert all(len(missing["collectors"][name]) == 1 for name in oca.COLLECTORS)
assert all(missing["collectors"][name][0]["status"] == "UNKNOWN" for name in oca.COLLECTORS)
assert all(missing["collectors"][name][0]["provider"] == "UNOBSERVED" for name in oca.COLLECTORS)

# Fail-closed malformed/authority cases.
expect_error("OBSERVATION_FROM_FUTURE", lambda: oca.build_packet(objective="x", observations=[obs("SOURCE", observed_at="2026-10-06T08:00:01Z")], generated_at=NOW))
expect_error("NON_VERIFIED_OBSERVATION_HAS_VERIFIED_FACTS", lambda: oca.build_packet(objective="x", observations=[obs("SOURCE", status="PARTIAL", verified_facts={"x": 1})], generated_at=NOW))
expect_error("OCA_CANNOT_ACCEPT_EFFECT_AUTHORITY", lambda: oca.build_packet(objective="x", observations=[{**obs("SOURCE"), "effect_authority": "WRITE"}], generated_at=NOW))
expect_error("OBSERVATIONS_MUST_BE_LIST", lambda: oca.build_packet(objective="x", observations={"collector": "SOURCE"}, generated_at=NOW))
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
