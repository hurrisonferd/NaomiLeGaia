"""Production entrypoint adding active DjinnOS v1 to the existing GaiaOS carrier."""
from __future__ import annotations

from typing import Any

from fastapi import Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

import shared_memory_browser_bridge
import gaiaos_api
import gaiaos_app
import djinn_runtime

app = shared_memory_browser_bridge.app
CARRIER_VERSION = "1.7.1"

# Preserve the established carrier and extend its version/source-backed boot packet.
gaiaos_app.EXTENSION_VERSION = CARRIER_VERSION
gaiaos_api.APP_VERSION = CARRIER_VERSION
app.version = CARRIER_VERSION

_original_boot_packet = gaiaos_app._boot_packet

def _djinn_boot_packet(invocation_surface: str) -> dict[str, Any]:
    packet = _original_boot_packet(invocation_surface)
    packet["carrier_version"] = CARRIER_VERSION
    packet["djinn"] = djinn_runtime.status(gaiaos_app._deployed_commit())
    packet.setdefault("laws", []).extend([
        "DJINN ARE TOOLS NOT PERSONS",
        "NO RETROACTIVE DJINN HISTORY",
        "NO MUTATION CROSSES THE SALT_CIRCLE",
    ])
    return packet

gaiaos_app._boot_packet = _djinn_boot_packet


class DjinnInvokeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    selector: str = Field(min_length=1, max_length=32)
    calling_prime: str = Field(min_length=1, max_length=32)
    objective: str = Field(min_length=1, max_length=2000)
    payload: dict[str, Any] = Field(default_factory=dict)
    invocation_id: str | None = Field(default=None, max_length=160)
    invoked_at: str | None = Field(default=None, max_length=64)
    salt_circle: dict[str, Any] | None = None


@app.get("/djinn/status", operation_id="djinnStatus")
def djinn_status() -> JSONResponse:
    return JSONResponse(
        djinn_runtime.status(gaiaos_app._deployed_commit()),
        headers={"Cache-Control": "no-store", "Pragma": "no-cache"},
    )


@app.get("/djinn/registry", operation_id="djinnRegistry")
def djinn_registry() -> JSONResponse:
    payload = djinn_runtime.load_registry()
    return JSONResponse(
        {**payload, "source_commit": gaiaos_app._deployed_commit()},
        headers={"Cache-Control": "no-store", "Pragma": "no-cache"},
    )


@app.get("/djinn/canary", operation_id="djinnCanary")
def djinn_canary() -> JSONResponse:
    return JSONResponse(
        djinn_runtime.run_canary(gaiaos_app._deployed_commit()),
        headers={"Cache-Control": "no-store", "Pragma": "no-cache"},
    )


@app.post("/djinn/invoke", operation_id="invokeDjinn")
def invoke_djinn(
    payload: DjinnInvokeRequest,
    request: Request,
    authorization: str | None = Header(default=None),
) -> JSONResponse:
    # Invocation is operator/session authenticated even for read-only helpers.
    # No external action adapters are exposed through this public route.
    if authorization is not None:
        gaiaos_api._authorize(authorization)
    else:
        gaiaos_api._authorize_browser_session(request)
    try:
        result = djinn_runtime.dispatch(
            payload.selector,
            calling_prime=payload.calling_prime,
            objective=payload.objective,
            payload=payload.payload,
            invocation_id=payload.invocation_id,
            invoked_at=payload.invoked_at,
            salt_circle=payload.salt_circle,
            action_adapters=None,
        )
    except djinn_runtime.DjinnError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return JSONResponse(result, headers={"Cache-Control": "no-store", "Pragma": "no-cache"})
