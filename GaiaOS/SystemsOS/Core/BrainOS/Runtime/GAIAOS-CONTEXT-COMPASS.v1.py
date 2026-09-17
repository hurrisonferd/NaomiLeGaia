#!/usr/bin/env python3
"""Bounded read-only source traversal for GaiaOS BrainOS Context Compass.

This runtime ranks current checkout files for a natural-language subject. It does
not execute domain effects, infer identity, read secrets, or claim completeness.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

DEFAULT_LIMIT = 10
MAX_LIMIT = 20
MAX_FILE_BYTES = 256_000
MAX_CONTENT_CHARS = 80_000

TEXT_SUFFIXES = {
    ".md",
    ".json",
    ".py",
    ".yaml",
    ".yml",
    ".txt",
    ".toml",
}

EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
}

SENSITIVE_PATH_TOKENS = {
    ".env",
    "secret",
    "secrets",
    "credential",
    "credentials",
    "private-key",
    "private_key",
    "apikey",
    "api_key",
}

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
    "map": ("brainos", "context", "compass", "source", "path"),
    "source": ("current", "readme", "version", "source", "contract"),
    "presentation": ("chatos", "presentation", "gold", "prosody"),
    "wild": ("presentation", "gold", "chatos"),
    "emoji": ("emojios", "expression", "registry"),
    "carrier": ("api", "openapi", "gpt", "mcp", "load"),
    "api": ("api", "openapi", "carrier"),
    "load": ("load", "current", "bootstrap", "instructions"),
}

OWNER_NAMES = {
    "BrainOS",
    "ChatOS",
    "ConvoOS",
    "MemberContinuityOS",
    "FairyOS",
    "EmojiOS",
    "GaiaOS",
}


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
    return expanded[:24]


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
    explicit = [
        repo_root / "GAIAOS-LOAD.md",
        repo_root / "README.md",
        repo_root / "render.yaml",
    ]
    files: list[Path] = []

    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(repo_root)
            if any(part in EXCLUDED_DIRS for part in rel.parts):
                continue
            if _is_sensitive(rel):
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

    path_hits = 0
    content_hits = 0
    for token in tokens:
        if token in rel_norm:
            path_hits += 1
        if token in content_norm:
            content_hits += 1

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

    if "/Protocols/" in rel or "/Protocols/".lower() in rel.lower():
        score += 5
        reasons.append("protocol_salience")
    if "/Runtime/" in rel or "/Runtime/".lower() in rel.lower():
        score += 4
        reasons.append("runtime_salience")
    if rel.startswith("GaiaOS/"):
        score += 5
        reasons.append("gaia_native_path")

    # Prevent generic boilerplate files from winning with no actual query overlap.
    if path_hits == 0 and content_hits == 0 and not (subject_norm and subject_norm in content_norm):
        return 0, []

    return score, reasons


def query_context(repo_root: Path, subject: str, limit: int = DEFAULT_LIMIT) -> dict[str, Any]:
    root = repo_root.resolve()
    limit = max(1, min(int(limit), MAX_LIMIT))
    tokens = _tokens(subject)
    ranked: list[dict[str, Any]] = []

    for path in _candidate_files(root):
        rel = path.relative_to(root).as_posix()
        content = _read_text(path)
        score, reasons = _score(rel, content, subject, tokens)
        if score <= 0:
            continue
        ranked.append(
            {
                "path": rel,
                "score": score,
                "reasons": reasons,
                "owner_candidates": _owner_candidates(rel),
            }
        )

    ranked.sort(key=lambda item: (-item["score"], item["path"].lower()))
    selected = ranked[:limit]

    owners: list[str] = []
    for item in selected:
        for owner in item["owner_candidates"]:
            if owner not in owners:
                owners.append(owner)

    unknowns: list[str] = []
    if not tokens:
        unknowns.append("subject produced no searchable tokens")
    if not selected:
        unknowns.append("no bounded current-source candidates matched; empty search is not proof of absence")

    return {
        "schema": "gaiaos.brainos.context-compass.packet.v1",
        "authority": "NAOMI",
        "mode": "READ_ONLY",
        "subject": subject,
        "query_tokens": tokens,
        "owner_candidates": owners,
        "denominator": {
            "repo_root": str(root),
            "candidate_file_count": len(_candidate_files(root)),
            "scope": ["GaiaOS/", "api/", ".github/", "GAIAOS-LOAD.md", "README.md", "render.yaml"],
        },
        "context_pack": selected,
        "unknowns": unknowns,
        "effect_authority": "NONE_READ_ONLY",
        "claim_ceiling": (
            "Bounded lexical/alias-assisted current-checkout ranking only. "
            "A hit is not semantic authority; a miss is not proof of absence; "
            "no identity, memory, or external effect is created."
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
    packet = query_context(repo_root, " ".join(args.subject), args.limit)
    print(json.dumps(packet, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
