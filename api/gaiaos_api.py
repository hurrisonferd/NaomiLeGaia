"""GaiaOS canonical loader API.

This service is intentionally read-only. It resolves the canonical GaiaOS
repository to one Git commit, then returns the small set of source contracts
needed by a carrier to bootstrap GaiaOS.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from fastapi import FastAPI, Header, HTTPException

APP_VERSION = "1.0.0"
REPOSITORY = os.getenv("GAIAOS_REPOSITORY", "hurrisonferd/NaomiLeGaia")
BRANCH = os.getenv("GAIAOS_BRANCH", "main")
GITHUB_API = "https://api.github.com"
RAW_BASE = "https://raw.githubusercontent.com"
API_KEY = os.getenv("GAIAOS_API_KEY")
TIMEOUT = float(os.getenv("GAIAOS_HTTP_TIMEOUT", "10"))

# Deliberately allowlist the loader surface. The API is not a general GitHub proxy.
LOAD_PATHS = [
    "GaiaOS/LOAD.v1.md",
    "GaiaOS/CURRENT.json",
    "GaiaOS/VERSION.json",
    "GaiaOS/PORT-MANIFEST.v1.json",
    "GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-RUNTIME-BOOTSTRAP.v1.md",
    "GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-INSTRUCTIONS.v1.md",
]

app = FastAPI(
    title="GaiaOS Canonical Loader API",
    version=APP_VERSION,
    description=(
        "Read-only carrier bootstrap API for the canonical GaiaOS source in "
        "hurrisonferd/NaomiLeGaia."
    ),
)


def _request(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "GaiaOS-Loader/1.0", "Accept": "application/json,text/plain"},
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
    url = f"{GITHUB_API}/repos/{owner}/{repo}/commits/{BRANCH}"
    payload = json.loads(_request(url).decode("utf-8"))
    sha = payload.get("sha")
    if not isinstance(sha, str) or len(sha) < 40:
        raise HTTPException(status_code=502, detail="Canonical branch did not return a valid commit SHA")
    return sha


def _fetch_file(commit: str, path: str) -> str:
    if path not in LOAD_PATHS:
        raise HTTPException(status_code=400, detail="Path is not part of the canonical loader surface")
    url = f"{RAW_BASE}/{REPOSITORY}/{commit}/{path}"
    try:
        return _request(url).decode("utf-8")
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


@app.get("/health", operation_id="health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "gaiaos-loader",
        "api_version": APP_VERSION,
        "canonical_repository": REPOSITORY,
        "canonical_branch": BRANCH,
        "authentication_required": API_KEY is not None,
    }


@app.get("/gaiaos/load", operation_id="loadGaiaOS")
def load_gaiaos(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """Return a verified, single-commit GaiaOS bootstrap bundle."""
    _authorize(authorization)
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
        "canonical": {
            "repository": REPOSITORY,
            "branch": BRANCH,
            "commit": commit,
            "loader_surface": LOAD_PATHS,
        },
        "current": current,
        "version": version,
        "manifest": manifest,
        "loader": _fetch_file(commit, "GaiaOS/LOAD.v1.md"),
        "runtime_bootstrap": _fetch_file(
            commit, "GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-RUNTIME-BOOTSTRAP.v1.md"
        ),
        "host_instructions": _fetch_file(
            commit, "GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-INSTRUCTIONS.v1.md"
        ),
        "proof_boundary": (
            "This API verifies source retrieval from one Git commit. It does not "
            "execute repository code and does not prove live carrier adoption."
        ),
    }
