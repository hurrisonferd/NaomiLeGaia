"""Signed-browser bridge for shared Naomi-owned GaiaOS MemoryOS writes.

This adapter exposes no bearer credential. It reuses the existing signed browser
session, constrains writes to owner=NAOMI and GaiaOS:* scopes, requires an
explicit single-use SALT_CIRCLE for each effect, and delegates all persistence
to the existing host_memory_gateway / MemoryOS lifecycle.
"""
from __future__ import annotations

import json
import re

from fastapi import HTTPException, Request

import browser_memcon_bridge as legacy
import djinn_runtime
import gaiaos_api
import host_memory_gateway
import memcon_runtime

app = legacy.app
_original_browser_chat = legacy.browser_chat

_SHARED_TARGET = "MEMORYOS_SHARED_BROWSER"
_SHARED_SCOPE = re.compile(r"^GaiaOS:[A-Za-z0-9_.:-]{1,160}$")

# Replace only the POST /chat route so shared-memory commands can be handled
# before delegating every existing command back to the established bridge.
app.routes[:] = [
    route for route in app.routes
    if not (
        getattr(route, "path", None) == "/chat"
        and "POST" in getattr(route, "methods", set())
    )
]


def _command_payload(command: str, operation: str) -> dict:
    body = re.sub(
        rf"^\s*{re.escape(operation)}\s*",
        "",
        command,
        flags=re.IGNORECASE,
    ).strip()
    try:
        data = json.loads(body)
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(status_code=422, detail="Explicit JSON object required") from None
    if not isinstance(data, dict):
        raise HTTPException(status_code=422, detail="Explicit JSON object required")
    return data


def _shared_scope(value: object) -> str:
    if not isinstance(value, str) or not _SHARED_SCOPE.fullmatch(value):
        raise HTTPException(
            status_code=422,
            detail="Shared browser MemoryOS scope must be an exact GaiaOS:* scope",
        )
    return value


def _validate_circle(circle: object, *, operation: str, scope: str) -> dict:
    if not isinstance(circle, dict):
        raise HTTPException(status_code=422, detail="salt_circle object required")
    operation_id = circle.get("operation_id")
    if not isinstance(operation_id, str) or not operation_id:
        raise HTTPException(status_code=422, detail="salt_circle.operation_id required")
    try:
        validated = djinn_runtime.validate_salt_circle(
            circle,
            invocation_id=operation_id,
            consume=True,
        )
    except djinn_runtime.SaltCircleBreach as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None
    if operation not in validated["allowed_operations"]:
        raise HTTPException(status_code=403, detail="SALT_CIRCLE: BREACH_ATTEMPT:OPERATION")
    if _SHARED_TARGET not in validated["allowed_targets"]:
        raise HTTPException(status_code=403, detail="SALT_CIRCLE: BREACH_ATTEMPT:TARGET")
    if scope not in validated["allowed_scopes"]:
        raise HTTPException(status_code=403, detail="SALT_CIRCLE: BREACH_ATTEMPT:SCOPE")
    if (
        operation in validated["explicit_forbiddens"]
        or _SHARED_TARGET in validated["explicit_forbiddens"]
        or scope in validated["explicit_forbiddens"]
    ):
        raise HTTPException(status_code=403, detail="SALT_CIRCLE: BREACH_ATTEMPT:EXPLICIT_FORBIDDEN")
    return validated


def _ensure_browser_session(request: Request) -> str:
    gaiaos_api._authorize_browser_session(request)
    session_id = legacy._browser_session_id(request)
    if memcon_runtime.get_session(session_id) is None:
        memcon_runtime.create_session(
            session_id,
            "browser-shared-memory",
            "Shared Naomi-owned GaiaOS preservation",
        )
    return session_id


