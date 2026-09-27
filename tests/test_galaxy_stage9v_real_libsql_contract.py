"""Stage 9V contract test using the actual libsql driver, without a remote DB.

This exercises cursor mapping, BEGIN IMMEDIATE, commit/close and fresh-connection
readback through the *real driver*. It uses a local temporary libSQL database
with an INJECTED connector, and MUST NOT claim a real Turso staging PASS.
"""
from __future__ import annotations

import hashlib
import hmac
import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))
import galaxy_stage9v_staging_turso as probe

STAGING_URL = "libsql://galaxy-stage9v-contract-test.turso.io"
PROD_URL = "libsql://gaiaos-production-placeholder.turso.io"
STAGING_ID = "8744d4f4-cea2-4d42-8b68-3f6cd349912a"
RUN_ID = "STAGE9V-LIBSQL-CONTRACT-20260927"
NONCE_HASH = hashlib.sha256(b"driver-contract-test-nonce").hexdigest()
TOKEN = "staging-only-fixture-token-never-authorizes-remote"
KEY = b"driver-contract-fixture-key-not-the-owner-signing-key"


def approved_packet(run_id=RUN_ID, nonce_hash=NONCE_HASH):
    manifest = {
        "schema": probe.APPROVAL_SCHEMA,
        "authority": "NAOMI",
        "target": probe.TARGET,
        "action": "WRITE_ONE_STAGING_CANARY",
        "expected_staging_id": STAGING_ID,
        "staging_url_sha256": probe._sha(probe._canonical_url(STAGING_URL).encode()),
        "production_url_sha256": probe._sha(probe._canonical_url(PROD_URL).encode()),
        "run_id": run_id,
        "nonce_sha256": nonce_hash,
    }
    return {
        "staging_url": STAGING_URL,
        "production_url": PROD_URL,
        "staging_token": TOKEN,
        "expected_staging_id": STAGING_ID,
        "run_id": run_id,
        "nonce_sha256": nonce_hash,
        "approval": manifest,
        "signature_hex": hmac.new(KEY, probe._bytes(manifest), hashlib.sha256).hexdigest(),
        "approval_key": KEY,
    }


