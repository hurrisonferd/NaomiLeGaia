"""GaiaOS canonical loader, council carrier API, and remote MCP carrier."""

from __future__ import annotations

import base64
import contextlib
import hashlib
import html
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
    "GaiaOS is Naomi's read-only source-backed support carrier. For ordinary requests, "
    "use gaia(request) as the PRIMARY FRONT DOOR. It returns bounded context, conservative "
    "Gaia-native council routing, source binding, authority, and proof limits in one compact packet. "
    "Use gaia_selftest for diagnostics. Use load_gaiaos, gaia_council, gaia_brain, gaia_context, "
    "gaia_dispatch, and gaia_operator only for explicit deep inspection or debugging. Do not make "
    "Naomi or Raven manually orchestrate subsystem tools when gaia() is sufficient. These tools are "
    "read-only support surfaces; dispatch is not execution, WARM is not saved, and Naomi retains final authority."
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



def _galaxy_runtime():
    """Lazy-load MemoryOS/GALAXY runtime to avoid API import cycles."""
    import memcon_runtime
    import memcon_entrypoint
    return memcon_runtime, memcon_entrypoint._memory_runtime()


def _galaxy_retrieval_ids(runtime, record: dict) -> list[str]:
    scope = str(record.get("scope") or "MemoryOS")
    result = runtime.retrieve(str(record.get("statement", "")), scope, 10)
    rows = result.get("retrieval", {}).get("records", [])
    return [str(row.get("record_id")) for row in rows if row.get("record_id")]


@app.get("/galaxy/canary/start", response_class=HTMLResponse)
def galaxy_canary_start(browser_request: Request):
    """Direct canary entrypoint that does not depend on OPENAI_API_KEY.
    If opened directly, bootstrap the same signed browser session used by the GaiaOS home page.
    """
    bootstrap_session = API_KEY is not None and not browser_request.cookies.get(SESSION_COOKIE)
    if not bootstrap_session:
        _authorize_browser_session(browser_request)
    memcon_runtime, runtime = _galaxy_runtime()
    token = secrets.token_hex(6)
    source = f"galaxy-phase1-canary:{token}"
    session = runtime.start_session(source, f"GALAXY Phase 1 two-memory relation canary {token}")
    statement_a = f"GALAXY-CANARY-A [{token}]: The test beacon emits a cyan signal."
    statement_b = f"GALAXY-CANARY-B [{token}]: The cyan signal from Canary A is part of the same controlled GALAXY test."
    event_a = runtime.record_event(session["session_id"], "NAOMI", "GALAXY_CANARY_INPUT", statement_a, source)
    event_b = runtime.record_event(session["session_id"], "NAOMI", "GALAXY_CANARY_INPUT", statement_b, source)
    candidate_a = runtime.candidate_from_event(
        event_a["event_id"], authority="NAOMI", record_type="TEST", scope="MemoryOS",
        statement=statement_a, source=source, owner="GALAXY_CANARY_A",
        why_material="Controlled durable endpoint A for the GALAXY Phase-1 relation canary.",
    )
    candidate_b = runtime.candidate_from_event(
        event_b["event_id"], authority="NAOMI", record_type="TEST", scope="MemoryOS",
        statement=statement_b, source=source, owner="GALAXY_CANARY_B",
        why_material="Controlled durable endpoint B for the GALAXY Phase-1 relation canary.",
    )
    payload = {
        "status": "APPROVAL_REQUIRED",
        "token": token,
        "candidate_a": candidate_a,
        "candidate_b": candidate_b,
        "durable_writes_performed": [],
        "relation_write_performed": False,
    }
    response = HTMLResponse(
        "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
        "<h1>GALAXY two-memory canary</h1>"
        f"<pre style='white-space:pre-wrap'>{html.escape(json.dumps(payload, indent=2))}</pre>"
        "<p><a style='font-size:22px' href='/galaxy/canary/approve'>Approve the two controlled memories</a></p>"
        "<p>START created candidates only. No durable memory or relation has been written.</p>"
        "</body></html>"
    )
    if bootstrap_session:
        response.set_cookie(SESSION_COOKIE, _session_token(), httponly=True, samesite="lax", secure=True, max_age=86400)
    return response


@app.get("/galaxy/canary/approve", response_class=HTMLResponse)
def galaxy_canary_approve(browser_request: Request):
    """Explicitly promote the paired memories, then create only a PROPOSED shadow edge."""
    _authorize_browser_session(browser_request)
    memcon_runtime, runtime = _galaxy_runtime()
    candidate_a = memcon_runtime.get_latest_memory_candidate("GALAXY_CANARY_A", "CANDIDATE")
    candidate_b = memcon_runtime.get_latest_memory_candidate("GALAXY_CANARY_B", "CANDIDATE")
    if candidate_a is None or candidate_b is None:
        raise HTTPException(status_code=409, detail="No paired pending GALAXY canary. Start a new canary first.")
    event_a = memcon_runtime.get_session_event(str(candidate_a.get("event_id")))
    event_b = memcon_runtime.get_session_event(str(candidate_b.get("event_id")))
    if not event_a or not event_b or event_a.get("session_id") != event_b.get("session_id"):
        raise HTTPException(status_code=409, detail="Latest canary candidates are not a matched pair.")

    promotion_a = runtime.promote_candidate(str(candidate_a["candidate_id"]), True, "NAOMI")
    promotion_b = runtime.promote_candidate(str(candidate_b["candidate_id"]), True, "NAOMI")
    if promotion_a.get("status") != "VERIFIED" or promotion_b.get("status") != "VERIFIED":
        raise HTTPException(status_code=409, detail="Both canary memories must verify before relation proposal.")

    record_a = memcon_runtime.get_record(str(promotion_a["record_id"]))
    record_b = memcon_runtime.get_record(str(promotion_b["record_id"]))
    if record_a is None or record_b is None:
        raise HTTPException(status_code=500, detail="Durable record readback failed.")

    pre_ids = _galaxy_retrieval_ids(runtime, record_b)
    relation = memcon_runtime.galaxy_propose_relation(
        source_record_id=str(record_b["record_id"]),
        target_record_id=str(record_a["record_id"]),
        relation_type="CONTEXT_FOR",
        strength=1.0,
        evidence={
            "source": "galaxy-phase1-two-memory-canary",
            "basis": "Controlled B CONTEXT_FOR A relation.",
            "session_id": event_a.get("session_id"),
            "pre_verification_retrieval_record_ids": pre_ids,
        },
        classifier="GALAXY_CONTROLLED_CANARY_V1",
    )
    edge_id = (relation.get("relation") or {}).get("edge_id")
    payload = {
        "status": "RELATION_PROPOSED",
        "memory_a_record_id": record_a["record_id"],
        "memory_b_record_id": record_b["record_id"],
        "relation": relation,
        "pre_verification_retrieval_record_ids": pre_ids,
    }
    verify = (
        f"<p><a style='font-size:22px' href='/galaxy/canary/verify/{html.escape(str(edge_id))}'>Verify proposed GALAXY edge</a></p>"
        if edge_id else "<p>No edge_id returned. Verification is not available.</p>"
    )
    return HTMLResponse(
        "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
        "<h1>GALAXY canary approval</h1>"
        f"<pre style='white-space:pre-wrap'>{html.escape(json.dumps(payload, indent=2))}</pre>"
        + verify +
        "<p>The relation is still PROPOSED and has no retrieval effect.</p>"
        "</body></html>"
    )


@app.get("/galaxy/canary/verify/{edge_id}", response_class=HTMLResponse)
def galaxy_canary_verify(edge_id: str, browser_request: Request):
    """Verify one proposed edge and compare ordinary MemoryOS retrieval before and after."""
    _authorize_browser_session(browser_request)
    memcon_runtime, runtime = _galaxy_runtime()
    before = memcon_runtime.galaxy_relation(edge_id)
    if before is None:
        raise HTTPException(status_code=404, detail="Unknown GALAXY edge_id.")
    source = memcon_runtime.get_record(str(before.get("source_record_id")))
    target = memcon_runtime.get_record(str(before.get("target_record_id")))
    if source is None or target is None:
        raise HTTPException(status_code=409, detail="GALAXY relation endpoint missing.")
    pre_ids = list((before.get("evidence") or {}).get("pre_verification_retrieval_record_ids") or [])
    verified = memcon_runtime.galaxy_verify_relation(edge_id, authority="NAOMI", approved=True)
    post_ids = _galaxy_retrieval_ids(runtime, source)
    payload = {
        "status": "VERIFIED",
        "verification": verified,
        "source_orbit": memcon_runtime.galaxy_record(str(source["record_id"])),
        "target_orbit": memcon_runtime.galaxy_record(str(target["record_id"])),
        "retrieval_comparison": {
            "before_record_ids": pre_ids,
            "after_record_ids": post_ids,
            "unchanged": bool(pre_ids) and pre_ids == post_ids,
            "retrieval_weighting_enabled": memcon_runtime.galaxy_status().get("retrieval_weighting_enabled"),
        },
    }
    return HTMLResponse(
        "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
        "<h1>GALAXY edge verification</h1>"
        f"<pre style='white-space:pre-wrap'>{html.escape(json.dumps(payload, indent=2))}</pre>"
        "</body></html>"
    )



def _galaxy_latest_controlled_verified_edge(memcon_runtime):
    """Resolve the newest verified Phase-1 canary edge for bounded Phase-2 calibration."""
    memcon_runtime.initialize()
    with memcon_runtime._db() as conn:
        row = memcon_runtime._fetchone_dict(
            conn,
            """SELECT edge_id FROM memory_relations
               WHERE status='VERIFIED' AND classifier='GALAXY_CONTROLLED_CANARY_V1'
               ORDER BY verified_at DESC, created_at DESC LIMIT 1""",
        )
    if not row:
        return None
    return memcon_runtime.galaxy_relation(str(row["edge_id"]))


@app.get("/galaxy/gravity/canary/preview", response_class=HTMLResponse)
def galaxy_gravity_canary_preview(browser_request: Request):
    """Preview Phase-2 scores for the proven Phase-1 pair. Performs no write."""
    bootstrap_session = API_KEY is not None and not browser_request.cookies.get(SESSION_COOKIE)
    if not bootstrap_session:
        _authorize_browser_session(browser_request)
    memcon_runtime, _ = _galaxy_runtime()
    relation = _galaxy_latest_controlled_verified_edge(memcon_runtime)
    if relation is None:
        raise HTTPException(status_code=409, detail="No verified controlled GALAXY canary edge is available.")
    source_id = str(relation["source_record_id"])
    target_id = str(relation["target_record_id"])
    payload = {
        "status": "SHADOW_PREVIEW",
        "phase": "PHASE_2_GRAVITY_SHADOW",
        "edge_id": relation["edge_id"],
        "source_preview": memcon_runtime.galaxy_gravity_preview(source_id),
        "target_preview": memcon_runtime.galaxy_gravity_preview(target_id),
        "writes_performed": [],
        "retrieval_weighting_enabled": False,
        "proof_boundary": (
            "These are deterministic shadow previews only. They are not authority, truth, or retrieval ordering. "
            "No gravity row is written by this preview."
        ),
    }
    run_url = "/galaxy/gravity/canary/run?edge_id=" + html.escape(str(relation["edge_id"]), quote=True)
    response = HTMLResponse(
        "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
        "<h1>GALAXY Phase 2 gravity preview</h1>"
        f"<pre style='white-space:pre-wrap'>{html.escape(json.dumps(payload, indent=2))}</pre>"
        f"<p><a style='font-size:22px' href='{run_url}'>Store these two shadow scores and run the retrieval control</a></p>"
        "<p>This next action writes only explainable shadow gravity rows. Ordinary retrieval remains unweighted.</p>"
        "</body></html>"
    )
    if bootstrap_session:
        response.set_cookie(SESSION_COOKIE, _session_token(), httponly=True, samesite="lax", secure=True, max_age=86400)
    return response


