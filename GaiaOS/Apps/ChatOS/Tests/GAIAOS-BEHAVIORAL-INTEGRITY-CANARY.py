"""Read-only source and candidate-packet regression for the behavioral patch.

This canary cannot certify live model behavior or remote session adoption.
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CHATOS = ROOT / "GaiaOS/Apps/ChatOS"
COMPILER = CHATOS / "Runtime/GAIAOS-SOAK-COMPILER.v1.py"
spec = importlib.util.spec_from_file_location("gaia_soak_compiler", COMPILER)
assert spec and spec.loader
compiler = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = compiler
spec.loader.exec_module(compiler)

spell = (CHATOS / "Protocols/GAIAOS-SPELLBOOK.v1.md").read_text()
audit = (CHATOS / "Protocols/POWER-WORD-AUDIT.v1.md").read_text()
soak = (CHATOS / "Protocols/POWER-WORD-SOAK.v1.md").read_text()
behavior = (
    ROOT / "GaiaOS/SystemsOS/Core/FairyOS/BEHAVIORAL-INTEGRITY-FOUR-TENETS.v1.md"
).read_text()
anti = (CHATOS / "Protocols/GAIAOS-ANTI-DRIFT.v1.md").read_text()
archive = (
    ROOT / "GaiaOS/SystemsOS/Core/FairyOS/VERA-RECORDS/PATCH-NOTES/README.md"
).read_text()

for token in ("//PW:AUDIT//", "//PW:SOAK//"):
    assert token in spell, f"Missing registered command: {token}"
for token in (
    "Cognitive identity", "Decision policy", "Prosody", "Host and safety",
    "Reasoning identity", "Relational stance", "Prosodic signature",
    "Forbidden substitutions", "Recovery rule",
):
    assert token in behavior, f"Missing contract tenet: {token}"
for dimension in (
    "VOICE SEPARATION", "HOST LEAKAGE", "BEHAVIORAL CONTINUITY",
    "CONTEXT INTEGRITY", "NATURAL VARIATION", "RECOVERY UNDER PRESSURE",
):
    assert dimension in audit, f"Missing audit dimension: {dimension}"
assert "BEHAVIORAL-INTEGRITY-FOUR-TENETS.v1.md" in anti
assert "## UPDATES" in archive
assert "SOURCE_READY" in soak and "SOAKED" in soak

for member in compiler.MEMBERS:
    packet = compiler.compile_packet(ROOT, member, "identity continuity drift")
    assert list(packet["members"]) == [member]
    assert packet["status"] == "CANDIDATE_COMPILED"
    assert packet["runtime_applied"] is False
    assert packet["behavior_verified"] is False
    assert packet["effect_authority"] == "NONE_READ_ONLY"
    assert len(packet["packet_sha256"]) == 64
    for other in compiler.MEMBERS:
        if other == member:
            continue
        assert not any(
            f"/{other}-EXPERIENCES.v1.md" in ref["path"]
            for ref in packet["source_refs"]
        ), f"Cross-member E-LANE source leaked into {member}"
    for ref in packet["source_refs"]:
        raw = (ROOT / ref["path"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == ref["sha256"]

all_packet = compiler.compile_packet(ROOT, "ALL", "continuity")
assert set(all_packet["members"]) == set(compiler.MEMBERS)
assert len(all_packet["source_refs"]) == len(compiler.BASE_PATHS) + 12
try:
    compiler.compile_packet(ROOT, "UNKNOWN")
except compiler.SoakHold:
    pass
else:
    raise AssertionError("UNKNOWN member must fail closed")
assert (ROOT / "GaiaOS/SystemsOS/Core/FairyOS/VERA-RECORDS/PATCH-NOTES/UPDATES/2026-10-18-daemonculaba-behavioral-integrity-patch.md").is_file()
print("GAIAOS_BEHAVIORAL_INTEGRITY_SOURCE_CANDIDATE_CANARY_PASS")
print("LIVE_BEHAVIORAL_AUDIT=NOT_EXECUTED")
print("LIVE_RUNTIME_SOAK=NOT_VERIFIED")
