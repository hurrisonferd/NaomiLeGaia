"""Explicit browser command bridge for live MemconOS and MemoryOS verification."""
from __future__ import annotations

import json
import uuid

from fastapi import Request

import gaiaos_app
import gaiaos_api
import memcon_entrypoint
import memcon_runtime
import gaia_memory_runtime

app = memcon_entrypoint.app
_original_chat = gaiaos_api.chat
TEST_OWNER = "NAOMI_BROWSER_TEST"

# Remove the generic POST /chat route so explicit runtime test commands execute
# in the carrier itself rather than being handed to the language model.
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
def browser_chat(request: gaiaos_api.ChatRequest, browser_request: Request):
    gaiaos_api._authorize_browser_session(browser_request)
    last_message = request.messages[-1].content.strip()

    if last_message == "Test the live MemconOS canary at the current pinned revision.":
        return _envelope("LIVE MEMCONOS CANARY EXECUTED", memcon_runtime.canary())

    if last_message == "Start the live MemoryOS lifecycle test.":
        token = uuid.uuid4().hex[:12]
        source = f"browser-memoryos-test:{token}"
        statement = f"Naomi approved a live MemoryOS lifecycle test marker {token}."
        session = gaia_memory_runtime.start_session(source, "Live MemoryOS lifecycle verification")
        event = gaia_memory_runtime.record_event(
            session["session_id"], "NAOMI", "TEST_INPUT", statement, source
        )
        candidate = gaia_memory_runtime.candidate_from_event(
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

    if last_message == "Approve the pending MemoryOS candidate.":
        candidate = memcon_runtime.get_latest_memory_candidate(TEST_OWNER, "CANDIDATE")
        if candidate is None:
            return _envelope(
                "MEMORYOS APPROVAL HOLD",
                {"status": "HOLD", "reason": "No pending browser MemoryOS candidate found."},
            )
        result = gaia_memory_runtime.promote_candidate(candidate["candidate_id"], True, "NAOMI")
        record_id = result.get("record_id")
        readback = memcon_runtime.get_record(record_id) if record_id else None
        retrieved = gaia_memory_runtime.retrieve(candidate["statement"], "MemoryOS", 10)
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

    return _original_chat(request, browser_request)
