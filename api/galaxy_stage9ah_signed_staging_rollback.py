"""GALAXY 9AH: separately signed, exact FIRST staging batch rollback.

SOURCE-ONLY DRAFT. Default is signature-verifying ZERO-CONNECTION dry run.
A later independently approved owner-local APPLY may delete ONLY the exact
unchanged Stage 9AG archival HOLD batch in separate sovmem-staging, preserving
all original signed import/item receipts and adding ONE signed rollback receipt.
Neither sovmem-main nor original GaiaOS production is connected or modified.
No real remote staging rollback has been executed or authorized by this PR.

Injected connector == LOCAL fixture. HMAC is possession, NOT real human
authentication, token-scope evidence or provider database identity proof.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any, Callable

import galaxy_stage9ag_staging_historical_import as ag
import galaxy_stage9y_canonical_staging as y
import galaxy_stage9v_staging_turso as v
import galaxy_stage9aa_preimport_readonly as aa

SCHEMA = "gaiaos.galaxy.stage9ah.first-staging-signed-rollback.v1"
APPROVAL_SCHEMA = "gaiaos.galaxy.stage9ah.separate-rollback-approval.v1"
TARGET = "EXACT_FIRST_STAGING_IMPORT_ROLLBACK_ONLY"
ROLLED_BACK = "ROLLED_BACK_STAGING"
LEDGER_STATUS = ROLLED_BACK
MAX_BATCH = 25


def _report(status: str, *, local: bool = False,
            uncertain: bool = False, verified: bool = False,
            replay: bool = False) -> dict[str, Any]:
    return {
        "schema": SCHEMA, "status": status, "target": TARGET,
        "test_connector_injected": local,
        "remote_staging_reopen_observed": verified and not local,
        "original_import_history_preserved": verified,
        "sovmem_main_connected": False,
        "original_production_connected": False,
        "provider_database_separation_independently_verified": False,
        "real_owner_identity_verified": False,
        "staging_token_scope_independently_verified": False,
        "gravity_modified": False, "e_lanes_modified": False,
        "mode_control_modified": False, "bigbang_activated": False,
        "archived_rows_promoted": 0,
        "staging_rollback_outcome_uncertain": uncertain,
        "writes_performed": (
            ["STAGING_ROLLBACK_COMMIT_UNVERIFIED"] if uncertain
            else ["EXACT_FIRST_STAGING_ROWS_REMOVED",
                  "SIGNED_ROLLBACK_RECEIPT_RETAINED"]
            if verified and not replay else []
        ),
        "proof_boundary": (
            "Local connector injection is NEVER remote Turso evidence. "
            "Even a real fresh staging readback does not prove owner identity, "
            "provider aliases, restricted credential scope, replica durability, "
            "independent recovery, complete migration or BIGBANG authorization."
        ),
    }


def _source_items(receipt: Any) -> list[dict[str, Any]] | None:
    """Extract exact Stage 9AG receipt provenance without any source statements."""
    if not isinstance(receipt, dict) or not isinstance(receipt.get("items"), list):
        return None
    entries = receipt["items"]
    if not 1 <= len(entries) <= MAX_BATCH:
        return None
    items = []
    for i, entry in enumerate(entries):
        if (not isinstance(entry, dict)
                or entry.get("index") != i
                or entry.get("status") != y.STATUS
                or not isinstance(entry.get("record_id"), str)
                or y.ID.fullmatch(entry["record_id"]) is None
                or not isinstance(entry.get("receipt_id"), str)
                or y.ID.fullmatch(entry["receipt_id"]) is None
                or any(
                    not isinstance(entry.get(key), str)
                    or y.HEX.fullmatch(entry[key]) is None
                    for key in (
                        "source_key_sha256", "statement_sha256",
                        "metadata_sha256", "row_sha256",
                    )
                )):
            return None
        items.append({
            "index": i, "proposed_record_id": entry["record_id"],
            "source_key_sha256": entry["source_key_sha256"],
            "statement_sha256": entry["statement_sha256"],
            "metadata_sha256": entry["metadata_sha256"],
        })
    if len({item["proposed_record_id"] for item in items}) != len(items):
        return None
    if len({item["source_key_sha256"] for item in items}) != len(items):
        return None
    return items


def _origin_signed(
    config: Any, pin: Any, original: Any, original_signature: Any,
    original_key: Any, receipt: Any, independently_pinned_receipt_sha256: Any,
) -> list[dict[str, Any]] | None:
    """Reconstruct original independent 9AG approval and exact receipt hash."""
    try:
        items = _source_items(receipt)
        if (items is None or not isinstance(original, dict)
                or not isinstance(original_key, bytes)
                or len(original_key) < 32
                or not isinstance(independently_pinned_receipt_sha256, str)
                or y.HEX.fullmatch(independently_pinned_receipt_sha256) is None
                or not aa._canonical_pin(config, pin)
                or original.get("canary_sha256") != pin["canary_sha256"]
                or receipt.get("schema") != ag.SCHEMA
                or receipt.get("target") != ag.TARGET
                or receipt.get("historical_status") != y.STATUS
                or receipt.get("remote_observation_pending_external_review") is not True
                or receipt.get("approval_id") != original.get("approval_id")
                or receipt.get("manifest_sha256") != y._sha(y._bytes(original))
                or receipt.get("export_sha256") != original.get("export_sha256")
                or receipt.get("source_sha256") != original.get("source_sha256")
                or receipt.get("canary_sha256") != pin["canary_sha256"]
                or receipt.get("receipt_sha256") !=
                y._sha(y._bytes({k: val for k, val in receipt.items()
                                 if k != "receipt_sha256"}))
                or receipt["receipt_sha256"] !=
                independently_pinned_receipt_sha256):
            return None
        expected = ag.expected_approval(
            config=config, pin=pin, approval_id=original["approval_id"],
            export_sha256=original["export_sha256"],
            source_sha256=original["source_sha256"], items=items,
        )
        if expected is None or not y._signed_exact(
            original, original_signature, original_key, expected,
        ):
            return None
        return items
    except (KeyError, TypeError, ValueError, OverflowError):
        return None


def expected_rollback_approval(
    *, config: dict[str, str], pin: dict[str, Any],
    original_approval: dict[str, Any], original_receipt: dict[str, Any],
    pinned_import_receipt_sha256: str, rollback_id: str,
) -> dict[str, Any] | None:
    """Separate signed 9AH action can NEVER reuse 9Z LOCAL rollback approval."""
    try:
        if (not isinstance(rollback_id, str)
                or y.ID.fullmatch(rollback_id) is None
                or _source_items(original_receipt) is None
                or not aa._canonical_pin(config, pin)
                or not isinstance(original_approval, dict)
                or original_approval.get("schema") != ag.APPROVAL_SCHEMA
                or original_approval.get("target") != ag.TARGET
                or original_approval.get("action") !=
                "WRITE_FIRST_SIGNED_HELD_STAGING_BATCH"
                or original_approval.get("expected_staging_id") !=
                config["expected_staging_id"]
                or original_approval.get("staging_url_sha256") !=
                pin["staging_url_sha256"]
                or original_approval.get("production_url_sha256") !=
                pin["production_url_sha256"]
                or original_receipt.get("receipt_sha256") !=
                pinned_import_receipt_sha256):
            return None
        return {
            "schema": APPROVAL_SCHEMA, "authority": "NAOMI",
            "target": TARGET, "action": "ROLL_BACK_EXACT_FIRST_STAGING_HOLD_BATCH",
            "rollback_id": rollback_id,
            "import_approval_id": original_approval["approval_id"],
            "import_manifest_sha256": y._sha(y._bytes(original_approval)),
            "import_receipt_sha256": pinned_import_receipt_sha256,
            "staging_url_sha256": pin["staging_url_sha256"],
            "production_url_sha256": pin["production_url_sha256"],
            "staging_uuid_sha256": pin["staging_uuid_sha256"],
            "canary_run_id": pin["run_id"],
            "canary_sha256": pin["canary_sha256"],
            "rows": [
                {
                    "record_id": entry["record_id"],
                    "source_key_sha256": entry["source_key_sha256"],
                    "row_sha256": entry["row_sha256"],
                } for entry in original_receipt["items"]
            ],
        }
    except (KeyError, TypeError, ValueError, OverflowError):
        return None


def _batch(conn: Any, import_id: str) -> dict[str, Any] | None:
    return ag._row(
        conn, "galaxy_stage9y_batches", "approval_id", import_id,
    )


def _rollback_ledger(conn: Any) -> list[dict[str, Any]]:
    cursor = conn.execute(
        f"SELECT {','.join(y.z.LEDGER_COLS)} FROM galaxy_stage9z_rollbacks"
    )
    result = []
    for row in cursor.fetchall():
        keys = y.z.LEDGER_COLS
        result.append(dict(row) if hasattr(row, "keys") else dict(zip(keys, row)))
    return result


def _check_deleted(
    conn: Any, *, config: dict[str, str], pin: dict[str, Any],
    original: dict[str, Any], original_receipt: dict[str, Any],
    original_key: bytes, rollback_approval: dict[str, Any],
    rollback_receipt: dict[str, Any], rollback_key: bytes,
) -> bool:
    """Verify unchanged original history and exact signed rollback postimage."""
    try:
        if not ag._safe_schema(conn, config, pin):
            return False
        batch = _batch(conn, original["approval_id"])
        ledgers = _rollback_ledger(conn)
        if (batch is None or len(ledgers) != 1
                or batch["status"] != ROLLED_BACK
                or batch["manifest_sha256"] !=
                y._sha(y._bytes(original))
                or batch["export_sha256"] != original["export_sha256"]
                or batch["source_sha256"] != original["source_sha256"]
                or batch["canary_sha256"] != pin["canary_sha256"]
                or batch["receipt_json"] != y._bytes(original_receipt).decode()
                or not hmac.compare_digest(
                    batch["receipt_hmac_sha256"],
                    hmac.new(original_key, y._bytes(original_receipt),
                             hashlib.sha256).hexdigest(),
                )
                or rollback_receipt.get("schema") != SCHEMA
                or rollback_receipt.get("target") != TARGET
                or rollback_receipt.get("status") != ROLLED_BACK
                or rollback_receipt.get("rollback_id") !=
                rollback_approval["rollback_id"]
                or rollback_receipt.get("import_approval_id") !=
                original["approval_id"]
                or rollback_receipt.get("manifest_sha256") !=
                y._sha(y._bytes(rollback_approval))
                or rollback_receipt.get("import_receipt_sha256") !=
                original_receipt["receipt_sha256"]
                or rollback_receipt.get("canary_sha256") !=
                pin["canary_sha256"]
                or rollback_receipt.get("deleted_exact_held_rows") !=
                len(original_receipt["items"])
                or rollback_receipt.get("original_import_ledgers_retained")
                is not True
                or rollback_receipt.get("receipt_sha256") !=
                y._sha(y._bytes({k: val for k, val in rollback_receipt.items()
                                 if k != "receipt_sha256"}))
                or rollback_receipt.get("items") != [
                    {
                        "record_id": item["record_id"],
                        "row_sha256": item["row_sha256"],
                        "source_key_sha256": item["source_key_sha256"],
                    } for item in original_receipt["items"]
                ]):
            return False
        saved = ledgers[0]
        if (saved["rollback_id"] != rollback_approval["rollback_id"]
                or saved["import_approval_id"] != original["approval_id"]
                or saved["rollback_manifest_sha256"] !=
                rollback_receipt["manifest_sha256"]
                or saved["import_receipt_sha256"] !=
                original_receipt["receipt_sha256"]
                or saved["receipt_json"] != y._bytes(rollback_receipt).decode()
                or saved["status"] != ROLLED_BACK
                or not hmac.compare_digest(
                    saved["receipt_hmac_sha256"],
                    hmac.new(rollback_key, y._bytes(rollback_receipt),
                             hashlib.sha256).hexdigest(),
                )
                or conn.execute(
                    "SELECT COUNT(*) FROM memory_records"
                ).fetchone()[0] != 0
                or conn.execute(
                    "SELECT COUNT(*) FROM galaxy_stage9y_batches"
                ).fetchone()[0] != 1
                or conn.execute(
                    "SELECT COUNT(*) FROM galaxy_stage9y_items"
                ).fetchone()[0] != len(original_receipt["items"])):
            return False
        for item in original_receipt["items"]:
            logged = ag._row(
                conn, "galaxy_stage9y_items", "receipt_id", item["receipt_id"],
            )
            if (logged is None or logged["approval_id"] !=
                original["approval_id"]
                or logged["record_id"] != item["record_id"]
                or logged["source_key_sha256"] != item["source_key_sha256"]
                or logged["statement_sha256"] != item["statement_sha256"]
                or logged["metadata_sha256"] != item["metadata_sha256"]
                or logged["row_sha256"] != item["row_sha256"]
                or logged["result"] != ag.RESULT
                or ag._row(
                    conn, "memory_records", "record_id", item["record_id"],
                ) is not None
                or conn.execute(
                    "SELECT COUNT(*) FROM memory_records WHERE source=?",
                    ("galaxy-archive-v1:" + item["source_key_sha256"],),
                ).fetchone()[0] != 0):
                return False
        return True
    except Exception:
        return False


def rollback_first_staging_batch(
    *, config: dict[str, str], pin: dict[str, Any],
    original_approval: dict[str, Any], original_signature: str,
    original_key: bytes, original_receipt: dict[str, Any],
    pinned_import_receipt_sha256: str,
    rollback_approval: dict[str, Any], rollback_signature: str,
    rollback_key: bytes,
    apply: bool = False, confirm_exact_original_row_review: bool = False,
    confirm_independent_import_receipt_pin: bool = False,
    confirm_provider_identity_reviewed: bool = False,
    confirm_staging_only_credential_reviewed: bool = False,
    confirm_irreversible_staging_row_removal: bool = False,
    connector: Callable[[str, str], Any] | None = None,
) -> dict[str, Any]:
    """Exact signed original + distinct rollback signature before any socket.

    APPLY is an owner-local future gate only. Caller provides all private
    materials explicitly, not via public CI or server HTTP. No source loader.
    """
    local = connector is not None
    items = _origin_signed(
        config, pin, original_approval, original_signature, original_key,
        original_receipt, pinned_import_receipt_sha256,
    )
    if items is None or not isinstance(rollback_key, bytes) or len(rollback_key) < 32:
        return _report("HOLD_SIGNED_ORIGINAL_IMPORT_AND_PIN_REQUIRED", local=local)
    if hmac.compare_digest(original_key, rollback_key):
        return _report("HOLD_INDEPENDENT_ROLLBACK_KEY_REQUIRED", local=local)
    expected = expected_rollback_approval(
        config=config, pin=pin, original_approval=original_approval,
        original_receipt=original_receipt,
        pinned_import_receipt_sha256=pinned_import_receipt_sha256,
        rollback_id=rollback_approval.get("rollback_id")
        if isinstance(rollback_approval, dict) else None,
    )
    if expected is None or not y._signed_exact(
        rollback_approval, rollback_signature, rollback_key, expected,
    ):
        return _report("HOLD_SEPARATELY_SIGNED_EXACT_ROLLBACK_REQUIRED", local=local)
    if not apply:
        out = _report("PASS_SIGNED_ROLLBACK_DRY_RUN_ZERO_CONNECTION", local=local)
        out["exact_held_rows_in_signed_manifest"] = len(items)
        return out
    if not all(flag is True for flag in (
        confirm_exact_original_row_review,
        confirm_independent_import_receipt_pin,
        confirm_provider_identity_reviewed,
        confirm_staging_only_credential_reviewed,
        confirm_irreversible_staging_row_removal,
    )):
        return _report("HOLD_FIVE_SEPARATE_ROLLBACK_CONFIRMATIONS_REQUIRED",
                       local=local)

    connect = connector if local else v._connect_live
    conn = None
    replay = False
    rollback_receipt = None
    status = None
    try:
        conn = connect(config["staging_url"], config["staging_token"])
        if not ag._safe_schema(conn, config, pin):
            status = "HOLD_STAGING_SCHEMA_MARKER_OR_CANARY_CHANGED"
        else:
            batch = _batch(conn, original_approval["approval_id"])
            if batch is None:
                status = "HOLD_ORIGINAL_STAGING_IMPORT_MISSING"
            else:
                ledgers = _rollback_ledger(conn)
                if len(ledgers) > 1:
                    status = "HOLD_UNEXPECTED_ROLLBACK_LEDGERS"
                elif len(ledgers) == 1:
                    row = ledgers[0]
                    if (row["rollback_id"] != rollback_approval["rollback_id"]
                            or row["import_approval_id"] !=
                            original_approval["approval_id"]):
                        status = "HOLD_DIFFERENT_ROLLBACK_ALREADY_RECORDED"
                    else:
                        rollback_receipt = json.loads(row["receipt_json"])
                        if not _check_deleted(
                            conn, config=config, pin=pin,
                            original=original_approval,
                            original_receipt=original_receipt,
                            original_key=original_key,
                            rollback_approval=rollback_approval,
                            rollback_receipt=rollback_receipt,
                            rollback_key=rollback_key,
                        ):
                            status = "HOLD_SIGNED_ROLLBACK_REPLAY_DRIFT"
                        else:
                            replay = True
                elif not ag._receipt_ok(
                    conn, original_receipt, items, original_approval,
                    original_key,
                ):
                    status = "HOLD_ORIGINAL_HELD_ROWS_OR_LEDGER_CHANGED"
    except Exception:
        status = "HOLD_STAGING_PRE_ROLLBACK_READ_UNAVAILABLE"
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                status = "HOLD_STAGING_PRE_ROLLBACK_CLOSE_UNVERIFIED"
    if status:
        return _report(status, local=local)
    if replay:
        return _fresh(
            config=config, pin=pin, original=original_approval,
            original_receipt=original_receipt, original_key=original_key,
            rollback_approval=rollback_approval,
            rollback_receipt=rollback_receipt, rollback_key=rollback_key,
            connector=connector, replay=True, committed=False,
        )

    attempted = False
    committed = False
    conn = None
    status = None
    try:
        conn = connect(config["staging_url"], config["staging_token"])
        conn.execute("BEGIN IMMEDIATE")
        if (not ag._safe_schema(conn, config, pin)
                or not ag._receipt_ok(
                    conn, original_receipt, items, original_approval,
                    original_key,
                )
                or _rollback_ledger(conn)):
            conn.rollback()
            status = "HOLD_STAGING_OR_SIGNED_BATCH_CHANGED_BEFORE_DELETE"
        else:
            attempted = True
            for entry in original_receipt["items"]:
                conn.execute(
                    "DELETE FROM memory_records WHERE record_id=? "
                    "AND source=? AND scope='MemoryOS' AND status=?",
                    (
                        entry["record_id"],
                        "galaxy-archive-v1:" + entry["source_key_sha256"],
                        y.STATUS,
                    ),
                )
                # Driver-neutral postcondition, no dependence on rowcount.
                if (ag._row(
                    conn, "memory_records", "record_id", entry["record_id"],
                ) is not None
                        or conn.execute(
                            "SELECT COUNT(*) FROM memory_records WHERE source=?",
                            ("galaxy-archive-v1:" + entry["source_key_sha256"],),
                        ).fetchone()[0] != 0):
                    raise ValueError("exact held row not deleted")
            conn.execute(
                "UPDATE galaxy_stage9y_batches SET status=? "
                "WHERE approval_id=? AND status=?",
                (ROLLED_BACK, original_approval["approval_id"], y.STATUS),
            )
            now = datetime.now(timezone.utc).isoformat()
            rollback_receipt = {
                "schema": SCHEMA, "target": TARGET, "status": ROLLED_BACK,
                "rollback_id": rollback_approval["rollback_id"],
                "import_approval_id": original_approval["approval_id"],
                "manifest_sha256": y._sha(y._bytes(rollback_approval)),
                "import_receipt_sha256": pinned_import_receipt_sha256,
                "canary_sha256": pin["canary_sha256"],
                "created_at": now,
                "deleted_exact_held_rows": len(items),
                "original_import_ledgers_retained": True,
                "items": rollback_approval["rows"],
            }
            rollback_receipt["receipt_sha256"] = y._sha(
                y._bytes(rollback_receipt)
            )
            conn.execute(
                f"INSERT INTO galaxy_stage9z_rollbacks "
                f"({','.join(y.z.LEDGER_COLS)}) VALUES "
                f"({','.join('?' for _ in y.z.LEDGER_COLS)})",
                (
                    rollback_approval["rollback_id"],
                    original_approval["approval_id"],
                    rollback_receipt["manifest_sha256"],
                    pinned_import_receipt_sha256,
                    y._bytes(rollback_receipt).decode(),
                    hmac.new(
                        rollback_key, y._bytes(rollback_receipt),
                        hashlib.sha256,
                    ).hexdigest(),
                    ROLLED_BACK, now,
                ),
            )
            # Verify exact postimage in SAME atomic transaction.
            if not _check_deleted(
                conn, config=config, pin=pin,
                original=original_approval, original_receipt=original_receipt,
                original_key=original_key,
                rollback_approval=rollback_approval,
                rollback_receipt=rollback_receipt,
                rollback_key=rollback_key,
            ):
                raise ValueError("atomic signed rollback postimage changed")
            conn.commit()
            committed = True
    except Exception:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        return _report(
            "HOLD_STAGING_ROLLBACK_TRANSACTION_OR_ACK_UNVERIFIED",
            local=local, uncertain=attempted,
        )
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                status = "HOLD_STAGING_ROLLBACK_CONNECTION_CLOSE_UNVERIFIED"
    if status:
        return _report(status, local=local, uncertain=attempted or committed)
    return _fresh(
        config=config, pin=pin, original=original_approval,
        original_receipt=original_receipt, original_key=original_key,
        rollback_approval=rollback_approval,
        rollback_receipt=rollback_receipt, rollback_key=rollback_key,
        connector=connector, replay=False, committed=committed,
    )


def _fresh(
    *, config: dict[str, str], pin: dict[str, Any],
    original: dict[str, Any], original_receipt: dict[str, Any],
    original_key: bytes, rollback_approval: dict[str, Any],
    rollback_receipt: dict[str, Any], rollback_key: bytes,
    connector: Callable[[str, str], Any] | None,
    replay: bool, committed: bool,
) -> dict[str, Any]:
    local = connector is not None
    connect = connector if local else v._connect_live
    conn = None
    status = None
    try:
        conn = connect(config["staging_url"], config["staging_token"])
        if not _check_deleted(
            conn, config=config, pin=pin, original=original,
            original_receipt=original_receipt, original_key=original_key,
            rollback_approval=rollback_approval,
            rollback_receipt=rollback_receipt, rollback_key=rollback_key,
        ):
            status = "HOLD_FRESH_SIGNED_ROLLBACK_POSTIMAGE_CHANGED"
    except Exception:
        status = "HOLD_FRESH_STAGING_ROLLBACK_REOPEN_UNAVAILABLE"
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                status = "HOLD_FRESH_STAGING_ROLLBACK_CLOSE_UNVERIFIED"
    if status:
        return _report(status, local=local, uncertain=committed)
    out = _report(
        "PASS_LOCAL_SIGNED_ROLLBACK_FRESH_REOPEN_FIXTURE" if local and not replay
        else "PASS_LOCAL_SIGNED_ROLLBACK_REPLAY_ZERO_WRITE" if local
        else "PASS_STAGING_SIGNED_ROLLBACK_FRESH_REOPEN" if not replay
        else "PASS_STAGING_SIGNED_ROLLBACK_REPLAY_ZERO_WRITE",
        local=local, verified=True, replay=replay,
    )
    out.update({
        "exact_held_rows_removed": len(original_receipt["items"]),
        "original_item_receipts_retained": len(original_receipt["items"]),
        "signed_rollback_receipts_retained": 1,
        "signed_rollback_receipt_sha256": rollback_receipt["receipt_sha256"],
        "independent_fresh_staging_readback": True,
        "zero_write_exact_replay": replay,
        "next_gate": "OWNER_REVIEWED_REAL_TURSO_TEST_AND_DURABLE_RESTART_PROOF",
    })
    return out