@app.get("/galaxy/gravity/canary/run", response_class=HTMLResponse)
def galaxy_gravity_canary_run(browser_request: Request, edge_id: str | None = None):
    """Persist two shadow scores and prove ordinary retrieval ordering is unchanged."""
    _authorize_browser_session(browser_request)
    memcon_runtime, runtime = _galaxy_runtime()
    relation = memcon_runtime.galaxy_relation(edge_id) if edge_id else _galaxy_latest_controlled_verified_edge(memcon_runtime)
    if relation is None:
        raise HTTPException(status_code=404, detail="Unknown or unavailable GALAXY edge.")
    if relation.get("status") != "VERIFIED" or relation.get("classifier") != "GALAXY_CONTROLLED_CANARY_V1":
        raise HTTPException(status_code=409, detail="Phase-2 canary requires a VERIFIED controlled Phase-1 edge.")

    source_id = str(relation["source_record_id"])
    target_id = str(relation["target_record_id"])
    source = memcon_runtime.get_record(source_id)
    target = memcon_runtime.get_record(target_id)
    if source is None or target is None:
        raise HTTPException(status_code=409, detail="Controlled relation endpoint is missing.")

    before_ids = _galaxy_retrieval_ids(runtime, source)
    source_score = memcon_runtime.galaxy_calculate_gravity(source_id, authority="NAOMI", approved=True)
    target_score = memcon_runtime.galaxy_calculate_gravity(target_id, authority="NAOMI", approved=True)
    after_ids = _galaxy_retrieval_ids(runtime, source)
    galaxy = memcon_runtime.galaxy_status()

    payload = {
        "status": "SHADOW_GRAVITY_CALCULATED",
        "phase": galaxy.get("phase"),
        "edge_id": relation["edge_id"],
        "source_score": source_score,
        "target_score": target_score,
        "source_orbit": memcon_runtime.galaxy_record(source_id),
        "target_orbit": memcon_runtime.galaxy_record(target_id),
        "retrieval_control": {
            "before_record_ids": before_ids,
            "after_record_ids": after_ids,
            "unchanged": bool(before_ids) and before_ids == after_ids,
            "retrieval_weighting_enabled": galaxy.get("retrieval_weighting_enabled"),
        },
        "guardrails": {
            "gravity_is_authority": False,
            "stored_gravity_feeds_its_own_score": False,
            "recency_component_enabled": False,
            "physical_pruning_enabled": galaxy.get("physical_pruning_enabled"),
        },
        "proof_boundary": (
            "This canary proves only that explainable shadow scores can be stored/read back for the controlled pair "
            "while ordinary retrieval remains unchanged. It does not prove score quality or authorize Phase-3 weighting."
        ),
    }
    return HTMLResponse(
        "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
        "<h1>GALAXY Phase 2 gravity canary</h1>"
        f"<pre style='white-space:pre-wrap'>{html.escape(json.dumps(payload, indent=2))}</pre>"
        "</body></html>"
    )


