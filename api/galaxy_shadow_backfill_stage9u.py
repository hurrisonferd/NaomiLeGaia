"""GALAXY Stage 9U: receipt-backed shadow-gravity backfill, isolated SQLite ONLY.

Offline proof primitive. No MemconOS/libsql/Turso imports, HTTP route, production
writes, E-LANE changes, release activation, or real operator authentication.
A trusted caller must separately prove the preview source and signing key.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import math
import re
import sqlite3
from datetime import datetime, timezone
from typing import Any, Callable

SCHEMA = "gaiaos.galaxy.stage9u.shadow-backfill.v1"
APPROVAL_SCHEMA = "gaiaos.galaxy.stage9u.signed-batch.v1"
TARGET = "ISOLATED_SQLITE_IN_MEMORY_ONLY"
MAX_BATCH = 25
_HEX = re.compile(r"[0-9a-f]{64}\Z")
_BATCH_ID = re.compile(r"[A-Za-z0-9_.:-]{8,100}\Z")
GRAVITY_COLS = (
    "record_id", "gravity_score", "score_version", "components_json",
    "reason_json", "calculated_at", "previous_score",
)


def _json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_json(value)).hexdigest()


def _hold(reason: str, *, error_type: str | None = None) -> dict[str, Any]:
    result = {
        "schema": SCHEMA, "status": reason,
        "target": TARGET, "production_writes": False,
        "production_retrieval_changed": False, "mode_control_modified": False,
        "memory_records_modified": False, "e_lanes_modified": False,
        "owner_live_authorization_proven": False, "writes_performed": [],
    }
    if error_type:
        result["error_type"] = error_type
    return result


def _isolated(conn: Any) -> bool:
    if type(conn) is not sqlite3.Connection or conn.in_transaction:
        return False
    try:
        dbs = conn.execute("PRAGMA database_list").fetchall()
        return len(dbs) == 1 and dbs[0][1] == "main" and dbs[0][2] == ""
    except (sqlite3.Error, IndexError, TypeError):
        return False


def _one(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> dict | None:
    cursor = conn.execute(sql, params)
    row = cursor.fetchone()
    return dict(zip((col[0] for col in cursor.description), row)) if row else None


def _all(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list[dict]:
    cursor = conn.execute(sql, params)
    cols = [col[0] for col in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def _source_snapshot(conn: sqlite3.Connection, rid: str) -> tuple[str, dict]:
    record = _one(conn, "SELECT * FROM memory_records WHERE record_id=?", (rid,))
    if record is None or record.get("scope") != "MemoryOS":
        raise ValueError("missing or non-MemoryOS record")
    if record.get("status") == "STAGED_HISTORICAL_HOLD":
        raise ValueError("unverified imported history not backfill eligible")
    # Includes non-verified edges, so proposal->VERIFIED changes invalidate a plan.
    relations = _all(
        conn, "SELECT * FROM memory_relations "
        "WHERE source_record_id=? OR target_record_id=? ORDER BY edge_id",
        (rid, rid),
    )
    importance = _one(conn, "SELECT * FROM memory_importance WHERE record_id=?", (rid,))
    lifecycle = _one(conn, "SELECT * FROM memory_lifecycle WHERE record_id=?", (rid,))
    lifecycle_events = _all(
        conn, "SELECT * FROM memory_lifecycle_events "
        "WHERE record_id=? ORDER BY event_id", (rid,),
    )
    source = {
        "record": record, "relations": relations, "importance": importance,
        "lifecycle": lifecycle, "lifecycle_events": lifecycle_events,
    }
    return _sha(source), source


def _gravity(conn: sqlite3.Connection, rid: str) -> dict | None:
    return _one(
        conn, "SELECT record_id,gravity_score,score_version,components_json,"
        "reason_json,calculated_at,previous_score "
        "FROM memory_gravity WHERE record_id=?", (rid,),
    )


def _valid_preview(preview: Any, rid: str, model: str) -> bool:
    if not isinstance(preview, dict):
        return False
    score = preview.get("gravity_score")
    if (
        preview.get("record_id") != rid or preview.get("score_version") != model
        or isinstance(score, bool) or not isinstance(score, (int, float))
        or not math.isfinite(score) or not 0.0 <= score <= 1.0
        or not isinstance(preview.get("components"), dict)
        or not isinstance(preview.get("reason"), dict)
    ):
        return False
    try:
        return len(_json(preview["components"])) <= 65536 and len(_json(preview["reason"])) <= 65536
    except (TypeError, ValueError, OverflowError):
        return False


def make_shadow_plan(
    conn: sqlite3.Connection, *,
    record_ids: list[str], score_version: str,
    preview: Callable[[str], dict],
) -> dict:
    """Read-only plan for one bounded MemoryOS batch. Never calculates owner intent."""
    if not _isolated(conn):
        return _hold("HOLD_NOT_ISOLATED_IN_MEMORY_SQLITE")
    if (
        not isinstance(record_ids, list) or not 1 <= len(record_ids) <= MAX_BATCH
        or any(not isinstance(rid, str) or not 1 <= len(rid) <= 200 for rid in record_ids)
        or len(set(record_ids)) != len(record_ids)
        or not isinstance(score_version, str) or not 1 <= len(score_version) <= 120
        or not callable(preview)
    ):
        return _hold("HOLD_PLAN_ARGUMENTS")
    before = conn.total_changes
    entries = []
    try:
        for rid in record_ids:
            old_source_sha, source = _source_snapshot(conn, rid)
            old = _gravity(conn, rid)
            # Already CURRENT is intentionally untouched; inspect it without replacing.
            if old and old["score_version"] == score_version:
                score = old["gravity_score"]
                if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score) or not 0 <= score <= 1:
                    return _hold("HOLD_INVALID_CURRENT_SCORE")
                entries.append({
                    "record_id": rid, "action": "SKIP_CURRENT",
                    "source_snapshot_sha256": old_source_sha,
                    "old_gravity_sha256": _sha(old),
                    "owner_importance_status": "OWNER_SET" if source["importance"] else "UNSET_NOT_ZERO",
                })
                continue
            candidate = preview(rid)
            if conn.total_changes != before or conn.in_transaction:
                # Source-only harness cannot certify callbacks with side effects.
                if conn.in_transaction:
                    conn.rollback()
                return _hold("HOLD_PREVIEW_CALLBACK_WROTE")
            after_sha, _ = _source_snapshot(conn, rid)
            if after_sha != old_source_sha or _gravity(conn, rid) != old:
                return _hold("HOLD_SOURCE_DRIFT_DURING_PREVIEW")
            if not _valid_preview(candidate, rid, score_version):
                return _hold("HOLD_PREVIEW_INVALID")
            entries.append({
                "record_id": rid, "action": "UPSERT_SHADOW",
                "source_snapshot_sha256": old_source_sha,
                "old_gravity_sha256": _sha(old) if old is not None else None,
                "owner_importance_status": "OWNER_SET" if source["importance"] else "UNSET_NOT_ZERO",
                "preview": {
                    "gravity_score": float(candidate["gravity_score"]),
                    "score_version": score_version, "components": candidate["components"],
                    "reason": candidate["reason"],
                },
            })
        if conn.total_changes != before or conn.in_transaction:
            return _hold("HOLD_READ_ONLY_INVARIANT")
        plan = {
            "schema": SCHEMA, "target": TARGET,
            "score_version": score_version, "entries": entries,
        }
        return {
            **_hold("PASS_READ_ONLY_PLAN"), "plan": plan,
            "plan_sha256": _sha(plan), "count": len(entries),
            "pending_count": sum(x["action"] == "UPSERT_SHADOW" for x in entries),
            "owner_importance_unset_count": sum(x["owner_importance_status"] == "UNSET_NOT_ZERO" for x in entries),
            "preview_model_bound_to_staging_verified": False,
        }
    except Exception as exc:
        if conn.in_transaction:
            conn.rollback()
        return _hold("HOLD_PLAN_FAILED", error_type=type(exc).__name__)


def _verify_approval(
    manifest: Any, signature_hex: Any, approval_key: Any,
    *, action: str, batch_id: str, plan_sha: str,
) -> bool:
    if not isinstance(manifest, dict) or set(manifest) != {
        "schema", "authority", "target", "action", "batch_id", "plan_sha256",
    }:
        return False
    if (
        not isinstance(approval_key, bytes) or len(approval_key) < 32
        or not isinstance(signature_hex, str) or _HEX.fullmatch(signature_hex) is None
        or manifest != {
            "schema": APPROVAL_SCHEMA, "authority": "NAOMI",
            "target": TARGET, "action": action,
            "batch_id": batch_id, "plan_sha256": plan_sha,
        }
    ):
        return False
    try:
        expected = hmac.new(approval_key, _json(manifest), hashlib.sha256).hexdigest()
    except (TypeError, ValueError):
        return False
    return hmac.compare_digest(expected, signature_hex)


def _ledger(conn: sqlite3.Connection) -> None:
    conn.execute("""CREATE TABLE IF NOT EXISTS galaxy_stage9u_batches (
        batch_id TEXT PRIMARY KEY, plan_sha256 TEXT NOT NULL,
        status TEXT NOT NULL, receipt_json TEXT NOT NULL,
        created_at TEXT NOT NULL, rolled_back_at TEXT
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS galaxy_stage9u_item_ledger (
        batch_id TEXT NOT NULL, record_id TEXT NOT NULL,
        source_snapshot_sha256 TEXT NOT NULL,
        old_gravity_json TEXT, new_gravity_sha256 TEXT,
        action TEXT NOT NULL, PRIMARY KEY (batch_id, record_id)
    )""")


def _plan_shape(plan: Any) -> bool:
    if (
        not isinstance(plan, dict) or set(plan) != {"schema", "target", "score_version", "entries"}
        or plan["schema"] != SCHEMA or plan["target"] != TARGET
        or not isinstance(plan["score_version"], str)
        or not 1 <= len(plan["score_version"]) <= 120
        or not isinstance(plan["entries"], list)
        or not 1 <= len(plan["entries"]) <= MAX_BATCH
    ):
        return False
    seen = set()
    for item in plan["entries"]:
        if not isinstance(item, dict) or not isinstance(item.get("record_id"), str):
            return False
        rid = item["record_id"]
        if rid in seen or not 1 <= len(rid) <= 200:
            return False
        seen.add(rid)
        if (
            item.get("action") not in ("SKIP_CURRENT", "UPSERT_SHADOW")
            or not isinstance(item.get("source_snapshot_sha256"), str)
            or _HEX.fullmatch(item["source_snapshot_sha256"]) is None
            or item.get("owner_importance_status") not in ("OWNER_SET", "UNSET_NOT_ZERO")
        ):
            return False
        old_hash = item.get("old_gravity_sha256")
        if old_hash is not None and (not isinstance(old_hash, str) or _HEX.fullmatch(old_hash) is None):
            return False
        if item["action"] == "UPSERT_SHADOW":
            candidate = item.get("preview")
            if not isinstance(candidate, dict) or set(candidate) != {
                "gravity_score", "score_version", "components", "reason",
            }:
                return False
            if not _valid_preview({**candidate, "record_id": rid}, rid, plan["score_version"]):
                return False
        elif old_hash is None or "preview" in item:
            return False
    try:
        return len(_json(plan)) <= 1_000_000
    except (TypeError, ValueError, OverflowError):
        return False


def apply_shadow_plan(
    conn: sqlite3.Connection, *,
    plan: dict, batch_id: str, approval: dict,
    signature_hex: str, approval_key: bytes,
) -> dict:
    """Atomic source-CAS backfill of *in-memory* memory_gravity with per-item ledger."""
    if not _isolated(conn):
        return _hold("HOLD_NOT_ISOLATED_IN_MEMORY_SQLITE")
    if not _plan_shape(plan):
        return _hold("HOLD_INVALID_PLAN")
    if not isinstance(batch_id, str) or _BATCH_ID.fullmatch(batch_id) is None:
        return _hold("HOLD_BATCH_ID")
    plan_sha = _sha(plan)
    if not _verify_approval(
        approval, signature_hex, approval_key,
        action="APPLY", batch_id=batch_id, plan_sha=plan_sha,
    ):
        return _hold("HOLD_SIGNED_APPROVAL_REQUIRED")
    try:
        conn.execute("BEGIN IMMEDIATE")
        _ledger(conn)
        existing = _one(
            conn, "SELECT plan_sha256,status,receipt_json "
            "FROM galaxy_stage9u_batches WHERE batch_id=?", (batch_id,),
        )
        if existing is not None:
            if existing["plan_sha256"] != plan_sha:
                conn.rollback()
                return _hold("HOLD_BATCH_ID_COLLISION")
            if existing["status"] != "APPLIED":
                conn.rollback()
                return _hold("HOLD_BATCH_ALREADY_ROLLED_BACK")
            for item in plan["entries"]:
                ledger = _one(
                    conn, "SELECT new_gravity_sha256 FROM galaxy_stage9u_item_ledger "
                    "WHERE batch_id=? AND record_id=?",
                    (batch_id, item["record_id"]),
                )
                if ledger is None or _sha(_gravity(conn, item["record_id"])) != ledger["new_gravity_sha256"]:
                    conn.rollback()
                    return _hold("HOLD_REPLAY_DRIFT")
                # A matching score alone is not proof that the original facts,
                # owner importance or governing context remained unchanged.
                source_hash, _ = _source_snapshot(conn, item["record_id"])
                if source_hash != item["source_snapshot_sha256"]:
                    conn.rollback()
                    return _hold("HOLD_REPLAY_SOURCE_DRIFT")
            conn.commit()
            return {
                **_hold("PASS_REPLAY_VERIFIED"), "idempotent": True,
                "receipt": json.loads(existing["receipt_json"]),
            }

        # All-or-nothing compare-before-write. Includes verified edges, lifecycle
        # and owner importance to reject an out-of-date gravity preview.
        old_rows = {}
        for item in plan["entries"]:
            rid = item["record_id"]
            actual_sha, source = _source_snapshot(conn, rid)
            old = _gravity(conn, rid)
            old_hash = _sha(old) if old is not None else None
            importance = "OWNER_SET" if source["importance"] else "UNSET_NOT_ZERO"
            if (
                actual_sha != item["source_snapshot_sha256"]
                or old_hash != item["old_gravity_sha256"]
                or importance != item["owner_importance_status"]
            ):
                conn.rollback()
                return _hold("HOLD_SOURCE_OR_SCORE_DRIFT")
            if item["action"] == "SKIP_CURRENT" and old["score_version"] != plan["score_version"]:
                conn.rollback()
                return _hold("HOLD_CURRENT_VERSION_CHANGED")
            old_rows[rid] = old
        # One score model version per batch; records never change scope or status.
        now = datetime.now(timezone.utc).isoformat()
        receipt_items = []
        for item in plan["entries"]:
            rid = item["record_id"]
            old = old_rows[rid]
            outcome = item["action"]
            if outcome == "UPSERT_SHADOW":
                candidate = item["preview"]
                new_values = (
                    candidate["gravity_score"], candidate["score_version"],
                    _json(candidate["components"]).decode("utf-8"),
                    _json(candidate["reason"]).decode("utf-8"), now,
                    old["gravity_score"] if old else None,
                )
                if old is None:
                    conn.execute(
                        "INSERT INTO memory_gravity "
                        "(record_id,gravity_score,score_version,components_json,"
                        "reason_json,calculated_at,previous_score) VALUES (?,?,?,?,?,?,?)",
                        (rid, *new_values),
                    )
                    outcome = "INSERTED_SHADOW"
                else:
                    conn.execute(
                        "UPDATE memory_gravity SET gravity_score=?,score_version=?,"
                        "components_json=?,reason_json=?,calculated_at=?,previous_score=? "
                        "WHERE record_id=?", (*new_values, rid),
                    )
                    outcome = "UPDATED_SHADOW"
            new_row = _gravity(conn, rid)
            if new_row is None:
                raise ValueError("readback missing")
            if item["action"] == "UPSERT_SHADOW" and (
                new_row["gravity_score"] != item["preview"]["gravity_score"]
                or new_row["score_version"] != plan["score_version"]
                or new_row["components_json"] != _json(item["preview"]["components"]).decode("utf-8")
                or new_row["reason_json"] != _json(item["preview"]["reason"]).decode("utf-8")
            ):
                raise ValueError("staging backfill readback mismatch")
            new_hash = _sha(new_row)
            conn.execute(
                "INSERT INTO galaxy_stage9u_item_ledger "
                "(batch_id,record_id,source_snapshot_sha256,old_gravity_json,"
                "new_gravity_sha256,action) VALUES (?,?,?,?,?,?)",
                (
                    batch_id, rid, item["source_snapshot_sha256"],
                    _json(old).decode("utf-8") if old is not None else None,
                    new_hash, outcome,
                ),
            )
            receipt_items.append({
                "record_id": rid, "action": outcome,
                "previous_gravity_sha256": item["old_gravity_sha256"],
                "new_gravity_sha256": new_hash,
                "source_snapshot_sha256": item["source_snapshot_sha256"],
                "owner_importance_status": item["owner_importance_status"],
            })
        receipt = {
            "schema": SCHEMA, "batch_id": batch_id, "plan_sha256": plan_sha,
            "target": TARGET, "score_version": plan["score_version"],
            "created_at": now, "items": receipt_items,
            "model_callback_production_proven": False,
            "real_owner_identity_verified": False, "live_turso_written": False,
            "readback_verified_in_memory": True,
        }
        receipt["receipt_sha256"] = _sha(receipt)
        conn.execute(
            "INSERT INTO galaxy_stage9u_batches "
            "(batch_id,plan_sha256,status,receipt_json,created_at,rolled_back_at)"
            " VALUES (?,?,?,?,?,NULL)",
            (batch_id, plan_sha, "APPLIED", _json(receipt).decode("utf-8"), now),
        )
        conn.commit()
        return {
            **_hold("PASS_IN_MEMORY_BACKFILL_READBACK"),
            "idempotent": False, "receipt": receipt,
            "writes_performed": ["ISOLATED_GRAVITY_ROWS", "ISOLATED_APPEND_ONLY_LEDGER"],
        }
    except Exception as exc:
        if conn.in_transaction:
            conn.rollback()
        return _hold("HOLD_BACKFILL_FAILED", error_type=type(exc).__name__)


def rollback_shadow_batch(
    conn: sqlite3.Connection, *,
    batch_id: str, plan_sha256: str, approval: dict,
    signature_hex: str, approval_key: bytes,
) -> dict:
    """Restore exact old gravity rows only if current rows match our written hashes."""
    if not _isolated(conn):
        return _hold("HOLD_NOT_ISOLATED_IN_MEMORY_SQLITE")
    if (
        not isinstance(batch_id, str) or _BATCH_ID.fullmatch(batch_id) is None
        or not isinstance(plan_sha256, str) or _HEX.fullmatch(plan_sha256) is None
        or not _verify_approval(
            approval, signature_hex, approval_key,
            action="ROLLBACK", batch_id=batch_id, plan_sha=plan_sha256,
        )
    ):
        return _hold("HOLD_SIGNED_ROLLBACK_REQUIRED")
    try:
        conn.execute("BEGIN IMMEDIATE")
        batch = _one(
            conn, "SELECT * FROM galaxy_stage9u_batches WHERE batch_id=?",
            (batch_id,),
        )
        if batch is None or batch["plan_sha256"] != plan_sha256:
            conn.rollback()
            return _hold("HOLD_UNKNOWN_OR_CONFLICTING_BATCH")
        if batch["status"] == "ROLLED_BACK":
            # A replayed rollback is only verified if every restored old score
            # (including old absence) still matches the immutable ledger.
            restored_ledger = _all(
                conn, "SELECT record_id,old_gravity_json FROM galaxy_stage9u_item_ledger "
                "WHERE batch_id=?", (batch_id,),
            )
            expected_items = json.loads(batch["receipt_json"])["items"]
            if len(restored_ledger) != len(expected_items):
                conn.rollback()
                return _hold("HOLD_ROLLBACK_REPLAY_LEDGER_INCOMPLETE")
            for saved in restored_ledger:
                original = json.loads(saved["old_gravity_json"]) if saved["old_gravity_json"] else None
                if _sha(_gravity(conn, saved["record_id"])) != _sha(original):
                    conn.rollback()
                    return _hold("HOLD_ROLLBACK_REPLAY_DRIFT")
            conn.commit()
            return {**_hold("PASS_ALREADY_ROLLED_BACK"), "idempotent": True}
        entries = _all(
            conn, "SELECT * FROM galaxy_stage9u_item_ledger "
            "WHERE batch_id=? ORDER BY record_id", (batch_id,),
        )
        receipt = json.loads(batch["receipt_json"])
        if len(entries) != len(receipt["items"]):
            conn.rollback()
            return _hold("HOLD_INCOMPLETE_ROLLBACK_LEDGER")
        for item in entries:
            current = _gravity(conn, item["record_id"])
            if _sha(current) != item["new_gravity_sha256"]:
                conn.rollback()
                return _hold("HOLD_ROLLBACK_SCORE_DRIFT")
        for item in entries:
            old_json = item["old_gravity_json"]
            if item["action"] == "SKIP_CURRENT":
                continue
            if old_json is None:
                conn.execute(
                    "DELETE FROM memory_gravity WHERE record_id=?",
                    (item["record_id"],),
                )
            else:
                old = json.loads(old_json)
                conn.execute(
                    "UPDATE memory_gravity SET gravity_score=?,score_version=?,"
                    "components_json=?,reason_json=?,calculated_at=?,previous_score=? "
                    "WHERE record_id=?",
                    tuple(old[col] for col in GRAVITY_COLS[1:]) + (old["record_id"],),
                )
            restored = _gravity(conn, item["record_id"])
            if _sha(restored) != _sha(json.loads(old_json) if old_json else None):
                raise ValueError("rollback readback mismatch")
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "UPDATE galaxy_stage9u_batches SET status='ROLLED_BACK',rolled_back_at=? "
            "WHERE batch_id=?", (now, batch_id),
        )
        conn.commit()
        return {
            **_hold("PASS_IN_MEMORY_ROLLBACK_READBACK"),
            "writes_performed": ["ISOLATED_GRAVITY_RESTORATION", "ISOLATED_BATCH_ROLLBACK_MARK"],
            "restored_count": sum(item["action"] != "SKIP_CURRENT" for item in entries),
        }
    except Exception as exc:
        if conn.in_transaction:
            conn.rollback()
        return _hold("HOLD_ROLLBACK_FAILED", error_type=type(exc).__name__)
