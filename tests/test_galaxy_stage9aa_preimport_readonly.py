"""GALAXY Stage 9AA: SELECT-only schema/canary proof, local fixtures ONLY."""
from __future__ import annotations

import contextlib
import hashlib
import importlib
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
import galaxy_stage9aa_preimport_readonly as aa
import galaxy_stage9v_staging_turso as v
import galaxy_stage9v_operator_preflight as vr

STAGE = "libsql://stage9aa-fixture-isolated.turso.io"
PROD = "libsql://stage9aa-fixture-production-never-open.turso.io"
MARKER = "7ec56adc-f0d8-4b72-a974-8a0f4e6e81bf"
RUN = "STAGE9AA-CANARY-FIXTURE-0001"
TOKEN = "STAGE9AA-FIXTURE-READONLY-TOKEN-NEVER-LIVE"
CANARY = {
    "run_id": RUN,
    "nonce_sha256": hashlib.sha256(b"synthetic-staging-canary").hexdigest(),
    "database_id": MARKER,
    "created_at": "2026-09-27T19:21:00+00:00",
}
CONFIG = {
    "staging_url": STAGE, "staging_token": TOKEN,
    "production_url": PROD, "expected_staging_id": MARKER,
}


def pin(config=CONFIG):
    s = v._canonical_url(config["staging_url"])
    p = v._canonical_url(config["production_url"])
    return {
        "schema": aa.PIN_SCHEMA,
        "run_id": RUN,
        "canary_sha256": hashlib.sha256(v._bytes(CANARY)).hexdigest(),
        "staging_uuid_sha256": hashlib.sha256(MARKER.encode()).hexdigest(),
        "staging_url_sha256": hashlib.sha256(s.encode()).hexdigest(),
        "production_url_sha256": hashlib.sha256(p.encode()).hexdigest(),
    }


class ReadOnlyConnector:
    """Even if Stage 9AA accidentally tries INSERT, this fixture refuses it."""
    def __init__(self, dbfile):
        self.dbfile = dbfile
        self.opens = []
        self.queries = []
        self.after_first_close = None
        self.fail_second_close = False

    def __call__(self, url, token):
        if url != STAGE or token != TOKEN:
            raise AssertionError("PRODUCTION OR UNKNOWN CREDENTIAL ATTEMPT")
        self.opens.append((url, token))
        conn = sqlite3.connect(self.dbfile)
        outer = self
        nth = len(self.opens)

        class ReadOnly:
            def execute(self, sql, params=()):
                outer.queries.append(sql)
                if not sql.strip().upper().startswith("SELECT "):
                    raise AssertionError("MUTATING SQL IS NEVER PERMITTED")
                return conn.execute(sql, params)

            def close(self):
                conn.close()
                if nth == 1 and outer.after_first_close is not None:
                    outer.after_first_close()
                if nth == 2 and outer.fail_second_close:
                    raise OSError("PRIVATE-CLOSE-ERROR-NO-ECHO")
        return ReadOnly()


