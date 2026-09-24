"""Independent, read-only HEATDEATH emergency carrier.

This app imports NO GaiaOS main application, hosted-chat code, GALAXY module or
MemoryOS writer. It runs in a separately built, minimal container and exposes
authenticated reads of existing authoritative legacy memory_records.

This is a RECOVERY READ SURFACE, not an independent full GaiaOS chat service or
a restored Phylactery. It performs no schema creation, promotion or mutation.
A fresh production instance requires remote storage and a separately configured
recovery API key. With no source database or invalid credentials, fail CLOSED.
"""
from __future__ import annotations

import hmac
import os
import sys
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

import gaiaos_memory_mode as memory_mode
import legacy_memory_reader as legacy
import memcon_runtime as storage

SCHEMA = "gaiaos.heatdeath.legacy-recovery.v1"
SERVICE = "gaiaos-legacy-recovery"
REQUIRED_COLUMNS = frozenset({
    "record_id", "authority", "record_type", "scope", "statement", "source",
    "status", "version", "created_at", "updated_at", "supersedes", "notes",
})

app = FastAPI(
    title="GaiaOS HEATDEATH Legacy Recovery",
    version="1.0.0",
    description="Isolated, authenticated, read-only legacy MemoryOS recovery.",
    docs_url=None, redoc_url=None, openapi_url=None,
)


class RecoverySearch(BaseModel):
    q: str = Field(default="", max_length=20000)
    scope: str | None = Field(default="MemoryOS", min_length=1, max_length=200)
    limit: int = Field(default=10, ge=1, le=20)
    broad_read_approved: bool = False


class RecoveryRecord(BaseModel):
    record_id: str = Field(min_length=1, max_length=200)


class RecoveryProbe(BaseModel):
    """Optional known-existing record; absence verifies only the read schema."""
    known_record_id: str | None = Field(default=None, min_length=1, max_length=200)


def _authorize(authorization: str | None) -> None:
    key = os.getenv("GAIAOS_RECOVERY_API_KEY", "")
    if len(key) < 32:
        raise HTTPException(status_code=503, detail="Recovery authentication is not configured")
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer authentication required")
    received = authorization.removeprefix("Bearer ").strip()
    if not hmac.compare_digest(received, key):
        raise HTTPException(status_code=401, detail="Invalid recovery credentials")


def _existing_storage() -> str:
    """Validate the existing DB without ever invoking schema initialization.

    The dedicated recovery process owns this imported storage module. Only
    AFTER a successful read-only check do we mark the module initialized so
    its existing search_records/get_record read functions skip their automatic
    CREATE TABLE IF NOT EXISTS initialization path.
    """
    local_test = os.getenv("GAIAOS_RECOVERY_ALLOW_LOCAL_TEST", "").strip() == "1"
    if not local_test and (
        storage.STORAGE_BACKEND != "turso_libsql"
        or not storage.TURSO_DATABASE_URL or not storage.TURSO_AUTH_TOKEN
    ):
        raise HTTPException(
            status_code=503,
            detail="Existing remote memory storage is not configured",
        )
    try:
        with storage._db() as connection:
            connection.execute(
                "SELECT record_id, authority, record_type, scope, statement,"
                " source, status, version, created_at, updated_at,"
                " supersedes, notes FROM memory_records LIMIT 0"
            )
            columns = {
                str(row[1]) for row in connection.execute(
                    "PRAGMA table_info(memory_records)"
                ).fetchall()
            }
        if not REQUIRED_COLUMNS.issubset(columns):
            raise ValueError("Existing legacy schema is incomplete")
    except Exception as exc:
        raise HTTPException(
            status_code=503, detail="Existing legacy memory schema is unavailable"
        ) from exc
    # No schema DDL: ONLY the verified, separately deployed read-only process
    # sets its local initialization guard after checking the existing table.
    storage._INITIALIZED = True
    return storage.STORAGE_BACKEND


def _mode() -> dict[str, Any]:
    """Recovery is strictly HEATDEATH regardless of the primary mode row."""
    control = memory_mode.mode_status(storage)
    return {
        "effective_mode": memory_mode.HEATDEATH,
        "primary_configured_mode": control.get("configured_mode"),
        "control_reason": control.get("reason"),
        "recovery_override": True,
    }


def _context() -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "service": SERVICE,
        "mode": memory_mode.HEATDEATH,
        "source_commit": os.getenv("GAIAOS_RECOVERY_SOURCE_COMMIT") or "UNATTESTED",
        "baseline_source_commit": legacy.BASELINE_SOURCE_COMMIT,
        "boot_id": storage.BOOT_ID,
        "effect_authority": "READ_ONLY",
        "ordinary_gaiaos_routes_available": False,
        "automatic_promotion": False,
        "e_lanes_modified": False,
        "writes_performed": [],
    }


