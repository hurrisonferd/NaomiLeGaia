"""Runtime MemconOS adapter mounted onto the existing GaiaOS carrier."""
from __future__ import annotations

import sqlite3
from typing import Any
from fastapi import Header, HTTPException
from pydantic import BaseModel, Field

import gaiaos_app
import memcon_runtime

app = gaiaos_app.app
mcp = gaiaos_app.mcp
memcon_runtime.initialize()

class MemoryWrite(BaseModel):
    authority: str = "NAOMI"
    approved: bool = False
    record_type: str = Field(min_length=1, max_length=100)
    scope: str = Field(min_length=1, max_length=200)
    statement: str = Field(min_length=1, max_length=20000)
    source: str = Field(min_length=1, max_length=2000)
    status: str = "ACTIVE"
    version: str = "1"
    supersedes: str | None = None
    notes: str = ""
    record_id: str | None = None

class MemoryUpdate(BaseModel):
    authority: str = "NAOMI"
    approved: bool = False
    statement: str | None = None
    status: str | None = None
    notes: str | None = None
    supersedes: str | None = None

def _auth(authorization: str | None) -> None:
    gaiaos_app.base._authorize(authorization)

@app.get("/memconos/health", operation_id="memconHealth")
def memcon_health(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _auth(authorization)
    memcon_runtime.initialize()
    return {"status":"ok","runtime":memcon_runtime.SCHEMA_VERSION,"database":str(memcon_runtime.DB_PATH),"durable_backend":True,"automatic_persistence":False,"authority":"NAOMI"}

@app.get("/memconos/read/{record_id}", operation_id="readMemconRecord")
def memcon_read_http(record_id: str, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _auth(authorization)
    record = memcon_runtime.get_record(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="MemconOS record not found")
    return {"record":record,"receipt":memcon_runtime._receipt("READ",record_id,"SUCCESS","Record retrieved from runtime store")}

@app.get("/memconos/search", operation_id="searchMemcon")
def memcon_search_http(q: str = "", limit: int = 20, scope: str | None = None, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _auth(authorization)
    return memcon_runtime.search_records(q,limit,scope)

@app.post("/memconos/write", operation_id="writeMemconRecord")
def memcon_write_http(payload: MemoryWrite, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _auth(authorization)
    try:
        return memcon_runtime.write_record(**payload.model_dump())
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except (ValueError, sqlite3.IntegrityError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.patch("/memconos/update/{record_id}", operation_id="updateMemconRecord")
def memcon_update_http(record_id: str, payload: MemoryUpdate, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _auth(authorization)
    try:
        return memcon_runtime.update_record(record_id,**payload.model_dump())
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"MemconOS record not found: {exc.args[0]}") from exc

@app.post("/memconos/canary", operation_id="runMemconCanary")
def memcon_canary_http(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _auth(authorization)
    return memcon_runtime.canary()

@mcp.tool()
def memcon_read(record_id: str) -> dict[str, Any]:
    """Read one durable MemconOS record and return a runtime receipt."""
    record=memcon_runtime.get_record(record_id)
    if record is None:
        return {"found":False,"record_id":record_id,"runtime":memcon_runtime.SCHEMA_VERSION}
    return {"found":True,"record":record,"receipt":memcon_runtime._receipt("READ",record_id,"SUCCESS","Record retrieved from runtime store")}

@mcp.tool()
def memcon_search(query: str = "", limit: int = 20) -> dict[str, Any]:
    """Search durable MemconOS records."""
    return memcon_runtime.search_records(query,limit)

@mcp.tool()
def memory_canary() -> dict[str, Any]:
    """Run the MemconOS runtime canary and return verification receipts."""
    return memcon_runtime.canary()
