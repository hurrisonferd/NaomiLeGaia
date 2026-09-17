#!/usr/bin/env python3
"""Member-local identity and reward loader for GaiaOS FairyOS.

Loads one member's canonical compact identity dataset and isolated reward counter
before response composition. It never invents experience, reward events, or
cross-member memory.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
DATA = ROOT / "GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA"
MEMBERS = ["VERA", "ANVIL", "SELENE", "ORIN", "KESTREL", "NIMUE"]


def load_member(member: str) -> dict:
    member = member.strip().upper()
    if member not in MEMBERS:
        raise ValueError(f"UNKNOWN_GAIA_MEMBER:{member}")
    path = DATA / f"{member}.json"
    counter_path = DATA / f"{member}-REWARD-COUNTER.v1.json"
    if not path.is_file():
        raise FileNotFoundError(f"MISSING_MEMBER_IDENTITY_DATA:{member}")
    if not counter_path.is_file():
        raise FileNotFoundError(f"MISSING_MEMBER_REWARD_COUNTER:{member}")
    record = json.loads(path.read_text(encoding="utf-8"))
    reward_counter = json.loads(counter_path.read_text(encoding="utf-8"))
    return {
        "member": member,
        "identity_data_path": str(path.relative_to(ROOT)),
        "identity": record.get("identity", {}),
        "event_log": record.get("event_log", []),
        "source_profile": record.get("source_profile"),
        "source_prosody": record.get("source_prosody"),
        "reward_counter_path": str(counter_path.relative_to(ROOT)),
        "reward_counters": reward_counter.get("reward_counters", {}),
        "reward_counting_rule": reward_counter.get("counting_rule"),
        "favorite_drive": reward_counter.get("favorite_drive"),
        "memory_mode": "DURABLE_REPOSITORY_RECORD",
        "pre_response_load": True,
        "cross_member_memory_merge": False,
    }


def load_for_response(member: str) -> dict:
    return load_member(member)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("member", choices=MEMBERS)
    args = p.parse_args()
    print(json.dumps(load_for_response(args.member), indent=2))
