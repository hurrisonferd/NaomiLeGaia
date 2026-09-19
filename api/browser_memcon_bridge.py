"""Explicit browser bridge for live MemconOS and MemoryOS verification."""
from __future__ import annotations

import hashlib
import html
import json
import re
import uuid

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

import gaiaos_app
import gaiaos_api
import memcon_entrypoint
import memcon_runtime
import solo_chat_runtime
import host_memory_gateway
import gaiaos_verification
import vaskon_runtime

app = memcon_entrypoint.app
_original_chat = gaiaos_api.chat
_memory_runtime = memcon_entrypoint._memory_runtime
TEST_OWNER = "NAOMI_BROWSER_TEST"

app.routes[:] = [
    route for route in app.routes
    if not (getattr(route, "path", None) == "/chat" and getattr(route, "methods", set()) == {"POST"})
]


def _envelope(title: str, body: dict) -> dict:
    return {
        "output": title + "\n\n" + json.dumps(body, ensure_ascii=False, indent=2),
        "model": "gaiaos-carrier-runtime",
        "source": gaiaos_app._deployed_source(),
        "execution": "OBSERVED_RUNTIME",
    }


@app.post("/chat", operation_id="browserChatWithMemoryRuntime")
async def browser_chat(browser_request: Request):
    gaiaos_api._authorize_browser_session(browser_request)
    payload = await browser_request.json()
    messages = payload.get("messages", [])
    last_message = messages[-1].get("content", "").strip() if messages else ""
    if last_message.lower().rstrip(".") == "test the live memconos canary at the current pinned revision":
        return _envelope("LIVE MEMCONOS CANARY EXECUTED", memcon_runtime.canary())
    if last_message.lower().rstrip(".") == "start the live memoryos lifecycle test":
        return _start_lifecycle()
    if last_message.lower().rstrip(".") == "approve the pending memoryos candidate":
        return _approve_lifecycle()
    if _is_command(last_message, "SOLO"):
        return _handle_solo(last_message, browser_request)
    if _is_command(last_message, "ENDSOLO"):
        return _handle_endsolo(browser_request)
    solo = memcon_runtime.get_solo_session(_browser_session_id(browser_request))
    if solo:
        return solo_chat_runtime.respond(
            [{"role": m.get("role"), "content": m.get("content")} for m in messages],
            solo,
        )
    if _is_preserve_command(last_message):
        return _handle_preserve(messages, browser_request)
    if _is_galaxy_command(last_message, "ORBIT"):
        return _handle_galaxy_orbit(last_message)
    if _is_galaxy_command(last_message, "GRAVITY"):
        return _handle_galaxy_gravity(last_message)
    if _is_command(last_message, "CANDIPULL"):
        return _handle_candipull(messages, browser_request)
    if _is_command(last_message, "MEMSAV"):
        return _handle_memsav(last_message)
    return _original_chat(gaiaos_api.ChatRequest.model_validate(payload), browser_request)


def _handle_solo(command: str, request: Request) -> dict:
    daemon = re.sub(r"^SOLO\s*", "", command, flags=re.IGNORECASE).rstrip(".").strip().upper()
    if not daemon:
        return _envelope("SOLO HOLD", {"status": "HOLD", "reason": "Prime Daemon name required."})
    try:
        result = solo_chat_runtime.activate(_browser_session_id(request), daemon)
    except ValueError as exc:
        return _envelope("SOLO HOLD", {"status": "HOLD", "reason": str(exc)})
    return _envelope("SOLO SESSION ESTABLISHED", result)

def _handle_endsolo(request: Request) -> dict:
    session_id = _browser_session_id(request)
    current = memcon_runtime.get_solo_session(session_id)
    memcon_runtime.end_solo_session(session_id)
    return _envelope("SOLO SESSION ENDED", {
        "status": "SOLO_INACTIVE",
        "previous_daemon": current.get("daemon") if current else None,
        "session_id": session_id,
    })


def _handle_solo_candipull(messages: list[dict], request: Request, solo: dict) -> dict:
    daemon = str(solo["daemon"]).upper()
    substantive = [
        str(m.get("content","")).strip() for m in messages[:-1]
        if str(m.get("role","")).lower() == "user"
        and str(m.get("content","")).strip()
        and not _is_command(str(m.get("content","")), "SOLO")
        and not _is_command(str(m.get("content","")), "CANDIPULL")
        and not _is_command(str(m.get("content","")), "MEMSAV")
    ]
    if not substantive:
        return _envelope("SOLO CANDIPULL HOLD", {"status":"HOLD","reason":"No substantive interaction available."})
    candidate = solo_chat_runtime.candidate(_browser_session_id(request), daemon, substantive[-1])
    return _envelope("SOLO CANDIDATE READY", {
        "status":"CANDIDATE_READY","daemon":daemon,"candidate":candidate,
        "memory_scope":f"Solo:{daemon}","other_e_lanes":"DENIED",
        "next_command":"MEMSAV <candidate_id>",
    })

