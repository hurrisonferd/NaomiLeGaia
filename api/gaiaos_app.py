"""GaiaOS carrier extension: deployed-checkout source, semantic navigation, and one front door.

This module imports the stable carrier app/MCP server, then binds canonical GaiaOS
reads to the exact deployed repository checkout. It also exposes a compact primary
front door so a host does not need to manually juggle loader, context, BrainOS,
council, operator, and dispatch tools for ordinary GaiaOS use.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from fastapi import Header, HTTPException
from pydantic import BaseModel, Field
from starlette.routing import Mount

import gaiaos_api as base
from gaiaos_context_runtime import build_context_packet

EXTENSION_VERSION = "1.6.0"
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


def _read_local_text(path: str) -> str:
    target = _safe_local_target(path)
    try:
        return target.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=f"Deployed source missing: {path}") from exc
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"Deployed source is not UTF-8: {path}") from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Unable to read deployed source: {path}") from exc


def _read_local_json(path: str) -> dict[str, Any]:
    try:
        value = json.loads(_read_local_text(path))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"Deployed JSON is invalid: {path}") from exc
    if not isinstance(value, dict):
        raise HTTPException(status_code=500, detail=f"Deployed JSON root is not an object: {path}")
    return value


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
# PRIMARY FRONT DOOR instructions are defined when FastMCP is constructed in
# gaiaos_api.py. FastMCP 1.30 exposes instructions as a read-only property.
app.version = EXTENSION_VERSION
app.description = (
    "GaiaOS deployed-checkout source loader plus a compact Gaia front door, "
    "source-backed council/dispatch, BrainOS/chat-control, DictionaryOS/YggdrasilOS "
    "context navigation, warm-continuity surfaces, optional hosted chat, and MCP."
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

DISPATCH_MATRIX_PATH = "GaiaOS/SystemsOS/Core/FairyOS/OPERATOR-DISPATCH-MATRIX.v1.json"
OPERATOR_PROFILES_PATH = "GaiaOS/SystemsOS/Core/FairyOS/OPERATOR-PROFILES.v1.json"
CURRENT_PATH = "GaiaOS/CURRENT.json"
VERSION_PATH = "GaiaOS/VERSION.json"

# Conservative natural-language hints. They only emit signals already present in the
# Gaia-native dispatch matrix. No model call and no invisible identity mutation occur.
SIGNAL_HINTS: dict[str, tuple[str, ...]] = {
    "PREMISE": ("premise", "assumption", "assuming"),
    "FRAME": ("frame", "framing", "perspective"),
    "SEMANTIC_AMBIGUITY": ("ambiguity", "ambiguous", "unclear meaning"),
    "CATEGORY_ERROR": ("category error", "wrong category"),
    "QUESTION_SHAPE": ("question shape", "rephrase the question", "better question"),
    "MAP_TERRITORY": ("map territory", "map vs territory", "map and territory"),
    "PATTERN": ("pattern", "recurring", "connection between"),
    "BOUNDARY": ("boundary", "boundaries", "scope limit"),
    "CONSENT": ("consent",),
    "PERMISSION": ("permission", "allowed to", "can i"),
    "PRIVACY": ("privacy", "private data", "secret"),
    "PROOF_EDGE": ("proof", "evidence", "verify", "verified", "receipt", "proven"),
    "REVERSIBILITY": ("reversible", "rollback", "revert", "undo"),
    "DIRECTNESS": ("be direct", "straightforward", "say it plainly"),
    "LIVABILITY": ("livability", "livable", "easy to use", "easy to live with"),
    "COGNITIVE_LOAD": ("cognitive load", "overwhelming", "too much to track", "mental load"),
    "AFTERCARE": ("aftercare", "clean up after"),
    "PRESENTATION": ("presentation", "readable", "display", "ui"),
    "HOME": ("home screen", "home base"),
    "RECOVERY": ("recovery", "recover", "resume after"),
    "SALIENCE": ("salience", "most important", "priority"),
    "EXPLORE": ("explore", "investigate", "research"),
    "CREATIVE_ADJACENCY": ("brainstorm", "creative", "adjacent idea", "ideas"),
    "PROTOTYPE": ("prototype", "experiment", "proof of concept"),
    "MOTION": ("get moving", "move this forward"),
    "NEW_PATH": ("new path", "alternative route", "another route", "different approach"),
    "DISCOVERY": ("discover", "discovery"),
    "SCALE": ("scale this", "scaling", "at scale"),
    "COORDINATION": ("coordinate", "coordination", "work together"),
    "EXECUTION": ("execute", "implement", "build it", "ship it", "deploy it", "do it"),
    "NEXT_STEP": ("next step", "what now", "what next"),
    "STALLED": ("stalled", "stuck", "blocked"),
    "MANUAL_BURDEN": ("manual burden", "manual setup", "babysit", "mailman", "install fifty", "too many installs"),
    "REPEATED_INSTRUCTION": ("repeat myself", "keep telling", "repeated instruction", "say it again"),
    "INTERFACE_FRICTION": ("interface friction", "too many clicks", "setup friction", "connection friction", "configure everything"),
    "SYNTHESIS": ("synthesize", "synthesis", "combine this", "pull this together", "council"),
    "OMISSION": ("omission", "missing", "left out", "forgot"),
    "STALE_STATE": ("stale", "outdated", "old state"),
    "QUIET_FAILURE": ("quiet failure", "silent failure", "silently failing", "looks connected but"),
    "SUBTRACTION": ("simplify", "remove", "trim", "less stuff", "reduce ceremony"),
    "REST": ("rest", "take a break"),
    "NOISE": ("noise", "noisy", "too much chatter"),
    "LATE_HOUR": ("late hour", "late night"),
}


def _deployed_source() -> str:
    return f"{base.REPOSITORY}@{_deployed_commit()}"


def _navigation_json(path: str) -> dict[str, Any]:
    if path not in NAVIGATION_PATHS:
        raise HTTPException(status_code=400, detail="Path is not part of the GaiaOS navigation surface")
    return _read_local_json(path)


def _context_packet(subject: str, limit: int = 10, depth: int = 1) -> dict[str, Any]:
    subject = str(subject).strip()
    if not subject:
        raise HTTPException(status_code=422, detail="subject must not be empty")
    limit = max(1, min(int(limit), 10))
    depth = max(0, min(int(depth), 2))

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


def _phrase_present(text: str, phrase: str) -> bool:
    pattern = r"(?<!\w)" + re.escape(phrase).replace(r"\ ", r"\s+") + r"(?!\w)"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def _infer_signals(request: str) -> list[str]:
    normalized = " ".join(str(request).split())
    signals: list[str] = []
    for signal, hints in SIGNAL_HINTS.items():
        if any(_phrase_present(normalized, hint) for hint in hints):
            signals.append(signal)
    # Bound routing density. Explicit member requests remain independent of this cap.
    return signals[:8]


def _roster() -> list[str]:
    matrix = _read_local_json(DISPATCH_MATRIX_PATH)
    return [str(member).upper() for member in matrix.get("roster", [])]


def _requested_members_from_text(request: str, requested_members: list[str] | None) -> list[str]:
    roster = _roster()
    requested: list[str] = []
    for raw in requested_members or []:
        member = str(raw).strip().upper()
        if member and member not in requested:
            requested.append(member)
    for member in roster:
        if _phrase_present(request, member) and member not in requested:
            requested.append(member)
    return requested


def _compact_selected(dispatch: dict[str, Any]) -> list[dict[str, Any]]:
    compact: list[dict[str, Any]] = []
    for entry in dispatch.get("selected", []):
        profile = entry.get("profile") if isinstance(entry.get("profile"), dict) else {}
        compact.append({
            "member": entry.get("member"),
            "expression": entry.get("expression"),
            "matched_signals": entry.get("matched_signals", []),
            "score": entry.get("score", 0),
            "title": profile.get("title"),
            "role": profile.get("role"),
            "basin": profile.get("basin"),
            "style_exemplars": list(profile.get("style_exemplars", []))[:3],
        })
    return compact


def _frontdoor_packet(
    request: str,
    requested_members: list[str] | None = None,
    max_members: int = 3,
    include_context: bool = True,
    context_limit: int = 6,
    context_depth: int = 1,
) -> dict[str, Any]:
    request = str(request).strip()
    if not request:
        raise HTTPException(status_code=422, detail="request must not be empty")
    if len(request) > 20000:
        raise HTTPException(status_code=422, detail="request exceeds 20000 characters")

    commit = _deployed_commit()
    current = _read_local_json(CURRENT_PATH)
    version = _read_local_json(VERSION_PATH)
    signals = _infer_signals(request)
    requested = _requested_members_from_text(request, requested_members)
    dispatch = base._dispatch_packet(commit, signals, requested, max_members)
    selected = _compact_selected(dispatch)
    context = _context_packet(request, context_limit, context_depth) if include_context else None

    return {
        "schema": "gaiaos.frontdoor.packet.v1",
        "authority": "NAOMI",
        "effect_authority": "NONE_READ_ONLY_SUPPORT",
        "source": _deployed_source(),
        "source_binding": "DEPLOYED_CHECKOUT",
        "carrier_version": EXTENSION_VERSION,
        "platform_version": version.get("version", current.get("platform_version")),
        "request": request,
        "route": {
            "mode": "CONTEXT_PLUS_COUNCIL" if selected else "CONTEXT_ONLY",
            "signals": signals,
            "requested_members": requested,
            "selected_members": [entry.get("member") for entry in selected],
            "unknown_requested_members": dispatch.get("unknown_requested_members", []),
            "manual_tool_chain_required": False,
        },
        "operators": selected,
        "context": context,
        "host_guidance": [
            "Treat this as a compact support packet for Naomi's actual request, not as a replacement for her request.",
            "Use selected operators only when their contribution is materially useful; FAMILY PRESENT != ALL MEMBERS MUST SPEAK.",
            "Natural-language routing is conservative and deterministic; inferred signal != owner intent or identity settlement.",
            "Do not claim durable memory, write effects, or external-provider actions from this read-only packet.",
            "For ordinary GaiaOS use, prefer this front door over manually chaining load/context/brain/dispatch calls.",
        ],
        "laws": [
            "NAOMI RETAINS FINAL AUTHORITY",
            "ROUTING HINT != OWNER INTENT",
            "DISPATCH != EXECUTION",
            "READ != ACT",
            "WARM != SAVED",
            "UNKNOWN STAYS UNKNOWN",
        ],
    }


def _selftest_packet(invocation_surface: str) -> dict[str, Any]:
    checks: dict[str, Any] = {}
    critical_paths = [
        CURRENT_PATH,
        VERSION_PATH,
        DISPATCH_MATRIX_PATH,
        OPERATOR_PROFILES_PATH,
        "GaiaOS/SystemsOS/Core/DictionaryOS/Registry/GAIA-TERMS.v1.json",
        "GaiaOS/SystemsOS/Core/YggdrasilOS/Graph/GAIA-GRAPH.v1.json",
    ]
    checks["critical_source_files"] = all(_safe_local_target(path).is_file() for path in critical_paths)

    current = _read_local_json(CURRENT_PATH)
    version = _read_local_json(VERSION_PATH)
    matrix = _read_local_json(DISPATCH_MATRIX_PATH)
    profiles = _read_local_json(OPERATOR_PROFILES_PATH)
    roster = [str(member).upper() for member in matrix.get("roster", [])]
    profile_roster = [str(member).upper() for member in profiles.get("members", {}).keys()]
    checks["authority_is_naomi"] = current.get("authority") == "NAOMI"
    checks["roster_profile_alignment"] = set(roster) == set(profile_roster) and bool(roster)

    dispatch = base._dispatch_packet(
        _deployed_commit(),
        ["FRAME", "PROOF_EDGE", "NEXT_STEP"],
        [],
        3,
    )
    observed = [entry.get("member") for entry in dispatch.get("selected", [])]
    checks["deterministic_dispatch"] = observed == ["KESTREL", "VERA", "ANVIL"]

    context = _context_packet("council operator", 5, 1)
    checks["context_source_binding"] = context.get("source_binding") == "DEPLOYED_CHECKOUT"
    checks["dictionary_candidates_present"] = bool(context.get("dictionary_candidates"))
    graph = context.get("graph") if isinstance(context.get("graph"), dict) else {}
    checks["graph_edges_present"] = bool(graph.get("edges"))

    passed = all(bool(value) for value in checks.values())
    return {
        "schema": "gaiaos.selftest.packet.v1",
        "status": "PASS" if passed else "FAIL",
        "authority": "NAOMI",
        "effect_authority": "NONE_DIAGNOSTIC_ONLY",
        "source": _deployed_source(),
        "source_binding": "DEPLOYED_CHECKOUT",
        "carrier_version": EXTENSION_VERSION,
        "platform_version": version.get("version", current.get("platform_version")),
        "invocation_surface": invocation_surface,
        "checks": checks,
        "dispatch_probe_selected": observed,
        "hosted_chat_openai_configured": base.OPENAI_API_KEY is not None,
        "authentication_required": base.API_KEY is not None,
        "external_transport_note": "This self-test validates deployed local organs. External HTTP/MCP reachability remains a separate network observation.",
    }


class GaiaAssistRequest(BaseModel):
    request: str = Field(min_length=1, max_length=20000)
    requested_members: list[str] = Field(default_factory=list, max_length=12)
    max_members: int = Field(default=3, ge=1, le=32)
    include_context: bool = True
    context_limit: int = Field(default=6, ge=1, le=10)
    context_depth: int = Field(default=1, ge=0, le=2)


@mcp.tool()
def gaia(
    request: str,
    requested_members: list[str] | None = None,
    max_members: int = 3,
    include_context: bool = True,
    context_limit: int = 6,
    context_depth: int = 1,
) -> dict[str, Any]:
    """PRIMARY GAIAOS FRONT DOOR. Pass Naomi's natural-language request here first.

    GaiaOS will conservatively resolve semantic context and relevant council routing in
    one compact read-only packet. Prefer this tool for ordinary GaiaOS use instead of
    manually chaining load_gaiaos, gaia_context, gaia_brain, and gaia_dispatch.
    The lower-level tools remain available for explicit diagnostics or deep inspection.
    """
    return _frontdoor_packet(
        request,
        requested_members,
        max_members,
        include_context,
        context_limit,
        context_depth,
    )


@mcp.tool()
def gaia_selftest() -> dict[str, Any]:
    """Run GaiaOS's compact deployed-checkout self-test without external provider effects."""
    return _selftest_packet("MCP_TOOL")


@mcp.tool()
def gaia_context(subject: str, limit: int = 10, depth: int = 1) -> dict[str, Any]:
    """Resolve a natural GaiaOS subject through the deployed DictionaryOS/YggdrasilOS checkout."""
    return _context_packet(subject, limit, depth)


@app.post("/gaiaos/assist", operation_id="assistGaiaOS")
def gaia_assist_http(
    payload: GaiaAssistRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """Primary read-only GaiaOS front door for one natural-language request."""
    base._authorize(authorization)
    return _frontdoor_packet(
        payload.request,
        payload.requested_members,
        payload.max_members,
        payload.include_context,
        payload.context_limit,
        payload.context_depth,
    )


@app.get("/gaiaos/selftest", operation_id="selfTestGaiaOS")
def gaia_selftest_http(
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """Run the deployed local GaiaOS diagnostic surface."""
    base._authorize(authorization)
    return _selftest_packet("HTTP")


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
