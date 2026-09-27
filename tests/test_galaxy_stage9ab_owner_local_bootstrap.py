"""Stage 9AB: owner-local staged bootstrap proofs, NO remote database access."""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))
import galaxy_stage9ab_owner_local_bootstrap as ab
import galaxy_stage9v_setup_bundle as vsetup
import galaxy_stage9v_staging_turso as v
import galaxy_stage9aa_local_schema_bundle as aabundle
import galaxy_stage9aa_preimport_readonly as aa

STAGE = "libsql://sovmem-staging-synthetic.aws-us-east-1.turso.io"
MAIN = "libsql://sovmem-main-synthetic.aws-us-east-1.turso.io"
TOKEN = "SYNTHETIC-STAGING-ONLY-TOKEN-NOT-REAL-SECURITY"


def bundles(marker="1c6c5644-4752-408f-8500-2cdb1d81a353"):
    vsql = vsetup.make_sql(marker).encode()
    aasql = aabundle.canonical_sql().encode()
    return {
        "v_manifest": {
            "schema": vsetup.MANIFEST_SCHEMA,
            "status": "OWNER_LOCAL_BUNDLE_CREATED_NOT_PROVISIONED",
            "database_name_label_only": "sovmem-staging",
            "staging_uuid": marker,
            "staging_sql_sha256": hashlib.sha256(vsql).hexdigest(),
            "tokens_included": False,
            "staging_database_accessed": False,
        },
        "v_sql": vsql,
        "aa_manifest": {
            "schema": aabundle.SCHEMA,
            "status": "OWNER_LOCAL_SCHEMA_FILES_ONLY_NOT_PROVISIONED",
            "staging_name_label_only": "sovmem-staging",
            "source_sql_sha256": hashlib.sha256(aasql).hexdigest(),
            "expected_layout_sha256": aa._sha(v._bytes(aa.EXPECTED_TABLES)),
            "tokens_included": False,
            "live_staging_provisioned": False,
        },
        "aa_sql": aasql,
    }


class OnlyStaging:
    def __init__(self, path):
        self.path = path
        self.calls = []

    def __call__(self, url, token):
        if url != STAGE or token != TOKEN:
            raise AssertionError("MUST NOT CONTACT MAIN OR INVALID STAGING TOKEN")
        self.calls.append((url, token))
        return sqlite3.connect(self.path)


class IsolatedBootstrapTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.root.chmod(0o700)
        self.stage_path = str(self.root / "staging.db")
        self.main_path = str(self.root / "main-untouched.db")
        with sqlite3.connect(self.main_path) as main:
            main.execute("CREATE TABLE untouched_marker (text TEXT)")
            main.execute("INSERT INTO untouched_marker VALUES ('MAIN_NEVER_TOUCH')")
        self.factory = OnlyStaging(self.stage_path)
        self.input = bundles()

    def run_bootstrap(self, **changes):
        args = {
            **self.input,
            "staging_name": "sovmem-staging",
            "main_name": "sovmem-main",
            "staging_url": STAGE,
            "main_url": MAIN,
            "staging_token": TOKEN,
            "confirm_apply": True,
            "confirm_provider_ids_reviewed": True,
            "confirm_staging_only": True,
            "confirm_main_untouched": True,
            "connector": self.factory,
        }
        args.update(changes)
        return ab.bootstrap_staging(**args)

    def check_main(self):
        with sqlite3.connect(self.main_path) as main:
            self.assertEqual(main.execute(
                "SELECT text FROM untouched_marker"
            ).fetchone(), ("MAIN_NEVER_TOUCH",))
            self.assertEqual(main.execute(
                "SELECT count(*) FROM sqlite_master WHERE type='table'"
            ).fetchone(), (1,))

    def test_dry_run_never_connects_even_if_config_is_present(self):
        report = self.run_bootstrap(confirm_apply=False)
        self.assertEqual(
            report["status"], "PASS_PRIVATE_BUNDLE_DRY_RUN_NO_CONNECTION"
        )
        self.assertEqual(self.factory.calls, [])
        self.assertFalse(Path(self.stage_path).exists())
        self.assertEqual(report["writes_performed"], [])
        self.assertFalse(report["owner_identity_independently_verified"])
        self.assertFalse(report["bigbang_activated"])
        self.check_main()

    def test_exact_schema_and_marker_via_two_connections(self):
        report = self.run_bootstrap()
        self.assertEqual(
            report["status"], "PASS_LOCAL_STAGING_SCHEMA_REOPEN_FIXTURE", report
        )
        self.assertTrue(report["fresh_separate_connection_readback"])
        self.assertEqual(report["new_staging_tables_verified"], 6)
        self.assertEqual(len(self.factory.calls), 2)
        self.assertFalse(report["staging_remotely_observed"])
        self.assertFalse(report["owner_identity_independently_verified"])
        self.assertFalse(report["provider_database_separation_independently_verified"])
        self.assertEqual(report["historical_rows_imported"], 0)
        self.assertEqual(report["writes_performed"],
                         ["SIX_STAGING_TABLES_AND_ONE_MARKER_INSERTED"])
        self.assertNotIn(TOKEN, json.dumps(report))
        self.assertNotIn(STAGE, json.dumps(report))
        with sqlite3.connect(self.stage_path) as db:
            self.assertTrue(
                ab._exact_new_schema(db, self.input["v_manifest"]["staging_uuid"])
            )
        self.check_main()

    def test_exact_replay_is_read_only_and_can_reconcile_lost_ack(self):
        first = self.run_bootstrap()
        self.assertEqual(first["status"], "PASS_LOCAL_STAGING_SCHEMA_REOPEN_FIXTURE")
        with sqlite3.connect(self.stage_path) as db:
            conn = db.execute("SELECT rootpage, sql FROM sqlite_master")
            before = conn.fetchall()
        replay = self.run_bootstrap()
        self.assertEqual(
            replay["status"],
            "PASS_LOCAL_STAGING_SCHEMA_EXACT_REPLAY_NO_WRITE",
        )
        self.assertEqual(replay["writes_performed"], [])
        self.assertTrue(replay["idempotent_read_only_replay"])
        with sqlite3.connect(self.stage_path) as db:
            self.assertEqual(
                db.execute("SELECT rootpage, sql FROM sqlite_master").fetchall(),
                before,
            )
        self.check_main()

    def test_wrong_address_label_and_same_endpoint_hold_before_connection(self):
        cases = [
            {"staging_url": MAIN, "main_url": STAGE},
            {"staging_url": MAIN},
            {"main_url": STAGE},
            {"staging_url": "libsql://sovmem-main-other.turso.io"},
            {"main_name": "sovmem-staging"},
            {"staging_url": "file:/tmp/not_remote.db"},
            {"main_url": "libsql://sovmem-main-a.turso.io?token=no"},
        ]
        for change in cases:
            with self.subTest(change=list(change)):
                result = self.run_bootstrap(**change)
                self.assertEqual(
                    result["status"], "HOLD_STAGING_MAIN_ADDRESS_OR_NAME_INVALID"
                )
        self.assertEqual(self.factory.calls, [])
        self.check_main()

    def test_each_confirmation_and_staging_only_token_required(self):
        for change in (
            {"confirm_provider_ids_reviewed": False},
            {"confirm_staging_only": False},
            {"confirm_main_untouched": False},
        ):
            with self.subTest(change=change):
                self.assertEqual(
                    self.run_bootstrap(**change)["status"],
                    "HOLD_EXPLICIT_OWNER_STAGING_APPROVAL_REQUIRED",
                )
        self.assertEqual(
            self.run_bootstrap(staging_token="")["status"],
            "HOLD_STAGING_ONLY_TOKEN_REQUIRED",
        )
        self.assertEqual(self.factory.calls, [])

    def test_manifest_tampering_labels_and_unapproved_sql_refused(self):
        data = bundles()
        tampered = dict(data)
        tampered["aa_sql"] = data["aa_sql"].replace(
            b"CREATE TABLE memory_records", b"DROP TABLE memory_records"
        )
        wrong = dict(data)
        wrong["v_manifest"] = {**data["v_manifest"], "staging_uuid": "0" * 36}
        labels = dict(data)
        labels["aa_manifest"] = {
            **data["aa_manifest"], "staging_name_label_only": "sovmem-main"
        }
        for change in (tampered, wrong, labels):
            with self.subTest(change=list(change)):
                self.assertEqual(
                    self.run_bootstrap(**change)["status"],
                    "HOLD_PRIVATE_SCHEMA_BUNDLE_INVALID",
                )
        self.assertEqual(self.factory.calls, [])
        self.check_main()

    def test_preexisting_data_or_unknown_schema_holds_before_any_setup(self):
        with sqlite3.connect(self.stage_path) as stage:
            stage.execute("CREATE TABLE E_LANE_NIMUE (private_text TEXT)")
            stage.execute("INSERT INTO E_LANE_NIMUE VALUES ('MUST_STAY')")
        report = self.run_bootstrap()
        self.assertEqual(
            report["status"], "HOLD_STAGING_NOT_EMPTY_OR_PARTIAL_SCHEMA"
        )
        self.assertEqual(report["writes_performed"], [])
        with sqlite3.connect(self.stage_path) as stage:
            self.assertEqual(stage.execute(
                "SELECT private_text FROM E_LANE_NIMUE"
            ).fetchone(), ("MUST_STAY",))
        self.check_main()

    def test_partial_schema_cannot_be_mistaken_for_exact_replay(self):
        with sqlite3.connect(self.stage_path) as stage:
            stage.execute(
                "CREATE TABLE galaxy_stage9v_staging_identity (a TEXT)"
            )
        self.assertEqual(
            self.run_bootstrap()["status"],
            "HOLD_STAGING_NOT_EMPTY_OR_PARTIAL_SCHEMA",
        )
        self.check_main()

    def test_mid_ddl_failure_rolls_back_all_six_tables_and_marker(self):
        outer = self.factory
        class Faulty:
            def __call__(self, url, token):
                raw = outer(url, token)
                class Proxy:
                    count = 0
                    def execute(self, sql, params=()):
                        if sql.strip().startswith(("CREATE ", "INSERT ")):
                            self.count += 1
                            if self.count == 4:
                                raise sqlite3.OperationalError("PRIVATE-CONNECTOR-FAULT")
                        return raw.execute(sql, params)
                    def commit(self): raw.commit()
                    def rollback(self): raw.rollback()
                    def close(self): raw.close()
                return Proxy()
        result = self.run_bootstrap(connector=Faulty())
        self.assertEqual(
            result["status"], "HOLD_STAGING_SETUP_OR_COMMIT_UNVERIFIED", result
        )
        self.assertTrue(result["staging_write_outcome_unknown"])
        self.assertNotIn("PRIVATE-CONNECTOR-FAULT", json.dumps(result))
        with sqlite3.connect(self.stage_path) as db:
            self.assertTrue(ab._known_empty(db))
        self.check_main()

    def test_lost_fresh_readback_holds_then_exact_replay_reconciles(self):
        stage = self.factory
        class FailSecond:
            def __init__(self): self.n = 0
            def __call__(self, url, token):
                self.n += 1
                if self.n == 2:
                    raise OSError("PRIVATE-SECOND-CONNECTION-FAIL")
                return stage(url, token)
        first = self.run_bootstrap(connector=FailSecond())
        self.assertEqual(first["status"], "HOLD_FRESH_STAGING_SCHEMA_UNAVAILABLE")
        self.assertTrue(first["staging_write_outcome_unknown"])
        self.assertNotIn("PRIVATE-SECOND-CONNECTION-FAIL", json.dumps(first))
        reconciled = self.run_bootstrap()
        self.assertEqual(
            reconciled["status"], "PASS_LOCAL_STAGING_SCHEMA_EXACT_REPLAY_NO_WRITE"
        )
        self.assertEqual(reconciled["writes_performed"], [])
        self.check_main()

    def test_after_canary_written_bootstrap_replay_refuses_to_mutate(self):
        self.run_bootstrap()
        with sqlite3.connect(self.stage_path) as db:
            db.execute(
                "INSERT INTO galaxy_stage9v_canaries VALUES(?,?,?,?)",
                ("SYNTHETIC-CANARY", "a"*64,
                 self.input["v_manifest"]["staging_uuid"], "2026-09-27"),
            )
        out = self.run_bootstrap()
        self.assertEqual(out["status"], "HOLD_STAGING_NOT_EMPTY_OR_PARTIAL_SCHEMA")
        self.assertEqual(out["writes_performed"], [])
        self.check_main()

    def test_real_libsql_driver_against_LOCAL_DISPOSABLE_FILE(self):
        try:
            import libsql
        except ImportError:
            self.skipTest("CI installs real local libsql driver")
        class LocalLibsql:
            def __init__(self): self.opens = 0
            def __call__(self, url, token):
                self.opens += 1
                if (url, token) != (STAGE, TOKEN):
                    raise AssertionError("REMOTE ROUTE OR TOKEN")
                return libsql.connect(database=self.stage_path)
        connector = LocalLibsql()
        connector.stage_path = self.stage_path
        result = self.run_bootstrap(connector=connector)
        self.assertEqual(result["status"], "PASS_LOCAL_STAGING_SCHEMA_REOPEN_FIXTURE",
                         result)
        self.assertEqual(connector.opens, 2)
        self.assertFalse(result["staging_remotely_observed"])
        self.check_main()

    def test_cli_private_file_validation_and_no_default_live_connect(self):
        vdir = self.root / "private-v"
        adir = self.root / "private-a"
        vdir.mkdir(mode=0o700)
        adir.mkdir(mode=0o700)
        paths = [
            (vdir / vsetup._MANIFEST_NAME, json.dumps(self.input["v_manifest"])),
            (vdir / vsetup._SQL_NAME, self.input["v_sql"]),
            (adir / aabundle.MANIFEST_NAME, json.dumps(self.input["aa_manifest"])),
            (adir / aabundle.SQL_NAME, self.input["aa_sql"]),
        ]
        for path, raw in paths:
            path.write_bytes(raw if isinstance(raw, bytes) else raw.encode())
            path.chmod(0o600)
        args = [
            "--stage9v-manifest", str(paths[0][0]),
            "--stage9v-sql", str(paths[1][0]),
            "--stage9aa-manifest", str(paths[2][0]),
            "--stage9aa-sql", str(paths[3][0]),
        ]
        with patch.object(v, "_connect_live",
                          side_effect=AssertionError("DRY RUN MUST NOT CONNECT")):
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                exit_code = ab.main(args)
            self.assertEqual(exit_code, 0)
            self.assertEqual(
                json.loads(captured.getvalue())["status"],
                "PASS_PRIVATE_BUNDLE_DRY_RUN_NO_CONNECTION",
            )
        paths[2][0].chmod(0o644)
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            exit_code = ab.main(args)
        self.assertEqual(exit_code, 2)
        self.assertEqual(
            json.loads(captured.getvalue())["status"],
            "HOLD_OWNER_PRIVATE_BUNDLE_FILES_INVALID",
        )
        self.assertEqual(self.factory.calls, [])
        self.check_main()


if __name__ == "__main__":
    unittest.main()
