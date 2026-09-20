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