def _handle_solo_memsav(command: str, request: Request, solo: dict) -> dict:
    body = re.sub(r"^MEMSAV\s*", "", command, flags=re.IGNORECASE).rstrip(".").strip()
    if not body:
        return _envelope("SOLO MEMSAV HOLD", {"status":"HOLD","reason":"Exact candidate_id required."})
    candidate_id = body.split()[0]
    candidate = memcon_runtime.get_memory_candidate(candidate_id)
    daemon = str(solo["daemon"]).upper()
    if not candidate:
        return _envelope("SOLO MEMSAV HOLD", {"status":"HOLD","reason":"Unknown candidate_id"})
    if str(candidate.get("owner","")).upper() != daemon or str(candidate.get("scope","")) != f"Solo:{daemon}":
        return _envelope("SOLO MEMSAV HOLD", {
            "status":"HOLD","reason":"Candidate is outside this SOLO member-local scope.",
            "daemon":daemon,"candidate_id":candidate_id,
        })
    entry = (
        f"MEM[EXPERIENCE_PRESERVATION|{candidate.get('created_at','')[:10]}|"
        f"SOLO {daemon}|dedicated_conversation]\n"
        f"WHAT: {candidate.get('statement','')}\n"
        f"MY_ROLE: Material interaction preserved through dedicated SOLO conversation.\n"
        f"TRACE: candidate {candidate_id}; session {candidate.get('event_id')}\n"
        f"STATUS: COMMITTED"
    )
    result = solo_chat_runtime.write_elane(_browser_session_id(request), daemon, entry, approved=True)
    if result.get("status") == "COMMITTED":
        memcon_runtime.mark_candidate(candidate_id, "VERIFIED", result.get("commit_sha"))
        result["candidate_id"] = candidate_id
        result["readback_required"] = True
    return _envelope("SOLO MEMSAV", result)


def _is_command(text: str, command: str) -> bool:
    return bool(re.match(rf"^\s*{re.escape(command)}(?:\s+.*)?[.!]?\s*$", text, flags=re.IGNORECASE))


def _is_galaxy_command(text: str, word: str) -> bool:
    return bool(re.match(rf"^\s*(?://)?PW:{re.escape(word)}(?://)?(?:\s+.*)?[.!]?\s*$", text, flags=re.IGNORECASE))


def _galaxy_command_body(command: str, word: str) -> str:
    return re.sub(rf"^\s*(?://)?PW:{re.escape(word)}(?://)?\s*", "", command, flags=re.IGNORECASE).rstrip(".").strip()


def _handle_galaxy_orbit(command: str) -> dict:
    """Read-only Phase 1 inspection. No edge is inferred or written by this command."""
    record_id = _galaxy_command_body(command, "ORBIT").split()[0] if _galaxy_command_body(command, "ORBIT") else ""
    if not record_id:
        return _envelope("PW:ORBIT", {
            "status": "READY",
            "galaxy": memcon_runtime.galaxy_status(),
            "usage": "//PW:ORBIT// MEM-<record_id>",
            "writes_performed": [],
        })
    result = memcon_runtime.galaxy_record(record_id)
    if result is None:
        return _envelope("PW:ORBIT HOLD", {"status": "HOLD", "reason": "Unknown durable record_id", "record_id": record_id})
    return _envelope("PW:ORBIT", {"status": "OBSERVED", "record_id": record_id, "orbit": result, "writes_performed": []})


def _handle_galaxy_gravity(command: str) -> dict:
    """Shadow-mode gravity inspection. Phase 1 intentionally performs no scoring."""
    record_id = _galaxy_command_body(command, "GRAVITY").split()[0] if _galaxy_command_body(command, "GRAVITY") else ""
    if not record_id:
        return _envelope("PW:GRAVITY", {
            "status": "SHADOW_NOT_SCORED",
            "galaxy": memcon_runtime.galaxy_status(),
            "usage": "//PW:GRAVITY// MEM-<record_id>",
            "writes_performed": [],
            "proof_boundary": "Phase 1 installs the gravity data surface but does not invent scores.",
        })
    result = memcon_runtime.galaxy_record(record_id)
    if result is None:
        return _envelope("PW:GRAVITY HOLD", {"status": "HOLD", "reason": "Unknown durable record_id", "record_id": record_id})
    return _envelope("PW:GRAVITY", {
        "status": "SHADOW_NOT_SCORED" if result.get("gravity") is None else "OBSERVED",
        "record_id": record_id,
        "gravity": result.get("gravity"),
        "retrieval_effect": "NONE_SHADOW_MODE",
        "writes_performed": [],
    })


def _is_preserve_command(text: str) -> bool:
    return bool(re.match(r"^\s*(?://)?PW:PRESERVE(?://)?(?:\s+.*)?[.!]?\s*$", text, flags=re.IGNORECASE))


