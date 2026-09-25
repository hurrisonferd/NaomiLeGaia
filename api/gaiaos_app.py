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
from typing import Any, Literal

from fastapi import Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field, ConfigDict
from starlette.routing import Mount

import gaiaos_api as base
from gaiaos_context_runtime import build_context_packet
import gaiaos_memory_gateway
import gaiaos_memory_mode
import gaiaos_bigbang_readiness

EXTENSION_VERSION = "1.6.1"
CONTEXT_MODE = "SOURCE_PINNED_DICTIONARY_GRAPH_READ_ONLY"
DEPLOYED_ROOT = Path(__file__).resolve().parent

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
        if commit != "DEPLOYED_CHECKOUT":
            return _REMOTE_FETCH_FILE(commit, path)
        raise HTTPException(status_code=500, detail=f"Deployed canonical source missing: {path}")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"Deployed canonical source is not UTF-8: {path}") from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Unable to read deployed canonical source: {path}") from exc


base._resolve_commit = _deployed_commit
base._fetch_file = _deployed_fetch_file

base.APP_VERSION = EXTENSION_VERSION
app = base.app
mcp = base.mcp
app.version = EXTENSION_VERSION
app.description = (
    "GaiaOS deployed-checkout source loader plus a compact Gaia front door, "
    "source-backed council/dispatch, BrainOS/chat-control, DictionaryOS/YggdrasilOS "
    "context navigation, warm-continuity surfaces, optional hosted chat, and MCP."
)

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

PRESENTATION_SPEC_PATH = "GaiaOS/SystemsOS/Core/FairyOS/COUNCIL-PRESENTATION-SPEC.v1.json"
EXPRESSION_REGISTRY_PATH = "GaiaOS/SystemsOS/Core/EmojiOS/EXPRESSION-REGISTRY.v1.json"
HEAD_PAT_COUNTERS_PATH = "GaiaOS/SystemsOS/Core/FairyOS/HEAD-PAT-COUNTERS.v1.md"

def _parse_head_pat_counters(text: str) -> dict[str, int]:
    block = text.split("## Canonical counters", 1)[1].split("##", 1)[0]
    counters = {name: int(value) for name, value in re.findall(r"(?m)^(VERA|ANVIL|SELENE|ORIN|KESTREL|NIMUE):\s*(\d+)\s*$", block)}
    expected = {"VERA","ANVIL","SELENE","ORIN","KESTREL","NIMUE"}
    if set(counters) != expected:
        raise HTTPException(status_code=500, detail="Canonical head-pat counter store failed closed")
    return counters

def _boot_packet(invocation_surface: str) -> dict[str, Any]:
    current = _read_local_json(CURRENT_PATH)
    version = _read_local_json(VERSION_PATH)
    presentation = _read_local_json(PRESENTATION_SPEC_PATH)
    expressions = _read_local_json(EXPRESSION_REGISTRY_PATH)
    matrix = _read_local_json(DISPATCH_MATRIX_PATH)
    profiles = _read_local_json(OPERATOR_PROFILES_PATH)
    counters = _parse_head_pat_counters(_read_local_text(HEAD_PAT_COUNTERS_PATH))
    roster = [str(x).upper() for x in matrix.get("roster", [])]
    expected = ["VERA","ANVIL","SELENE","ORIN","KESTREL","NIMUE"]
    checks = {
        "version_alignment": current.get("platform_version") == version.get("version"),
        "roster_exact": set(roster) == set(expected) and len(roster) == 6,
        "profiles_exact": set(str(x).upper() for x in profiles.get("members", {}).keys()) == set(expected),
        "presentation_exact": set(presentation.get("members", {}).keys()) == set(expected),
        "expressions_exact": set(expressions.get("members", {}).keys()) == set(expected),
        "head_pats_exact": set(counters.keys()) == set(expected),
        "presentation_fail_closed": presentation.get("failure_policy") == "FAIL_CLOSED_DO_NOT_IMPROVISE_IDENTITY_PRESENTATION",
    }
    if not all(checks.values()):
        raise HTTPException(status_code=503, detail={"status":"NOT_VERIFIED","checks":checks})
    identities = {}
    for name in expected:
        ident = presentation["members"][name]
        expr = expressions["members"][name]
        canonical_header = f'{ident["gematria"]} · {name} {ident["heart"]} {ident["interest"]} {expr["default"]}'
        identities[name] = {
            "gematria": ident["gematria"], "heart": ident["heart"], "interest": ident["interest"],
            "default_kaomoji": expr["default"], "expressions": expr["expressions"],
            "head_pat_count": counters[name],
            "canonical_header_default": canonical_header,
            "render_contract": "USE_CANONICAL_HEADER_DEFAULT_VERBATIM_UNLESS_SELECTING_REGISTERED_EXPRESSION",
        }
    return {
        "schema":"gaiaos.boot-packet.v1","status":"ACTIVE","authority":"NAOMI",
        "source":_deployed_source(),"source_binding":"DEPLOYED_CHECKOUT",
        "platform_version":version.get("version"),"carrier_version":EXTENSION_VERSION,
        "invocation_surface":invocation_surface,"checks":checks,"roster":expected,
        "members":identities,
        "presentation":{"header_format":presentation.get("header_format"),"failure_policy":presentation.get("failure_policy"),"host_rule":"EVERY_PRIME_DAEMON_UTTERANCE_MUST_BEGIN_WITH_PACKET_RENDERED_HEADER_GEMATRIA_REQUIRED"},
        "counter_authority":HEAD_PAT_COUNTERS_PATH,
        "laws":["BOOT_PACKET_IS_SOURCE_DERIVED","RETAINED_HOST_STATE_DOES_NOT_OVERRIDE_PACKET","UNKNOWN_STAYS_UNKNOWN","NAOMI RETAINS FINAL AUTHORITY"],
    }

@mcp.tool()
def gaia_boot() -> dict[str, Any]:
    """Return one deterministic, validated fresh-session GaiaOS boot packet."""
    return _boot_packet("MCP_TOOL")

