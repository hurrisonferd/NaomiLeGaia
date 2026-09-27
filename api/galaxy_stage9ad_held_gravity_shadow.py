"""Stage 9AD: safe LOCAL historical HOLD -> independent gravity shadow boundary.

Given a signed, already imported Stage 9Y LOCAL fixture, preserve its real
HOLD state and audit ledger while building a separate, never-persisted in-memory
SQLite snapshot. Invoke the actual Stage 9U gravity model/ledger routines
against THREE additional SYNTHETIC ACTIVE fixtures; refuse all held history.
No remote connector, Turso, HTTP, production runtime, E-LANE or mode API.
This is a test integration, NOT approval to activate any historical memory.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
from pathlib import Path
from typing import Any

import galaxy_stage9y_canonical_staging as y
import galaxy_stage9z_local_rollback as z
import galaxy_shadow_backfill_stage9u as u

SCHEMA = "gaiaos.galaxy.stage9ad.held-history-gravity-shadow.v1"
MODEL = "galaxy.gravity.fixture.v2"
BATCH_ID = "STAGE9AD-SYNTHETIC-GRAVITY-0001"
KEY = b"stage9ad-local-shadow-test-only-not-real-authorization-0001"
ACTIVE_IDS = (
    "MEM-STAGE9AD-SYNTHETIC-A", "MEM-STAGE9AD-SYNTHETIC-B",
    "MEM-STAGE9AD-SYNTHETIC-C",
)


def _report(status: str, **safe_counts: Any) -> dict[str, Any]:
    out: dict[str, Any] = {
        "schema": SCHEMA, "status": status,
        "target": "SIGNED_LOCAL_STAGE9Y_FIXTURE_TO_ISOLATED_IN_MEMORY_9U",
        "test_only": True, "remote_turso_accessed": False,
        "real_sovmem_staging_accessed": False,
        "real_sovmem_main_accessed": False,
        "production_memory_modified": False,
        "staged_history_activated": False,
        "held_historical_gravity_rows_written": 0,
        "staging_fixture_gravity_rows_written": 0,
        "e_lanes_modified": False, "bigbang_activated": False,
        "source_original_and_receipts_retained": False,
        "live_owner_identity_verified": False,
        "preview_model_calibration_verified": False,
        "proof_boundary": (
            "Signed test-key provenance + in-memory-only Stage 9U gravity. "
            "No real historic record activated or gravity backfilled on disk; "
            "no live model calibration, remote staging, replica or cutover."
        ),
    }
    out.update(safe_counts)
    return out


def _shadow_schema(conn: sqlite3.Connection) -> None:
    """Adds only Stage 9U's original five support tables to an IN-MEMORY copy."""
    conn.executescript("""
    CREATE TABLE memory_gravity (
        record_id TEXT PRIMARY KEY, gravity_score REAL NOT NULL,
        score_version TEXT NOT NULL, components_json TEXT NOT NULL,
        reason_json TEXT NOT NULL, calculated_at TEXT NOT NULL,
        previous_score REAL
    );
    CREATE TABLE memory_relations (
        edge_id TEXT PRIMARY KEY, source_record_id TEXT NOT NULL,
        target_record_id TEXT NOT NULL, relation_type TEXT NOT NULL,
        strength REAL NOT NULL, status TEXT NOT NULL,
        evidence_json TEXT NOT NULL, classifier TEXT NOT NULL,
        authority TEXT NOT NULL, created_at TEXT NOT NULL,
        verified_at TEXT
    );
    CREATE TABLE memory_importance (
        record_id TEXT PRIMARY KEY, gate_units INTEGER NOT NULL,
        model_version TEXT NOT NULL, updated_at TEXT NOT NULL,
        authority TEXT NOT NULL, previous_units INTEGER
    );
    CREATE TABLE memory_lifecycle (
        record_id TEXT PRIMARY KEY, state TEXT NOT NULL,
        changed_at TEXT NOT NULL, reason TEXT NOT NULL,
        authority TEXT NOT NULL, receipt_id TEXT
    );
    CREATE TABLE memory_lifecycle_events (
        event_id TEXT PRIMARY KEY, record_id TEXT NOT NULL,
        previous_event_id TEXT, from_state TEXT NOT NULL,
        to_state TEXT NOT NULL, action TEXT NOT NULL,
        changed_at TEXT NOT NULL, reason TEXT NOT NULL,
        authority TEXT NOT NULL, receipt_id TEXT NOT NULL
    );
    """)
    for rid in ACTIVE_IDS:
        conn.execute(
            "INSERT INTO memory_records VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                rid, "NAOMI", "SYNTHETIC_FIXTURE", "MemoryOS",
                "STAGE9AD-FAKE-ACTIVE-" + rid,
                "stage9ad-fake-independent-active-seed",
                "ACTIVE", "1", "2025-01-01", "2025-01-01",
                None, "{}",
            ),
        )
    conn.execute(
        "INSERT INTO memory_gravity VALUES (?,?,?,?,?,?,?)",
        (ACTIVE_IDS[1], .36, "galaxy.gravity.fixture.v1",
         '{"old":1}', '{"old":true}', "2025-01-01", None),
    )
    conn.execute(
        "INSERT INTO memory_gravity VALUES (?,?,?,?,?,?,?)",
        (ACTIVE_IDS[2], .9, MODEL,
         '{"current":1}', '{"current":true}', "2025-01-01", None),
    )
    conn.execute(
        "INSERT INTO memory_importance VALUES (?,?,?,?,?,?)",
        (ACTIVE_IDS[1], 3, "SEVEN_GATES", "2025-01-01", "NAOMI", None),
    )
    conn.execute(
        "INSERT INTO memory_relations VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            "STAGE9AD-SYNTHETIC-EDGE", ACTIVE_IDS[0], ACTIVE_IDS[1],
            "REINFORCES", .7, "VERIFIED", "{}",
            "SYNTHETIC_FIXTURE", "NAOMI", "2025-01-01", "2025-01-01",
        ),
    )
    conn.commit()


