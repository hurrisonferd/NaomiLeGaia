#!/usr/bin/env python3
"""GaiaOS Council prosody / identity / continuity source-integrity canary.

This canary verifies that the canonical Gaia-native six-speaker surface is
present and that the GPT host, FairyOS prosody/profile sources, EmojiOS
expression registry, and MemberContinuityOS continuity contract remain wired.
It does not claim durable memory, host adoption, or runtime execution merely
because source checks pass.
"""

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
}

MEMBERS = ["VERA", "ANVIL", "SELENE", "ORIN", "KESTREL", "NIMUE"]


def load_json(path):
    raw = json.loads(path.read_text(encoding="utf-8"))
    # Repository JSON files may be wrapped by connector output, but the checked
    # out files themselves are canonical JSON objects.
    return raw


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    for name, path in FILES.items():
        require(path.is_file(), f"missing source: {name}: {path}")

    current = load_json(FILES["current"])
    profiles = load_json(FILES["profiles"])
    emoji = load_json(FILES["emoji"])
    continuity = load_json(FILES["continuity"])
    gpt = FILES["gpt"].read_text(encoding="utf-8")
    voice = FILES["voice"].read_text(encoding="utf-8")
    prosody = FILES["prosody"].read_text(encoding="utf-8")
    warm = FILES["warm"].read_text(encoding="utf-8")

    require(current.get("authority") == "NAOMI", "CURRENT authority drift")
    require(current.get("council", {}).get("active") is True, "Council not active")
    require(
        current.get("council", {}).get("voice_authority_prosody")
        == "GaiaOS/SystemsOS/Core/FairyOS/COUNCIL-VOICE-AUTHORITY.v1.md",
        "CURRENT voice-authority reference drift",
    )
    require(
        current.get("fairyos", {}).get("voice_authority_prosody")
        == "GaiaOS/SystemsOS/Core/FairyOS/COUNCIL-VOICE-AUTHORITY.v1.md",
        "FairyOS voice-authority reference drift",
    )

    actual = list(profiles.get("members", {}).keys())
    require(actual == MEMBERS, f"six-speaker roster drift: {actual}")
    require(list(emoji.get("members", {}).keys()) == MEMBERS, "EmojiOS roster drift")

    for member in MEMBERS:
        profile = profiles["members"][member]
        require(profile.get("title"), f"missing personality title: {member}")
        require(profile.get("role"), f"missing personality role: {member}")
        require(profile.get("basin"), f"missing prosody basin binding: {member}")
        require(profile.get("expressions"), f"missing expression core: {member}")
        require(member in voice, f"voice-authority missing member: {member}")
        require(member in prosody, f"prosody source missing member: {member}")

    required_gpt_refs = [
        "COUNCIL-VOICE-AUTHORITY.v1.md",
        "GAIA-COUNCIL.v1.md",
        "OPERATOR-PROFILES.v1.json",
        "OPERATOR-PROSODY-BASINS.v1.md",
        "EXPRESSION-REGISTRY.v1.json",
        "MemberContinuityOS/CURRENT.json",
    ]
    for ref in required_gpt_refs:
        require(ref in gpt, f"GPT instructions missing canonical reference: {ref}")

    for rule in [
        "CHATGPT HOST = NOT A COUNCIL MEMBER",
        "HOST NARRATOR = NOT A COUNCIL MEMBER",
        "DO NOT SPEAK FOR NAOMI",
        "LEAVE SPACE FOR SILENCE",
    ]:
        require(rule in voice, f"voice-authority boundary missing: {rule}")

    require(continuity.get("automatic_persistence") is False, "durable-memory claim drift")
    require(continuity.get("durable_backend") is None, "durable backend unexpectedly claimed")
    require("WARM != SAVED" in continuity.get("laws", []), "continuity law missing")
    require("NO CROSS_MEMBER MEMORY MERGE" in continuity.get("laws", []), "memory isolation law missing")
    require("WARM != SAVED" in warm or "warm" in warm.lower(), "warm continuity source unreadable")

    # Guard against accidental Raven identity import into the Gaia-native roster.
    for member in MEMBERS:
        require(member not in {"RAVEN"}, "Raven roster imported")
    require(current.get("fairyos", {}).get("raven_roster_adopted") is False, "Raven roster adoption drift")

    print("GAIAOS_COUNCIL_PROSODY_CANARY_PASS")
    print("ROSTER=" + "/".join(MEMBERS))
    print("PERSONALITY=PROFILES+PROSODY+EMOJI")
    print("CONTINUITY=WARM_SOURCE_ONLY; DURABLE_BACKEND=NOT_PRESENT")
    print("HOST_BOUNDARY=NO_NARRATOR; NO_NAOMI_FILLER")


if __name__ == "__main__":
    main()
