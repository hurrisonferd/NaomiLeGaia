#!/usr/bin/env python3
"""Bounded read-only source traversal for GaiaOS BrainOS Context Compass.

DictionaryOS resolves Naomi-natural names and aliases, YggdrasilOS contributes
explicit relationship paths, and lexical ranking fills the remaining bounded
context pack. None of these layers grants authority or executes effects.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path
from typing import Any

DEFAULT_LIMIT = 10
MAX_LIMIT = 20
MAX_FILE_BYTES = 256_000
MAX_CONTENT_CHARS = 80_000

TEXT_SUFFIXES = {".md", ".json", ".py", ".yaml", ".yml", ".txt", ".toml"}
EXCLUDED_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache"}
SENSITIVE_PATH_TOKENS = {".env", "secret", "secrets", "credential", "credentials", "private-key", "private_key", "apikey", "api_key"}

SEMANTIC_HINTS: dict[str, tuple[str, ...]] = {
    "council": ("council", "fairyos", "operator", "dispatch"),
    "operator": ("fairyos", "operator", "prosody", "dispatch"),
    "fairy": ("fairyos", "operator", "council"),
    "conversation": ("chatos", "convoos", "conversation", "reentry"),
    "chat": ("chatos", "conversation", "carrier"),
    "reentry": ("convoos", "reentry", "thread", "home", "sidequest"),
    "resume": ("convoos", "reentry", "thread", "home"),
    "memory": ("membercontinuityos", "convoos", "warm", "continuity"),
    "continuity": ("membercontinuityos", "convoos", "warm", "reentry"),
    "brain": ("brainos", "context", "compass", "support"),
    "map": ("yggdrasilos", "graph", "context", "compass", "source", "path"),
    "graph": ("yggdrasilos", "relationships", "nodes", "edges"),
    "dictionary": ("dictionaryos", "term", "alias", "semantic"),
    "alias": ("dictionaryos", "term", "semantic"),
    "source": ("current", "readme", "version", "source", "contract"),
    "presentation": ("chatos", "presentation", "gold", "prosody"),
    "wild": ("presentation", "gold", "chatos"),
    "emoji": ("emojios", "expression", "registry"),
    "carrier": ("api", "openapi", "gpt", "mcp", "load"),
    "api": ("api", "openapi", "carrier"),
    "load": ("load", "current", "bootstrap", "instructions"),
}

OWNER_NAMES = {
    "BrainOS", "ChatOS", "ConvoOS", "MemberContinuityOS", "FairyOS",
    "EmojiOS", "DictionaryOS", "YggdrasilOS", "GaiaOS",
}

DICTIONARY_RUNTIME = "GaiaOS/SystemsOS/Core/DictionaryOS/Runtime/GAIAOS-DICTIONARY-RESOLVER.v1.py"
YGGDRASIL_RUNTIME = "GaiaOS/SystemsOS/Core/YggdrasilOS/Runtime/GAIAOS-YGGDRASIL-QUERY.v1.py"


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _tokens(subject: str) -> list[str]:
    base = [token for token in _normalize(subject).split() if len(token) >= 2]
    expanded: list[str] = []
    for token in base:
        if token not in expanded:
            expanded.append(token)
        for hint in SEMANTIC_HINTS.get(token, ()):
            if hint not in expanded:
                expanded.append(hint)
    return expanded[:32]


def _is_sensitive(path: Path) -> bool:
    lowered_parts = [part.lower() for part in path.parts]
    for part in lowered_parts:
        if part in SENSITIVE_PATH_TOKENS:
            return True
        if any(token in part for token in SENSITIVE_PATH_TOKENS if token != ".env"):
            return True
    return any(part.startswith(".env") for part in lowered_parts)


def _candidate_files(repo_root: Path) -> list[Path]:
    roots = [repo_root / "GaiaOS", repo_root / "api", repo_root / ".github"]
    explicit = [repo_root / "GAIAOS-LOAD.md", repo_root / "README.md", repo_root / "render.yaml"]
    files: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(repo_root)
            if any(part in EXCLUDED_DIRS for part in rel.parts) or _is_sensitive(rel):
                continue
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            try:
                if path.stat().st_size > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            files.append(path)
    for path in explicit:
        if path.is_file() and not _is_sensitive(path.relative_to(repo_root)):
            files.append(path)
    unique = {path.resolve(): path for path in files}
    return sorted(unique.values(), key=lambda p: str(p.relative_to(repo_root)).lower())


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")[:MAX_CONTENT_CHARS]
    except (OSError, UnicodeDecodeError):
        return ""


def _owner_candidates(rel: str) -> list[str]:
    found: list[str] = []
    lower = rel.lower()
    for owner in OWNER_NAMES:
        if owner.lower() in lower:
            found.append(owner)
    if not found and rel.startswith("api/"):
        found.append("GaiaOS carrier")
    return found


def _load_runtime(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load runtime: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _navigation_context(repo_root: Path, subject: str) -> dict[str, Any]:
    dictionary = _load_runtime(repo_root / DICTIONARY_RUNTIME, "gaia_dictionary_runtime")
    yggdrasil = _load_runtime(repo_root / YGGDRASIL_RUNTIME, "gaia_yggdrasil_runtime")
    resolution = dictionary.resolve_terms(repo_root, subject, 6)
    object_ids = [item["id"] for item in resolution.get("candidates", [])]
    graph = yggdrasil.query_graph(repo_root, object_ids, depth=1, limit=24) if object_ids else {
        "known_object_ids": [], "unknown_object_ids": [], "nodes": [], "edges": [], "source_paths": []
    }

    direct_paths: list[str] = []
    for candidate in resolution.get("candidates", []):
        for path in candidate.get("source_paths", []):
            if path not in direct_paths:
                direct_paths.append(path)
    related_paths = [path for path in graph.get("source_paths", []) if path not in direct_paths]
    return {"resolution": resolution, "graph": graph, "direct_paths": direct_paths, "related_paths": related_paths}


def _score(rel: str, content: str, subject: str, tokens: list[str]) -> tuple[int, list[str]]:
    rel_norm = _normalize(rel)
    content_norm = _normalize(content)
    subject_norm = _normalize(subject)
    score = 0
    reasons: list[str] = []
    if subject_norm and subject_norm in rel_norm:
        score += 60
        reasons.append("exact_subject_in_path")
    if subject_norm and subject_norm in content_norm:
        score += 30
        reasons.append("exact_subject_in_content")
    path_hits = sum(1 for token in tokens if token in rel_norm)
    content_hits = sum(1 for token in tokens if token in content_norm)
    if path_hits:
        score += min(path_hits, 8) * 10
        reasons.append(f"path_token_hits:{path_hits}")
    if content_hits:
        score += min(content_hits, 10) * 4
        reasons.append(f"content_token_hits:{content_hits}")
    name = Path(rel).name.upper()
    if name.startswith("CURRENT"):
        score += 18
        reasons.append("current_pointer_salience")
    elif name == "README.MD":
        score += 14
        reasons.append("readme_salience")
    elif name.startswith("VERSION"):
        score += 10
        reasons.append("version_salience")
    if "/protocols/" in rel.lower():
        score += 5
        reasons.append("protocol_salience")
    if "/runtime/" in rel.lower():
        score += 4
        reasons.append("runtime_salience")
    if rel.startswith("GaiaOS/"):
        score += 5
        reasons.append("gaia_native_path")
    if path_hits == 0 and content_hits == 0 and not (subject_norm and subject_norm in content_norm):
        return 0, []
    return score, reasons


def query_context(repo_root: Path, subject: str, limit: int = DEFAULT_LIMIT) -> dict[str, Any]:
    root = repo_root.resolve()
    limit = max(1, min(int(limit), MAX_LIMIT))
    tokens = _tokens(subject)
    ranked: list[dict[str, Any]] = []
    unknowns: list[str] = []

    try:
        navigation = _navigation_context(root, subject)
    except Exception as exc:
        navigation = {"resolution": {"candidates": []}, "graph": {"nodes": [], "edges": []}, "direct_paths": [], "related_paths": []}
        unknowns.append(f"navigation support unavailable: {type(exc).__name__}")

    for candidate in navigation["resolution"].get("candidates", []):
        for token in _tokens(candidate.get("term", "")):
            if token not in tokens:
                tokens.append(token)
    tokens = tokens[:32]

    direct = set(navigation["direct_paths"])
    related = set(navigation["related_paths"])
    candidates = _candidate_files(root)
    for path in candidates:
        rel = path.relative_to(root).as_posix()
        content = _read_text(path)
        score, reasons = _score(rel, content, subject, tokens)
        if rel in direct:
            score += 55
            reasons.append("dictionary_direct_source")
        if rel in related:
            score += 25
            reasons.append("yggdrasil_related_source")
        if score <= 0:
            continue
        ranked.append({"path": rel, "score": score, "reasons": reasons, "owner_candidates": _owner_candidates(rel)})

    ranked.sort(key=lambda item: (-item["score"], item["path"].lower()))
    selected = ranked[:limit]
    owners: list[str] = []
    for item in selected:
        for owner in item["owner_candidates"]:
            if owner not in owners:
                owners.append(owner)

    if not tokens:
        unknowns.append("subject produced no searchable tokens")
    if not selected:
        unknowns.append("no bounded current-source candidates matched; empty search is not proof of absence")

    return {
        "schema": "gaiaos.brainos.context-compass.packet.v2",
        "authority": "NAOMI",
        "mode": "READ_ONLY",
        "subject": subject,
        "query_tokens": tokens,
        "dictionary_candidates": [
            {"id": item["id"], "term": item["term"], "score": item["score"]}
            for item in navigation["resolution"].get("candidates", [])
        ],
        "graph_object_ids": navigation["graph"].get("known_object_ids", []),
        "graph_edges_considered": len(navigation["graph"].get("edges", [])),
        "owner_candidates": owners,
        "denominator": {
            "repo_root": str(root),
            "candidate_file_count": len(candidates),
            "scope": ["GaiaOS/", "api/", ".github/", "GAIAOS-LOAD.md", "README.md", "render.yaml"],
            "dictionaryos": "ACTIVE_READ_ONLY",
            "yggdrasilos": "ACTIVE_READ_ONLY",
        },
        "context_pack": selected,
        "unknowns": unknowns,
        "effect_authority": "NONE_READ_ONLY",
        "claim_ceiling": (
            "Bounded DictionaryOS alias resolution + explicit YggdrasilOS graph traversal + lexical current-checkout ranking. "
            "A hit is not semantic authority; a miss is not proof of absence; no identity, memory, or external effect is created."
        ),
    }


def _find_repo_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "GaiaOS").is_dir() and (candidate / "GAIAOS-LOAD.md").exists():
            return candidate
    raise SystemExit("GAIAOS_CONTEXT_COMPASS_ERROR repository root not found")


def main() -> None:
    parser = argparse.ArgumentParser(description="GaiaOS bounded Context Compass")
    parser.add_argument("subject", nargs="+", help="Natural-language subject to resolve")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args()
    repo_root = args.repo_root.resolve() if args.repo_root else _find_repo_root(Path(__file__))
    print(json.dumps(query_context(repo_root, " ".join(args.subject), args.limit), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
