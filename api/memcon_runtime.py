"""MemconOS durable runtime backend.

SQLite is used so the service has a real durable store without adding a database
service dependency. Render persistence is provided by mounting /data as a disk.
This module never treats GitHub source persistence as runtime memory.
"""
from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path(os.getenv("MEMCONOS_DB_PATH", "/data/memconos.db"))
SCHEMA_VERSION = "memconos.runtime.v1"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def initialize() -> None:
    with _db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS memory_records (
                record_id TEXT PRIMARY KEY,
                authority TEXT NOT NULL,
                record_type TEXT NOT NULL,
                scope TEXT NOT NULL,
                statement TEXT NOT NULL,
                source TEXT NOT NULL,
                status TEXT NOT NULL,
                version TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                supersedes TEXT,
                notes TEXT NOT NULL DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_memory_scope ON memory_records(scope);
            CREATE INDEX IF NOT EXISTS idx_memory_status ON memory_records(status);
            CREATE INDEX IF NOT EXISTS idx_memory_created ON memory_records(created_at);
            CREATE TABLE IF NOT EXISTS runtime_receipts (
                receipt_id TEXT PRIMARY KEY,
                operation TEXT NOT NULL,
                record_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                result TEXT NOT NULL,
                detail TEXT NOT NULL
            );
            """
        )


def _receipt(operation: str, record_id: str, result: str, detail: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"MEMREC-{uuid.uuid4().hex}",
        "operation": operation,
        "record_id": record_id,
        "timestamp": _now(),
        "result": result,
        "detail": detail,
        "runtime": SCHEMA_VERSION,
    }
    with _db() as conn:
        conn.execute(
            "INSERT INTO runtime_receipts VALUES (?, ?, ?, ?, ?, ?)",
            (receipt["receipt_id"], operation, record_id, receipt["timestamp"], result, json.dumps(receipt)),
        )
    return receipt


def write_record(*, authority: str, record_type: str, scope: str, statement: str,
                 source: str, status: str = "ACTIVE", version: str = "1",
                 supersedes: str | None = None, notes: str = "",
                 approved: bool = False, record_id: str | None = None) -> dict[str, Any]:
    if authority != "NAOMI":
        raise PermissionError("Memory writes require authority=NAOMI")
    if not approved:
        raise PermissionError("Memory writes require explicit Naomi approval")
    if not statement.strip():
        raise ValueError("statement must not be empty")
    if not source.strip():
        raise ValueError("source must not be empty")
    initialize()
    record_id = record_id or f"MEM-{uuid.uuid4().hex}"
    created = _now()
    with _db() as conn:
        conn.execute(
            "INSERT INTO memory_records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (record_id, authority, record_type, scope, statement, source, status,
             version, created, created, supersedes, notes),
        )
    return {"record": get_record(record_id), "receipt": _receipt("WRITE", record_id, "SUCCESS", "Durably written to SQLite runtime store")}


def get_record(record_id: str) -> dict[str, Any] | None:
    initialize()
    with _db() as conn:
        row = conn.execute("SELECT * FROM memory_records WHERE record_id = ?", (record_id,)).fetchone()
    return dict(row) if row else None


def search_records(query: str, limit: int = 20, scope: str | None = None) -> dict[str, Any]:
    initialize()
    terms = [term.strip().lower() for term in query.split() if term.strip()]
    limit = max(1, min(int(limit), 100))
    with _db() as conn:
        if scope:
            rows = conn.execute(
                "SELECT * FROM memory_records WHERE scope = ? ORDER BY created_at DESC LIMIT ?",
                (scope, limit),
            ).fetchall()
        elif terms:
            pattern = "%" + "%".join(terms) + "%"
            rows = conn.execute(
                "SELECT * FROM memory_records WHERE lower(statement) LIKE ? OR lower(notes) LIKE ? OR lower(record_id) LIKE ? OR lower(scope) LIKE ? ORDER BY created_at DESC LIMIT ?",
                (pattern, pattern, pattern, pattern, limit),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM memory_records ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    return {"records": [dict(row) for row in rows], "count": len(rows), "runtime": SCHEMA_VERSION}


def update_record(record_id: str, *, authority: str, approved: bool, statement: str | None = None,
                  status: str | None = None, notes: str | None = None,
                  supersedes: str | None = None) -> dict[str, Any]:
    if authority != "NAOMI" or not approved:
        raise PermissionError("Record updates require explicit Naomi approval")
    initialize()
    old = get_record(record_id)
    if old is None:
        raise KeyError(record_id)
    values = {
        "statement": statement if statement is not None else old["statement"],
        "status": status if status is not None else old["status"],
        "notes": notes if notes is not None else old["notes"],
        "supersedes": supersedes if supersedes is not None else old["supersedes"],
        "updated_at": _now(),
    }
    with _db() as conn:
        conn.execute(
            "UPDATE memory_records SET statement=?, status=?, notes=?, supersedes=?, updated_at=? WHERE record_id=?",
            (values["statement"], values["status"], values["notes"], values["supersedes"], values["updated_at"], record_id),
        )
    return {"record": get_record(record_id), "receipt": _receipt("UPDATE", record_id, "SUCCESS", "Durably updated in SQLite runtime store")}


def canary() -> dict[str, Any]:
    initialize()
    canary_id = "GAIA-MEMCON-ALPHA-001"
    existing = get_record(canary_id)
    if existing is None:
        write_record(
            authority="NAOMI", approved=True, record_id=canary_id,
            record_type="CANARY", scope="MemconOS",
            statement="When information fits the MemconOS criteria, record it for future recall.",
            source="GaiaOS/SystemsOS/Core/MemberContinuityOS/MEMCONOS-CANARY.v1.md",
            status="ACTIVE", version="1", notes="Runtime bootstrap canary",
        )
        existing = get_record(canary_id)
    read_receipt = _receipt("READ", canary_id, "SUCCESS", "Canary retrieved from runtime store")
    return {
        "schema": SCHEMA_VERSION,
        "canary_id": canary_id,
        "runtime_store": str(DB_PATH),
        "record": existing,
        "read_receipt": read_receipt,
        "runtime_persistence": True,
        "source_persistence": True,
        "claim_ceiling": "This proves the running service can durably read/write the runtime store. It does not prove automatic capture from every ChatGPT conversation.",
    }
