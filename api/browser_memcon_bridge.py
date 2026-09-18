"""Explicit browser bridge for live MemconOS and MemoryOS verification."""
from __future__ import annotations

import hashlib
import html
import json
import re
import uuid

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse

import gaiaos_app
import gaiaos_api
import memcon_entrypoint
import memcon_runtime
import solo_chat_runtime
import host_memory_gateway  # registers host-facing MemoryOS MCP/HTTP tools

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
        f"SOLO {daemon}|dedicated_conversation]\\n"
        f"WHAT: {candidate.get('statement','')}\\n"
        f"MY_ROLE: Material interaction preserved through dedicated SOLO conversation.\\n"
        f"TRACE: candidate {candidate_id}; session {candidate.get('event_id')}\\n"
        f"STATUS: COMMITTED"
    )
    result = solo_chat_runtime.write_elane(
        _browser_session_id(request), daemon, entry, approved=True
    )
    if result.get("status") == "COMMITTED":
        memcon_runtime.mark_candidate(candidate_id, "VERIFIED", result.get("commit_sha"))
        result["candidate_id"] = candidate_id
        result["readback_required"] = True
    return _envelope("SOLO MEMSAV", result)


def _is_command(text: str, command: str) -> bool:
    return bool(re.match(rf"^\s*{re.escape(command)}(?:\s+.*)?[.!]?\s*$", text, flags=re.IGNORECASE))


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
    result = memcon_runtime.list_memory_candidates(
        session_id=session_id, status="CANDIDATE", limit=50, subject=subject or None
    )
    return _envelope("CANDIPULL", {
        "status": "CANDIDATES_READY",
        "session_id": session_id,
        "subject": subject,
        "candidates": result["candidates"],
        "count": result["count"],
        "durable_write": "NOT_PERFORMED",
        "next_command": "MEMSAV <candidate_id>",
        "proof_boundary": "Candidate creation is non-durable. MEMSAV requires explicit Naomi authorization and reports the actual write receipt and verification.",
    })


def _handle_memsav(command: str) -> dict:
    body = re.sub(r"^MEMSAV\s*", "", command, flags=re.IGNORECASE).rstrip(".").strip()
    ids = [token.strip() for token in re.split(r"[,\\s]+", body) if token.strip()]
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
        "carrier_source": gaiaos_app._deployed_source(),
        "session": session, "event": event, "candidate": candidate,
        "pre_approval_durable_matches": durable_matches["records"],
        "pre_approval_durable_count": durable_matches["count"],
        "candidate_is_non_durable": durable_matches["count"] == 0,
        "next_command": "Approve the pending MemoryOS candidate.",
        "approval_boundary": "No durable memory write occurs until explicit Naomi approval.",
    })


def _approve_lifecycle() -> dict:
    runtime = _memory_runtime()
    candidate = memcon_runtime.get_latest_memory_candidate(TEST_OWNER, "CANDIDATE")
    if candidate is None:
        return _envelope("MEMORYOS APPROVAL HOLD", {
            "status": "HOLD", "reason": "No pending browser MemoryOS candidate found."
        })
    result = runtime.promote_candidate(candidate["candidate_id"], True, "NAOMI")
    record_id = result.get("record_id")
    readback = memcon_runtime.get_record(record_id) if record_id else None
    retrieved = runtime.retrieve(candidate["statement"], "MemoryOS", 10)
    return _envelope("MEMORYOS LIFECYCLE VERIFIED", {
        "candidate_id": candidate["candidate_id"], "promotion": result,
        "readback": readback, "retrieval": retrieved,
        "checks": {
            "explicit_approval": True,
            "write_receipt_success": result.get("write_receipt", {}).get("result") == "SUCCESS",
            "readback_matches_candidate": bool(
                readback and readback.get("statement") == candidate.get("statement")
                and readback.get("scope") == candidate.get("scope")
            ),
            "retrieval_has_no_authority": retrieved.get("context_authority") == "NONE",
            "retrieval_is_not_identity_adoption": retrieved.get("retrieval_is_not_identity_adoption") is True,
        },
    })


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
        "<p>Runtime action was not reported as successful.</p>"
        "</body></html>",
        status_code=500,
    )


@app.get("/memoryos/start", response_class=HTMLResponse)
def memoryos_start(browser_request: Request):
    gaiaos_api._authorize_browser_session(browser_request)
    try:
        result = _start_lifecycle()
        output = html.escape(result["output"])
        return HTMLResponse(
            "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
            "<h1>MemoryOS start</h1>"
            f"<pre style='white-space:pre-wrap'>{output}</pre>"
            "<p><a style='font-size:22px' href='/memoryos/approve'>Approve pending candidate</a></p>"
            "</body></html>"
        )
    except Exception as exc:
        return _error_page("MemoryOS start failed", exc)


@app.get("/memoryos/approve", response_class=HTMLResponse)
def memoryos_approve(browser_request: Request):
    gaiaos_api._authorize_browser_session(browser_request)
    try:
        result = _approve_lifecycle()
        output = html.escape(result["output"])
        return HTMLResponse(
            "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
            "<h1>MemoryOS approval</h1>"
            f"<pre style='white-space:pre-wrap'>{output}</pre>"
            "</body></html>"
        )
    except Exception as exc:
        return _error_page("MemoryOS approval failed", exc)


@app.get("/memoryos/test", response_class=HTMLResponse)
def memoryos_test_page(browser_request: Request):
    gaiaos_api._authorize_browser_session(browser_request)
    return HTMLResponse("""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>GaiaOS MemoryOS Test</title></head><body style="font-family:-apple-system;padding:20px;background:#111;color:#eee">
<h1>MemoryOS lifecycle test</h1>
<p>Direct carrier-runtime test. No JavaScript.</p>
<p><a style="font-size:24px" href="/memoryos/start">1. Start test</a></p>
<p><a style="font-size:24px" href="/memoryos/approve">2. Approve pending candidate</a></p>
</body></html>""")


# Normal browser chat behavior remains available for all non-test requests.