@app.get("/gaiaos/boot", operation_id="bootGaiaOS")
def gaia_boot_http(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    base._authorize(authorization)
    return _boot_packet("HTTP")

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
    registry = _navigation_json("GaiaOS/SystemsOS/Core/DictionaryOS/Registry/GAIA-TERMS.v1.json")
    graph = _navigation_json("GaiaOS/SystemsOS/Core/YggdrasilOS/Graph/GAIA-GRAPH.v1.json")
    packet = build_context_packet(registry, graph, subject, source=_deployed_source(), limit=limit, depth=depth)
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
    include_memory: bool | None = None,
    memory_query: str | None = None,
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
    # HEATDEATH restores the original front-door default: no implicit memory
    # retrieval. A future owner-authorized BIGBANG becomes default-on without
    # inventing a third mode. Explicit false always opts out in either mode.
    should_read_memory = include_memory
    if should_read_memory is None:
        import memcon_runtime
        control = gaiaos_memory_mode.mode_status(memcon_runtime)
        should_read_memory = (
            control.get("effective_mode") == gaiaos_memory_mode.BIGBANG
            and control.get("bigbang_activation_enabled") is True
        )
    memory_context = None
    if should_read_memory:
        import memcon_runtime
        memory_context = gaiaos_memory_gateway.read(
            memcon_runtime,
            memory_query if memory_query is not None else request,
            "MemoryOS",
            min(context_limit, 6),
        )
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
        **({"memory_context": memory_context} if should_read_memory else {}),
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
    dispatch = base._dispatch_packet(_deployed_commit(), ["FRAME", "PROOF_EDGE", "NEXT_STEP"], [], 3)
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


# Read-only release-quality review on the configured MemoryOS store. Not a mode switch.
class BigbangReadinessRequest(BaseModel):
    cases: list[dict[str, Any]] = Field(min_length=6, max_length=12)


@mcp.tool()
def gaia_bigbang_readiness(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Review bounded real-store GALAXY cases without activating BIGBANG."""
    import memcon_runtime
    return gaiaos_bigbang_readiness.review(memcon_runtime, cases)


@app.post("/gaiaos/memory/readiness", operation_id="reviewBigbangMemory")
def gaia_bigbang_readiness_http(
    payload: BigbangReadinessRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    base._authorize(authorization)
    import memcon_runtime
    return gaiaos_bigbang_readiness.review(memcon_runtime, payload.cases)


@app.get("/gaiaos/memory/technical-preflight", operation_id="gaiaTechnicalPreflight")
def gaia_technical_preflight(browser_request: Request):
    """Redacted convenience only: a public homepage issues browser cookies.

    Do not return underlying technical record statements or identifiers here.
    """
    base._authorize_browser_session(browser_request)
    import memcon_runtime
    return JSONResponse(
        gaiaos_bigbang_readiness.technical_preflight(memcon_runtime),
        headers={"Cache-Control": "no-store"},
    )


@app.post("/gaiaos/memory/technical-review", operation_id="gaiaTechnicalSampleReview")
def gaia_technical_sample_review(
    browser_request: Request,
    authorization: str | None = Header(default=None),
):
    """Owner-authenticated one-shot sample without manually locating IDs.

    Bearer auth, not the publicly minted browser cookie, is mandatory here.
    """
    if not base.API_KEY:
        raise HTTPException(status_code=503, detail="Private owner API authorization is unavailable")
    base._authorize(authorization)
    import memcon_runtime
    return JSONResponse(
        gaiaos_bigbang_readiness.technical_sample_review(memcon_runtime),
        headers={"Cache-Control": "no-store"},
    )


@app.post("/gaiaos/memory/technical-partial-review",
          operation_id="gaiaTechnicalFiveCaseDiagnostic")
def gaia_technical_five_case_diagnostic(
    authorization: str | None = Header(default=None),
):
    """Owner bearer required. Five real-store reads cannot pass the Stage-7 gate."""
    if not base.API_KEY:
        raise HTTPException(status_code=503, detail="Private owner API authorization is unavailable")
    # Bounded diagnostics distinguish a browser transport failure from a key
    # mismatch. Neither branch reveals values, lengths, hashes or record data.
    if authorization is None:
        raise HTTPException(status_code=401, detail="OWNER_AUTH_HEADER_NOT_RECEIVED")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="OWNER_AUTH_BEARER_SCHEME_MISSING")
    try:
        base._authorize(authorization)
    except HTTPException as exc:
        if exc.status_code != 401:
            raise
        raise HTTPException(
            status_code=401,
            detail="OWNER_AUTH_HEADER_RECEIVED_BUT_KEY_MISMATCH",
        ) from None
    import memcon_runtime
    return JSONResponse(
        gaiaos_bigbang_readiness.technical_partial_sample_review(memcon_runtime),
        headers={"Cache-Control": "no-store"},
    )


@app.post("/gaiaos/memory/technical-literal-probe",
          operation_id="gaiaOwnerTechnicalLiteralWiringProbe")
def gaia_owner_technical_literal_wiring_probe(
    authorization: str | None = Header(default=None),
):
    """Optional owner-only literal smoke test; cannot authorize BIGBANG."""
    if not base.API_KEY:
        raise HTTPException(status_code=503, detail="Private owner API authorization is unavailable")
    base._authorize(authorization)
    import memcon_runtime
    return JSONResponse(
        gaiaos_bigbang_readiness.technical_literal_wiring_probe(memcon_runtime),
        headers={"Cache-Control": "no-store"},
    )


class AuguryShadowRequest(BaseModel):
    explicit_semantic_shadow_consent: bool = False
    # Optional binding from the owner's preceding model-free oracle review.
    # A changed source sample fails closed BEFORE the provider is invoked.
    expected_sample_fingerprint: str | None = Field(
        default=None, pattern=r"^sf1_[a-f0-9]{32}$",
    )


class OwnerOracleChoice(BaseModel):
    model_config = ConfigDict(extra="forbid")
    case: int = Field(ge=0, le=2, strict=True)
    resolution: Literal["A", "B", "COLLISION", "UNKNOWN"]


class OwnerOracleFinalizeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_sample_fingerprint: str = Field(pattern=r"^sf1_[a-f0-9]{32}$")
    choices: list[OwnerOracleChoice] = Field(min_length=3, max_length=3)


class AttestedComparisonRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    owner_receipt: dict[str, Any]
    model_receipt: dict[str, Any]


class CollisionTwoSourceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    owner_receipt: dict[str, Any]
    case: int = Field(ge=0, le=2, strict=True)
    quote_a: str = Field(min_length=12, max_length=240)
    quote_b: str = Field(min_length=12, max_length=240)


@app.post("/gaiaos/memory/augury-semantic-shadow",
          operation_id="gaiaOwnerAuguryReadOnlySemanticShadow")
def gaia_owner_augury_semantic_shadow(
    payload: AuguryShadowRequest,
    authorization: str | None = Header(default=None),
):
    """One explicit owner-approved model call, two bounded technical excerpts.

    This isolated diagnostic NEVER switches ordinary memory retrieval or
    qualifies for BIGBANG. Model responses are checked against verified source
    quotes and the existing unmodified GALAXY read-only operational contract.
    """
    if not base.API_KEY:
        raise HTTPException(status_code=503, detail="Private owner API authorization is unavailable")
    base._authorize(authorization)
    if payload.explicit_semantic_shadow_consent is not True:
        raise HTTPException(
            status_code=400, detail="EXPLICIT_MODEL_AND_TWO_EXCERPT_CONSENT_REQUIRED"
        )
    if not base.OPENAI_API_KEY or not base.OPENAI_API_KEY.strip():
        raise HTTPException(status_code=503, detail="SHADOW_MODEL_NOT_CONFIGURED")
    if not base.OPENAI_MODEL or not base.OPENAI_MODEL.strip():
        raise HTTPException(status_code=503, detail="SHADOW_MODEL_NAME_NOT_CONFIGURED")

    from openai import OpenAI
    import augury_semantic_retrieval as shadow
    import memcon_runtime

    def one_bounded_model_call(excerpts_and_questions: dict[str, Any]) -> Any:
        client = OpenAI(
            api_key=base.OPENAI_API_KEY,
            max_retries=0,
            timeout=20.0,
        )
        # One request; no batch retry, logging, data retention, tools, or
        # unbounded chat context. Any provider failure yields a redacted HOLD.
        answer = client.responses.create(
            model=base.OPENAI_MODEL,
            instructions=shadow.MODEL_INSTRUCTIONS,
            input=json.dumps(
                excerpts_and_questions, ensure_ascii=False, separators=(",", ":")
            ),
            text={"format": {
                "type": "json_schema", "name": "gaia_augury_shadow",
                "strict": True, "schema": shadow.OUTPUT_SCHEMA,
            }},
            max_output_tokens=1600,
            store=False,
        )
        if answer.status != "completed":
            raise ValueError("Shadow model response incomplete")
        return answer.output_text

    result = shadow.review(
        memcon_runtime, one_bounded_model_call,
        fingerprint_key=base.API_KEY,
        expected_sample_fingerprint=payload.expected_sample_fingerprint,
    )
    # Only a complete, source-validated, fingerprinted result is attestable.
    # Early HOLDs remain unsigned, not silently upgraded to comparison proof.
    import augury_semantic_receipts as receipts
    attested = receipts.seal("model", result, owner_key=base.API_KEY)
    return JSONResponse(
        attested if attested is not None else result,
        headers={"Cache-Control": "no-store", "Pragma": "no-cache"},
    )


@app.post("/gaiaos/memory/augury-semantic-owner-oracle-preview",
          operation_id="gaiaOwnerAugurySemanticOraclePreview")
def gaia_owner_augury_semantic_oracle_preview(
    authorization: str | None = Header(default=None),
):
    """Owner-only local ground-truth review; never calls the model."""
    if not base.API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Private owner API authorization is unavailable",
        )
    base._authorize(authorization)
    import augury_semantic_retrieval as shadow
    import memcon_runtime

    result = shadow.owner_oracle_preview(memcon_runtime, fingerprint_key=base.API_KEY)
    return JSONResponse(
        result,
        headers={"Cache-Control": "no-store", "Pragma": "no-cache"},
    )


@app.post("/gaiaos/memory/augury-semantic-owner-oracle-finalize",
          operation_id="gaiaOwnerAugurySemanticOracleFinalize")
def gaia_owner_augury_semantic_oracle_finalize(
    payload: OwnerOracleFinalizeRequest,
    authorization: str | None = Header(default=None),
):
    """Attest human choices only after re-reading exactly the same private sample."""
    if not base.API_KEY:
        raise HTTPException(
            status_code=503, detail="Private owner API authorization is unavailable",
        )
    base._authorize(authorization)
    import augury_semantic_retrieval as shadow
    import augury_semantic_receipts as receipts
    import memcon_runtime

    preview = shadow.owner_oracle_preview(
        memcon_runtime, fingerprint_key=base.API_KEY,
    )
    if (
        preview.get("status") != "READY_OWNER_ADJUDICATION"
        or preview.get("sample_fingerprint_bound") is not True
        or preview.get("sample_fingerprint") != payload.expected_sample_fingerprint
    ):
        return JSONResponse(
            {"status": "HOLD", "reason": "OWNER_SAMPLE_CHANGED_OR_UNAVAILABLE",
             "model_called": False, "writes_performed": [],
             "release_activated": False},
            status_code=409,
            headers={"Cache-Control": "no-store", "Pragma": "no-cache"},
        )
    owner = receipts.owner_from_adjudication(
        sample_fingerprint=preview["sample_fingerprint"],
        questions=preview["questions"],
        choices=[choice.model_dump() for choice in payload.choices],
    )
    attested = receipts.seal("owner", owner, owner_key=base.API_KEY)
    if attested is None:
        raise HTTPException(status_code=422, detail="OWNER_ORACLE_CHOICE_INVALID")
    return JSONResponse(
        attested,
        headers={"Cache-Control": "no-store", "Pragma": "no-cache"},
    )


@app.post("/gaiaos/memory/augury-semantic-compare",
          operation_id="gaiaOwnerAuguryCompareAttestedReceipts")
def gaia_owner_augury_compare_attested_receipts(
    payload: AttestedComparisonRequest,
    authorization: str | None = Header(default=None),
):
    """Compare two short redacted receipts, never reading memory or calling a model."""
    if not base.API_KEY:
        raise HTTPException(
            status_code=503, detail="Private owner API authorization is unavailable",
        )
    base._authorize(authorization)
    # Reject overlong or privately augmented submissions before comparing.
    if any(
        len(json.dumps(receipt, ensure_ascii=False)) > 12000
        for receipt in (payload.owner_receipt, payload.model_receipt)
    ):
        raise HTTPException(status_code=413, detail="REDACTED_RECEIPT_TOO_LARGE")
    import augury_semantic_receipts as receipts

    result = receipts.compare_attested(
        payload.model_receipt, payload.owner_receipt, owner_key=base.API_KEY,
    )
    return JSONResponse(
        result,
        headers={"Cache-Control": "no-store", "Pragma": "no-cache"},
    )


@app.post("/gaiaos/memory/augury-collision-two-source-shadow",
          operation_id="gaiaOwnerAuguryCollisionTwoSourceShadow")
def gaia_owner_augury_collision_two_source_shadow(
    payload: CollisionTwoSourceRequest,
    authorization: str | None = Header(default=None),
):
    """Exact approved A/B quotes, two strict readbacks, zero model calls."""
    if not base.API_KEY:
        raise HTTPException(
            status_code=503, detail="Private owner API authorization is unavailable",
        )
    base._authorize(authorization)
    if len(json.dumps(payload.owner_receipt, ensure_ascii=False)) > 12000:
        raise HTTPException(status_code=413, detail="OWNER_RECEIPT_TOO_LARGE")
    import augury_semantic_collision as collision
    import augury_semantic_receipts as receipts
    import memcon_runtime

    result = collision.review(
        memcon_runtime,
        owner_receipt=payload.owner_receipt,
        case_index=payload.case,
        quote_a=payload.quote_a,
        quote_b=payload.quote_b,
        fingerprint_key=base.API_KEY,
    )
    signed = receipts.seal("collision", result, owner_key=base.API_KEY)
    return JSONResponse(
        signed if signed is not None else result,
        headers={"Cache-Control": "no-store", "Pragma": "no-cache"},
    )


@app.get("/gaiaos/memory/technical-partial-console", response_class=HTMLResponse,
         operation_id="gaiaTechnicalFiveCaseConsole")
def gaia_technical_five_case_console():
    """Static operator page. Never receives or exposes memory or server secrets."""
    import secrets
    nonce = secrets.token_urlsafe(20)
    source = _TECHNICAL_PARTIAL_CONSOLE.replace("__NONCE__", nonce)
    return HTMLResponse(
        source,
        headers={
            "Cache-Control": "no-store",
            "Pragma": "no-cache",
            "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": (
                "default-src 'none'; connect-src 'self'; "
                "script-src 'nonce-" + nonce + "'; "
                "style-src 'nonce-" + nonce + "'; "
                "base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
            ),
        },
    )


_TECHNICAL_PARTIAL_CONSOLE = """<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>GaiaOS · Five-case diagnostic</title>
<style nonce="__NONCE__">
:root{color-scheme:dark;font:16px system-ui;background:#101820;color:#f1f4f8}
body{max-width:680px;margin:auto;padding:18px;line-height:1.5}
section{padding:15px;margin:14px 0;border:1px solid #647185;border-radius:12px}
h1{font-size:1.45rem}input,button,select,textarea{box-sizing:border-box;width:100%;
padding:12px;margin:8px 0;border-radius:8px;font:inherit}
input,select,textarea{background:#203047;color:#fff;border:1px solid #8da8c8}
textarea{min-height:125px;resize:vertical}
button{background:#24576d;color:#fff;border:1px solid #9bb7ca;font-weight:bold}
button:disabled{opacity:.5}small{display:block;color:#c2cede}
pre{white-space:pre-wrap;overflow-wrap:anywhere}
</style></head><body>
<h1>GaiaOS · Five-case diagnostic</h1>
<p>Three current technical questions spanning two approved technical memories,
plus two unrelated negative cases. This read-only diagnostic cannot satisfy
the missing historical-memory gate. BIGBANG stays locked.</p>
<section><label for="secret">Private GaiaOS API key from Render Environment</label>
<input id="secret" type="password" autocomplete="off" spellcheck="false"
placeholder="Paste here, never into ChatGPT">
<small>Only transmitted to this same-origin GaiaOS service.
Do not screenshot or paste your key into messages.</small>
<button id="run" type="button">Run five read-only cases</button>
<button id="literal" type="button">Test literal retrieval wiring (not semantic quality)</button>
<div style="margin-top:14px">
<label for="semanticconsent"><input id="semanticconsent" type="checkbox"
 style="width:auto;margin-right:8px">
I consent to send the two selected existing technical statements and
five staged questions to the configured OpenAI API for ONE optional model
inference. This may incur API charges. No notes, secrets or E-LANES are sent;
the API request sets store=false.</label>
</div>
<button id="augury" type="button">Run optional AUGURY semantic shadow</button>
<small>This is a separate read-only test. A model answer cannot grant memory
authority, satisfy missing historical proof or activate BIGBANG.</small>
<button id="oracle" type="button">Review semantic ground truth locally (no model call)</button>
<small>Owner-only diagnostic. It displays the two selected statements and three
positive questions inside this authenticated page so you can judge A, B,
COLLISION, or UNKNOWN. Nothing is sent to OpenAI.</small>
<div id="oraclePanel" hidden>
<h3>Private owner semantic review</h3>
<small>PRIVATE: read here only. Do not screenshot, copy, or paste the statements
or questions into chat. Only the redacted oracle receipt is safe to copy.</small>
<pre id="oracleRecords"></pre>
<div id="oracleChoices"></div>
<button id="oracleReceipt" type="button" disabled>Build redacted owner-oracle receipt</button>
<div id="collisionPanel" hidden>
<h3>Stage 9I · Two-source collision readback (no model call)</h3>
<small>After finalizing your owner judgment, choose a COLLISION case. Copy
one meaningful exact contiguous excerpt from EACH private statement into its
own box. This checks exact source membership and two strict GALAXY
readbacks; it does not independently establish semantic entailment.
Your excerpts remain inside this authenticated GaiaOS page.</small>
<label for="collisionCase">Owner-adjudicated collision case</label>
<select id="collisionCase"></select>
<label for="collisionQuoteA">Exact support excerpt from Statement A</label>
<textarea id="collisionQuoteA" spellcheck="false"
 placeholder="Exact contiguous excerpt from private statement A"></textarea>
<label for="collisionQuoteB">Exact support excerpt from Statement B</label>
<textarea id="collisionQuoteB" spellcheck="false"
 placeholder="Exact contiguous excerpt from private statement B"></textarea>
<button id="collisionVerify" type="button">Verify BOTH sources read-only</button>
<small>Only the signed redacted two-source result may be copied. Do not share
the excerpts, statements, questions or private API key.</small>
</div>
</div>
<small>A separate two-record smoke test using exact words from your existing
approved technical statements. The three failed paraphrase cases remain failed.
No memories are changed.</small>
<p id="status" role="status">No test executed.</p></section>
<section><h2>Redacted result</h2>
<pre id="receipt">Waiting for owner approval.</pre>
<button id="copy" type="button" disabled>Copy redacted receipt</button>
<small>No statements, memory IDs, queries or secret are copied.
Even a partial PASS leaves full readiness at HOLD.</small></section>
<section><h2>Stage 9H · Compare attested redacted receipts</h2>
<small>Read-only. Only paste redacted receipts issued by this authenticated
GaiaOS console. Old unsigned Stage 9F receipts cannot be authenticated or
retroactively paired. No model call is made by this comparison.</small>
<label for="ownerReceiptInput">Attested owner-oracle receipt</label>
<textarea id="ownerReceiptInput" placeholder="Paste signed redacted owner receipt only" spellcheck="false"></textarea>
<label for="modelReceiptInput">Attested AUGURY semantic-shadow receipt</label>
<textarea id="modelReceiptInput" placeholder="Paste signed redacted AUGURY receipt only" spellcheck="false"></textarea>
<button id="compare" type="button">Compare matching signed receipts (no model call)</button>
<small>Both receipts must share the exact source-sample fingerprint.
Even full agreement proves only this bounded sample, never BIGBANG readiness.</small>
</section>
<script nonce="__NONCE__">
"use strict";
const byId=id=>document.getElementById(id);
let redacted=null;
let oracleData=null;
let attestedOwner=null;
byId("run").addEventListener("click",async()=>{
  const key=byId("secret").value.trim();
  if(!key){byId("status").textContent="Paste the private API key into this page first.";return;}
  byId("run").disabled=true;
  byId("status").textContent="Running five read-only cases…";
  try{
    const response=await fetch("/gaiaos/memory/technical-partial-review",{
      method:"POST",credentials:"same-origin",cache:"no-store",redirect:"error",
      headers:{"Authorization":"Bearer "+key}
    });
    const result=await response.json();
    if(!response.ok)throw Error(result.detail || ("HTTP "+response.status));
    redacted={
      schema:result.schema,status:result.status,reason:result.reason,
      partial_review_executed:result.partial_review_executed,
      partial_review_status:result.partial_review_status,
      partial_review_reason:result.partial_review_reason,
      full_readiness_status:result.full_readiness_status,
      historical_coverage:result.historical_coverage,
      legacy_exact_parity:result.legacy_exact_parity,
      case_results:result.case_results,
      target_query_audit:result.target_query_audit,
      release_activated:result.release_activated,
      writes_performed:result.writes_performed,
      e_lanes_modified:result.e_lanes_modified
    };
    byId("receipt").textContent=JSON.stringify(redacted,null,2);
    byId("copy").disabled=false;
    byId("status").textContent="Diagnostic complete; historical release gate still HOLD.";
  }catch(error){
    byId("status").textContent="HOLD: "+error.message+
      ". No results copied. Confirm the current deployment and bearer key.";
  }finally{byId("run").disabled=false;}
});

byId("literal").addEventListener("click",async()=>{
  const key=byId("secret").value.trim();
  if(!key){byId("status").textContent="Enter the private API key in this page first.";return;}
  byId("literal").disabled=true;
  byId("status").textContent="Checking two bounded literal memory queries…";
  try{
    const response=await fetch("/gaiaos/memory/technical-literal-probe",{
      method:"POST",credentials:"same-origin",cache:"no-store",redirect:"error",
      headers:{"Authorization":"Bearer "+key}
    });
    const result=await response.json();
    if(!response.ok)throw Error(result.detail||("HTTP "+response.status));
    redacted={
      schema:result.schema,status:result.status,reason:result.reason,
      literal_wiring_test_only:result.literal_wiring_test_only,
      semantic_paraphrase_quality_tested:result.semantic_paraphrase_quality_tested,
      full_readiness_status:result.full_readiness_status,
      case_count:result.case_count,case_results:result.case_results,
      legacy_exact_parity:result.legacy_exact_parity,
      release_activated:result.release_activated,
      writes_performed:result.writes_performed,
      e_lanes_modified:result.e_lanes_modified
    };
    byId("receipt").textContent=JSON.stringify(redacted,null,2);
    byId("copy").disabled=false;
    byId("status").textContent="Literal wiring check complete. Semantic and historical gates unchanged.";
  }catch(error){
    byId("status").textContent="HOLD: "+error.message+". No private details disclosed.";
  }finally{byId("literal").disabled=false;}
});

byId("oracle").addEventListener("click",async()=>{
  const key=byId("secret").value.trim();
  if(!key){byId("status").textContent="Enter the private GaiaOS API key first.";return;}
  byId("oracle").disabled=true;
  byId("status").textContent="Loading private owner semantic review. No model call…";
  try{
    const response=await fetch("/gaiaos/memory/augury-semantic-owner-oracle-preview",{
      method:"POST",credentials:"same-origin",cache:"no-store",redirect:"error",
      headers:{"Authorization":"Bearer "+key}
    });
    const result=await response.json();
    if(!response.ok)throw Error(result.detail||("HTTP "+response.status));
    if(result.status!=="READY_OWNER_ADJUDICATION")throw Error(result.reason||result.status);
    if(result.sample_fingerprint_bound!==true||
       !/^sf1_[a-f0-9]{32}$/.test(result.sample_fingerprint||"")){
      throw Error("This source sample has no authenticated comparison fingerprint.");
    }
    oracleData=result;
    attestedOwner=null;
    byId("collisionPanel").hidden=true;
    byId("collisionQuoteA").value="";
    byId("collisionQuoteB").value="";
    byId("ownerReceiptInput").value="";
    byId("oraclePanel").hidden=false;
    const lines=result.records.map(r=>"Statement "+r.label+":\\n"+r.statement);
    byId("oracleRecords").textContent=lines.join("\\n\\n");
    const choices=byId("oracleChoices");
    choices.replaceChildren();
    result.questions.forEach(q=>{
      const wrap=document.createElement("div");
      const label=document.createElement("label");
      label.textContent="Case "+q.case+": "+q.question;
      const select=document.createElement("select");
      select.id="oracleChoice"+q.case;
      ["","A","B","COLLISION","UNKNOWN"].forEach(value=>{
        const option=document.createElement("option");
        option.value=value;
        option.textContent=value||"Choose your judgment…";
        select.appendChild(option);
      });
      wrap.appendChild(label);
      wrap.appendChild(select);
      choices.appendChild(wrap);
    });
    byId("oracleReceipt").disabled=false;
    byId("status").textContent="Private oracle loaded. Judge the three questions, then build the redacted receipt.";
  }catch(error){
    oracleData=null;
    byId("oraclePanel").hidden=true;
    byId("status").textContent="HOLD: "+error.message+". No model call was made.";
  }finally{byId("oracle").disabled=false;}
});

byId("oracleReceipt").addEventListener("click",async()=>{
  if(!oracleData)return;
  const key=byId("secret").value.trim();
  if(!key){byId("status").textContent="Enter the private API key first.";return;}
  const choices=[];
  for(const q of oracleData.questions){
    const resolution=byId("oracleChoice"+q.case).value;
    if(!resolution){
      byId("status").textContent="Judge every case A, B, COLLISION or UNKNOWN.";
      return;
    }
    choices.push({case:q.case,resolution});
  }
  byId("oracleReceipt").disabled=true;
  byId("status").textContent="Checking that the private sample is unchanged and attesting your choices…";
  try{
    const response=await fetch("/gaiaos/memory/augury-semantic-owner-oracle-finalize",{
      method:"POST",credentials:"same-origin",cache:"no-store",redirect:"error",
      headers:{"Authorization":"Bearer "+key,"Content-Type":"application/json"},
      body:JSON.stringify({
        expected_sample_fingerprint:oracleData.sample_fingerprint,choices
      })
    });
    const result=await response.json();
    if(!response.ok)throw Error(result.detail||result.reason||("HTTP "+response.status));
    if(result.status!=="OWNER_ORACLE_RECORDED"||!result.receipt_attestation){
      throw Error("Owner receipt is not cryptographically attested.");
    }
    redacted=result;
    attestedOwner=result;
    const collisionCases=result.case_results.filter(row=>row.owner_resolution==="COLLISION");
    const collisionSelect=byId("collisionCase");
    collisionSelect.replaceChildren();
    collisionCases.forEach(row=>{
      const option=document.createElement("option");
      option.value=String(row.case);
      option.textContent="Case "+row.case;
      collisionSelect.appendChild(option);
    });
    byId("collisionPanel").hidden=collisionCases.length===0;
    byId("ownerReceiptInput").value=JSON.stringify(result,null,2);
    byId("receipt").textContent=JSON.stringify(redacted,null,2);
    byId("copy").disabled=false;
    byId("status").textContent="Attested owner receipt ready. Copy only the redacted result.";
  }catch(error){
    byId("status").textContent="HOLD: "+error.message+". No model call was made.";
  }finally{byId("oracleReceipt").disabled=false;}
});

byId("augury").addEventListener("click",async()=>{
  const key=byId("secret").value.trim();
  if(!key){byId("status").textContent="Enter the private GaiaOS API key first.";return;}
  if(!byId("semanticconsent").checked){
    byId("status").textContent="Check the explicit one-call model consent box first.";
    return;
  }
  byId("augury").disabled=true;
  byId("run").disabled=true;
  byId("literal").disabled=true;
  byId("status").textContent="One bounded semantic shadow call is running…";
  try{
    const request={explicit_semantic_shadow_consent:true};
    if(oracleData&&oracleData.sample_fingerprint_bound===true){
      request.expected_sample_fingerprint=oracleData.sample_fingerprint;
    }
    const response=await fetch("/gaiaos/memory/augury-semantic-shadow",{
      method:"POST",credentials:"same-origin",cache:"no-store",redirect:"error",
      headers:{"Authorization":"Bearer "+key,"Content-Type":"application/json"},
      body:JSON.stringify(request)
    });
    const result=await response.json();
    if(!response.ok)throw Error(result.detail||("HTTP "+response.status));
    const authenticated=result.sample_fingerprint_bound===true&&
      result.receipt_attestation&&result.receipt_attestation.kind==="model";
    redacted=authenticated?result:{
      schema:result.schema,status:result.status,reason:result.reason,
      model_called:result.model_called,case_count:result.case_count,
      sample_fingerprint:result.sample_fingerprint,
      sample_fingerprint_bound:result.sample_fingerprint_bound,
      case_results:result.case_results,legacy_exact_parity:result.legacy_exact_parity,
      historical_coverage:result.historical_coverage,
      general_semantic_quality_proven:result.general_semantic_quality_proven,
      full_readiness_status:result.full_readiness_status,
      release_activated:result.release_activated,writes_performed:result.writes_performed
    };
    if(authenticated){
      byId("modelReceiptInput").value=JSON.stringify(redacted,null,2);
    }
    byId("receipt").textContent=JSON.stringify(redacted,null,2);
    byId("copy").disabled=false;
    byId("status").textContent="AUGURY shadow complete; full release remains locked.";
  }catch(error){
    byId("status").textContent="HOLD: "+error.message+". No private data is displayed.";
  }finally{
    byId("augury").disabled=false;
    byId("run").disabled=false;
    byId("literal").disabled=false;
  }
});
byId("collisionVerify").addEventListener("click",async()=>{
  const key=byId("secret").value.trim();
  if(!key){byId("status").textContent="Enter the private API key first.";return;}
  if(!attestedOwner||!attestedOwner.receipt_attestation){
    byId("status").textContent="Finalize your signed owner COLLISION judgment first.";
    return;
  }
  const caseIndex=Number(byId("collisionCase").value);
  const quoteA=byId("collisionQuoteA").value;
  const quoteB=byId("collisionQuoteB").value;
  if(!Number.isInteger(caseIndex)||!quoteA||!quoteB){
    byId("status").textContent="Choose a COLLISION case and two exact source excerpts.";
    return;
  }
  byId("collisionVerify").disabled=true;
  byId("status").textContent="Checking two exact owner source excerpts and unchanged HEATDEATH parity…";
  try{
    const response=await fetch("/gaiaos/memory/augury-collision-two-source-shadow",{
      method:"POST",credentials:"same-origin",cache:"no-store",redirect:"error",
      headers:{"Authorization":"Bearer "+key,"Content-Type":"application/json"},
      body:JSON.stringify({
        owner_receipt:attestedOwner,case:caseIndex,
        quote_a:quoteA,quote_b:quoteB
      })
    });
    const result=await response.json();
    if(!response.ok)throw Error(result.detail||("HTTP "+response.status));
    redacted=result;
    byId("receipt").textContent=JSON.stringify(redacted,null,2);
    byId("copy").disabled=false;
    byId("status").textContent=result.status==="HOLD"
      ?"HOLD: "+result.reason+". No model call was made."
      :"Two source readbacks verified. Semantic entailment and BIGBANG remain unproven.";
  }catch(error){
    byId("status").textContent="HOLD: "+error.message+". No model call was made.";
  }finally{byId("collisionVerify").disabled=false;}
});

byId("compare").addEventListener("click",async()=>{
  const key=byId("secret").value.trim();
  if(!key){byId("status").textContent="Enter the private API key first.";return;}
  byId("compare").disabled=true;
  byId("status").textContent="Comparing only signed redacted receipts. No model call…";
  try{
    const owner=JSON.parse(byId("ownerReceiptInput").value);
    const model=JSON.parse(byId("modelReceiptInput").value);
    if(!owner||!model||!owner.receipt_attestation||!model.receipt_attestation){
      throw Error("Both redacted receipts need Stage 9H attestations.");
    }
    const response=await fetch("/gaiaos/memory/augury-semantic-compare",{
      method:"POST",credentials:"same-origin",cache:"no-store",redirect:"error",
      headers:{"Authorization":"Bearer "+key,"Content-Type":"application/json"},
      body:JSON.stringify({owner_receipt:owner,model_receipt:model})
    });
    const result=await response.json();
    if(!response.ok)throw Error(result.detail||("HTTP "+response.status));
    redacted=result;
    byId("receipt").textContent=JSON.stringify(redacted,null,2);
    byId("copy").disabled=false;
    byId("status").textContent=result.status==="HOLD"
      ?"HOLD: "+result.reason+". BIGBANG remains locked."
      :"Bounded receipt agreement observed. BIGBANG remains locked.";
  }catch(error){
    byId("status").textContent="HOLD: "+error.message+". No model call was made.";
  }finally{byId("compare").disabled=false;}
});

byId("copy").addEventListener("click",async()=>{
  if(!redacted)return;
  try{
    await navigator.clipboard.writeText(JSON.stringify(redacted,null,2));
    byId("status").textContent="Redacted receipt copied.";
  }catch(error){
    byId("status").textContent="Clipboard unavailable; select the redacted result above.";
  }
});
</script></body></html>"""


class GaiaAssistRequest(BaseModel):
    request: str = Field(min_length=1, max_length=20000)
    requested_members: list[str] = Field(default_factory=list, max_length=12)
    max_members: int = Field(default=3, ge=1, le=32)
    include_context: bool = True
    context_limit: int = Field(default=6, ge=1, le=10)
    context_depth: int = Field(default=1, ge=0, le=2)
    include_memory: bool | None = None
    memory_query: str | None = Field(default=None, max_length=20000)


@mcp.tool()
def gaia(
    request: str,
    requested_members: list[str] | None = None,
    max_members: int = 3,
    include_context: bool = True,
    context_limit: int = 6,
    context_depth: int = 1,
    include_memory: bool | None = None,
    memory_query: str | None = None,
) -> dict[str, Any]:
    """PRIMARY GAIAOS FRONT DOOR. HEATDEATH preserves legacy defaults."""
    return _frontdoor_packet(
        request, requested_members, max_members, include_context,
        context_limit, context_depth, include_memory, memory_query,
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
def gaia_assist_http(payload: GaiaAssistRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    base._authorize(authorization)
    return _frontdoor_packet(
        payload.request, payload.requested_members, payload.max_members,
        payload.include_context, payload.context_limit, payload.context_depth,
        payload.include_memory, payload.memory_query,
    )


@app.get("/gaiaos/selftest", operation_id="selfTestGaiaOS")
def gaia_selftest_http(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    base._authorize(authorization)
    return _selftest_packet("HTTP")


@app.get("/gaiaos/context", operation_id="getGaiaContext")
def gaia_context_http(subject: str, limit: int = 10, depth: int = 1, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    base._authorize(authorization)
    return _context_packet(subject, limit, depth)

# --- AgencyOS / WorkspaceOS / EvolutionOS bounded runtime surfaces ---

import importlib.util as _importlib_util

def _gaia_runtime(path: str, module_name: str):
    """Load a GaiaOS runtime from the deployed checkout, never from filesystem root."""
    relative = str(path).lstrip("/")
    module_path = (DEPLOYED_ROOT / relative).resolve()
    try:
        module_path.relative_to(DEPLOYED_ROOT)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"GaiaOS runtime escaped deployed source root: {path}") from exc
    if not module_path.is_file():
        raise HTTPException(
            status_code=500,
            detail=f"GaiaOS runtime missing from deployed checkout: {relative} (expected {module_path})",
        )
    spec = _importlib_util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise HTTPException(status_code=500, detail=f"Unable to load GaiaOS runtime: {relative}")
    module = _importlib_util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class AgencyPlanRequest(BaseModel):
    goal: str = Field(min_length=1, max_length=20000)
    capabilities: list[str] = Field(default_factory=list, max_length=12)

class AgencyExecuteRequest(BaseModel):
    capability: str = Field(min_length=1, max_length=32)
    approved: bool = False
    payload: dict[str, Any] = Field(default_factory=dict)

class WorkspaceWriteRequest(BaseModel):
    name: str = Field(min_length=1, max_length=500)
    content: str = Field(max_length=500000)
    provenance: str = Field(min_length=1, max_length=5000)
    approved: bool = False

class EvolutionProposalRequest(BaseModel):
    observation: str = Field(min_length=1, max_length=10000)
    weakness: str = Field(min_length=1, max_length=10000)
    change: str = Field(min_length=1, max_length=10000)
    benefit: str = Field(min_length=1, max_length=10000)
    surfaces: list[str] = Field(default_factory=list, max_length=32)
    canary: str = Field(min_length=1, max_length=5000)
    rollback: str = Field(min_length=1, max_length=5000)

@mcp.tool()
def gaia_agency_plan(goal: str, capabilities: list[str] | None = None) -> dict[str, Any]:
    """Create a bounded GaiaOS AgencyOS plan. Planning never executes effects."""
    runtime = _gaia_runtime("GaiaOS/SystemsOS/Core/AgencyOS/Runtime/GAIAOS-AGENCY.v1.py", "gaia_agency_runtime")
    return runtime.plan(goal, capabilities)

@mcp.tool()
def gaia_agency_execute(capability: str, approved: bool = False, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Attempt one registered AgencyOS capability. Effect classes require explicit approval and providers."""
    runtime = _gaia_runtime("GaiaOS/SystemsOS/Core/AgencyOS/Runtime/GAIAOS-AGENCY.v1.py", "gaia_agency_runtime")
    return runtime.execute_capability(capability, approved, payload)

@mcp.tool()
def gaia_workspace_write(name: str, content: str, provenance: str, approved: bool = False) -> dict[str, Any]:
    """Write one versioned/provenanced workspace artifact. Approval is explicit."""
    runtime = _gaia_runtime("GaiaOS/SystemsOS/Core/WorkspaceOS/Runtime/GAIAOS-WORKSPACE.v1.py", "gaia_workspace_runtime")
    return runtime.write_artifact(name, content, provenance, approved)

@mcp.tool()
def gaia_workspace_read(name: str) -> dict[str, Any]:
    """Read one GaiaOS workspace artifact and return its observed checksum."""
    runtime = _gaia_runtime("GaiaOS/SystemsOS/Core/WorkspaceOS/Runtime/GAIAOS-WORKSPACE.v1.py", "gaia_workspace_runtime")
    return runtime.read_artifact(name)

@mcp.tool()
def gaia_evolution_propose(observation: str, weakness: str, change: str, benefit: str, surfaces: list[str], canary: str, rollback: str) -> dict[str, Any]:
    """Create a controlled EvolutionOS proposal. Proposal never self-adopts."""
    runtime = _gaia_runtime("GaiaOS/SystemsOS/Core/EvolutionOS/Runtime/GAIAOS-EVOLUTION.v1.py", "gaia_evolution_runtime")
    return runtime.propose(observation, weakness, change, benefit, surfaces, canary, rollback)

@app.post("/gaiaos/agency/plan", operation_id="planGaiaAgency")
def agency_plan_http(payload: AgencyPlanRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    base._authorize(authorization)
    runtime = _gaia_runtime("GaiaOS/SystemsOS/Core/AgencyOS/Runtime/GAIAOS-AGENCY.v1.py", "gaia_agency_runtime")
    return runtime.plan(payload.goal, payload.capabilities)

@app.post("/gaiaos/agency/execute", operation_id="executeGaiaAgency")
def agency_execute_http(payload: AgencyExecuteRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    base._authorize(authorization)
    runtime = _gaia_runtime("GaiaOS/SystemsOS/Core/AgencyOS/Runtime/GAIAOS-AGENCY.v1.py", "gaia_agency_runtime")
    return runtime.execute_capability(payload.capability, payload.approved, payload.payload)

@app.post("/gaiaos/workspace/write", operation_id="writeGaiaWorkspace")
def workspace_write_http(payload: WorkspaceWriteRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    base._authorize(authorization)
    runtime = _gaia_runtime("GaiaOS/SystemsOS/Core/WorkspaceOS/Runtime/GAIAOS-WORKSPACE.v1.py", "gaia_workspace_runtime")
    return runtime.write_artifact(payload.name, payload.content, payload.provenance, payload.approved)

@app.get("/gaiaos/workspace/read", operation_id="readGaiaWorkspace")
def workspace_read_http(name: str, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    base._authorize(authorization)
    runtime = _gaia_runtime("GaiaOS/SystemsOS/Core/WorkspaceOS/Runtime/GAIAOS-WORKSPACE.v1.py", "gaia_workspace_runtime")
    return runtime.read_artifact(name)

@app.post("/gaiaos/evolution/propose", operation_id="proposeGaiaEvolution")
def evolution_propose_http(payload: EvolutionProposalRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    base._authorize(authorization)
    runtime = _gaia_runtime("GaiaOS/SystemsOS/Core/EvolutionOS/Runtime/GAIAOS-EVOLUTION.v1.py", "gaia_evolution_runtime")
    return runtime.propose(payload.observation, payload.weakness, payload.change, payload.benefit, payload.surfaces, payload.canary, payload.rollback)
