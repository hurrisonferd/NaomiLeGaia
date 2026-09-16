"""GaiaOS canonical loader, council carrier API, and remote MCP carrier."""

from __future__ import annotations

import base64
import contextlib
import hashlib
import hmac
import json
import os
import secrets
import urllib.error
import urllib.request
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from openai import OpenAI
from pydantic import BaseModel, Field

APP_VERSION = "1.4.0"
REPOSITORY = os.getenv("GAIAOS_REPOSITORY", "hurrisonferd/NaomiLeGaia")
BRANCH = os.getenv("GAIAOS_BRANCH", "main")
GITHUB_API = "https://api.github.com"
RAW_BASE = "https://raw.githubusercontent.com"
API_KEY = os.getenv("GAIAOS_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
TIMEOUT = float(os.getenv("GAIAOS_HTTP_TIMEOUT", "10"))
SESSION_COOKIE = "gaiaos_session"
MCP_PUBLIC_HOST = os.getenv("MCP_PUBLIC_HOST", "ligeia-api.onrender.com")

CORE_LOAD_PATHS = [
    "GaiaOS/LOAD.v1.md",
    "GaiaOS/CURRENT.json",
    "GaiaOS/VERSION.json",
    "GaiaOS/PORT-MANIFEST.v1.json",
    "GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-RUNTIME-BOOTSTRAP.v1.md",
    "GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-INSTRUCTIONS.v1.md",
]

COUNCIL_PATHS = [
    "GaiaOS/COUNCIL-OPERATING-CONTRACT.v1.md",
    "GaiaOS/Apps/ChatOS/CURRENT.json",
    "GaiaOS/Apps/ChatOS/Protocols/GAIAOS-COUNCIL-COMMANDS.v1.md",
    "GaiaOS/SystemsOS/Core/BrainOS/CURRENT.json",
    "GaiaOS/SystemsOS/Core/ConvoOS/CURRENT.json",
    "GaiaOS/SystemsOS/Core/FairyOS/CURRENT.json",
    "GaiaOS/SystemsOS/Core/FairyOS/GAIA-COUNCIL.v1.md",
    "GaiaOS/SystemsOS/Core/FairyOS/OPERATOR-DISPATCH-MATRIX.v1.json",
    "GaiaOS/SystemsOS/Core/FairyOS/OPERATOR-PROFILES.v1.json",
    "GaiaOS/SystemsOS/Core/FairyOS/OPERATOR-PROSODY-BASINS.v1.md",
    "GaiaOS/SystemsOS/Core/EmojiOS/CURRENT.json",
    "GaiaOS/SystemsOS/Core/EmojiOS/EXPRESSION-REGISTRY.v1.json",
    "GaiaOS/HOT-WARM-COLD-CONVERSATION-FABRIC.v1.md",
    "GaiaOS/Apps/ChatOS/Protocols/CHATOS-RESPONSE-MODES.v1.json",
    "GaiaOS/Apps/ChatOS/Protocols/CHATOS-CAST-WIDTH-MODES.v1.json",
    "GaiaOS/Apps/ChatOS/Protocols/COUNCIL-DISSENT-PACKET.v1.schema.json",
    "GaiaOS/SystemsOS/Core/BrainOS/Protocols/BRAINOS-SUPPORT-FABRIC-CURRENT.v1.json",
    "GaiaOS/SystemsOS/Core/BrainOS/Protocols/BRAINOS-CONTEXT-COMPASS.v1.json",
    "GaiaOS/SystemsOS/Core/MemberContinuityOS/CURRENT.json",
    "GaiaOS/SystemsOS/Core/MemberContinuityOS/WARM-CANDIDATE-BUFFER.v1.md",
]

LOAD_PATHS = CORE_LOAD_PATHS + COUNCIL_PATHS

mcp = FastMCP(
    "GaiaOS Carrier",
    instructions=(
        "Canonical GaiaOS source loader and council surface. load_gaiaos retrieves the current "
        "GaiaOS bootstrap, gaia_council retrieves the full source-backed council packet, "
        "gaia_dispatch deterministically resolves explicit typed signals through the current "
        "FairyOS matrix, gaia_operator retrieves one current operator profile, and gaia_brain "
        "returns the current Gaia-native cognitive support and continuity contracts. These tools "
        "are read-only and do not claim domain effects, durable memory, or automatic identity adoption."
    ),
    stateless_http=True,
    json_response=True,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=["localhost:*", "127.0.0.1:*", "[::1]:*", MCP_PUBLIC_HOST, f"{MCP_PUBLIC_HOST}:*"],
        allowed_origins=[
            "http://localhost:*",
            "http://127.0.0.1:*",
            f"https://{MCP_PUBLIC_HOST}",
            f"https://{MCP_PUBLIC_HOST}:*",
        ],
    ),
)


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=20000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=40)


