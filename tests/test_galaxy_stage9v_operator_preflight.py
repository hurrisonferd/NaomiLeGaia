"""Stage 9V operator safety: read-only staging assessment, no token echoes."""
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

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))
import galaxy_stage9v_operator_preflight as readiness
import galaxy_stage9v_staging_turso as probe

STAGING = "libsql://stage9v-readiness-fixture.turso.io"
PRODUCTION = "libsql://production-fixture.turso.io"
STAGING_ID = "8744d4f4-cea2-4d42-8b68-3f6cd349912a"
TOKEN = "PRIVATE-STAGING-TOKEN-NEVER-ECHOED"


class OperatorReadinessTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = str(Path(tmp.name) / "staging-only.db")
        self.connect_count = 0
        self.queries = []
        with sqlite3.connect(self.path) as db:
            db.executescript("""
                CREATE TABLE galaxy_stage9v_staging_identity (
                    schema TEXT, environment TEXT, database_id TEXT,
                    authority TEXT, status TEXT
                );
                CREATE TABLE galaxy_stage9v_canaries (
                    run_id TEXT PRIMARY KEY, nonce_sha256 TEXT,
                    database_id TEXT, created_at TEXT
                );
                CREATE TABLE memory_records (
                    record_id TEXT PRIMARY KEY, statement TEXT
                );
                INSERT INTO memory_records VALUES ('KEEP','NO-CHANGES');
            """)
            db.execute(
                "INSERT INTO galaxy_stage9v_staging_identity VALUES (?,?,?,?,?)",
                (probe.IDENTITY_SCHEMA, "STAGING_ONLY", STAGING_ID, "NAOMI", "ACTIVE"),
            )

    def connector(self, url, token):
        if url != STAGING or token != TOKEN:
            raise AssertionError("attempted to access non-staging credentials")
        self.connect_count += 1
        db = sqlite3.connect(self.path)
        outer = self

        class ReadOnly:
            def execute(self, query, params=()):
                outer.queries.append(query)
                if not query.strip().upper().startswith("SELECT "):
                    raise AssertionError("non-SELECT attempted")
                return db.execute(query, params)

            def close(self):
                db.close()

        return ReadOnly()

    def assess(self, **kw):
        params = {
            "staging_url": STAGING, "staging_token": TOKEN,
            "production_url": PRODUCTION, "expected_staging_id": STAGING_ID,
            "connector": self.connector,
        }
        params.update(kw)
        return readiness.check_staging_readiness(**params)

    def test_valid_marker_requires_two_selects_and_no_writes(self):
        with sqlite3.connect(self.path) as db:
            before = db.total_changes
            previous_rows = db.execute("SELECT * FROM memory_records").fetchall()
        out = self.assess()
        self.assertEqual(out["status"], "PASS_STAGING_READINESS_READ_ONLY", out)
        self.assertEqual(self.connect_count, 1)
        self.assertEqual(out["reads_performed"], 2)
        self.assertEqual(len(self.queries), 2)
        self.assertTrue(all(q.strip().upper().startswith("SELECT ") for q in self.queries))
        self.assertEqual(out["writes_performed"], [])
        self.assertFalse(out["staging_turso_remotely_observed"])
        self.assertFalse(out["provider_database_separation_independently_verified"])
        self.assertFalse(out["live_owner_authentication_verified"])
        self.assertFalse(out["canary_written"])
        self.assertFalse(out["mode_control_modified"])
        self.assertFalse(out["e_lanes_modified"])
        self.assertTrue(out["staging_marker_readback_verified"])
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT * FROM memory_records").fetchall(), previous_rows)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM galaxy_stage9v_canaries").fetchone()[0], 0)
        self.assertNotIn(TOKEN, json.dumps(out))
        self.assertNotIn(STAGING, json.dumps(out))
        self.assertNotIn(PRODUCTION, json.dumps(out))

    def test_same_staging_and_production_url_refused_before_connect(self):
        out = self.assess(production_url="https://stage9v-readiness-fixture.turso.io")
        self.assertEqual(out["status"], "HOLD_STAGING_AND_PRODUCTION_URLS_NOT_SEPARATE")
        self.assertEqual(self.connect_count, 0)
        self.assertEqual(out["reads_performed"], 0)

    def test_missing_bad_credentials_or_uuid_refused_before_connect(self):
        self.assertEqual(self.assess(staging_token="")["status"], "HOLD_STAGING_TOKEN_MISSING")
        self.assertEqual(self.assess(expected_staging_id="invalid")["status"], "HOLD_STAGING_UUID_INVALID")
        self.assertEqual(self.connect_count, 0)

    def test_duplicate_or_revoked_marker_holds(self):
        with sqlite3.connect(self.path) as db:
            db.execute(
                "INSERT INTO galaxy_stage9v_staging_identity VALUES (?,?,?,?,?)",
                (probe.IDENTITY_SCHEMA, "STAGING_ONLY", STAGING_ID, "NAOMI", "ACTIVE"),
            )
        self.assertEqual(self.assess()["status"], "HOLD_STAGING_IDENTITY_UNVERIFIED")
        with sqlite3.connect(self.path) as db:
            db.execute("DELETE FROM galaxy_stage9v_staging_identity")
            db.execute(
                "INSERT INTO galaxy_stage9v_staging_identity VALUES (?,?,?,?,?)",
                (probe.IDENTITY_SCHEMA, "STAGING_ONLY", STAGING_ID, "NAOMI", "REVOKED"),
            )
        self.assertEqual(self.assess()["status"], "HOLD_STAGING_IDENTITY_UNVERIFIED")

    def test_missing_canary_table_holds_without_schema_creation(self):
        with sqlite3.connect(self.path) as db:
            db.execute("DROP TABLE galaxy_stage9v_canaries")
        out = self.assess()
        self.assertEqual(out["status"], "HOLD_STAGING_READ_UNAVAILABLE")
        self.assertEqual(out["error_type"], "OperationalError")
        with sqlite3.connect(self.path) as db:
            self.assertIsNone(db.execute(
                "SELECT name FROM sqlite_master WHERE name='galaxy_stage9v_canaries'",
            ).fetchone())

    def test_unexpected_canary_columns_block_readiness(self):
        with sqlite3.connect(self.path) as db:
            db.execute("DROP TABLE galaxy_stage9v_canaries")
            db.execute("CREATE TABLE galaxy_stage9v_canaries (run_id TEXT)")
        out = self.assess()
        # The missing columns cannot be SELECTed, so fail-closed as unavailable.
        self.assertEqual(out["status"], "HOLD_STAGING_READ_UNAVAILABLE")

    def test_connector_error_is_redacted(self):
        def failing(*_):
            raise RuntimeError("STAGING-PRIVATE-CREDENTIAL")
        out = self.assess(connector=failing)
        self.assertEqual(out["status"], "HOLD_STAGING_READ_UNAVAILABLE")
        self.assertEqual(out["error_type"], "RuntimeError")
        self.assertNotIn("STAGING-PRIVATE-CREDENTIAL", json.dumps(out))

    def test_cli_missing_env_gives_variable_names_not_values(self):
        sink = io.StringIO()
        with patch.dict(os.environ, {}, clear=True), contextlib.redirect_stdout(sink):
            code = readiness.main(["--confirm-read-only"])
        out = json.loads(sink.getvalue())
        self.assertEqual(code, 2)
        self.assertEqual(out["status"], "HOLD_REQUIRED_OPERATOR_ENV_UNSET")
        self.assertEqual(set(out["missing_variable_names"]), set(readiness.CONFIG.values()))
        self.assertNotIn("PRIVATE-STAGING", sink.getvalue())

    def test_cli_requires_explicit_read_only_flag(self):
        sink = io.StringIO()
        with contextlib.redirect_stdout(sink):
            code = readiness.main([])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(sink.getvalue())["status"],
                         "HOLD_EXPLICIT_READ_ONLY_FLAG_REQUIRED")

    def test_cli_from_env_calls_exact_config_without_echo(self):
        variables = {
            readiness.CONFIG["staging_url"]: STAGING,
            readiness.CONFIG["staging_token"]: TOKEN,
            readiness.CONFIG["production_url"]: PRODUCTION,
            readiness.CONFIG["expected_staging_id"]: STAGING_ID,
        }
        result = self.assess()
        sink = io.StringIO()
        with patch.dict(os.environ, variables, clear=True), patch.object(
            readiness, "check_staging_readiness", return_value=result,
        ) as call, contextlib.redirect_stdout(sink):
            code = readiness.main(["--confirm-read-only"])
        self.assertEqual(code, 0)
        call.assert_called_once_with(
            staging_url=STAGING, staging_token=TOKEN,
            production_url=PRODUCTION, expected_staging_id=STAGING_ID,
        )
        self.assertNotIn(TOKEN, sink.getvalue())
        self.assertNotIn(STAGING, sink.getvalue())
        self.assertEqual(json.loads(sink.getvalue())["status"],
                         "PASS_STAGING_READINESS_READ_ONLY")


if __name__ == "__main__":
    unittest.main()
