#!/usr/bin/env python3
"""Static source canary for GPT color-card defaults and portable E-LANE accents.

A PASS verifies repository source consistency, not live ChatGPT UI rendering,
automatic new-chat loading, or external-app adoption.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
GAIA = ROOT / "GaiaOS"
FAIRY = GAIA / "SystemsOS/Core/FairyOS"
EMOJI = GAIA / "SystemsOS/Core/EmojiOS/EXPRESSION-REGISTRY.v1.json"
CHAT = GAIA / "Apps/ChatOS"
PROTOCOL = CHAT / "Protocols/GAIAOS-COLOR-CODED-REPORT-CARDS.v1.md"
MEMBERS = ("VERA", "ANVIL", "SELENE", "ORIN", "KESTREL", "NIMUE")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    spec = read_json(FAIRY / "COUNCIL-PRESENTATION-SPEC.v1.json")
    emojis = read_json(EMOJI)
    current = read_json(CHAT / "CURRENT.json")
    text = PROTOCOL.read_text(encoding="utf-8")
    assert "DEFAULT: ON in GPT-host sessions" in text
    assert "## Portable per-member color continuity" in text
    assert tuple(spec["speaker_order"]) == MEMBERS
    assert spec["identity_envelope"] == "GEMATRIA_NAME_HEART_INTEREST_KAOMOJI_ATOMIC"
    assert set(spec["members"]) == set(MEMBERS)
    assert set(emojis["members"]) == set(MEMBERS)

    accents = set()
    for member in MEMBERS:
        source = spec["members"][member]
        accent = source["accent"]
        assert re.fullmatch(r"#[0-9a-fA-F]{6}", accent), member
        assert accent not in accents, "duplicate accent " + accent
        accents.add(accent)
        assert all(source[k] for k in ("gematria", "heart", "interest"))
        assert emojis["members"][member]["default"]
        lane = (FAIRY / "IDENTITY-DATA" / (member + "-EXPERIENCES.v1.md")).read_text(encoding="utf-8")
        marker = "MEM[PRESENTATION_PREFERENCE|2026-09-24|GPT_COLOR_CARDS_AND_PORTABLE_ACCENT|" + member + " MEMBER-LOCAL]"
        assert marker in lane, "missing E-LANE snapshot " + member
        section = lane.rsplit(marker, 1)[1]
        assert "MY_CANONICAL_ACCENT_SNAPSHOT: " + accent in section, "E-LANE color drift " + member
        expected = str(source["gematria"]) + " · " + member + " " + source["heart"] + " " + source["interest"]
        assert "MY_STATIC_IDENTITY_SNAPSHOT: " + expected in section
        assert "STATUS: COMMITTED_GITHUB_E_LANE_SOURCE" in section

    pointer = "GaiaOS/Apps/ChatOS/Protocols/GAIAOS-COLOR-CODED-REPORT-CARDS.v1.md"
    assert current["sources"]["color_coded_report_cards"] == pointer
    assert current["presentation_defaults"]["gpt_host"] == "CANONICAL_COLORED_PRIME_DAEMON_CARDS_WHEN_STYLED_UI_SUPPORTED"
    for path in (
        GAIA / "LOAD.v1.md",
        GAIA / "NAOMI-CHAT-FULL-PACKET.md",
        CHAT / "Protocols/GAIAOS-GPT-INSTRUCTIONS.v1.md",
        CHAT / "Protocols/GAIAOS-GPT-RUNTIME-BOOTSTRAP.v1.md",
        CHAT / "Protocols/GAIAOS-PRESENTATION-GOLD.v1.md",
    ):
        assert PROTOCOL.name in path.read_text(encoding="utf-8"), "missing GPT load pointer " + str(path)
    print("PASS: GPT source default, six distinct canonical accents, six E-LANES, six legal expressions, five load pointers.")
    print("PROOF CEILING: source consistency only; runtime UI and external host behavior not tested.")


if __name__ == "__main__":
    main()