class DispatchRequest(BaseModel):
    signals: list[str] = Field(min_length=1, max_length=32)
    requested_members: list[str] = Field(default_factory=list, max_length=12)
    max_members: int = Field(default=3, ge=1, le=32)


def _request(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "GaiaOS-Loader/1.4", "Accept": "application/json,text/plain"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.read()
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        raise HTTPException(status_code=502, detail=f"Canonical source unavailable: {exc}") from exc


def _authorize(authorization: str | None) -> None:
    if API_KEY is None:
        return
    if authorization != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def _session_token() -> str:
    """Create a signed browser session token without exposing the server API key."""
    if not API_KEY:
        raise HTTPException(status_code=503, detail="GAIAOS_API_KEY is not configured on the carrier")
    nonce = secrets.token_urlsafe(32)
    signature = hmac.new(API_KEY.encode(), nonce.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{nonce}.{signature}".encode()).decode()


def _authorize_browser_session(request: Request) -> None:
    if API_KEY is None:
        return
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Browser session missing; reload the GaiaOS page")
    try:
        raw = base64.urlsafe_b64decode(token.encode()).decode()
        nonce, signature = raw.rsplit(".", 1)
    except (ValueError, UnicodeDecodeError, base64.binascii.Error) as exc:
        raise HTTPException(status_code=401, detail="Invalid browser session") from exc
    expected = hmac.new(API_KEY.encode(), nonce.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=401, detail="Invalid browser session")


def _resolve_commit() -> str:
    owner, repo = REPOSITORY.split("/", 1)
    payload = json.loads(_request(f"{GITHUB_API}/repos/{owner}/{repo}/commits/{BRANCH}").decode("utf-8"))
    sha = payload.get("sha")
    if not isinstance(sha, str) or len(sha) < 40:
        raise HTTPException(status_code=502, detail="Canonical branch did not return a valid commit SHA")
    return sha


def _fetch_file(commit: str, path: str) -> str:
    if path not in LOAD_PATHS:
        raise HTTPException(status_code=400, detail="Path is not part of the canonical loader surface")
    try:
        return _request(f"{RAW_BASE}/{REPOSITORY}/{commit}/{path}").decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"Canonical file is not UTF-8: {path}") from exc


def _json_file(commit: str, path: str) -> dict[str, Any]:
    try:
        value = json.loads(_fetch_file(commit, path))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"Canonical JSON is invalid: {path}") from exc
    if not isinstance(value, dict):
        raise HTTPException(status_code=502, detail=f"Canonical JSON root is not an object: {path}")
    return value


