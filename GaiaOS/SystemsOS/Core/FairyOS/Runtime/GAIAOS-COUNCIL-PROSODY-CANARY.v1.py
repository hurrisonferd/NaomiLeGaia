#!/usr/bin/env python3
"""GaiaOS Council prosody / identity / continuity source-integrity canary."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
FILES = {
    "current": ROOT / "GaiaOS/CURRENT.json",
    "gpt": ROOT / "GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-INSTRUCTIONS.v1.md",
    "voice": ROOT / "GaiaOS/SystemsOS/Core/FairyOS/COUNCIL-VOICE-AUTHORITY.v1.md",
    "profiles": ROOT / "GaiaOS/SystemsOS/Core/FairyOS/OPERATOR-PROFILES.v1.json",
    "prosody": ROOT / "GaiaOS/SystemsOS/Core/FairyOS/OPERATOR-PROSODY-BASINS.v1.md",
    "emoji": ROOT / "GaiaOS/SystemsOS/Core/EmojiOS/EXPRESSION-REGISTRY.v1.json",
    "continuity": ROOT / "GaiaOS/SystemsOS/Core/MemberContinuityOS/CURRENT.json",
    "warm": ROOT / "GaiaOS/SystemsOS/Core/MemberContinuityOS/WARM-CANDIDATE-BUFFER.v1.md",
    "registry": ROOT / "GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA/REGISTRY.v1.json",
    "loader": ROOT / "GaiaOS/SystemsOS/Core/FairyOS/Runtime/GAIAOS-MEMBER-IDENTITY-RUNTIME.v1.py",
}
MEMBERS = ["VERA", "ANVIL", "SELENE", "ORIN", "KESTREL", "NIMUE"]

def require(condition, message):
    if not condition:
        raise AssertionError(message)

def main():
    for name, path in FILES.items():
        require(path.is_file(), f"missing source: {name}: {path}")
    current = json.loads(FILES["current"].read_text())
    profiles = json.loads(FILES["profiles"].read_text())
    emoji = json.loads(FILES["emoji"].read_text())
    registry = json.loads(FILES["registry"].read_text())
    continuity = json.loads(FILES["continuity"].read_text())
    gpt = FILES["gpt"].read_text()
    voice = FILES["voice"].read_text()
    prosody = FILES["prosody"].read_text()
    require(current["authority"] == "NAOMI", "CURRENT authority drift")
    require(current["council"]["active"] is True, "Council not active")
    require(current["fairyos"]["voice_authority_prosody"] == "GaiaOS/SystemsOS/Core/FairyOS/COUNCIL-VOICE-AUTHORITY.v1.md", "voice authority drift")
    require(current["fairyos"]["identity_data"]["registry"] == "GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA/REGISTRY.v1.json", "identity registry drift")
    require(registry["pre_response_load"] is True, "pre-response identity load disabled")
    require(registry["auto_event_sync"] is True, "identity event sync disabled")
    require(list(profiles["members"].keys()) == MEMBERS, "six-speaker profile roster drift")
    require(list(emoji["members"].keys()) == MEMBERS, "six-speaker emoji roster drift")
    require(list(registry["members"].keys()) == MEMBERS, "six-speaker identity registry drift")
    for member in MEMBERS:
        record = json.loads((ROOT / registry["members"][member]).read_text())
        profile = profiles["members"][member]
        require(record["member"] == member, f"identity owner drift: {member}")
        require(record["identity"]["title"] == profile["title"], f"title mismatch: {member}")
        require(record["identity"]["role"] == profile["role"], f"role mismatch: {member}")
        require(record["identity"]["basin"] == profile["basin"], f"basin mismatch: {member}")
        require(member in voice and member in prosody, f"canonical voice/prosody missing: {member}")
        require(record.get("event_log") is not None, f"event log missing: {member}")
        require(record.get("event_log_policy"), f"event policy missing: {member}")
        require(member in gpt, f"GPT member surface missing: {member}")
    for ref in ["IDENTITY-DATA/REGISTRY.v1.json", "GAIAOS-MEMBER-IDENTITY-RUNTIME.v1.py", "COUNCIL-VOICE-AUTHORITY.v1.md", "OPERATOR-PROFILES.v1.json", "OPERATOR-PROSODY-BASINS.v1.md", "EXPRESSION-REGISTRY.v1.json"]:
        require(ref in gpt, f"GPT canonical reference missing: {ref}")
    for rule in ["CHATGPT HOST = NOT A COUNCIL MEMBER", "HOST NARRATOR = NOT A COUNCIL MEMBER", "DO NOT SPEAK FOR NAOMI", "LEAVE SPACE FOR SILENCE"]:
        require(rule in voice, f"voice boundary missing: {rule}")
    require(continuity.get("automatic_persistence") is False, "MemberContinuityOS durable claim drift")
    require(continuity.get("durable_backend") is None, "MemberContinuityOS backend claim drift")
    require("WARM != SAVED" in continuity.get("laws", []), "warm/durable boundary missing")
    require("NO CROSS_MEMBER MEMORY MERGE" in continuity.get("laws", []), "memory isolation law missing")
    require(current["fairyos"]["raven_roster_adopted"] is False, "Raven roster adoption drift")
    print("GAIAOS_COUNCIL_PROSODY_IDENTITY_CANARY_PASS")
    print("ROSTER=" + "/".join(MEMBERS))
    print("IDENTITY_DATA=6_ISOLATED_DATASETS; PRE_RESPONSE_LOAD=PASS; AUTO_EVENT_SYNC=PASS")
    print("PROSODY=PROFILE+PROSODY+VOICE_AUTHORITY+EMOJI=PASS")
    print("DURABLE_MEMORY=REPOSITORY_RECORD; MEMBERCONTINUITY_DURABLE_BACKEND=NOT_PRESENT")
    print("HOST_BOUNDARY=NO_NARRATOR; NO_NAOMI_FILLER")

if __name__ == "__main__":
    main()
