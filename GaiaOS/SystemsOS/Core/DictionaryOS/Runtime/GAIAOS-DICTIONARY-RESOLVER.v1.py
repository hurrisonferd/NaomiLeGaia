#!/usr/bin/env python3
"""GaiaOS DictionaryOS bounded term/alias resolver."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

REGISTRY = "GaiaOS/SystemsOS/Core/DictionaryOS/Registry/GAIA-TERMS.v1.json"


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _tokens(text: str) -> set[str]:
    return {token for token in _norm(text).split() if len(token) >= 2}


def resolve_terms(repo_root: Path, subject: str, limit: int = 8) -> dict[str, Any]:
    root = repo_root.resolve()
    data = json.loads((root / REGISTRY).read_text(encoding="utf-8"))
    subject_norm = _norm(subject)
    subject_tokens = _tokens(subject)
    ranked: list[dict[str, Any]] = []

    for obj in data.get("objects", []):
        labels = [obj.get("term", ""), *obj.get("aliases", [])]
        score = 0
        reasons: list[str] = []
        for label in labels:
            label_norm = _norm(label)
            if not label_norm:
                continue
            if subject_norm == label_norm:
                score = max(score, 100)
                reasons.append(f"exact:{label}")
            elif label_norm in subject_norm:
                score = max(score, 70 + min(len(label_norm), 20))
                reasons.append(f"phrase:{label}")
            else:
                overlap = len(subject_tokens & _tokens(label))
                if overlap:
                    score = max(score, overlap * 18)
                    reasons.append(f"token_overlap:{label}:{overlap}")
        if score:
            ranked.append({
                "id": obj["id"],
                "term": obj["term"],
                "score": score,
                "reasons": reasons,
                "source_paths": obj.get("source_paths", []),
            })

    ranked.sort(key=lambda item: (-item["score"], item["id"]))
    selected = ranked[: max(1, min(int(limit), 20))]
    return {
        "schema": "gaiaos.dictionaryos.resolution-packet.v1",
        "authority": "NAOMI",
        "subject": subject,
        "candidates": selected,
        "unknown": not bool(selected),
        "effect_authority": "NONE_READ_ONLY",
        "claim_ceiling": "Alias-assisted candidate resolution only; candidates do not create authority or identity."
    }


def _find_root(start: Path) -> Path:
    for candidate in [start.resolve(), *start.resolve().parents]:
        if (candidate / REGISTRY).exists():
            return candidate
    raise SystemExit("GAIAOS_DICTIONARY_ERROR repository root not found")


def main() -> None:
    parser = argparse.ArgumentParser(description="GaiaOS DictionaryOS resolver")
    parser.add_argument("subject", nargs="+")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args()
    root = args.repo_root.resolve() if args.repo_root else _find_root(Path(__file__))
    print(json.dumps(resolve_terms(root, " ".join(args.subject), args.limit), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