class RealLocalLibsqlContractTests(unittest.TestCase):
    def setUp(self):
        # CI explicitly installs libsql. An import failure FAILS, not skips, this gate.
        self.libsql = importlib.import_module("libsql")
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.staging_path = str(Path(tmp.name) / "verified-staging-fixture.db")
        self.production_path = str(Path(tmp.name) / "untouched-production-fixture.db")
        self.connection_count = 0
        with self.libsql.connect(database=self.staging_path) as conn:
            conn.execute(
                "CREATE TABLE galaxy_stage9v_staging_identity "
                "(schema TEXT, environment TEXT, database_id TEXT, authority TEXT, status TEXT)"
            )
            conn.execute(
                "INSERT INTO galaxy_stage9v_staging_identity VALUES (?,?,?,?,?)",
                (probe.IDENTITY_SCHEMA, "STAGING_ONLY", STAGING_ID, "NAOMI", "ACTIVE"),
            )
            conn.execute(
                "CREATE TABLE galaxy_stage9v_canaries "
                "(run_id TEXT PRIMARY KEY,nonce_sha256 TEXT,"
                "database_id TEXT,created_at TEXT)"
            )
            conn.execute(
                "CREATE TABLE memory_records "
                "(record_id TEXT PRIMARY KEY,statement TEXT NOT NULL)"
            )
            conn.execute(
                "INSERT INTO memory_records VALUES (?,?)",
                ("STAGING-SENTINEL", "MUST-REMAIN-UNTOUCHED"),
            )
            conn.commit()
        with self.libsql.connect(database=self.production_path) as conn:
            conn.execute(
                "CREATE TABLE memory_records "
                "(record_id TEXT PRIMARY KEY,statement TEXT NOT NULL)"
            )
            conn.execute(
                "INSERT INTO memory_records VALUES (?,?)",
                ("PRODUCTION-SENTINEL", "MUST-REMAIN-UNTOUCHED"),
            )
            conn.commit()

    def local_driver_connector(self, url, token):
        if url != STAGING_URL or token != TOKEN:
            raise AssertionError("attempt to use unapproved database or credential")
        self.connection_count += 1
        return self.libsql.connect(database=self.staging_path)

    def probe(self, packet=None):
        return probe.prove_staging_turso_canary(
            **(packet or approved_packet()), connector=self.local_driver_connector,
        )

    def assert_sentinels(self):
        with self.libsql.connect(database=self.staging_path) as staging:
            self.assertEqual(staging.execute(
                "SELECT record_id,statement FROM memory_records"
            ).fetchall(), [("STAGING-SENTINEL", "MUST-REMAIN-UNTOUCHED")])
        with self.libsql.connect(database=self.production_path) as production:
            self.assertEqual(production.execute(
                "SELECT record_id,statement FROM memory_records"
            ).fetchall(), [("PRODUCTION-SENTINEL", "MUST-REMAIN-UNTOUCHED")])

    def test_real_local_libsql_commit_close_and_fresh_connection_readback(self):
        result = self.probe()
        self.assertEqual(result["status"], "PASS_STAGING_CANARY_REOPEN_READBACK", result)
        self.assertEqual(self.connection_count, 2)
        self.assertFalse(result["staging_turso_verified"])
        self.assertTrue(result["test_connector_injected"])
        self.assertTrue(result["reopen_readback_verified"])
        self.assertEqual(result["writes_performed"], ["ONE_SEPARATE_STAGING_CANARY"])
        with self.libsql.connect(database=self.staging_path) as fresh:
            row = fresh.execute(
                "SELECT run_id,nonce_sha256,database_id FROM galaxy_stage9v_canaries"
            ).fetchall()
        self.assertEqual(row, [(RUN_ID, NONCE_HASH, STAGING_ID)])
        self.assert_sentinels()

    def test_real_local_libsql_exact_replay_is_read_only(self):
        first = self.probe()
        self.assertEqual(first["status"], "PASS_STAGING_CANARY_REOPEN_READBACK", first)
        second = self.probe()
        self.assertEqual(second["status"], "PASS_STAGING_CANARY_REOPEN_READBACK", second)
        self.assertTrue(second["idempotent"])
        self.assertEqual(second["writes_performed"], [])
        self.assertEqual(first["canary_sha256"], second["canary_sha256"])
        self.assertEqual(self.connection_count, 4)
        self.assert_sentinels()

    def test_real_local_libsql_conflicting_nonce_never_overwrites(self):
        self.assertEqual(self.probe()["status"], "PASS_STAGING_CANARY_REOPEN_READBACK")
        conflict = self.probe(approved_packet(nonce_hash="0" * 64))
        self.assertEqual(conflict["status"], "HOLD_STAGING_RUN_ID_CONFLICT")
        with self.libsql.connect(database=self.staging_path) as check:
            nonce = check.execute(
                "SELECT nonce_sha256 FROM galaxy_stage9v_canaries WHERE run_id=?",
                (RUN_ID,),
            ).fetchone()[0]
        self.assertEqual(nonce, NONCE_HASH)
        self.assert_sentinels()

    def test_real_local_libsql_identity_revocation_holds_without_write(self):
        with self.libsql.connect(database=self.staging_path) as conn:
            conn.execute(
                "UPDATE galaxy_stage9v_staging_identity SET status='REVOKED'"
            )
            conn.commit()
        result = self.probe()
        self.assertEqual(result["status"], "HOLD_STAGING_IDENTITY_NOT_VERIFIED")
        self.assertEqual(self.connection_count, 1)
        with self.libsql.connect(database=self.staging_path) as check:
            count = check.execute(
                "SELECT COUNT(*) FROM galaxy_stage9v_canaries"
            ).fetchone()[0]
        self.assertEqual(count, 0)
        self.assert_sentinels()

    def test_remote_driver_call_signature_is_explicit(self):
        sentinel = object()
        with patch.object(self.libsql, "connect", return_value=sentinel) as call:
            result = probe._connect_live(STAGING_URL, TOKEN)
        self.assertIs(result, sentinel)
        call.assert_called_once_with(database=STAGING_URL, auth_token=TOKEN)


if __name__ == "__main__":
    unittest.main()
