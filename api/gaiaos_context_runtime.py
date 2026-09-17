"""Pure read-only semantic navigation for the GaiaOS carrier.

The carrier receives canonical DictionaryOS and YggdrasilOS JSON from one
resolved Git commit and composes a bounded context packet. This module has no
network, host, identity, memory, or domain-effect authority.
"""

from __future__ import annotations

import re
from collections import deque
from typing import Any

MAX_CANDIDATES = 20
MAX_CONTEXT_PATHS = 30
MAX_DEPTH = 3


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


def _tokens(text: str) -> set[str]:
    return {token for token in _norm(text).split() if len(token) >= 2}


def resolve_terms(registry: dict[str, Any], subject: str, limit: int = 8) -> list[dict[str, Any]]:
    subject_norm = _norm(subject)
    subject_tokens = _tokens(subject)
    ranked: list[dict[str, Any]] = []

    for obj in registry.get("objects", []):
        if not isinstance(obj, dict) or not isinstance(obj.get("id"), str):
            continue
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
                "term": obj.get("term", obj["id"]),
                "score": score,
                "reasons": reasons,
                "source_paths": [str(path) for path in obj.get("source_paths", []) if isinstance(path, str)],
            })

    ranked.sort(key=lambda item: (-item["score"], item["id"]))
    return ranked[: max(1, min(int(limit), MAX_CANDIDATES))]


def query_graph(
    graph: dict[str, Any],
    object_ids: list[str],
    depth: int = 1,
    limit: int = 30,
) -> dict[str, Any]:
    nodes = {
        node["id"]: node
        for node in graph.get("nodes", [])
        if isinstance(node, dict) and isinstance(node.get("id"), str)
    }
    edges = [edge for edge in graph.get("edges", []) if isinstance(edge, dict)]
    depth = max(0, min(int(depth), MAX_DEPTH))
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
            source = edge.get("from")
            target = edge.get("to")
            if source == current:
                neighbor = target
                direction = "out"
            elif target == current:
                neighbor = source
                direction = "in"
            else:
                continue
            if not isinstance(neighbor, str):
                continue
            traversed.append({
                "from": source,
                "to": target,
                "type": edge.get("type", "RELATED"),
                "direction_from_query": direction,
                "distance": level + 1,
            })
            if neighbor in nodes and neighbor not in seen:
                seen.add(neighbor)
                queue.append((neighbor, level + 1))
            if len(traversed) >= limit:
                break

    related_nodes = [nodes[node_id] for node_id in sorted(seen) if node_id in nodes]
    source_paths: list[str] = []
    for node in related_nodes:
        for path in node.get("source_paths", []):
            if isinstance(path, str) and path not in source_paths:
                source_paths.append(path)

    return {
        "known_object_ids": known,
        "unknown_object_ids": unknown,
        "nodes": related_nodes,
        "edges": traversed,
        "source_paths": source_paths,
    }


def build_context_packet(
    registry: dict[str, Any],
    graph: dict[str, Any],
    subject: str,
    *,
    source: str,
    limit: int = 10,
    depth: int = 1,
) -> dict[str, Any]:
    limit = max(1, min(int(limit), MAX_CONTEXT_PATHS))
    dictionary_candidates = resolve_terms(registry, subject, min(limit, 8))
    object_ids = [item["id"] for item in dictionary_candidates]
    graph_packet = query_graph(graph, object_ids, depth=depth, limit=max(limit * 3, 12))

    path_scores: dict[str, int] = {}
    path_reasons: dict[str, list[str]] = {}
    for candidate in dictionary_candidates:
        candidate_score = int(candidate.get("score", 0))
        for path in candidate.get("source_paths", []):
            path_scores[path] = max(path_scores.get(path, 0), 100 + candidate_score)
            path_reasons.setdefault(path, []).append(f"dictionary:{candidate['id']}")

    for node in graph_packet.get("nodes", []):
        node_id = str(node.get("id", "UNKNOWN"))
        for path in node.get("source_paths", []):
            if not isinstance(path, str):
                continue
            path_scores[path] = max(path_scores.get(path, 0), 50)
            path_reasons.setdefault(path, []).append(f"graph:{node_id}")

    context_pack = [
        {"path": path, "score": score, "reasons": path_reasons.get(path, [])}
        for path, score in path_scores.items()
    ]
    context_pack.sort(key=lambda item: (-item["score"], item["path"].lower()))
    context_pack = context_pack[:limit]

    unknowns: list[str] = []
    if not dictionary_candidates:
        unknowns.append("no DictionaryOS candidate matched; empty resolution is not proof of absence")
    if dictionary_candidates and not graph_packet.get("known_object_ids"):
        unknowns.append("DictionaryOS candidates did not resolve to current YggdrasilOS graph nodes")

    return {
        "schema": "gaiaos.brainos.remote-context-packet.v1",
        "authority": "NAOMI",
        "source": source,
        "mode": "SOURCE_PINNED_DICTIONARY_GRAPH_READ_ONLY",
        "subject": subject,
        "dictionary_candidates": dictionary_candidates,
        "graph": {
            "known_object_ids": graph_packet.get("known_object_ids", []),
            "unknown_object_ids": graph_packet.get("unknown_object_ids", []),
            "edges": graph_packet.get("edges", []),
        },
        "context_pack": context_pack,
        "unknowns": unknowns,
        "effect_authority": "NONE_READ_ONLY",
        "laws": [
            "TERM HIT != AUTHORITY",
            "GRAPH EDGE != EFFECT",
            "REMOTE CONTEXT PACK != DURABLE MEMORY",
            "EMPTY RESOLUTION != ABSENCE",
            "NAOMI RETAINS FINAL AUTHORITY",
        ],
        "claim_ceiling": (
            "Source-pinned DictionaryOS and explicit YggdrasilOS navigation only. "
            "The carrier does not claim local-checkout lexical traversal, semantic completeness, "
            "durable memory, identity settlement, or domain effects."
        ),
    }
