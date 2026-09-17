"""Runtime MemconOS and MemoryOS adapter mounted onto the GaiaOS carrier."""
from __future__ import annotations

import sqlite3
from typing import Any
from fastapi import Header, HTTPException
from pydantic import BaseModel, Field

import gaiaos_app
import memcon_runtime

MEMORY_RUNTIME_PATH = "GaiaOS/SystemsOS/Core/MemoryOS/Runtime/GAIAOS-MEMORY.v1.py"

app = gaiaos_app.app
mcp = gaiaos_app.mcp
memcon_runtime.initialize()

def _memory_runtime():
    return gaiaos_app._gaia_runtime(MEMORY_RUNTIME_PATH, "gaia_memory_runtime")

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

class MemorySession(BaseModel):
    source: str = Field(min_length=1, max_length=2000)
    subject: str = Field(default="", max_length=20000)

class MemoryEvent(BaseModel):
    session_id: str = Field(min_length=1, max_length=200)
    actor: str = Field(min_length=1, max_length=100)
    event_type: str = Field(min_length=1, max_length=100)
    statement: str = Field(min_length=1, max_length=20000)
    source: str = Field(min_length=1, max_length=2000)
    relation: str = "PART_OF"

class MemoryCandidate(BaseModel):
    event_id: str = Field(min_length=1, max_length=200)
    authority: str = "NAOMI"
    record_type: str = Field(min_length=1, max_length=100)
    scope: str = Field(min_length=1, max_length=200)
    statement: str = Field(min_length=1, max_length=20000)
    source: str = Field(min_length=1, max_length=2000)
    owner: str = Field(min_length=1, max_length=100)
    why_material: str = Field(min_length=1, max_length=5000)
    other_voices: list[str] = Field(default_factory=list, max_length=12)
    tension: str = Field(default="", max_length=5000)

class MemoryPromote(BaseModel):
    authority: str = "NAOMI"
    approved: bool = False

def _auth(authorization: str | None) -> None:
    gaiaos_app.base._authorize(authorization)

@app.get("/memconos/health", operation_id="memconHealth")
def memcon_health(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _auth(authorization)
    memcon_runtime.initialize()
    return {"status":"ok","runtime":memcon_runtime.SCHEMA_VERSION,"database":str(memcon_runtime.DB_PATH),
            "durable_backend":True,"automatic_persistence":False,"authority":"NAOMI",
            "memoryos_lifecycle":True}

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

@app.post("/memoryos/session", operation_id="startMemorySession")
def memory_session_http(payload: MemorySession, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _auth(authorization)
    return _memory_runtime().start_session(payload.source, payload.subject)

@app.post("/memoryos/event", operation_id="recordMemoryEvent")
def memory_event_http(payload: MemoryEvent, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _auth(authorization)
    runtime = _memory_runtime()
    try:
        return runtime.record_event(**payload.model_dump())
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/memoryos/session/{session_id}", operation_id="readMemorySession")
def memory_session_read_http(session_id: str, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _auth(authorization)
    session = memcon_runtime.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="MemoryOS session not found")
    return {"schema": "gaiaos.memoryos.runtime.v1", "status":"OBSERVED", "session":session}

@app.post("/memoryos/candidate", operation_id="createMemoryCandidate")
def memory_candidate_http(payload: MemoryCandidate, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _auth(authorization)
    runtime = _memory_runtime()
    try:
        return runtime.candidate_from_event(**payload.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"MemoryOS event not found: {exc.args[0]}") from exc

@app.get("/memoryos/candidate/{candidate_id}", operation_id="readMemoryCandidate")
def memory_candidate_read_http(candidate_id: str, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _auth(authorization)
    candidate = memcon_runtime.get_memory_candidate(candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="MemoryOS candidate not found")
    return {"schema":"gaiaos.memoryos.runtime.v1","status":"OBSERVED","candidate":candidate}

@app.post("/memoryos/promote/{candidate_id}", operation_id="promoteMemoryCandidate")
def memory_promote_http(candidate_id: str, payload: MemoryPromote, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _auth(authorization)
    try:
        return _memory_runtime().promote_candidate(candidate_id, payload.approved, payload.authority)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"MemoryOS candidate not found: {exc.args[0]}") from exc

@app.get("/memoryos/retrieve", operation_id="retrieveMemoryContext")
def memory_retrieve_http(q: str = "", scope: str | None = None, limit: int = 10, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _auth(authorization)
    return _memory_runtime().retrieve(q, scope, limit)

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

@mcp.tool()
def memory_start_session(source: str, subject: str = "") -> dict[str, Any]:
    """Start a bounded MemoryOS session event graph."""
    return _memory_runtime().start_session(source, subject)

@mcp.tool()
def memory_record_event(session_id: str, actor: str, event_type: str, statement: str, source: str, relation: str = "PART_OF") -> dict[str, Any]:
    """Record one provenance-bearing event in a MemoryOS session graph."""
    return _memory_runtime().record_event(session_id, actor, event_type, statement, source, relation)

@mcp.tool()
def memory_candidate(event_id: str, record_type: str, scope: str, statement: str, source: str, owner: str,
                     why_material: str, authority: str = "NAOMI", other_voices: list[str] | None = None,
                     tension: str = "") -> dict[str, Any]:
    """Create a non-durable memory candidate from an observed event."""
    return _memory_runtime().candidate_from_event(
        event_id, authority=authority, record_type=record_type, scope=scope,
        statement=statement, source=source, owner=owner, why_material=why_material,
        other_voices=other_voices, tension=tension,
    )

@mcp.tool()
def memory_promote(candidate_id: str, approved: bool = False, authority: str = "NAOMI") -> dict[str, Any]:
    """Promote a memory candidate only with explicit Naomi approval, then verify the durable record."""
    return _memory_runtime().promote_candidate(candidate_id, approved, authority)

@mcp.tool()
def memory_retrieve(query: str = "", scope: str | None = None, limit: int = 10) -> dict[str, Any]:
    """Retrieve durable memory as context, never as identity authority."""
    return _memory_runtime().retrieve(query, scope, limit)