@app.get("/healthz")
def healthz():
    """Minimal liveness only. This deliberately proves NOTHING about memory."""
    return {
        "service": SERVICE,
        "status": "ALIVE",
        "memory": "NOT_CHECKED",
        "recovery_key_configured": len(
            os.getenv("GAIAOS_RECOVERY_API_KEY", "")
        ) >= 32,
    }


@app.get("/legacy/status")
def status(authorization: str | None = Header(default=None)):
    _authorize(authorization)
    backend = _existing_storage()
    return {
        **_context(),
        "status": "READ_ONLY_LEGACY_READY",
        "storage_backend": backend,
        **_mode(),
        "proof_boundary": (
            "Existing memory table and read-only emergency carrier verified "
            "at this instant. A schema check is not proof of record-level "
            "recall, current live Turso durability, full GaiaOS chat recovery "
            "or an independently restored historical backup."
        ),
    }


@app.post("/legacy/search")
def search(payload: RecoverySearch,
           authorization: str | None = Header(default=None)):
    _authorize(authorization)
    if not payload.q.strip() and not payload.broad_read_approved:
        raise HTTPException(
            status_code=422, detail="Empty-query broad search requires explicit opt-in"
        )
    backend = _existing_storage()
    try:
        result = legacy.read(storage, payload.q, payload.scope, payload.limit)
        if (
            not isinstance(result, dict)
            or not isinstance(result.get("records"), list)
            or result.get("count") != len(result["records"])
            or result.get("scope_applied") != payload.scope
            or result.get("query_filter_active") is not bool(payload.q.strip())
            or not isinstance(result.get("runtime"), str)
        ):
            raise ValueError("Legacy retrieval returned an invalid envelope")
    except Exception as exc:
        raise HTTPException(
            status_code=503, detail="Legacy retrieval unavailable or inconsistent"
        ) from exc
    return {
        **_context(),
        "status": "PASS_LEGACY_READ",
        "storage_backend": backend,
        "retrieval": result,
        "record_count": result["count"],
        "semantic_galaxy_applied": False,
        "proof_boundary": "Direct legacy read of existing authorized records; no writes.",
    }


@app.post("/legacy/record")
def record(payload: RecoveryRecord,
           authorization: str | None = Header(default=None)):
    _authorize(authorization)
    backend = _existing_storage()
    try:
        item = storage.get_record(payload.record_id)
    except Exception as exc:
        raise HTTPException(
            status_code=503, detail="Existing legacy record store unavailable"
        ) from exc
    if item is None:
        raise HTTPException(status_code=404, detail="Record not found")
    if not isinstance(item, dict) or item.get("record_id") != payload.record_id:
        raise HTTPException(status_code=503, detail="Legacy record readback invalid")
    return {
        **_context(),
        "status": "PASS_LEGACY_RECORD_READ",
        "storage_backend": backend,
        "record": item,
        "semantic_galaxy_applied": False,
    }


@app.post("/legacy/selftest")
def selftest(payload: RecoveryProbe,
             authorization: str | None = Header(default=None)):
    _authorize(authorization)
    backend = _existing_storage()
    galaxy_modules = [
        name for name in sys.modules
        if name == "galaxy_frontdoor_context" or name == "galaxy_production"
        or name.startswith("galaxy_")
    ]
    if galaxy_modules:
        raise HTTPException(
            status_code=503, detail="GALAXY isolation invariant failed"
        )
    verified_record_id: str | None = None
    if payload.known_record_id:
        try:
            found = storage.get_record(payload.known_record_id)
        except Exception as exc:
            raise HTTPException(status_code=503,
                                detail="Known-record verification unavailable") from exc
        if not isinstance(found, dict) or found.get("record_id") != payload.known_record_id:
            raise HTTPException(
                status_code=409, detail="Known record was not recovered"
            )
        verified_record_id = found["record_id"]
    return {
        **_context(),
        "status": "PASS_RECOVERY_SCHEMA_AND_ISOLATION" if not verified_record_id
                  else "PASS_RECOVERY_KNOWN_RECORD",
        "storage_backend": backend,
        "galaxy_import_count": 0,
        "known_record_verified": bool(verified_record_id),
        "verified_record_id": verified_record_id,
        "proof_boundary": (
            "Read-only existing schema, isolated imports and optional exact "
            "record observed. Does not prove independent full ChatOS recovery."
        ),
    }
