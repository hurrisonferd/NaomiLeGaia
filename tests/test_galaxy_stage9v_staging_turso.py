"""Stage 9V: separately identified staging-DB canary; never production memory."""
from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))
import galaxy_stage9v_staging_turso as probe

STAGING = "libsql://gaia-galaxy-isolated-staging.turso.io"
PRODUCTION = "libsql://gaia-galaxy-original-prod.turso.io"
STAGING_ID = "a7dce73b-b313-4d70-9354-9d7c78b8240f"
TOKEN = "separate-stage9v-staging-fixture-token-not-live"
KEY = b"isolated-stage9v-fixture-signing-key-not-a-live-owner-key"
RUN = "STAGE9V-CANARY-20260927-001"
NONCE = hashlib.sha256(b"isolated-staging-only-fixture-nonce").hexdigest()


def signed(run=RUN, nonce=NONCE):
    body = {
        "schema": probe.APPROVAL_SCHEMA, "authority": "NAOMI",
        "target": probe.TARGET, "action": "WRITE_ONE_STAGING_CANARY",
        "expected_staging_id": STAGING_ID,
        "staging_url_sha256": probe._sha(probe._canonical_url(STAGING).encode()),
        "production_url_sha256": probe._sha(probe._canonical_url(PRODUCTION).encode()),
        "run_id": run, "nonce_sha256": nonce,
    }
    return {
        "staging_url": STAGING, "staging_token": TOKEN,
        "production_url": PRODUCTION, "expected_staging_id": STAGING_ID,
        "run_id": run, "nonce_sha256": nonce, "approval": body,
        "signature_hex": hmac.new(KEY, probe._bytes(body), hashlib.sha256).hexdigest(),
        "approval_key": KEY,
    }


class FakeSeparateTurso:
    def __init__(self, staging_file: str, production_file: str):
        self.staging_file = staging_file
        self.production_file = production_file
        self.opens = []
        self.fail_on_reopen = False
        self.corrupt_reopen_identity = False
        self.uncertain_commit = False

    def __call__(self, url, token):
        self.opens.append((url, token))
        if url != STAGING or token != TOKEN:
            raise AssertionError("PRODUCTION OR UNEXPECTED DB CONNECTION ATTEMPT")
        if self.fail_on_reopen and len(self.opens) > 1:
            raise OSError("PRIVATE_STAGING_READBACK_CONNECTION_DETAIL")
        if self.corrupt_reopen_identity and len(self.opens) > 1:
            with sqlite3.connect(self.staging_file) as m:
                m.execute("UPDATE galaxy_stage9v_staging_identity SET status='REVOKED'")
        conn = sqlite3.connect(self.staging_file)
        if self.uncertain_commit:
            self.uncertain_commit = False
            class AckLost:
                def execute(self, *args):
                    return conn.execute(*args)
                def commit(self):
                    conn.commit()
                    raise OSError("PRIVATE_COMMIT_ACK_LOST")
                def rollback(self):
                    return conn.rollback()
                def close(self):
                    return conn.close()
            return AckLost()
        return conn


