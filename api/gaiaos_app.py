"""GaiaOS carrier extension: source-pinned semantic context navigation.

This module imports the stable carrier app/MCP server, then adds one bounded
read-only context surface backed by canonical DictionaryOS + YggdrasilOS data.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import Header, HTTPException

from gaiaos_api import (
    RAW_BASE,
    REPOSITORY,
    _authorize,
    _request,
    _resolve_commit,
    app,
    mcp,
)
from gaiaos_context_runtime import build_context_packet

NAVIGATION_PATHS = {
    "GaiaOS/SystemsOS/Core/DictionaryOS/Registry/GAIA-TERMS.v1.json",
    "GaiaOS/SystemsOS/Core/YggdrasilOS/Graph/GAIA-GRAPH.v1.json",
}


def _navigation_json(commit: str, path: str) -> dict[str, Any]:
    if path not in NAVIGATION_PATHS:
        raise HTTPException(status_code=400, detail="Path is not part of the GaiaOS navigation surface")
    try:
        value = json.loads(_request(f"{RAW_BASE}/{REPOSITORY}/{commit}/{path}").decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"Canonical navigation source is not UTF-8: {path}") from exc
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"Canonical navigation JSON is invalid: {path}") from exc
    if not isinstance(value, dict):
        raise HTTPException(status_code=502, detail=f"Canonical navigation JSON root is not an object: {path}")
    return value


def _context_packet(subject: str, limit: int = 10, depth: int = 1) -> dict[str, Any]:
    subject = str(subject).strip()
    if not subject:
        raise HTTPException(status_code=422, detail="subject must not be empty")
    commit = _resolve_commit()
    registry = _navigation_json(
        commit,
        "GaiaOS/SystemsOS/Core/DictionaryOS/Registry/GAIA-TERMS.v1.json",
    )
    graph = _navigation_json(
        commit,
        "GaiaOS/SystemsOS/Core/YggdrasilOS/Graph/GAIA-GRAPH.v1.json",
    )
    return build_context_packet(
        registry,
        graph,
        subject,
        source=f"{REPOSITORY}@{commit}",
        limit=limit,
        depth=depth,
    )


@mcp.tool()
def gaia_context(subject: str, limit: int = 10, depth: int = 1) -> dict[str, Any]:
    """Resolve a natural GaiaOS subject through source-pinned DictionaryOS and YggdrasilOS."""
    return _context_packet(subject, limit, depth)


@app.get("/gaiaos/context", operation_id="getGaiaContext")
def gaia_context_http(
    subject: str,
    limit: int = 10,
    depth: int = 1,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """Read-only source-pinned GaiaOS semantic context query."""
    _authorize(authorization)
    return _context_packet(subject, limit, depth)
