"""GALAXY Stage 9AG: guarded first signed archival batch into separate staging.

SOURCE-ONLY DRAFT. DRY RUN by default: no DB connections, no user action.
A future explicit owner-local invocation may apply ONE 1..25 record batch only
to an independently reviewed, EMPTY, six-table staging database after its
privately pinned Stage 9X canary. No production/main connection or credentials,
E-LANE writes, gravity changes, historical promotion or BIGBANG unlock.

The first remote attempt has NEVER been performed. Injected connectors prove
LOCAL compatibility only and must never be labeled remote Turso evidence.
A signed HMAC proves possession of a key, NOT owner identity; provider IDs,
token scope, aliases, source review and final authorization are external gates.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any, Callable

import galaxy_archive_staging as archive
import galaxy_stage9y_canonical_staging as y
import galaxy_stage9v_staging_turso as v
import galaxy_stage9aa_preimport_readonly as aa
import galaxy_stage9ab_owner_local_bootstrap as ab

SCHEMA = "gaiaos.galaxy.stage9ag.first-staging-historical-import.v1"
APPROVAL_SCHEMA = "gaiaos.galaxy.stage9ag.owner-local-staging-import-approval.v1"
TARGET = "FIRST_SEPARATE_STAGING_HISTORICAL_BATCH_ONLY"
RESULT = "INSERTED_STAGING_HOLD"
ROLLED_BACK = frozenset(("ROLLED_BACK_LOCAL_FIXTURE", "ROLLED_BACK_STAGING"))


def _report(status: str, *, injected: bool = False,
            uncertain: bool = False, proven: bool = False,
            replay: bool = False) -> dict[str, Any]:
    return {
        "schema": SCHEMA, "status": status, "target": TARGET,
        "test_connector_injected": injected,
        "staging_remotely_observed": proven and not injected,
        "independent_owner_authentication_verified": False,
        "provider_identity_and_alias_separation_verified": False,
        "token_scope_independently_verified": False,
        "production_connected": False, "sovmem_main_connected": False,
        "original_gaiaos_production_connected": False,
        "gravity_modified": False, "e_lanes_modified": False,
        "mode_control_modified": False, "bigbang_activated": False,
        "historical_memories_activated": 0,
        "write_outcome_uncertain": uncertain,
        "writes_performed": (
            ["STAGING_BATCH_COMMIT_OUTCOME_UNVERIFIED"] if uncertain
            else ["ONE_HELD_STAGING_BATCH_AND_SIGNED_ITEM_RECEIPTS"]
            if proven and not replay else []
        ),
        "proof_boundary": (
            "First batch only. Local injection never proves remote Turso. "
            "A real reopening would prove connection readback, NOT provider "
            "alias/credential scope, live owner identity, restart or replica "
            "durability, real source truth, remote rollback or release."
        ),
    }


def expected_approval(
    *, config: dict[str, str], pin: dict[str, Any],
    approval_id: str, export_sha256: str, source_sha256: str,
    items: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Exact domain-separated remote action. Stage 9Y LOCAL signature CANNOT apply."""
    if not isinstance(config, dict) or not aa._canonical_pin(config, pin):
        return None
    if (not ab._host_has_label(config["staging_url"], "sovmem-staging")
            or not ab._host_has_label(config["production_url"], "sovmem-main")):
        return None
    if (not isinstance(export_sha256, str) or y.HEX.fullmatch(export_sha256) is None
            or not isinstance(source_sha256, str)
            or y.HEX.fullmatch(source_sha256) is None
            or not isinstance(items, list) or not 1 <= len(items) <= y.BATCH_CAP):
        return None
    base = y._expected_manifest(
        config=config,
        approval={
            "approval_id": approval_id, "canary_run_id": pin["run_id"],
            "canary_sha256": pin["canary_sha256"],
        },
        export_hash=export_sha256, source_hash=source_sha256, items=items,
    )
    if base is None or base.get("historical_status") != y.STATUS:
        return None
    return {
        **base, "schema": APPROVAL_SCHEMA, "target": TARGET,
        "action": "WRITE_FIRST_SIGNED_HELD_STAGING_BATCH",
    }


