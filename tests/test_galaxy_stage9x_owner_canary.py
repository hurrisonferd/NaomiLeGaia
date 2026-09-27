"""Stage 9X source-only safety tests. ALL endpoints and credentials are fixtures."""
from __future__ import annotations

import contextlib
import hashlib
import hmac
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
import galaxy_stage9v_staging_turso as probe
import galaxy_stage9x_owner_canary as operator

STAGING = "libsql://stage9x-isolated-fixture.turso.io"
PRODUCTION = "libsql://stage9x-production-never-open.turso.io"
MARKER = "06d197d8-c314-412d-bd70-1386bc155fed"
TOKEN = "stage9x-fixture-staging-token-NOT-A-REAL-SECRET"
KEY = b"stage9x-ci-key-only-not-a-real-human-approval-key"
RUN = "STAGE9X-FIXTURE-20260927-0001"
NONCE = hashlib.sha256(b"local-synthetic-nonce").hexdigest()
CONFIG = {
    "staging_url": STAGING, "staging_token": TOKEN,
    "production_url": PRODUCTION, "expected_staging_id": MARKER,
}


def signed(*, run=RUN, nonce=NONCE, key=KEY):
    manifest = {
        "schema": probe.APPROVAL_SCHEMA, "authority": "NAOMI",
        "target": probe.TARGET, "action": "WRITE_ONE_STAGING_CANARY",
        "expected_staging_id": MARKER,
        "staging_url_sha256": hashlib.sha256(
            probe._canonical_url(STAGING).encode()
        ).hexdigest(),
        "production_url_sha256": hashlib.sha256(
            probe._canonical_url(PRODUCTION).encode()
        ).hexdigest(),
        "run_id": run, "nonce_sha256": nonce,
    }
    signature = hmac.new(key, probe._bytes(manifest), hashlib.sha256).hexdigest()
    return manifest, signature


class IsolatedConnector:
    def __init__(self, path):
        self.path = path
        self.calls = []
        self.ack_lost_once = False

    def __call__(self, url, token):
        if (url, token) != (STAGING, TOKEN):
            raise AssertionError("PRODUCTION TARGET OR CREDENTIAL USED")
        self.calls.append((url, token))
        conn = sqlite3.connect(self.path)
        if self.ack_lost_once and len(self.calls) == 2:
            self.ack_lost_once = False

            class LostAck:
                def execute(self, *args):
                    return conn.execute(*args)

                def commit(self):
                    conn.commit()
                    raise OSError("PRIVATE ACK FAILURE; NEVER ECHO")

                def rollback(self):
                    conn.rollback()

                def close(self):
                    conn.close()

            # Preflight uses no commit; place this wrapper only on the second
            # connection in the three-connection operator sequence instead.
            if len(self.calls) == 2:
                return LostAck()
        return conn


class OwnerLocalCanaryTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.staging = str(Path(tmp.name) / "staging-fixture.db")
        self.production = str(Path(tmp.name) / "production-fixture.db")
        self.connector = IsolatedConnector(self.staging)
        with sqlite3.connect(self.staging) as c:
            c.executescript("""
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
                INSERT INTO memory_records VALUES ('STAGING','PRESERVE-THIS');
            """)
            c.execute(
                "INSERT INTO galaxy_stage9v_staging_identity VALUES (?,?,?,?,?)",
                (probe.IDENTITY_SCHEMA, "STAGING_ONLY", MARKER, "NAOMI", "ACTIVE"),
            )
        with sqlite3.connect(self.production) as c:
            c.executescript("""
                CREATE TABLE memory_records (
                    record_id TEXT PRIMARY KEY, statement TEXT
                );
                INSERT INTO memory_records VALUES ('PROD','NEVER-TOUCH');
            """)

    def run_operator(self, *, manifest=None, signature=None, key=KEY,
                     config=None, **overrides):
        default_manifest, default_sig = signed()
        kw = {
            "config": config if config is not None else CONFIG,
            "approval": manifest if manifest is not None else default_manifest,
            "signature_hex": signature if signature is not None else default_sig,
            "approval_key": key,
            "confirm_provider_identity": True,
            "confirm_separate_owner_approval": True,
            "confirm_one_canary": True,
            "connector": self.connector,
        }
        kw.update(overrides)
        return operator.execute_owner_local_canary(**kw)

    def state(self):
        with sqlite3.connect(self.staging) as db:
            rows = db.execute(
                "SELECT run_id,nonce_sha256,database_id "
                "FROM galaxy_stage9v_canaries ORDER BY run_id"
            ).fetchall()
            staging = db.execute("SELECT * FROM memory_records").fetchall()
        with sqlite3.connect(self.production) as db:
            production = db.execute("SELECT * FROM memory_records").fetchall()
        return rows, staging, production

    def assert_preserved(self):
        _, staging, production = self.state()
        self.assertEqual(staging, [("STAGING", "PRESERVE-THIS")])
        self.assertEqual(production, [("PROD", "NEVER-TOUCH")])

    def test_signed_fixture_preflights_then_writes_once_then_reopens(self):
        out = self.run_operator()
        self.assertEqual(out["status"], "HOLD_LOCAL_FIXTURE_NOT_REMOTE", out)
        self.assertEqual(out["read_only_preflight_status"],
                         "PASS_STAGING_READINESS_READ_ONLY")
        self.assertEqual(out["stage9v_canary_status"],
                         "PASS_STAGING_CANARY_REOPEN_READBACK")
        self.assertTrue(out["local_hmac_manifest_verified"])
        self.assertFalse(out["staging_turso_reopen_observed"])
        self.assertFalse(out["live_owner_identity_verified"])
        self.assertFalse(out["provider_database_separation_independently_verified"])
        self.assertFalse(out["bigbang_activated"])
        self.assertEqual(out["writes_performed"], ["ONE_SEPARATE_STAGING_CANARY"])
        self.assertEqual(len(self.connector.calls), 3)
        self.assertEqual(self.state()[0], [(RUN, NONCE, MARKER)])
        self.assert_preserved()
        emitted = json.dumps(out)
        for private in (STAGING, PRODUCTION, TOKEN, MARKER, KEY.decode()):
            self.assertNotIn(private, emitted)

    def test_exact_signed_replay_is_read_only(self):
        self.assertEqual(self.run_operator()["status"], "HOLD_LOCAL_FIXTURE_NOT_REMOTE")
        replay = self.run_operator()
        self.assertEqual(replay["status"], "HOLD_LOCAL_FIXTURE_NOT_REMOTE")
        self.assertTrue(replay["idempotent_replay"])
        self.assertEqual(replay["writes_performed"], [])
        self.assertEqual(len(self.connector.calls), 6)
        self.assertEqual(len(self.state()[0]), 1)
        self.assert_preserved()

    def test_confirmation_is_not_inferred_from_hmac_or_manifest(self):
        for key in ("confirm_provider_identity", "confirm_separate_owner_approval",
                    "confirm_one_canary"):
            with self.subTest(flag=key):
                kwargs = {key: False}
                out = self.run_operator(**kwargs)
                self.assertEqual(
                    out["status"], "HOLD_EXPLICIT_OPERATOR_CONFIRMATIONS_REQUIRED"
                )
        self.assertEqual(self.connector.calls, [])
        self.assertEqual(self.state()[0], [])
        self.assert_preserved()

    def test_bad_signature_action_nonce_and_alias_hold_before_connection(self):
        manifest, sig = signed()
        for changed, new_sig, conf in (
            ({**manifest, "action": "WRITE_PRODUCTION"}, sig, CONFIG),
            ({**manifest, "nonce_sha256": "0" * 64}, sig, CONFIG),
            ({**manifest, "authority": "ANYONE"}, sig, CONFIG),
            (manifest, "0" * 64, CONFIG),
            (manifest, sig, {**CONFIG, "production_url": STAGING}),
            (manifest, sig, {**CONFIG, "staging_token": ""}),
            (manifest, sig, {**CONFIG, "expected_staging_id": "wrong"}),
        ):
            with self.subTest(changed=changed, config=conf):
                out = self.run_operator(
                    manifest=changed, signature=new_sig, config=conf
                )
                self.assertEqual(out["status"],
                                 "HOLD_SIGNED_EXACT_STAGING_ACTION_REQUIRED")
        self.assertEqual(self.connector.calls, [])
        self.assertEqual(self.state()[0], [])

    def test_revoked_or_missing_marker_fails_read_only_before_canary(self):
        with sqlite3.connect(self.staging) as db:
            db.execute("UPDATE galaxy_stage9v_staging_identity SET status='REVOKED'")
        out = self.run_operator()
        self.assertEqual(out["status"], "HOLD_READ_ONLY_PREFLIGHT_NOT_PASSED")
        self.assertEqual(out["read_only_preflight_status"],
                         "HOLD_STAGING_IDENTITY_UNVERIFIED")
        self.assertEqual(len(self.connector.calls), 1)
        self.assertEqual(self.state()[0], [])
        self.assert_preserved()

    def test_existing_run_with_different_signed_nonce_never_overwrites(self):
        self.run_operator()
        other, signature = signed(nonce="0" * 64)
        out = self.run_operator(manifest=other, signature=signature)
        self.assertEqual(out["status"], "HOLD_CANARY_NOT_VERIFIED")
        self.assertEqual(out["stage9v_canary_status"],
                         "HOLD_STAGING_RUN_ID_CONFLICT")
        self.assertEqual(self.state()[0], [(RUN, NONCE, MARKER)])
        self.assert_preserved()

    def test_commit_ack_failure_is_ambiguous_and_exact_replay_recovers(self):
        self.connector.ack_lost_once = True
        first = self.run_operator()
        self.assertEqual(first["status"], "HOLD_CANARY_NOT_VERIFIED")
        self.assertTrue(first["staging_write_outcome_unknown"])
        self.assertEqual(first["writes_performed"],
                         ["STAGING_CANARY_WRITE_OUTCOME_UNVERIFIED"])
        self.assertNotIn("PRIVATE ACK FAILURE", json.dumps(first))
        self.assertEqual(self.state()[0], [(RUN, NONCE, MARKER)])
        second = self.run_operator()
        self.assertEqual(second["status"], "HOLD_LOCAL_FIXTURE_NOT_REMOTE")
        self.assertTrue(second["idempotent_replay"])
        self.assertEqual(second["writes_performed"], [])
        self.assert_preserved()

    def test_no_production_or_member_side_effect_imports(self):
        import sys as loaded
        self.assertNotIn("memcon_runtime", loaded.modules)
        self.assertNotIn("gaiaos_memory_gateway", loaded.modules)
        self.assert_preserved()