@app.get("/galaxy/gravity/{record_id}", response_class=HTMLResponse)
def galaxy_gravity_inspection(record_id: str, browser_request: Request):
    """Read stored and preview shadow gravity for one record. No write."""
    _authorize_browser_session(browser_request)
    memcon_runtime, _ = _galaxy_runtime()
    try:
        preview = memcon_runtime.galaxy_gravity_preview(record_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown durable record_id.")
    payload = {
        "status": "OBSERVED" if memcon_runtime.galaxy_gravity(record_id) is not None else "SHADOW_PREVIEW_ONLY",
        "stored": memcon_runtime.galaxy_gravity(record_id),
        "preview": preview,
        "retrieval_effect": "NONE_SHADOW_MODE",
        "writes_performed": [],
    }
    return HTMLResponse(
        "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
        "<h1>GALAXY gravity inspection</h1>"
        f"<pre style='white-space:pre-wrap'>{html.escape(json.dumps(payload, indent=2))}</pre>"
        "</body></html>"
    )



GALAXY_CALIBRATION_CLASSIFIER = "GALAXY_GRAVITY_CALIBRATION_V1"
GALAXY_CALIBRATION_PREFIX = "galaxy-phase2-calibration:"
GALAXY_CALIBRATION_OWNERS = {
    "CORE": "GALAXY_CAL_CORE",
    "SATELLITE": "GALAXY_CAL_SATELLITE",
    "REINFORCER": "GALAXY_CAL_REINFORCER",
    "REVISION": "GALAXY_CAL_REVISION",
    "ISOLATED": "GALAXY_CAL_ISOLATED",
}


def _galaxy_calibration_records(memcon_runtime, source: str) -> dict[str, dict]:
    """Resolve controlled calibration records by their preserved memory_owner notes."""
    memcon_runtime.initialize()
    with memcon_runtime._db() as conn:
        rows = memcon_runtime._fetchall_dicts(
            conn,
            "SELECT * FROM memory_records WHERE source=? ORDER BY created_at",
            (source,),
        )
    by_role: dict[str, dict] = {}
    owner_to_role = {owner: role for role, owner in GALAXY_CALIBRATION_OWNERS.items()}
    for row in rows:
        owner = ""
        try:
            owner = str(json.loads(str(row.get("notes") or "{}")).get("memory_owner") or "")
        except (TypeError, json.JSONDecodeError):
            owner = ""
        role = owner_to_role.get(owner)
        if role:
            by_role[role] = row
    return by_role


def _galaxy_calibration_edges(memcon_runtime, records: dict[str, dict]) -> list[dict]:
    """Return only calibration edges wholly contained in this controlled constellation."""
    record_ids = {str(record["record_id"]) for record in records.values()}
    if not record_ids:
        return []
    memcon_runtime.initialize()
    with memcon_runtime._db() as conn:
        rows = memcon_runtime._fetchall_dicts(
            conn,
            "SELECT * FROM memory_relations WHERE classifier=? ORDER BY created_at",
            (GALAXY_CALIBRATION_CLASSIFIER,),
        )
    return [
        row for row in rows
        if str(row.get("source_record_id")) in record_ids
        and str(row.get("target_record_id")) in record_ids
    ]


def _galaxy_calibration_context(memcon_runtime, session_id: str) -> tuple[dict, str, dict[str, dict]]:
    session = memcon_runtime.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Unknown calibration session.")
    source = str(session.get("source") or "")
    if not source.startswith(GALAXY_CALIBRATION_PREFIX):
        raise HTTPException(status_code=409, detail="Session is not a GALAXY Phase-2 calibration session.")
    return session, source, _galaxy_calibration_records(memcon_runtime, source)


def _galaxy_calibration_summary(previews: dict[str, dict]) -> dict:
    scores = {role: float(item["gravity_score"]) for role, item in previews.items()}
    ordered = [
        {"role": role, "gravity_score": score}
        for role, score in sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    ]
    component_names = sorted({
        name
        for item in previews.values()
        for name in (item.get("components") or {}).keys()
    })
    variation = {}
    for name in component_names:
        values = sorted({
            float((item.get("components") or {}).get(name, {}).get("normalized", 0.0))
            for item in previews.values()
        })
        variation[name] = {
            "normalized_values": values,
            "varies_across_constellation": len(values) > 1,
        }
    expected = {
        "isolated_below_satellite": scores.get("ISOLATED", 0.0) < scores.get("SATELLITE", 0.0),
        "satellite_below_reinforcer": scores.get("SATELLITE", 0.0) < scores.get("REINFORCER", 0.0),
        "reinforcer_below_core": scores.get("REINFORCER", 0.0) < scores.get("CORE", 0.0),
        "core_below_revision": scores.get("CORE", 0.0) < scores.get("REVISION", 0.0),
    }
    return {
        "scores_by_role": scores,
        "ordered_high_to_low": ordered,
        "unique_score_count": len(set(scores.values())),
        "score_spread": round(max(scores.values()) - min(scores.values()), 6) if scores else 0.0,
        "component_variation": variation,
        "synthetic_discrimination_checks": expected,
        "all_synthetic_discrimination_checks_pass": bool(expected) and all(expected.values()),
        "interpretation_boundary": (
            "Passing these synthetic checks shows that the formula distinguishes deliberately different graph structures. "
            "It does not prove that the weights predict real-world usefulness."
        ),
    }


@app.get("/galaxy/gravity/calibration/start", response_class=HTMLResponse)
def galaxy_gravity_calibration_start(browser_request: Request):
    """Create a five-record synthetic calibration constellation as candidates only."""
    from urllib.parse import urlencode

    bootstrap_session = API_KEY is not None and not browser_request.cookies.get(SESSION_COOKIE)
    if not bootstrap_session:
        _authorize_browser_session(browser_request)
    memcon_runtime, runtime = _galaxy_runtime()
    token = secrets.token_hex(6)
    source = GALAXY_CALIBRATION_PREFIX + token
    session = runtime.start_session(source, f"GALAXY Phase 2 broader gravity calibration {token}")

    specs = {
        "CORE": "GALAXY-CAL-CORE [{token}]: The calibration core reports a violet carrier pulse.",
        "SATELLITE": "GALAXY-CAL-SATELLITE [{token}]: A satellite note provides limited context for the calibration core.",
        "REINFORCER": "GALAXY-CAL-REINFORCER [{token}]: An independent observation reinforces the calibration core.",
        "REVISION": "GALAXY-CAL-REVISION [{token}]: A later controlled observation revises the calibration core toward ultraviolet.",
        "ISOLATED": "GALAXY-CAL-ISOLATED [{token}]: This control memory has no GALAXY relations.",
    }
    candidates = {}
    for role, template in specs.items():
        statement = template.format(token=token)
        event = runtime.record_event(session["session_id"], "NAOMI", "GALAXY_CALIBRATION_INPUT", statement, source)
        candidates[role] = runtime.candidate_from_event(
            event["event_id"],
            authority="NAOMI",
            record_type="TEST",
            scope="MemoryOS",
            statement=statement,
            source=source,
            owner=GALAXY_CALIBRATION_OWNERS[role],
            why_material=f"Controlled {role.lower()} endpoint for GALAXY Phase-2 broader gravity calibration.",
        )

    payload = {
        "status": "CALIBRATION_CANDIDATES_READY",
        "phase": "PHASE_2_GRAVITY_SHADOW",
        "token": token,
        "session_id": session["session_id"],
        "roles": list(specs.keys()),
        "candidates": candidates,
        "durable_memory_writes_performed": [],
        "relation_writes_performed": [],
        "gravity_writes_performed": [],
        "retrieval_weighting_enabled": False,
        "authority_boundary": (
            "START creates calibration candidates only. It does not promote durable memories, "
            "create relations, verify edges, or write gravity."
        ),
    }
    approve_url = "/galaxy/gravity/calibration/approve?" + urlencode({"session_id": session["session_id"]})
    response = HTMLResponse(
        "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
        "<h1>GALAXY broader Phase 2 calibration</h1>"
        f"<pre style='white-space:pre-wrap'>{html.escape(json.dumps(payload, indent=2))}</pre>"
        f"<p><a style='font-size:22px' href='{html.escape(approve_url, quote=True)}'>Approve five controlled calibration memories and propose the calibration graph</a></p>"
        "<p>This approval promotes the five controlled memories and proposes four shadow relations. The relations remain PROPOSED.</p>"
        "</body></html>"
    )
    if bootstrap_session:
        response.set_cookie(SESSION_COOKIE, _session_token(), httponly=True, samesite="lax", secure=True, max_age=86400)
    return response


@app.get("/galaxy/gravity/calibration/approve", response_class=HTMLResponse)
def galaxy_gravity_calibration_approve(browser_request: Request, session_id: str):
    """Promote the controlled records and propose, but do not verify, the calibration graph."""
    from urllib.parse import urlencode

    _authorize_browser_session(browser_request)
    memcon_runtime, runtime = _galaxy_runtime()
    session, source, records = _galaxy_calibration_context(memcon_runtime, session_id)

    if len(records) < len(GALAXY_CALIBRATION_OWNERS):
        pending = memcon_runtime.list_memory_candidates(session_id=session_id, status="CANDIDATE", limit=50)
        by_owner = {str(item.get("owner") or ""): item for item in pending.get("candidates", [])}
        promotions = {}
        for role, owner in GALAXY_CALIBRATION_OWNERS.items():
            if role in records:
                promotions[role] = {"status": "ALREADY_DURABLE", "record_id": records[role]["record_id"]}
                continue
            candidate = by_owner.get(owner)
            if not candidate:
                raise HTTPException(status_code=409, detail=f"Missing calibration candidate for {role}.")
            result = runtime.promote_candidate(str(candidate["candidate_id"]), True, "NAOMI")
            if result.get("status") != "VERIFIED":
                raise HTTPException(status_code=409, detail=f"Calibration memory {role} did not verify.")
            promotions[role] = result
        records = _galaxy_calibration_records(memcon_runtime, source)
    else:
        promotions = {
            role: {"status": "ALREADY_DURABLE", "record_id": record["record_id"]}
            for role, record in records.items()
        }

    if set(records) != set(GALAXY_CALIBRATION_OWNERS):
        raise HTTPException(status_code=409, detail="Controlled calibration constellation is incomplete after promotion.")

    relation_specs = [
        ("SATELLITE", "CONTEXT_FOR", "CORE", 0.40, "Low-strength contextual satellite."),
        ("REINFORCER", "REINFORCES", "CORE", 0.80, "Independent reinforcement of the core."),
        ("REVISION", "REVISES", "CORE", 0.90, "Controlled revision signal aimed at the core."),
        ("REVISION", "CONTRADICTS", "REINFORCER", 0.70, "Controlled contradiction introduces revision significance."),
    ]
    proposals = []
    for source_role, relation_type, target_role, strength, basis in relation_specs:
        proposals.append(memcon_runtime.galaxy_propose_relation(
            source_record_id=str(records[source_role]["record_id"]),
            target_record_id=str(records[target_role]["record_id"]),
            relation_type=relation_type,
            strength=strength,
            evidence={
                "source": "galaxy-phase2-broader-calibration",
                "session_id": session_id,
                "calibration_source": source,
                "source_role": source_role,
                "target_role": target_role,
                "basis": basis,
            },
            classifier=GALAXY_CALIBRATION_CLASSIFIER,
        ))

    edges = _galaxy_calibration_edges(memcon_runtime, records)
    payload = {
        "status": "CALIBRATION_GRAPH_PROPOSED",
        "phase": "PHASE_2_GRAVITY_SHADOW",
        "session_id": session_id,
        "records": {role: record["record_id"] for role, record in records.items()},
        "promotions": promotions,
        "proposals": proposals,
        "edges": edges,
        "verified_edge_count": sum(1 for edge in edges if edge.get("status") == "VERIFIED"),
        "retrieval_weighting_enabled": False,
        "authority_boundary": (
            "The five memories are durable under explicit approval. Calibration edges are still only PROPOSED "
            "unless a prior idempotent run already verified them. Gravity has not been written by this step."
        ),
    }
    verify_url = "/galaxy/gravity/calibration/verify?" + urlencode({"session_id": session_id})
    return HTMLResponse(
        "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
        "<h1>GALAXY calibration graph proposal</h1>"
        f"<pre style='white-space:pre-wrap'>{html.escape(json.dumps(payload, indent=2))}</pre>"
        f"<p><a style='font-size:22px' href='{html.escape(verify_url, quote=True)}'>Verify the four controlled calibration edges</a></p>"
        "<p>Verification is a separate Naomi-authorized step. No gravity scoring occurs here.</p>"
        "</body></html>"
    )


@app.get("/galaxy/gravity/calibration/verify", response_class=HTMLResponse)
def galaxy_gravity_calibration_verify(browser_request: Request, session_id: str):
    """Explicitly verify the four controlled calibration edges, with no gravity write."""
    from urllib.parse import urlencode

    _authorize_browser_session(browser_request)
    memcon_runtime, _ = _galaxy_runtime()
    _, _, records = _galaxy_calibration_context(memcon_runtime, session_id)
    if len(records) != len(GALAXY_CALIBRATION_OWNERS):
        raise HTTPException(status_code=409, detail="Calibration records are incomplete.")
    edges = _galaxy_calibration_edges(memcon_runtime, records)
    if len(edges) != 4:
        raise HTTPException(status_code=409, detail=f"Expected 4 controlled calibration edges, found {len(edges)}.")

    verification = []
    for edge in edges:
        verification.append(memcon_runtime.galaxy_verify_relation(
            str(edge["edge_id"]), authority="NAOMI", approved=True
        ))
    readback = _galaxy_calibration_edges(memcon_runtime, records)
    all_verified = len(readback) == 4 and all(edge.get("status") == "VERIFIED" for edge in readback)
    payload = {
        "status": "CALIBRATION_GRAPH_VERIFIED" if all_verified else "HOLD",
        "phase": "PHASE_2_GRAVITY_SHADOW",
        "session_id": session_id,
        "verification": verification,
        "edge_readback": readback,
        "all_four_edges_verified": all_verified,
        "gravity_writes_performed": [],
        "retrieval_weighting_enabled": False,
        "proof_boundary": (
            "This step proves only the controlled calibration graph verification/readback. "
            "No gravity score is calculated or stored here."
        ),
    }
    preview_url = "/galaxy/gravity/calibration/preview?" + urlencode({"session_id": session_id})
    return HTMLResponse(
        "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
        "<h1>GALAXY calibration graph verification</h1>"
        f"<pre style='white-space:pre-wrap'>{html.escape(json.dumps(payload, indent=2))}</pre>"
        + (
            f"<p><a style='font-size:22px' href='{html.escape(preview_url, quote=True)}'>Preview broader shadow-gravity calibration</a></p>"
            if all_verified else
            "<p>Graph is not fully verified. Do not proceed to scoring.</p>"
        )
        + "</body></html>"
    )


@app.get("/galaxy/gravity/calibration/preview", response_class=HTMLResponse)
def galaxy_gravity_calibration_preview(browser_request: Request, session_id: str):
    """Preview scores over a deliberately varied five-record graph. No gravity writes."""
    from urllib.parse import urlencode

    _authorize_browser_session(browser_request)
    memcon_runtime, _ = _galaxy_runtime()
    _, _, records = _galaxy_calibration_context(memcon_runtime, session_id)
    edges = _galaxy_calibration_edges(memcon_runtime, records)
    if len(edges) != 4 or not all(edge.get("status") == "VERIFIED" for edge in edges):
        raise HTTPException(status_code=409, detail="Calibration graph must have exactly four VERIFIED edges before preview.")

    previews = {
        role: memcon_runtime.galaxy_gravity_preview(str(record["record_id"]))
        for role, record in records.items()
    }
    payload = {
        "status": "BROADER_SHADOW_PREVIEW",
        "phase": "PHASE_2_GRAVITY_SHADOW",
        "session_id": session_id,
        "records": {role: record["record_id"] for role, record in records.items()},
        "verified_edges": edges,
        "previews": previews,
        "calibration_summary": _galaxy_calibration_summary(previews),
        "gravity_writes_performed": [],
        "retrieval_weighting_enabled": False,
        "proof_boundary": (
            "This synthetic constellation tests discrimination and component behavior only. "
            "It does not prove that shadow weights correspond to real-world memory usefulness."
        ),
    }
    run_url = "/galaxy/gravity/calibration/run?" + urlencode({"session_id": session_id})
    return HTMLResponse(
        "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
        "<h1>GALAXY broader Phase 2 gravity preview</h1>"
        f"<pre style='white-space:pre-wrap'>{html.escape(json.dumps(payload, indent=2))}</pre>"
        f"<p><a style='font-size:22px' href='{html.escape(run_url, quote=True)}'>Store the five shadow scores and run retrieval controls</a></p>"
        "<p>Gravity remains non-authoritative and retrieval weighting remains disabled.</p>"
        "</body></html>"
    )


@app.get("/galaxy/gravity/calibration/run", response_class=HTMLResponse)
def galaxy_gravity_calibration_run(browser_request: Request, session_id: str):
    """Store/re-read the varied calibration scores and compare ordinary retrieval before/after."""
    _authorize_browser_session(browser_request)
    memcon_runtime, runtime = _galaxy_runtime()
    _, _, records = _galaxy_calibration_context(memcon_runtime, session_id)
    edges = _galaxy_calibration_edges(memcon_runtime, records)
    if len(edges) != 4 or not all(edge.get("status") == "VERIFIED" for edge in edges):
        raise HTTPException(status_code=409, detail="Calibration graph is not fully verified.")

    before = {
        role: _galaxy_retrieval_ids(runtime, record)
        for role, record in records.items()
    }
    scoring = {
        role: memcon_runtime.galaxy_calculate_gravity(
            str(record["record_id"]), authority="NAOMI", approved=True
        )
        for role, record in records.items()
    }
    after = {
        role: _galaxy_retrieval_ids(runtime, record)
        for role, record in records.items()
    }
    previews = {
        role: memcon_runtime.galaxy_gravity_preview(str(record["record_id"]))
        for role, record in records.items()
    }
    galaxy = memcon_runtime.galaxy_status()
    retrieval_checks = {
        role: {
            "before_record_ids": before[role],
            "after_record_ids": after[role],
            "unchanged": bool(before[role]) and before[role] == after[role],
        }
        for role in records
    }
    new_receipt_count = sum(1 for item in scoring.values() if item.get("receipt"))
    idempotent_count = sum(1 for item in scoring.values() if item.get("idempotent") is True)
    payload = {
        "status": "BROADER_SHADOW_CALIBRATION_RAN",
        "phase": galaxy.get("phase"),
        "session_id": session_id,
        "scores": scoring,
        "orbits": {
            role: memcon_runtime.galaxy_record(str(record["record_id"]))
            for role, record in records.items()
        },
        "calibration_summary": _galaxy_calibration_summary(previews),
        "retrieval_controls": retrieval_checks,
        "all_retrieval_orders_unchanged": all(item["unchanged"] for item in retrieval_checks.values()),
        "new_receipt_count": new_receipt_count,
        "idempotent_count": idempotent_count,
        "all_five_idempotent": idempotent_count == len(records),
        "retrieval_weighting_enabled": galaxy.get("retrieval_weighting_enabled"),
        "guardrails": {
            "gravity_is_authority": False,
            "stored_gravity_feeds_its_own_score": False,
            "recency_component_enabled": False,
            "physical_pruning_enabled": galaxy.get("physical_pruning_enabled"),
        },
        "proof_boundary": (
            "This bounded synthetic calibration measures score discrimination, idempotency, readback, and retrieval non-effect. "
            "It does not establish real-world optimal weights and does not authorize Phase-3 weighted retrieval."
        ),
    }
    return HTMLResponse(
        "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
        "<h1>GALAXY broader Phase 2 gravity calibration</h1>"
        f"<pre style='white-space:pre-wrap'>{html.escape(json.dumps(payload, indent=2))}</pre>"
        "<p>Reopening this exact URL is the idempotency check. Identical inputs should produce no new receipts.</p>"
        "</body></html>"
    )



GALAXY_REAL_CALIBRATION_LIMIT = 8


def _galaxy_real_memory_population(memcon_runtime) -> tuple[list[dict], list[dict]]:
    """Read the non-test MemoryOS population and its VERIFIED graph without mutation."""
    memcon_runtime.initialize()
    with memcon_runtime._db() as conn:
        records = memcon_runtime._fetchall_dicts(
            conn,
            """SELECT * FROM memory_records
               WHERE scope='MemoryOS'
                 AND upper(record_type) <> 'TEST'
                 AND source NOT LIKE 'galaxy-phase1-canary:%'
                 AND source NOT LIKE 'galaxy-phase2-calibration:%'
               ORDER BY created_at DESC""",
        )
        edges = memcon_runtime._fetchall_dicts(
            conn,
            """SELECT edge_id, source_record_id, target_record_id, relation_type,
                      strength, classifier, authority, created_at, verified_at
               FROM memory_relations
               WHERE status='VERIFIED'
               ORDER BY verified_at DESC, created_at DESC""",
        )
    record_ids = {str(record["record_id"]) for record in records}
    real_edges = [
        edge for edge in edges
        if str(edge.get("source_record_id")) in record_ids
        and str(edge.get("target_record_id")) in record_ids
    ]
    return records, real_edges


def _galaxy_real_relation_profile(record_id: str, edges: list[dict]) -> dict:
    incident = [
        edge for edge in edges
        if str(edge.get("source_record_id")) == record_id
        or str(edge.get("target_record_id")) == record_id
    ]
    strengths = [
        max(0.0, min(float(edge.get("strength") or 0.0), 1.0))
        for edge in incident
    ]
    significant_types = {"CONTRADICTS", "REVISES", "SUPERSEDES"}
    significant_count = sum(
        1 for edge in incident
        if str(edge.get("relation_type") or "") in significant_types
    )
    return {
        "verified_relation_count": len(incident),
        "verified_relation_types": sorted({
            str(edge.get("relation_type") or "") for edge in incident
            if str(edge.get("relation_type") or "")
        }),
        "mean_verified_relation_strength": round(
            (sum(strengths) / len(strengths)) if strengths else 0.0, 6
        ),
        "revision_significance_edges": significant_count,
    }


def _galaxy_real_sample(records: list[dict], edges: list[dict], limit: int) -> tuple[list[dict], dict]:
    """Select a deterministic bounded sample favoring naturally distinct graph profiles."""
    limit = max(1, min(int(limit), GALAXY_REAL_CALIBRATION_LIMIT))
    enriched = []
    signatures: dict[tuple, list[dict]] = {}
    for record in records:
        record_id = str(record["record_id"])
        profile = _galaxy_real_relation_profile(record_id, edges)
        item = {"record": record, "relation_profile": profile}
        enriched.append(item)
        signature = (
            int(profile["verified_relation_count"]),
            tuple(profile["verified_relation_types"]),
            float(profile["mean_verified_relation_strength"]),
            int(profile["revision_significance_edges"]),
            str(record.get("authority") or ""),
            str(record.get("status") or ""),
        )
        signatures.setdefault(signature, []).append(item)

    representatives = [items[0] for items in signatures.values()]
    representatives.sort(
        key=lambda item: (
            -int(item["relation_profile"]["verified_relation_count"]),
            -int(item["relation_profile"]["revision_significance_edges"]),
            -float(item["relation_profile"]["mean_verified_relation_strength"]),
            str(item["record"].get("created_at") or ""),
        )
    )

    selected = representatives[:limit]
    selected_ids = {str(item["record"]["record_id"]) for item in selected}
    if len(selected) < limit:
        for item in enriched:
            record_id = str(item["record"]["record_id"])
            if record_id in selected_ids:
                continue
            selected.append(item)
            selected_ids.add(record_id)
            if len(selected) >= limit:
                break

    relation_bearing_count = sum(
        1 for item in enriched
        if int(item["relation_profile"]["verified_relation_count"]) > 0
    )
    summary = {
        "eligible_real_memory_count": len(records),
        "relation_bearing_real_memory_count": relation_bearing_count,
        "zero_relation_real_memory_count": len(records) - relation_bearing_count,
        "unique_relation_profile_count": len(signatures),
        "selected_sample_count": len(selected),
        "selection_method": (
            "One newest representative per naturally distinct VERIFIED relation profile, "
            "favoring higher relation degree/revision significance/mean strength, then fill "
            "remaining slots with newest eligible records. No relation or memory is modified."
        ),
    }
    return selected, summary


@app.get("/galaxy/gravity/real-calibration/preview", response_class=HTMLResponse)
def galaxy_gravity_real_calibration_preview(
    browser_request: Request,
    limit: int = GALAXY_REAL_CALIBRATION_LIMIT,
):
    """Observe shadow-v1 over existing non-test memories. Performs zero writes."""
    bootstrap_session = API_KEY is not None and not browser_request.cookies.get(SESSION_COOKIE)
    if not bootstrap_session:
        _authorize_browser_session(browser_request)
    memcon_runtime, _ = _galaxy_runtime()

    records, edges = _galaxy_real_memory_population(memcon_runtime)
    selected, population = _galaxy_real_sample(records, edges, limit)
    sample = []
    preview_scores = []
    relation_counts = []
    for item in selected:
        record = item["record"]
        record_id = str(record["record_id"])
        preview = memcon_runtime.galaxy_gravity_preview(record_id)
        stored = memcon_runtime.galaxy_gravity(record_id)
        preview_scores.append(float(preview["gravity_score"]))
        relation_counts.append(int(item["relation_profile"]["verified_relation_count"]))
        sample.append({
            "record": {
                "record_id": record_id,
                "authority": record.get("authority"),
                "record_type": record.get("record_type"),
                "scope": record.get("scope"),
                "statement": record.get("statement"),
                "source": record.get("source"),
                "status": record.get("status"),
                "created_at": record.get("created_at"),
                "updated_at": record.get("updated_at"),
                "supersedes": record.get("supersedes"),
            },
            "relation_profile": item["relation_profile"],
            "shadow_preview": preview,
            "stored_shadow_gravity": stored,
        })

    unique_scores = sorted(set(preview_scores))
    relation_bearing = population["relation_bearing_real_memory_count"]
    profile_count = population["unique_relation_profile_count"]
    readiness = (
        "OBSERVABLE_GRAPH_DIVERSITY"
        if relation_bearing >= 2 and profile_count >= 2
        else "GRAPH_COVERAGE_LIMITED"
    )
    diagnostics = {
        **population,
        "sample_unique_score_count": len(unique_scores),
        "sample_score_values": unique_scores,
        "sample_score_spread": (
            round(max(unique_scores) - min(unique_scores), 6)
            if unique_scores else 0.0
        ),
        "sample_relation_count_values": sorted(set(relation_counts)),
        "calibration_readiness": readiness,
        "coverage_interpretation": (
            "Natural graph diversity exists in the current non-test MemoryOS population. "
            "Naomi can now compare score explanations against actual memory importance/usefulness."
            if readiness == "OBSERVABLE_GRAPH_DIVERSITY"
            else
            "The current non-test MemoryOS population does not yet contain enough naturally varied VERIFIED "
            "GALAXY structure for meaningful real-memory weight calibration. Equal or near-equal scores here "
            "are a graph-coverage finding, not evidence that the formula is well calibrated."
        ),
    }
    payload = {
        "status": "REAL_MEMORY_SHADOW_PREVIEW",
        "phase": "PHASE_2_GRAVITY_SHADOW",
        "population_diagnostics": diagnostics,
        "sample": sample,
        "writes_performed": [],
        "relations_mutated": [],
        "gravity_rows_mutated": [],
        "retrieval_weighting_enabled": False,
        "review_questions": [
            "Do higher shadow scores correspond to memories Naomi considers more broadly useful or important?",
            "Is any relation-rich but low-value memory being inflated by graph density?",
            "Is any isolated but important memory being underweighted because it lacks graph coverage?",
            "Do contradiction/revision edges deserve the amount of shadow influence they currently receive?",
        ],
        "proof_boundary": (
            "This endpoint only observes existing durable non-test memories and VERIFIED relations. "
            "It does not create, verify, weaken, or remove relations; it does not write gravity; "
            "it does not alter retrieval. Real-memory calibration remains a Naomi-reviewed shadow exercise."
        ),
    }
    response = HTMLResponse(
        "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
        "<h1>GALAXY Phase 2 real-memory shadow calibration</h1>"
        f"<pre style='white-space:pre-wrap'>{html.escape(json.dumps(payload, indent=2))}</pre>"
        "<p>No action button is provided here intentionally. Review comes before any mutation.</p>"
        "</body></html>"
    )
    if bootstrap_session:
        response.set_cookie(
            SESSION_COOKIE, _session_token(), httponly=True, samesite="lax",
            secure=True, max_age=86400
        )
    return response



GALAXY_REAL_INVENTORY_LIMIT = 12


def _galaxy_real_candidate_inventory(memcon_runtime, limit: int) -> dict:
    """Inspect latent non-test MemoryOS material without creating or promoting anything."""
    memcon_runtime.initialize()
    limit = max(1, min(int(limit), GALAXY_REAL_INVENTORY_LIMIT))
    with memcon_runtime._db() as conn:
        candidate_rows = memcon_runtime._fetchall_dicts(
            conn,
            """SELECT c.*, e.session_id, e.actor, e.event_type, e.created_at AS event_created_at,
                      s.subject
               FROM memory_candidates c
               JOIN session_events e ON e.event_id = c.event_id
               JOIN sessions s ON s.session_id = e.session_id
               WHERE upper(c.record_type) <> 'TEST'
                 AND c.scope='MemoryOS'
                 AND c.source NOT LIKE 'galaxy-phase1-canary:%'
                 AND c.source NOT LIKE 'galaxy-phase2-calibration:%'
               ORDER BY c.created_at DESC""",
        )
        event_rows = memcon_runtime._fetchall_dicts(
            conn,
            """SELECT e.*, s.subject
               FROM session_events e
               JOIN sessions s ON s.session_id = e.session_id
               WHERE e.source NOT LIKE 'galaxy-phase1-canary:%'
                 AND e.source NOT LIKE 'galaxy-phase2-calibration:%'
               ORDER BY e.created_at DESC""",
        )
        linked_event_rows = memcon_runtime._fetchall_dicts(
            conn,
            """SELECT event_id FROM memory_candidates
               WHERE upper(record_type) <> 'TEST'
                 AND scope='MemoryOS'
                 AND source NOT LIKE 'galaxy-phase1-canary:%'
                 AND source NOT LIKE 'galaxy-phase2-calibration:%'""",
        )

    linked_event_ids = {str(row["event_id"]) for row in linked_event_rows}
    unrepresented_events = [
        event for event in event_rows
        if str(event.get("event_id")) not in linked_event_ids
    ]
    pending_candidates = [
        row for row in candidate_rows
        if str(row.get("status") or "") == "CANDIDATE"
    ]
    already_promoted = [
        row for row in candidate_rows
        if str(row.get("status") or "") != "CANDIDATE"
    ]

    def candidate_view(row: dict) -> dict:
        other_voices = []
        try:
            other_voices = json.loads(str(row.get("other_voices") or "[]"))
        except (TypeError, json.JSONDecodeError):
            other_voices = []
        return {
            "candidate_id": row.get("candidate_id"),
            "event_id": row.get("event_id"),
            "session_id": row.get("session_id"),
            "subject": row.get("subject"),
            "actor": row.get("actor"),
            "event_type": row.get("event_type"),
            "authority": row.get("authority"),
            "record_type": row.get("record_type"),
            "scope": row.get("scope"),
            "statement": row.get("statement"),
            "source": row.get("source"),
            "owner": row.get("owner"),
            "why_material": row.get("why_material"),
            "other_voices": other_voices,
            "tension": row.get("tension"),
            "status": row.get("status"),
            "duplicate_of": row.get("duplicate_of"),
            "promoted_record_id": row.get("promoted_record_id"),
            "created_at": row.get("created_at"),
        }

    def event_view(row: dict) -> dict:
        return {
            "event_id": row.get("event_id"),
            "session_id": row.get("session_id"),
            "subject": row.get("subject"),
            "actor": row.get("actor"),
            "event_type": row.get("event_type"),
            "statement": row.get("statement"),
            "source": row.get("source"),
            "relation": row.get("relation"),
            "created_at": row.get("created_at"),
        }

    return {
        "non_test_memoryos_candidate_count": len(candidate_rows),
        "pending_non_test_candidate_count": len(pending_candidates),
        "already_nonpending_candidate_count": len(already_promoted),
        "non_test_session_event_count": len(event_rows),
        "session_events_without_non_test_memoryos_candidate_count": len(unrepresented_events),
        "pending_candidates": [candidate_view(row) for row in pending_candidates[:limit]],
        "recent_unrepresented_session_events": [event_view(row) for row in unrepresented_events[:limit]],
        "diagnostic": (
            "LATENT_MEMORY_CANDIDATES_AVAILABLE"
            if pending_candidates
            else (
                "UNREPRESENTED_SESSION_EVENTS_AVAILABLE"
                if unrepresented_events
                else "NO_LATENT_REAL_MEMORY_MATERIAL_FOUND"
            )
        ),
    }


@app.get("/galaxy/gravity/real-calibration/inventory", response_class=HTMLResponse)
def galaxy_gravity_real_calibration_inventory(
    browser_request: Request,
    limit: int = GALAXY_REAL_INVENTORY_LIMIT,
):
    """Read-only inventory of latent real-memory material already inside MemconOS."""
    bootstrap_session = API_KEY is not None and not browser_request.cookies.get(SESSION_COOKIE)
    if not bootstrap_session:
        _authorize_browser_session(browser_request)
    memcon_runtime, _ = _galaxy_runtime()
    inventory = _galaxy_real_candidate_inventory(memcon_runtime, limit)
    payload = {
        "status": "REAL_MEMORY_LATENT_INVENTORY",
        "phase": "PHASE_2_GRAVITY_SHADOW",
        "inventory": inventory,
        "writes_performed": [],
        "candidates_promoted": [],
        "relations_mutated": [],
        "gravity_rows_mutated": [],
        "retrieval_weighting_enabled": False,
        "next_step_interpretation": {
            "LATENT_MEMORY_CANDIDATES_AVAILABLE": (
                "Existing non-test MemoryOS candidates are available for Naomi review. "
                "Do not auto-promote them."
            ),
            "UNREPRESENTED_SESSION_EVENTS_AVAILABLE": (
                "MemconOS contains non-test session events that have not yet become MemoryOS candidates. "
                "A separate candidate-creation review surface should be built before any durable promotion."
            ),
            "NO_LATENT_REAL_MEMORY_MATERIAL_FOUND": (
                "No eligible non-test candidates or session events are currently available in MemconOS. "
                "Real-memory calibration must wait for real memory ingestion or an explicitly supplied source."
            ),
        }.get(inventory["diagnostic"]),
        "proof_boundary": (
            "Inventory only. This endpoint does not create candidates, promote memory, create or verify relations, "
            "write gravity, or alter retrieval."
        ),
    }
    response = HTMLResponse(
        "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
        "<h1>GALAXY Phase 2 latent real-memory inventory</h1>"
        f"<pre style='white-space:pre-wrap'>{html.escape(json.dumps(payload, indent=2))}</pre>"
        "<p>No action button is exposed. The inventory determines the next safe ingestion step.</p>"
        "</body></html>"
    )
    if bootstrap_session:
        response.set_cookie(
            SESSION_COOKIE, _session_token(), httponly=True, samesite="lax",
            secure=True, max_age=86400
        )
    return response



def _galaxy_real_event_review(event: dict) -> dict:
    """Classify latent session events for human review without creating candidates."""
    event_type = str(event.get("event_type") or "")
    source = str(event.get("source") or "")
    statement = str(event.get("statement") or "")
    event_type_upper = event_type.upper()
    source_lower = source.lower()
    statement_lower = statement.lower()

    hard_test_flags = []
    soft_review_flags = []
    if "TEST" in event_type_upper:
        hard_test_flags.append("EVENT_TYPE_IS_TEST")
    if "test" in source_lower or "canary" in source_lower:
        hard_test_flags.append("SOURCE_IS_TEST_OR_CANARY")
    if source_lower.startswith("galaxy-phase"):
        hard_test_flags.append("SOURCE_IS_GALAXY_CONTROLLED_TEST")
    if "test" in statement_lower:
        soft_review_flags.append("STATEMENT_MENTIONS_TEST")
    if "pw:preserve" in statement_lower:
        soft_review_flags.append("PW_PRESERVE_CONTEXT")

    calibration_hold_flags = []
    if "STATEMENT_MENTIONS_TEST" in soft_review_flags and "PW_PRESERVE_CONTEXT" in soft_review_flags:
        calibration_hold_flags.append("CONTROL_COMMAND_TEST_CONTEXT")

    if hard_test_flags:
        disposition = "TEST_LIKE_HOLD"
        candidate_creation_allowed = False
        reason = (
            "Event is structurally test-like by event type or source and is held out of real-memory "
            "candidate creation unless the ingestion policy is deliberately changed."
        )
    elif calibration_hold_flags:
        disposition = "CALIBRATION_SUITABILITY_HOLD"
        candidate_creation_allowed = False
        reason = (
            "Event is a real browser interaction but its content is itself a control-command test. "
            "It is held out of the real-memory calibration sample so test context is not relabeled as "
            "representative semantic memory merely to create coverage."
        )
    else:
        disposition = "NAOMI_REVIEW_REQUIRED"
        candidate_creation_allowed = True
        reason = (
            "Event is not structurally classified as test data and is not held by the current calibration "
            "suitability filter. Candidate creation is available only as an explicit Naomi action and remains non-durable."
        )

    return {
        "event": event,
        "disposition": disposition,
        "candidate_creation_allowed": candidate_creation_allowed,
        "hard_test_flags": hard_test_flags,
        "soft_review_flags": soft_review_flags,
        "calibration_hold_flags": calibration_hold_flags,
        "reason": reason,
    }


def _galaxy_event_existing_candidate(memcon_runtime, event_id: str) -> dict | None:
    memcon_runtime.initialize()
    with memcon_runtime._db() as conn:
        row = memcon_runtime._fetchone_dict(
            conn,
            """SELECT * FROM memory_candidates
               WHERE event_id=? AND scope='MemoryOS'
               ORDER BY created_at DESC LIMIT 1""",
            (event_id,),
        )
    if row is None:
        return None
    try:
        row["other_voices"] = json.loads(str(row.get("other_voices") or "[]"))
    except (TypeError, json.JSONDecodeError):
        row["other_voices"] = []
    return row


@app.get("/galaxy/gravity/real-calibration/candidate-review", response_class=HTMLResponse)
def galaxy_gravity_real_candidate_review(
    browser_request: Request,
    limit: int = GALAXY_REAL_INVENTORY_LIMIT,
):
    """Review latent session events before any candidate creation."""
    from urllib.parse import urlencode

    bootstrap_session = API_KEY is not None and not browser_request.cookies.get(SESSION_COOKIE)
    if not bootstrap_session:
        _authorize_browser_session(browser_request)
    memcon_runtime, _ = _galaxy_runtime()
    inventory = _galaxy_real_candidate_inventory(memcon_runtime, limit)
    reviews = [
        _galaxy_real_event_review(event)
        for event in inventory["recent_unrepresented_session_events"]
    ]

    eligible = [item for item in reviews if item["candidate_creation_allowed"]]
    held = [item for item in reviews if not item["candidate_creation_allowed"]]
    payload = {
        "status": "REAL_MEMORY_CANDIDATE_REVIEW",
        "phase": "PHASE_2_GRAVITY_SHADOW",
        "reviewed_event_count": len(reviews),
        "candidate_creation_options_count": len(eligible),
        "held_event_count": len(held),
        "structural_test_hold_count": sum(1 for item in held if item["disposition"] == "TEST_LIKE_HOLD"),
        "calibration_suitability_hold_count": sum(1 for item in held if item["disposition"] == "CALIBRATION_SUITABILITY_HOLD"),
        "candidate_creation_options": eligible,
        "held_events": held,
        "writes_performed": [],
        "candidates_created": [],
        "candidates_promoted": [],
        "relations_mutated": [],
        "gravity_rows_mutated": [],
        "retrieval_weighting_enabled": False,
        "review_boundary": (
            "This page classifies existing session events for Naomi review. Structural test events and real interactions "
            "whose content is itself control-test context can be held out of calibration. A reviewable event can become "
            "only a non-durable MemoryOS candidate after a separate explicit click."
        ),
    }

    links = []
    for item in eligible:
        event = item["event"]
        event_id = str(event.get("event_id") or "")
        href = "/galaxy/gravity/real-calibration/candidate-create?" + urlencode({"event_id": event_id})
        links.append(
            "<li><a href='" + html.escape(href, quote=True) + "'>"
            + html.escape(f"Create non-durable candidate from {event_id}")
            + "</a></li>"
        )
    actions = (
        "<h2>Explicit candidate-creation options</h2><ul>" + "".join(links) + "</ul>"
        if links else
        "<p>No event currently passes the structural test-data hold for candidate creation.</p>"
    )
    response = HTMLResponse(
        "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
        "<h1>GALAXY real-memory candidate review</h1>"
        f"<pre style='white-space:pre-wrap'>{html.escape(json.dumps(payload, indent=2))}</pre>"
        + actions +
        "<p>No durable promotion occurs on this page or by candidate creation.</p>"
        "</body></html>"
    )
    if bootstrap_session:
        response.set_cookie(
            SESSION_COOKIE, _session_token(), httponly=True, samesite="lax",
            secure=True, max_age=86400
        )
    return response


@app.get("/galaxy/gravity/real-calibration/candidate-create", response_class=HTMLResponse)
def galaxy_gravity_real_candidate_create(browser_request: Request, event_id: str):
    """Explicitly create one non-durable real-memory candidate from a reviewed event."""
    _authorize_browser_session(browser_request)
    memcon_runtime, runtime = _galaxy_runtime()
    event = memcon_runtime.get_session_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Unknown session event.")

    existing = _galaxy_event_existing_candidate(memcon_runtime, event_id)
    if existing is not None:
        payload = {
            "status": "CANDIDATE_ALREADY_EXISTS",
            "event_id": event_id,
            "candidate": existing,
            "idempotent": True,
            "durable_memory_write_performed": False,
            "candidate_promotion_performed": False,
            "retrieval_weighting_enabled": False,
        }
        return HTMLResponse(
            "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
            "<h1>GALAXY real-memory candidate creation</h1>"
            f"<pre style='white-space:pre-wrap'>{html.escape(json.dumps(payload, indent=2))}</pre>"
            "<p>An existing candidate already represents this event. No duplicate was created.</p>"
            "</body></html>"
        )

    review = _galaxy_real_event_review({
        "event_id": event.get("event_id"),
        "session_id": event.get("session_id"),
        "subject": "",
        "actor": event.get("actor"),
        "event_type": event.get("event_type"),
        "statement": event.get("statement"),
        "source": event.get("source"),
        "relation": event.get("relation"),
        "created_at": event.get("created_at"),
    })
    if not review["candidate_creation_allowed"]:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Structurally test-like event is held out of real-memory candidate creation.",
                "hard_test_flags": review["hard_test_flags"],
            },
        )

    candidate = runtime.candidate_from_event(
        event_id,
        authority="NAOMI",
        record_type="INTERACTION",
        scope="MemoryOS",
        statement=str(event.get("statement") or ""),
        source=str(event.get("source") or ""),
        owner="NAOMI_REAL_MEMORY_REVIEW",
        why_material=(
            "Naomi explicitly selected this existing MemconOS session event for bounded real-memory "
            "calibration review. Candidate creation is non-durable and does not imply promotion."
        ),
        other_voices=[],
        tension="Candidate requires separate Naomi review before any durable promotion.",
    )
    payload = {
        "status": "REAL_MEMORY_CANDIDATE_CREATED",
        "phase": "PHASE_2_GRAVITY_SHADOW",
        "source_event_review": review,
        "candidate": candidate,
        "durable_memory_write_performed": False,
        "candidate_promotion_performed": False,
        "relations_mutated": [],
        "gravity_rows_mutated": [],
        "retrieval_weighting_enabled": False,
        "next_step": (
            "Inspect this exact candidate. No promotion control is exposed yet; durable promotion requires "
            "a separate explicit Naomi-reviewed gate."
        ),
    }
    return HTMLResponse(
        "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
        "<h1>GALAXY real-memory candidate creation</h1>"
        f"<pre style='white-space:pre-wrap'>{html.escape(json.dumps(payload, indent=2))}</pre>"
        "<p>Candidate created only. It is not durable memory and has no GALAXY gravity or retrieval effect.</p>"
        "</body></html>"
    )



