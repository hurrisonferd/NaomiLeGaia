"""GALAXY Stage 9Z: exact signed rollback of Stage 9Y LOCAL fixture rows.

Native SQLite fixture only; no libSQL, production runtime, external connector,
HTTP route or implicit schema creation. These fixture HMAC keys do not establish
Naomi's real identity or approve any actual remote staging/production mutation.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import galaxy_stage9y_canonical_staging as y

SCHEMA = "gaiaos.galaxy.stage9z.signed-fixture-rollback.v1"
APPROVAL_SCHEMA = "gaiaos.galaxy.stage9z.rollback-approval.v1"
TARGET = "LOCAL_CANONICAL_STAGING_ROLLBACK_FIXTURE_ONLY"
ROLLED_BACK = "ROLLED_BACK_LOCAL_FIXTURE"
_HEX = re.compile(r"[0-9a-f]{64}\Z")
_ID = re.compile(r"[A-Za-z0-9_.:-]{8,100}\Z")
LEDGER_COLS = (
    "rollback_id", "import_approval_id", "rollback_manifest_sha256",
    "import_receipt_sha256", "receipt_json", "receipt_hmac_sha256",
    "status", "created_at",
)
ALLOWED_TABLES = frozenset((
    "memory_records", "galaxy_stage9v_staging_identity",
    "galaxy_stage9v_canaries", "galaxy_stage9y_batches",
    "galaxy_stage9y_items", "galaxy_stage9z_rollbacks",
))


def _hold(status: str, *, uncertain: bool = False,
          error_type: str | None = None) -> dict[str, Any]:
    result = {
        "schema": SCHEMA, "status": status, "target": TARGET,
        "remote_turso_accessed": False, "production_accessed": False,
        "production_modified": False, "gravity_modified": False,
        "e_lanes_modified": False, "mode_control_modified": False,
        "bigbang_activated": False, "live_owner_identity_verified": False,
        "provider_database_separation_verified": False,
        "writes_performed": (
            ["LOCAL_FIXTURE_ROLLBACK_OUTCOME_UNVERIFIED"] if uncertain else []
        ),
        "proof_boundary": (
            "Local native SQLite fixture only. Test-key signatures are not "
            "live owner authentication. No remote rollback/restart proven."
        ),
    }
    if error_type is not None:
        result["error_type"] = error_type
    return result


def _protected_schema(conn: sqlite3.Connection) -> bool:
    """Reject unknown tables, triggers and views to prevent hidden references."""
    try:
        objects = conn.execute(
            "SELECT type,name FROM sqlite_master "
            "WHERE type IN ('table','view','trigger')"
        ).fetchall()
        actual = set()
        for kind, name in objects:
            if name.startswith("sqlite_"):
                continue
            if kind != "table" or name not in ALLOWED_TABLES:
                return False
            actual.add(name)
        if actual != ALLOWED_TABLES:
            return False
        cursor = conn.execute(
            f"SELECT {','.join(LEDGER_COLS)} FROM galaxy_stage9z_rollbacks LIMIT 0"
        )
        return tuple(col[0] for col in cursor.description) == LEDGER_COLS
    except (sqlite3.Error, TypeError, ValueError):
        return False


def _items(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "index": entry["index"],
            "proposed_record_id": entry["record_id"],
            "source_key_sha256": entry["source_key_sha256"],
            "statement_sha256": entry["statement_sha256"],
            "metadata_sha256": entry["metadata_sha256"],
        }
        for entry in receipt["items"]
    ]


def _original_signed(
    original_manifest: Any, original_signature: Any, original_key: Any,
    config: dict[str, str], batch: dict[str, Any], receipt: dict[str, Any],
) -> bool:
    try:
        if (not isinstance(original_manifest, dict)
                or not isinstance(original_key, bytes) or len(original_key) < 32
                or not isinstance(receipt, dict)
                or receipt["schema"] != y.SCHEMA
                or receipt["target"] != y.TARGET
                or receipt["historical_status"] != y.STATUS
                or receipt["approval_id"] != batch["approval_id"]
                or receipt["manifest_sha256"] != batch["manifest_sha256"]
                or receipt["export_sha256"] != batch["export_sha256"]
                or receipt["source_sha256"] != batch["source_sha256"]
                or receipt["canary_sha256"] != batch["canary_sha256"]
                or batch["receipt_json"] != y._bytes(receipt).decode("utf-8")
                or receipt["receipt_sha256"] != y._sha(y._bytes({
                    k: v for k, v in receipt.items() if k != "receipt_sha256"
                }))
                or not hmac.compare_digest(
                    batch["receipt_hmac_sha256"],
                    hmac.new(original_key, y._bytes(receipt),
                             hashlib.sha256).hexdigest(),
                )):
            return False
        items = _items(receipt)
        if not 1 <= len(items) <= y.BATCH_CAP:
            return False
        if any(item["index"] != i for i, item in enumerate(items)):
            return False
        expected = y._expected_manifest(
            config=config, approval=original_manifest,
            export_hash=receipt["export_sha256"],
            source_hash=receipt["source_sha256"], items=items,
        )
        return (
            expected is not None
            and y._signed_exact(
                original_manifest, original_signature, original_key, expected
            )
            and receipt["manifest_sha256"] == y._sha(y._bytes(expected))
            and receipt["approval_id"] == expected["approval_id"]
        )
    except (KeyError, TypeError, ValueError, OverflowError):
        return False


def expected_rollback_manifest(
    *, original_manifest: dict[str, Any], original_receipt: dict[str, Any],
    rollback_id: str,
) -> dict[str, Any]:
    """Build exact expected approval for a separately held LOCAL fixture key."""
    return {
        "schema": APPROVAL_SCHEMA, "authority": "NAOMI",
        "target": TARGET, "action": "ROLLBACK_NEW_LOCAL_HISTORICAL_ROWS",
        "rollback_id": rollback_id,
        "import_approval_id": original_receipt["approval_id"],
        "import_manifest_sha256": original_receipt["manifest_sha256"],
        "import_receipt_sha256": original_receipt["receipt_sha256"],
        "staging_url_sha256": original_manifest["staging_url_sha256"],
        "production_url_sha256": original_manifest["production_url_sha256"],
        "staging_uuid": original_manifest["expected_staging_id"],
        "canary_run_id": original_manifest["canary_run_id"],
        "canary_sha256": original_receipt["canary_sha256"],
        "rows": [
            {
                "record_id": item["record_id"],
                "row_sha256": item["row_sha256"],
                "source_key_sha256": item["source_key_sha256"],
            }
            for item in original_receipt["items"]
        ],
    }


def _check_deleted(
    conn: sqlite3.Connection, batch: dict[str, Any],
    original_receipt: dict[str, Any], rollback_receipt: dict[str, Any],
    rollback_key: bytes,
) -> bool:
    """Check exact post-image and immutable, signed receipt/history ledgers."""
    try:
        saved = y._row(conn.execute(
            f"SELECT {','.join(LEDGER_COLS)} FROM galaxy_stage9z_rollbacks "
            "WHERE rollback_id=?", (rollback_receipt["rollback_id"],),
        ))
        current = y._row(conn.execute(
            f"SELECT {','.join(y.BATCH_COLS)} FROM galaxy_stage9y_batches "
            "WHERE approval_id=?", (batch["approval_id"],),
        ))
        if (saved is None or current is None
                or saved["import_approval_id"] != batch["approval_id"]
                or saved["rollback_manifest_sha256"] != rollback_receipt["manifest_sha256"]
                or saved["import_receipt_sha256"] != original_receipt["receipt_sha256"]
                or saved["status"] != ROLLED_BACK
                or saved["receipt_json"] != y._bytes(rollback_receipt).decode("utf-8")
                or not hmac.compare_digest(
                    saved["receipt_hmac_sha256"],
                    hmac.new(rollback_key, y._bytes(rollback_receipt),
                             hashlib.sha256).hexdigest(),
                )
                or rollback_receipt["receipt_sha256"] != y._sha(y._bytes({
                    k: v for k, v in rollback_receipt.items()
                    if k != "receipt_sha256"
                }))
                or current["status"] != ROLLED_BACK
                or any(current[col] != batch[col]
                       for col in y.BATCH_COLS if col != "status")):
            return False
        if rollback_receipt["deleted_new_fixture_rows"] != len(original_receipt["items"]):
            return False
        for entry in original_receipt["items"]:
            if y._stored_record(conn, entry["record_id"]) is not None:
                return False
            # Another row with the same source would silently resurrect it.
            if y._row(conn.execute(
                "SELECT record_id FROM memory_records WHERE source=? LIMIT 1",
                ("galaxy-archive-v1:" + entry["source_key_sha256"],),
            )) is not None:
                return False
            item = y._row(conn.execute(
                f"SELECT {','.join(y.ITEM_COLS)} FROM galaxy_stage9y_items "
                "WHERE receipt_id=?", (entry["receipt_id"],),
            ))
            if (item is None or item["approval_id"] != batch["approval_id"]
                    or item["record_id"] != entry["record_id"]
                    or item["source_key_sha256"] != entry["source_key_sha256"]
                    or item["statement_sha256"] != entry["statement_sha256"]
                    or item["metadata_sha256"] != entry["metadata_sha256"]
                    or item["row_sha256"] != entry["row_sha256"]
                    or item["result"] != "INSERTED_LOCAL_FIXTURE"):
                return False
        return True
    except (sqlite3.Error, KeyError, TypeError, ValueError, OverflowError):
        return False


def rollback_local_import(
    *, fixture_connection: sqlite3.Connection, fixture_root: str | Path,
    config: dict[str, str], original_manifest: dict[str, Any],
    original_signature: str, original_key: bytes,
    rollback_manifest: dict[str, Any], rollback_signature: str,
    rollback_key: bytes, confirm_exact_rollback: bool,
    confirm_no_live_target: bool, confirm_retained_ledger: bool,
) -> dict[str, Any]:
    """Rollback solely new, unchanged Stage 9Y fixture rows, retain all proof."""
    if not all((confirm_exact_rollback, confirm_no_live_target,
                confirm_retained_ledger)):
        return _hold("HOLD_EXPLICIT_SEPARATE_ROLLBACK_REVIEW_REQUIRED")
    path = y._fixture_path(fixture_connection, fixture_root)
    if path is None:
        return _hold("HOLD_NOT_ISOLATED_NATIVE_SQLITE_FIXTURE")
    conn = fixture_connection
    if not _protected_schema(conn):
        return _hold("HOLD_UNKNOWN_DEPENDENCIES_OR_LEDGER_SCHEMA")
    if (not isinstance(original_manifest, dict)
            or not isinstance(rollback_manifest, dict)
            or not isinstance(original_key, bytes)
            or not isinstance(rollback_key, bytes)
            or len(original_key) < 32 or len(rollback_key) < 32
            or hmac.compare_digest(original_key, rollback_key)):
        return _hold("HOLD_INDEPENDENT_ROLLBACK_SIGNATURE_REQUIRED")
    import_id = original_manifest.get("approval_id")
    rollback_id = rollback_manifest.get("rollback_id")
    if (not isinstance(import_id, str) or _ID.fullmatch(import_id) is None
            or not isinstance(rollback_id, str)
            or _ID.fullmatch(rollback_id) is None):
        return _hold("HOLD_APPROVAL_ID_INVALID")
    try:
        batch = y._row(conn.execute(
            f"SELECT {','.join(y.BATCH_COLS)} FROM galaxy_stage9y_batches "
            "WHERE approval_id=?", (import_id,),
        ))
    except sqlite3.Error:
        return _hold("HOLD_IMPORT_LEDGER_NOT_READABLE")
    if batch is None:
        return _hold("HOLD_ORIGINAL_IMPORT_NOT_FOUND")
    try:
        receipt = json.loads(batch["receipt_json"])
    except (TypeError, ValueError):
        return _hold("HOLD_ORIGINAL_RECEIPT_INVALID")
    if not _original_signed(
        original_manifest, original_signature, original_key,
        config, batch, receipt,
    ):
        return _hold("HOLD_ORIGINAL_IMPORT_SIGNATURE_OR_RECEIPT_INVALID")
    try:
        expected = expected_rollback_manifest(
            original_manifest=original_manifest, original_receipt=receipt,
            rollback_id=rollback_id,
        )
    except (KeyError, TypeError, ValueError):
        return _hold("HOLD_ROLLBACK_APPROVAL_SHAPE_INVALID")
    if not y._signed_exact(
        rollback_manifest, rollback_signature, rollback_key, expected
    ):
        return _hold("HOLD_EXACT_SIGNED_ROLLBACK_ACTION_REQUIRED")
    if not y._schema_and_identity(
        conn, original_manifest["expected_staging_id"],
        original_manifest["canary_run_id"],
        original_manifest["canary_sha256"],
    ):
        return _hold("HOLD_MARKER_OR_CANARY_CHANGED")

    started = False
    replay = False
    rollback_receipt: dict[str, Any] | None = None
    try:
        conn.execute("BEGIN IMMEDIATE")
        if (not _protected_schema(conn)
                or not y._schema_and_identity(
                    conn, original_manifest["expected_staging_id"],
                    original_manifest["canary_run_id"],
                    original_manifest["canary_sha256"],
                )):
            conn.rollback()
            return _hold("HOLD_SCHEMA_OR_IDENTITY_CHANGED")
        current = y._row(conn.execute(
            f"SELECT {','.join(y.BATCH_COLS)} FROM galaxy_stage9y_batches "
            "WHERE approval_id=?", (import_id,),
        ))
        if current != batch:
            conn.rollback()
            return _hold("HOLD_ORIGINAL_IMPORT_CHANGED")
        prev = y._rows(conn.execute(
            f"SELECT {','.join(LEDGER_COLS)} FROM galaxy_stage9z_rollbacks "
            "WHERE rollback_id=? OR import_approval_id=? LIMIT 2",
            (rollback_id, import_id),
        ))
        if prev:
            if (len(prev) != 1 or prev[0]["rollback_id"] != rollback_id
                    or prev[0]["import_approval_id"] != import_id
                    or prev[0]["rollback_manifest_sha256"] != y._sha(y._bytes(expected))
                    or batch["status"] != ROLLED_BACK):
                conn.rollback()
                return _hold("HOLD_ROLLBACK_APPROVAL_COLLISION")
            try:
                rollback_receipt = json.loads(prev[0]["receipt_json"])
            except (TypeError, ValueError):
                conn.rollback()
                return _hold("HOLD_ROLLBACK_LEDGER_INVALID")
            if not _check_deleted(conn, batch, receipt, rollback_receipt, rollback_key):
                conn.rollback()
                return _hold("HOLD_ROLLBACK_REPLAY_DRIFT")
            conn.rollback()
            replay = True
        else:
            if batch["status"] != y.STATUS:
                conn.rollback()
                return _hold("HOLD_ORIGINAL_BATCH_NOT_STAGED")
            items = receipt.get("items")
            if (not isinstance(items, list)
                    or any(entry.get("result") != "INSERTED_LOCAL_FIXTURE"
                           for entry in items)
                    or not y._check_receipt(conn, receipt, _items(receipt))):
                conn.rollback()
                return _hold("HOLD_ORIGINAL_ROW_OR_LEDGER_DRIFT")
            # _protected_schema rejects any unknown referencing tables,
            # view or trigger: rollback cannot orphan later graph/score writes.
            started = True
            for entry in items:
                removed = conn.execute(
                    "DELETE FROM memory_records "
                    "WHERE record_id=? AND scope='MemoryOS' "
                    "AND status=? AND source=?",
                    (
                        entry["record_id"], y.STATUS,
                        "galaxy-archive-v1:" + entry["source_key_sha256"],
                    ),
                ).rowcount
                if removed != 1:
                    raise ValueError("fixture row count changed")
            updated = conn.execute(
                "UPDATE galaxy_stage9y_batches SET status=? "
                "WHERE approval_id=? AND status=?",
                (ROLLED_BACK, import_id, y.STATUS),
            ).rowcount
            if updated != 1:
                raise ValueError("fixture batch changed")
            now = datetime.now(timezone.utc).isoformat()
            rollback_receipt = {
                "schema": SCHEMA, "target": TARGET, "status": ROLLED_BACK,
                "rollback_id": rollback_id, "import_approval_id": import_id,
                "manifest_sha256": y._sha(y._bytes(expected)),
                "import_receipt_sha256": receipt["receipt_sha256"],
                "canary_sha256": receipt["canary_sha256"],
                "created_at": now,
                "deleted_new_fixture_rows": len(items),
                "original_import_ledgers_retained": True,
                "items": [
                    {
                        "record_id": item["record_id"],
                        "row_sha256": item["row_sha256"],
                        "source_key_sha256": item["source_key_sha256"],
                    }
                    for item in items
                ],
            }
            rollback_receipt["receipt_sha256"] = y._sha(y._bytes(rollback_receipt))
            mac = hmac.new(
                rollback_key, y._bytes(rollback_receipt), hashlib.sha256
            ).hexdigest()
            conn.execute(
                f"INSERT INTO galaxy_stage9z_rollbacks "
                f"({','.join(LEDGER_COLS)}) VALUES "
                f"({','.join('?' for _ in LEDGER_COLS)})",
                (
                    rollback_id, import_id, y._sha(y._bytes(expected)),
                    receipt["receipt_sha256"],
                    y._bytes(rollback_receipt).decode("utf-8"),
                    mac, ROLLED_BACK, now,
                ),
            )
            if not _check_deleted(
                conn, batch, receipt, rollback_receipt, rollback_key,
            ):
                raise ValueError("signed rollback readback mismatch")
            conn.commit()
    except Exception as exc:
        try:
            conn.rollback()
        except sqlite3.Error:
            pass
        return _hold(
            "HOLD_LOCAL_ROLLBACK_TRANSACTION_OR_ACK_FAILED",
            uncertain=started, error_type=type(exc).__name__,
        )

    try:
        with sqlite3.connect(path) as fresh:
            if (not _protected_schema(fresh)
                    or not y._schema_and_identity(
                        fresh, original_manifest["expected_staging_id"],
                        original_manifest["canary_run_id"],
                        original_manifest["canary_sha256"],
                    )
                    or not _check_deleted(
                        fresh, batch, receipt, rollback_receipt, rollback_key,
                    )):
                return _hold(
                    "HOLD_FRESH_LOCAL_ROLLBACK_READBACK_CHANGED",
                    uncertain=not replay,
                )
    except (OSError, sqlite3.Error, TypeError, ValueError) as exc:
        return _hold(
            "HOLD_FRESH_LOCAL_ROLLBACK_UNAVAILABLE",
            uncertain=not replay, error_type=type(exc).__name__,
        )
    out = _hold(
        "PASS_LOCAL_ROLLBACK_RECEIPT_REOPEN"
        if not replay else "PASS_LOCAL_ROLLBACK_EXACT_REPLAY_ZERO_WRITE"
    )
    out.update({
        "rollback_receipt": rollback_receipt,
        "original_import_ledgers_retained": True,
        "fresh_local_connection_readback": True,
        "idempotent_replay": replay,
        "writes_performed": [] if replay else [
            "LOCAL_FIXTURE_NEW_ROWS_REMOVED",
            "LOCAL_FIXTURE_SIGNED_ROLLBACK_LEDGER_RETAINED",
        ],
    })
    return out