def _safe_schema(conn: Any, config: dict[str, str],
                 pin: dict[str, Any]) -> bool:
    """Read-only six-table layout + exact marker + independently pinned canary."""
    try:
        if not v._identity(conn, config["expected_staging_id"]):
            return False
        objects = conn.execute(
            "SELECT type,name FROM sqlite_master "
            "WHERE type IN ('table','view','trigger')"
        ).fetchall()
        tables = {
            name for kind, name in objects
            if isinstance(name, str) and name.startswith("sqlite_")
        }
        # Reject every non-internal trigger, view, extra or missing table.
        expected = {("table", name) for name in aa.EXPECTED_TABLES}
        actual = {(kind, name) for kind, name in objects
                  if not (isinstance(name, str) and name.startswith("sqlite_"))}
        if actual != expected:
            return False
        for name, cols in aa.EXPECTED_TABLES.items():
            if aa._columns(conn.execute(f"SELECT * FROM {name} LIMIT 0")) != cols:
                return False
        row = v._canary(conn, pin["run_id"])
        if (row is None or row.get("database_id") != config["expected_staging_id"]
                or v._sha(v._bytes(row)) != pin["canary_sha256"]):
            return False
        if conn.execute(
            "SELECT COUNT(*) FROM galaxy_stage9v_canaries"
        ).fetchone()[0] != 1:
            return False
        return True
    except Exception:
        return False


def _empty(conn: Any) -> bool:
    try:
        return all(
            type(n) is int and n == 0 for n in (
                conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in aa.EMPTY_TABLES
            )
        )
    except Exception:
        return False


def _row(conn: Any, table: str, key: str, value: str) -> dict[str, Any] | None:
    # Identifiers are all static constants, never caller input.
    cols = {
        "memory_records": y.RECORD_COLS,
        "galaxy_stage9y_batches": y.BATCH_COLS,
        "galaxy_stage9y_items": y.ITEM_COLS,
    }[table]
    return v._row(conn.execute(
        f"SELECT {','.join(cols)} FROM {table} WHERE {key}=?", (value,),
    ))


def _receipt_ok(
    conn: Any, receipt: Any, items: list[dict[str, Any]],
    approval: dict[str, Any], approval_key: bytes,
) -> bool:
    """Independent exact readback of every imported row, receipt and hash."""
    try:
        if (not isinstance(receipt, dict)
                or receipt.get("schema") != SCHEMA
                or receipt.get("target") != TARGET
                or receipt.get("historical_status") != y.STATUS
                or receipt.get("approval_id") != approval["approval_id"]
                or receipt.get("manifest_sha256") != y._sha(y._bytes(approval))
                or receipt.get("export_sha256") != approval["export_sha256"]
                or receipt.get("source_sha256") != approval["source_sha256"]
                or receipt.get("canary_sha256") != approval["canary_sha256"]
                or receipt.get("remote_storage_written") is not False
                or receipt.get("receipt_sha256") != y._sha(y._bytes({
                    k: val for k, val in receipt.items()
                    if k != "receipt_sha256"
                }))
                or not isinstance(receipt.get("items"), list)
                or len(receipt["items"]) != len(items)):
            return False
        batch = _row(
            conn, "galaxy_stage9y_batches", "approval_id",
            approval["approval_id"],
        )
        if (batch is None or batch["status"] != y.STATUS
                or batch["manifest_sha256"] != receipt["manifest_sha256"]
                or batch["receipt_json"] != y._bytes(receipt).decode()
                or not hmac.compare_digest(
                    batch["receipt_hmac_sha256"],
                    hmac.new(approval_key, y._bytes(receipt),
                             hashlib.sha256).hexdigest(),
                )):
            return False
        if (conn.execute(
            "SELECT COUNT(*) FROM galaxy_stage9y_batches"
        ).fetchone()[0] != 1
                or conn.execute(
                    "SELECT COUNT(*) FROM galaxy_stage9y_items"
                ).fetchone()[0] != len(items)
                or conn.execute(
                    "SELECT COUNT(*) FROM memory_records"
                ).fetchone()[0] != len(items)
                or conn.execute(
                    "SELECT COUNT(*) FROM galaxy_stage9z_rollbacks"
                ).fetchone()[0] != 0):
            return False
        for actual, expected in zip(receipt["items"], items):
            rid = expected["proposed_record_id"]
            if (actual.get("record_id") != rid
                    or actual.get("index") != expected["index"]
                    or actual.get("status") != y.STATUS
                    or actual.get("source_key_sha256") !=
                    expected["source_key_sha256"]
                    or actual.get("statement_sha256") !=
                    expected["statement_sha256"]
                    or actual.get("metadata_sha256") !=
                    expected["metadata_sha256"]):
                return False
            record = _row(conn, "memory_records", "record_id", rid)
            if (record is None or record["status"] != y.STATUS
                    or record["scope"] != "MemoryOS"
                    or record["source"] !=
                    "galaxy-archive-v1:" + expected["source_key_sha256"]
                    or y._sha(y._bytes(record)) != actual["row_sha256"]):
                return False
            item = _row(
                conn, "galaxy_stage9y_items", "receipt_id",
                actual["receipt_id"],
            )
            if (item is None or item["record_id"] != rid
                    or item["approval_id"] != approval["approval_id"]
                    or item["result"] != RESULT
                    or item["source_key_sha256"] !=
                    expected["source_key_sha256"]
                    or item["statement_sha256"] !=
                    expected["statement_sha256"]
                    or item["metadata_sha256"] !=
                    expected["metadata_sha256"]
                    or item["row_sha256"] != actual["row_sha256"]):
                return False
        return True
    except Exception:
        return False