def _shared_candipull(command: str, request: Request) -> dict:
    data = _command_payload(command, "SHARED-CANDIPULL")
    required = {
        "owner",
        "scope",
        "statement",
        "source",
        "why_material",
        "record_type",
        "salt_circle",
    }
    if set(data) != required:
        raise HTTPException(
            status_code=422,
            detail="Exact owner, scope, statement, source, why_material, record_type and salt_circle required",
        )
    if data["owner"] != "NAOMI":
        raise HTTPException(status_code=403, detail="Shared browser MemoryOS owner must be NAOMI")
    if data["record_type"] != "INTERACTION":
        raise HTTPException(status_code=422, detail="Shared browser v1 accepts record_type INTERACTION only")
    scope = _shared_scope(data["scope"])
    session_id = _ensure_browser_session(request)
    _validate_circle(
        data["salt_circle"],
        operation="SHARED_CANDIPULL",
        scope=scope,
    )
    try:
        observation = host_memory_gateway.HostObservation(
            owner="NAOMI",
            scope=scope,
            statement=data["statement"],
            source=data["source"],
            why_material=data["why_material"],
            record_type="INTERACTION",
            other_voices=[],
        )
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid shared MemoryOS observation") from None
    result = host_memory_gateway._host_candipull(
        host_memory_gateway.HostCandidatePull(
            session_id=session_id,
            subject=scope,
            observations=[observation],
        )
    )
    return legacy._envelope("SHARED-CANDIPULL", {
        **result,
        "browser_session_bound": True,
        "owner_boundary": "NAOMI_ONLY",
        "scope_boundary": "GaiaOS:*",
        "durable_write": "NOT_PERFORMED",
        "next_operation": "SHARED-MEMSAV with exact candidate_id and a fresh SALT_CIRCLE",
    })


def _shared_memsav(command: str, request: Request) -> dict:
    data = _command_payload(command, "SHARED-MEMSAV")
    required = {"candidate_id", "approved", "authority", "scope", "salt_circle"}
    if set(data) != required:
        raise HTTPException(
            status_code=422,
            detail="Exact candidate_id, approved, authority, scope and salt_circle required",
        )
    if data["approved"] is not True or data["authority"] != "NAOMI":
        raise HTTPException(status_code=403, detail="Explicit Naomi approval required")
    if not isinstance(data["candidate_id"], str) or not data["candidate_id"]:
        raise HTTPException(status_code=422, detail="Exact candidate_id required")
    scope = _shared_scope(data["scope"])
    session_id = _ensure_browser_session(request)
    candidate = memcon_runtime.get_memory_candidate(data["candidate_id"])
    if candidate is None:
        raise HTTPException(status_code=404, detail="Unknown candidate_id")
    event = memcon_runtime.get_session_event(candidate["event_id"])
    if (
        event is None
        or event.get("session_id") != session_id
        or candidate.get("owner") != "NAOMI"
        or candidate.get("scope") != scope
        or not str(candidate.get("scope", "")).startswith("GaiaOS:")
    ):
        raise HTTPException(
            status_code=403,
            detail="Candidate ownership, scope or browser session mismatch",
        )
    if candidate.get("status") != "CANDIDATE":
        raise HTTPException(
            status_code=409,
            detail="Candidate is not pending; inspect prior result before retrying",
        )
    _validate_circle(
        data["salt_circle"],
        operation="SHARED_MEMSAV",
        scope=scope,
    )
    result = host_memory_gateway._host_memsav(
        host_memory_gateway.HostMemorySave(
            candidate_ids=[candidate["candidate_id"]],
            approved=True,
            authority="NAOMI",
        )
    )
    readback_routes = []
    for item in result.get("results", []):
        plan = item.get("elane_plan") or {}
        if plan.get("targets") or plan.get("github_write_required") is True:
            raise HTTPException(
                status_code=500,
                detail="HOLD_SHARED_BRIDGE_UNEXPECTED_ELANE_PLAN",
            )
        record_id = item.get("record_id")
        if record_id:
            readback_routes.append(
                f"/memoryos/continuity?record_id={record_id}"
            )
    return legacy._envelope("SHARED-MEMSAV", {
        **result,
        "browser_session_bound": True,
        "owner_boundary": "NAOMI_ONLY",
        "scope_boundary": "GaiaOS:*",
        "elane_writes": "FORBIDDEN_AND_NOT_PERFORMED",
        "continuity_readback_routes": readback_routes,
    })


@app.post("/chat", operation_id="browserChatWithSharedMemoryRuntime")
async def browser_chat_with_shared_memory(browser_request: Request):
    payload = await browser_request.json()
    messages = payload.get("messages", []) if isinstance(payload, dict) else []
    last_message = ""
    if messages:
        last = messages[-1]
        if isinstance(last, dict):
            last_message = str(last.get("content", "")).strip()
    if re.match(r"^\s*SHARED-CANDIPULL(?:\s|$)", last_message, flags=re.IGNORECASE):
        return _shared_candipull(last_message, browser_request)
    if re.match(r"^\s*SHARED-MEMSAV(?:\s|$)", last_message, flags=re.IGNORECASE):
        return _shared_memsav(last_message, browser_request)
    return await _original_browser_chat(browser_request)