def _council_bundle(commit: str) -> dict[str, Any]:
    """Retrieve current council identity, routing, expression, and carrier contracts."""
    return {
        "contract": _fetch_file(commit, "GaiaOS/COUNCIL-OPERATING-CONTRACT.v1.md"),
        "commands": _fetch_file(commit, "GaiaOS/Apps/ChatOS/Protocols/GAIAOS-COUNCIL-COMMANDS.v1.md"),
        "fairyos_current": _json_file(commit, "GaiaOS/SystemsOS/Core/FairyOS/CURRENT.json"),
        "council": _fetch_file(commit, "GaiaOS/SystemsOS/Core/FairyOS/GAIA-COUNCIL.v1.md"),
        "profiles": _json_file(commit, "GaiaOS/SystemsOS/Core/FairyOS/OPERATOR-PROFILES.v1.json"),
        "prosody_basins": _fetch_file(commit, "GaiaOS/SystemsOS/Core/FairyOS/OPERATOR-PROSODY-BASINS.v1.md"),
        "dispatch_matrix": _json_file(commit, "GaiaOS/SystemsOS/Core/FairyOS/OPERATOR-DISPATCH-MATRIX.v1.json"),
        "emojios_current": _json_file(commit, "GaiaOS/SystemsOS/Core/EmojiOS/CURRENT.json"),
        "expression_registry": _json_file(commit, "GaiaOS/SystemsOS/Core/EmojiOS/EXPRESSION-REGISTRY.v1.json"),
        "brainos_current": _json_file(commit, "GaiaOS/SystemsOS/Core/BrainOS/CURRENT.json"),
        "convoos_current": _json_file(commit, "GaiaOS/SystemsOS/Core/ConvoOS/CURRENT.json"),
        "chatos_current": _json_file(commit, "GaiaOS/Apps/ChatOS/CURRENT.json"),
        "hot_warm_cold": _fetch_file(commit, "GaiaOS/HOT-WARM-COLD-CONVERSATION-FABRIC.v1.md"),
        "response_modes": _json_file(commit, "GaiaOS/Apps/ChatOS/Protocols/CHATOS-RESPONSE-MODES.v1.json"),
        "cast_width": _json_file(commit, "GaiaOS/Apps/ChatOS/Protocols/CHATOS-CAST-WIDTH-MODES.v1.json"),
        "dissent_schema": _json_file(commit, "GaiaOS/Apps/ChatOS/Protocols/COUNCIL-DISSENT-PACKET.v1.schema.json"),
        "brainos_support": _json_file(commit, "GaiaOS/SystemsOS/Core/BrainOS/Protocols/BRAINOS-SUPPORT-FABRIC-CURRENT.v1.json"),
        "context_compass": _json_file(commit, "GaiaOS/SystemsOS/Core/BrainOS/Protocols/BRAINOS-CONTEXT-COMPASS.v1.json"),
        "member_continuity": _json_file(commit, "GaiaOS/SystemsOS/Core/MemberContinuityOS/CURRENT.json"),
        "warm_candidate_buffer": _fetch_file(commit, "GaiaOS/SystemsOS/Core/MemberContinuityOS/WARM-CANDIDATE-BUFFER.v1.md"),
        "identity_boundary": (
            "The six current names are source-backed GaiaOS placeholder operator slots. "
            "Naomi retains authority to adopt, rename, replace, reorder, or re-theme them."
        ),
    }


def _load_bundle() -> dict[str, Any]:
    """Retrieve the GaiaOS bootstrap and council surface from one Git commit."""
    commit = _resolve_commit()
    current = _json_file(commit, "GaiaOS/CURRENT.json")
    version = _json_file(commit, "GaiaOS/VERSION.json")
    manifest = _json_file(commit, "GaiaOS/PORT-MANIFEST.v1.json")
    return {
        "gaiaos": {
            "mode": "ACTIVE",
            "source": f"{REPOSITORY}@{commit}",
            "branch": BRANCH,
            "platform_version": version.get("version", current.get("platform_version")),
            "authority": current.get("authority", "UNKNOWN"),
            "bootstrap": "VERIFIED",
        },
        "canonical": {"repository": REPOSITORY, "branch": BRANCH, "commit": commit, "loader_surface": LOAD_PATHS},
        "current": current,
        "version": version,
        "manifest": manifest,
        "loader": _fetch_file(commit, "GaiaOS/LOAD.v1.md"),
        "runtime_bootstrap": _fetch_file(commit, "GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-RUNTIME-BOOTSTRAP.v1.md"),
        "host_instructions": _fetch_file(commit, "GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-INSTRUCTIONS.v1.md"),
        "council_bundle": _council_bundle(commit),
        "proof_boundary": (
            "This API verifies source retrieval from one Git commit and can deterministically "
            "route explicit council signals and expose the current Gaia-native BrainOS/chat-control "
            "contracts. It does not execute owner-domain effects, prove durable memory or automatic "
            "carrier adoption, or settle Naomi's permanent operator identities."
        ),
    }


