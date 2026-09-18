"""Browser command bridge for live MemconOS verification.

This module replaces the generic /chat route with a narrow, explicit command path
for the live MemconOS canary. All other browser chat requests delegate unchanged
to the existing GaiaOS Responses API chat handler.
"""
from __future__ import annotations

from fastapi import Request

import gaiaos_app
import gaiaos_api
import memcon_entrypoint
import memcon_runtime

app = memcon_entrypoint.app
_original_chat = gaiaos_api.chat

# Remove the original /chat route so the explicit canary command is intercepted
# before the generic OpenAI Responses API path.
app.routes[:] = [
    route
    for route in app.routes
    if not (getattr(route, "path", None) == "/chat" and getattr(route, "methods", set()) == {"POST"})
]


@app.post("/chat", operation_id="browserChatWithMemconCanary")
def browser_chat(request: gaiaos_api.ChatRequest, browser_request: Request):
    gaiaos_api._authorize_browser_session(browser_request)

    last_message = request.messages[-1].content.strip()
    if last_message == "Test the live MemconOS canary at the current pinned revision.":
        result = memcon_runtime.canary()
        return {
            "output": (
                "LIVE MEMCONOS CANARY EXECUTED\\n\\n"
                f"carrier_source: {gaiaos_app._deployed_source()}\\n"
                f"platform: {gaiaos_api.APP_VERSION}\\n"
                "execution_surface: browser /chat command bridge\\n\\n"
                + __import__("json").dumps(result, ensure_ascii=False, indent=2)
            ),
            "model": "gaiaos-carrier-runtime",
            "source": gaiaos_app._deployed_source(),
            "execution": "OBSERVED_RUNTIME",
        }

    return _original_chat(request, browser_request)