def make_schema(conn):
    conn.executescript("""
        CREATE TABLE galaxy_stage9v_staging_identity (
            schema TEXT NOT NULL, environment TEXT NOT NULL,
            database_id TEXT PRIMARY KEY, authority TEXT NOT NULL,
            status TEXT NOT NULL
        );
        CREATE TABLE galaxy_stage9v_canaries (
            run_id TEXT PRIMARY KEY, nonce_sha256 TEXT NOT NULL,
            database_id TEXT NOT NULL, created_at TEXT NOT NULL
        );
        CREATE TABLE memory_records (
            record_id TEXT PRIMARY KEY,
            authority TEXT NOT NULL, record_type TEXT NOT NULL,
            scope TEXT NOT NULL, statement TEXT NOT NULL,
            source TEXT NOT NULL, status TEXT NOT NULL,
            version TEXT NOT NULL, created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL, supersedes TEXT,
            notes TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE galaxy_stage9y_batches (
            approval_id TEXT PRIMARY KEY,
            manifest_sha256 TEXT NOT NULL,
            export_sha256 TEXT NOT NULL,
            source_sha256 TEXT NOT NULL,
            canary_sha256 TEXT NOT NULL,
            receipt_json TEXT NOT NULL,
            receipt_hmac_sha256 TEXT NOT NULL,
            status TEXT NOT NULL, created_at TEXT NOT NULL
        );
        CREATE TABLE galaxy_stage9y_items (
            receipt_id TEXT PRIMARY KEY, approval_id TEXT NOT NULL,
            record_id TEXT NOT NULL, source_key_sha256 TEXT NOT NULL,
            statement_sha256 TEXT NOT NULL, metadata_sha256 TEXT NOT NULL,
            row_sha256 TEXT NOT NULL, result TEXT NOT NULL
        );
        CREATE TABLE galaxy_stage9z_rollbacks (
            rollback_id TEXT PRIMARY KEY,
            import_approval_id TEXT NOT NULL UNIQUE,
            rollback_manifest_sha256 TEXT NOT NULL,
            import_receipt_sha256 TEXT NOT NULL,
            receipt_json TEXT NOT NULL,
            receipt_hmac_sha256 TEXT NOT NULL,
            status TEXT NOT NULL, created_at TEXT NOT NULL
        );
    """)
    conn.execute(
        "INSERT INTO galaxy_stage9v_staging_identity VALUES (?,?,?,?,?)",
        (v.IDENTITY_SCHEMA, "STAGING_ONLY", MARKER, "NAOMI", "ACTIVE"),
    )
    conn.execute(
        "INSERT INTO galaxy_stage9v_canaries VALUES (?,?,?,?)",
        tuple(CANARY[k] for k in (
            "run_id", "nonce_sha256", "database_id", "created_at"
        )),
    )
    conn.commit()


class LocalReadOnlyReadinessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dbfile = str(Path(self.tmp.name) / "isolated-stage9aa.db")
        with sqlite3.connect(self.dbfile) as db:
            make_schema(db)
        self.factory = ReadOnlyConnector(self.dbfile)

    def assess(self, **overrides):
        options = {
            "config": CONFIG, "pin": pin(),
            "confirm_independent_canary_pin": True,
            "connector": self.factory,
        }
        options.update(overrides)
        return aa.check_preimport_staging(**options)

    def test_readonly_full_schema_prior_canary_and_empty_staging(self):
        out = self.assess()
        self.assertEqual(out["status"], "PASS_LOCAL_READ_ONLY_SCHEMA_FIXTURE", out)
        self.assertTrue(out["schema_layout_verified"])
        self.assertTrue(out["pinned_same_database_canary_verified"])
        self.assertTrue(out["preimport_tables_empty_verified"])
        self.assertFalse(out["staging_turso_remotely_observed"])
        self.assertFalse(out["provider_database_separation_independently_verified"])
        self.assertFalse(out["live_owner_authentication_verified"])
        self.assertFalse(out["staging_token_readonly_permission_independently_verified"])
        self.assertEqual(out["read_only_select_count"], 16)
        self.assertEqual(out["staging_writes_performed"], [])
        self.assertEqual(len(self.factory.opens), 2)
        self.assertTrue(all(
            s.strip().upper().startswith("SELECT ")
            for s in self.factory.queries
        ))
        self.assertFalse(any(
            "SELECT * FROM memory_records" in s and "LIMIT 0" not in s
            for s in self.factory.queries
        ))
        serialized = json.dumps(out)
        for private in (STAGE, PROD, TOKEN, MARKER, CANARY["nonce_sha256"]):
            self.assertNotIn(private, serialized)
        with sqlite3.connect(self.dbfile) as conn:
            self.assertEqual(conn.execute(
                "SELECT COUNT(*) FROM memory_records"
            ).fetchone()[0], 0)
            self.assertEqual(conn.execute(
                "SELECT COUNT(*) FROM galaxy_stage9v_canaries"
            ).fetchone()[0], 1)

    def test_pin_or_alias_mismatch_holds_before_any_connection(self):
        base = pin()
        for change in (
            {"pin": {**base, "staging_uuid_sha256": "0" * 64}},
            {"pin": {**base, "production_url_sha256": "0" * 64}},
            {"pin": {**base, "unexpected_token": TOKEN}},
            {"pin": {**base, "run_id": "bad!"}},
            {"config": {**CONFIG, "production_url": STAGE}},
            {"config": {**CONFIG, "staging_token": ""}},
            {"config": {**CONFIG, "expected_staging_id": "bad"}},
            {"confirm_independent_canary_pin": False},
        ):
            with self.subTest(changed=list(change)):
                out = self.assess(**change)
                self.assertTrue(out["status"].startswith("HOLD_"), out)
        self.assertEqual(self.factory.opens, [])

    def test_well_formed_but_wrong_canary_digest_requires_readonly_comparison(self):
        # A valid 64-hex digest cannot be rejected just by offline shape.
        # Its mismatch is established by two SELECT-only staging connections.
        wrong = {**pin(), "canary_sha256": "0" * 64}
        out = self.assess(pin=wrong)
        self.assertEqual(out["status"], "HOLD_PREVIOUS_CANARY_MISSING_OR_CHANGED")
        self.assertEqual(len(self.factory.opens), 2)
        self.assertTrue(all(
            q.strip().upper().startswith("SELECT ") for q in self.factory.queries
        ))
        self.assertEqual(out["staging_writes_performed"], [])

    def test_canary_missing_changed_or_multiple_holds_without_data_write(self):
        with sqlite3.connect(self.dbfile) as db:
            db.execute("UPDATE galaxy_stage9v_canaries SET nonce_sha256=?", ("0"*64,))
        self.assertEqual(self.assess()["status"], "HOLD_PREVIOUS_CANARY_MISSING_OR_CHANGED")
        with sqlite3.connect(self.dbfile) as db:
            db.execute("UPDATE galaxy_stage9v_canaries SET nonce_sha256=?",
                       (CANARY["nonce_sha256"],))
            db.execute(
                "INSERT INTO galaxy_stage9v_canaries VALUES (?,?,?,?)",
                ("EXTRA-CANARY", "1"*64, MARKER, CANARY["created_at"]),
            )
        self.assertEqual(self.assess()["status"], "HOLD_STAGING_PREIMPORT_NOT_EMPTY")

    def test_revoked_or_replaced_marker_stops_after_original_preflight(self):
        with sqlite3.connect(self.dbfile) as db:
            db.execute("UPDATE galaxy_stage9v_staging_identity SET status='REVOKED'")
        out = self.assess()
        self.assertEqual(out["status"], "HOLD_STAGING_IDENTITY_PREFLIGHT")
        self.assertEqual(out["stage9v_preflight_status"],
                         "HOLD_STAGING_IDENTITY_UNVERIFIED")
        self.assertEqual(len(self.factory.opens), 1)

    def test_identity_revoked_between_readonly_connections_holds(self):
        def revoke():
            with sqlite3.connect(self.dbfile) as db:
                db.execute(
                    "UPDATE galaxy_stage9v_staging_identity SET status='REVOKED'"
                )
        self.factory.after_first_close = revoke
        out = self.assess()
        self.assertEqual(out["status"], "HOLD_STAGING_IDENTITY_CHANGED")
        self.assertEqual(len(self.factory.opens), 2)

    def test_unknown_tables_e_lanes_views_and_triggers_hold(self):
        for ddl, undo in (
            ("CREATE TABLE E_LANE_NIMUE (statement TEXT)", "DROP TABLE E_LANE_NIMUE"),
            ("CREATE TABLE memory_gravity (record_id TEXT)",
             "DROP TABLE memory_gravity"),
            ("CREATE VIEW alias AS SELECT record_id FROM memory_records",
             "DROP VIEW alias"),
            ("CREATE TRIGGER hidden BEFORE INSERT ON memory_records "
             "BEGIN SELECT 1; END", "DROP TRIGGER hidden"),
        ):
            with self.subTest(ddl=ddl):
                with sqlite3.connect(self.dbfile) as db:
                    db.execute(ddl)
                self.assertEqual(
                    self.assess()["status"],
                    "HOLD_UNEXPECTED_OR_MISSING_STAGING_OBJECTS",
                )
                with sqlite3.connect(self.dbfile) as db:
                    db.execute(undo)

    def test_column_addition_or_missing_receipt_table_holds(self):
        with sqlite3.connect(self.dbfile) as db:
            db.execute(
                "ALTER TABLE memory_records ADD COLUMN surprise_secret TEXT"
            )
        self.assertEqual(
            self.assess()["status"], "HOLD_CANONICAL_COLUMN_LAYOUT_MISMATCH"
        )
        with sqlite3.connect(self.dbfile) as db:
            db.execute("DROP TABLE galaxy_stage9z_rollbacks")
        self.assertEqual(
            self.assess()["status"], "HOLD_UNEXPECTED_OR_MISSING_STAGING_OBJECTS"
        )

    def test_historical_records_and_import_ledger_must_be_empty_before_import(self):
        with sqlite3.connect(self.dbfile) as db:
            db.execute(
                "INSERT INTO memory_records VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                ("PRIVATE-ID", "NAOMI", "TEST", "MemoryOS", "PRIVATE-STATEMENT",
                 "source", "STAGED_HISTORICAL_HOLD", "1", "now", "now", None, "{}"),
            )
        out = self.assess()
        self.assertEqual(out["status"], "HOLD_STAGING_PREIMPORT_NOT_EMPTY")
        self.assertTrue(out["schema_layout_verified"])
        self.assertTrue(out["pinned_same_database_canary_verified"])
        self.assertNotIn("PRIVATE-STATEMENT", json.dumps(out))
        self.assertNotIn("PRIVATE-ID", json.dumps(out))

    def test_fail_closed_if_second_connection_close_fails(self):
        self.factory.fail_second_close = True
        out = self.assess()
        self.assertEqual(out["status"], "HOLD_STAGING_CONNECTION_CLOSE_FAILED")
        self.assertFalse(out["staging_turso_remotely_observed"])
        self.assertNotIn("PRIVATE-CLOSE-ERROR", json.dumps(out))

    def test_private_cli_requires_flags_and_secure_independent_pin(self):
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / "pinned-stage9x.json"
            file.write_text(json.dumps(pin()), encoding="utf-8")
            file.chmod(0o600)
            args = ["--pinned-canary-json", str(file)]
            sink = io.StringIO()
            with patch.dict(os.environ, {}, clear=True), contextlib.redirect_stdout(sink):
                code = aa.main(args)
            self.assertEqual(code, 2)
            self.assertEqual(
                json.loads(sink.getvalue())["status"],
                "HOLD_EXPLICIT_READ_ONLY_CONFIRMATION_REQUIRED",
            )
            full = args + [
                "--confirm-read-only", "--confirm-independent-canary-pin",
            ]
            env = dict(zip(vr.CONFIG.values(), CONFIG.values()))
            with patch.dict(os.environ, env, clear=True):
                file.chmod(0o644)
                sink = io.StringIO()
                with contextlib.redirect_stdout(sink):
                    code = aa.main(full)
                self.assertEqual(code, 2)
                self.assertEqual(
                    json.loads(sink.getvalue())["status"],
                    "HOLD_PRIVATE_CANARY_PIN_INVALID",
                )
                file.chmod(0o600)
                file.write_text('{"run_id":"first","run_id":"second"}')
                sink = io.StringIO()
                with contextlib.redirect_stdout(sink):
                    code = aa.main(full)
                self.assertEqual(code, 2)
                self.assertEqual(
                    json.loads(sink.getvalue())["status"],
                    "HOLD_PRIVATE_CANARY_PIN_INVALID",
                )

    def test_driver_local_fixture_is_not_remote_proof(self):
        libsql = importlib.import_module("libsql")
        opens = []
        def local_driver(url, token):
            self.assertEqual((url, token), (STAGE, TOKEN))
            opens.append(url)
            return libsql.connect(database=self.dbfile)
        out = self.assess(connector=local_driver)
        self.assertEqual(out["status"], "PASS_LOCAL_READ_ONLY_SCHEMA_FIXTURE", out)
        self.assertFalse(out["staging_turso_remotely_observed"])
        self.assertTrue(out["test_connector_injected"])
        self.assertEqual(len(opens), 2)
        self.assertEqual(out["staging_writes_performed"], [])


if __name__ == "__main__":
    unittest.main()
