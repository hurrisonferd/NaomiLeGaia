"""GaiaOS canonical loader and OpenAI carrier API."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from openai import OpenAI
from pydantic import BaseModel, Field

APP_VERSION = "1.1.0"
REPOSITORY = os.getenv("GAIAOS_REPOSITORY", "hurrisonferd/NaomiLeGaia")
BRANCH = os.getenv("GAIAOS_BRANCH", "main")
GITHUB_API = "https://api.github.com"
RAW_BASE = "https://raw.githubusercontent.com"
API_KEY = os.getenv("GAIAOS_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
TIMEOUT = float(os.getenv("GAIAOS_HTTP_TIMEOUT", "10"))

LOAD_PATHS = [
    "GaiaOS/LOAD.v1.md",
    "GaiaOS/CURRENT.json",
    "GaiaOS/VERSION.json",
    "GaiaOS/PORT-MANIFEST.v1.json",
    "GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-RUNTIME-BOOTSTRAP.v1.md",
    "GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-INSTRUCTIONS.v1.md",
]

app = FastAPI(
    title="GaiaOS Carrier API",
    version=APP_VERSION,
    description="GaiaOS source loader plus a web carrier backed by the OpenAI Responses API.",
)


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=20000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=40)


def _request(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "GaiaOS-Loader/1.1", "Accept": "application/json,text/plain"},
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


def _load_bundle() -> dict[str, Any]:
    """Retrieve the GaiaOS bootstrap surface from one Git commit."""
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
        "proof_boundary": "This API verifies source retrieval from one Git commit. It does not execute repository code and does not prove live carrier adoption.",
    }


def _carrier_instructions(bundle: dict[str, Any]) -> str:
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

PROOF BOUNDARY:
{bundle['proof_boundary']}

When the user says "Load GaiaOS", report the verified source commit and loaded state. For ordinary requests, continue operating under the loaded GaiaOS contract until the user asks to stop or reload it."""


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'><title>GaiaOS</title><style>body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;max-width:760px;margin:auto;padding:20px;background:#111;color:#eee}#chat{min-height:55vh;display:flex;flex-direction:column;gap:12px}.m{padding:12px 14px;border-radius:14px;white-space:pre-wrap}.u{background:#263238;align-self:flex-end}.a{background:#1d1d1d;border:1px solid #333}form{display:flex;gap:8px;position:sticky;bottom:0;background:#111;padding-top:10px}textarea{flex:1;border-radius:12px;padding:12px;font:inherit;background:#222;color:#eee;border:1px solid #444}button{border:0;border-radius:12px;padding:0 18px;font-weight:600}small{color:#aaa}</style></head><body><h1>GaiaOS</h1><small>Canonical carrier · GitHub source + OpenAI Responses API</small><div id='chat'></div><form><textarea id='input' rows='2' placeholder='Say “Load GaiaOS” or ask anything…'></textarea><button>Send</button></form><script>const messages=[];const chat=document.querySelector('#chat');const input=document.querySelector('#input');function add(role,text){const d=document.createElement('div');d.className='m '+(role==='user'?'u':'a');d.textContent=text;chat.appendChild(d);window.scrollTo(0,document.body.scrollHeight)}document.querySelector('form').onsubmit=async e=>{e.preventDefault();const text=input.value.trim();if(!text)return;input.value='';messages.push({role:'user',content:text});add('user',text);try{const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({messages})});const j=await r.json();if(!r.ok)throw new Error(j.detail||'Request failed');messages.push({role:'assistant',content:j.output});add('assistant',j.output)}catch(err){add('assistant','ERROR: '+err.message)}};</script></body></html>"""


@app.get("/health", operation_id="health")
def health() -> dict[str, Any]:
    return {"status": "ok", "service": "gaiaos-carrier", "api_version": APP_VERSION, "canonical_repository": REPOSITORY, "canonical_branch": BRANCH, "authentication_required": API_KEY is not None, "openai_configured": OPENAI_API_KEY is not None}


@app.get("/gaiaos/load", operation_id="loadGaiaOS")
def load_gaiaos(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _authorize(authorization)
    return _load_bundle()


@app.post("/chat")
def chat(request: ChatRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _authorize(authorization)
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