def _handle_preserve(messages: list[dict], request: Request) -> dict:
    """POWER WORD preservation router. Proposes destinations; performs no durable write."""
    last = str(messages[-1].get("content", "")).strip()
    directive = re.sub(r"^\s*(?://)?PW:PRESERVE(?://)?\s*", "", last, flags=re.IGNORECASE).rstrip(".").strip()
    candidate = _ensure_chat_candidate(messages, request, directive)
    if candidate is None:
        return _envelope("PW:PRESERVE HOLD", {"status": "HOLD", "reason": "No substantive interaction available to preserve."})
    owner = str(candidate.get("owner", "NAOMI")).upper()
    daemon_names = {"VERA", "ANVIL", "SELENE", "ORIN", "KESTREL", "NIMUE"}
    return _envelope("PW:PRESERVE ROUTING PROPOSAL", {
        "status": "APPROVAL_REQUIRED",
        "power_word": "PW:PRESERVE",
        "directive": directive,
        "candidate": candidate,
        "routing": {
            "memoryos": {
                "recommended": True,
                "candidate_id": candidate.get("candidate_id"),
                "durable_write": "NOT_PERFORMED",
                "approval_command": f"MEMSAV {candidate.get('candidate_id')}",
            },
            "e_lane": {
                "recommended": owner in daemon_names,
                "owner": owner if owner in daemon_names else None,
                "durable_write": "NOT_PERFORMED",
                "reason": "E-LANE is member-attributed developmental history. Ordinary ChatOS material remains MemoryOS-only unless a member-local perspective is explicitly identified.",
            },
        },
        "writes_performed": [],
        "next_command": f"MEMSAV {candidate.get('candidate_id')}",
        "authority_boundary": "PW:PRESERVE proposes routing. It does not bypass Naomi approval, silently write an E-LANE, or make host-memory claims.",
    })


def _browser_session_id(request: Request) -> str:
    token = request.cookies.get(gaiaos_api.SESSION_COOKIE)
    if not token:
        raise ValueError("Browser session missing; reload the GaiaOS page")
    return f"BROWSER-{hashlib.sha256(token.encode('utf-8')).hexdigest()[:24]}"


def _ensure_chat_candidate(messages: list[dict], request: Request, subject: str = "") -> dict | None:
    substantive = [
        str(message.get("content", "")).strip()
        for message in messages[:-1]
        if str(message.get("role", "")).lower() == "user"
        and str(message.get("content", "")).strip()
        and not _is_command(str(message.get("content", "")), "CANDIPULL")
        and not _is_command(str(message.get("content", "")), "MEMSAV")
    ]
    if not substantive:
        return None
    statement = substantive[-1]
    session_id = _browser_session_id(request)
    existing = memcon_runtime.list_memory_candidates(session_id=session_id, status="CANDIDATE", limit=100, subject=subject or None)
    normalized = " ".join(statement.lower().split())
    for item in existing["candidates"]:
        if " ".join(str(item.get("statement", "")).lower().split()) == normalized:
            return item
    session = memcon_runtime.get_session(session_id)
    if session is None:
        memcon_runtime.create_session(session_id, "browser-chat", subject)
    runtime = _memory_runtime()
    event = runtime.record_event(session_id, "NAOMI", "CHAT_INTERACTION", statement, "browser-chat")
    return runtime.candidate_from_event(
        event["event_id"], authority="NAOMI", record_type="INTERACTION", scope="ChatOS",
        statement=statement, source="browser-chat", owner="NAOMI",
        why_material="Candidate created by explicit CANDIPULL from the current browser chat interaction.",
    )


def _handle_candipull(messages: list[dict], request: Request) -> dict:
    last = str(messages[-1].get("content", "")).strip()
    subject = re.sub(r"^CANDIPULL\s*", "", last, flags=re.IGNORECASE).rstrip(".").strip()
    _ensure_chat_candidate(messages, request, subject)
    session_id = _browser_session_id(request)
    result = memcon_runtime.list_memory_candidates(session_id=session_id, status="CANDIDATE", limit=50, subject=subject or None)
    return _envelope("CANDIPULL", {
        "status": "CANDIDATES_READY","session_id": session_id,"subject": subject,
        "candidates": result["candidates"],"count": result["count"],"durable_write": "NOT_PERFORMED",
        "next_command": "MEMSAV <candidate_id>",
        "proof_boundary": "Candidate creation is non-durable. MEMSAV requires explicit Naomi authorization and reports the actual write receipt and verification.",
    })