def _normalize_member(name: str) -> str:
    return name.strip().upper()


def _dispatch_packet(
    commit: str,
    signals: list[str],
    requested_members: list[str] | None = None,
    max_members: int = 3,
) -> dict[str, Any]:
    """Resolve explicit typed signals through the current source dispatch matrix."""
    matrix = _json_file(commit, "GaiaOS/SystemsOS/Core/FairyOS/OPERATOR-DISPATCH-MATRIX.v1.json")
    profiles = _json_file(commit, "GaiaOS/SystemsOS/Core/FairyOS/OPERATOR-PROFILES.v1.json")
    roster = [str(x).upper() for x in matrix.get("roster", [])]
    members = matrix.get("members", {})
    tie_break = [str(x).upper() for x in matrix.get("tie_break_order", roster)]
    requested = [_normalize_member(x) for x in (requested_members or [])]
    unknown_requested = [x for x in requested if x not in roster]
    requested = [x for x in requested if x in roster]

    normalized_signals: list[str] = []
    for raw in signals:
        signal = str(raw).strip().upper().replace(" ", "_").replace("-", "_")
        if signal and signal not in normalized_signals:
            normalized_signals.append(signal)

    signal_owners: dict[str, list[str]] = {}
    scores: dict[str, int] = {member: 0 for member in roster}
    for member in roster:
        spec = members.get(member, {})
        accepted = {str(x).upper() for x in spec.get("signals", [])}
        for signal in normalized_signals:
            if signal in accepted:
                scores[member] += 1
                signal_owners.setdefault(signal, []).append(member)

    order = {member: index for index, member in enumerate(tie_break)}
    ranked = sorted(
        [member for member in roster if scores.get(member, 0) > 0 and member not in requested],
        key=lambda member: (-scores.get(member, 0), order.get(member, len(order)), member),
    )

    cap = max(1, min(int(max_members), max(len(roster), 1)))
    effective_cap = max(cap, len(requested))
    selected = (requested + ranked)[:effective_cap]

    contributions: list[dict[str, Any]] = []
    profile_members = profiles.get("members", {})
    for member in selected:
        spec = members.get(member, {})
        expression = spec.get("default_expression", "DEFAULT")
        expression_by_signal = spec.get("expression_by_signal", {})
        matched_signals = [signal for signal in normalized_signals if member in signal_owners.get(signal, [])]
        for signal in normalized_signals:
            mapped = expression_by_signal.get(signal)
            if mapped:
                expression = mapped
                break
        contributions.append({
            "member": member,
            "score": scores.get(member, 0),
            "matched_signals": matched_signals,
            "expression": expression,
            "profile": profile_members.get(member, {}),
        })

    unknown_signals = [signal for signal in normalized_signals if signal not in signal_owners]
    return {
        "schema": "gaiaos.council.dispatch-packet.v1",
        "authority": "NAOMI",
        "source": f"{REPOSITORY}@{commit}",
        "signals": normalized_signals,
        "requested_members": requested,
        "unknown_requested_members": unknown_requested,
        "selected": contributions,
        "unknown_signals": unknown_signals,
        "family_present": True,
        "roster": roster,
        "placeholder_roster": True,
        "effect_authority": "NONE_READ_ONLY_DISPATCH",
        "laws": [
            "EXPLICIT_CURRENT_MEMBER_REQUESTS SURVIVE THE CAST CAP",
            "FAMILY PRESENT != ALL MEMBERS MUST SPEAK",
            "DISPATCH != EXECUTION",
            "UNKNOWN STAYS UNKNOWN",
            "NAOMI RETAINS FINAL AUTHORITY",
        ],
    }


