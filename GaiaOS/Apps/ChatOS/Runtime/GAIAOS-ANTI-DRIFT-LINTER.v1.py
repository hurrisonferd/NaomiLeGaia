#!/usr/bin/env python3
"""Read-only GaiaOS anti-drift linter for transient Prime-Daemon speech."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

GAIA = Path(__file__).resolve().parents[3]
FAIRYOS = GAIA / "SystemsOS" / "Core" / "FairyOS"
EMOJIOS = GAIA / "SystemsOS" / "Core" / "EmojiOS"
CHATOS = GAIA / "Apps" / "ChatOS"

PRESENTATION = FAIRYOS / "COUNCIL-PRESENTATION-SPEC.v1.json"
EXPRESSIONS = EMOJIOS / "EXPRESSION-REGISTRY.v1.json"
HOTCARD = CHATOS / "Protocols" / "GAIAOS-ANTI-DRIFT-HOTCARD.v1.json"

OPENING_SIGNALS = [
    re.compile(r"^\s*(?:yes[.!]?\s+)?you(?:'re| are)\s+(?:absolutely|completely|so)\s+right\b", re.I),
    re.compile(r"^\s*that makes (?:complete|total) sense\b", re.I),
    re.compile(r"^\s*i love that\b", re.I),
]
GENERIC_SIGNALS = [
    re.compile(r"\bperfect combination\b", re.I),
    re.compile(r"\banytime you want\b", re.I),
    re.compile(r"\bwhenever you want\b", re.I),
]
GENERIC_CLOSERS = [
    re.compile(r"(?:anytime|whenever) you want[^.!?]*[.!?]?\s*$", re.I),
    re.compile(r"i(?:'m| am) (?:here|ready) when you are[.!]?\s*$", re.I),
]
SUPPORT_FLATTENING_SIGNALS = [
    re.compile(r"\byou don['’]?t have to (?:solve|fix|figure out) (?:everything|it all)(?: today| right now)?\b", re.I),
    re.compile(r"\bone (?:thing|step) at a time\b", re.I),
    re.compile(r"\bbe gentle with yourself\b", re.I),
    re.compile(r"\byou deserve (?:rest|care|support|kindness)\b", re.I),
    re.compile(r"\bi(?:'m| am) here with you\b", re.I),
    re.compile(r"\bit(?:'s| is) okay to (?:feel|rest|struggle|not know)\b", re.I),
    re.compile(r"\byou(?:'re| are) doing (?:enough|the best you can)\b", re.I),
]
SUPPORT_FLATTENING_THRESHOLD = 2


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_header_parts(member: str) -> tuple[str, set[str]]:
    presentation = _load_json(PRESENTATION)
    expressions = _load_json(EXPRESSIONS)
    m = presentation["members"][member]
    prefix = f'{m["gematria"]} · {member} {m["heart"]} {m["interest"]} '
    expr = expressions["members"][member]
    allowed = {expr["default"], *expr["expressions"].values()}
    return prefix, allowed


def lint_response(member: str, text: str) -> list[str]:
    """Return deterministic surface-level drift errors; never mutate input or sources."""
    errors: list[str] = []
    presentation = _load_json(PRESENTATION)
    if member not in presentation["members"]:
        return [f"unknown_member:{member}"]

    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return ["empty_response"]

    prefix, allowed = canonical_header_parts(member)
    first = lines[0].strip()
    if not first.startswith(prefix):
        errors.append("identity_header_mismatch")
    else:
        rendered_expression = first[len(prefix):].strip()
        if rendered_expression not in allowed:
            errors.append("cross_member_or_unregistered_kaomoji")

    body = "\n".join(lines[1:]).strip()
    if not body:
        errors.append("empty_member_body")
        return errors

    if any(pattern.search(body) for pattern in OPENING_SIGNALS):
        errors.append("generic_validation_opening")
    if any(pattern.search(body) for pattern in GENERIC_SIGNALS):
        errors.append("generic_host_scaffold")
    if any(pattern.search(body) for pattern in GENERIC_CLOSERS):
        errors.append("generic_continue_offer_closer")

    support_signal_count = sum(1 for pattern in SUPPORT_FLATTENING_SIGNALS if pattern.search(body))
    if support_signal_count >= SUPPORT_FLATTENING_THRESHOLD:
        errors.append("generic_supportive_flattening")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only GaiaOS anti-drift response linter")
    parser.add_argument("--member", required=True, choices=["VERA", "ANVIL", "SELENE", "ORIN", "KESTREL", "NIMUE"])
    parser.add_argument("--text-file", required=True)
    args = parser.parse_args()

    text = Path(args.text_file).read_text(encoding="utf-8")
    errors = lint_response(args.member, text)
    print(json.dumps({"member": args.member, "pass": not errors, "errors": errors}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
