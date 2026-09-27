"""Stage 9AH: signed FIRST staging rollback on disposable LOCAL native/libSQL.

The exact original Stage 9AG signed two-row import is the setup, not a
handwritten mock. Both unrelated synthetic MAIN and original GaiaOS disk
sentinels must remain byte-identical across every authorized/failed rollback.
No real Turso, model access, Render change or production authorization.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
import sys
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))
sys.path.insert(0, str(ROOT / "tests"))
import galaxy_stage9ah_signed_staging_rollback as ah
import galaxy_stage9ag_staging_historical_import as ag
import galaxy_stage9v_staging_turso as v
import galaxy_stage9z_local_rollback as z
import galaxy_stage9y_canonical_staging as y
from test_galaxy_stage9ag_staging_historical_import import (
    FirstSignedStagingTests, LocalOnly, KEY as IMPORT_KEY,
)

ROLLBACK_KEY = b"STAGE9AH-SYNTHETIC-DISTINCT-ROLLBACK-KEY-NOT-OWNER-001"
ROLLBACK_ID = "STAGE9AH-SYNTHETIC-ROLLBACK-001"


class FirstStagingRollbackTests(unittest.TestCase):
    def setUp(self):
        fx = FirstSignedStagingTests(
            "test_first_batch_atomic_exact_two_hold_rows_and_signed_receipts"
        )
        fx.setUp()
        self.addCleanup(fx.doCleanups)
        self.fx = fx
        first = fx.run_import(apply=True)
        self.assertEqual(
            first["status"], "PASS_LOCAL_HELD_STAGING_IMPORT_REOPEN_FIXTURE",
            first,
        )
        self.assertEqual(fx.counts(), (2, 1, 2, 0))
        with sqlite3.connect(fx.stage) as db:
            row = db.execute(
                "SELECT receipt_json FROM galaxy_stage9y_batches"
            ).fetchone()
            self.receipt = json.loads(row[0])
        self.expected = ah.expected_rollback_approval(
            config=fx.config, pin=fx.pin,
            original_approval=fx.approval, original_receipt=self.receipt,
            pinned_import_receipt_sha256=self.receipt["receipt_sha256"],
            rollback_id=ROLLBACK_ID,
        )
        self.assertIsNotNone(self.expected)
        self.signature = hmac.new(
            ROLLBACK_KEY, y._bytes(self.expected), hashlib.sha256,
        ).hexdigest()
        self.connector = LocalOnly(fx.stage)
        self.args = {
            "config": fx.config, "pin": fx.pin,
            "original_approval": fx.approval,
            "original_signature": fx.signature,
            "original_key": IMPORT_KEY,
            "original_receipt": self.receipt,
            "pinned_import_receipt_sha256": self.receipt["receipt_sha256"],
            "rollback_approval": self.expected,
            "rollback_signature": self.signature,
            "rollback_key": ROLLBACK_KEY,
            "confirm_exact_original_row_review": True,
            "confirm_independent_import_receipt_pin": True,
            "confirm_provider_identity_reviewed": True,
            "confirm_staging_only_credential_reviewed": True,
            "confirm_irreversible_staging_row_removal": True,
            "connector": self.connector,
        }

    def call(self, **changes):
        with patch.object(
            v, "_connect_live",
            side_effect=AssertionError("REAL TURSO CONNECTION FORBIDDEN"),
        ):
            return ah.rollback_first_staging_batch(**{**self.args, **changes})

    def protected(self):
        self.fx.protected()
        self.assertEqual(self.fx.main.read_bytes(), self.fx.main_bytes)
        self.assertEqual(
            self.fx.original.read_bytes(), self.fx.original_bytes,
        )

    def test_default_dry_run_verifies_both_signatures_without_any_connection(self):
        before = self.fx.stage.read_bytes()
        result = self.call()
        self.assertEqual(
            result["status"], "PASS_SIGNED_ROLLBACK_DRY_RUN_ZERO_CONNECTION",
        )
        self.assertEqual(result["exact_held_rows_in_signed_manifest"], 2)
        self.assertEqual(self.connector.calls, [])
        self.assertEqual(result["writes_performed"], [])
        self.assertFalse(result["remote_staging_reopen_observed"])
        self.assertFalse(result["real_owner_identity_verified"])
        self.assertFalse(result["bigbang_activated"])
        self.assertEqual(self.fx.stage.read_bytes(), before)
        self.assertEqual(self.fx.counts(), (2, 1, 2, 0))
        self.protected()

    def test_exact_signed_first_batch_rollback_retains_every_receipt(self):
        first = self.call(apply=True)
        self.assertEqual(
            first["status"],
            "PASS_LOCAL_SIGNED_ROLLBACK_FRESH_REOPEN_FIXTURE", first,
        )
        self.assertEqual(self.fx.counts(), (0, 1, 2, 1))
        self.assertEqual(first["exact_held_rows_removed"], 2)
        self.assertEqual(first["original_item_receipts_retained"], 2)
        self.assertEqual(first["signed_rollback_receipts_retained"], 1)
        self.assertTrue(first["independent_fresh_staging_readback"])
        self.assertTrue(first["original_import_history_preserved"])
        self.assertFalse(first["remote_staging_reopen_observed"])
        self.assertFalse(first["provider_database_separation_independently_verified"])
        self.assertFalse(first["real_owner_identity_verified"])
        self.assertFalse(first["bigbang_activated"])
        with sqlite3.connect(self.fx.stage) as db:
            self.assertEqual(
                db.execute(
                    "SELECT status FROM galaxy_stage9y_batches"
                ).fetchone(), (ah.ROLLED_BACK,),
            )
            preserved = json.loads(db.execute(
                "SELECT receipt_json FROM galaxy_stage9y_batches"
            ).fetchone()[0])
            self.assertEqual(preserved, self.receipt)
            self.assertEqual(
                db.execute(
                    "SELECT COUNT(*) FROM galaxy_stage9y_items "
                    "WHERE result=?", (ag.RESULT,),
                ).fetchone()[0], 2,
            )
        raw = json.dumps(first)
        for private in (
            self.fx.config["staging_token"],
            self.fx.config["staging_url"],
            self.fx.config["production_url"],
            "STAGE9AC-SYNTHETIC-ARCHIVED-MEMORY",
        ):
            self.assertNotIn(private, raw)
        self.protected()

    def test_exact_replay_is_read_only_and_byte_identical(self):
        self.call(apply=True)
        before = self.fx.stage.read_bytes()
        old_connect_count = len(self.connector.calls)
        replay = self.call(apply=True)
        self.assertEqual(
            replay["status"], "PASS_LOCAL_SIGNED_ROLLBACK_REPLAY_ZERO_WRITE",
            replay,
        )
        self.assertEqual(replay["writes_performed"], [])
        self.assertTrue(replay["zero_write_exact_replay"])
        self.assertGreater(len(self.connector.calls), old_connect_count)
        self.assertEqual(self.fx.stage.read_bytes(), before)
        self.assertEqual(self.fx.counts(), (0, 1, 2, 1))
        self.protected()

    def test_actual_public_libsql_driver_local_file_and_exact_replay(self):
        try:
            import libsql
        except ImportError:
            self.skipTest("CI explicitly installs libsql for local file")
        connector = LocalOnly(self.fx.stage, driver="libsql")
        first = self.call(apply=True, connector=connector)
        self.assertEqual(
            first["status"], "PASS_LOCAL_SIGNED_ROLLBACK_FRESH_REOPEN_FIXTURE",
            first,
        )
        self.assertGreaterEqual(len(connector.calls), 3)
        self.assertFalse(first["remote_staging_reopen_observed"])
        second = self.call(apply=True, connector=connector)
        self.assertEqual(
            second["status"], "PASS_LOCAL_SIGNED_ROLLBACK_REPLAY_ZERO_WRITE",
            second,
        )
        self.protected()

    def test_independent_remote_rollback_signature_cannot_be_9z_local_signature(self):
        local_manifest = z.expected_rollback_manifest(
            original_manifest=self.fx.approval,
            original_receipt=self.receipt,
            rollback_id=ROLLBACK_ID,
        )
        fake_signature = hmac.new(
            ROLLBACK_KEY, y._bytes(local_manifest),
            hashlib.sha256,
        ).hexdigest()
        out = self.call(
            apply=True, rollback_approval=local_manifest,
            rollback_signature=fake_signature,
        )
        self.assertEqual(
            out["status"], "HOLD_SEPARATELY_SIGNED_EXACT_ROLLBACK_REQUIRED",
        )
        self.assertEqual(self.connector.calls, [])
        self.assertEqual(self.fx.counts(), (2, 1, 2, 0))
        self.protected()

    def test_import_key_cannot_be_rollback_key(self):
        manifest = self.expected
        signature = hmac.new(
            IMPORT_KEY, y._bytes(manifest), hashlib.sha256,
        ).hexdigest()
        out = self.call(
            apply=True, rollback_key=IMPORT_KEY, rollback_signature=signature,
        )
        self.assertEqual(out["status"], "HOLD_INDEPENDENT_ROLLBACK_KEY_REQUIRED")
        self.assertEqual(self.connector.calls, [])
        self.protected()

    def test_all_five_separate_rollback_flags_must_be_literal_true(self):
        flags = (
            "confirm_exact_original_row_review",
            "confirm_independent_import_receipt_pin",
            "confirm_provider_identity_reviewed",
            "confirm_staging_only_credential_reviewed",
            "confirm_irreversible_staging_row_removal",
        )
        for flag in flags:
            for false in (False, 1, "true"):
                with self.subTest(flag=flag, value=false):
                    result = self.call(apply=True, **{flag: false})
                    self.assertEqual(
                        result["status"],
                        "HOLD_FIVE_SEPARATE_ROLLBACK_CONFIRMATIONS_REQUIRED",
                    )
        self.assertEqual(self.connector.calls, [])
        self.assertEqual(self.fx.counts(), (2, 1, 2, 0))
        self.protected()

    def test_invalid_original_signature_changed_pin_receipt_and_url_fail_preconnect(self):
        tampered = dict(self.receipt)
        tampered["canary_sha256"] = "0" * 64
        mutations = (
            {"original_signature": "0" * 64},
            {"original_key": b"wrong-independent-test-key" * 3},
            {"original_receipt": tampered},
            {"pinned_import_receipt_sha256": "0" * 64},
            {"rollback_signature": "0" * 64},
            {"rollback_key": b"wrong-distinct-rollback-key" * 3},
            {"config": {**self.fx.config, "staging_token": ""}},
            {"config": {
                **self.fx.config, "staging_url": self.fx.config["production_url"],
            }},
            {"pin": {**self.fx.pin, "canary_sha256": "0" * 64}},
        )
        for mutation in mutations:
            with self.subTest(mutation=list(mutation)):
                self.assertTrue(
                    self.call(apply=True, **mutation)["status"].startswith("HOLD_")
                )
        self.assertEqual(self.connector.calls, [])
        self.assertEqual(self.fx.counts(), (2, 1, 2, 0))
        self.protected()

    def test_unknown_trigger_or_extra_table_holds_before_delete(self):
        with sqlite3.connect(self.fx.stage) as db:
            db.execute(
                "CREATE VIEW fake_reference AS SELECT 1 AS value"
            )
        out = self.call(apply=True)
        self.assertEqual(
            out["status"], "HOLD_STAGING_SCHEMA_MARKER_OR_CANARY_CHANGED",
            out,
        )
        self.assertEqual(self.fx.counts(), (2, 1, 2, 0))
        with sqlite3.connect(self.fx.stage) as db:
            db.execute("DROP VIEW fake_reference")
        self.protected()

    def test_mutated_original_row_never_deleted_or_trusted(self):
        with sqlite3.connect(self.fx.stage) as db:
            db.execute(
                "UPDATE memory_records SET status='ACTIVE'"
            )
        result = self.call(apply=True)
        self.assertEqual(
            result["status"], "HOLD_ORIGINAL_HELD_ROWS_OR_LEDGER_CHANGED",
            result,
        )
        self.assertEqual(self.fx.counts(), (2, 1, 2, 0))
        self.protected()

    def test_canary_revocation_holds_no_deletes(self):
        with sqlite3.connect(self.fx.stage) as db:
            db.execute(
                "UPDATE galaxy_stage9v_canaries SET nonce_sha256=?",
                ("0" * 64,),
            )
        result = self.call(apply=True)
        self.assertEqual(
            result["status"], "HOLD_STAGING_SCHEMA_MARKER_OR_CANARY_CHANGED",
            result,
        )
        self.assertEqual(self.fx.counts(), (2, 1, 2, 0))
        # Restore the deliberately corrupted synthetic canary so the common
        # preservation assertion tests the rollback, not the attack fixture.
        with sqlite3.connect(self.fx.stage) as db:
            db.execute(
                "UPDATE galaxy_stage9v_canaries SET nonce_sha256=?",
                (self.fx.canary["nonce_sha256"],),
            )
        self.protected()

    def test_failed_batch_status_update_rolls_back_any_prior_row_deletes(self):
        factory = self.connector

        class FailUpdate:
            def __call__(self, url, token):
                raw = factory(url, token)

                class Proxy:
                    def execute(self, sql, params=()):
                        if sql.startswith("UPDATE galaxy_stage9y_batches"):
                            raise sqlite3.OperationalError("PRIVATE-ROLLBACK-FAIL")
                        return raw.execute(sql, params)
                    def rollback(self):
                        raw.rollback()
                    def commit(self):
                        raw.commit()
                    def close(self):
                        raw.close()
                return Proxy()

        result = self.call(apply=True, connector=FailUpdate())
        self.assertEqual(
            result["status"], "HOLD_STAGING_ROLLBACK_TRANSACTION_OR_ACK_UNVERIFIED",
            result,
        )
        self.assertTrue(result["staging_rollback_outcome_uncertain"])
        self.assertNotIn("PRIVATE-ROLLBACK-FAIL", json.dumps(result))
        self.assertEqual(self.fx.counts(), (2, 1, 2, 0))
        self.protected()

    def test_lost_post_commit_fresh_readback_holds_then_exact_replay_recovers(self):
        factory = self.connector

        class FailFresh:
            n = 0
            def __call__(self, url, token):
                self.n += 1
                if self.n == 3:
                    raise OSError("PRIVATE-REOPEN-FAILED")
                return factory(url, token)

        first = self.call(apply=True, connector=FailFresh())
        self.assertEqual(
            first["status"], "HOLD_FRESH_STAGING_ROLLBACK_REOPEN_UNAVAILABLE",
            first,
        )
        self.assertTrue(first["staging_rollback_outcome_uncertain"])
        self.assertEqual(self.fx.counts(), (0, 1, 2, 1))
        old = self.fx.stage.read_bytes()
        second = self.call(apply=True)
        self.assertEqual(
            second["status"], "PASS_LOCAL_SIGNED_ROLLBACK_REPLAY_ZERO_WRITE",
            second,
        )
        self.assertEqual(self.fx.stage.read_bytes(), old)
        self.assertEqual(second["writes_performed"], [])
        self.protected()

    def test_after_rollback_new_and_old_9ag_imports_both_fail_closed(self):
        first = self.call(apply=True)
        self.assertEqual(
            first["status"], "PASS_LOCAL_SIGNED_ROLLBACK_FRESH_REOPEN_FIXTURE",
        )
        old_import = self.fx.run_import(apply=True)
        self.assertEqual(
            old_import["status"], "HOLD_EXISTING_APPROVAL_CONFLICT_OR_ROLLED_BACK",
        )
        second = ag.expected_approval(
            config=self.fx.config, pin=self.fx.pin,
            approval_id="STAGE9AH-UNAUTHORIZED-SECOND-IMPORT",
            export_sha256=v._sha(self.fx.export),
            source_sha256=v._sha(self.fx.source),
            items=self.fx.items,
        )
        signed = hmac.new(
            IMPORT_KEY, y._bytes(second), hashlib.sha256,
        ).hexdigest()
        new_import = self.fx.run_import(
            apply=True, approval=second, signature_hex=signed,
        )
        self.assertEqual(
            new_import["status"], "HOLD_ONLY_FIRST_EMPTY_STAGING_BATCH_SUPPORTED",
        )
        self.assertEqual(self.fx.counts(), (0, 1, 2, 1))
        self.protected()

    def test_different_signed_rollback_id_fails_after_first_receipt(self):
        self.call(apply=True)
        other = ah.expected_rollback_approval(
            config=self.fx.config, pin=self.fx.pin,
            original_approval=self.fx.approval,
            original_receipt=self.receipt,
            pinned_import_receipt_sha256=self.receipt["receipt_sha256"],
            rollback_id="STAGE9AH-ANOTHER-SIGNED-ROLLBACK",
        )
        sig = hmac.new(
            ROLLBACK_KEY, y._bytes(other), hashlib.sha256,
        ).hexdigest()
        result = self.call(
            apply=True, rollback_approval=other,
            rollback_signature=sig,
        )
        self.assertEqual(
            result["status"], "HOLD_DIFFERENT_ROLLBACK_ALREADY_RECORDED",
        )
        self.assertEqual(self.fx.counts(), (0, 1, 2, 1))
        self.protected()

    def test_tampered_signed_rollback_ledger_fails_exact_replay(self):
        self.call(apply=True)
        with sqlite3.connect(self.fx.stage) as db:
            db.execute(
                "UPDATE galaxy_stage9z_rollbacks SET receipt_hmac_sha256=?",
                ("0" * 64,),
            )
        out = self.call(apply=True)
        self.assertEqual(out["status"], "HOLD_SIGNED_ROLLBACK_REPLAY_DRIFT")
        self.assertEqual(out["writes_performed"], [])
        self.assertEqual(self.fx.counts(), (0, 1, 2, 1))
        self.protected()

    def test_resurrected_same_source_after_rollback_fails_exact_replay(self):
        self.call(apply=True)
        with sqlite3.connect(self.fx.stage) as db:
            db.execute(
                "INSERT INTO memory_records VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    "MEM-STAGE9AH-UNAUTHORIZED-RESURRECTION", "NAOMI",
                    "TEST", "MemoryOS", "UNAUTHORIZED-SOURCE-RESURRECTION",
                    "galaxy-archive-v1:" +
                    self.receipt["items"][0]["source_key_sha256"],
                    "ACTIVE", "1", "2026-01-01", "2026-01-01", None, "{}",
                ),
            )
        result = self.call(apply=True)
        self.assertEqual(result["status"], "HOLD_SIGNED_ROLLBACK_REPLAY_DRIFT")
        self.assertEqual(result["writes_performed"], [])
        self.assertEqual(self.fx.counts(), (1, 1, 2, 1))
        self.protected()


if __name__ == "__main__":
    unittest.main()