class Stage9VStagingProbeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.stage_file = str(Path(temp.name) / "separate_stage.db")
        self.prod_file = str(Path(temp.name) / "production.db")
        self.factory = FakeSeparateTurso(self.stage_file, self.prod_file)
        with sqlite3.connect(self.stage_file) as conn:
            conn.executescript("""
                CREATE TABLE galaxy_stage9v_staging_identity (
                    schema TEXT NOT NULL, environment TEXT NOT NULL,
                    database_id TEXT NOT NULL, authority TEXT NOT NULL,
                    status TEXT NOT NULL
                );
                CREATE TABLE galaxy_stage9v_canaries (
                    run_id TEXT PRIMARY KEY, nonce_sha256 TEXT NOT NULL,
                    database_id TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE memory_records (
                    record_id TEXT PRIMARY KEY, statement TEXT NOT NULL
                );
                INSERT INTO memory_records VALUES
                    ('SENTINEL-STAGING','DO-NOT-ALTER-STAGING-MEMORY');
            """)
            conn.execute(
                "INSERT INTO galaxy_stage9v_staging_identity VALUES (?,?,?,?,?)",
                (probe.IDENTITY_SCHEMA, "STAGING_ONLY", STAGING_ID, "NAOMI", "ACTIVE"),
            )
        with sqlite3.connect(self.prod_file) as conn:
            conn.executescript("""
                CREATE TABLE memory_records (
                    record_id TEXT PRIMARY KEY, statement TEXT NOT NULL
                );
                INSERT INTO memory_records VALUES
                    ('SENTINEL-PRODUCTION','DO-NOT-ALTER-PRODUCTION-MEMORY');
            """)

    def run_probe(self, payload=None, factory=None):
        args = payload if payload is not None else signed()
        return probe.prove_staging_turso_canary(
            **args, connector=factory if factory is not None else self.factory,
        )

    def stage_rows(self):
        with sqlite3.connect(self.stage_file) as conn:
            return conn.execute(
                "SELECT run_id,nonce_sha256,database_id,created_at "
                "FROM galaxy_stage9v_canaries ORDER BY run_id",
            ).fetchall()

    def assert_originals_unchanged(self):
        with sqlite3.connect(self.stage_file) as staging:
            self.assertEqual(
                staging.execute("SELECT * FROM memory_records").fetchall(),
                [("SENTINEL-STAGING", "DO-NOT-ALTER-STAGING-MEMORY")],
            )
        with sqlite3.connect(self.prod_file) as prod:
            self.assertEqual(
                prod.execute("SELECT * FROM memory_records").fetchall(),
                [("SENTINEL-PRODUCTION", "DO-NOT-ALTER-PRODUCTION-MEMORY")],
            )

    def test_one_canary_commits_and_reopens_exact_staging_target(self):
        out = self.run_probe()
        self.assertEqual(out["status"], "PASS_STAGING_CANARY_REOPEN_READBACK", out)
        self.assertFalse(out["staging_turso_verified"])  # Injected SQLite is NOT real Turso.
        self.assertTrue(out["test_connector_injected"])
        self.assertTrue(out["reopen_readback_verified"])
        self.assertEqual(out["writes_performed"], ["ONE_SEPARATE_STAGING_CANARY"])
        self.assertFalse(out["schema_changes"])
        self.assertFalse(out["production_memory_records_modified"])
        self.assertFalse(out["production_gravity_modified"])
        self.assertFalse(out["bigbang_activated"])
        self.assertFalse(out["mode_control_modified"])
        self.assertFalse(out["live_owner_identity_verified"])
        self.assertEqual(len(self.stage_rows()), 1)
        self.assertEqual(len(self.factory.opens), 2)
        self.assertEqual(self.factory.opens, [(STAGING, TOKEN), (STAGING, TOKEN)])
        self.assert_originals_unchanged()

    def test_repeat_exact_run_is_idempotent_and_reopens(self):
        first = self.run_probe()
        second = self.run_probe()
        self.assertEqual(first["status"], "PASS_STAGING_CANARY_REOPEN_READBACK")
        self.assertEqual(second["status"], "PASS_STAGING_CANARY_REOPEN_READBACK")
        self.assertTrue(second["idempotent"])
        self.assertEqual(second["writes_performed"], [])
        self.assertEqual(first["canary_sha256"], second["canary_sha256"])
        self.assertEqual(len(self.stage_rows()), 1)
        self.assertEqual(len(self.factory.opens), 4)
        self.assert_originals_unchanged()

    def test_same_run_different_nonce_is_not_overwritten(self):
        self.assertEqual(self.run_probe()["status"], "PASS_STAGING_CANARY_REOPEN_READBACK")
        other = signed(nonce="0" * 64)
        result = self.run_probe(other)
        self.assertEqual(result["status"], "HOLD_STAGING_RUN_ID_CONFLICT")
        self.assertEqual(len(self.stage_rows()), 1)
        self.assertEqual(self.stage_rows()[0][1], NONCE)

    def test_different_run_id_is_separately_recorded(self):
        self.run_probe()
        result = self.run_probe(signed(run="STAGE9V-CANARY-20260927-002"))
        self.assertEqual(result["status"], "PASS_STAGING_CANARY_REOPEN_READBACK")
        self.assertEqual(len(self.stage_rows()), 2)

    def test_wrong_identity_and_wrong_environment_fail_before_any_write(self):
        for field, value in (
            ("database_id", "00000000-0000-4000-8000-000000000000"),
            ("environment", "PRODUCTION"),
            ("authority", "OTHER"),
            ("status", "REVOKED"),
            ("schema", "WRONG"),
        ):
            with self.subTest(field=field):
                with sqlite3.connect(self.stage_file) as conn:
                    conn.execute(
                        f"UPDATE galaxy_stage9v_staging_identity SET {field}=?",
                        (value,),
                    )
                result = self.run_probe()
                self.assertEqual(result["status"], "HOLD_STAGING_IDENTITY_NOT_VERIFIED")
                self.assertEqual(self.stage_rows(), [])
                with sqlite3.connect(self.stage_file) as conn:
                    conn.execute(
                        "UPDATE galaxy_stage9v_staging_identity "
                        "SET schema=?,environment=?,database_id=?,authority=?,status=?",
                        (probe.IDENTITY_SCHEMA, "STAGING_ONLY", STAGING_ID, "NAOMI", "ACTIVE"),
                    )
        self.assert_originals_unchanged()

    def test_duplicate_identity_rows_fail_closed(self):
        with sqlite3.connect(self.stage_file) as conn:
            conn.execute(
                "INSERT INTO galaxy_stage9v_staging_identity VALUES (?,?,?,?,?)",
                (probe.IDENTITY_SCHEMA, "STAGING_ONLY", STAGING_ID, "NAOMI", "ACTIVE"),
            )
        result = self.run_probe()
        self.assertEqual(result["status"], "HOLD_STAGING_IDENTITY_NOT_VERIFIED")
        self.assertEqual(self.stage_rows(), [])

    def test_missing_preprovisioned_tables_fail_before_writes(self):
        with sqlite3.connect(self.stage_file) as conn:
            conn.execute("DROP TABLE galaxy_stage9v_canaries")
        result = self.run_probe()
        self.assertEqual(result["status"], "HOLD_STAGING_CONNECT_OR_WRITE_FAILED")
        with sqlite3.connect(self.stage_file) as conn:
            self.assertIsNone(conn.execute(
                "SELECT name FROM sqlite_master WHERE name='galaxy_stage9v_canaries'",
            ).fetchone())
        self.assert_originals_unchanged()

    def test_invalid_separation_urls_fail_before_connect(self):
        originals = signed()
        mutations = [
            ("staging_url", PRODUCTION),
            ("staging_url", "file:/tmp/production.db"),
            ("staging_url", "libsql://user:pw@fake.turso.io"),
            ("staging_url", "libsql://bad.turso.io/path"),
            ("staging_url", "https://fake.turso.io?secret=1"),
            ("staging_url", "libsql://staging.turso.io:8080"),
            ("production_url", ""),
            ("production_url", STAGING),
        ]
        for field, value in mutations:
            with self.subTest(field=field, value=value):
                packet = {**originals, field: value}
                result = self.run_probe(packet)
                self.assertEqual(
                    result["status"], "HOLD_STAGING_URL_NOT_SEPARATE_FROM_PRODUCTION",
                )
        self.assertEqual(self.factory.opens, [])
        self.assert_originals_unchanged()

    def test_missing_separate_staging_token_or_invalid_id_fails_before_connect(self):
        for field, value, status in [
            ("staging_token", "", "HOLD_SEPARATE_STAGING_CREDENTIALS_MISSING"),
            ("expected_staging_id", "00000000-0000-1000-8000-000000000000",
             "HOLD_STAGING_ID_INVALID"),
            ("run_id", "bad", "HOLD_RUN_ID_INVALID"),
            ("nonce_sha256", "xyz", "HOLD_NONCE_DIGEST_INVALID"),
        ]:
            with self.subTest(field=field):
                args = {**signed(), field: value}
                self.assertEqual(self.run_probe(args)["status"], status)
        self.assertEqual(self.factory.opens, [])

    def test_forged_signature_owner_target_or_url_pin_stays_disconnected(self):
        cases = []
        bad_sig = signed()
        bad_sig["signature_hex"] = "0" * 64
        cases.append(bad_sig)
        bad_owner = signed()
        bad_owner["approval"] = {**bad_owner["approval"], "authority": "OTHER"}
        cases.append(bad_owner)
        wrong_target = signed()
        wrong_target["approval"] = {**wrong_target["approval"], "target": "PRODUCTION"}
        cases.append(wrong_target)
        wrong_pin = signed()
        wrong_pin["approval"] = {**wrong_pin["approval"], "staging_url_sha256": "0" * 64}
        cases.append(wrong_pin)
        short_key = signed()
        short_key["approval_key"] = b"too-short"
        cases.append(short_key)
        for args in cases:
            self.assertEqual(
                self.run_probe(args)["status"],
                "HOLD_OWNER_SIGNED_STAGING_APPROVAL_REQUIRED",
            )
        self.assertEqual(self.factory.opens, [])
        self.assert_originals_unchanged()

    def test_reopen_failure_discloses_committed_but_unverified_outcome(self):
        self.factory.fail_on_reopen = True
        out = self.run_probe()
        self.assertEqual(out["status"], "HOLD_STAGING_REOPEN_READBACK_UNAVAILABLE")
        self.assertEqual(out["error_type"], "OSError")
        self.assertEqual(
            out["writes_performed"], ["STAGING_CANARY_WRITE_OUTCOME_UNVERIFIED"],
        )
        self.assertEqual(len(self.stage_rows()), 1)
        self.assertNotIn("PRIVATE_STAGING_READBACK_CONNECTION_DETAIL", json.dumps(out))
        self.assert_originals_unchanged()
        self.factory.fail_on_reopen = False
        retry = self.run_probe()
        self.assertEqual(retry["status"], "PASS_STAGING_CANARY_REOPEN_READBACK")
        self.assertTrue(retry["idempotent"])

    def test_commit_acknowledgment_lost_reports_indeterminate_write(self):
        self.factory.uncertain_commit = True
        out = self.run_probe()
        self.assertEqual(out["status"], "HOLD_STAGING_CONNECT_OR_WRITE_FAILED")
        self.assertEqual(out["writes_performed"], ["STAGING_CANARY_WRITE_OUTCOME_UNVERIFIED"])
        self.assertNotIn("PRIVATE_COMMIT_ACK_LOST", json.dumps(out))
        self.assertEqual(len(self.stage_rows()), 1)
        again = self.run_probe()
        self.assertEqual(again["status"], "PASS_STAGING_CANARY_REOPEN_READBACK")
        self.assertTrue(again["idempotent"])

    def test_reopened_identity_change_blocks_claim_of_durability(self):
        self.factory.corrupt_reopen_identity = True
        result = self.run_probe()
        self.assertEqual(result["status"], "HOLD_REOPENED_STAGING_IDENTITY_CHANGED")
        self.assertEqual(result["writes_performed"],
                         ["STAGING_CANARY_WRITE_OUTCOME_UNVERIFIED"])
        self.assertEqual(len(self.stage_rows()), 1)

    def test_simulated_failed_insertion_does_not_create_canary(self):
        with sqlite3.connect(self.stage_file) as conn:
            conn.executescript("""
                CREATE TRIGGER deny_canary_insert BEFORE INSERT
                ON galaxy_stage9v_canaries BEGIN
                SELECT RAISE(ABORT, 'PRIVATE-STAGING-TRIGGER-ERROR');
                END;
            """)
        out = self.run_probe()
        self.assertEqual(out["status"], "HOLD_STAGING_CONNECT_OR_WRITE_FAILED")
        self.assertEqual(out["error_type"], "IntegrityError")
        self.assertEqual(self.stage_rows(), [])
        self.assertNotIn("PRIVATE-STAGING-TRIGGER-ERROR", json.dumps(out))

    def test_result_does_not_echo_separate_token_or_database_urls(self):
        out = self.run_probe()
        text = json.dumps(out)
        for secret in (TOKEN, KEY.decode(), STAGING, PRODUCTION):
            self.assertNotIn(secret, text)
        self.assertIn("staging_identity_sha256", text)
        self.assertIn("canary_sha256", text)


if __name__ == "__main__":
    unittest.main()
