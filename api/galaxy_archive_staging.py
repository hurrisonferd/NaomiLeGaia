"""Stage 9T: independently pinned archive intake into *in-memory* staging only.

This is a source-only proof harness, NOT a production or staging-Turso importer.
It cannot reach MemconOS, Turso, the GaiaOS HTTP front door or E-LANE files.
It requires separate export/source byte pins and a testable HMAC approval envelope;
real operator authentication and key custody remain deployment HOLDs.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
import sqlite3
from datetime import datetime, timezone
from typing import Any

import galaxy_archive_preflight as preflight

SCHEMA = "gaiaos.galaxy.stage9t.in-memory-staging.v1"
APPROVAL_SCHEMA = "gaiaos.galaxy.stage9t.approval.v1"
TARGET = "ISOLATED_SQLITE_IN_MEMORY_ONLY"
STAGED_STATUS = "STAGED_HISTORICAL_HOLD"
MAX_SOURCE_BYTES = 5_000_000
_HEX = re.compile(r"[0-9a-f]{64}\Z")
_ID = re.compile(r"[A-Za-z0-9_.:-]{8,100}\Z")


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _hold(status: str, *, error_type: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema": SCHEMA,
        "status": status,
        "execution": TARGET,
        "writes_performed": [],
        "production_writes": False,
        "source_records_modified": False,
        "gravity_rows_modified": False,
        "e_lanes_modified": False,
        "mode_control_modified": False,
        "owner_live_authorization_proven": False,
    }
    if error_type is not None:
        result["error_type"] = error_type
    return result


def _unique_json_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _reject_nonfinite(_: str) -> None:
    raise ValueError("non-finite JSON constant")


def _verified_packet(
    export_bytes: Any, pinned_export_sha256: Any,
    source_bytes: Any, pinned_source_sha256: Any,
) -> tuple[dict[str, Any], list[dict[str, Any]]] | str:
    # Pins must be delivered by a trusted *separate* caller, not extracted
    # from the archive packet that they purportedly authenticate.
    if (
        not isinstance(export_bytes, bytes)
        or not 1 <= len(export_bytes) <= preflight.MAX_PACKET_BYTES
        or not isinstance(source_bytes, bytes)
        or not 1 <= len(source_bytes) <= MAX_SOURCE_BYTES
        or not isinstance(pinned_export_sha256, str)
        or _HEX.fullmatch(pinned_export_sha256) is None
        or not isinstance(pinned_source_sha256, str)
        or _HEX.fullmatch(pinned_source_sha256) is None
    ):
        return "HOLD_BYTES_OR_TRUSTED_PINS_MISSING"
    if not hmac.compare_digest(_digest(export_bytes), pinned_export_sha256):
        return "HOLD_EXPORT_DIGEST_MISMATCH"
    if not hmac.compare_digest(_digest(source_bytes), pinned_source_sha256):
        return "HOLD_ORIGINAL_SOURCE_DIGEST_MISMATCH"
    try:
        packet = json.loads(
            export_bytes.decode("utf-8"),
            object_pairs_hook=_unique_json_pairs,
            parse_constant=_reject_nonfinite,
        )
    except (ValueError, UnicodeDecodeError, TypeError):
        return "HOLD_EXPORT_JSON_INVALID"
    audit = preflight.preflight_archive_batch(packet)
    if audit["status"] != "PASS_PREFLIGHT_REVIEW_REQUIRED":
        return "HOLD_ARCHIVE_PREFLIGHT"
    items = audit["items"]
    if len(items) != len(packet["records"]) or any(
        item["status"] != "REVIEW_REQUIRED" for item in items
    ):
        return "HOLD_NON_MEMORY_OR_CONFLICTED_BATCH"
    archive = packet["archive"]
    if (
        archive.get("source_content_sha256") != pinned_source_sha256
    ):
        return "HOLD_SOURCE_PIN_NOT_IN_MANIFEST"
    # Stage 9T's v1 intake deliberately supports literal UTF-8 source exports
    # only; JSON-escaped/derived transcript extraction requires a separate
    # provenance-aware parser and must not be accepted by assumption.
    for record in packet["records"]:
        if record["statement"].encode("utf-8") not in source_bytes:
            return "HOLD_STATEMENT_NOT_FOUND_IN_PINNED_SOURCE"
    return packet, items


def _verified_approval(
    approval: Any, signature_hex: Any, approval_key: Any,
    export_sha: str, source_sha: str, items: list[dict[str, Any]],
) -> str | None:
    if (
        not isinstance(approval_key, bytes) or len(approval_key) < 32
        or not isinstance(approval, dict)
        or not isinstance(signature_hex, str)
        or _HEX.fullmatch(signature_hex) is None
    ):
        return "HOLD_APPROVAL_KEY_OR_SIGNATURE"
    required = {
        "schema", "authority", "target", "approval_id",
        "export_sha256", "source_sha256", "historical_status", "items",
    }
    if set(approval) != required:
        return "HOLD_APPROVAL_FORMAT"
    ident = approval.get("approval_id")
    if not isinstance(ident, str) or _ID.fullmatch(ident) is None:
        return "HOLD_APPROVAL_ID"
    expected_items = [
        {
            "index": item["index"],
            "source_key_sha256": item["source_key_sha256"],
            "statement_sha256": item["statement_sha256"],
            "metadata_sha256": item["metadata_sha256"],
        }
        for item in items
    ]
    if (
        approval.get("schema") != APPROVAL_SCHEMA
        or approval.get("authority") != "NAOMI"
        or approval.get("target") != TARGET
        or approval.get("historical_status") != STAGED_STATUS
        or approval.get("export_sha256") != export_sha
        or approval.get("source_sha256") != source_sha
        or approval.get("items") != expected_items
    ):
        return "HOLD_APPROVAL_DOES_NOT_MATCH_EXPORT"
    try:
        signature = hmac.new(approval_key, _canonical(approval), hashlib.sha256).hexdigest()
    except (TypeError, ValueError):
        return "HOLD_APPROVAL_FORMAT"
    if not hmac.compare_digest(signature, signature_hex):
        return "HOLD_APPROVAL_SIGNATURE_INVALID"
    return None


def _memory_connection(conn: Any) -> bool:
    if type(conn) is not sqlite3.Connection or conn.in_transaction:
        return False
    try:
        dbs = conn.execute("PRAGMA database_list").fetchall()
        # PRAGMA returns an empty path for the in-memory main database.
        return len(dbs) == 1 and dbs[0][1] == "main" and dbs[0][2] == ""
    except (sqlite3.Error, TypeError, IndexError):
        return False


def _init_staging(conn: sqlite3.Connection) -> None:
    # Schema mirrors the existing MemconOS memory_records record contract.
    # Local in-memory staging is not the authoritative MemoryOS database.
    conn.execute("""CREATE TABLE IF NOT EXISTS memory_records (
        record_id TEXT PRIMARY KEY, authority TEXT NOT NULL,
        record_type TEXT NOT NULL, scope TEXT NOT NULL,
        statement TEXT NOT NULL, source TEXT NOT NULL,
        status TEXT NOT NULL, version TEXT NOT NULL,
        created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
        supersedes TEXT, notes TEXT NOT NULL DEFAULT ''
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS galaxy_stage9t_approvals (
        approval_id TEXT PRIMARY KEY, manifest_sha256 TEXT NOT NULL,
        export_sha256 TEXT NOT NULL, source_sha256 TEXT NOT NULL,
        receipt_json TEXT NOT NULL, created_at TEXT NOT NULL
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS galaxy_stage9t_item_receipts (
        receipt_id TEXT PRIMARY KEY, approval_id TEXT NOT NULL,
        record_id TEXT NOT NULL, source_key_sha256 TEXT NOT NULL,
        statement_sha256 TEXT NOT NULL, metadata_sha256 TEXT NOT NULL,
        result TEXT NOT NULL, UNIQUE(approval_id, source_key_sha256)
    )""")


def _archive_note(
    packet: dict[str, Any], record: dict[str, Any], item: dict[str, Any],
    export_sha: str, source_sha: str,
) -> dict[str, Any]:
    source = packet["archive"]
    return {
        "galaxy_archive": {
            "source_key_sha256": item["source_key_sha256"],
            "statement_sha256": item["statement_sha256"],
            "metadata_sha256": item["metadata_sha256"],
            "export_sha256": export_sha,
            "source_content_sha256": source_sha,
            "source_kind": source["source_kind"],
            "source_system": source["source_system"],
            "document_id": source["document_id"],
            "source_locator": source["source_locator"],
            "source_record_id": record["source_record_id"],
            "evidence_ref": record["evidence_ref"],
            "original_created_at": record["original_created_at"],
            "date_confidence": record["date_confidence"],
            "attribution_basis": record["attribution_basis"],
            "original_lifecycle_unverified": True,
            "no_e_lane_ownership_inferred": True,
        }
    }


def _matches(
    row: dict[str, Any], item: dict[str, Any], source_tag: str,
    export_sha: str, source_sha: str,
) -> bool:
    try:
        metadata = json.loads(row["notes"])["galaxy_archive"]
    except (TypeError, ValueError, KeyError):
        return False
    return (
        row["scope"] == "MemoryOS"
        and row["source"] == source_tag
        and row["status"] == STAGED_STATUS
        and _digest(row["statement"].encode("utf-8")) == item["statement_sha256"]
        and metadata.get("source_key_sha256") == item["source_key_sha256"]
        and metadata.get("statement_sha256") == item["statement_sha256"]
        and metadata.get("metadata_sha256") == item["metadata_sha256"]
        and metadata.get("export_sha256") == export_sha
        and metadata.get("source_content_sha256") == source_sha
    )


def _read_row(conn: sqlite3.Connection, record_id: str) -> dict[str, Any] | None:
    cursor = conn.execute(
        "SELECT record_id,scope,source,statement,notes,status "
        "FROM memory_records WHERE record_id=?", (record_id,),
    )
    row = cursor.fetchone()
    return dict(zip((col[0] for col in cursor.description), row)) if row else None


def stage_approved_export(
    *, export_bytes: bytes, pinned_export_sha256: str,
    source_bytes: bytes, pinned_source_sha256: str,
    approval: dict[str, Any], signature_hex: str, approval_key: bytes,
    staging_connection: sqlite3.Connection,
) -> dict[str, Any]:
    """Test actual pinned source+export bytes and signed *simulated* owner intent.

    Only in-memory SQLite is accepted; no live owner credentials are managed
    here. Every write is to the caller-supplied in-memory connection and all
    rows remain on historical HOLD. No external effects or new HTTP routes.
    """
    if not _memory_connection(staging_connection):
        return _hold("HOLD_NOT_ISOLATED_IN_MEMORY_SQLITE")
    verified = _verified_packet(
        export_bytes, pinned_export_sha256, source_bytes, pinned_source_sha256,
    )
    if isinstance(verified, str):
        return _hold(verified)
    packet, items = verified
    why = _verified_approval(
        approval, signature_hex, approval_key,
        pinned_export_sha256, pinned_source_sha256, items,
    )
    if why is not None:
        return _hold(why)
    manifest_sha = _digest(_canonical(approval))
    now = datetime.now(timezone.utc).isoformat()
    conn = staging_connection
    try:
        _init_staging(conn)
        conn.execute("BEGIN IMMEDIATE")
        previous = conn.execute(
            "SELECT manifest_sha256,export_sha256,source_sha256,receipt_json "
            "FROM galaxy_stage9t_approvals WHERE approval_id=?",
            (approval["approval_id"],),
        ).fetchone()
        if previous is not None:
            old_manifest, old_export, old_source, receipt_json = previous
            if (
                old_manifest != manifest_sha or old_export != pinned_export_sha256
                or old_source != pinned_source_sha256
            ):
                conn.rollback()
                return _hold("HOLD_APPROVAL_ID_REUSED_DIFFERENT_CONTENT")
            receipt = json.loads(receipt_json)
            for saved in receipt["items"]:
                item = items[saved["index"]]
                row = _read_row(conn, saved["record_id"])
                if row is None or not _matches(
                    row, item, "galaxy-archive-v1:" + item["source_key_sha256"],
                    pinned_export_sha256, pinned_source_sha256,
                ):
                    conn.rollback()
                    return _hold("HOLD_STAGING_REPLAY_DRIFT")
            conn.commit()
            return {
                **_hold("PASS_STAGING_REPLAY_VERIFIED"),
                "receipt": receipt, "idempotent": True,
                "source_bytes_digest_verified": True,
                "export_bytes_digest_verified": True,
            }

        pending = []
        for index, (source_record, item) in enumerate(zip(packet["records"], items)):
            source_tag = "galaxy-archive-v1:" + item["source_key_sha256"]
            proposed_id = item["proposed_record_id"]
            cursor = conn.execute(
                "SELECT record_id,scope,source,statement,notes,status "
                "FROM memory_records WHERE source=? OR record_id=?",
                (source_tag, proposed_id),
            )
            cols = [col[0] for col in cursor.description]
            hits = [dict(zip(cols, row)) for row in cursor.fetchall()]
            same_source = [row for row in hits if row["source"] == source_tag]
            if len(same_source) > 1 or any(
                row["record_id"] == proposed_id and row["source"] != source_tag
                for row in hits
            ):
                conn.rollback()
                return _hold("HOLD_STAGING_COLLISION")
            if same_source:
                row = same_source[0]
                if not _matches(
                    row, item, source_tag, pinned_export_sha256, pinned_source_sha256,
                ):
                    conn.rollback()
                    return _hold("HOLD_STAGING_SOURCE_CONFLICT")
                pending.append((index, item, source_record, source_tag,
                                row["record_id"], "EXISTING_VERIFIED"))
            else:
                pending.append((index, item, source_record, source_tag,
                                proposed_id, "INSERTED_STAGING"))

        receipt_items = []
        for index, item, source_record, source_tag, record_id, outcome in pending:
            if outcome == "INSERTED_STAGING":
                note = _archive_note(
                    packet, source_record, item,
                    pinned_export_sha256, pinned_source_sha256,
                )
                conn.execute(
                    "INSERT INTO memory_records "
                    "(record_id,authority,record_type,scope,statement,source,"
                    "status,version,created_at,updated_at,supersedes,notes) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        record_id, "NAOMI", source_record["record_type"], "MemoryOS",
                        source_record["statement"], source_tag, STAGED_STATUS, "1",
                        now, now, None, _canonical(note).decode("utf-8"),
                    ),
                )
            row = _read_row(conn, record_id)
            if row is None or not _matches(
                row, item, source_tag, pinned_export_sha256, pinned_source_sha256,
            ):
                raise ValueError("staging readback does not match source")
            receipt_id = "STAGE9T-ITEM-" + _digest(_canonical({
                "approval_id": approval["approval_id"],
                "record_id": record_id,
                "source_key_sha256": item["source_key_sha256"],
            }))[:32]
            conn.execute(
                "INSERT INTO galaxy_stage9t_item_receipts "
                "(receipt_id,approval_id,record_id,source_key_sha256,"
                "statement_sha256,metadata_sha256,result) "
                "VALUES (?,?,?,?,?,?,?)",
                (
                    receipt_id, approval["approval_id"], record_id,
                    item["source_key_sha256"], item["statement_sha256"],
                    item["metadata_sha256"], outcome,
                ),
            )
            receipt_items.append({
                "index": index, "record_id": record_id,
                "source_key_sha256": item["source_key_sha256"],
                "statement_sha256": item["statement_sha256"],
                "metadata_sha256": item["metadata_sha256"],
                "result": outcome, "receipt_id": receipt_id,
                "historical_status": STAGED_STATUS,
            })
        receipt = {
            "schema": SCHEMA, "approval_id": approval["approval_id"],
            "manifest_sha256": manifest_sha, "export_sha256": pinned_export_sha256,
            "source_sha256": pinned_source_sha256, "created_at": now,
            "target": TARGET, "items": receipt_items,
            "source_bytes_digest_verified": True,
            "export_bytes_digest_verified": True,
            "original_attribution_independently_verified": False,
            "real_owner_identity_verified": False,
            "live_storage_written": False,
        }
        receipt["receipt_sha256"] = _digest(_canonical(receipt))
        conn.execute(
            "INSERT INTO galaxy_stage9t_approvals "
            "(approval_id,manifest_sha256,export_sha256,source_sha256,"
            "receipt_json,created_at) VALUES (?,?,?,?,?,?)",
            (
                approval["approval_id"], manifest_sha, pinned_export_sha256,
                pinned_source_sha256, _canonical(receipt).decode("utf-8"), now,
            ),
        )
        conn.commit()
        return {
            **_hold("PASS_IN_MEMORY_STAGING_READBACK"),
            "receipt": receipt,
            "idempotent": False,
            "writes_performed": [
                "ISOLATED_IN_MEMORY_RECORDS",
                "ISOLATED_IN_MEMORY_APPEND_ONLY_RECEIPTS",
            ],
            "source_bytes_digest_verified": True,
            "export_bytes_digest_verified": True,
        }
    except Exception as exc:
        if conn.in_transaction:
            conn.rollback()
        return _hold("HOLD_STAGING_FAILED", error_type=type(exc).__name__)
