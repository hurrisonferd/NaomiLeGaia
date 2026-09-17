"""GaiaOS carrier extension: deployed-checkout source and semantic navigation.

This module imports the stable carrier app/MCP server, then binds canonical GaiaOS
reads to the exact deployed repository checkout before adding the bounded read-only
Context Compass surface. Live council, operator, dispatch, BrainOS, loader, chat
bootstrap, and context reads therefore do not require a second outbound GitHub fetch
when the requested canonical source is already present in the deployed checkout.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import Header, HTTPException
from starlette.routing import Mount

import gaiaos_api as base
from gaiaos_context_runtime import build_context_packet

EXTENSION_VERSION = "1.5.0"
CONTEXT_MODE = "SOURCE_PINNED_DICTIONARY_GRAPH_READ_ONLY"
DEPLOYED_ROOT = Path(__file__).resolve().parent.parent

# Preserve the original remote source functions as bounded fallbacks. The deployed
# checkout is authoritative for the running build; GitHub is only consulted when a
# canonical loader path is unexpectedly absent locally.
_REMOTE_RESOLVE_COMMIT = base._resolve_commit
_REMOTE_FETCH_FILE = base._fetch_file


def _deployed_commit() -> str:
    commit = (
        os.getenv("RENDER_GIT_COMMIT")
        or os.getenv("GIT_COMMIT")
        or os.getenv("SOURCE_COMMIT")
    )
    if commit:
        return commit
    try:
        return _REMOTE_RESOLVE_COMMIT()
    except HTTPException:
        return "DEPLOYED_CHECKOUT"


def _safe_local_target(path: str) -> Path:
    target = (DEPLOYED_ROOT / path).resolve()
    try:
        target.relative_to(DEPLOYED_ROOT)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Canonical source path escaped deployed source root") from exc
    return target


def _deployed_fetch_file(commit: str, path: str) -> str:
    if path not in base.LOAD_PATHS:
        raise HTTPException(status_code=400, detail="Path is not part of the canonical loader surface")

    target = _safe_local_target(path)
    try:
        return target.read_text(encoding="utf-8")
    except FileNotFoundError:
        # A missing deployed file is unusual, but keep the original source-backed
        # behavior available rather than silently fabricating content.
        if commit != "DEPLOYED_CHECKOUT":
            return _REMOTE_FETCH_FILE(commit, path)
        raise HTTPException(status_code=500, detail=f"Deployed canonical source missing: {path}")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"Deployed canonical source is not UTF-8: {path}") from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Unable to read deployed canonical source: {path}") from exc


# All existing base loader/council/MCP route functions resolve these globals at call
# time, so this single binding hardens the entire live source-reading surface.
base._resolve_commit = _deployed_commit
base._fetch_file = _deployed_fetch_file

base.APP_VERSION = EXTENSION_VERSION
app = base.app
mcp = base.mcp
app.version = EXTENSION_VERSION
app.description = (
    "GaiaOS deployed-checkout source loader plus source-backed council/dispatch, "
    "BrainOS/chat-control, DictionaryOS/YggdrasilOS context navigation, warm-continuity "
    "surfaces, a web carrier backed by the OpenAI Responses API, and a read-only MCP carrier."
)

# The base carrier historically mounted FastMCP at /mcp while FastMCP itself also
# used its default /mcp transport path, yielding /mcp/mcp. MCP Python SDK 1.x uses
# the settings object for this mounted-path override. Replace only that Mount so the
# public endpoint advertised by /health is genuinely /mcp.
app.routes[:] = [
    route
    for route in app.routes
    if not (isinstance(route, Mount) and getattr(route, "path", None) == "/mcp")
]
mcp.settings.streamable_http_path = "/"
app.mount("/mcp", mcp.streamable_http_app())
app.openapi_schema = None

NAVIGATION_PATHS = {
    "GaiaOS/SystemsOS/Core/DictionaryOS/Registry/GAIA-TERMS.v1.json",
    "GaiaOS/SystemsOS/Core/YggdrasilOS/Graph/GAIA-GRAPH.v1.json",
}


def _deployed_source() -> str:
    return f"{base.REPOSITORY}@{_deployed_commit()}"


def _navigation_json(path: str) -> dict[str, Any]:
    if path not in NAVIGATION_PATHS:
        raise HTTPException(status_code=400, detail="Path is not part of the GaiaOS navigation surface")

    target = _safe_local_target(path)
    try:
        value = json.loads(target.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=f"Deployed navigation source missing: {path}") from exc
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"Deployed navigation source is not UTF-8: {path}") from exc
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"Deployed navigation JSON is invalid: {path}") from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Unable to read deployed navigation source: {path}") from exc

    if not isinstance(value, dict):
        raise HTTPException(status_code=500, detail=f"Deployed navigation JSON root is not an object: {path}")
    return value


def _context_packet(subject: str, limit: int = 10, depth: int = 1) -> dict[str, Any]:
    subject = str(subject).strip()
    if not subject:
        raise HTTPException(status_code=422, detail="subject must not be empty")

    registry = _navigation_json(
        "GaiaOS/SystemsOS/Core/DictionaryOS/Registry/GAIA-TERMS.v1.json"
    )
    graph = _navigation_json(
        "GaiaOS/SystemsOS/Core/YggdrasilOS/Graph/GAIA-GRAPH.v1.json"
    )
    packet = build_context_packet(
        registry,
        graph,
        subject,
        source=_deployed_source(),
        limit=limit,
        depth=depth,
    )
    packet["carrier_mode"] = CONTEXT_MODE
    packet["carrier_version"] = EXTENSION_VERSION
    packet["source_binding"] = "DEPLOYED_CHECKOUT"
    return packet


@mcp.tool()
def gaia_context(subject: str, limit: int = 10, depth: int = 1) -> dict[str, Any]:
    """Resolve a natural GaiaOS subject through the deployed DictionaryOS/YggdrasilOS checkout."""
    return _context_packet(subject, limit, depth)


@app.get("/gaiaos/context", operation_id="getGaiaContext")
def gaia_context_http(
    subject: str,
    limit: int = 10,
    depth: int = 1,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """Read-only GaiaOS semantic context query bound to the deployed repository checkout."""
    base._authorize(authorization)
    return _context_packet(subject, limit, depth)
