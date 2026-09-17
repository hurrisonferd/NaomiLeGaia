"""GaiaOS carrier extension: deployed-checkout semantic context navigation.

This module imports the stable carrier app/MCP server, then adds one bounded
read-only context surface backed by the DictionaryOS + YggdrasilOS data shipped
inside the exact deployed repository checkout. The live context route therefore
does not depend on a second outbound GitHub fetch after deployment.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import Header, HTTPException

import gaiaos_api as base
from gaiaos_context_runtime import build_context_packet

EXTENSION_VERSION = "1.5.0"
CONTEXT_MODE = "SOURCE_PINNED_DICTIONARY_GRAPH_READ_ONLY"
DEPLOYED_ROOT = Path(__file__).resolve().parent.parent
base.APP_VERSION = EXTENSION_VERSION
app = base.app
mcp = base.mcp
app.version = EXTENSION_VERSION
app.description = (
    "GaiaOS source loader plus source-backed council/dispatch, BrainOS/chat-control, "
    "deployed-checkout DictionaryOS/YggdrasilOS context navigation, warm-continuity surfaces, "
    "a web carrier backed by the OpenAI Responses API, and a read-only MCP carrier."
)
app.openapi_schema = None

NAVIGATION_PATHS = {
    "GaiaOS/SystemsOS/Core/DictionaryOS/Registry/GAIA-TERMS.v1.json",
    "GaiaOS/SystemsOS/Core/YggdrasilOS/Graph/GAIA-GRAPH.v1.json",
}


def _deployed_source() -> str:
    commit = (
        os.getenv("RENDER_GIT_COMMIT")
        or os.getenv("GIT_COMMIT")
        or os.getenv("SOURCE_COMMIT")
        or "DEPLOYED_CHECKOUT"
    )
    return f"{base.REPOSITORY}@{commit}"


def _navigation_json(path: str) -> dict[str, Any]:
    if path not in NAVIGATION_PATHS:
        raise HTTPException(status_code=400, detail="Path is not part of the GaiaOS navigation surface")

    target = (DEPLOYED_ROOT / path).resolve()
    try:
        target.relative_to(DEPLOYED_ROOT)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Navigation path escaped deployed source root") from exc

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