def _handle_memsav(command: str) -> dict:
    body = re.sub(r"^MEMSAV\s*", "", command, flags=re.IGNORECASE).rstrip(".").strip()
    ids = [token.strip() for token in re.split(r"[,\s]+", body) if token.strip()]
    if not ids:
        return _envelope("MEMSAV HOLD", {"status": "HOLD", "reason": "Exact candidate_id required; omitted ID does not mean save everything."})
    runtime = _memory_runtime()
    results = []
    for candidate_id in ids:
        candidate = memcon_runtime.get_memory_candidate(candidate_id)
        if candidate is None:
            results.append({"candidate_id": candidate_id, "status": "HOLD", "reason": "Unknown candidate_id"})
            continue
        results.append(runtime.promote_candidate(candidate_id, True, "NAOMI"))
    return _envelope("MEMSAV", {
        "status": "COMPLETED" if all(item.get("status") == "VERIFIED" for item in results) else "PARTIAL_OR_HOLD",
        "results": results,
        "proof_boundary": "Only VERIFIED results with an actual write receipt and read-back verification are durable.",
    })


def _start_lifecycle() -> dict:
    token = uuid.uuid4().hex[:12]
    source = f"browser-memoryos-test:{token}"
    statement = f"Naomi approved a live MemoryOS lifecycle test marker {token}."
    runtime = _memory_runtime()
    session = runtime.start_session(source, "Live MemoryOS lifecycle verification")
    event = runtime.record_event(session["session_id"], "NAOMI", "TEST_INPUT", statement, source)
    candidate = runtime.candidate_from_event(
        event["event_id"], authority="NAOMI", record_type="TEST", scope="MemoryOS",
        statement=statement, source=source, owner=TEST_OWNER,
        why_material="Bounded test marker used to verify candidate-before-approval and post-approval retrieval.",
    )
    durable_matches = memcon_runtime.search_records(statement, limit=20, scope="MemoryOS")
    return _envelope("MEMORYOS TEST PAUSED AT APPROVAL GATE", {
        "carrier_source": gaiaos_app._deployed_source(),"session": session,"event": event,"candidate": candidate,
        "pre_approval_durable_matches": durable_matches["records"],"pre_approval_durable_count": durable_matches["count"],
        "candidate_is_non_durable": durable_matches["count"] == 0,
        "next_command": "Approve the pending MemoryOS candidate.",
        "approval_boundary": "No durable memory write occurs until explicit Naomi approval.",
    })


def _approve_lifecycle() -> dict:
    runtime = _memory_runtime()
    candidate = memcon_runtime.get_latest_memory_candidate(TEST_OWNER, "CANDIDATE")
    if candidate is None:
        return _envelope("MEMORYOS APPROVAL HOLD", {"status": "HOLD","reason": "No pending browser MemoryOS candidate found."})
    result = runtime.promote_candidate(candidate["candidate_id"], True, "NAOMI")
    record_id = result.get("record_id")
    readback = memcon_runtime.get_record(record_id) if record_id else None
    retrieved = runtime.retrieve(candidate["statement"], "MemoryOS", 10)
    return _envelope("MEMORYOS LIFECYCLE VERIFIED", {
        "candidate_id": candidate["candidate_id"],"promotion": result,"readback": readback,"retrieval": retrieved,
        "checks": {
            "explicit_approval": True,
            "write_receipt_success": result.get("write_receipt", {}).get("result") == "SUCCESS",
            "readback_matches_candidate": bool(readback and readback.get("statement") == candidate.get("statement") and readback.get("scope") == candidate.get("scope")),
            "retrieval_has_no_authority": retrieved.get("context_authority") == "NONE",
            "retrieval_is_not_identity_adoption": retrieved.get("retrieval_is_not_identity_adoption") is True,
        },
    })


@app.get("/galaxy/status", operation_id="galaxyRuntimeStatus")
def galaxy_runtime_status(browser_request: Request):
    gaiaos_api._authorize_browser_session(browser_request)
    return memcon_runtime.galaxy_status()


@app.get("/galaxy/record/{record_id}", operation_id="galaxyRecordInspection")
def galaxy_record_inspection(record_id: str, browser_request: Request):
    gaiaos_api._authorize_browser_session(browser_request)
    result = memcon_runtime.galaxy_record(record_id)
    if result is None:
        return JSONResponse({"status": "HOLD", "reason": "Unknown durable record_id", "record_id": record_id}, status_code=404)
    return result


@app.post("/memoryos/browser-test", operation_id="browserMemoryOSLifecycleTest")
async def browser_memoryos_test(browser_request: Request):
    gaiaos_api._authorize_browser_session(browser_request)
    payload = await browser_request.json()
    action = str(payload.get("action", "")).strip().lower()
    if action == "start":
        return _start_lifecycle()
    if action == "approve":
        return _approve_lifecycle()
    return {"status": "ERROR", "detail": "action must be start or approve"}


def _error_page(title: str, exc: Exception) -> HTMLResponse:
    detail = f"{type(exc).__name__}: {exc}"
    return HTMLResponse(
        "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
        f"<h1>{html.escape(title)}</h1>"
        f"<pre style='white-space:pre-wrap'>{html.escape(detail)}</pre>"
        "<p>Runtime action was not reported as successful.</p></body></html>",
        status_code=500,
    )


