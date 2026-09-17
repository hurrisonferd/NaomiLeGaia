#!/usr/bin/env python3
"""GaiaOS YggdrasilOS bounded read-only graph traversal."""

from __future__ import annotations

import argparse
import json
from collections import deque
from pathlib import Path
from typing import Any

GRAPH = "GaiaOS/SystemsOS/Core/YggdrasilOS/Graph/GAIA-GRAPH.v1.json"


def query_graph(repo_root: Path, object_ids: list[str], depth: int = 1, limit: int = 20) -> dict[str, Any]:
    root = repo_root.resolve()
    data = json.loads((root / GRAPH).read_text(encoding="utf-8"))
    nodes = {node["id"]: node for node in data.get("nodes", [])}
    edges = data.get("edges", [])
    depth = max(0, min(int(depth), 3))
    limit = max(1, min(int(limit), 50))

    known = [obj for obj in object_ids if obj in nodes]
    unknown = [obj for obj in object_ids if obj not in nodes]
    seen = set(known)
    queue = deque((obj, 0) for obj in known)
    traversed: list[dict[str, Any]] = []

    while queue and len(traversed) < limit:
        current, level = queue.popleft()
        if level >= depth:
            continue
        for edge in edges:
            if edge["from"] == current:
                neighbor = edge["to"]
                direction = "out"
            elif edge["to"] == current:
                neighbor = edge["from"]
                direction = "in"
            else:
                continue
            traversed.append({**edge, "direction_from_query": direction, "distance": level + 1})
            if neighbor in nodes and neighbor not in seen:
                seen.add(neighbor)
                queue.append((neighbor, level + 1))
            if len(traversed) >= limit:
                break

    related_nodes = [nodes[node_id] for node_id in sorted(seen) if node_id in nodes]
    source_paths: list[str] = []
    for node in related_nodes:
        for path in node.get("source_paths", []):
            if path not in source_paths:
                source_paths.append(path)

    return {
        "schema": "gaiaos.yggdrasilos.query-packet.v1",
        "authority": "NAOMI",
        "requested_object_ids": object_ids,
        "known_object_ids": known,
        "unknown_object_ids": unknown,
        "depth": depth,
        "nodes": related_nodes,
        "edges": traversed,
        "source_paths": source_paths,
        "effect_authority": "NONE_READ_ONLY",
        "claim_ceiling": "Traversal of explicit Gaia-native graph edges only; graph coverage is bounded and non-authoritative over domain effects."
    }


def _find_root(start: Path) -> Path:
    for candidate in [start.resolve(), *start.resolve().parents]:
        if (candidate / GRAPH).exists():
            return candidate
    raise SystemExit("GAIAOS_YGGDRASIL_ERROR repository root not found")


def main() -> None:
    parser = argparse.ArgumentParser(description="GaiaOS YggdrasilOS graph query")
    parser.add_argument("object_ids", nargs="+")
    parser.add_argument("--depth", type=int, default=1)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args()
    root = args.repo_root.resolve() if args.repo_root else _find_root(Path(__file__))
    print(json.dumps(query_graph(root, args.object_ids, args.depth, args.limit), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