def stage_first_signed_batch(
    *, config: dict[str, str], pin: dict[str, Any],
    export_bytes: bytes, pinned_export_sha256: str,
    source_bytes: bytes, pinned_source_sha256: str,
    approval: dict[str, Any], signature_hex: str, approval_key: bytes,
    apply: bool = False, confirm_source_review: bool = False,
    confirm_independent_pin: bool = False,
    confirm_provider_ids_reviewed: bool = False,
    confirm_staging_token_scope_reviewed: bool = False,
    confirm_first_held_batch_only: bool = False,
    connector: Callable[[str, str], Any] | None = None,
) -> dict[str, Any]:
    """Default dry-run has ZERO connections, even with populated config.

    Real live use is a separate future owner action requiring five *literal*
    confirmations and an entirely separate Stage 9AG HMAC manifest/key.
    """
    injected = connector is not None
    verified = archive._verified_packet(
        export_bytes, pinned_export_sha256,
        source_bytes, pinned_source_sha256,
    )
    if isinstance(verified, str):
        return _report("HOLD_SOURCE_EXPORT_PINS_OR_ARCHIVE_INVALID",
                       injected=injected)
    packet, items = verified
    if not 1 <= len(items) <= y.BATCH_CAP:
        return _report("HOLD_BATCH_SIZE_NOT_1_TO_25", injected=injected)
    expected = expected_approval(
        config=config, pin=pin, approval_id=approval.get("approval_id")
        if isinstance(approval, dict) else None,
        export_sha256=pinned_export_sha256,
        source_sha256=pinned_source_sha256, items=items,
    )
    if expected is None or not y._signed_exact(
        approval, signature_hex, approval_key, expected,
    ):
        return _report("HOLD_DOMAIN_SEPARATED_SIGNED_STAGING_APPROVAL_REQUIRED",
                       injected=injected)
    if not apply:
        result = _report("PASS_SIGNED_SOURCE_DRY_RUN_ZERO_CONNECTION",
                         injected=injected)
        result["signed_source_and_export_pins_verified"] = True
        result["exact_batch_item_count"] = len(items)
        return result
    if not all(flag is True for flag in (
        confirm_source_review, confirm_independent_pin,
        confirm_provider_ids_reviewed,
        confirm_staging_token_scope_reviewed,
        confirm_first_held_batch_only,
    )):
        return _report("HOLD_FIVE_EXPLICIT_OWNER_CONFIRMATIONS_REQUIRED",
                       injected=injected)
    connect = connector if injected else v._connect_live
    conn = None
    attempted = False
    committed = False
    replay = False
    prior = None
    receipt = None
    status = None
    marker = config["expected_staging_id"]
    try:
        conn = connect(config["staging_url"], config["staging_token"])
        if not _safe_schema(conn, config, pin):
            status = "HOLD_STAGING_SCHEMA_IDENTITY_OR_CANARY_MISMATCH"
        else:
            prior = _row(
                conn, "galaxy_stage9y_batches",
                "approval_id", approval["approval_id"],
            )
            if prior is not None:
                if (prior["status"] != y.STATUS
                        or prior["manifest_sha256"] !=
                        y._sha(y._bytes(approval))):
                    status = "HOLD_EXISTING_APPROVAL_CONFLICT_OR_ROLLED_BACK"
                else:
                    receipt = json.loads(prior["receipt_json"])
                    if not _receipt_ok(
                        conn, receipt, items, approval, approval_key,
                    ):
                        status = "HOLD_REPLAY_ROW_OR_SIGNED_LEDGER_DRIFT"
                    else:
                        replay = True
            elif not _empty(conn):
                status = "HOLD_ONLY_FIRST_EMPTY_STAGING_BATCH_SUPPORTED"
    except Exception:
        status = "HOLD_STAGING_PREFLIGHT_UNAVAILABLE"
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                status = "HOLD_STAGING_PREFLIGHT_CLOSE_UNVERIFIED"
    if status is not None:
        return _report(status, injected=injected)
    # A new import MUST pass Stage 9AA's independently pinned full read-only
    # pre-import gate. Exact same-signed replay is deliberately SELECT-only:
    # 9AA correctly refuses nonempty staging after our first import.
    if not replay:
        pre = aa.check_preimport_staging(
            config=config, pin=pin, confirm_independent_canary_pin=True,
            connector=connector,
        )
        if pre.get("status") != (
            "PASS_LOCAL_READ_ONLY_SCHEMA_FIXTURE" if injected
            else "PASS_STAGING_READ_ONLY_PREIMPORT"
        ) or pre.get("preimport_tables_empty_verified") is not True:
            return _report("HOLD_STAGE9AA_PREIMPORT_READINESS",
                           injected=injected)
    else:
        return _fresh_readback(
            config, pin, items, approval, approval_key, receipt,
            connector=connector, replay=True, inserted=False,
        )

    # Second empty/identity check is INSIDE BEGIN IMMEDIATE, not just at
    # connection-level preflight. Only six already-reviewed tables are used.
    conn = None
    status = None
    try:
        conn = connect(config["staging_url"], config["staging_token"])
        conn.execute("BEGIN IMMEDIATE")
        if not _safe_schema(conn, config, pin) or not _empty(conn):
            conn.rollback()
            status = "HOLD_STAGING_CHANGED_BEFORE_ATOMIC_INSERT"
        else:
            now = datetime.now(timezone.utc).isoformat()
            entries = []
            for source_record, item in zip(packet["records"], items):
                rid = item["proposed_record_id"]
                source = "galaxy-archive-v1:" + item["source_key_sha256"]
                notes = archive._archive_note(
                    packet, source_record, item,
                    pinned_export_sha256, pinned_source_sha256,
                )
                values = (
                    rid, "NAOMI", source_record["record_type"],
                    "MemoryOS", source_record["statement"], source,
                    y.STATUS, "1", now, now, None,
                    y._bytes(notes).decode(),
                )
                attempted = True
                conn.execute(
                    "INSERT INTO memory_records "
                    f"({','.join(y.RECORD_COLS)}) VALUES "
                    f"({','.join('?' for _ in y.RECORD_COLS)})",
                    values,
                )
                record = _row(conn, "memory_records", "record_id", rid)
                if record != dict(zip(y.RECORD_COLS, values)):
                    raise ValueError("staging row mismatch")
                digest = y._sha(y._bytes(record))
                item_id = "STAGE9AG-ITEM-" + y._sha(y._bytes({
                    "approval_id": approval["approval_id"],
                    "record_id": rid,
                    "source_key_sha256": item["source_key_sha256"],
                }))[:32]
                conn.execute(
                    "INSERT INTO galaxy_stage9y_items "
                    f"({','.join(y.ITEM_COLS)}) VALUES "
                    f"({','.join('?' for _ in y.ITEM_COLS)})",
                    (
                        item_id, approval["approval_id"], rid,
                        item["source_key_sha256"],
                        item["statement_sha256"], item["metadata_sha256"],
                        digest, RESULT,
                    ),
                )
                entries.append({
                    "index": item["index"], "receipt_id": item_id,
                    "record_id": rid,
                    "source_key_sha256": item["source_key_sha256"],
                    "statement_sha256": item["statement_sha256"],
                    "metadata_sha256": item["metadata_sha256"],
                    "row_sha256": digest, "status": y.STATUS,
                })
            receipt = {
                "schema": SCHEMA, "target": TARGET,
                "approval_id": approval["approval_id"],
                "manifest_sha256": y._sha(y._bytes(approval)),
                "export_sha256": pinned_export_sha256,
                "source_sha256": pinned_source_sha256,
                "canary_sha256": pin["canary_sha256"],
                "historical_status": y.STATUS, "created_at": now,
                "items": entries,
                "original_attribution_independently_verified": False,
                "live_owner_authentication_verified": False,
                # The receipt is source-computed; no assertion of real remote
                # proof until independent fresh readback and connector check.
                "remote_storage_written": False,
            }
            receipt["receipt_sha256"] = y._sha(y._bytes(receipt))
            mac = hmac.new(
                approval_key, y._bytes(receipt), hashlib.sha256,
            ).hexdigest()
            conn.execute(
                "INSERT INTO galaxy_stage9y_batches "
                f"({','.join(y.BATCH_COLS)}) VALUES "
                f"({','.join('?' for _ in y.BATCH_COLS)})",
                (
                    approval["approval_id"],
                    receipt["manifest_sha256"],
                    pinned_export_sha256, pinned_source_sha256,
                    pin["canary_sha256"], y._bytes(receipt).decode(),
                    mac, y.STATUS, now,
                ),
            )
            if not _receipt_ok(conn, receipt, items, approval, approval_key):
                raise ValueError("transactional staging receipt mismatch")
            conn.commit()
            committed = True
    except Exception:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        return _report("HOLD_STAGING_TRANSACTION_OUTCOME_UNVERIFIED",
                       injected=injected, uncertain=attempted)
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                status = "HOLD_STAGING_WRITE_CONNECTION_CLOSE_UNVERIFIED"
    if status is not None:
        return _report(status, injected=injected,
                       uncertain=attempted or committed)
    return _fresh_readback(
        config, pin, items, approval, approval_key, receipt,
        connector=connector, replay=False, inserted=committed,
    )


