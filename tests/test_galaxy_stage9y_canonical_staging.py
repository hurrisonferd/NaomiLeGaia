"""Stage 9Y: native file-backed canonical staging fixture, never real Turso."""
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
import galaxy_archive_preflight as preflight
import galaxy_archive_staging as t
import galaxy_stage9v_staging_turso as v
import galaxy_stage9y_canonical_staging as y
from test_galaxy_archive_staging_stage9t import envelope, record, SECRET, SOURCE

STAGE = "libsql://stage9y-isolated-fixture.turso.io"
PROD = "libsql://stage9y-prod-never-contact.turso.io"
MARKER = "7e75e39e-2a66-4a0b-8dbe-3a4b04e3b74d"
RUN = "STAGE9Y-CANARY-FIXTURE-0001"
NONCE = hashlib.sha256(b"test-only-canary-nonce").hexdigest()
CONFIG = {
    "staging_url": STAGE, "production_url": PROD,
    "expected_staging_id": MARKER,
}


class CanonicalFixtureTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.stage_file = self.root / "isolated-staging.db"
        self.production_file = self.root / "never-touch-production.db"
        self.conn = sqlite3.connect(self.stage_file)
        self.addCleanup(self.conn.close)
        self.conn.executescript("""
            CREATE TABLE galaxy_stage9v_staging_identity (
                schema TEXT, environment TEXT, database_id TEXT,
                authority TEXT, status TEXT
            );
            CREATE TABLE galaxy_stage9v_canaries (
                run_id TEXT PRIMARY KEY, nonce_sha256 TEXT,
                database_id TEXT, created_at TEXT
            );
            CREATE TABLE memory_records (
                record_id TEXT PRIMARY KEY, authority TEXT NOT NULL,
                record_type TEXT NOT NULL, scope TEXT NOT NULL,
                statement TEXT NOT NULL, source TEXT NOT NULL,
                status TEXT NOT NULL, version TEXT NOT NULL,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                supersedes TEXT, notes TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE galaxy_stage9y_batches (
                approval_id TEXT PRIMARY KEY, manifest_sha256 TEXT,
                export_sha256 TEXT, source_sha256 TEXT,
                canary_sha256 TEXT, receipt_json TEXT, receipt_hmac_sha256 TEXT,
                status TEXT, created_at TEXT
            );
            CREATE TABLE galaxy_stage9y_items (
                receipt_id TEXT PRIMARY KEY, approval_id TEXT NOT NULL,
                record_id TEXT NOT NULL, source_key_sha256 TEXT NOT NULL,
                statement_sha256 TEXT NOT NULL, metadata_sha256 TEXT NOT NULL,
                row_sha256 TEXT NOT NULL, result TEXT NOT NULL,
                UNIQUE(approval_id, source_key_sha256)
            );
        """)
        self.conn.execute(
            "INSERT INTO galaxy_stage9v_staging_identity VALUES (?,?,?,?,?)",
            (v.IDENTITY_SCHEMA, "STAGING_ONLY", MARKER, "NAOMI", "ACTIVE"),
        )
        self.canary = {
            "run_id": RUN, "nonce_sha256": NONCE,
            "database_id": MARKER,
            "created_at": "2026-09-27T18:45:00+00:00",
        }
        self.canary_hash = hashlib.sha256(v._bytes(self.canary)).hexdigest()
        self.conn.execute(
            "INSERT INTO galaxy_stage9v_canaries VALUES (?,?,?,?)",
            tuple(self.canary.values()),
        )
        self.conn.commit()
        with sqlite3.connect(self.production_file) as prod:
            prod.execute(
                "CREATE TABLE memory_records (record_id TEXT PRIMARY KEY, statement TEXT)"
            )
            prod.execute(
                "INSERT INTO memory_records VALUES ('PROD-SENTINEL','DO-NOT-TOUCH')"
            )

    def packet(self, records=None, approval_id="stage9y-fixture-approval-0001",
               source=SOURCE):
        data = envelope(records, approval_id=approval_id, source=source)
        verified = t._verified_packet(
            data["export_bytes"], data["pinned_export_sha256"],
            data["source_bytes"], data["pinned_source_sha256"],
        )
        if isinstance(verified, str):
            raise AssertionError(verified)
        _, items = verified
        manifest = y._expected_manifest(
            config=CONFIG, approval={
                "approval_id": approval_id, "canary_run_id": RUN,
                "canary_sha256": self.canary_hash,
            }, export_hash=data["pinned_export_sha256"],
            source_hash=data["pinned_source_sha256"], items=items,
        )
        data["approval"] = manifest
        data["signature_hex"] = hmac.new(
            SECRET, y._bytes(manifest), hashlib.sha256,
        ).hexdigest()
        data.update({
            "config": CONFIG, "fixture_connection": self.conn,
            "fixture_root": self.root,
            "confirm_separate_fixture": True,
            "confirm_owner_source_review": True,
            "confirm_canary_evidence_review": True,
        })
        return data

    def run_fixture(self, data=None, **changes):
        payload = self.packet() if data is None else data
        payload = {**payload, **changes}
        return y.stage_historical_fixture(**payload)

    def row_counts(self):
        return tuple(self.conn.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0] for table in (
            "memory_records", "galaxy_stage9y_batches", "galaxy_stage9y_items"
        ))

    def assert_original_untouched(self):
        with sqlite3.connect(self.production_file) as prod:
            self.assertEqual(
                prod.execute("SELECT * FROM memory_records").fetchall(),
                [("PROD-SENTINEL", "DO-NOT-TOUCH")],
            )
        self.assertEqual(self.conn.execute(
            "SELECT status FROM galaxy_stage9v_staging_identity"
        ).fetchone(), ("ACTIVE",))
        self.assertEqual(self.conn.execute(
            "SELECT * FROM galaxy_stage9v_canaries"
        ).fetchall(), [tuple(self.canary.values())])

    def test_atomic_one_record_import_ledger_and_independent_reopen(self):
        out = self.run_fixture()
        self.assertEqual(out["status"], "PASS_LOCAL_CANONICAL_STAGING_REOPEN_FIXTURE", out)
        self.assertEqual(self.row_counts(), (1, 1, 1))
        self.assertTrue(out["fresh_local_connection_readback"])
        self.assertFalse(out["staging_turso_remotely_observed"])
        self.assertFalse(out["live_owner_authentication_verified"])
        self.assertFalse(out["provider_database_separation_independently_verified"])
        self.assertFalse(out["production_accessed"])
        self.assertFalse(out["e_lanes_modified"])
        self.assertFalse(out["gravity_modified"])
        self.assertFalse(out["bigbang_activated"])
        self.assertEqual(
            out["writes_performed"], ["LOCAL_FIXTURE_HISTORICAL_ROWS_AND_RECEIPTS"]
        )
        self.assertEqual(
            out["receipt"]["items"][0]["status"], "STAGED_HISTORICAL_HOLD"
        )
        with sqlite3.connect(self.stage_file) as fresh:
            record_row = fresh.execute(
                "SELECT authority,scope,statement,status,created_at,notes "
                "FROM memory_records"
            ).fetchone()
        self.assertEqual(record_row[0:4], (
            "NAOMI", "MemoryOS", "PRIVATE-MEMORY-LINE-001", "STAGED_HISTORICAL_HOLD"
        ))
        provenance = json.loads(record_row[5])["galaxy_archive"]
        self.assertIsNone(provenance["original_created_at"])
        self.assertEqual(provenance["source_content_sha256"],
                         hashlib.sha256(SOURCE).hexdigest())
        self.assertNotIn("PRIVATE-MEMORY-LINE-001", json.dumps(out))
        self.assertNotIn("PRIVATE-DOCUMENT-ID-SECRET", json.dumps(out))
        self.assertNotIn("PRIVATE-SOURCE-LOCATION-SECRET", json.dumps(out))
        self.assert_original_untouched()

    def test_exact_replay_no_writes_and_same_signed_receipt(self):
        payload = self.packet()
        first = self.run_fixture(payload)
        prior = self.conn.total_changes
        repeat = self.run_fixture(payload)
        self.assertEqual(repeat["status"], "PASS_LOCAL_EXACT_REPLAY_ZERO_WRITE", repeat)
        self.assertEqual(repeat["receipt"], first["receipt"])
        self.assertTrue(repeat["idempotent_replay"])
        self.assertEqual(repeat["writes_performed"], [])
        self.assertEqual(self.conn.total_changes, prior)
        self.assertEqual(self.row_counts(), (1, 1, 1))
        self.assert_original_untouched()

    def test_two_records_one_failed_insert_rolls_back_entire_batch(self):
        payload = self.packet([record(1), record(2)])
        packet = json.loads(payload["export_bytes"])
        second_id = preflight.preflight_archive_batch(packet)["items"][1]["proposed_record_id"]
        self.conn.execute(
            "CREATE TRIGGER inject_failure BEFORE INSERT ON memory_records "
            f"WHEN NEW.record_id='{second_id}' BEGIN "
            "SELECT RAISE(ABORT,'PRIVATE-FIXTURE-INSERT-ERROR'); END"
        )
        self.conn.commit()
        out = self.run_fixture(payload)
        self.assertEqual(out["status"],
                         "HOLD_LOCAL_STAGING_TRANSACTION_OR_ACK_FAILED", out)
        self.assertEqual(self.row_counts(), (0, 0, 0))
        self.assertNotIn("PRIVATE-FIXTURE-INSERT-ERROR", json.dumps(out))
        self.assert_original_untouched()

    def test_source_collision_holds_before_write(self):
        data = self.packet()
        item = preflight.preflight_archive_batch(
            json.loads(data["export_bytes"])
        )["items"][0]
        self.conn.execute(
            "INSERT INTO memory_records VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                item["proposed_record_id"], "NAOMI", "TEST", "MemoryOS",
                "UNAPPROVED-OTHER-STATEMENT",
                "galaxy-archive-v1:" + item["source_key_sha256"],
                "ACTIVE", "1", "now", "now", None, "{}",
            ),
        )
        self.conn.commit()
        out = self.run_fixture(data)
        self.assertEqual(out["status"],
                         "HOLD_EXISTING_SOURCE_OR_RECORD_ID_COLLISION")
        self.assertEqual(self.row_counts(), (1, 0, 0))
        self.assert_original_untouched()

    def test_same_approval_different_signed_export_holds(self):
        first = self.packet()
        self.assertEqual(self.run_fixture(first)["status"],
                         "PASS_LOCAL_CANONICAL_STAGING_REOPEN_FIXTURE")
        other_source = b"New dossier\nPRIVATE-MEMORY-LINE-002\n"
        altered = self.packet(
            [record(2)], source=other_source,
        )
        out = self.run_fixture(altered)
        self.assertEqual(out["status"],
                         "HOLD_APPROVAL_ID_REUSE_OR_REPLAY_DRIFT")
        self.assertEqual(self.row_counts(), (1, 1, 1))
        self.assert_original_untouched()

    def test_drift_in_row_and_ledger_refuses_exact_replay(self):
        data = self.packet()
        self.run_fixture(data)
        self.conn.execute(
            "UPDATE memory_records SET statement='ALTERED-FIXTURE-CONTENT'"
        )
        self.conn.commit()
        out = self.run_fixture(data)
        self.assertEqual(out["status"],
                         "HOLD_SIGNED_RECEIPT_OR_STAGING_REPLAY_DRIFT")
        self.assertEqual(self.row_counts(), (1, 1, 1))
        self.assert_original_untouched()

    def test_revoke_canary_change_uuid_and_wrong_schema_fail_before_write(self):
        data = self.packet()
        self.conn.execute("UPDATE galaxy_stage9v_staging_identity SET status='REVOKED'")
        self.conn.commit()
        self.assertEqual(
            self.run_fixture(data)["status"],
            "HOLD_CANONICAL_SCHEMA_IDENTITY_OR_CANARY_MISMATCH",
        )
        self.conn.execute("UPDATE galaxy_stage9v_staging_identity SET status='ACTIVE'")
        self.conn.execute(
            "UPDATE galaxy_stage9v_canaries SET nonce_sha256=?", ("0" * 64,)
        )
        self.conn.commit()
        self.assertEqual(
            self.run_fixture(data)["status"],
            "HOLD_CANONICAL_SCHEMA_IDENTITY_OR_CANARY_MISMATCH",
        )
        self.conn.execute(
            "UPDATE galaxy_stage9v_canaries SET nonce_sha256=?", (NONCE,)
        )
        self.conn.execute("DROP TABLE galaxy_stage9y_items")
        self.conn.commit()
        self.assertEqual(
            self.run_fixture(data)["status"],
            "HOLD_CANONICAL_SCHEMA_IDENTITY_OR_CANARY_MISMATCH",
        )
        self.assertEqual(self.conn.execute(
            "SELECT COUNT(*) FROM memory_records"
        ).fetchone()[0], 0)
        self.assert_original_untouched()

    def test_unsigned_actions_and_invalid_pins_hold_before_write(self):
        original = self.packet()
        for change in (
            {"signature_hex": "0" * 64},
            {"approval_key": b"X" * 40},
            {"approval": {**original["approval"], "target": "PRODUCTION"}},
            {"config": {**CONFIG, "production_url": STAGE}},
            {"config": {**CONFIG, "expected_staging_id": "wrong"}},
            {"pinned_source_sha256": "0" * 64},
            {"pinned_export_sha256": "0" * 64},
        ):
            with self.subTest(change=list(change)):
                out = self.run_fixture(original, **change)
                self.assertTrue(out["status"].startswith("HOLD_"), out)
        self.assertEqual(self.row_counts(), (0, 0, 0))
        self.assert_original_untouched()

    def test_six_e_lanes_and_vaskon_scope_cannot_import(self):
        for member in (*sorted(preflight.MEMBERS), "VASKON"):
            e = envelope([record(scope="E_LANE", member=member)])
            # This blocked batch can never receive a valid Stage 9Y manifest.
            result = self.run_fixture(
                self.packet(), export_bytes=e["export_bytes"],
                pinned_export_sha256=e["pinned_export_sha256"],
            )
            self.assertIn(result["status"], (
                "HOLD_ARCHIVE_PREFLIGHT", "HOLD_NON_MEMORY_OR_CONFLICTED_BATCH"
            ))
        self.assertEqual(self.row_counts(), (0, 0, 0))
        self.assert_original_untouched()

    def test_26_items_exceeds_initial_batch_cap_with_zero_write(self):
        expanded = b"\n".join(
            f"PRIVATE-MEMORY-LINE-{i:03d}".encode("utf-8")
            for i in range(1, 27)
        )
        data = self.packet(
            [record(i) for i in range(1, 27)], source=expanded,
        )
        self.assertEqual(
            self.run_fixture(data)["status"], "HOLD_INITIAL_BATCH_CAP_25"
        )
        self.assertEqual(self.row_counts(), (0, 0, 0))

    def test_inmemory_attached_and_unrelated_disk_paths_rejected(self):
        data = self.packet()
        mem = sqlite3.connect(":memory:")
        self.addCleanup(mem.close)
        self.assertEqual(
            self.run_fixture(data, fixture_connection=mem)["status"],
            "HOLD_NOT_SEPARATE_FILE_BACKED_NATIVE_SQLITE_FIXTURE",
        )
        self.conn.execute("ATTACH DATABASE ':memory:' AS other")
        self.assertEqual(
            self.run_fixture(data)["status"],
            "HOLD_NOT_SEPARATE_FILE_BACKED_NATIVE_SQLITE_FIXTURE",
        )
        self.conn.execute("DETACH DATABASE other")
        another = tempfile.TemporaryDirectory()
        self.addCleanup(another.cleanup)
        self.assertEqual(
            self.run_fixture(data, fixture_root=another.name)["status"],
            "HOLD_NOT_SEPARATE_FILE_BACKED_NATIVE_SQLITE_FIXTURE",
        )
        self.assertEqual(self.row_counts(), (0, 0, 0))

    def test_explicit_confirmations_all_required_before_any_write(self):
        data = self.packet()
        for flag in (
            "confirm_separate_fixture", "confirm_owner_source_review",
            "confirm_canary_evidence_review",
        ):
            out = self.run_fixture(data, **{flag: False})
            self.assertEqual(out["status"],
                             "HOLD_EXPLICIT_FIXTURE_REVIEW_REQUIRED")
        self.assertEqual(self.row_counts(), (0, 0, 0))

    def test_failure_of_independent_reopen_never_promoted(self):
        data = self.packet()
        with patch.object(y.sqlite3, "connect", side_effect=sqlite3.OperationalError):
            out = self.run_fixture(data)
        self.assertEqual(out["status"],
                         "HOLD_FRESH_CONNECTION_READBACK_UNAVAILABLE")
        self.assertEqual(out["writes_performed"],
                         ["LOCAL_FIXTURE_WRITE_OUTCOME_UNVERIFIED"])
        # After ambiguous readback the exact signed replay reconciles state.
        retry = self.run_fixture(data)
        self.assertEqual(retry["status"], "PASS_LOCAL_EXACT_REPLAY_ZERO_WRITE")
        self.assertEqual(self.row_counts(), (1, 1, 1))
        self.assert_original_untouched()

    def test_receipt_tamper_rejected_and_no_implicit_imports(self):
        data = self.packet()
        self.run_fixture(data)
        self.conn.execute(
            "UPDATE galaxy_stage9y_batches SET receipt_hmac_sha256=?", ("0" * 64,)
        )
        self.conn.commit()
        self.assertEqual(
            self.run_fixture(data)["status"],
            "HOLD_SIGNED_RECEIPT_OR_STAGING_REPLAY_DRIFT",
        )
        self.assertNotIn("memcon_runtime", sys.modules)
        self.assertNotIn("libsql", sys.modules)
        self.assert_original_untouched()


if __name__ == "__main__":
    unittest.main()