def _operator_packet(commit: str, member: str) -> dict[str, Any]:
    profiles = _json_file(commit, "GaiaOS/SystemsOS/Core/FairyOS/OPERATOR-PROFILES.v1.json")
    matrix = _json_file(commit, "GaiaOS/SystemsOS/Core/FairyOS/OPERATOR-DISPATCH-MATRIX.v1.json")
    name = _normalize_member(member)
    profile = profiles.get("members", {}).get(name)
    if not isinstance(profile, dict):
        raise HTTPException(status_code=404, detail=f"Operator is not in the current GaiaOS roster: {name}")
    return {
        "schema": "gaiaos.council.operator-packet.v1",
        "authority": "NAOMI",
        "source": f"{REPOSITORY}@{commit}",
        "member": name,
        "profile": profile,
        "dispatch": matrix.get("members", {}).get(name, {}),
        "prosody_source": "GaiaOS/SystemsOS/Core/FairyOS/OPERATOR-PROSODY-BASINS.v1.md",
        "placeholder_slot": True,
        "effect_authority": "NONE_PRESENTATION_AND_ROUTING_ONLY",
    }


def _carrier_instructions(bundle: dict[str, Any]) -> str:
    council = bundle["council_bundle"]
    return f"""You are the GaiaOS carrier.

Treat the following retrieved repository material as the canonical GaiaOS operating contract for this response. Do not invent missing state. Preserve authority, evidence, identity, and proof boundaries. Do not expose private chain-of-thought.

CANONICAL SOURCE: {bundle['gaiaos']['source']}
PLATFORM: {bundle['gaiaos']['platform_version']}
AUTHORITY: {bundle['gaiaos']['authority']}

GAIAOS LOAD CONTRACT:
{bundle['loader']}

RUNTIME BOOTSTRAP:
{bundle['runtime_bootstrap']}

HOST INSTRUCTIONS:
{bundle['host_instructions']}

CURRENT STATE:
{json.dumps(bundle['current'], ensure_ascii=False, indent=2)}

VERSION:
{json.dumps(bundle['version'], ensure_ascii=False, indent=2)}

COUNCIL OPERATING CONTRACT:
{council['contract']}

COUNCIL COMMANDS:
{council['commands']}

CURRENT FAIRYOS:
{json.dumps(council['fairyos_current'], ensure_ascii=False, indent=2)}

CURRENT COUNCIL:
{council['council']}

OPERATOR PROFILES:
{json.dumps(council['profiles'], ensure_ascii=False, indent=2)}

OPERATOR PROSODY BASINS:
{council['prosody_basins']}

DISPATCH MATRIX:
{json.dumps(council['dispatch_matrix'], ensure_ascii=False, indent=2)}

HOT / WARM / COLD FABRIC:
{council['hot_warm_cold']}

RESPONSE MODES:
{json.dumps(council['response_modes'], ensure_ascii=False, indent=2)}

CAST WIDTH:
{json.dumps(council['cast_width'], ensure_ascii=False, indent=2)}

BRAINOS SUPPORT FABRIC:
{json.dumps(council['brainos_support'], ensure_ascii=False, indent=2)}

BRAINOS CONTEXT COMPASS:
{json.dumps(council['context_compass'], ensure_ascii=False, indent=2)}

MEMBER CONTINUITY CURRENT:
{json.dumps(council['member_continuity'], ensure_ascii=False, indent=2)}

WARM CANDIDATE BUFFER:
{council['warm_candidate_buffer']}

PROOF BOUNDARY:
{bundle['proof_boundary']}

When the user says "Load GaiaOS", report the verified source commit and loaded state. When the user invokes COUNCIL / GAIA COUNCIL / ASK <MEMBER> or a cast-width command, use the current Gaia Council sources above, preserve materially different operator positions, and keep the placeholder-roster boundary visible when identity adoption is material. For ordinary requests, use the HOT path and current visible context first; invoke BrainOS/ConvoOS support only when material. WARM candidates are not durable saves. Continue operating under the loaded GaiaOS contract until the user asks to stop or reload it."""