@app.get("/memoryos/start", response_class=HTMLResponse)
def memoryos_start(browser_request: Request):
    gaiaos_api._authorize_browser_session(browser_request)
    try:
        result = _start_lifecycle()
        output = html.escape(result["output"])
        return HTMLResponse("<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
            "<h1>MemoryOS start</h1>" + f"<pre style='white-space:pre-wrap'>{output}</pre>"
            "<p><a style='font-size:22px' href='/memoryos/approve'>Approve pending candidate</a></p></body></html>")
    except Exception as exc:
        return _error_page("MemoryOS start failed", exc)


@app.get("/memoryos/approve", response_class=HTMLResponse)
def memoryos_approve(browser_request: Request):
    gaiaos_api._authorize_browser_session(browser_request)
    try:
        result = _approve_lifecycle()
        output = html.escape(result["output"])
        # _approve_lifecycle returns a carrier envelope; promotion lives inside its JSON output.
        # Parse that observed payload so the UI cannot silently lose the verified record_id.
        approved_payload = {}
        try:
            approved_payload = json.loads(result["output"].split("\n\n", 1)[1])
        except (KeyError, IndexError, json.JSONDecodeError):
            approved_payload = {}
        record_id = approved_payload.get("promotion", {}).get("record_id")
        continuity_action = ""
        if record_id:
            from urllib.parse import urlencode
            continuity_url = "/memoryos/continuity?" + urlencode({"record_id": str(record_id)})
            continuity_action = (
                "<p><a style='display:inline-block;font-size:22px;padding:12px 16px;background:#eee;color:#111;"
                "text-decoration:none;border-radius:10px' href='" + html.escape(continuity_url, quote=True) + "'>"
                "Continue with this exact record</a></p>"
                "<p>The record ID above was supplied directly by the verified promotion receipt. No manual transcription is required.</p>"
            )
        return HTMLResponse("<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
            "<h1>MemoryOS approval</h1>" + continuity_action
            + f"<pre style='white-space:pre-wrap'>{output}</pre></body></html>")
    except Exception as exc:
        return _error_page("MemoryOS approval failed", exc)


@app.get("/memoryos/test", response_class=HTMLResponse)
def memoryos_test_page(browser_request: Request):
    gaiaos_api._authorize_browser_session(browser_request)
    return HTMLResponse("""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>GaiaOS MemoryOS Test</title></head><body style="font-family:-apple-system;padding:20px;background:#111;color:#eee">
<h1>MemoryOS lifecycle test</h1><p>Direct carrier-runtime test. No JavaScript.</p>
<p><a style="font-size:24px" href="/memoryos/start">1. Start test</a></p>
<p><a style="font-size:24px" href="/memoryos/approve">2. Approve pending candidate</a></p>
</body></html>""")



@app.get("/persistence/canary", response_class=HTMLResponse, operation_id="restartPersistenceCanary")
def restart_persistence_canary(browser_request: Request, token: str | None = None):
    gaiaos_api._authorize_browser_session(browser_request)
    try:
        result = memcon_runtime.restart_canary(token)
        if token is None and result.get("status") == "ARMED":
            # Pin the newly armed marker into the browser URL immediately. This
            # prevents a refresh from silently creating a different marker.
            pinned_url = "/persistence/canary?token=" + str(result["token"])
            return RedirectResponse(url=pinned_url, status_code=303)
        output = html.escape(json.dumps(result, ensure_ascii=False, indent=2))
        if result.get("status") == "PASS":
            action = "<p><strong>RESTART PERSISTENCE PROVEN.</strong> The marker survived into a different carrier process boot.</p>"
        else:
            action = (
                "<p><strong>Marker pinned.</strong> Restart or redeploy the Render service now. "
                "When it is back online, return to this exact page and tap the button below.</p>"
                "<p><a style='display:inline-block;font-size:22px;padding:12px 16px;background:#eee;color:#111;"
                "text-decoration:none;border-radius:10px' href=''>Check after restart</a></p>"
                "<p>Refreshing this page is also safe: the marker is stored in this page's URL and will not be replaced.</p>"
            )
        return HTMLResponse("<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
            "<h1>GaiaOS Restart Persistence Canary</h1>"
            + action + f"<pre style='white-space:pre-wrap'>{output}</pre></body></html>")
    except Exception as exc:
        return _error_page("Restart persistence canary failed", exc)


def _continuity_identity() -> dict:
    return {
        "boot_id": memcon_runtime.BOOT_ID,
        "render_instance_id": memcon_runtime.RENDER_INSTANCE_ID or None,
        "process_fingerprint": memcon_runtime._process_fingerprint(),
    }


def _safe_debug_value(value):
    try:
        return {"type": type(value).__name__, "repr": repr(value)}
    except Exception as exc:
        return {"type": type(value).__name__, "repr_error": type(exc).__name__}


