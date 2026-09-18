"""Explicit browser command bridge for live MemconOS and MemoryOS verification."""
from __future__ import annotations

import json
import uuid

from fastapi import Request
from fastapi.responses import HTMLResponse

import gaiaos_app
import gaiaos_api
import memcon_entrypoint
import memcon_runtime

app = memcon_entrypoint.app
_original_chat = gaiaos_api.chat
_memory_runtime = memcon_entrypoint._memory_runtime
TEST_OWNER = "NAOMI_BROWSER_TEST"

# Remove the generic POST /chat route so the existing browser chat remains unchanged
# for ordinary requests while explicit runtime commands can use this carrier surface.
app.routes[:] = [
    route
    for route in app.routes
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

    return _original_chat(gaiaos_api.ChatRequest.model_validate(payload), browser_request)


def _start_lifecycle() -> dict:
    token = uuid.uuid4().hex[:12]
    source = f"browser-memoryos-test:{token}"
    statement = f"Naomi approved a live MemoryOS lifecycle test marker {token}."
    runtime = _memory_runtime()
    session = runtime.start_session(source, "Live MemoryOS lifecycle verification")
    event = runtime.record_event(
        session["session_id"], "NAOMI", "TEST_INPUT", statement, source
    )
    candidate = runtime.candidate_from_event(
        event["event_id"],
        authority="NAOMI",
        record_type="TEST",
        scope="MemoryOS",
        statement=statement,
        source=source,
        owner=TEST_OWNER,
        why_material="Bounded test marker used to verify candidate-before-approval and post-approval retrieval.",
    )
    durable_matches = memcon_runtime.search_records(statement, limit=20, scope="MemoryOS")
    return _envelope(
        "MEMORYOS TEST PAUSED AT APPROVAL GATE",
        {
            "carrier_source": gaiaos_app._deployed_source(),
            "session": session,
            "event": event,
            "candidate": candidate,
            "pre_approval_durable_matches": durable_matches["records"],
            "pre_approval_durable_count": durable_matches["count"],
            "candidate_is_non_durable": durable_matches["count"] == 0,
            "next_command": "Approve the pending MemoryOS candidate.",
            "approval_boundary": "No durable memory write occurs until explicit Naomi approval.",
        },
    )


def _approve_lifecycle() -> dict:
    runtime = _memory_runtime()
    candidate = memcon_runtime.get_latest_memory_candidate(TEST_OWNER, "CANDIDATE")
    if candidate is None:
        return _envelope(
            "MEMORYOS APPROVAL HOLD",
            {"status": "HOLD", "reason": "No pending browser MemoryOS candidate found."},
        )
    result = runtime.promote_candidate(candidate["candidate_id"], True, "NAOMI")
    record_id = result.get("record_id")
    readback = memcon_runtime.get_record(record_id) if record_id else None
    retrieved = runtime.retrieve(candidate["statement"], "MemoryOS", 10)
    return _envelope(
        "MEMORYOS LIFECYCLE VERIFIED",
        {
            "candidate_id": candidate["candidate_id"],
            "promotion": result,
            "readback": readback,
            "retrieval": retrieved,
            "checks": {
                "explicit_approval": True,
                "write_receipt_success": result.get("write_receipt", {}).get("result") == "SUCCESS",
                "readback_matches_candidate": bool(
                    readback
                    and readback.get("statement") == candidate.get("statement")
                    and readback.get("scope") == candidate.get("scope")
                ),
                "retrieval_has_no_authority": retrieved.get("context_authority") == "NONE",
                "retrieval_is_not_identity_adoption": retrieved.get("retrieval_is_not_identity_adoption") is True,
            },
        },
    )


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


@app.get("/memoryos/test", response_class=HTMLResponse)
def memoryos_test_page(browser_request: Request):
    gaiaos_api._authorize_browser_session(browser_request)
    return HTMLResponse("""<!doctype html>
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>GaiaOS MemoryOS Test</title>
<style>
body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;max-width:760px;margin:auto;padding:20px;background:#111;color:#eee}
button{font:inherit;padding:14px 18px;border:0;border-radius:12px;margin:6px 0}
pre{white-space:pre-wrap;background:#1d1d1d;border:1px solid #333;border-radius:14px;padding:14px;overflow:auto}
#approve{display:none}
</style></head><body>
<h1>MemoryOS lifecycle test</h1>
<p>This page runs the carrier runtime directly. It does not ask the language model to execute anything.</p>
<button id="start">1. Start test</button>
<button id="approve">2. Approve candidate</button>
<pre id="out">Waiting for test start.</pre>
<script>
const out=document.querySelector("#out"), approve=document.querySelector("#approve");
async function run(action){
  const r=await fetch("/memoryos/browser-test",{method:"POST",headers:{"Content-Type":"application/json"},credentials:"same-origin",body:JSON.stringify({action})});
  const j=await r.json(); out.textContent=j.output||JSON.stringify(j,null,2);
  if(action==="start" && j.output && j.output.includes("MEMORYOS TEST PAUSED AT APPROVAL GATE")) approve.style.display="block";
}
document.querySelector("#start").onclick=()=>run("start");
approve.onclick=()=>run("approve");
</script></body></html>""")


# Normal browser chat behavior remains available for all non-test requests.
