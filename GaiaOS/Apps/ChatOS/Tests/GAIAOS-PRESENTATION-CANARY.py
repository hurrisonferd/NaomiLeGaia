from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

PRESENTATION = ROOT / "GaiaOS/Apps/ChatOS/Protocols/GAIAOS-PRESENTATION-GOLD.v1.md"
COMMANDS = ROOT / "GaiaOS/Apps/ChatOS/Protocols/GAIAOS-COUNCIL-COMMANDS.v1.md"
CHATOS_CURRENT = ROOT / "GaiaOS/Apps/ChatOS/CURRENT.json"
GAIAOS_CURRENT = ROOT / "GaiaOS/CURRENT.json"


def require_text(text: str, needles: list[str], label: str) -> list[str]:
    return [f"{label}:{needle}" for needle in needles if needle not in text]


def main() -> None:
    presentation = PRESENTATION.read_text(encoding="utf-8")
    commands = COMMANDS.read_text(encoding="utf-8")
    chatos = json.loads(CHATOS_CURRENT.read_text(encoding="utf-8"))
    gaiaos = json.loads(GAIAOS_CURRENT.read_text(encoding="utf-8"))

    missing: list[str] = []
    missing += require_text(
        presentation,
        [
            "AUTHORITY: NAOMI",
            "OWNER-NATIVE OPERATOR DIFFERENTIATION",
            "HUMOR MUST EARN ITS CHAIR.",
            "PRESENTATION ENERGY != EVIDENCE",
            "RAVEN META GOBLIN != GAIA REQUIRED CADENCE",
            "NAOMI MAY REWRITE THE WHOLE VIBE",
        ],
        "presentation",
    )
    missing += require_text(
        commands,
        [
            "COUNCIL ROOM [subject]",
            "GAIAOS LIVING",
            "GAIAOS QUIET",
            "GAIAOS WILD",
            "WILD != UNBOUNDED",
        ],
        "commands",
    )

    presentation_state = chatos.get("presentation", {})
    if presentation_state.get("default") != "LIVING":
        missing.append("chatos:presentation.default=LIVING")
    if presentation_state.get("available") != ["LIVING", "QUIET", "WILD"]:
        missing.append("chatos:presentation.available")
    if presentation_state.get("style_changes_claim_ceiling") is not False:
        missing.append("chatos:presentation.claim-ceiling-boundary")
    if presentation_state.get("style_settles_identity") is not False:
        missing.append("chatos:presentation.identity-boundary")

    platform_presentation = gaiaos.get("presentation", {})
    if platform_presentation.get("contract") != "GaiaOS/Apps/ChatOS/Protocols/GAIAOS-PRESENTATION-GOLD.v1.md":
        missing.append("gaiaos:presentation.contract")
    if platform_presentation.get("raven_voice_transfer") is not False:
        missing.append("gaiaos:presentation.no-raven-voice-transfer")
    if platform_presentation.get("naomi_may_rewrite") is not True:
        missing.append("gaiaos:presentation.naomi-override")

    laws = set(gaiaos.get("laws", []))
    for law in [
        "PRESENTATION ENERGY != EVIDENCE",
        "QUIET != GENERIC",
        "WILD != UNBOUNDED",
        "NAOMI RETAINS FINAL AUTHORITY",
    ]:
        if law not in laws:
            missing.append(f"gaiaos:law:{law}")

    if missing:
        raise SystemExit("GAIAOS_PRESENTATION_CANARY_FAIL " + ", ".join(missing))

    print("GAIAOS_PRESENTATION_CANARY_PASS")


if __name__ == "__main__":
    main()