def _memoryos_raw_read_diagnostic(record_id: str) -> dict:
    """Read-only backend interrogation. Never returns credentials."""
    with memcon_runtime._db() as conn:
        exact_cursor = conn.execute("SELECT * FROM memory_records WHERE record_id = ?", (record_id,))
        exact_description = getattr(exact_cursor, "description", None)
        exact_rows = exact_cursor.fetchall()
        broad_cursor = conn.execute("SELECT * FROM memory_records WHERE scope = ? ORDER BY created_at DESC LIMIT ?", ("MemoryOS", 10))
        broad_description = getattr(broad_cursor, "description", None)
        broad_rows = broad_cursor.fetchall()
        sql_probe_cursor = conn.execute(
            """SELECT record_id, length(record_id), hex(record_id), quote(record_id),
                      typeof(record_id), record_id = ?,
                      length(?) AS requested_length, hex(?) AS requested_hex,
                      quote(?) AS requested_quote, typeof(?) AS requested_type
               FROM memory_records WHERE scope = ? ORDER BY created_at DESC LIMIT 10""",
            (record_id, record_id, record_id, record_id, record_id, "MemoryOS"),
        )
        sql_probe_description = getattr(sql_probe_cursor, "description", None)
        sql_probe_rows = sql_probe_cursor.fetchall()
    def describe(desc):
        return [{"type": type(col).__name__, "repr": repr(col), "name": getattr(col, "name", None)} for col in (desc or [])]
    def rows(raw):
        return [{"row_type": type(row).__name__, "values": [_safe_debug_value(v) for v in row]} for row in raw]
    return {
        "backend": memcon_runtime.STORAGE_BACKEND,
        "requested": {"repr": repr(record_id), "length": len(record_id), "codepoints": [ord(ch) for ch in record_id]},
        "exact_query": {"description": describe(exact_description), "row_count": len(exact_rows), "rows": rows(exact_rows)},
        "broad_query": {"description": describe(broad_description), "row_count": len(broad_rows), "rows": rows(broad_rows)},
        "sql_value_probe": {"description": describe(sql_probe_description), "row_count": len(sql_probe_rows), "rows": rows(sql_probe_rows)},
        "proof_boundary": "Read-only raw driver and SQL value evidence. No persistence conclusion is implied by this diagnostic alone.",
    }

@app.get("/memoryos/raw-diagnostic", response_class=HTMLResponse, operation_id="memoryOSRawDiagnostic")
def memoryos_raw_diagnostic(browser_request: Request, record_id: str):
    gaiaos_api._authorize_browser_session(browser_request)
    try:
        diagnostic = _memoryos_raw_read_diagnostic(record_id)
        output = html.escape(json.dumps(diagnostic, ensure_ascii=False, indent=2))
        return HTMLResponse("<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'><h1>MemoryOS raw read diagnostic</h1><pre style='white-space:pre-wrap'>" + output + "</pre></body></html>")
    except Exception as exc:
        return _error_page("MemoryOS raw diagnostic failed", exc)


