"""Stage 9AA private SQL generator: zero DB access until manual fixture test."""
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))
import galaxy_stage9aa_local_schema_bundle as bundle
import galaxy_stage9aa_preimport_readonly as aa
import galaxy_stage9v_setup_bundle as vsetup
import galaxy_stage9v_staging_turso as v

MARKER = "1c6c5644-4752-408f-8500-2cdb1d81a353"


class OwnerLocalSchemaBundleTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.root.chmod(0o700)
        self.out = self.root / "owner-private-schema"
        self.label = "gaiaos-galaxy-stage9v"

    def make(self, **changes):
        args = {
            "destination": self.out, "staging_name_label": self.label,
        }
        args.update(changes)
        return bundle.create_bundle(**args)

    def test_only_two_new_private_files_and_no_remote_or_git_effect(self):
        result = self.make()
        self.assertEqual(result["status"], "PASS_LOCAL_SCHEMA_BUNDLE_CREATED", result)
        self.assertEqual(sorted(p.name for p in self.out.iterdir()),
                         sorted((bundle.SQL_NAME, bundle.MANIFEST_NAME)))
        self.assertEqual(self.out.stat().st_mode & 0o777, 0o700)
        for file in self.out.iterdir():
            self.assertEqual(file.stat().st_mode & 0o777, 0o600)
        self.assertEqual(result["database_connections"], 0)
        self.assertFalse(result["production_accessed"])
        self.assertFalse(result["remote_staging_accessed"])
        self.assertFalse(result["credentials_used"])
        self.assertFalse(result["git_updated"])
        source = (self.out / bundle.SQL_NAME).read_bytes()
        manifest = json.loads((self.out / bundle.MANIFEST_NAME).read_text())
        self.assertEqual(manifest["source_sql_sha256"],
                         hashlib.sha256(source).hexdigest())
        self.assertEqual(manifest["source_sql_sha256"], result["sql_sha256"])
        self.assertEqual(
            manifest["expected_layout_sha256"],
            aa._sha(v._bytes(aa.EXPECTED_TABLES)),
        )
        self.assertFalse(manifest["live_staging_provisioned"])
        self.assertFalse(manifest["tokens_included"])
        self.assertEqual(source.decode().count("CREATE TABLE "), 4)
        self.assertNotIn("TURSO_AUTH_TOKEN", source.decode())
        self.assertNotIn("PRIVATE_TOKEN", json.dumps(manifest))
        self.assertNotIn(str(self.root), json.dumps(result))

    def test_stage9v_plus_generated_sql_matches_exact_six_table_layout(self):
        result = self.make()
        self.assertEqual(result["status"], "PASS_LOCAL_SCHEMA_BUNDLE_CREATED")
        sql = (self.out / bundle.SQL_NAME).read_text()
        with sqlite3.connect(":memory:") as db:
            db.executescript(vsetup.make_sql(MARKER))
            db.executescript(sql)
            names = {
                row[0] for row in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            self.assertEqual(names, set(aa.EXPECTED_TABLES))
            for table, expected in aa.EXPECTED_TABLES.items():
                cursor = db.execute(f"SELECT * FROM {table} LIMIT 0")
                self.assertEqual(
                    tuple(c[0] for c in cursor.description),
                    expected,
                    table,
                )
            self.assertEqual(db.execute(
                "SELECT schema,environment,database_id,authority,status "
                "FROM galaxy_stage9v_staging_identity"
            ).fetchone(), (v.IDENTITY_SCHEMA, "STAGING_ONLY", MARKER,
                           "NAOMI", "ACTIVE"))
            self.assertEqual(db.execute(
                "SELECT COUNT(*) FROM memory_records"
            ).fetchone()[0], 0)

    def test_refuses_existing_dir_symlink_non_private_parent_and_repo(self):
        self.assertEqual(self.make()["status"], "PASS_LOCAL_SCHEMA_BUNDLE_CREATED")
        self.assertEqual(
            self.make()["status"],
            "HOLD_PRIVATE_NEW_DIRECTORY_REQUIRED_OUTSIDE_REPO",
        )
        linked = self.root / "owner-symlink"
        linked.symlink_to(self.out)
        self.assertEqual(
            self.make(destination=linked)["status"], "HOLD_SYMLINK_OUTPUT_FORBIDDEN"
        )
        self.root.chmod(0o755)
        self.assertEqual(
            self.make(destination=self.root / "unsafe-parent-new")["status"],
            "HOLD_PARENT_DIRECTORY_MUST_BE_OWNER_ONLY",
        )
        self.assertEqual(
            self.make(destination=ROOT / "tests" / "never-created-secret")["status"],
            "HOLD_PRIVATE_NEW_DIRECTORY_REQUIRED_OUTSIDE_REPO",
        )

    def test_rejects_invalid_name_or_unapproved_cli_invocation(self):
        self.assertEqual(
            self.make(staging_name_label="DROP TABLE prod;")["status"],
            "HOLD_INVALID_PRIVATE_BUNDLE_ARGUMENTS",
        )
        sink = io.StringIO()
        with contextlib.redirect_stdout(sink):
            code = bundle.main([
                "--destination", str(self.out),
                "--staging-name-label", self.label,
            ])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(sink.getvalue())["status"],
                         "HOLD_EXPLICIT_LOCAL_ONLY_FLAG_REQUIRED")
        self.assertFalse(self.out.exists())
        sink = io.StringIO()
        with contextlib.redirect_stdout(sink):
            code = bundle.main([
                "--destination", str(self.out),
                "--staging-name-label", self.label,
                "--confirm-local-file-only",
            ])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(sink.getvalue())["status"],
                         "PASS_LOCAL_SCHEMA_BUNDLE_CREATED")


if __name__ == "__main__":
    unittest.main()
