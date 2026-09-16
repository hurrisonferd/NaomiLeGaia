#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

VALID_STANCES = {"AGREE", "OBJECT", "CONTRADICT", "PROPOSE", "QUESTION"}


def reduce(issue: str, contributions: list[dict[str, Any]]) -> dict[str, Any]:
    """Reduce council contributions without deleting minority positions."""
    normalized: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in contributions:
        speaker = str(item.get("speaker") or "").strip().upper()
        stance = str(item.get("stance") or "").upper()
        text = str(item.get("text") or "").strip()
        if not speaker or not text or stance not in VALID_STANCES:
            raise ValueError("COUNCIL_CONTRIBUTION_REQUIRES_SPEAKER_VALID_STANCE_TEXT")
        key = (speaker, stance, text)
        if key in seen:
            continue
        seen.add(key)
        normalized.append({"speaker": speaker, "stance": stance, "text": text})

    normalized.sort(key=lambda x: (x["speaker"], x["stance"], x["text"]))

    def group(stance: str) -> list[dict[str, str]]:
        return [x for x in normalized if x["stance"] == stance]

    participants = sorted({x["speaker"] for x in normalized})
    return {
        "schema": "gaiaos.chatos.council-dissent-packet.v1",
        "authority": "NAOMI",
        "issue": str(issue),
        "participants": participants,
        "agreements": group("AGREE"),
        "minority_objections": group("OBJECT"),
        "contradictions": group("CONTRADICT"),
        "unique_proposals": group("PROPOSE"),
        "unresolved_questions": [x["text"] for x in group("QUESTION")],
        "recommended_cut": None,
        "source_contributions": normalized,
        "law": "SYNTHESIS_MAY_NOT_DELETE_DISSENT",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Preserve Gaia Council dissent without synthetic unanimity")
    parser.add_argument("contributions", type=Path)
    parser.add_argument("--issue", required=True)
    args = parser.parse_args()
    value = json.loads(args.contributions.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError("CONTRIBUTIONS_ROOT_MUST_BE_ARRAY")
    print(json.dumps(reduce(args.issue, value), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