@app.get("/galaxy/gravity/real-calibration/seed", response_class=HTMLResponse)
def galaxy_gravity_real_seed_form(browser_request: Request):
    """Render an explicit Naomi-authored real-memory seed intake. No mutation."""
    bootstrap_session = API_KEY is not None and not browser_request.cookies.get(SESSION_COOKIE)
    if not bootstrap_session:
        _authorize_browser_session(browser_request)

    body = """
    <html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee;max-width:900px'>
    <h1>GALAXY Phase 2 real-memory seed intake</h1>
    <p>Use this only for a real semantic memory you want represented in MemoryOS calibration.
    Submission creates a <strong>non-durable candidate only</strong>. It does not promote memory,
    create relations, write gravity, or change retrieval.</p>
    <form method='get' action='/galaxy/gravity/real-calibration/seed/create'>
      <label>Memory statement</label><br/>
      <textarea name='statement' rows='5' maxlength='4000' required
        style='width:100%;font-size:17px;margin:8px 0 18px 0'></textarea>
      <label>Why this memory matters for future context</label><br/>
      <textarea name='why_material' rows='3' maxlength='1200' required
        style='width:100%;font-size:17px;margin:8px 0 18px 0'></textarea>
      <label>Optional subject</label><br/>
      <input name='subject' maxlength='300' style='width:100%;font-size:17px;margin:8px 0 18px 0'/>
      <button type='submit' style='font-size:20px;padding:10px 16px'>Create non-durable calibration candidate</button>
    </form>
    <p style='margin-top:24px'>Do not use synthetic canaries or control-test markers here. The goal is representative real memory.</p>
    </body></html>
    """
    response = HTMLResponse(body)
    if bootstrap_session:
        response.set_cookie(
            SESSION_COOKIE, _session_token(), httponly=True, samesite="lax",
            secure=True, max_age=86400
        )
    return response


