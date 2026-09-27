"""GALAXY Stage 9Y: canonical-schema, signed historical-import LOCAL fixture.

SOURCE-ONLY, NO REMOTE DATABASE PATH. This deliberately accepts a native
sqlite3.Connection to a separate file below an explicit fixture directory.
There is NO libsql import, production MemconOS import, HTTP route, environment
secret, external connector or automatic schema creation. The transaction is
shaped for a future independently authorized staging Turso adapter; it is NOT
that adapter. A real staging Turso import is still prohibited at this stage.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import galaxy_archive_staging as stage9t
import galaxy_stage9v_staging_turso as stage9v

SCHEMA = "gaiaos.galaxy.stage9y.canonical-staging-fixture.v1"
APPROVAL_SCHEMA = "gaiaos.galaxy.stage9y.signed-import-fixture.v1"
TARGET = "LOCAL_CANONICAL_STAGING_SQLITE_FIXTURE_ONLY"
STATUS = stage9t.STAGED_STATUS
ROOT = Path(__file__).resolve().parents[1]
BATCH_CAP = 25
HEX = re.compile(r"[0-9a-f]{64}\\Z")
ID = re.compile(r"[A-Za-z0-9_.:-]{8,100}\\Z")
RECORD_COLS = (
    "record_id", "authority", "record_type", "scope", "statement", "source",
    "status", "version", "created_at", "updated_at", "supersedes", "notes",
)
BATCH_COLS = (
    "approval_id", "manifest_sha256", "export_sha256", "source_sha256",
    "canary_sha256", "receipt_json", "receipt_hmac_sha256", "status",
    "created_at",
)
ITEM_COLS = (
    "receipt_id", "approval_id", "record_id", "source_key_sha256",
    "statement_sha256", "metadata_sha256", "row_sha256", "result",
)


def _bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _hold(status: str, *, unverified_write: bool = False,
          error_type: str | None = None) -> dict[str, Any]:
    result = {
        "schema": SCHEMA, "status": status, "target": TARGET,
        "staging_turso_remotely_observed": False,
        "live_owner_authentication_verified": False,
        "provider_database_separation_independently_verified": False,
        "historical_statements_attributed_by_importer": False,
        "production_accessed": False, "production_modified": False,
        "gravity_modified": False, "e_lanes_modified": False,
        "mode_control_modified": False, "bigbang_activated": False,
        "writes_performed": (
            ["LOCAL_FIXTURE_WRITE_OUTCOME_UNVERIFIED"] if unverified_write else []
        ),
        "proof_boundary": (
            "Only a caller-provided, separately located native SQLite test "
            "database. HMAC possession is simulated authorization, NOT live "
            "owner identity. Neither remote Turso nor production is accessible."
        ),
    }
    if error_type is not None:
        result["error_type"] = error_type
    return result


def _fixture_path(conn: Any, fixture_root: Any) -> Path | None:
    """Reject in-memory, attached, source-repo and arbitrary disk connections."""
    if type(conn) is not sqlite3.Connection or conn.in_transaction:
        return None
    if not isinstance(fixture_root, (str, Path)):
        return None
    try:
        root = Path(fixture_root).expanduser().resolve(strict=True)
        if (not root.is_dir() or root == ROOT or ROOT in root.parents
                or root.is_symlink()):
            return None
        listing = conn.execute("PRAGMA database_list").fetchall()
        if len(listing) != 1 or listing[0][1] != "main" or not listing[0][2]:
            return None
        path = Path(listing[0][2]).resolve(strict=True)
        if (path == root or root not in path.parents
                or path == ROOT or ROOT in path.parents
                or not path.is_file() or path.is_symlink()):
            return None
        return path
    except (OSError, sqlite3.Error, IndexError, TypeError, ValueError):
        return None


def _row(cursor: Any) -> dict[str, Any] | None:
    names = [c[0] if isinstance(c, (tuple, list))
             else getattr(c, "name", str(c)) for c in cursor.description]
    value = cursor.fetchone()
    return dict(zip(names, value)) if value is not None else None


def _rows(cursor: Any) -> list[dict[str, Any]]:
    names = [c[0] if isinstance(c, (tuple, list))
             else getattr(c, "name", str(c)) for c in cursor.description]
    return [dict(zip(names, row)) for row in cursor.fetchall()]


def _schema_and_identity(conn: sqlite3.Connection, marker: str,
                         run_id: str, expected_canary_sha: str) -> bool:
    """Read ONLY tables already provisioned in the separate test database."""
    if not stage9v._identity(conn, marker):
        return False
    try:
        required = (
            ("memory_records", RECORD_COLS),
            ("galaxy_stage9y_batches", BATCH_COLS),
            ("galaxy_stage9y_items", ITEM_COLS),
            ("galaxy_stage9v_canaries",
             ("run_id", "nonce_sha256", "database_id", "created_at")),
        )
        for table, columns in required:
            cursor = conn.execute(f"SELECT {','.join(columns)} FROM {table} LIMIT 0")
            actual = tuple(c[0] if isinstance(c, (tuple, list))
                           else getattr(c, "name", str(c))
                           for c in cursor.description)
            if actual != columns:
                return False
        canary = stage9v._canary(conn, run_id)
        if (canary is None or canary.get("database_id") != marker
                or not isinstance(canary.get("nonce_sha256"), str)
                or HEX.fullmatch(canary["nonce_sha256"]) is None
                or _sha(_bytes(canary)) != expected_canary_sha):
            return False
        return True
    except (sqlite3.Error, TypeError, ValueError, OverflowError):
        return False


def _signed_exact(approval: Any, signature: Any, key: Any,
                  expected: dict[str, Any]) -> bool:
    if (not isinstance(approval, dict) or approval != expected
            or not isinstance(key, bytes) or len(key) < 32
            or not isinstance(signature, str) or HEX.fullmatch(signature) is None):
        return False
    try:
        return hmac.compare_digest(
            signature,
            hmac.new(key, _bytes(approval), hashlib.sha256).hexdigest(),
        )
    except (TypeError, ValueError, OverflowError):
        return False


def _expected_manifest(*, config: dict[str, str], approval: Any,
                       export_hash: str, source_hash: str,
                       items: list[dict[str, Any]]) -> dict[str, Any] | None:
    stage = stage9v._canonical_url(config.get("staging_url"))
    prod = stage9v._canonical_url(config.get("production_url"))
    marker = config.get("expected_staging_id")
    if (stage is None or prod is None or stage == prod
            or not stage9v._valid_id(marker) or not isinstance(approval, dict)):
        return None
    approval_id = approval.get("approval_id")
    run = approval.get("canary_run_id")
    canary_hash = approval.get("canary_sha256")
    if (not isinstance(approval_id, str) or ID.fullmatch(approval_id) is None
            or not isinstance(run, str) or ID.fullmatch(run) is None
            or not isinstance(canary_hash, str)
            or HEX.fullmatch(canary_hash) is None):
        return None
    return {
        "schema": APPROVAL_SCHEMA, "authority": "NAOMI",
        "target": TARGET, "action": "IMPORT_HISTORICAL_TO_LOCAL_FIXTURE",
        "approval_id": approval_id, "expected_staging_id": marker,
        "staging_url_sha256": _sha(stage.encode()),
        "production_url_sha256": _sha(prod.encode()),
        "export_sha256": export_hash, "source_sha256": source_hash,
        "historical_status": STATUS, "canary_run_id": run,
        "canary_sha256": canary_hash,
        "items": [
            {
                "index": item["index"],
                "source_key_sha256": item["source_key_sha256"],
                "statement_sha256": item["statement_sha256"],
                "metadata_sha256": item["metadata_sha256"],
            }
            for item in items
        ],
    }


def _stored_record(conn: sqlite3.Connection, rid: str) -> dict[str, Any] | None:
    return _row(conn.execute(
        f"SELECT {','.join(RECORD_COLS)} FROM memory_records WHERE record_id=?",
        (rid,),
    ))


def _check_receipt(conn: sqlite3.Connection, receipt: Any,
                   items: list[dict[str, Any]]) -> bool:
    try:
        if (not isinstance(receipt, dict) or receipt.get("schema") != SCHEMA
                or receipt.get("target") != TARGET
                or receipt.get("historical_status") != STATUS
                or not isinstance(receipt.get("items"), list)
                or len(receipt["items"]) != len(items)
                or receipt.get("receipt_sha256") != _sha(_bytes({
                    k: v for k, v in receipt.items() if k != "receipt_sha256"
                }))):
            return False
        for entry, item in zip(receipt["items"], items):
            if (entry.get("source_key_sha256") != item["source_key_sha256"]
                    or entry.get("statement_sha256") != item["statement_sha256"]
                    or entry.get("metadata_sha256") != item["metadata_sha256"]
                    or entry.get("record_id") != item["proposed_record_id"]
                    or entry.get("status") != STATUS):
                return False
            record = _stored_record(conn, entry["record_id"])
            if (record is None or record["status"] != STATUS
                    or record["scope"] != "MemoryOS"
                    or record["source"] != (
                        "galaxy-archive-v1:" + item["source_key_sha256"]
                    )
                    or _sha(_bytes(record)) != entry["row_sha256"]):
                return False
            # Recheck source uniqueness, not just primary-key uniqueness.
            sources = _rows(conn.execute(
                "SELECT record_id FROM memory_records WHERE source=? LIMIT 2",
                (record["source"],),
            ))
            if len(sources) != 1 or sources[0]["record_id"] != entry["record_id"]:
                return False
            logged = _row(conn.execute(
                f"SELECT {','.join(ITEM_COLS)} FROM galaxy_stage9y_items "
                "WHERE receipt_id=?", (entry["receipt_id"],),
            ))
            if (logged is None or logged["approval_id"] != receipt["approval_id"]
                    or logged["record_id"] != entry["record_id"]
                    or logged["source_key_sha256"] != entry["source_key_sha256"]
                    or logged["statement_sha256"] != entry["statement_sha256"]
                    or logged["metadata_sha256"] != entry["metadata_sha256"]
                    or logged["row_sha256"] != entry["row_sha256"]
                    or logged["result"] != "INSERTED_LOCAL_FIXTURE"):
                return False
        batch = _row(conn.execute(
            f"SELECT {','.join(BATCH_COLS)} FROM galaxy_stage9y_batches "
            "WHERE approval_id=?", (receipt["approval_id"],),
        ))
        return (
            batch is not None
            and batch["status"] == STATUS
            and batch["manifest_sha256"] == receipt["manifest_sha256"]
            and batch["export_sha256"] == receipt["export_sha256"]
            and batch["source_sha256"] == receipt["source_sha256"]
            and batch["canary_sha256"] == receipt["canary_sha256"]
            and batch["receipt_json"] == _bytes(receipt).decode("utf-8")
        )
    except (sqlite3.Error, TypeError, KeyError, ValueError, OverflowError):
        return False


def stage_historical_fixture(
    *, fixture_connection: sqlite3.Connection, fixture_root: str | Path,
    config: dict[str, str], export_bytes: bytes,
    pinned_export_sha256: str, source_bytes: bytes,
    pinned_source_sha256: str, approval: Any,
    signature_hex: str, approval_key: bytes,
    confirm_separate_fixture: bool, confirm_owner_source_review: bool,
    confirm_canary_evidence_review: bool,
) -> dict[str, Any]:
    """Implement the proposed canonical import mechanics on LOCAL fixtures ONLY.

    First verify independent source-byte pins, per-item hashes, exact signed
    fixture approval, staging identity and prior same-DB canary. Then perform an
    atomic 1..25 record import and ledger, followed by a fresh file readback.
    No caller-supplied connection or fixture path can trigger remote libsql.
    """
    if not all((confirm_separate_fixture, confirm_owner_source_review,
                confirm_canary_evidence_review)):
        return _hold("HOLD_EXPLICIT_FIXTURE_REVIEW_REQUIRED")
    path = _fixture_path(fixture_connection, fixture_root)
    if path is None:
        return _hold("HOLD_NOT_SEPARATE_FILE_BACKED_NATIVE_SQLITE_FIXTURE")
    verified = stage9t._verified_packet(
        export_bytes, pinned_export_sha256, source_bytes, pinned_source_sha256,
    )
    if isinstance(verified, str):
        return _hold(verified)
    packet, items = verified
    if len(items) > BATCH_CAP:
        return _hold("HOLD_INITIAL_BATCH_CAP_25")
    expected = _expected_manifest(
        config=config, approval=approval, export_hash=pinned_export_sha256,
        source_hash=pinned_source_sha256, items=items,
    )
    if expected is None or not _signed_exact(
        approval, signature_hex, approval_key, expected,
    ):
        return _hold("HOLD_EXACT_SIGNED_LOCAL_FIXTURE_APPROVAL_REQUIRED")
    conn = fixture_connection
    marker = approval["expected_staging_id"]
    run = approval["canary_run_id"]
    canary_hash = approval["canary_sha256"]
    if not _schema_and_identity(conn, marker, run, canary_hash):
        return _hold("HOLD_CANONICAL_SCHEMA_IDENTITY_OR_CANARY_MISMATCH")

    manifest_sha = _sha(_bytes(approval))
    now = datetime.now(timezone.utc).isoformat()
    started_writes = False
    try:
        conn.execute("BEGIN IMMEDIATE")
        if not _schema_and_identity(conn, marker, run, canary_hash):
            conn.rollback()
            return _hold("HOLD_STAGING_IDENTITY_CHANGED")
        previous = _row(conn.execute(
            f"SELECT {','.join(BATCH_COLS)} FROM galaxy_stage9y_batches "
            "WHERE approval_id=?", (approval["approval_id"],),
        ))
        if previous is not None:
            if (previous["manifest_sha256"] != manifest_sha
                    or previous["export_sha256"] != pinned_export_sha256
                    or previous["source_sha256"] != pinned_source_sha256
                    or previous["canary_sha256"] != canary_hash):
                conn.rollback()
                return _hold("HOLD_APPROVAL_ID_REUSE_OR_REPLAY_DRIFT")
            try:
                receipt = json.loads(previous["receipt_json"])
                if (previous["receipt_hmac_sha256"] != hmac.new(
                    approval_key, _bytes(receipt), hashlib.sha256,
                ).hexdigest() or not _check_receipt(conn, receipt, items)):
                    conn.rollback()
                    return _hold("HOLD_SIGNED_RECEIPT_OR_STAGING_REPLAY_DRIFT")
            except (ValueError, TypeError, OverflowError):
                conn.rollback()
                return _hold("HOLD_SIGNED_RECEIPT_OR_STAGING_REPLAY_DRIFT")
            conn.rollback()  # Exact replay MUST do zero writes.
            replay = True
        else:
            # All collision checks run BEFORE the FIRST insertion.
            for item in items:
                source = "galaxy-archive-v1:" + item["source_key_sha256"]
                hits = _rows(conn.execute(
                    "SELECT record_id,source FROM memory_records "
                    "WHERE source=? OR record_id=? LIMIT 3",
                    (source, item["proposed_record_id"]),
                ))
                if hits:
                    conn.rollback()
                    return _hold("HOLD_EXISTING_SOURCE_OR_RECORD_ID_COLLISION")
            entries: list[dict[str, Any]] = []
            for source_record, item in zip(packet["records"], items):
                rid = item["proposed_record_id"]
                source = "galaxy-archive-v1:" + item["source_key_sha256"]
                notes = stage9t._archive_note(
                    packet, source_record, item,
                    pinned_export_sha256, pinned_source_sha256,
                )
                values = (
                    rid, "NAOMI", source_record["record_type"], "MemoryOS",
                    source_record["statement"], source, STATUS, "1",
                    now, now, None, _bytes(notes).decode("utf-8"),
                )
                started_writes = True
                conn.execute(
                    "INSERT INTO memory_records "
                    f"({','.join(RECORD_COLS)}) VALUES ({','.join('?' for _ in RECORD_COLS)})",
                    values,
                )
                row = _stored_record(conn, rid)
                if row is None or row != dict(zip(RECORD_COLS, values)):
                    raise ValueError("local staging row mismatch")
                receipt_id = "STAGE9Y-ITEM-" + _sha(_bytes({
                    "approval_id": approval["approval_id"], "record_id": rid,
                    "source_key_sha256": item["source_key_sha256"],
                }))[:32]
                row_sha = _sha(_bytes(row))
                conn.execute(
                    f"INSERT INTO galaxy_stage9y_items ({','.join(ITEM_COLS)}) "
                    f"VALUES ({','.join('?' for _ in ITEM_COLS)})",
                    (
                        receipt_id, approval["approval_id"], rid,
                        item["source_key_sha256"], item["statement_sha256"],
                        item["metadata_sha256"], row_sha,
                        "INSERTED_LOCAL_FIXTURE",
                    ),
                )
                entries.append({
                    "index": item["index"], "receipt_id": receipt_id,
                    "record_id": rid, "source_key_sha256": item["source_key_sha256"],
                    "statement_sha256": item["statement_sha256"],
                    "metadata_sha256": item["metadata_sha256"],
                    "row_sha256": row_sha, "status": STATUS,
                })
            receipt = {
                "schema": SCHEMA, "target": TARGET,
                "approval_id": approval["approval_id"],
                "manifest_sha256": manifest_sha,
                "export_sha256": pinned_export_sha256,
                "source_sha256": pinned_source_sha256,
                "canary_sha256": canary_hash, "historical_status": STATUS,
                "created_at": now, "items": entries,
                "original_attribution_independently_verified": False,
                "owner_live_authorization_proven": False,
                "remote_storage_written": False,
            }
            receipt["receipt_sha256"] = _sha(_bytes(receipt))
            mac = hmac.new(approval_key, _bytes(receipt), hashlib.sha256).hexdigest()
            conn.execute(
                f"INSERT INTO galaxy_stage9y_batches ({','.join(BATCH_COLS)}) "
                f"VALUES ({','.join('?' for _ in BATCH_COLS)})",
                (
                    approval["approval_id"], manifest_sha,
                    pinned_export_sha256, pinned_source_sha256,
                    canary_hash, _bytes(receipt).decode("utf-8"),
                    mac, STATUS, now,
                ),
            )
            if not _check_receipt(conn, receipt, items):
                raise ValueError("ledger and staging readback mismatch")
            conn.commit()
            replay = False
    except Exception as exc:
        try:
            conn.rollback()
        except sqlite3.Error:
            pass
        return _hold(
            "HOLD_LOCAL_STAGING_TRANSACTION_OR_ACK_FAILED",
            unverified_write=started_writes, error_type=type(exc).__name__,
        )
    # Read through a wholly fresh connection, without touching caller's conn.
    # A failed reopen means the earlier commit is UNKNOWN until exact replay.
    try:
        with sqlite3.connect(path) as reopened:
            if (not _schema_and_identity(reopened, marker, run, canary_hash)
                    or not _check_receipt(reopened, receipt, items)):
                return _hold(
                    "HOLD_FRESH_CONNECTION_READBACK_CHANGED",
                    unverified_write=not replay,
                )
    except (OSError, sqlite3.Error, TypeError, ValueError) as exc:
        return _hold(
            "HOLD_FRESH_CONNECTION_READBACK_UNAVAILABLE",
            unverified_write=not replay, error_type=type(exc).__name__,
        )
    out = _hold(
        "PASS_LOCAL_CANONICAL_STAGING_REOPEN_FIXTURE"
        if not replay else "PASS_LOCAL_EXACT_REPLAY_ZERO_WRITE",
    )
    out.update({
        "source_and_export_bytes_verified": True,
        "local_hmac_fixture_approval_verified": True,
        "fixture_identity_and_canary_verified": True,
        "fresh_local_connection_readback": True,
        "idempotent_replay": replay,
        "writes_performed": (
            [] if replay else ["LOCAL_FIXTURE_HISTORICAL_ROWS_AND_RECEIPTS"]
        ),
        "receipt": receipt,
    })
    return out
