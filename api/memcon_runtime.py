"""MemconOS durable runtime backend for MemoryOS and MemberContinuityOS."""
from __future__ import annotations

import json
import os
import sqlite3

try:
    import libsql
except ImportError:  # Local development may intentionally omit the remote driver.
    libsql = None
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path(os.getenv("MEMCONOS_DB_PATH", "/data/memconos.db"))
SCHEMA_VERSION = "memconos.runtime.v2"
BOOT_ID = "BOOT-" + uuid.uuid4().hex
RENDER_INSTANCE_ID = os.getenv("RENDER_INSTANCE_ID", "").strip()
TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL", "").strip()
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "").strip()
STORAGE_BACKEND = "turso_libsql" if TURSO_DATABASE_URL and TURSO_AUTH_TOKEN else "local_sqlite"

def _process_fingerprint() -> dict[str, Any]:
    """Return observable OS-level facts for the currently running carrier process."""
    pid = os.getpid()
    proc_start_ticks = None
    try:
        # Linux /proc/<pid>/stat field 22 is process start time in clock ticks
        # since system boot. It distinguishes PID reuse across process lifetimes.
        stat_fields = Path(f"/proc/{pid}/stat").read_text().split()
        proc_start_ticks = stat_fields[21] if len(stat_fields) > 21 else None
    except (OSError, IndexError):
        pass
    return {
        "pid": pid,
        "proc_start_ticks": proc_start_ticks,
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_dict(row: Any, cursor: Any = None) -> dict[str, Any] | None:
    if row is None:
        return None
    if hasattr(row, "keys"):
        return dict(row)
    description = getattr(cursor, "description", None)
    if description:
        return {str(col[0]): value for col, value in zip(description, row)}
    raise TypeError("Database row could not be mapped to column names")


def _db():
    """Open the configured storage backend.

    Turso is selected only when both remote credentials are present. Otherwise
    local SQLite remains available for development. Production callers can
    inspect storage_status() and must not describe local ephemeral storage as
    durable merely because it is writable.
    """
    if STORAGE_BACKEND == "turso_libsql":
        if libsql is None:
            raise RuntimeError("Turso credentials are configured but the libsql driver is unavailable")
        conn = libsql.connect(database=TURSO_DATABASE_URL, auth_token=TURSO_AUTH_TOKEN)
        conn.execute("PRAGMA foreign_keys=ON")
        return conn
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def storage_status() -> dict[str, Any]:
    """Return non-secret facts about the active memory storage backend."""
    return {
        "backend": STORAGE_BACKEND,
        "remote_configured": bool(TURSO_DATABASE_URL and TURSO_AUTH_TOKEN),
        "database_url_present": bool(TURSO_DATABASE_URL),
        "auth_token_present": bool(TURSO_AUTH_TOKEN),
        "local_path": str(DB_PATH) if STORAGE_BACKEND == "local_sqlite" else None,
        "claim_ceiling": (
            "Remote credentials are configured; durability still requires a post-restart canary PASS."
            if STORAGE_BACKEND == "turso_libsql"
            else "Local SQLite is writable but may be ephemeral on the current carrier."
        ),
    }


def _execute_script(conn, script: str) -> None:
    """Execute our simple semicolon-delimited schema on SQLite-compatible drivers."""
    for statement in script.split(";"):
        statement = statement.strip()
        if statement:
            conn.execute(statement)


def initialize() -> None:
    with _db() as conn:
        _execute_script(conn,
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
            CREATE TABLE IF NOT EXISTS solo_sessions (
                session_id TEXT PRIMARY KEY,
                daemon TEXT NOT NULL,
                source TEXT NOT NULL,
                created_at TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1
            );
            CREATE INDEX IF NOT EXISTS idx_solo_sessions_daemon ON solo_sessions(daemon);
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
    return {"record": get_record(record_id), "receipt": _receipt("WRITE", record_id, "SUCCESS", "Written to configured runtime store")}


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
    return {"record": get_record(record_id), "receipt": _receipt("UPDATE", record_id, "SUCCESS", "Updated in configured runtime store")}


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



def create_solo_session(session_id: str, daemon: str, source: str) -> dict[str, Any]:
    """Create or replace the active dedicated Prime Daemon session for one browser session."""
    initialize()
    daemon = daemon.strip().upper()
    with _db() as conn:
        conn.execute("UPDATE solo_sessions SET active=0 WHERE session_id=?", (session_id,))
        conn.execute(
            "INSERT OR REPLACE INTO solo_sessions(session_id,daemon,source,created_at,active) VALUES(?,?,?,?,1)",
            (session_id, daemon, source, _now()),
        )
    return get_solo_session(session_id)  # type: ignore[return-value]


def get_solo_session(session_id: str) -> dict[str, Any] | None:
    initialize()
    with _db() as conn:
        row = conn.execute(
            "SELECT * FROM solo_sessions WHERE session_id=? AND active=1",
            (session_id,),
        ).fetchone()
    return dict(row) if row else None


def end_solo_session(session_id: str) -> None:
    initialize()
    with _db() as conn:
        conn.execute("UPDATE solo_sessions SET active=0 WHERE session_id=?", (session_id,))



def restart_canary(token: str | None = None) -> dict[str, Any]:
    """Prove the durable runtime store survives a process restart."""
    initialize()
    marker_id = token.strip() if token else f"RESTART-{uuid.uuid4().hex}"
    if token is None:
        with _db() as conn:
            conn.execute(
                "INSERT INTO memory_records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    marker_id, "NAOMI", "RESTART_CANARY", "MemconOS",
                    "GaiaOS restart persistence canary",
                    "GaiaOS runtime restart verification",
                    "ACTIVE", "1", _now(), _now(), None,
                    json.dumps({"boot_id": BOOT_ID, "render_instance_id": RENDER_INSTANCE_ID, "process_fingerprint": _process_fingerprint()}),
                ),
            )
        return {
            "schema": SCHEMA_VERSION,
            "status": "ARMED",
            "token": marker_id,
            "boot_id": BOOT_ID,
            "render_instance_id": RENDER_INSTANCE_ID or None,
            "process_fingerprint": _process_fingerprint(),
            "instruction": "Restart or redeploy the service, then call /persistence/canary?token=<token>.",
            "proof_boundary": "Armed only. Persistence is not proven until the token is read after a different process boot.",
        }

    with _db() as conn:
        cursor = conn.execute(
            "SELECT notes, created_at FROM memory_records WHERE record_id=? AND record_type='RESTART_CANARY'",
            (marker_id,),
        )
        row = cursor.fetchone()
    if row is None:
        return {
            "schema": SCHEMA_VERSION,
            "status": "FAIL",
            "token": marker_id,
            "boot_id": BOOT_ID,
            "render_instance_id": RENDER_INSTANCE_ID or None,
            "process_fingerprint": _process_fingerprint(),
            "detail": "Restart canary marker was not found in the durable runtime store.",
        }
    saved = json.loads(_row_dict(row, cursor)["notes"])
    prior_boot = str(saved.get("boot_id", ""))
    prior_render_instance = str(saved.get("render_instance_id", ""))
    prior_process = saved.get("process_fingerprint") or {}
    current_process = _process_fingerprint()
    process_changed = bool(prior_process) and (
        prior_process.get("pid") != current_process.get("pid")
        or (
            prior_process.get("proc_start_ticks") is not None
            and current_process.get("proc_start_ticks") is not None
            and prior_process.get("proc_start_ticks") != current_process.get("proc_start_ticks")
        )
    )
    boot_changed = bool(prior_boot) and prior_boot != BOOT_ID
    render_instance_changed = bool(prior_render_instance) and bool(RENDER_INSTANCE_ID) and prior_render_instance != RENDER_INSTANCE_ID
    restarted = boot_changed or render_instance_changed or process_changed
    return {
        "schema": SCHEMA_VERSION,
        "status": "PASS" if restarted else "NOT_RESTARTED",
        "token": marker_id,
        "boot_id": BOOT_ID,
        "prior_boot_id": prior_boot,
        "render_instance_id": RENDER_INSTANCE_ID or None,
        "prior_render_instance_id": prior_render_instance or None,
        "boot_id_changed": boot_changed,
        "render_instance_changed": render_instance_changed,
        "process_fingerprint": current_process,
        "prior_process_fingerprint": prior_process or None,
        "process_fingerprint_changed": process_changed,
        "restart_predicate": "boot_id_changed OR render_instance_changed OR process_fingerprint_changed",
        "marker_created_at": _row_dict(row, cursor)["created_at"],
        "durable_read_observed": True,
        "different_process_boot_observed": restarted,
        "proof_boundary": "PASS proves the marker survived into a different carrier process identity. It does not prove every memory operation is automatically persisted.",
    }

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
        "runtime_store": storage_status(),
        "record": existing,
        "read_receipt": read_receipt,
        "runtime_persistence": True,
        "source_persistence": True,
        "claim_ceiling": "This proves the running service can durably read/write the runtime store. It does not prove automatic capture from every ChatGPT conversation.",
    }
