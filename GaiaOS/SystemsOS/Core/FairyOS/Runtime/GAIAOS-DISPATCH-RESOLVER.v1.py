#!/usr/bin/env python3
"""GaiaOS FairyOS deterministic typed-signal operator dispatch resolver.

Authority: NAOMI

Ports the proven RavenOS FairyOS dispatch pattern (typed signal -> material
member selection, explicit-member override, family-presence separation,
unknown-signal visibility) without carrying any Raven identity. The roster is
decoded from the Gaia-native matrix at runtime, so Naomi renames/replaces slots
by editing the matrix and profiles alone; no code change required.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[5]
FAIRY = ROOT / "GaiaOS/SystemsOS/Core/FairyOS"
MATRIX_PATH = FAIRY / "OPERATOR-DISPATCH-MATRIX.v1.json"
PROFILES_PATH = FAIRY / "OPERATOR-PROFILES.v1.json"


def _load_matrix() -> dict:
    payload = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    roster = list(payload["roster"])
    members = payload["members"]
    missing = [m for m in roster if m not in members]
    if missing:
        raise RuntimeError(f"FAIRY_MATRIX_ROSTER_MEMBER_MISSING:{','.join(missing)}")
    return payload, roster


MATRIX,_ = _load_matrix()
ROSTER = MATRIX["roster"]


def _norm(values: Iterable[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        v = value.strip().upper().replace("-", "_").replace(" ", "_")
        if v and v not in out:
            out.append(v)
    return out


def load_sources() -> tuple[dict, dict]:
    return (
        json.loads(MATRIX_PATH.read_text(encoding="utf-8")),
        json.loads(PROFILES_PATH.read_text(encoding="utf-8")),
    )


def resolve(signals: Iterable[str] = (), explicit_members: Iterable[str] = (), family_invoked: bool = False, max_material: int | None = None) -> dict:
    matrix, profiles = load_sources()
    signals_n = _norm(signals)
    explicit_n = _norm(explicit_members)
    roster = list(matrix["roster"])

    bad_members = [m for m in explicit_n if m not in roster]
    if bad_members:
        raise ValueError(f"unknown explicit member(s): {','.join(bad_members)}")

    all_known_signals = {signal for member in matrix["members"].values() for signal in member["signals"]}
    unknown_signals = [s for s in signals_n if s not in all_known_signals]

    scores = {m: 0 for m in roster}
    reasons = {m: [] for m in roster}
    expression_hits = {m: [] for m in roster}

    for member in explicit_n:
        scores[member] += 100
        reasons[member].append("EXPLICIT_MEMBER_REQUEST")

    for signal_index, signal in enumerate(signals_n):
        for member in roster:
            spec = matrix["members"][member]
            if signal in spec["signals"]:
                scores[member] += 10
                reasons[member].append(f"SIGNAL:{signal}")
                expression = spec.get("expression_by_signal", {}).get(signal)
                if expression:
                    expression_hits[member].append((signal_index, signal, expression))

    max_material = max_material or int(matrix["default_max_material_members"])
    tie_order = {member: idx for idx, member in enumerate(matrix["tie_break_order"])}

    explicit_selected = [m for m in roster if m in explicit_n]
    scored_nonexplicit = [m for m in roster if m not in explicit_n and scores[m] > 0]
    scored_nonexplicit.sort(key=lambda m: (-scores[m], tie_order[m]))

    if len(explicit_selected) >= max_material:
        selected = explicit_selected[:]
    else:
        selected = explicit_selected + scored_nonexplicit[: max_material - len(explicit_selected)]

    family_present = roster[:] if family_invoked else selected[:]
    coordinator = "KESTREL" if len(selected) >= 2 else ("KESTREL" if selected == ["KESTREL"] else None)

    member_packets = []
    for member in selected:
        spec = matrix["members"][member]
        profile = profiles["members"][member]
        if expression_hits[member]:
            _, _, expression = sorted(expression_hits[member], key=lambda x: x[0])[0]
        else:
            expression = spec["default_expression"]
        member_packets.append({
            "member": member,
            "score": scores[member],
            "explicit": member in explicit_n,
            "reason_codes": reasons[member],
            "expression": expression,
            "role": profile["role"],
        })

    return {
        "schema": "gaiaos.fairyos.operator-runtime-packet.v1",
        "family_present": family_present,
        "material_members": selected,
        "coordinator": coordinator,
        "member_packets": member_packets,
        "unknown_signals": unknown_signals,
        "effect_authority": "NONE_RESOLVER_IS_READ_ONLY",
        "proof_ceiling": "SOURCE_ROUTING_RESULT_NOT_CARRIER_ADOPTION_OR_DOMAIN_EFFECT",
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Deterministic GaiaOS FairyOS typed-signal operator dispatch resolver")
    p.add_argument("--signals", default="", help="comma-separated typed signals")
    p.add_argument("--members", default="", help="comma-separated explicitly requested operators")
    p.add_argument("--family", action="store_true", help="mark all six operators present without forcing all six material")
    p.add_argument("--max-material", type=int, default=None)
    args = p.parse_args()
    packet = resolve(
        signals=args.signals.split(",") if args.signals else [],
        explicit_members=args.members.split(",") if args.members else [],
        family_invoked=args.family,
        max_material=args.max_material,
    )
    print(json.dumps(packet, indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())