class PrivateCliTests(unittest.TestCase):
    def test_flags_gate_before_environment_or_private_file_access(self):
        stdout = io.StringIO()
        with patch.dict(os.environ, {}, clear=True), contextlib.redirect_stdout(stdout):
            code = operator.main([
                "--approval-json", "/does/not/exist.json",
                "--signature-file", "/does/not/exist.sig",
                "--key-file", "/does/not/exist.key",
            ])
        self.assertEqual(code, 2)
        self.assertEqual(
            json.loads(stdout.getvalue())["status"],
            "HOLD_EXPLICIT_OPERATOR_CONFIRMATIONS_REQUIRED",
        )

    def test_private_file_rejects_mode_symlink_and_bad_inputs(self):
        with tempfile.TemporaryDirectory() as folder:
            good = Path(folder) / "private.json"
            good.write_text("{}", encoding="utf-8")
            good.chmod(0o600)
            self.assertEqual(operator._private_file(str(good), 32), b"{}")
            good.chmod(0o644)
            with self.assertRaises(ValueError):
                operator._private_file(str(good), 32)
            good.chmod(0o600)
            link = Path(folder) / "symlink.json"
            link.symlink_to(good)
            with self.assertRaises(ValueError):
                operator._private_file(str(link), 32)

    def test_duplicate_json_manifest_refused_without_connection(self):
        with tempfile.TemporaryDirectory() as folder:
            paths = [Path(folder) / n for n in ("manifest.json", "sig", "key")]
            for path, raw in zip(paths, (
                b'{"run_id":"a","run_id":"b"}',
                b"0" * 64,
                b"k" * 40,
            )):
                path.write_bytes(raw)
                path.chmod(0o600)
            env = dict(zip(operator.CONFIG.values(), CONFIG.values()))
            stdout = io.StringIO()
            with patch.dict(os.environ, env, clear=True), \
                    contextlib.redirect_stdout(stdout):
                code = operator.main([
                    "--approval-json", str(paths[0]),
                    "--signature-file", str(paths[1]),
                    "--key-file", str(paths[2]),
                    "--confirm-provider-identity",
                    "--confirm-separate-owner-approval",
                    "--confirm-one-staging-canary",
                ])
            self.assertEqual(code, 2)
            self.assertEqual(json.loads(stdout.getvalue())["status"],
                             "HOLD_PRIVATE_SIGNED_INPUT_INVALID")
            self.assertNotIn(TOKEN, stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
