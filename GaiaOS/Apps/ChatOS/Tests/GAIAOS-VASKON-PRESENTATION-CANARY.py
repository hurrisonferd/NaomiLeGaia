#!/usr/bin/env python3
"""Fail-closed source/behavior canary for explicitly conjured VASKON presentation."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
RENDERER = ROOT / "GaiaOS/SystemsOS/Core/FairyOS/Runtime/GAIAOS-PRESENTATION-RENDERER.v1.py"
SPEC = ROOT / "GaiaOS/SystemsOS/Core/FairyOS/COUNCIL-PRESENTATION-SPEC.v1.json"
EMOJI = ROOT / "GaiaOS/SystemsOS/Core/EmojiOS/EXPRESSION-REGISTRY.v1.json"
PROTOCOL = ROOT / "GaiaOS/Apps/ChatOS/Protocols/CONJURE-VASKON.v1.md"
HOST = ROOT / "GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-INSTRUCTIONS.v1.md"
PRESENTATION_GOLD = ROOT / "GaiaOS/Apps/ChatOS/Protocols/GAIAOS-PRESENTATION-GOLD.v1.md"
LOADER = ROOT / "GaiaOS/LOAD.v1.md"
BOOTSTRAP = ROOT / "GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-RUNTIME-BOOTSTRAP.v1.md"

def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

def expect_error(fn, message: str) -> None:
    try:
        fn()
    except Exception:
        return
    raise AssertionError(message)

def load_renderer():
    spec = importlib.util.spec_from_file_location("gaiaos_presentation", RENDERER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module

def main() -> None:
    for path in (RENDERER, SPEC, EMOJI, PROTOCOL, HOST, PRESENTATION_GOLD, LOADER, BOOTSTRAP):
        require(path.is_file(), f"missing source: {path}")

    renderer = load_renderer()
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    emoji = json.loads(EMOJI.read_text(encoding="utf-8"))
    protocol = PROTOCOL.read_text(encoding="utf-8")
    host = HOST.read_text(encoding="utf-8")
    presentation_gold = PRESENTATION_GOLD.read_text(encoding="utf-8")
    loader = LOADER.read_text(encoding="utf-8")
    bootstrap = BOOTSTRAP.read_text(encoding="utf-8")

    vaskon = spec["synthesis_modes"]["VASKON"]
    require("VASKON" not in spec["members"], "VASKON leaked into Prime Daemon roster")
    require("VASKON" not in spec["speaker_order"], "VASKON leaked into speaker_order")
    require(vaskon["gematria"] == 82, "VASKON gematria drift")
    require(vaskon["heart"] == "🖤", "VASKON heart drift")
    require(vaskon["symbol"] == "✴️", "VASKON synthesis symbol drift")
    require(vaskon["class"] == "TEMPORARY_SIX_PRIME_DAEMON_SYNTHESIS", "VASKON class drift")
    require(vaskon["invocation"] == "CONJURE:VASKON", "VASKON canonical invocation drift")
    require(vaskon["aliases"] == ["//C:82//"], "VASKON alias drift")

    vexpr = emoji["synthesis_modes"]["VASKON"]
    require(vexpr["default"] == "(◉‿◉)", "VASKON default kaomoji drift")

    expected = "82 · VASKON 🖤 ✴️ (◉‿◉)"
    require(
        renderer.canonical_header("VASKON", invocation="CONJURE:VASKON") == expected,
        "canonical VASKON header drift",
    )
    require(
        renderer.canonical_header("VASKON", invocation="//C:82//") == expected,
        "VASKON alias did not normalize to canonical envelope",
    )
    require(
        renderer.normalize_synthesis_invocation("VASKON", "//C:82//") == "CONJURE:VASKON",
        "VASKON alias normalization failed",
    )

    expect_error(
        lambda: renderer.render("VASKON", "test"),
        "naked VASKON render did not fail closed",
    )
    expect_error(
        lambda: renderer.render("VASKON", "test", invocation="VASKON"),
        "invalid VASKON invocation did not fail closed",
    )

    invalid_headers = [
        "VASKON 🖤 ✴️ (◉‿◉)",
        "82 · VASKON ✴️ (◉‿◉)",
        "82 · VASKON 🖤 (◉‿◉)",
        "82 · VASKON 🖤 ✴️",
        "82 · VASKON ✴️ 🖤 (◉‿◉)",
        "82 · VASKON 🖤 ✴️ (¬‿¬)",
        "82 · VASKON 🖤 ✴️ (◉‿◉) (¬‿¬)",
    ]
    for header in invalid_headers:
        expect_error(
            lambda header=header: renderer.validate_header(
                "VASKON", header, invocation="CONJURE:VASKON"
            ),
            f"invalid VASKON header accepted: {header}",
        )

    for state, kaomoji in vexpr["expressions"].items():
        header = renderer.canonical_header(
            "VASKON",
            expression_state=state,
            invocation="CONJURE:VASKON",
        )
        require(header == f"82 · VASKON 🖤 ✴️ {kaomoji}", f"VASKON expression drift: {state}")

    require(
        renderer.canonical_header(
            "VASKON",
            expression_state="UNREGISTERED",
            invocation="CONJURE:VASKON",
        ) == expected,
        "unknown VASKON expression did not fall back to default",
    )

    required_protocol = [
        "CANONICAL DEFAULT HEADER: 82 · VASKON 🖤 ✴️ (◉‿◉)",
        "VASKON PRESENTATION REQUIRES EXPLICIT CONJURE STATE",
        "NO NAKED VASKON NAME REACHES PRESENTATION",
        "INVALID VASKON HEADER → FAIL CLOSED",
        "//C:82//",
    ]
    for needle in required_protocol:
        require(needle in protocol, f"VASKON protocol presentation marker missing: {needle}")

    required_boot = [
        "82 · VASKON 🖤 ✴️",
        "//C:82//",
        "CONJURE:VASKON",
        "fail closed",
    ]
    for needle in required_boot:
        require(needle in loader, f"loader VASKON integrity marker missing: {needle}")
        require(needle in bootstrap, f"bootstrap VASKON integrity marker missing: {needle}")

    required_gold = [
        "82 · VASKON 🖤 ✴️ (◉‿◉)",
        "QUIET MODE != NAKED VASKON",
        "WILD MODE != EXTRA VASKON MARKERS",
        "PRESENTATION GOLD != LICENSE TO IMPROVISE IDENTITY",
    ]
    for needle in required_gold:
        require(needle in presentation_gold, f"Presentation Gold VASKON marker missing: {needle}")

    required_host = [
        "82 · VASKON 🖤 ✴️ (◉‿◉)",
        "CONJURE:VASKON",
        "//C:82//",
        "NO NAKED VASKON NAME REACHES PRESENTATION",
    ]
    for needle in required_host:
        require(needle in host, f"host VASKON presentation instruction missing: {needle}")

    # Reuse the already-wired presentation CI entrypoint to exercise six-member
    # and SOLO source/response guards alongside the existing VASKON checks.
    subprocess.run(
        [sys.executable, str(ROOT / "GaiaOS/Apps/ChatOS/Tests/GAIAOS-PRIME-DAEMON-PRESENTATION-CANARY.py")],
        check=True,
    )
    print("GAIAOS_VASKON_PRESENTATION_CANARY_PASS")
    print("HEADER=" + expected)
    print("ALIAS=//C:82// -> CONJURE:VASKON")
    print("FAIL_CLOSED=UNCONJURED+INVALID_INVOCATION+MISSING_OR_REORDERED_MARKERS")
    print("EXPRESSION_STATES=" + str(len(vexpr["expressions"])) + "+DEFAULT")
    print("ROSTER_MEMBERSHIP=FALSE")

if __name__ == "__main__":
    main()
