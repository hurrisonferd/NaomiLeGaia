"""Stage 9Z: exact isolated rollback and anti-resurrection safety tests."""
from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))
sys.path.insert(0, str(ROOT / "tests"))

import galaxy_stage9y_canonical_staging as y
import galaxy_stage9z_local_rollback as z
from test_galaxy_stage9y_canonical_staging import (
    CanonicalFixtureTests, CONFIG, SOURCE, record,
)

ROLLBACK_KEY = b"stage9z-distinct-test-rollback-key-not-real-human-authorization"


class SignedLocalRollbackTests(unittest.TestCase):
    def setUp(self):
        self.fx = CanonicalFixtureTests(
            "test_atomic_one_record_import_ledger_and_independent_reopen"
        )
        self.fx.setUp()
        self.addCleanup(self.fx.doCleanups)
        self.fx.conn.execute("""
            CREATE TABLE galaxy_stage9z_rollbacks (
                rollback_id TEXT PRIMARY KEY,
                import_approval_id TEXT NOT NULL UNIQUE,
                rollback_manifest_sha256 TEXT NOT NULL,
                import_receipt_sha256 TEXT NOT NULL,
                receipt_json TEXT NOT NULL,
                receipt_hmac_sha256 TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        self.fx.conn.commit()
        self.original = self.fx.packet()
        self.first = self.fx.run_fixture(self.original)
        self.assertEqual(
            self.first["status"], "PASS_LOCAL_CANONICAL_STAGING_REOPEN_FIXTURE",
            self.first,
        )
        self.rollback_id = "stage9z-fixture-rollback-0001"

    def packet(self, *, rollback_id=None):
        manifest = z.expected_rollback_manifest(
            original_manifest=self.original["approval"],
            original_receipt=self.first["receipt"],
            rollback_id=rollback_id or self.rollback_id,
        )
        return {
            "fixture_connection": self.fx.conn,
            "fixture_root": self.fx.root,
            "config": CONFIG,
            "original_manifest": self.original["approval"],
            "original_signature": self.original["signature_hex"],
            "original_key": self.original["approval_key"],
            "rollback_manifest": manifest,
            "rollback_signature": hmac.new(
                ROLLBACK_KEY, y._bytes(manifest), hashlib.sha256,
            ).hexdigest(),
            "rollback_key": ROLLBACK_KEY,
            "confirm_exact_rollback": True,
            "confirm_no_live_target": True,
            "confirm_retained_ledger": True,
        }

    def rollback(self, data=None, **changes):
        return z.rollback_local_import(
            **{**(data or self.packet()), **changes},
        )

    def state(self):
        return (
            self.fx.conn.execute("SELECT COUNT(*) FROM memory_records").fetchone()[0],
            self.fx.conn.execute("SELECT COUNT(*) FROM galaxy_stage9y_batches").fetchone()[0],
            self.fx.conn.execute("SELECT COUNT(*) FROM galaxy_stage9y_items").fetchone()[0],
            self.fx.conn.execute("SELECT COUNT(*) FROM galaxy_stage9z_rollbacks").fetchone()[0],
        )

    def protected(self):
        self.fx.assert_original_untouched()
        self.assertEqual(
            self.fx.conn.execute("SELECT COUNT(*) FROM galaxy_stage9v_canaries").fetchone()[0],
            1,
        )

    def test_signed_exact_rollback_removes_only_new_rows_and_retains_receipts(self):
        self.fx.conn.execute(
            "INSERT INTO memory_records VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                "MEM-EXISTING-SENTINEL", "NAOMI", "TEST", "MemoryOS",
                "PRESERVE-EXISTING-ROW", "preexisting-nonarchive",
                "ACTIVE", "1", "2026-01-01", "2026-01-01", None, "{}",
            ),
        )
        self.fx.conn.commit()
        result = self.rollback()
        self.assertEqual(result["status"], "PASS_LOCAL_ROLLBACK_RECEIPT_REOPEN", result)
        self.assertEqual(result["writes_performed"], [
            "LOCAL_FIXTURE_NEW_ROWS_REMOVED",
            "LOCAL_FIXTURE_SIGNED_ROLLBACK_LEDGER_RETAINED",
        ])
        self.assertTrue(result["fresh_local_connection_readback"])
        self.assertTrue(result["original_import_ledgers_retained"])
        self.assertFalse(result["remote_turso_accessed"])
        self.assertFalse(result["live_owner_identity_verified"])
        self.assertFalse(result["e_lanes_modified"])
        self.assertFalse(result["bigbang_activated"])
        self.assertEqual(self.state(), (1, 1, 1, 1))
        self.assertEqual(
            self.fx.conn.execute(
                "SELECT statement FROM memory_records WHERE record_id='MEM-EXISTING-SENTINEL'"
            ).fetchone(), ("PRESERVE-EXISTING-ROW",),
        )
        self.assertEqual(
            self.fx.conn.execute("SELECT status FROM galaxy_stage9y_batches").fetchone(),
            (z.ROLLED_BACK,),
        )
        self.assertNotIn("PRIVATE-MEMORY-LINE", json.dumps(result))
        self.assertNotIn("PRIVATE-DOCUMENT-ID", json.dumps(result))
        self.protected()

    def test_second_rollback_is_exact_zero_write_and_preserves_receipt(self):
        first = self.rollback()
        before = self.fx.conn.total_changes
        second = self.rollback()
        self.assertEqual(second["status"], "PASS_LOCAL_ROLLBACK_EXACT_REPLAY_ZERO_WRITE")
        self.assertEqual(first["rollback_receipt"], second["rollback_receipt"])
        self.assertEqual(second["writes_performed"], [])
        self.assertTrue(second["idempotent_replay"])
        self.assertEqual(self.fx.conn.total_changes, before)
        self.assertEqual(self.state(), (0, 1, 1, 1))
        self.protected()

    def test_signature_tampering_and_missing_confirmations_never_delete(self):
        good = self.packet()
        cases = (
            {"rollback_signature": "0" * 64},
            {"rollback_key": b"wrong-test-key" * 4},
            {"original_signature": "0" * 64},
            {"original_key": b"wrong-import-key" * 3},
            {"rollback_key": good["original_key"]},
            {"rollback_manifest": {**good["rollback_manifest"], "target": "PRODUCTION"}},
            {"rollback_manifest": {**good["rollback_manifest"], "action": "ERASE_ALL"}},
            {"confirm_exact_rollback": False},
            {"confirm_no_live_target": False},
            {"confirm_retained_ledger": False},
        )
        for mutation in cases:
            with self.subTest(mutation=list(mutation)):
                result = self.rollback(good, **mutation)
                self.assertTrue(result["status"].startswith("HOLD_"), result)
                self.assertEqual(self.state(), (1, 1, 1, 0))
        self.protected()

    def test_row_mutation_and_import_ledger_tampering_block_rollback(self):
        self.fx.conn.execute(
            "UPDATE memory_records SET status='ACTIVE'"
        )
        self.fx.conn.commit()
        self.assertEqual(
            self.rollback()["status"], "HOLD_ORIGINAL_ROW_OR_LEDGER_DRIFT"
        )
        self.assertEqual(self.state(), (1, 1, 1, 0))
        self.fx.conn.execute(
            "UPDATE memory_records SET status=?", (y.STATUS,)
        )
        self.fx.conn.execute(
            "UPDATE galaxy_stage9y_batches SET receipt_hmac_sha256=?", ("0" * 64,)
        )
        self.fx.conn.commit()
        self.assertEqual(
            self.rollback()["status"],
            "HOLD_ORIGINAL_IMPORT_SIGNATURE_OR_RECEIPT_INVALID",
        )
        self.assertEqual(self.state(), (1, 1, 1, 0))
        self.protected()

    def test_unknown_graph_dependencies_and_triggers_hold_before_delete(self):
        self.fx.conn.execute(
            "CREATE TABLE memory_relations (source_record_id TEXT, target_record_id TEXT)"
        )
        self.fx.conn.commit()
        self.assertEqual(
            self.rollback()["status"], "HOLD_UNKNOWN_DEPENDENCIES_OR_LEDGER_SCHEMA"
        )
        self.fx.conn.execute("DROP TABLE memory_relations")
        self.fx.conn.execute(
            "CREATE TRIGGER orphan_guard BEFORE DELETE ON memory_records "
            "BEGIN SELECT RAISE(ABORT,'do-not-delete'); END"
        )
        self.fx.conn.commit()
        self.assertEqual(
            self.rollback()["status"], "HOLD_UNKNOWN_DEPENDENCIES_OR_LEDGER_SCHEMA"
        )
        self.assertEqual(self.state(), (1, 1, 1, 0))
        self.protected()

    def test_marker_revocation_and_canary_drift_hold(self):
        self.fx.conn.execute(
            "UPDATE galaxy_stage9v_staging_identity SET status='REVOKED'"
        )
        self.fx.conn.commit()
        self.assertEqual(self.rollback()["status"], "HOLD_MARKER_OR_CANARY_CHANGED")
        self.fx.conn.execute(
            "UPDATE galaxy_stage9v_staging_identity SET status='ACTIVE'"
        )
        self.fx.conn.execute(
            "UPDATE galaxy_stage9v_canaries SET nonce_sha256=?", ("0" * 64,)
        )
        self.fx.conn.commit()
        self.assertEqual(self.rollback()["status"], "HOLD_MARKER_OR_CANARY_CHANGED")
        self.assertEqual(self.state(), (1, 1, 1, 0))

    def test_unrelated_fixture_or_attached_db_is_refused(self):
        with tempfile.TemporaryDirectory() as elsewhere:
            self.assertEqual(
                self.rollback(fixture_root=elsewhere)["status"],
                "HOLD_NOT_ISOLATED_NATIVE_SQLITE_FIXTURE",
            )
        self.fx.conn.execute("ATTACH DATABASE ':memory:' AS extra")
        self.assertEqual(
            self.rollback()["status"], "HOLD_NOT_ISOLATED_NATIVE_SQLITE_FIXTURE",
        )
        self.fx.conn.execute("DETACH DATABASE extra")
        self.assertEqual(self.state(), (1, 1, 1, 0))

    def test_failed_final_update_rolls_back_prior_deletes_atomically(self):
        def no_batch_update(action, table, column, db, source):
            if action == sqlite3.SQLITE_UPDATE and table == "galaxy_stage9y_batches":
                return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK
        self.fx.conn.set_authorizer(no_batch_update)
        try:
            result = self.rollback()
        finally:
            self.fx.conn.set_authorizer(None)
        self.assertEqual(result["status"], "HOLD_LOCAL_ROLLBACK_TRANSACTION_OR_ACK_FAILED")
        self.assertEqual(result["writes_performed"],
                         ["LOCAL_FIXTURE_ROLLBACK_OUTCOME_UNVERIFIED"])
        self.assertEqual(self.state(), (1, 1, 1, 0))
        self.protected()

    def test_failed_fresh_reopen_holds_and_exact_replay_reconciles(self):
        payload = self.packet()
        with patch.object(z.sqlite3, "connect",
                          side_effect=sqlite3.OperationalError("PRIVATE-REOPEN-FAIL")):
            first = self.rollback(payload)
        self.assertEqual(first["status"], "HOLD_FRESH_LOCAL_ROLLBACK_UNAVAILABLE")
        self.assertEqual(first["writes_performed"],
                         ["LOCAL_FIXTURE_ROLLBACK_OUTCOME_UNVERIFIED"])
        self.assertNotIn("PRIVATE-REOPEN-FAIL", json.dumps(first))
        self.assertEqual(self.state(), (0, 1, 1, 1))
        second = self.rollback(payload)
        self.assertEqual(second["status"], "PASS_LOCAL_ROLLBACK_EXACT_REPLAY_ZERO_WRITE")
        self.assertEqual(second["writes_performed"], [])
        self.protected()

    def test_tampered_rollback_ledger_is_rejected_on_replay(self):
        self.assertEqual(self.rollback()["status"], "PASS_LOCAL_ROLLBACK_RECEIPT_REOPEN")
        self.fx.conn.execute(
            "UPDATE galaxy_stage9z_rollbacks SET receipt_hmac_sha256=?",
            ("0" * 64,),
        )
        self.fx.conn.commit()
        self.assertEqual(self.rollback()["status"], "HOLD_ROLLBACK_REPLAY_DRIFT")
        self.assertEqual(self.state(), (0, 1, 1, 1))
        self.protected()

    def test_changed_roll_back_id_cannot_overwrite_existing_ledger(self):
        self.rollback()
        changed = self.packet(rollback_id="stage9z-fixture-rollback-0002")
        self.assertEqual(
            self.rollback(changed)["status"], "HOLD_ROLLBACK_APPROVAL_COLLISION"
        )
        self.assertEqual(self.state(), (0, 1, 1, 1))
        self.protected()

    def test_source_resurrection_under_new_approval_is_refused(self):
        self.rollback()
        new_import = self.fx.packet(approval_id="stage9y-new-approval-0002")
        attempt = self.fx.run_fixture(new_import)
        self.assertEqual(
            attempt["status"], "HOLD_PREVIOUSLY_ROLLED_BACK_SOURCE", attempt
        )
        self.assertEqual(self.state(), (0, 1, 1, 1))
        self.protected()

    def test_rollback_replay_refuses_resurrected_source_and_recovers_when_removed(self):
        self.rollback()
        old = self.first["receipt"]["items"][0]
        self.fx.conn.execute(
            "INSERT INTO memory_records VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                old["record_id"], "NAOMI", "TEST", "MemoryOS",
                "UNAPPROVED-RESURRECTION",
                "galaxy-archive-v1:" + old["source_key_sha256"],
                y.STATUS, "1", "now", "now", None, "{}",
            ),
        )
        self.fx.conn.commit()
        self.assertEqual(self.rollback()["status"], "HOLD_ROLLBACK_REPLAY_DRIFT")
        self.fx.conn.execute("DELETE FROM memory_records WHERE record_id=?",
                             (old["record_id"],))
        self.fx.conn.commit()
        self.assertEqual(
            self.rollback()["status"], "PASS_LOCAL_ROLLBACK_EXACT_REPLAY_ZERO_WRITE"
        )
        self.protected()


if __name__ == "__main__":
    unittest.main()