@app.get("/galaxy/gravity/real-calibration/seed/create", response_class=HTMLResponse)
def galaxy_gravity_real_seed_create(
    browser_request: Request,
    statement: str,
    why_material: str,
    subject: str = "",
):
    """Create one explicit Naomi-authored non-durable MemoryOS seed candidate."""
    _authorize_browser_session(browser_request)
    memcon_runtime, runtime = _galaxy_runtime()

    statement = statement.strip()
    why_material = why_material.strip()
    subject = subject.strip()
    if not statement:
        raise HTTPException(status_code=400, detail="Memory statement must not be empty.")
    if not why_material:
        raise HTTPException(status_code=400, detail="why_material must not be empty.")
    if len(statement) > 4000 or len(why_material) > 1200 or len(subject) > 300:
        raise HTTPException(status_code=400, detail="Seed fields exceed bounded calibration limits.")

    token = secrets.token_hex(6)
    source = f"galaxy-real-seed:{token}"
    session = runtime.start_session(
        source,
        subject or f"GALAXY Phase 2 real-memory seed {token}",
    )
    event = runtime.record_event(
        session["session_id"],
        "NAOMI",
        "REAL_MEMORY_SEED_INPUT",
        statement,
        source,
    )
    candidate = runtime.candidate_from_event(
        event["event_id"],
        authority="NAOMI",
        record_type="INTERACTION",
        scope="MemoryOS",
        statement=statement,
        source=source,
        owner="NAOMI_REAL_MEMORY_SEED",
        why_material=why_material,
        other_voices=[],
        tension="Explicit calibration seed; requires separate Naomi review before durable promotion.",
    )
    payload = {
        "status": "REAL_MEMORY_SEED_CANDIDATE_CREATED",
        "phase": "PHASE_2_GRAVITY_SHADOW",
        "session": session,
        "event": event,
        "candidate": candidate,
        "durable_memory_write_performed": False,
        "candidate_promotion_performed": False,
        "relations_mutated": [],
        "gravity_rows_mutated": [],
        "retrieval_weighting_enabled": False,
        "authority_boundary": (
            "Naomi authored this seed explicitly. It is only a non-durable MemoryOS candidate. "
            "Durable promotion, graph relation creation, gravity scoring, and retrieval weighting remain separate gates."
        ),
    }
    return HTMLResponse(
        "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee;max-width:900px'>"
        "<h1>GALAXY real-memory seed candidate</h1>"
        f"<pre style='white-space:pre-wrap'>{html.escape(json.dumps(payload, indent=2))}</pre>"
        "<p><a style='font-size:20px' href='/galaxy/gravity/real-calibration/seed/promote-review?candidate_id="
        + html.escape(str(candidate["candidate_id"]), quote=True)
        + "'>Review this exact candidate for durable promotion</a></p>"
        "<p><a style='font-size:20px' href='/galaxy/gravity/real-calibration/seed'>Add another real-memory seed</a></p>"
        "<p><a style='font-size:20px' href='/galaxy/gravity/real-calibration/inventory'>Inspect latent candidate inventory</a></p>"
        "<p>Promotion remains a separate Naomi-authorized gate.</p>"
        "</body></html>"
    )



