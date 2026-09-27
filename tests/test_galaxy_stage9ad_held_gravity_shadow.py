"""Stage 9AD: signed canonical held-history and real Stage 9U volatility boundary."""
from __future__ import annotations

import copy
import hashlib
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
import galaxy_stage9ad_held_gravity_shadow as ad
import galaxy_shadow_backfill_stage9u as u
from test_galaxy_stage9z_local_rollback import SignedLocalRollbackTests


class HeldArchiveShadowIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.fx = SignedLocalRollbackTests(
            "test_signed_exact_rollback_removes_only_new_rows_and_retains_receipts"
        )
        self.fx.setUp()
        self.addCleanup(self.fx.doCleanups)

    def invoke(self, **changes):
        params = {
            "fixture_connection": self.fx.fx.conn,
            "fixture_root": self.fx.fx.root,
            "config": self.fx.original["config"],
            "original_manifest": self.fx.original["approval"],
            "original_signature": self.fx.original["signature_hex"],
            "original_key": self.fx.original["approval_key"],
            "original_receipt": self.fx.first["receipt"],
            "confirm_synthetic_local_only": True,
        }
        params.update(changes)
        return ad.rehearse_held_archive_gravity_shadow(**params)

    def test_full_signed_held_archive_preserved_with_actual_u_gravity(self):
        staging = self.fx.fx.stage_file
        before = staging.read_bytes()
        total = self.fx.fx.conn.total_changes
        result = self.invoke()
        self.assertEqual(
            result["status"],
            "PASS_LOCAL_HELD_ARCHIVE_GRAVITY_SHADOW_REHEARSAL",
            result,
        )
        self.assertEqual(result["held_historical_records_preserved"], 1)
        self.assertEqual(result["active_synthetic_records_exercised"], 3)
        self.assertEqual(result["synthetic_shadow_scores_inserted"], 1)
        self.assertEqual(result["synthetic_shadow_scores_updated"], 1)
        self.assertEqual(result["synthetic_current_scores_skipped"], 1)
        self.assertTrue(result["owner_importance_absent_preserved_as_unset"])
        self.assertTrue(result["independent_shadow_replay_zero_write"])
        self.assertTrue(result["independent_shadow_rollback_zero_write_replay"])
        self.assertFalse(result["staged_history_activated"])
        self.assertEqual(result["held_historical_gravity_rows_written"], 0)
        self.assertTrue(result["source_original_and_receipts_retained"])
        self.assertFalse(result["real_sovmem_staging_accessed"])
        self.assertFalse(result["real_sovmem_main_accessed"])
        self.assertFalse(result["bigbang_activated"])
        self.assertFalse(result["live_owner_identity_verified"])
        self.assertFalse(result["preview_model_calibration_verified"])
        self.assertEqual(staging.read_bytes(), before)
        self.assertEqual(self.fx.fx.conn.total_changes, total)
        self.assertNotIn("memory_gravity", {
            row[0] for row in self.fx.fx.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        })
        self.assertEqual(
            self.fx.fx.conn.execute("SELECT status FROM memory_records").fetchone(),
            ("STAGED_HISTORICAL_HOLD",),
        )
        self.assertNotIn("PRIVATE-MEMORY-LINE", json.dumps(result))
        self.assertNotIn("PRIVATE-DOCUMENT-ID", json.dumps(result))
        self.fx.protected()

    def test_original_import_rollback_still_works_after_shadow_rehearsal(self):
        self.assertEqual(
            self.invoke()["status"],
            "PASS_LOCAL_HELD_ARCHIVE_GRAVITY_SHADOW_REHEARSAL",
        )
        rolled = self.fx.rollback()
        self.assertEqual(rolled["status"], "PASS_LOCAL_ROLLBACK_RECEIPT_REOPEN")
        self.assertEqual(
            self.invoke()["status"], "HOLD_ORIGINAL_STAGED_BATCH_MISSING"
        )
        self.assertEqual(self.fx.state(), (0, 1, 1, 1))
        self.fx.protected()

    def test_unsigned_or_bad_manifest_refused_before_volatile_backup(self):
        cases = [
            {"original_signature": "0" * 64},
            {"original_key": b"wrong-independent-fixture-key" * 2},
            {"original_manifest": {
                **self.fx.original["approval"],
                "staging_url_sha256": "0" * 64,
            }},
            {"original_receipt": {
                **self.fx.first["receipt"], "source_sha256": "0" * 64,
            }},
            {"confirm_synthetic_local_only": False},
        ]
        before = self.fx.fx.stage_file.read_bytes()
        for change in cases:
            with self.subTest(change=list(change)):
                report = self.invoke(**change)
                self.assertTrue(report["status"].startswith("HOLD_"), report)
                self.assertEqual(self.fx.fx.stage_file.read_bytes(), before)
                self.assertFalse(report["staged_history_activated"])
        self.fx.protected()

    def test_changed_canary_status_and_unknown_graph_table_fail_closed(self):
        self.fx.fx.conn.execute(
            "UPDATE galaxy_stage9v_canaries SET nonce_sha256=?", ("0" * 64,)
        )
        self.fx.fx.conn.commit()
        self.assertEqual(
            self.invoke()["status"], "HOLD_STAGING_IDENTITY_OR_CANARY_CHANGED"
        )
        self.fx.fx.conn.execute(
            "UPDATE galaxy_stage9v_canaries SET nonce_sha256=?",
            (self.fx.fx.canary["nonce_sha256"],),
        )
        self.fx.fx.conn.execute(
            "CREATE TABLE memory_relations (source_record_id TEXT)"
        )
        self.fx.fx.conn.commit()
        self.assertEqual(
            self.invoke()["status"], "HOLD_UNKNOWN_STAGING_DEPENDENCIES"
        )
        self.assertEqual(
            self.fx.fx.conn.execute(
                "SELECT count(*) FROM memory_records"
            ).fetchone()[0], 1,
        )

    def test_staged_row_mutation_denies_shadow_instead_of_upgrading_it(self):
        self.fx.fx.conn.execute(
            "UPDATE memory_records SET status='ACTIVE'"
        )
        self.fx.fx.conn.commit()
        report = self.invoke()
        self.assertEqual(report["status"], "HOLD_ORIGINAL_ROW_OR_ITEM_LEDGER_DRIFT")
        self.assertEqual(report["held_historical_gravity_rows_written"], 0)
        self.assertFalse(report["staged_history_activated"])
        self.assertEqual(
            self.fx.fx.conn.execute("SELECT status FROM memory_records").fetchone(),
            ("ACTIVE",),
        )

    def test_inmemory_or_wrong_fixture_file_refused(self):
        with sqlite3.connect(":memory:") as unrelated:
            self.assertEqual(
                self.invoke(fixture_connection=unrelated)["status"],
                "HOLD_NOT_ISOLATED_LOCAL_STAGING_FIXTURE",
            )
        with tempfile.TemporaryDirectory() as other:
            self.assertEqual(
                self.invoke(fixture_root=Path(other))["status"],
                "HOLD_NOT_ISOLATED_LOCAL_STAGING_FIXTURE",
            )

    def test_u_plan_apply_and_rollback_faults_hold_without_file_mutation(self):
        before = self.fx.fx.stage_file.read_bytes()
        with patch.object(
            u, "apply_shadow_plan", return_value={"status": "HOLD_BACKFILL_FAILED"},
        ):
            self.assertEqual(
                self.invoke()["status"], "HOLD_SHADOW_BACKFILL_NOT_PROVEN"
            )
        with patch.object(
            u, "rollback_shadow_batch",
            return_value={"status": "HOLD_ROLLBACK_SCORE_DRIFT"},
        ):
            self.assertEqual(
                self.invoke()["status"], "HOLD_SHADOW_ROLLBACK_NOT_PROVEN"
            )
        self.assertEqual(self.fx.fx.stage_file.read_bytes(), before)
        self.fx.protected()


if __name__ == "__main__":
    unittest.main()
