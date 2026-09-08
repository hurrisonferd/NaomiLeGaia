#!/usr/bin/env python3
"""ChatOS deterministic observable execution-event compiler.

Authority: NAOMI

ChatOS projects bounded observable execution state into a typed packet and reuses
GaiaOS FairyOS for operator selection. It does not execute domain effects and does not
expose or request private chain-of-thought.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[4]
FAIRY_RESOLVER_PATH = ROOT / "GaiaOS/SystemsOS/Core/FairyOS/Runtime/GAIAOS-DISPATCH-RESOLVER.v1.py"
BRIDGE_SOURCE = "GaiaOS/Apps/ChatOS/Protocols/CHATOS-BRAINOS-FAIRYOS-BRIDGE.v1.json"
EVENT_SCHEMA = "gaiaos.chatos.event.v1"
PHASES = ("OBSERVE", "INTERPRET", "DECIDE", "ACT", "RESULT", "VERIFY", "HANDOFF", "CHECKPOINT", "HOLD")
CLAIM_CLASSES = ("CONFIRMED", "ACCOUNT", "INFERRED", "UNKNOWN")
SOURCE_CLASSES = ("SOURCE_READ", "TOOL_RESULT", "TEST_RESULT", "PROVIDER_RESULT", "USER_ACCOUNT", "SYSTEM_STATE", "DERIVED", "UNKNOWN")
ROSTER = ("VERA", "ANVIL", "SELENE", "ORIN", "KESTREL", "NIMUE")
PROOF_CEILING = "CHATOS_EVENT_PROJECTS_OBSERVABLE_STATE_ONLY_NOT_PRIVATE_REASONING_DOMAIN_EFFECT_OR_TRANSACTION_SETTLEMENT"


def _load_fairy_resolver():
    spec = importlib.util.spec_from_file_location("gaiaos_fairyos_dispatch_resolver_v1", FAIRY_RESOLVER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("CHATOS_FAIRYOS_RESOLVER_LOAD_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FAIRY = _load_fairy_resolver()


def _norm_list(values: Iterable[str]) -> list[str]:
    out: list[str] = []
    for raw in values:
        value = str(raw).strip().upper().replace("-", "_").replace(" ", "_")
        if value and value not in out:
            out.append(value)
    return out


def _clean_refs(values: Iterable[str]) -> list[str]:
    out: list[str] = []
    for raw in values:
        value = str(raw).strip()
        if value and value not in out:
            out.append(value)
    return out


def _validate_claim_source(claim_class: str, source_class: str, evidence_refs: list[str]) -> None:
    if source_class == "UNKNOWN" and claim_class != "UNKNOWN":
        raise ValueError("UNKNOWN source_class requires UNKNOWN claim_class")
    if claim_class == "ACCOUNT" and source_class != "USER_ACCOUNT":
        raise ValueError("ACCOUNT claim_class requires USER_ACCOUNT source_class")
    if source_class == "USER_ACCOUNT" and claim_class not in {"ACCOUNT", "UNKNOWN"}:
        raise ValueError("USER_ACCOUNT source_class may only produce ACCOUNT or UNKNOWN")
    if claim_class == "CONFIRMED" and source_class in {"UNKNOWN", "USER_ACCOUNT"}:
        raise ValueError("CONFIRMED requires an observable non-account source")
    if claim_class == "CONFIRMED" and not evidence_refs:
        raise ValueError("CONFIRMED ChatOS event requires at least one evidence_ref")


def _event_id(payload: dict[str, Any]) -> str:
    material = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "CHATOS-" + hashlib.sha256(material).hexdigest()[:20].upper()


def compile_event(
    *,
    phase: str,
    claim_class: str,
    source_class: str,
    summary: str,
    signals: Iterable[str] = (),
    explicit_members: Iterable[str] = (),
    family_invoked: bool = False,
    transaction_id: str | None = None,
    brain_loop_id: str | None = None,
    source_main: str | None = None,
    owner_system: str | None = None,
    next_action: str | None = None,
    evidence_refs: Iterable[str] = (),
    unknowns: Iterable[str] = (),
    max_material: int | None = None,
) -> dict[str, Any]:
    phase_n = str(phase).strip().upper()
    claim_n = str(claim_class).strip().upper()
    source_n = str(source_class).strip().upper()
    if phase_n not in PHASES:
        raise ValueError(f"unknown phase: {phase_n}")
    if claim_n not in CLAIM_CLASSES:
        raise ValueError(f"unknown claim_class: {claim_n}")
    if source_n not in SOURCE_CLASSES:
        raise ValueError(f"unknown source_class: {source_n}")

    summary_n = str(summary).strip()
    if not summary_n:
        raise ValueError("summary is required")
    if len(summary_n) > 700:
        raise ValueError("summary exceeds 700 characters")

    signals_n = _norm_list(signals)
    explicit_n = _norm_list(explicit_members)
    bad_members = [m for m in explicit_n if m not in ROSTER]
    if bad_members:
        raise ValueError("unknown explicit member(s): " + ",".join(bad_members))
    evidence_n = _clean_refs(evidence_refs)
    unknowns_n = _clean_refs(unknowns)
    _validate_claim_source(claim_n, source_n, evidence_n)

    dispatch = FAIRY.resolve(
        signals=signals_n,
        explicit_members=explicit_n,
        family_invoked=bool(family_invoked),
        max_material=max_material,
    )

    identity_material = {
        "phase": phase_n,
        "claim_class": claim_n,
        "source_class": source_n,
        "summary": summary_n,
        "signals": signals_n,
        "explicit_members": explicit_n,
        "family_invoked": bool(family_invoked),
        "transaction_id": transaction_id,
        "brain_loop_id": brain_loop_id,
        "source_main": source_main,
        "owner_system": owner_system,
        "next_action": next_action,
        "evidence_refs": evidence_n,
        "unknowns": unknowns_n,
    }

    return {
        "schema": EVENT_SCHEMA,
        "event_id": _event_id(identity_material),
        "transaction_id": transaction_id,
        "brain_loop_id": brain_loop_id,
        "source_main": source_main,
        "phase": phase_n,
        "claim_class": claim_n,
        "source_class": source_n,
        "owner_system": owner_system,
        "summary": summary_n,
        "signals": signals_n,
        "explicit_members": explicit_n,
        "family_invoked": bool(family_invoked),
        "next_action": next_action,
        "evidence_refs": evidence_n,
        "unknowns": unknowns_n,
        "fairyos_dispatch": dispatch,
        "effect_authority": "NONE_CHATOS_PRESENTATION_ONLY",
        "proof_ceiling": PROOF_CEILING,
    }


def render_checkpoint(event: dict[str, Any]) -> list[str]:
    """Return compact observable lines suitable for a chat/execution console.

    This is deterministic presentation of the event packet, not free-form reasoning.
    """
    lines = [
        f"CHATOS {event['phase']} [{event['claim_class']}/{event['source_class']}] {event['summary']}"
    ]
    packets = event["fairyos_dispatch"].get("member_packets", [])
    if packets:
        members = " + ".join(f"{p['member']}:{p['expression']}" for p in packets)
        lines.append(f"FAE {members}")
    unknown_signals = event["fairyos_dispatch"].get("unknown_signals", [])
    if unknown_signals:
        lines.append("UNKNOWN_SIGNAL " + ",".join(unknown_signals))
    if event.get("next_action"):
        lines.append("NEXT " + str(event["next_action"]))
    if event.get("unknowns"):
        lines.append("UNKNOWN " + " | ".join(event["unknowns"]))
    return lines


def main() -> int:
    p = argparse.ArgumentParser(description="Compile a bounded observable ChatOS execution event")
    p.add_argument("--phase", required=True, choices=PHASES)
    p.add_argument("--claim-class", required=True, choices=CLAIM_CLASSES)
    p.add_argument("--source-class", required=True, choices=SOURCE_CLASSES)
    p.add_argument("--summary", required=True)
    p.add_argument("--signals", default="", help="comma-separated FairyOS typed signals")
    p.add_argument("--members", default="", help="comma-separated explicit operators")
    p.add_argument("--family", action="store_true")
    p.add_argument("--transaction-id", default=None)
    p.add_argument("--brain-loop-id", default=None)
    p.add_argument("--source-main", default=None)
    p.add_argument("--owner-system", default=None)
    p.add_argument("--next-action", default=None)
    p.add_argument("--evidence-ref", action="append", default=[])
    p.add_argument("--unknown", action="append", default=[])
    p.add_argument("--max-material", type=int, default=None)
    p.add_argument("--render", action="store_true", help="also emit compact visible checkpoint lines")
    args = p.parse_args()

    event = compile_event(
        phase=args.phase,
        claim_class=args.claim_class,
        source_class=args.source_class,
        summary=args.summary,
        signals=args.signals.split(",") if args.signals else [],
        explicit_members=args.members.split(",") if args.members else [],
        family_invoked=args.family,
        transaction_id=args.transaction_id,
        brain_loop_id=args.brain_loop_id,
        source_main=args.source_main,
        owner_system=args.owner_system,
        next_action=args.next_action,
        evidence_refs=args.evidence_ref,
        unknowns=args.unknown,
        max_material=args.max_material,
    )
    output: dict[str, Any] = {"event": event}
    if args.render:
        output["visible_checkpoint"] = render_checkpoint(event)
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())