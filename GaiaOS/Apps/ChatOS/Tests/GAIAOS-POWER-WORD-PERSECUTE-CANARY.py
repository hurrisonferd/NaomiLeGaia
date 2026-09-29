from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

PROTOCOL = ROOT / "GaiaOS/Apps/ChatOS/Protocols/POWER-WORD-PERSECUTE.v1.md"
SPELLBOOK = ROOT / "GaiaOS/Apps/ChatOS/Protocols/GAIAOS-SPELLBOOK.v1.md"
COMMANDS = ROOT / "GaiaOS/Apps/ChatOS/Protocols/GAIAOS-COUNCIL-COMMANDS.v1.md"
INSTRUCTIONS = ROOT / "GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-INSTRUCTIONS.v1.md"
BOOTSTRAP = ROOT / "GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-RUNTIME-BOOTSTRAP.v1.md"
CHAT_CURRENT = ROOT / "GaiaOS/Apps/ChatOS/CURRENT.json"
GAIA_CURRENT = ROOT / "GaiaOS/CURRENT.json"
LOADER = ROOT / "GaiaOS/LOAD.v1.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def require(text: str, needle: str, label: str) -> None:
    assert needle in text, f"{label}: missing {needle!r}"


def main() -> None:
    protocol = read(PROTOCOL)
    spellbook = read(SPELLBOOK)
    commands = read(COMMANDS)
    instructions = read(INSTRUCTIONS)
    bootstrap = read(BOOTSTRAP)
    loader = read(LOADER)
    chat_current = json.loads(read(CHAT_CURRENT))
    gaia_current = json.loads(read(GAIA_CURRENT))

    for text, label in ((protocol, "protocol"), (spellbook, "spellbook"), (commands, "commands")):
        require(text, "//PW:PERSECUTE//", label)

    for lens in ("VERA", "ANVIL", "SELENE", "ORIN", "KESTREL", "NIMUE"):
        require(protocol, lens, "protocol six-lens coverage")

    for drift_class in (
        "PROSPECTIVE MEMORY COLLAPSE",
        "ATTRIBUTION DRIFT",
        "STATUS DRIFT",
        "TEMPORAL DRIFT",
        "CONFIDENCE DRIFT",
        "CONTINUITY SUBSTITUTION",
        "SOURCE CONFLATION",
        "INFERENCE HARDENING",
        "UNSUPPORTED FABRICATION",
    ):
        require(protocol, drift_class, "drift taxonomy")

    require(protocol, "REPAIR AUTHORIZATION REQUIRED", "repair boundary")
    require(protocol, "INVESTIGATION != MUTATION", "non-mutative default")
    require(protocol, "UNKNOWN STAYS UNKNOWN", "unknown preservation")

    require(commands, "Canonical registry: `GaiaOS/Apps/ChatOS/Protocols/GAIAOS-SPELLBOOK.v1.md`", "command registry")
    require(instructions, "POWER-WORD-PERSECUTE.v1.md", "GPT instructions")
    require(bootstrap, "POWER-WORD-PERSECUTE.v1.md", "runtime bootstrap")
    require(loader, "POWER-WORD-PERSECUTE.v1.md", "canonical loader")

    assert chat_current["sources"]["spellbook"].endswith("GAIAOS-SPELLBOOK.v1.md")
    assert chat_current["sources"]["power_word_persecute"].endswith("POWER-WORD-PERSECUTE.v1.md")
    assert chat_current["power_words"]["persecute"]["invocation"] == "//PW:PERSECUTE//"
    assert chat_current["power_words"]["persecute"]["durable_repair_requires_separate_authorization"] is True

    assert gaia_current["chatos"]["spellbook"].endswith("GAIAOS-SPELLBOOK.v1.md")
    assert gaia_current["chatos"]["persecute"].endswith("POWER-WORD-PERSECUTE.v1.md")
    assert "PERSECUTE IS INVESTIGATORY BY DEFAULT" in gaia_current["laws"]
    assert "REPAIR REQUIRES SEPARATE NAOMI AUTHORIZATION" in gaia_current["laws"]

    print("PASS: //PW:PERSECUTE// canonical source wiring and authority boundaries")


if __name__ == "__main__":
    main()