def _fresh_readback(
    config: dict[str, str], pin: dict[str, Any],
    items: list[dict[str, Any]], approval: dict[str, Any],
    approval_key: bytes, receipt: dict[str, Any],
    *, connector: Callable[[str, str], Any] | None,
    replay: bool, inserted: bool,
) -> dict[str, Any]:
    injected = connector is not None
    connect = connector if injected else v._connect_live
    conn = None
    status = None
    try:
        conn = connect(config["staging_url"], config["staging_token"])
        if (not _safe_schema(conn, config, pin)
                or not _receipt_ok(
                    conn, receipt, items, approval, approval_key,
                )):
            status = "HOLD_FRESH_STAGING_SIGNED_READBACK_CHANGED"
    except Exception:
        status = "HOLD_FRESH_STAGING_REOPEN_UNAVAILABLE"
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                status = "HOLD_FRESH_STAGING_CLOSE_UNVERIFIED"
    if status is not None:
        return _report(status, injected=injected, uncertain=inserted)
    out = _report(
        "PASS_LOCAL_HELD_STAGING_IMPORT_REOPEN_FIXTURE" if injected and not replay
        else "PASS_LOCAL_SIGNED_REPLAY_NO_WRITE" if injected
        else "PASS_STAGING_HELD_IMPORT_REOPEN_OBSERVED" if not replay
        else "PASS_STAGING_SIGNED_REPLAY_NO_WRITE",
        injected=injected, proven=True, replay=replay,
    )
    out.update({
        "exact_held_rows": len(items), "signed_item_receipts": len(items),
        "fresh_separate_connection_readback": True,
        "original_pinned_source_and_export_verified": True,
        "exact_domain_separated_approval_verified": True,
        "staging_schema_and_canary_pin_reverified": True,
        "idempotent_zero_write_replay": replay,
        "signed_receipt_sha256": receipt["receipt_sha256"],
        "next_gate": "SEPARATELY_SIGNED_STAGING_ROLLBACK_AND_RESTART_DURABILITY",
    })
    return out