def _galaxy_real_seed_candidate(memcon_runtime, candidate_id: str) -> dict:
    candidate = memcon_runtime.get_memory_candidate(candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Unknown real-memory seed candidate.")
    if str(candidate.get("owner") or "") != "NAOMI_REAL_MEMORY_SEED":
        raise HTTPException(status_code=409, detail="Candidate is not owned by the explicit real-memory seed lane.")
    if str(candidate.get("scope") or "") != "MemoryOS":
        raise HTTPException(status_code=409, detail="Candidate is outside MemoryOS.")
    if not str(candidate.get("source") or "").startswith("galaxy-real-seed:"):
        raise HTTPException(status_code=409, detail="Candidate source is not an explicit GALAXY real-memory seed.")
    return candidate


@app.get("/galaxy/gravity/real-calibration/seed/promote-review", response_class=HTMLResponse)
def galaxy_gravity_real_seed_promote_review(browser_request: Request, candidate_id: str):
    """Read one exact seed candidate before any durable promotion."""
    from urllib.parse import urlencode

    bootstrap_session = API_KEY is not None and not browser_request.cookies.get(SESSION_COOKIE)
    if not bootstrap_session:
        _authorize_browser_session(browser_request)
    memcon_runtime, _ = _galaxy_runtime()
    candidate = _galaxy_real_seed_candidate(memcon_runtime, candidate_id)
    event = memcon_runtime.get_session_event(str(candidate.get("event_id") or ""))
    promoted_record_id = candidate.get("promoted_record_id")
    durable_record = (
        memcon_runtime.get_record(str(promoted_record_id))
        if promoted_record_id else None
    )
    promotable = str(candidate.get("status") or "") == "CANDIDATE" and not promoted_record_id
    payload = {
        "status": "REAL_MEMORY_SEED_PROMOTION_REVIEW",
        "phase": "PHASE_2_GRAVITY_SHADOW",
        "candidate": candidate,
        "source_event": event,
        "already_durable_record": durable_record,
        "promotion_available": promotable,
        "writes_performed": [],
        "relations_mutated": [],
        "gravity_rows_mutated": [],
        "retrieval_weighting_enabled": False,
        "review_boundary": (
            "This page reads the exact candidate only. Durable promotion requires the separate explicit Naomi click below. "
            "Promotion does not authorize relation creation, gravity scoring, or retrieval weighting."
        ),
    }
    if promotable:
        promote_url = "/galaxy/gravity/real-calibration/seed/promote?" + urlencode({"candidate_id": candidate_id})
        action = (
            "<p><a style='font-size:22px' href='" + html.escape(promote_url, quote=True) + "'>"
            "Approve durable promotion of this exact candidate</a></p>"
        )
    else:
        action = "<p>This candidate is not pending promotion.</p>"
    response = HTMLResponse(
        "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee;max-width:1000px'>"
        "<h1>GALAXY real-memory durable-promotion review</h1>"
        f"<pre style='white-space:pre-wrap'>{html.escape(json.dumps(payload, indent=2))}</pre>"
        + action +
        "<p>No relation or gravity action is coupled to promotion.</p>"
        "</body></html>"
    )
    if bootstrap_session:
        response.set_cookie(
            SESSION_COOKIE, _session_token(), httponly=True, samesite="lax",
            secure=True, max_age=86400
        )
    return response


@app.get("/galaxy/gravity/real-calibration/seed/promote", response_class=HTMLResponse)
def galaxy_gravity_real_seed_promote(browser_request: Request, candidate_id: str):
    """Explicitly promote one exact seed candidate to durable MemoryOS."""
    _authorize_browser_session(browser_request)
    memcon_runtime, runtime = _galaxy_runtime()
    candidate = _galaxy_real_seed_candidate(memcon_runtime, candidate_id)

    existing_record_id = candidate.get("promoted_record_id")
    if str(candidate.get("status") or "") != "CANDIDATE" and existing_record_id:
        record = memcon_runtime.get_record(str(existing_record_id))
        payload = {
            "status": "REAL_MEMORY_SEED_ALREADY_DURABLE",
            "phase": "PHASE_2_GRAVITY_SHADOW",
            "candidate_id": candidate_id,
            "record": record,
            "idempotent": True,
            "new_write_receipt": None,
            "relations_mutated": [],
            "gravity_rows_mutated": [],
            "retrieval_weighting_enabled": False,
        }
        return HTMLResponse(
            "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee;max-width:1000px'>"
            "<h1>GALAXY real-memory durable promotion</h1>"
            f"<pre style='white-space:pre-wrap'>{html.escape(json.dumps(payload, indent=2))}</pre>"
            "<p>The candidate was already durable. No new mutation occurred.</p>"
            "</body></html>"
        )

    if str(candidate.get("status") or "") != "CANDIDATE":
        raise HTTPException(
            status_code=409,
            detail=f"Candidate is not promotable from status {candidate.get('status')}.",
        )

    result = runtime.promote_candidate(candidate_id, True, "NAOMI")
    if result.get("status") != "VERIFIED":
        raise HTTPException(status_code=409, detail={"message": "Durable promotion did not verify.", "result": result})

    record_id = str(result["record_id"])
    record = memcon_runtime.get_record(record_id)
    payload = {
        "status": "REAL_MEMORY_SEED_DURABLE_VERIFIED",
        "phase": "PHASE_2_GRAVITY_SHADOW",
        "candidate_id": candidate_id,
        "promotion": result,
        "record_readback": record,
        "relations_mutated": [],
        "gravity_rows_mutated": [],
        "retrieval_weighting_enabled": False,
        "authority_boundary": (
            "Only this exact Naomi-reviewed seed candidate was promoted to durable MemoryOS. "
            "No GALAXY relation was created or verified, no gravity was written, and retrieval remains unweighted."
        ),
    }
    return HTMLResponse(
        "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee;max-width:1000px'>"
        "<h1>GALAXY real-memory durable promotion</h1>"
        f"<pre style='white-space:pre-wrap'>{html.escape(json.dumps(payload, indent=2))}</pre>"
        "<p><a style='font-size:20px' href='/galaxy/gravity/real-calibration/preview'>Re-run real-memory shadow calibration preview</a></p>"
        "<p>Do not infer calibration quality yet. One durable real memory is only the first population point.</p>"
        "</body></html>"
    )


GALAXY_REAL_RELATION_CLASSIFIER = "GALAXY_REAL_CALIBRATION_V1"


def _galaxy_real_relation_endpoint(memcon_runtime, record_id: str) -> dict:
    """Require one durable non-test MemoryOS endpoint for real calibration."""
    record = memcon_runtime.get_record(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown durable record: {record_id}")
    if str(record.get("scope") or "") != "MemoryOS":
        raise HTTPException(status_code=409, detail=f"Record {record_id} is outside MemoryOS.")
    if str(record.get("record_type") or "").upper() == "TEST":
        raise HTTPException(status_code=409, detail=f"Record {record_id} is test material and cannot enter real calibration.")
    source = str(record.get("source") or "")
    if source.startswith("galaxy-phase1-canary:") or source.startswith("galaxy-phase2-calibration:"):
        raise HTTPException(status_code=409, detail=f"Record {record_id} is synthetic calibration material.")
    if str(record.get("authority") or "") != "NAOMI":
        raise HTTPException(status_code=409, detail=f"Record {record_id} is outside the Naomi-authorized real-memory lane.")
    return record


def _galaxy_real_matching_relation(memcon_runtime, source_record_id: str, target_record_id: str, relation_type: str):
    orbit = memcon_runtime.galaxy_record(source_record_id) or {}
    for edge in orbit.get("relations", []):
        if (
            str(edge.get("source_record_id")) == source_record_id
            and str(edge.get("target_record_id")) == target_record_id
            and str(edge.get("relation_type") or "").upper() == relation_type.upper()
            and str(edge.get("status") or "") in {"PROPOSED", "VERIFIED"}
        ):
            return edge
    return None


def _galaxy_real_relation_spec(memcon_runtime, source_record_id: str, target_record_id: str,
                               relation_type: str, strength: float, basis: str) -> dict:
    source = _galaxy_real_relation_endpoint(memcon_runtime, source_record_id)
    target = _galaxy_real_relation_endpoint(memcon_runtime, target_record_id)
    relation_type = relation_type.strip().upper()
    if relation_type not in memcon_runtime.GALAXY_RELATION_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported GALAXY relation type: {relation_type}")
    if source_record_id == target_record_id:
        raise HTTPException(status_code=400, detail="A real-memory calibration relation cannot target itself.")
    try:
        strength = float(strength)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Relation strength must be numeric.") from exc
    if not 0.0 <= strength <= 1.0:
        raise HTTPException(status_code=400, detail="Relation strength must be between 0.0 and 1.0.")
    basis = basis.strip()
    if not basis:
        raise HTTPException(status_code=400, detail="A bounded human-readable relation basis is required.")
    if len(basis) > 1200:
        raise HTTPException(status_code=400, detail="Relation basis exceeds the 1200-character calibration limit.")
    return {
        "source": source,
        "target": target,
        "relation_type": relation_type,
        "strength": strength,
        "basis": basis,
    }


@app.get("/galaxy/gravity/real-calibration/relation/review", response_class=HTMLResponse)
def galaxy_gravity_real_relation_review(
    browser_request: Request,
    source_record_id: str,
    target_record_id: str,
    relation_type: str,
    strength: float,
    basis: str,
):
    """Read exact real-memory endpoints and proposed semantics before any edge write."""
    from urllib.parse import urlencode

    bootstrap_session = API_KEY is not None and not browser_request.cookies.get(SESSION_COOKIE)
    if not bootstrap_session:
        _authorize_browser_session(browser_request)
    memcon_runtime, _ = _galaxy_runtime()
    spec = _galaxy_real_relation_spec(
        memcon_runtime, source_record_id, target_record_id, relation_type, strength, basis
    )
    existing = _galaxy_real_matching_relation(
        memcon_runtime, source_record_id, target_record_id, spec["relation_type"]
    )
    proposal_available = existing is None
    payload = {
        "status": "REAL_MEMORY_RELATION_REVIEW",
        "phase": "PHASE_2_GRAVITY_SHADOW",
        "source_record": spec["source"],
        "target_record": spec["target"],
        "proposed_relation": {
            "source_record_id": source_record_id,
            "relation_type": spec["relation_type"],
            "target_record_id": target_record_id,
            "strength": spec["strength"],
            "basis": spec["basis"],
            "classifier": GALAXY_REAL_RELATION_CLASSIFIER,
        },
        "existing_matching_relation": existing,
        "proposal_available": proposal_available,
        "writes_performed": [],
        "relations_mutated": [],
        "gravity_rows_mutated": [],
        "retrieval_weighting_enabled": False,
        "review_boundary": (
            "This page is read-only. It validates the two real-memory endpoints and the exact proposed semantic edge. "
            "Creating a PROPOSED edge requires a separate Naomi click. PROPOSED is not VERIFIED, and neither state changes retrieval in Phase 2."
        ),
    }
    if proposal_available:
        href = "/galaxy/gravity/real-calibration/relation/propose?" + urlencode({
            "source_record_id": source_record_id,
            "target_record_id": target_record_id,
            "relation_type": spec["relation_type"],
            "strength": str(spec["strength"]),
            "basis": spec["basis"],
        })
        action = (
            "<p><a style='font-size:22px' href='" + html.escape(href, quote=True) + "'>"
            "Create this exact relation as PROPOSED</a></p>"
        )
    else:
        action = "<p>An equivalent PROPOSED or VERIFIED edge already exists. No proposal action is offered.</p>"
    response = HTMLResponse(
        "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee;max-width:1100px'>"
        "<h1>GALAXY real-memory relation review</h1>"
        f"<pre style='white-space:pre-wrap'>{html.escape(json.dumps(payload, indent=2))}</pre>"
        + action +
        "<p>Review is deliberately separate from proposal and verification.</p>"
        "</body></html>"
    )
    if bootstrap_session:
        response.set_cookie(
            SESSION_COOKIE, _session_token(), httponly=True, samesite="lax",
            secure=True, max_age=86400
        )
    return response


@app.get("/galaxy/gravity/real-calibration/relation/propose", response_class=HTMLResponse)
def galaxy_gravity_real_relation_propose(
    browser_request: Request,
    source_record_id: str,
    target_record_id: str,
    relation_type: str,
    strength: float,
    basis: str,
):
    """Explicitly write one PROPOSED real-calibration edge. No verification or gravity write."""
    from urllib.parse import urlencode

    _authorize_browser_session(browser_request)
    memcon_runtime, runtime = _galaxy_runtime()
    spec = _galaxy_real_relation_spec(
        memcon_runtime, source_record_id, target_record_id, relation_type, strength, basis
    )
    pre_ids = _galaxy_retrieval_ids(runtime, spec["source"])
    result = memcon_runtime.galaxy_propose_relation(
        source_record_id=source_record_id,
        target_record_id=target_record_id,
        relation_type=spec["relation_type"],
        strength=spec["strength"],
        evidence={
            "source": "galaxy-real-calibration",
            "basis": spec["basis"],
            "phase": "PHASE_2_GRAVITY_SHADOW",
            "naomi_reviewed_proposal": True,
            "pre_verification_retrieval_record_ids": pre_ids,
        },
        classifier=GALAXY_REAL_RELATION_CLASSIFIER,
    )
    relation = result.get("relation") or {}
    edge_id = str(relation.get("edge_id") or "")
    relation_status = str(relation.get("status") or "")
    payload = {
        "status": "REAL_MEMORY_RELATION_PROPOSED" if relation_status == "PROPOSED" else "REAL_MEMORY_RELATION_EXISTING",
        "phase": "PHASE_2_GRAVITY_SHADOW",
        "proposal_result": result,
        "pre_verification_retrieval_record_ids": pre_ids,
        "relation_verified": relation_status == "VERIFIED",
        "durable_memory_writes_performed": [],
        "gravity_rows_mutated": [],
        "retrieval_weighting_enabled": False,
        "authority_boundary": (
            "Only the exact reviewed edge may be written here. A PROPOSED relation is non-authoritative and has no retrieval effect. "
            "Verification remains a separate Naomi-authorized gate."
        ),
    }
    if edge_id and relation_status == "PROPOSED":
        href = "/galaxy/gravity/real-calibration/relation/verify-review?" + urlencode({"edge_id": edge_id})
        action = (
            "<p><a style='font-size:22px' href='" + html.escape(href, quote=True) + "'>"
            "Review this exact proposed edge for verification</a></p>"
        )
    else:
        action = "<p>No new verification action is required from this proposal response.</p>"
    return HTMLResponse(
        "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee;max-width:1100px'>"
        "<h1>GALAXY real-memory relation proposal</h1>"
        f"<pre style='white-space:pre-wrap'>{html.escape(json.dumps(payload, indent=2))}</pre>"
        + action +
        "<p>No gravity score is written and retrieval remains unweighted.</p>"
        "</body></html>"
    )


def _galaxy_real_calibration_edge(memcon_runtime, edge_id: str) -> dict:
    relation = memcon_runtime.galaxy_relation(edge_id)
    if relation is None:
        raise HTTPException(status_code=404, detail="Unknown GALAXY relation edge.")
    if str(relation.get("classifier") or "") != GALAXY_REAL_RELATION_CLASSIFIER:
        raise HTTPException(status_code=409, detail="Edge is outside the real-memory calibration classifier.")
    _galaxy_real_relation_endpoint(memcon_runtime, str(relation.get("source_record_id") or ""))
    _galaxy_real_relation_endpoint(memcon_runtime, str(relation.get("target_record_id") or ""))
    return relation


@app.get("/galaxy/gravity/real-calibration/relation/verify-review", response_class=HTMLResponse)
def galaxy_gravity_real_relation_verify_review(browser_request: Request, edge_id: str):
    """Read one exact proposed real-calibration edge before verification."""
    from urllib.parse import urlencode

    bootstrap_session = API_KEY is not None and not browser_request.cookies.get(SESSION_COOKIE)
    if not bootstrap_session:
        _authorize_browser_session(browser_request)
    memcon_runtime, _ = _galaxy_runtime()
    relation = _galaxy_real_calibration_edge(memcon_runtime, edge_id)
    source = memcon_runtime.get_record(str(relation["source_record_id"]))
    target = memcon_runtime.get_record(str(relation["target_record_id"]))
    verification_available = str(relation.get("status") or "") == "PROPOSED"
    payload = {
        "status": "REAL_MEMORY_RELATION_VERIFICATION_REVIEW",
        "phase": "PHASE_2_GRAVITY_SHADOW",
        "relation": relation,
        "source_record": source,
        "target_record": target,
        "verification_available": verification_available,
        "writes_performed": [],
        "relations_mutated": [],
        "gravity_rows_mutated": [],
        "retrieval_weighting_enabled": False,
        "review_boundary": (
            "This page reads one exact PROPOSED real-calibration edge. Verification requires a separate Naomi click. "
            "Verification does not write gravity and does not enable weighted retrieval."
        ),
    }
    if verification_available:
        href = "/galaxy/gravity/real-calibration/relation/verify?" + urlencode({"edge_id": edge_id})
        action = (
            "<p><a style='font-size:22px' href='" + html.escape(href, quote=True) + "'>"
            "Verify this exact real-memory relation</a></p>"
        )
    else:
        action = "<p>This edge is not pending verification.</p>"
    response = HTMLResponse(
        "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee;max-width:1100px'>"
        "<h1>GALAXY real-memory relation verification review</h1>"
        f"<pre style='white-space:pre-wrap'>{html.escape(json.dumps(payload, indent=2))}</pre>"
        + action +
        "<p>No gravity or retrieval action is coupled to verification review.</p>"
        "</body></html>"
    )
    if bootstrap_session:
        response.set_cookie(
            SESSION_COOKIE, _session_token(), httponly=True, samesite="lax",
            secure=True, max_age=86400
        )
    return response


@app.get("/galaxy/gravity/real-calibration/relation/verify", response_class=HTMLResponse)
def galaxy_gravity_real_relation_verify(browser_request: Request, edge_id: str):
    """Explicit Naomi verification of one exact real-memory calibration edge."""
    _authorize_browser_session(browser_request)
    memcon_runtime, runtime = _galaxy_runtime()
    before = _galaxy_real_calibration_edge(memcon_runtime, edge_id)
    source = memcon_runtime.get_record(str(before["source_record_id"]))
    target = memcon_runtime.get_record(str(before["target_record_id"]))
    pre_ids = list((before.get("evidence") or {}).get("pre_verification_retrieval_record_ids") or [])
    result = memcon_runtime.galaxy_verify_relation(edge_id, authority="NAOMI", approved=True)
    relation = result.get("relation") or memcon_runtime.galaxy_relation(edge_id)
    post_ids = _galaxy_retrieval_ids(runtime, source)
    source_orbit = memcon_runtime.galaxy_record(str(source["record_id"]))
    target_orbit = memcon_runtime.galaxy_record(str(target["record_id"]))
    source_preview = memcon_runtime.galaxy_gravity_preview(str(source["record_id"]))
    target_preview = memcon_runtime.galaxy_gravity_preview(str(target["record_id"]))
    payload = {
        "status": "REAL_MEMORY_RELATION_VERIFIED",
        "phase": "PHASE_2_GRAVITY_SHADOW",
        "verification": result,
        "relation_readback": relation,
        "source_orbit": source_orbit,
        "target_orbit": target_orbit,
        "source_shadow_preview": source_preview,
        "target_shadow_preview": target_preview,
        "retrieval_comparison": {
            "before_record_ids": pre_ids,
            "after_record_ids": post_ids,
            "unchanged": pre_ids == post_ids,
            "retrieval_weighting_enabled": False,
        },
        "durable_memory_writes_performed": [],
        "gravity_rows_mutated": [],
        "retrieval_weighting_enabled": False,
        "authority_boundary": (
            "Verification authorizes only this exact semantic edge. Gravity remains shadow-only and unstored here; "
            "ordinary retrieval remains unweighted."
        ),
    }
    return HTMLResponse(
        "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee;max-width:1100px'>"
        "<h1>GALAXY real-memory relation verification</h1>"
        f"<pre style='white-space:pre-wrap'>{html.escape(json.dumps(payload, indent=2))}</pre>"
        "<p><a style='font-size:20px' href='/galaxy/gravity/real-calibration/preview'>Re-run real-memory shadow calibration preview</a></p>"
        "<p>The verified edge may change shadow score previews because graph structure changed. It still does not change retrieval.</p>"
        "</body></html>"
    )


@app.get("/galaxy/gravity/real-calibration/uncertainty-review", response_class=HTMLResponse)
def galaxy_gravity_real_uncertainty_review(browser_request: Request, record_id: str):
    """Read-only Phase-2 counterfactual lens for an uncertain calibration judgment."""
    bootstrap_session = API_KEY is not None and not browser_request.cookies.get(SESSION_COOKIE)
    if not bootstrap_session:
        _authorize_browser_session(browser_request)
    memcon_runtime, _ = _galaxy_runtime()
    record = _galaxy_real_relation_endpoint(memcon_runtime, record_id)
    current = memcon_runtime.galaxy_gravity_preview(record_id)

    current_score = float(current["gravity_score"])
    base_without_explicit = round(current_score, 6)
    max_explicit_only = round(current_score + 0.05, 6)

    def one_relation_score(strength: float, *, revision: bool = False) -> float:
        # Counterfactual math only for a currently isolated ACTIVE/NAOMI record.
        # One relation adds degree contribution 0.25*(1/4), mean-strength 0.20*strength,
        # and a revision-like relation additionally adds 0.10*(1/2).
        score = 0.25 + 0.15 + (0.25 * 0.25) + (0.20 * strength)
        if revision:
            score += 0.10 * 0.5
        return round(score, 6)

    payload = {
        "status": "REAL_MEMORY_CALIBRATION_UNCERTAINTY_REVIEW",
        "phase": "PHASE_2_GRAVITY_SHADOW",
        "record": {
            "record_id": record.get("record_id"),
            "statement": record.get("statement"),
            "authority": record.get("authority"),
            "status": record.get("status"),
        },
        "current_shadow_preview": current,
        "counterfactual_math_only": {
            "current_score": base_without_explicit,
            "max_explicit_importance_only": {
                "hypothetical_explicit_importance_normalized": 1.0,
                "score": max_explicit_only,
                "note": "Uses the existing v1 explicit-importance weight of 0.05. No importance signal is written or activated.",
            },
            "one_nonrevision_relation": [
                {"strength": 0.50, "score": one_relation_score(0.50)},
                {"strength": 0.85, "score": one_relation_score(0.85)},
                {"strength": 1.00, "score": one_relation_score(1.00)},
            ],
            "one_revision_like_relation_at_0_85": {
                "score": one_relation_score(0.85, revision=True),
                "note": "Illustrates the current revision-significance weight only. No relation is proposed or written.",
            },
        },
        "interpretation_boundary": (
            "These are counterfactual arithmetic probes against the current shadow-v1 weights, not recommendations, "
            "semantic relation proposals, or evidence that any score is correct. They exist to make Naomi's uncertainty inspectable."
        ),
        "writes_performed": [],
        "relations_mutated": [],
        "gravity_rows_mutated": [],
        "retrieval_weighting_enabled": False,
    }
    response = HTMLResponse(
        "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee;max-width:1100px'>"
        "<h1>GALAXY Phase 2 calibration uncertainty review</h1>"
        f"<pre style='white-space:pre-wrap'>{html.escape(json.dumps(payload, indent=2))}</pre>"
        "<p>No action is offered here. This page changes nothing; it only exposes how strongly the current v1 weights respond to different inputs.</p>"
        "</body></html>"
    )
    if bootstrap_session:
        response.set_cookie(
            SESSION_COOKIE, _session_token(), httponly=True, samesite="lax",
            secure=True, max_age=86400
        )
    return response


@app.get("/galaxy/gravity/real-calibration/weight-options", response_class=HTMLResponse)
def galaxy_gravity_real_weight_options(browser_request: Request):
    """Read-only counterfactual weight families after Naomi rejects the current leverage ratio."""
    bootstrap_session = API_KEY is not None and not browser_request.cookies.get(SESSION_COOKIE)
    if not bootstrap_session:
        _authorize_browser_session(browser_request)
    memcon_runtime, _ = _galaxy_runtime()

    records, edges = _galaxy_real_memory_population(memcon_runtime)

    profiles = [
        {
            "name": "CURRENT_V1",
            "weights": {
                "durable_active": 0.25,
                "verified_graph_degree": 0.25,
                "verified_relation_strength": 0.20,
                "provenance_confidence": 0.15,
                "revision_significance": 0.10,
                "explicit_importance": 0.05,
            },
            "purpose": "Reference only; this is the currently deployed shadow-v1 formula.",
        },
        {
            "name": "SOFT_REBALANCE",
            "weights": {
                "durable_active": 0.25,
                "verified_graph_degree": 0.20,
                "verified_relation_strength": 0.15,
                "provenance_confidence": 0.15,
                "revision_significance": 0.10,
                "explicit_importance": 0.15,
            },
            "purpose": "Reduces graph leverage and gives explicit importance a material channel without making it dominant.",
        },
        {
            "name": "PARITY_AT_ONE_085_RELATION",
            "weights": {
                "durable_active": 0.25,
                "verified_graph_degree": 0.16129,
                "verified_relation_strength": 0.16129,
                "provenance_confidence": 0.15,
                "revision_significance": 0.10,
                "explicit_importance": 0.17742,
            },
            "purpose": "Constructed so one non-revision relation at strength 0.85 has approximately the same maximum contribution as explicit importance.",
        },
        {
            "name": "IMPORTANCE_LEADING",
            "weights": {
                "durable_active": 0.25,
                "verified_graph_degree": 0.15,
                "verified_relation_strength": 0.15,
                "provenance_confidence": 0.15,
                "revision_significance": 0.10,
                "explicit_importance": 0.20,
            },
            "purpose": "Makes maximum explicit importance stronger than one non-revision relation at strength 0.85.",
        },
    ]

    def normalized_for(record: dict) -> dict:
        record_id = str(record["record_id"])
        profile = _galaxy_real_relation_profile(record_id, edges)
        degree = int(profile["verified_relation_count"])
        significant = int(profile["revision_significance_edges"])
        return {
            "durable_active": 1.0 if str(record.get("status") or "").upper() == "ACTIVE" else 0.0,
            "verified_graph_degree": min(degree / 4.0, 1.0),
            "verified_relation_strength": float(profile["mean_verified_relation_strength"]),
            "provenance_confidence": 1.0 if str(record.get("authority") or "").upper() == "NAOMI" else 0.0,
            "revision_significance": min(significant / 2.0, 1.0),
            "explicit_importance": 0.0,
        }

    def score(weights: dict, normalized: dict) -> float:
        return round(sum(float(normalized[k]) * float(weights[k]) for k in weights), 6)

    comparisons = []
    for profile in profiles:
        weights = profile["weights"]
        one_relation_085 = round((weights["verified_graph_degree"] * 0.25) + (weights["verified_relation_strength"] * 0.85), 6)
        explicit_max = round(weights["explicit_importance"], 6)
        ratio = round(one_relation_085 / explicit_max, 6) if explicit_max > 0 else None
        rows = []
        for record in records:
            norm = normalized_for(record)
            baseline = score(weights, norm)
            important_norm = dict(norm)
            important_norm["explicit_importance"] = 1.0
            rows.append({
                "record_id": record.get("record_id"),
                "statement": record.get("statement"),
                "relation_profile": _galaxy_real_relation_profile(str(record["record_id"]), edges),
                "score_with_current_explicit_importance_signal": baseline,
                "score_if_explicit_importance_were_max": score(weights, important_norm),
            })
        comparisons.append({
            "name": profile["name"],
            "purpose": profile["purpose"],
            "weights": weights,
            "weight_sum": round(sum(weights.values()), 6),
            "one_nonrevision_relation_at_0_85_contribution": one_relation_085,
            "max_explicit_importance_contribution": explicit_max,
            "relation_to_explicit_max_ratio": ratio,
            "real_memory_counterfactuals": rows,
        })

    payload = {
        "status": "REAL_MEMORY_WEIGHT_OPTIONS_REVIEW",
        "phase": "PHASE_2_GRAVITY_SHADOW",
        "naomi_calibration_verdict": {
            "question": "Should one verified semantic relation be allowed to outweigh the entire explicit-importance signal by the current amount?",
            "answer": "NO",
            "resolved": "The current 4.65x relation-vs-explicit-importance leverage is not acceptable.",
            "unresolved": "The desired ratio and final weights remain undecided.",
        },
        "profiles": comparisons,
        "important_signal_warning": (
            "Changing the explicit-importance weight alone cannot help an isolated memory unless an explicit importance signal is separately defined and authorized. "
            "All currently stored real memories still have explicit_importance normalized to 0.0."
        ),
        "writes_performed": [],
        "relations_mutated": [],
        "gravity_rows_mutated": [],
        "retrieval_weighting_enabled": False,
        "selection_performed": False,
        "proof_boundary": (
            "This page performs arithmetic only. It does not change GALAXY_SCORE_VERSION, deployed weights, memory records, relations, gravity rows, or retrieval ordering."
        ),
    }
    response = HTMLResponse(
        "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee;max-width:1200px'>"
        "<h1>GALAXY Phase 2 counterfactual weight options</h1>"
        f"<pre style='white-space:pre-wrap'>{html.escape(json.dumps(payload, indent=2))}</pre>"
        "<p>No profile is selected here. Review comes before any formula revision.</p>"
        "</body></html>"
    )
    if bootstrap_session:
        response.set_cookie(
            SESSION_COOKIE, _session_token(), httponly=True, samesite="lax",
            secure=True, max_age=86400
        )
    return response


@app.get("/galaxy/gravity/real-calibration/importance-three-level", response_class=HTMLResponse)
def galaxy_gravity_real_importance_three_level(browser_request: Request, record_id: str):
    """Read-only semantics and score lens for Naomi's chosen three-level explicit-importance model."""
    bootstrap_session = API_KEY is not None and not browser_request.cookies.get(SESSION_COOKIE)
    if not bootstrap_session:
        _authorize_browser_session(browser_request)
    memcon_runtime, _ = _galaxy_runtime()
    record = _galaxy_real_relation_endpoint(memcon_runtime, record_id)
    current = memcon_runtime.galaxy_gravity_preview(record_id)

    levels = [
        {
            "value": 0.0,
            "label": "NORMAL",
            "meaning": "No explicit importance boost. The memory is governed by durability, provenance, graph structure, and revision signals only.",
        },
        {
            "value": 0.5,
            "label": "IMPORTANT",
            "meaning": "Naomi marks the memory as materially important for future context. This increases contextual influence but does not make the memory truth, authority, or permission.",
        },
        {
            "value": 1.0,
            "label": "FOUNDATIONAL",
            "meaning": "Naomi marks the memory as foundational context that should remain strongly available even when graph-isolated. This still does not override provenance, contradiction, revision, or Naomi's later changes.",
        },
    ]

    profiles = [
        {
            "name": "CURRENT_V1",
            "weights": {
                "durable_active": 0.25,
                "verified_graph_degree": 0.25,
                "verified_relation_strength": 0.20,
                "provenance_confidence": 0.15,
                "revision_significance": 0.10,
                "explicit_importance": 0.05,
            },
        },
        {
            "name": "SOFT_REBALANCE",
            "weights": {
                "durable_active": 0.25,
                "verified_graph_degree": 0.20,
                "verified_relation_strength": 0.15,
                "provenance_confidence": 0.15,
                "revision_significance": 0.10,
                "explicit_importance": 0.15,
            },
        },
        {
            "name": "PARITY_AT_ONE_085_RELATION",
            "weights": {
                "durable_active": 0.25,
                "verified_graph_degree": 0.16129,
                "verified_relation_strength": 0.16129,
                "provenance_confidence": 0.15,
                "revision_significance": 0.10,
                "explicit_importance": 0.17742,
            },
        },
        {
            "name": "IMPORTANCE_LEADING",
            "weights": {
                "durable_active": 0.25,
                "verified_graph_degree": 0.15,
                "verified_relation_strength": 0.15,
                "provenance_confidence": 0.15,
                "revision_significance": 0.10,
                "explicit_importance": 0.20,
            },
        },
    ]

    components = current["components"]
    normalized_base = {
        name: float(spec["normalized"])
        for name, spec in components.items()
    }

    def score(weights: dict, importance: float) -> float:
        norm = dict(normalized_base)
        norm["explicit_importance"] = importance
        return round(sum(float(norm[k]) * float(weights[k]) for k in weights), 6)

    comparisons = []
    for profile in profiles:
        comparisons.append({
            "name": profile["name"],
            "weights": profile["weights"],
            "scores_by_importance_level": [
                {
                    "value": level["value"],
                    "label": level["label"],
                    "score": score(profile["weights"], float(level["value"])),
                }
                for level in levels
            ],
        })

    payload = {
        "status": "REAL_MEMORY_THREE_LEVEL_IMPORTANCE_REVIEW",
        "phase": "PHASE_2_GRAVITY_SHADOW",
        "selected_model": "THREE_LEVEL",
        "record": {
            "record_id": record.get("record_id"),
            "statement": record.get("statement"),
            "authority": record.get("authority"),
            "status": record.get("status"),
        },
        "proposed_semantics": levels,
        "authorization_model": {
            "who_may_set": "NAOMI",
            "default": 0.0,
            "allowed_values": [0.0, 0.5, 1.0],
            "mutation_requires": "separate exact-record review and explicit Naomi approval",
            "later_revision_allowed": True,
            "importance_is_not": ["truth", "authority", "permission", "relation strength"],
        },
        "current_shadow_preview": current,
        "counterfactual_profile_scores": comparisons,
        "writes_performed": [],
        "importance_signal_mutated": False,
        "relations_mutated": [],
        "gravity_rows_mutated": [],
        "retrieval_weighting_enabled": False,
        "selection_performed": False,
        "proof_boundary": (
            "This page defines and compares the proposed three-level semantics only. "
            "It does not store an importance value, change deployed weights, write gravity, alter relations, or affect retrieval."
        ),
    }
    response = HTMLResponse(
        "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee;max-width:1200px'>"
        "<h1>GALAXY Phase 2 three-level explicit-importance review</h1>"
        f"<pre style='white-space:pre-wrap'>{html.escape(json.dumps(payload, indent=2))}</pre>"
        "<p>No importance value is set here. Review the meanings of NORMAL, IMPORTANT, and FOUNDATIONAL before any storage design is authorized.</p>"
        "</body></html>"
    )
    if bootstrap_session:
        response.set_cookie(
            SESSION_COOKIE, _session_token(), httponly=True, samesite="lax",
            secure=True, max_age=86400
        )
    return response


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