def _preview(rid: str) -> dict[str, Any]:
    return {
        "record_id": rid, "gravity_score": .61 if rid == ACTIVE_IDS[0] else .79,
        "score_version": MODEL,
        "components": {"fixture": {"normalized": .61, "weight": 1.0}},
        "reason": {"model": "SYNTHETIC_FIXTURE_ONLY"},
    }


def _sign(action: str, batch_id: str, plan_sha: str) -> dict[str, Any]:
    manifest = {
        "schema": u.APPROVAL_SCHEMA, "authority": "NAOMI",
        "target": u.TARGET, "action": action,
        "batch_id": batch_id, "plan_sha256": plan_sha,
    }
    return {
        "approval": manifest,
        "signature_hex": hmac.new(KEY, u._json(manifest), hashlib.sha256).hexdigest(),
        "approval_key": KEY,
    }


def rehearse_held_archive_gravity_shadow(
    *, fixture_connection: sqlite3.Connection,
    fixture_root: str | Path, config: dict[str, str],
    original_manifest: dict[str, Any], original_signature: str,
    original_key: bytes, original_receipt: dict[str, Any],
    confirm_synthetic_local_only: bool,
) -> dict[str, Any]:
    """Read signed Stage 9Y import, prove HOLD, exercise U only in volatile copy.

    A caller-provided file-backed fixture is accepted ONLY if native sqlite3,
    inside a separate explicitly supplied directory outside the repository,
    with exact six-table schema, ACTIVE staging marker, exact canary and
    cryptographically matching signed Stage 9Y per-row receipts.
    """
    if confirm_synthetic_local_only is not True:
        return _report("HOLD_EXPLICIT_LOCAL_SHADOW_REVIEW_REQUIRED")
    path = y._fixture_path(fixture_connection, fixture_root)
    if path is None:
        return _report("HOLD_NOT_ISOLATED_LOCAL_STAGING_FIXTURE")
    conn = fixture_connection
    if not z._protected_schema(conn):
        return _report("HOLD_UNKNOWN_STAGING_DEPENDENCIES")
    if (not isinstance(original_manifest, dict)
            or not isinstance(original_receipt, dict)
            or not isinstance(original_key, bytes) or len(original_key) < 32):
        return _report("HOLD_ORIGINAL_SIGNED_IMPORT_REQUIRED")
    try:
        marker = original_manifest["expected_staging_id"]
        run_id = original_manifest["canary_run_id"]
        canary_hash = original_manifest["canary_sha256"]
        if not y._schema_and_identity(conn, marker, run_id, canary_hash):
            return _report("HOLD_STAGING_IDENTITY_OR_CANARY_CHANGED")
        batch = y._row(conn.execute(
            f"SELECT {','.join(y.BATCH_COLS)} FROM galaxy_stage9y_batches "
            "WHERE approval_id=?", (original_manifest["approval_id"],),
        ))
        if (batch is None or batch["status"] != y.STATUS
                or batch["receipt_json"] != y._bytes(original_receipt).decode()):
            return _report("HOLD_ORIGINAL_STAGED_BATCH_MISSING")
        if not z._original_signed(
            original_manifest, original_signature, original_key, config,
            batch, original_receipt,
        ):
            return _report("HOLD_ORIGINAL_SIGNED_RECEIPT_INVALID")
        if not y._check_receipt(
            conn, original_receipt, z._items(original_receipt),
        ):
            return _report("HOLD_ORIGINAL_ROW_OR_ITEM_LEDGER_DRIFT")
        ids = tuple(item["record_id"] for item in original_receipt["items"])
        if not 1 <= len(ids) <= y.BATCH_CAP:
            return _report("HOLD_ORIGINAL_ITEM_COUNT")
        for rid in ids:
            record = y._stored_record(conn, rid)
            if (record is None or record["scope"] != "MemoryOS"
                    or record["status"] != y.STATUS):
                return _report("HOLD_ARCHIVAL_STATUS_OR_SCOPE_CHANGED")
        original_bytes = path.read_bytes()
        original_total_changes = conn.total_changes
    except (KeyError, TypeError, ValueError, sqlite3.Error, OSError):
        return _report("HOLD_ORIGINAL_LOCAL_PROOF_UNREADABLE")

    shadow = sqlite3.connect(":memory:")
    try:
        # SQLite backup's destination is volatile, never an attached file.
        conn.backup(shadow)
        if not u._isolated(shadow):
            return _report("HOLD_NOT_IN_MEMORY_SHADOW")
        if any(
            shadow.execute(
                "SELECT status FROM memory_records WHERE record_id=?", (rid,),
            ).fetchone() != (y.STATUS,) for rid in ids
        ):
            return _report("HOLD_SHADOW_HISTORICAL_STATUS_CHANGED")
        _shadow_schema(shadow)
        # Stage 9U MUST refuse the held records. No preview should ever
        # convert them to an ACTIVE/current memory or infer owner importance.
        before_held = shadow.total_changes
        held_attempt = u.make_shadow_plan(
            shadow, record_ids=list(ids), score_version=MODEL, preview=_preview,
        )
        if (held_attempt.get("status") != "HOLD_PLAN_FAILED"
                or shadow.total_changes != before_held
                or shadow.execute(
                    "SELECT count(*) FROM memory_gravity "
                    f"WHERE record_id IN ({','.join('?' for _ in ids)})",
                    ids,
                ).fetchone()[0] != 0):
            return _report("HOLD_UNVERIFIED_ARCHIVE_ELIGIBILITY_BYPASS")
        original_records = shadow.execute(
            "SELECT * FROM memory_records ORDER BY record_id",
        ).fetchall()
        original_gravity = shadow.execute(
            "SELECT * FROM memory_gravity ORDER BY record_id",
        ).fetchall()
        # Three independently seeded SYNTHETIC ACTIVE records demonstrate
        # INSERT / UPDATE / SKIP using the REAL Stage 9U engine and receipts.
        plan = u.make_shadow_plan(
            shadow, record_ids=list(ACTIVE_IDS),
            score_version=MODEL, preview=_preview,
        )
        if (plan.get("status") != "PASS_READ_ONLY_PLAN"
                or plan.get("pending_count") != 2
                or plan.get("owner_importance_unset_count") != 2
                or [i["action"] for i in plan["plan"]["entries"]] != [
                    "UPSERT_SHADOW", "UPSERT_SHADOW", "SKIP_CURRENT",
                ]):
            return _report("HOLD_ACTIVE_SYNTHETIC_SHADOW_PLAN")
        args = {
            "plan": plan["plan"], "batch_id": BATCH_ID,
            **_sign("APPLY", BATCH_ID, plan["plan_sha256"]),
        }
        applied = u.apply_shadow_plan(shadow, **args)
        if (applied.get("status") != "PASS_IN_MEMORY_BACKFILL_READBACK"
                or [x["action"] for x in applied["receipt"]["items"]] != [
                    "INSERTED_SHADOW", "UPDATED_SHADOW", "SKIP_CURRENT",
                ]):
            return _report("HOLD_SHADOW_BACKFILL_NOT_PROVEN")
        after_apply = shadow.total_changes
        replay = u.apply_shadow_plan(shadow, **args)
        if (replay.get("status") != "PASS_REPLAY_VERIFIED"
                or shadow.total_changes != after_apply):
            return _report("HOLD_SHADOW_APPLY_REPLAY_CHANGED")
        rolled = u.rollback_shadow_batch(
            shadow, batch_id=BATCH_ID, plan_sha256=plan["plan_sha256"],
            **_sign("ROLLBACK", BATCH_ID, plan["plan_sha256"]),
        )
        if (rolled.get("status") != "PASS_IN_MEMORY_ROLLBACK_READBACK"
                or rolled.get("restored_count") != 2):
            return _report("HOLD_SHADOW_ROLLBACK_NOT_PROVEN")
        after_rollback = shadow.total_changes
        rolled_replay = u.rollback_shadow_batch(
            shadow, batch_id=BATCH_ID, plan_sha256=plan["plan_sha256"],
            **_sign("ROLLBACK", BATCH_ID, plan["plan_sha256"]),
        )
        if (rolled_replay.get("status") != "PASS_ALREADY_ROLLED_BACK"
                or shadow.total_changes != after_rollback):
            return _report("HOLD_SHADOW_ROLLBACK_REPLAY_CHANGED")
        if (shadow.execute(
            "SELECT * FROM memory_records ORDER BY record_id",
        ).fetchall() != original_records
                or shadow.execute(
                    "SELECT * FROM memory_gravity ORDER BY record_id",
                ).fetchall() != original_gravity
                or shadow.execute(
                    "SELECT count(*) FROM memory_gravity "
                    f"WHERE record_id IN ({','.join('?' for _ in ids)})",
                    ids,
                ).fetchone()[0] != 0
                or shadow.execute(
                    "SELECT count(*) FROM galaxy_stage9u_item_ledger",
                ).fetchone()[0] != 3):
            return _report("HOLD_SHADOW_FINAL_ROW_OR_LEDGER_DRIFT")
    except Exception as exc:
        return _report("HOLD_ISOLATED_SHADOW_GRAVITY_FAILED",
                       exception_type=type(exc).__name__)
    finally:
        shadow.close()

    # The SOURCE of the snapshot, including its original signed importer
    # ledger and canary, must remain byte-for-byte unchanged.
    try:
        if (conn.total_changes != original_total_changes
                or path.read_bytes() != original_bytes):
            return _report("HOLD_STAGING_FIXTURE_CHANGED")
    except OSError:
        return _report("HOLD_STAGING_FIXTURE_READBACK_UNAVAILABLE")
    return _report(
        "PASS_LOCAL_HELD_ARCHIVE_GRAVITY_SHADOW_REHEARSAL",
        held_historical_records_preserved=len(ids),
        active_synthetic_records_exercised=3,
        synthetic_shadow_scores_inserted=1,
        synthetic_shadow_scores_updated=1,
        synthetic_current_scores_skipped=1,
        independent_shadow_replay_zero_write=True,
        independent_shadow_rollback_zero_write_replay=True,
        owner_importance_absent_preserved_as_unset=True,
        original_signed_staging_unchanged=True,
        source_original_and_receipts_retained=True,
        in_memory_only_shadow_ledger_rows=3,
    )
