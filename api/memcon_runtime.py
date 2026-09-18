"""MemconOS durable runtime backend for MemoryOS and MemberContinuityOS."""
from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path(os.getenv("MEMCONOS_DB_PATH", "/data/memconos.db"))
SCHEMA_VERSION = "memconos.runtime.v2"


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

            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                subject TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS session_events (
                event_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                actor TEXT NOT NULL,
                event_type TEXT NOT NULL,
                statement TEXT NOT NULL,
                source TEXT NOT NULL,
                relation TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES sessions(session_id)
            );
            CREATE INDEX IF NOT EXISTS idx_session_events_session ON session_events(session_id);
            CREATE INDEX IF NOT EXISTS idx_session_events_actor ON session_events(actor);

            CREATE TABLE IF NOT EXISTS memory_candidates (
                candidate_id TEXT PRIMARY KEY,
                event_id TEXT NOT NULL,
                authority TEXT NOT NULL,
                record_type TEXT NOT NULL,
                scope TEXT NOT NULL,
                statement TEXT NOT NULL,
                source TEXT NOT NULL,
                owner TEXT NOT NULL,
                why_material TEXT NOT NULL,
                other_voices TEXT NOT NULL,
                tension TEXT NOT NULL,
                fingerprint TEXT NOT NULL,
                duplicate_of TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                promoted_record_id TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_candidates_status ON memory_candidates(status);
            CREATE INDEX IF NOT EXISTS idx_candidates_fingerprint ON memory_candidates(fingerprint);
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


def create_session(session_id: str, source: str, subject: str = "") -> None:
    initialize()
    with _db() as conn:
        conn.execute("INSERT INTO sessions VALUES (?, ?, ?, ?)", (session_id, source, subject, _now()))


def create_session_event(*, event_id: str, session_id: str, actor: str,
                         event_type: str, statement: str, source: str,
                         relation: str = "PART_OF") -> None:
    initialize()
    with _db() as conn:
        conn.execute(
            "INSERT INTO session_events VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (event_id, session_id, actor, event_type, statement, source, relation, _now()),
        )


def get_session_event(event_id: str) -> dict[str, Any] | None:
    initialize()
    with _db() as conn:
        row = conn.execute("SELECT * FROM session_events WHERE event_id=?",(event_id,)).fetchone()
    return dict(row) if row else None


def get_session(session_id: str) -> dict[str, Any] | None:
    initialize()
    with _db() as conn:
        session = conn.execute("SELECT * FROM sessions WHERE session_id=?",(session_id,)).fetchone()
        events = conn.execute("SELECT * FROM session_events WHERE session_id=? ORDER BY created_at",(session_id,)).fetchall()
    if session is None:
        return None
    result = dict(session)
    result["events"] = [dict(row) for row in events]
    return result


def create_memory_candidate(candidate: dict[str, Any]) -> None:
    initialize()
    with _db() as conn:
        conn.execute(
            """INSERT INTO memory_candidates
            (candidate_id,event_id,authority,record_type,scope,statement,source,owner,
             why_material,other_voices,tension,fingerprint,duplicate_of,status,created_at,promoted_record_id)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,NULL)""",
            (
                candidate["candidate_id"], candidate["event_id"], candidate["authority"],
                candidate["record_type"], candidate["scope"], candidate["statement"],
                candidate["source"], candidate["owner"], candidate["why_material"],
                json.dumps(candidate.get("other_voices", [])),
                candidate.get("tension", ""), candidate["fingerprint"],
                candidate.get("duplicate_of"), candidate["status"], candidate["created_at"],
            ),
        )


def get_memory_candidate(candidate_id: str) -> dict[str, Any] | None:
    initialize()
    with _db() as conn:
        row = conn.execute("SELECT * FROM memory_candidates WHERE candidate_id=?",(candidate_id,)).fetchone()
    if row is None:
        return None
    result = dict(row)
    result["other_voices"] = json.loads(result["other_voices"])
    return result


def list_memory_candidates(session_id: str | None = None, status: str | None = "CANDIDATE", limit: int = 50, subject: str | None = None) -> dict[str, Any]:
    """List bounded MemoryOS candidates, optionally restricted to one session."""
    initialize()
    limit = max(1, min(int(limit), 100))
    with _db() as conn:
        clauses = []
        params: list[Any] = []
        if session_id:
            clauses.append("e.session_id = ?")
            params.append(session_id)
        if status:
            clauses.append("c.status = ?")
            params.append(status)
        if subject:
            clauses.append("s.subject LIKE ?")
            params.append(f"%{subject}%")
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        rows = conn.execute(
            f"""SELECT c.*, e.session_id, s.subject
                FROM memory_candidates c
                JOIN session_events e ON e.event_id = c.event_id
                JOIN sessions s ON s.session_id = e.session_id
                {where}
                ORDER BY c.created_at DESC
                LIMIT ?""",
            (*params, limit),
        ).fetchall()
    candidates = []
    for row in rows:
        item = dict(row)
        item["other_voices"] = json.loads(item["other_voices"])
        candidates.append(item)
    return {
        "schema": "memconos.runtime.v2",
        "candidates": candidates,
        "count": len(candidates),
        "session_id": session_id,
        "subject_filter": subject,
        "status_filter": status,
        "runtime": SCHEMA_VERSION,
    }


def get_latest_memory_candidate(owner: str, status: str = "CANDIDATE") -> dict[str, Any] | None:
    initialize()
    with _db() as conn:
        row = conn.execute(
            "SELECT * FROM memory_candidates WHERE owner=? AND status=? ORDER BY created_at DESC LIMIT 1",
            (owner, status),
        ).fetchone()
    if row is None:
        return None
    result = dict(row)
    result["other_voices"] = json.loads(result["other_voices"])
    return result


def find_fingerprint(fingerprint: str) -> str | None:
    initialize()
    with _db() as conn:
        row = conn.execute(
            "SELECT record_id FROM memory_records WHERE lower(notes) LIKE ? LIMIT 1",
            (f'"fingerprint": "{fingerprint}"',),
        ).fetchone()
    return row["record_id"] if row else None


def mark_candidate(candidate_id: str, status: str, promoted_record_id: str | None = None) -> None:
    initialize()
    with _db() as conn:
        conn.execute(
            "UPDATE memory_candidates SET status=?, promoted_record_id=? WHERE candidate_id=?",
            (status, promoted_record_id, candidate_id),
        )


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
