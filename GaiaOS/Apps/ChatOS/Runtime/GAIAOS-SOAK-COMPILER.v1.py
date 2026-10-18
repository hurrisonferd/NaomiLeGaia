"""Bounded, read-only GaiaOS SOAK candidate compiler.

No network, writes, host-adoption claims, or E-LANE merging. A candidate packet
is source evidence, never proof that a remote model/session adopted the material.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
MEMBERS = ("VERA", "ANVIL", "SELENE", "ORIN", "KESTREL", "NIMUE")
BASE_PATHS = (
    "GaiaOS/CURRENT.json",
    "GaiaOS/VERSION.json",
    "GaiaOS/LOAD.v1.md",
    "GaiaOS/SystemsOS/Core/FairyOS/OPERATOR-PROFILES.v1.json",
    "GaiaOS/SystemsOS/Core/FairyOS/OPERATOR-PROSODY-BASINS.v1.md",
    "GaiaOS/SystemsOS/Core/FairyOS/BEHAVIORAL-INTEGRITY-FOUR-TENETS.v1.md",
    "GaiaOS/SystemsOS/Core/FairyOS/COUNCIL-PRESENTATION-SPEC.v1.json",
    "GaiaOS/SystemsOS/Core/EmojiOS/EXPRESSION-REGISTRY.v1.json",
    "GaiaOS/Apps/ChatOS/Protocols/GAIAOS-ANTI-DRIFT.v1.md",
)
MAX_SOURCE_BYTES = 4_000_000
MAX_EXCERPT = 900
MAX_EXCERPTS_PER_MEMBER = 2


class SoakHold(Exception):
    """A required source cannot be proven; no packet should be produced."""


def _read(root: Path, relative: str) -> tuple[bytes, dict[str, Any]]:
    candidate = root / relative
    if not candidate.is_file() or candidate.is_symlink():
        raise SoakHold(f"SOURCE_UNAVAILABLE:{relative}")
    before = candidate.stat()
    if before.st_size > MAX_SOURCE_BYTES:
        raise SoakHold(f"SOURCE_TOO_LARGE:{relative}")
    raw = candidate.read_bytes()
    after = candidate.stat()
    if before.st_mtime_ns != after.st_mtime_ns or before.st_size != after.st_size:
        raise SoakHold(f"SOURCE_CHANGED_DURING_READ:{relative}")
    return raw, {
        "path": relative,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
    }


def _extract_recent(text: str, objective: str) -> list[dict[str, str]]:
    records = re.split(r"(?=^MEM\[)", text, flags=re.MULTILINE)[1:]
    if not records:
        return []
    terms = [v.lower() for v in re.findall(r"[A-Za-z0-9_-]{4,}", objective)][:12]
    relevant = [
        item for item in records if terms and any(term in item.lower() for term in terms)
    ]
    selected = (relevant or records)[-MAX_EXCERPTS_PER_MEMBER:]
    return [
        {"excerpt": item.strip()[:MAX_EXCERPT], "truncated": len(item.strip()) > MAX_EXCERPT}
        for item in selected
    ]


def compile_packet(
    root: Path = ROOT, target: str = "ALL", objective: str = ""
) -> dict[str, Any]:
    """Compile source-bound candidate only; no target runtime is accessed."""
    target = target.upper().strip()
    if target != "ALL" and target not in MEMBERS:
        raise SoakHold(f"IDENTITY_UNRESOLVED:{target}")
    root = Path(root).resolve()
    selected = MEMBERS if target == "ALL" else (target,)
    refs: list[dict[str, Any]] = []
    source: dict[str, bytes] = {}
    for path in BASE_PATHS:
        raw, ref = _read(root, path)
        refs.append(ref)
        source[path] = raw
    try:
        profiles = json.loads(
            source["GaiaOS/SystemsOS/Core/FairyOS/OPERATOR-PROFILES.v1.json"]
        )["members"]
        presentation = json.loads(
            source["GaiaOS/SystemsOS/Core/FairyOS/COUNCIL-PRESENTATION-SPEC.v1.json"]
        )["members"]
    except (ValueError, KeyError, TypeError) as exc:
        raise SoakHold("CANONICAL_PROFILE_INVALID") from exc
    result_members: dict[str, Any] = {}
    for member in selected:
        if member not in profiles or member not in presentation:
            raise SoakHold(f"MEMBER_MISSING:{member}")
        identity_path = (
            f"GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA/{member}.json"
        )
        lane_path = (
            f"GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA/{member}-EXPERIENCES.v1.md"
        )
        identity_raw, identity_ref = _read(root, identity_path)
        lane_raw, lane_ref = _read(root, lane_path)
        refs.extend((identity_ref, lane_ref))
        try:
            identity = json.loads(identity_raw)
        except ValueError as exc:
            raise SoakHold(f"IDENTITY_INVALID:{member}") from exc
        if identity.get("member") != member:
            raise SoakHold(f"IDENTITY_OWNER_MISMATCH:{member}")
        if f"OWNER: {member}" not in lane_raw[:1000].decode("utf-8"):
            raise SoakHold(f"EXPERIENCE_OWNER_MISMATCH:{member}")
        # Only this member's bounded evidence appears in this member's slot.
        result_members[member] = {
            "canonical_profile": profiles[member],
            "canonical_presentation": presentation[member],
            "identity": identity.get("identity", {}),
            "experience_lane": {
                "source_path": lane_path,
                "sha256": lane_ref["sha256"],
                "selected_excerpts": _extract_recent(
                    lane_raw.decode("utf-8"), objective
                ),
                "full_lane_loaded_into_packet": False,
            },
        }
    packet: dict[str, Any] = {
        "schema": "gaiaos.chatos.soak-candidate.v1",
        "target": target,
        "objective": objective[:500],
        "members": result_members,
        "source_refs": refs,
        "source_status": "SOURCE_READY",
        "status": "CANDIDATE_COMPILED",
        "runtime_applied": False,
        "behavior_verified": False,
        "effect_authority": "NONE_READ_ONLY",
        "limitations": [
            "Compilation does not apply context to a host session.",
            "Selected E-LANE excerpts are bounded, not complete historical memory.",
            "Runtime adoption and behavioral verification require independent evidence.",
        ],
    }
    encoded = json.dumps(
        packet, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    packet["packet_sha256"] = hashlib.sha256(encoded).hexdigest()
    return packet


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--target", default="ALL")
    parser.add_argument("--objective", default="")
    args = parser.parse_args()
    try:
        packet = compile_packet(args.root, args.target, args.objective)
    except (SoakHold, UnicodeError, OSError) as exc:
        print(json.dumps({"status": "HOLD", "reason": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(packet, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