@app.get("/memoryos/continuity", response_class=HTMLResponse, operation_id="memoryOSContinuityTest")
def memoryos_continuity(
    browser_request: Request,
    record_id: str,
    prior_boot: str | None = None,
    prior_render: str | None = None,
    prior_pid: int | None = None,
    prior_ticks: str | None = None,
):
    gaiaos_api._authorize_browser_session(browser_request)
    try:
        record = memcon_runtime.get_record(record_id)
        if record is None:
            # Read-only diagnostics: identify the active backend and show whether
            # any recent MemoryOS records are visible there. This prevents a
            # missing row from being misreported as a persistence conclusion.
            visible_records = memcon_runtime.search_records("", 10, "MemoryOS")
            id_comparison = [{"requested_repr": repr(record_id), "requested_length": len(record_id), "visible_repr": repr(item.get("record_id")), "visible_length": len(str(item.get("record_id", ""))), "python_exact_equal": item.get("record_id") == record_id, "requested_codepoints": [ord(ch) for ch in record_id], "visible_codepoints": [ord(ch) for ch in str(item.get("record_id", ""))]} for item in visible_records.get("records", [])]
            diagnostic = {
                "schema": "gaiaos.memoryos.continuity-diagnostic.v2",
                "status": "HOLD",
                "record_id": record_id,
                "exact_record_retrieved": False,
                "storage": memcon_runtime.storage_status(),
                "memoryos_records_visible": visible_records,
                "record_id_comparison": id_comparison,
                "carrier": _continuity_identity(),
                "interpretation": (
                    "The requested record is not visible in the currently configured runtime store. "
                    "This diagnostic does not determine whether it was deleted, written to another backend, "
                    "or never durably committed there."
                ),
                "next_action": "Do not restart. Use the canonical record_id from the visible durable record if this request contains a transcription error.",
            }
            output = html.escape(json.dumps(diagnostic, ensure_ascii=False, indent=2))
            return HTMLResponse(
                "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
                "<h1>MemoryOS continuity HOLD</h1><p>The exact record was not found. Read-only diagnostics follow.</p>"
                f"<pre style='white-space:pre-wrap'>{output}</pre></body></html>",
                status_code=404,
            )

        current = _continuity_identity()
        current_pf = current["process_fingerprint"]
        if prior_boot is None:
            params = {
                "record_id": record_id,
                "prior_boot": current["boot_id"],
                "prior_render": current["render_instance_id"] or "",
                "prior_pid": str(current_pf.get("pid", "")),
                "prior_ticks": str(current_pf.get("proc_start_ticks", "")),
            }
            from urllib.parse import urlencode
            return RedirectResponse(url="/memoryos/continuity?" + urlencode(params), status_code=303)

        prior = {
            "boot_id": prior_boot,
            "render_instance_id": prior_render or None,
            "process_fingerprint": {"pid": prior_pid, "proc_start_ticks": prior_ticks},
        }
        boot_changed = current["boot_id"] != prior["boot_id"]
        render_changed = bool(current["render_instance_id"] and prior["render_instance_id"] and current["render_instance_id"] != prior["render_instance_id"])
        process_changed = (
            current_pf.get("pid") != prior_pid
            or str(current_pf.get("proc_start_ticks")) != str(prior_ticks)
        )
        different_carrier = boot_changed or render_changed or process_changed
        exact_record_retrieved = record.get("record_id") == record_id
        status = "PASS" if (different_carrier and exact_record_retrieved) else "NOT_RESTARTED"
        result = {
            "schema": "gaiaos.memoryos.continuity-receipt.v1",
            "status": status,
            "record_id": record_id,
            "record_retrieved": True,
            "record": record,
            "storage": memcon_runtime.storage_status(),
            "current_carrier": current,
            "prior_carrier": prior,
            "checks": {
                "boot_id_changed": boot_changed,
                "render_instance_changed": render_changed,
                "process_fingerprint_changed": process_changed,
                "different_carrier_observed": different_carrier,
                "exact_record_retrieved": exact_record_retrieved,
            },
            "proof_boundary": (
                "PASS proves this exact MemoryOS record was retrieved after an observed carrier identity change. "
                "It does not prove every MemoryOS operation or every failure mode."
            ),
        }
        output = html.escape(json.dumps(result, ensure_ascii=False, indent=2))
        if status == "PASS":
            action = "<p><strong>MEMORYOS CONTINUITY PROVEN.</strong> Exact record retrieved after carrier identity changed.</p>"
        else:
            action = (
                "<p><strong>Baseline pinned.</strong> Do not change this URL. Restart Render once, wait for it to return, "
                "then tap the button below.</p>"
                "<p><a style='display:inline-block;font-size:22px;padding:12px 16px;background:#eee;color:#111;"
                "text-decoration:none;border-radius:10px' href=''>Check after restart</a></p>"
            )
        return HTMLResponse(
            "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
            "<h1>GaiaOS MemoryOS Continuity Test</h1>" + action
            + f"<pre style='white-space:pre-wrap'>{output}</pre></body></html>"
        )
    except Exception as exc:
        return _error_page("MemoryOS continuity test failed", exc)


