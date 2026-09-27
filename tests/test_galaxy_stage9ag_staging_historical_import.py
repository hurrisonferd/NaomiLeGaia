"""Stage 9AG signed first archival Turso adapter: DISPOSABLE LOCAL ONLY.

Real native sqlite and actual public libSQL driver against a temporary local
file, separate untouched production/main sentinels. No credential or network.
An injected connector can NEVER claim a successful remote staging run.
"""
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
import galaxy_stage9ag_staging_historical_import as ag
import galaxy_stage9ac_full_local_rehearsal as chain
import galaxy_stage9aa_preimport_readonly as aa
import galaxy_stage9ab_owner_local_bootstrap as ab
import galaxy_stage9v_staging_turso as v
import galaxy_stage9y_canonical_staging as y
import galaxy_archive_staging as archive
from test_galaxy_stage9ab_owner_local_bootstrap import bundles

KEY = b"STAGE9AG-SYNTHETIC-FIXTURE-KEY-ONLY-NEVER-OWNER-KEY-001"
RUN = "STAGE9AG-SYNTHETIC-PINNED-CANARY-001"
NONCE = hashlib.sha256(b"STAGE9AG-PRIVATE-SYNTHETIC-NONCE").hexdigest()
APPROVAL_ID = "STAGE9AG-SYNTHETIC-FIRST-BATCH-001"


class LocalOnly:
    def __init__(self, path: Path, *, driver: str = "native"):
        self.path = path
        self.driver = driver
        self.calls = []

    def __call__(self, url, token):
        if (url, token) != (chain.STAGE, chain.TOKEN):
            raise AssertionError("MUST NOT CONNECT MAIN OR REAL TURSO")
        self.calls.append("LOCAL_STAGING_FILE_ONLY")
        if self.driver == "libsql":
            import libsql
            return libsql.connect(database=str(self.path))
        return sqlite3.connect(self.path)


class FirstSignedStagingTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.root.chmod(0o700)
        self.stage = self.root / "staging.db"
        self.main = self.root / "sovmem-main-SYNTHETIC.db"
        self.original = self.root / "original-GaiaOS-SYNTHETIC.db"
        for path, sentinel in (
            (self.main, "SOVMEM_MAIN_PRESERVE"),
            (self.original, "GAIAOS_ORIGINAL_PRESERVE"),
        ):
            with sqlite3.connect(path) as db:
                db.execute("CREATE TABLE untouched (sentinel TEXT)")
                db.execute("INSERT INTO untouched VALUES (?)", (sentinel,))
        self.main_bytes = self.main.read_bytes()
        self.original_bytes = self.original.read_bytes()
        self.bundle = bundles()
        self.marker = self.bundle["v_manifest"]["staging_uuid"]
        with sqlite3.connect(self.stage) as db:
            for statement in ab._commands(self.marker):
                db.execute(statement)
            db.execute(
                "INSERT INTO galaxy_stage9v_canaries VALUES (?,?,?,?)",
                (RUN, NONCE, self.marker, "2026-09-27T17:35:00+00:00"),
            )
        self.canary = {
            "run_id": RUN, "nonce_sha256": NONCE,
            "database_id": self.marker,
            "created_at": "2026-09-27T17:35:00+00:00",
        }
        self.pin = {
            "schema": aa.PIN_SCHEMA,
            "run_id": RUN, "canary_sha256": v._sha(v._bytes(self.canary)),
            "staging_uuid_sha256": v._sha(self.marker.encode()),
            "staging_url_sha256": v._sha(
                v._canonical_url(chain.STAGE).encode()
            ),
            "production_url_sha256": v._sha(
                v._canonical_url(chain.MAIN).encode()
            ),
        }
        self.config = {
            "staging_url": chain.STAGE,
            "production_url": chain.MAIN,
            "staging_token": chain.TOKEN,
            "expected_staging_id": self.marker,
        }
        self.export = chain._synthetic_export()
        self.source = chain.SOURCE
        packet = archive._verified_packet(
            self.export, v._sha(self.export),
            self.source, v._sha(self.source),
        )
        self.assertFalse(isinstance(packet, str), packet)
        self.items = packet[1]
        self.approval = ag.expected_approval(
            config=self.config, pin=self.pin,
            approval_id=APPROVAL_ID,
            export_sha256=v._sha(self.export),
            source_sha256=v._sha(self.source),
            items=self.items,
        )
        self.assertIsNotNone(self.approval)
        self.signature = hmac.new(
            KEY, y._bytes(self.approval), hashlib.sha256,
        ).hexdigest()
        self.connector = LocalOnly(self.stage)
        self.args = dict(
            config=self.config, pin=self.pin,
            export_bytes=self.export,
            pinned_export_sha256=v._sha(self.export),
            source_bytes=self.source,
            pinned_source_sha256=v._sha(self.source),
            approval=self.approval, signature_hex=self.signature,
            approval_key=KEY, connector=self.connector,
            confirm_source_review=True,
            confirm_independent_pin=True,
            confirm_provider_ids_reviewed=True,
            confirm_staging_token_scope_reviewed=True,
            confirm_first_held_batch_only=True,
        )

    def run_import(self, **changes):
        with patch.object(
            v, "_connect_live",
            side_effect=AssertionError("NO REMOTE NETWORK"),
        ):
            return ag.stage_first_signed_batch(**{**self.args, **changes})

    def protected(self):
        self.assertEqual(self.main.read_bytes(), self.main_bytes)
        self.assertEqual(self.original.read_bytes(), self.original_bytes)
        with sqlite3.connect(self.stage) as db:
            self.assertTrue(v._identity(db, self.marker))
            self.assertEqual(v._canary(db, RUN), self.canary)
            self.assertTrue(ag._safe_schema(db, self.config, self.pin))

    def counts(self):
        with sqlite3.connect(self.stage) as db:
            return tuple(
                db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                for t in (
                    "memory_records", "galaxy_stage9y_batches",
                    "galaxy_stage9y_items", "galaxy_stage9z_rollbacks",
                )
            )

    def test_default_dry_run_zero_connections_zero_changes_even_with_config(self):
        original = self.stage.read_bytes()
        result = self.run_import()
        self.assertEqual(
            result["status"], "PASS_SIGNED_SOURCE_DRY_RUN_ZERO_CONNECTION",
        )
        self.assertEqual(result["exact_batch_item_count"], 2)
        self.assertEqual(self.connector.calls, [])
        self.assertEqual(self.stage.read_bytes(), original)
        self.assertEqual(result["writes_performed"], [])
        self.assertFalse(result["staging_remotely_observed"])
        self.assertFalse(result["independent_owner_authentication_verified"])
        self.assertEqual(self.counts(), (0, 0, 0, 0))
        self.protected()

    def test_first_batch_atomic_exact_two_hold_rows_and_signed_receipts(self):
        result = self.run_import(apply=True)
        self.assertEqual(
            result["status"], "PASS_LOCAL_HELD_STAGING_IMPORT_REOPEN_FIXTURE",
            result,
        )
        self.assertEqual(result["exact_held_rows"], 2)
        self.assertEqual(result["signed_item_receipts"], 2)
        self.assertTrue(result["fresh_separate_connection_readback"])
        self.assertFalse(result["staging_remotely_observed"])
        self.assertFalse(result["provider_identity_and_alias_separation_verified"])
        self.assertFalse(result["bigbang_activated"])
        self.assertFalse(result["e_lanes_modified"])
        self.assertEqual(self.counts(), (2, 1, 2, 0))
        with sqlite3.connect(self.stage) as db:
            self.assertEqual(
                db.execute("SELECT DISTINCT status FROM memory_records")
                .fetchall(), [(y.STATUS,)],
            )
            self.assertEqual(
                db.execute(
                    "SELECT DISTINCT result FROM galaxy_stage9y_items"
                ).fetchall(), [(ag.RESULT,)],
            )
            self.assertTrue(all(
                row[0].startswith("galaxy-archive-v1:")
                for row in db.execute("SELECT source FROM memory_records")
            ))
        redacted = json.dumps(result)
        for string in (chain.STAGE, chain.MAIN, chain.TOKEN,
                       "STAGE9AC-SYNTHETIC-ARCHIVED-MEMORY"):
            self.assertNotIn(string, redacted)
        self.protected()

    def test_exact_replay_is_separate_fresh_read_only_and_byte_identical(self):
        self.assertEqual(
            self.run_import(apply=True)["status"],
            "PASS_LOCAL_HELD_STAGING_IMPORT_REOPEN_FIXTURE",
        )
        old = self.stage.read_bytes()
        count = len(self.connector.calls)
        replay = self.run_import(apply=True)
        self.assertEqual(replay["status"], "PASS_LOCAL_SIGNED_REPLAY_NO_WRITE",
                         replay)
        self.assertTrue(replay["idempotent_zero_write_replay"])
        self.assertEqual(replay["writes_performed"], [])
        self.assertGreater(len(self.connector.calls), count)
        self.assertEqual(self.stage.read_bytes(), old)
        self.assertEqual(self.counts(), (2, 1, 2, 0))
        self.protected()

    def test_real_libsql_driver_uses_only_local_disposable_file(self):
        try:
            import libsql
        except ImportError:
            self.skipTest("CI installs REAL libsql for local-file tests")
        connector = LocalOnly(self.stage, driver="libsql")
        result = self.run_import(apply=True, connector=connector)
        self.assertEqual(
            result["status"], "PASS_LOCAL_HELD_STAGING_IMPORT_REOPEN_FIXTURE",
            result,
        )
        self.assertGreaterEqual(len(connector.calls), 5)
        self.assertFalse(result["staging_remotely_observed"])
        self.assertEqual(self.counts(), (2, 1, 2, 0))
        replay = self.run_import(apply=True, connector=connector)
        self.assertEqual(replay["status"], "PASS_LOCAL_SIGNED_REPLAY_NO_WRITE",
                         replay)
        self.protected()

    def test_all_five_owner_flags_hold_before_any_connection(self):
        flags = (
            "confirm_source_review", "confirm_independent_pin",
            "confirm_provider_ids_reviewed",
            "confirm_staging_token_scope_reviewed",
            "confirm_first_held_batch_only",
        )
        for flag in flags:
            with self.subTest(flag=flag):
                out = self.run_import(apply=True, **{flag: False})
                self.assertEqual(
                    out["status"],
                    "HOLD_FIVE_EXPLICIT_OWNER_CONFIRMATIONS_REQUIRED",
                )
                out = self.run_import(apply=True, **{flag: 1})
                self.assertEqual(
                    out["status"],
                    "HOLD_FIVE_EXPLICIT_OWNER_CONFIRMATIONS_REQUIRED",
                )
        self.assertEqual(self.connector.calls, [])
        self.assertEqual(self.counts(), (0, 0, 0, 0))
        self.protected()

    def test_local_9y_signature_cannot_be_reused_as_remote_9ag_consent(self):
        local = y._expected_manifest(
            config=self.config, approval={
                "approval_id": APPROVAL_ID,
                "canary_run_id": RUN,
                "canary_sha256": self.pin["canary_sha256"],
            },
            export_hash=v._sha(self.export),
            source_hash=v._sha(self.source),
            items=self.items,
        )
        sig = hmac.new(KEY, y._bytes(local), hashlib.sha256).hexdigest()
        out = self.run_import(
            apply=True, approval=local, signature_hex=sig,
        )
        self.assertEqual(
            out["status"],
            "HOLD_DOMAIN_SEPARATED_SIGNED_STAGING_APPROVAL_REQUIRED",
        )
        self.assertEqual(self.connector.calls, [])
        self.protected()

    def test_wrong_pins_token_host_or_signed_manifest_hold_before_connection(self):
        for change in (
            {"signature_hex": "0" * 64},
            {"approval_key": b"wrong-key-is-not-the-owner" * 3},
            {"pinned_source_sha256": "0" * 64},
            {"pinned_export_sha256": "0" * 64},
            {"config": {**self.config, "staging_url": chain.MAIN}},
            {"config": {**self.config, "staging_token": ""}},
            {"config": {**self.config, "production_url": chain.STAGE}},
            {"pin": {**self.pin, "canary_sha256": "0" * 64}},
        ):
            with self.subTest(change=list(change)):
                self.assertTrue(
                    self.run_import(apply=True, **change)["status"].startswith("HOLD_")
                )
        self.assertEqual(self.connector.calls, [])
        self.assertEqual(self.counts(), (0, 0, 0, 0))
        self.protected()

    def test_unknown_view_or_preexisting_row_holds_without_overwrite(self):
        with sqlite3.connect(self.stage) as db:
            db.execute(
                "CREATE VIEW malicious_view AS SELECT 1 AS fake"
            )
        self.assertEqual(
            self.run_import(apply=True)["status"],
            "HOLD_STAGING_SCHEMA_IDENTITY_OR_CANARY_MISMATCH",
        )
        with sqlite3.connect(self.stage) as db:
            db.execute("DROP VIEW malicious_view")
            db.execute(
                "INSERT INTO memory_records VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    "MEM-STAGE9AG-EXISTING", "NAOMI", "TEST", "MemoryOS",
                    "EXISTING_PRIVATE_DATA", "preexisting", "ACTIVE", "1",
                    "2026-01-01", "2026-01-01", None, "{}",
                ),
            )
        self.assertEqual(
            self.run_import(apply=True)["status"],
            "HOLD_ONLY_FIRST_EMPTY_STAGING_BATCH_SUPPORTED",
        )
        with sqlite3.connect(self.stage) as db:
            self.assertEqual(
                db.execute("SELECT statement FROM memory_records").fetchone(),
                ("EXISTING_PRIVATE_DATA",),
            )
        self.protected()

    def test_changed_canary_or_identity_holds_before_insertion(self):
        with sqlite3.connect(self.stage) as db:
            db.execute(
                "UPDATE galaxy_stage9v_canaries SET nonce_sha256=?",
                ("0"*64,),
            )
        self.assertEqual(
            self.run_import(apply=True)["status"],
            "HOLD_STAGING_SCHEMA_IDENTITY_OR_CANARY_MISMATCH",
        )
        self.assertEqual(self.counts(), (0, 0, 0, 0))
        self.assertEqual(len(self.connector.calls), 1)

    def test_fault_during_item_insert_rolls_back_entire_batch(self):
        factory = self.connector
        class Fault:
            def __call__(self, url, token):
                raw = factory(url, token)
                class Proxy:
                    def execute(self, sql, params=()):
                        if sql.strip().startswith("INSERT INTO galaxy_stage9y_items"):
                            raise sqlite3.OperationalError("PRIVATE-DO-NOT-EXPOSE")
                        return raw.execute(sql, params)
                    def commit(self): raw.commit()
                    def rollback(self): raw.rollback()
                    def close(self): raw.close()
                return Proxy()
        result = self.run_import(apply=True, connector=Fault())
        self.assertEqual(
            result["status"], "HOLD_STAGING_TRANSACTION_OUTCOME_UNVERIFIED",
            result,
        )
        self.assertTrue(result["write_outcome_uncertain"])
        self.assertNotIn("PRIVATE-DO-NOT-EXPOSE", json.dumps(result))
        self.assertEqual(self.counts(), (0, 0, 0, 0))
        self.protected()

    def test_lost_postcommit_fresh_readback_recovers_with_exact_replay(self):
        factory = self.connector
        class FailFinal:
            def __init__(self): self.calls = 0
            def __call__(self, url, token):
                self.calls += 1
                if self.calls == 6:
                    raise OSError("PRIVATE-FRESH-REOPEN-FAIL")
                return factory(url, token)
        bad = FailFinal()
        first = self.run_import(apply=True, connector=bad)
        self.assertEqual(
            first["status"], "HOLD_FRESH_STAGING_REOPEN_UNAVAILABLE", first
        )
        self.assertTrue(first["write_outcome_uncertain"])
        self.assertEqual(self.counts(), (2, 1, 2, 0))
        recovered = self.run_import(apply=True)
        self.assertEqual(
            recovered["status"], "PASS_LOCAL_SIGNED_REPLAY_NO_WRITE", recovered
        )
        self.assertEqual(recovered["writes_performed"], [])
        self.protected()

    def test_mutated_row_or_receipt_holds_on_signed_replay(self):
        self.run_import(apply=True)
        with sqlite3.connect(self.stage) as db:
            db.execute("UPDATE memory_records SET status='ACTIVE'")
        failure = self.run_import(apply=True)
        self.assertEqual(failure["status"], "HOLD_REPLAY_ROW_OR_SIGNED_LEDGER_DRIFT")
        self.assertEqual(failure["writes_performed"], [])
        self.protected()

    def test_second_new_approval_cannot_write_more_than_initial_single_batch(self):
        self.run_import(apply=True)
        second_approval = ag.expected_approval(
            config=self.config, pin=self.pin,
            approval_id="STAGE9AG-SYNTHETIC-SECOND-BATCH",
            export_sha256=v._sha(self.export),
            source_sha256=v._sha(self.source),
            items=self.items,
        )
        signed = hmac.new(
            KEY, y._bytes(second_approval), hashlib.sha256,
        ).hexdigest()
        failure = self.run_import(
            apply=True, approval=second_approval, signature_hex=signed,
        )
        self.assertEqual(
            failure["status"], "HOLD_ONLY_FIRST_EMPTY_STAGING_BATCH_SUPPORTED",
        )
        self.assertEqual(self.counts(), (2, 1, 2, 0))
        self.protected()


if __name__ == "__main__":
    unittest.main()