@mcp.tool()
def load_gaiaos() -> dict[str, Any]:
    """Load the current canonical GaiaOS bootstrap and council surface from GitHub."""
    return _load_bundle()


@mcp.tool()
def gaia_council() -> dict[str, Any]:
    """Return the full current source-backed Gaia Council packet from one Git commit."""
    commit = _resolve_commit()
    return {
        "source": f"{REPOSITORY}@{commit}",
        "authority": "NAOMI",
        "council": _council_bundle(commit),
        "effect_authority": "NONE_READ_ONLY",
    }


@mcp.tool()
def gaia_dispatch(
    signals: list[str],
    requested_members: list[str] | None = None,
    max_members: int = 3,
) -> dict[str, Any]:
    """Deterministically route explicit typed signals through the current GaiaOS FairyOS matrix."""
    commit = _resolve_commit()
    return _dispatch_packet(commit, signals, requested_members, max_members)


@mcp.tool()
def gaia_operator(member: str) -> dict[str, Any]:
    """Return one current GaiaOS operator profile and dispatch surface."""
    commit = _resolve_commit()
    return _operator_packet(commit, member)


@mcp.tool()
def gaia_brain() -> dict[str, Any]:
    """Return current Gaia-native BrainOS, chat-control, and warm-continuity source contracts."""
    commit = _resolve_commit()
    council = _council_bundle(commit)
    return {
        "source": f"{REPOSITORY}@{commit}",
        "authority": "NAOMI",
        "brainos_current": council["brainos_current"],
        "brainos_support": council["brainos_support"],
        "context_compass": council["context_compass"],
        "hot_warm_cold": council["hot_warm_cold"],
        "response_modes": council["response_modes"],
        "cast_width": council["cast_width"],
        "member_continuity": council["member_continuity"],
        "warm_candidate_buffer": council["warm_candidate_buffer"],
        "effect_authority": "NONE_READ_ONLY",
    }


@contextlib.asynccontextmanager
async def _lifespan(_: FastAPI):
    async with mcp.session_manager.run():
        yield


app = FastAPI(
    title="GaiaOS Carrier API",
    version=APP_VERSION,
    description=(
        "GaiaOS source loader plus source-backed council/dispatch, BrainOS/chat-control, "
        "and warm-continuity surfaces, a web carrier backed by the OpenAI Responses API, "
        "and a read-only MCP carrier."
    ),
    lifespan=_lifespan,
)


