"""Stage 9AC: TRUE predecessor integration on disposable local files ONLY."""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))
import galaxy_stage9ac_full_local_rehearsal as chain
import galaxy_stage9v_staging_turso as v


class CompleteOfflineIntegrationTests(unittest.TestCase):
    def test_end_to_end_native_sqlite_preserves_main_and_original_sentinels(self):
        with patch.object(v, "_connect_live", side_effect=AssertionError(
            "ANY ACTUAL TURSO CONNECTION IS FORBIDDEN IN STAGE 9AC"
        )):
            result = chain.run_local_rehearsal(driver="native")
        self.assertEqual(result["status"], "PASS_FULL_SYNTHETIC_LOCAL_CHAIN", result)
        self.assertEqual(result["step_statuses"], chain.EXPECTED)
        self.assertEqual(result["fully_reconciled_synthetic_rows"], 2)
        self.assertEqual(result["preserved_import_item_receipts"], 2)
        self.assertEqual(result["preserved_signed_rollback_receipts"], 1)
        self.assertTrue(result["main_and_original_sentinel_byte_identical"])
        self.assertTrue(result["same_approval_import_and_rollback_replays_zero_write"])
        self.assertTrue(result["new_approval_rolled_back_source_blocked"])
        self.assertTrue(result["fresh_local_connection_readbacks"])
        self.assertFalse(result["actual_turso_connected"])
        self.assertFalse(result["actual_sovmem_main_connected"])
        self.assertFalse(result["original_gaiaos_production_connected"])
        self.assertFalse(result["owner_authenticated"])
        self.assertFalse(result["provider_database_separation_verified"])
        self.assertFalse(result["bigbang_activated"])
        self.assertFalse(result["e_lanes_modified"])
        self.assertFalse(result["gravity_modified"])
        self.assertGreaterEqual(result["local_connector_open_count"], 10)
        raw = json.dumps(result)
        for needle in (
            chain.TOKEN, chain.STAGE, chain.MAIN,
            "STAGE9AC-SYNTHETIC-ARCHIVED-MEMORY",
            "synthetic-event-001", "source_locator",
            "stage9ac-local-import-test-key",
        ):
            self.assertNotIn(needle, raw)

    def test_actual_libsql_driver_local_file_runs_same_complete_chain(self):
        try:
            import libsql
        except ImportError:
            self.skipTest("CI explicitly installs libsql for local-only driver check")
        with patch.object(v, "_connect_live", side_effect=AssertionError(
            "REMOTE PATH MUST NEVER OPEN"
        )):
            result = chain.run_local_rehearsal(driver="libsql")
        self.assertEqual(result["status"], "PASS_FULL_SYNTHETIC_LOCAL_CHAIN", result)
        self.assertEqual(result["step_statuses"], chain.EXPECTED)
        self.assertFalse(result["actual_turso_connected"])
        self.assertFalse(result["actual_sovmem_staging_connected"])
        self.assertFalse(result["actual_sovmem_main_connected"])

    def test_cli_requires_explicit_flag_and_returns_single_redacted_receipt(self):
        output = io.StringIO()
        with patch.object(v, "_connect_live", side_effect=AssertionError(
            "NO NETWORK"
        )), contextlib.redirect_stdout(output):
            result = chain.main([])
        self.assertEqual(result, 2)
        self.assertEqual(
            json.loads(output.getvalue())["status"],
            "HOLD_EXPLICIT_LOCAL_FIXTURE_FLAG_REQUIRED",
        )
        output = io.StringIO()
        with patch.object(v, "_connect_live", side_effect=AssertionError(
            "NO NETWORK"
        )), contextlib.redirect_stdout(output):
            result = chain.main(["--local-fixture-only", "--driver", "native"])
        self.assertEqual(result, 0)
        self.assertEqual(
            json.loads(output.getvalue())["status"],
            "PASS_FULL_SYNTHETIC_LOCAL_CHAIN",
        )
        self.assertNotIn(chain.TOKEN, output.getvalue())
        self.assertNotIn("STAGE9AC-SYNTHETIC-ARCHIVED", output.getvalue())

    def test_remote_claim_from_local_canary_is_rejected(self):
        with patch.object(
            chain.x, "execute_owner_local_canary",
            return_value={
                "status": "PASS_REMOTE_STAGING_CANARY_REOPEN",
                "stage9v_canary_status": "PASS_STAGING_CANARY_REOPEN_READBACK",
                "staging_turso_reopen_observed": True,
                "staging_canary_written": True,
            },
        ), patch.object(v, "_connect_live", side_effect=AssertionError):
            result = chain.run_local_rehearsal()
        self.assertEqual(result["status"], "HOLD_LOCAL_CANARY", result)
        self.assertEqual(
            result["step_statuses"]["canary"], "PASS_REMOTE_STAGING_CANARY_REOPEN"
        )
        self.assertFalse(result["actual_turso_connected"])

    def test_false_remote_preimport_claim_from_local_connector_is_rejected(self):
        with patch.object(
            chain.aa, "check_preimport_staging",
            return_value={
                "status": "PASS_STAGING_READ_ONLY_PREIMPORT",
                "staging_turso_remotely_observed": True,
                "preimport_tables_empty_verified": True,
            },
        ), patch.object(v, "_connect_live", side_effect=AssertionError):
            result = chain.run_local_rehearsal()
        self.assertEqual(result["status"], "HOLD_LOCAL_PREIMPORT", result)
        self.assertFalse(result["actual_turso_connected"])

    def test_signed_rollback_failure_fails_complete_rehearsal_closed(self):
        with patch.object(
            chain.z, "rollback_local_import",
            return_value={"status": "HOLD_ROLLBACK_LEDGER_DRIFT"},
        ), patch.object(v, "_connect_live", side_effect=AssertionError):
            result = chain.run_local_rehearsal()
        self.assertEqual(result["status"], "HOLD_LOCAL_ROLLBACK", result)
        self.assertEqual(
            result["step_statuses"]["rollback"], "HOLD_ROLLBACK_LEDGER_DRIFT"
        )
        self.assertFalse(result["actual_turso_connected"])

    def test_invalid_driver_and_errors_never_expose_private_exception_strings(self):
        self.assertEqual(
            chain.run_local_rehearsal(driver="remote")["status"],
            "HOLD_UNKNOWN_LOCAL_DRIVER",
        )
        with patch.object(chain.prep, "prepare",
                          side_effect=OSError("PRIVATE-LOCAL-PATH-DO-NOT-ECHO")):
            out = chain.run_local_rehearsal()
        self.assertEqual(out["status"], "HOLD_LOCAL_REHEARSAL_EXCEPTION")
        self.assertEqual(out["exception_type"], "OSError")
        self.assertNotIn("PRIVATE-LOCAL-PATH", json.dumps(out))


if __name__ == "__main__":
    unittest.main()