@app.get("/memoryos/continuity/recover", response_class=HTMLResponse, operation_id="memoryOSContinuityRecover")
def memoryos_continuity_recover(browser_request: Request):
    """Read-only recovery for a lost pinned tab using an independently preserved pre-restart baseline."""
    gaiaos_api._authorize_browser_session(browser_request)
    try:
        # Resolve the canonical record from durable evidence, not a hand-copied ID.
        expected_source = "browser-memoryos-test:371a6d98a3bd"
        with memcon_runtime._db() as conn:
            canonical_cursor = conn.execute(
                "SELECT record_id FROM memory_records WHERE scope = ? AND source = ? ORDER BY created_at DESC LIMIT 1",
                ("MemoryOS", expected_source),
            )
            canonical_row = canonical_cursor.fetchone()
        if canonical_row is None:
            raise RuntimeError("Canonical continuity record was not found by its durable source marker")
        record_id = str(canonical_row[0])
        prior = {
            "boot_id": "BOOT-bf2621aa5b3c49039789b452515a98bd",
            "render_instance_id": "srv-dafvq6ijnfac739rih70-hibernate-66bc89c57-5k4kv",
            "process_fingerprint": {"pid": 7, "proc_start_ticks": "1225523065"},
        }
        record = memcon_runtime.get_record(record_id)
        # Independent read-only witness: ask the configured database directly
        # whether the exact ID exists, and also list recent MemoryOS IDs. This
        # separates durable-row presence from any higher-level retrieval bug.
        with memcon_runtime._db() as conn:
            exact_cursor = conn.execute(
                "SELECT record_id, authority, record_type, scope, statement, source, status, version, created_at, updated_at, supersedes, notes FROM memory_records WHERE record_id = ?",
                (record_id,),
            )
            exact_rows = exact_cursor.fetchall()
            broad_cursor = conn.execute(
                "SELECT record_id, scope, source, created_at, updated_at FROM memory_records WHERE scope = ? ORDER BY created_at DESC LIMIT 10",
                ("MemoryOS",),
            )
            broad_rows = broad_cursor.fetchall()
        raw_exact = [_safe_debug_value(list(row)) for row in exact_rows]
        raw_broad = [_safe_debug_value(list(row)) for row in broad_rows]
        broad_ids = [str(row[0]) for row in broad_rows]
        raw_exact_present = any(str(row[0]) == record_id for row in exact_rows)
        broad_exact_present = record_id in broad_ids
        current = _continuity_identity()
        current_pf = current["process_fingerprint"]
        boot_changed = current["boot_id"] != prior["boot_id"]
        render_changed = bool(current["render_instance_id"] and current["render_instance_id"] != prior["render_instance_id"])
        process_changed = (
            current_pf.get("pid") != prior["process_fingerprint"]["pid"]
            or str(current_pf.get("proc_start_ticks")) != prior["process_fingerprint"]["proc_start_ticks"]
        )
        different_carrier = boot_changed or render_changed or process_changed
        exact_record_retrieved = bool(record and record.get("record_id") == record_id)
        status = "PASS" if (different_carrier and exact_record_retrieved) else "HOLD"
        result = {
            "schema": "gaiaos.memoryos.continuity-recovery-receipt.v2",
            "status": status,
            "baseline_source": "operator-preserved pre-restart screenshot",
            "record_identity_source": "durable MemoryOS source marker resolved by database",
            "record_id": record_id,
            "record_retrieved": record is not None,
            "record": record,
            "raw_database_witness": {
                "exact_sql_present": raw_exact_present,
                "broad_scan_contains_exact_id": broad_exact_present,
                "exact_rows": raw_exact,
                "recent_memoryos_rows": raw_broad,
                "interpretation": (
                    "If either raw presence check is true while record_retrieved is false, the durable row exists and the higher-level retrieval path is defective. "
                    "If both raw presence checks are false, this endpoint has not found the named row in the configured database."
                ),
            },
            "storage": memcon_runtime.storage_status(),
            "prior_carrier": prior,
            "current_carrier": current,
            "checks": {
                "boot_id_changed": boot_changed,
                "render_instance_changed": render_changed,
                "process_fingerprint_changed": process_changed,
                "different_carrier_observed": different_carrier,
                "exact_record_retrieved": exact_record_retrieved,
            },
            "proof_boundary": (
                "PASS proves the exact named MemoryOS record is readable now and that the live carrier identity differs "
                "from the independently preserved pre-restart baseline. The prior baseline values came from the operator's "
                "pre-restart screenshot, not from durable server-side pinning. It does not prove every MemoryOS operation "
                "or universal cross-host continuity."
            ),
        }
        output = html.escape(json.dumps(result, ensure_ascii=False, indent=2))
        heading = "MEMORYOS RECOVERY CONTINUITY PROVEN" if status == "PASS" else "MemoryOS recovery continuity HOLD"
        return HTMLResponse(
            "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
            f"<h1>{heading}</h1><pre style='white-space:pre-wrap'>{output}</pre></body></html>"
        )
    except Exception as exc:
        return _error_page("MemoryOS continuity recovery failed", exc)


@app.get("/verify", response_class=HTMLResponse, operation_id="verificationPage")
def verification_page(browser_request: Request):
    gaiaos_api._authorize_browser_session(browser_request)
    result = gaiaos_verification.run_verification()
    output = html.escape(json.dumps(result, ensure_ascii=False, indent=2))
    return HTMLResponse("<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
        "<h1>GaiaOS Implementation Verification</h1>"
        "<p>Every PASS below is an observation from this running carrier process.</p>"
        f"<pre style='white-space:pre-wrap'>{output}</pre>"
        "</body></html>")



@app.get("/vaskon/test", response_class=HTMLResponse, operation_id="liveVaskonTest")
def live_vaskon_test(browser_request: Request):
    gaiaos_api._authorize_browser_session(browser_request)
    try:
        result = vaskon_runtime.run_live_test()
        output = html.escape(json.dumps(result, ensure_ascii=False, indent=2))
        return HTMLResponse("<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
            "<h1>GaiaOS Live VASKON Runtime Test</h1>"
            "<p>Every field below is an observation from this running carrier process.</p>"
            f"<pre style='white-space:pre-wrap'>{output}</pre>"
            "</body></html>")
    except Exception as exc:
        return _error_page("Live VASKON test failed", exc)

@app.post("/verify", operation_id="verificationRun")
async def verification_run(browser_request: Request):
    gaiaos_api._authorize_browser_session(browser_request)
    result = gaiaos_verification.run_verification()
    return _envelope("GAIAOS IMPLEMENTATION VERIFICATION", result)


# Normal browser chat behavior remains available for all non-test requests.