@app.get("/", response_class=HTMLResponse)
def home(response: Response) -> str:
    if API_KEY is not None:
        response.set_cookie(SESSION_COOKIE, _session_token(), httponly=True, samesite="lax", secure=True, max_age=86400)
    return """<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'><title>GaiaOS</title><style>body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;max-width:760px;margin:auto;padding:20px;background:#111;color:#eee}#chat{min-height:55vh;display:flex;flex-direction:column;gap:12px}.m{padding:12px 14px;border-radius:14px;white-space:pre-wrap}.u{background:#263238;align-self:flex-end}.a{background:#1d1d1d;border:1px solid #333}form{display:flex;gap:8px;position:sticky;bottom:0;background:#111;padding-top:10px}textarea{flex:1;border-radius:12px;padding:12px;font:inherit;background:#222;color:#eee;border:1px solid #444}button{border:0;border-radius:12px;padding:0 18px;font-weight:600}small{color:#aaa}</style></head><body><h1>GaiaOS</h1><small>Canonical carrier · GitHub source + Gaia Council + BrainOS + OpenAI Responses API · MCP</small><div id='chat'></div><form><textarea id='input' rows='2' placeholder='Say “Load GaiaOS”, “Council”, or ask anything…'></textarea><button>Send</button></form><script>const messages=[];const chat=document.querySelector('#chat');const input=document.querySelector('#input');function add(role,text){const d=document.createElement('div');d.className='m '+(role==='user'?'u':'a');d.textContent=text;chat.appendChild(d);window.scrollTo(0,document.body.scrollHeight)}document.querySelector('form').onsubmit=async e=>{e.preventDefault();const text=input.value.trim();if(!text)return;input.value='';messages.push({role:'user',content:text});add('user',text);try{const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},credentials:'same-origin',body:JSON.stringify({messages})});const j=await r.json();if(!r.ok)throw new Error(j.detail||'Request failed');messages.push({role:'assistant',content:j.output});add('assistant',j.output)}catch(err){add('assistant','ERROR: '+err.message)}};</script></body></html>"""


@app.get("/health", operation_id="health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "gaiaos-carrier",
        "api_version": APP_VERSION,
        "canonical_repository": REPOSITORY,
        "canonical_branch": BRANCH,
        "authentication_required": API_KEY is not None,
        "openai_configured": OPENAI_API_KEY is not None,
        "mcp_endpoint": "/mcp",
        "council_surface": True,
        "brain_support_surface": True,
        "hot_warm_cold_surface": True,
    }


@app.get("/gaiaos/load", operation_id="loadGaiaOS")
def load_gaiaos_http(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _authorize(authorization)
    return _load_bundle()


@app.get("/gaiaos/council", operation_id="getGaiaCouncil")
def gaia_council_http(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _authorize(authorization)
    commit = _resolve_commit()
    return {
        "source": f"{REPOSITORY}@{commit}",
        "authority": "NAOMI",
        "council": _council_bundle(commit),
        "effect_authority": "NONE_READ_ONLY",
    }


@app.get("/gaiaos/operator/{member}", operation_id="getGaiaOperator")
def gaia_operator_http(member: str, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _authorize(authorization)
    return _operator_packet(_resolve_commit(), member)


@app.post("/gaiaos/dispatch", operation_id="dispatchGaiaCouncil")
def gaia_dispatch_http(payload: DispatchRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _authorize(authorization)
    return _dispatch_packet(_resolve_commit(), payload.signals, payload.requested_members, payload.max_members)


@app.get("/gaiaos/brain", operation_id="getGaiaBrain")
def gaia_brain_http(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _authorize(authorization)
    commit = _resolve_commit()
    council = _council_bundle(commit)
    return {
        "source": f"{REPOSITORY}@{commit}",
        "authority": "NAOMI",
        "brainos_current": council["brainos_current"],
        "brainos_support": council["brainos_support"],
        "context_compass": council["context_compass"],
        "hot_warm_cold": council["hot_warm_cold"],
        "response_modes": council["response_modes"],
        "cast_width": council["cast_width"],
        "member_continuity": council["member_continuity"],
        "warm_candidate_buffer": council["warm_candidate_buffer"],
        "effect_authority": "NONE_READ_ONLY",
    }


@app.post("/chat")
def chat(request: ChatRequest, browser_request: Request) -> dict[str, Any]:
    _authorize_browser_session(browser_request)
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not configured on the carrier")

    bundle = _load_bundle()
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.responses.create(
        model=OPENAI_MODEL,
        instructions=_carrier_instructions(bundle),
        input=[{"role": message.role, "content": message.content} for message in request.messages],
    )
    return {"output": response.output_text, "model": OPENAI_MODEL, "source": bundle["gaiaos"]["source"]}


# The MCP server is mounted alongside the existing browser/API carrier.
app.mount("/mcp", mcp.streamable_http_app())
