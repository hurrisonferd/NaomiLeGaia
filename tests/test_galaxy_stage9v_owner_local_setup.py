"""Stage 9V: owner-local setup must not access Turso or original repository."""
from __future__ import annotations

import contextlib
import io
import json
import os
import sqlite3
import stat
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))
import galaxy_stage9v_setup_bundle as setup
import galaxy_stage9v_staging_turso as probe


class Stage9VOwnerLocalBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dest = Path(self.temp.name) / "owner-only-stage9v"
        self.name = "gaiaos-galaxy-isolated-stage9v"

    def generate(self, **changes):
        args = {"destination": self.dest, "database_name": self.name}
        args.update(changes)
        return setup.create_bundle(**args)

    def test_sql_bundle_is_valid_local_sql_and_no_remote_effect(self):
        with patch.object(probe, "_connect_live",
                          side_effect=AssertionError("REMOTE DB MUST NEVER CONNECT")):
            report = self.generate()
        self.assertEqual(report["status"], "PASS_OWNER_LOCAL_BUNDLE_CREATED", report)
        self.assertEqual(report["writes_performed"],
                         ["NEW_PRIVATE_LOCAL_SQL_FILE", "NEW_PRIVATE_LOCAL_MANIFEST"])
        self.assertFalse(report["secrets_included"])
        self.assertFalse(report["provider_database_separation_verified"])
        self.assertFalse(report["production_writes"])
        self.assertFalse(report["staging_writes"])
        self.assertFalse(report["git_updates"])
        self.assertEqual(sorted(p.name for p in self.dest.iterdir()), sorted([
            "stage9v-new-staging-identity.sql", "stage9v-local-setup-manifest.json",
        ]))
        manifest = json.loads((self.dest / "stage9v-local-setup-manifest.json").read_text())
        sql = (self.dest / "stage9v-new-staging-identity.sql").read_text()
        expected = str(uuid.UUID(manifest["staging_uuid"]))
        self.assertEqual(manifest["staging_uuid"], expected)
        self.assertEqual(uuid.UUID(expected).version, 4)
        self.assertEqual(manifest["staging_sql_sha256"], report["staging_sql_sha256"])
        self.assertEqual(manifest["database_name_label_only"], self.name)
        self.assertEqual(sql.count("CREATE TABLE"), 2)
        self.assertEqual(sql.count("INSERT INTO"), 1)
        self.assertNotIn("memory_records", sql)
        self.assertNotIn("memory_gravity", sql)
        self.assertNotIn("auth_token", sql)
        self.assertNotIn("TURSO_DATABASE_AUTH_TOKEN", sql)
        with sqlite3.connect(":memory:") as db:
            db.executescript(sql)
            self.assertTrue(probe._identity(db, manifest["staging_uuid"]))
            self.assertEqual(db.execute("SELECT COUNT(*) FROM galaxy_stage9v_canaries").fetchone()[0], 0)
            marker = db.execute(
                "SELECT schema,environment,database_id,authority,status "
                "FROM galaxy_stage9v_staging_identity"
            ).fetchone()
        self.assertEqual(marker, (
            probe.IDENTITY_SCHEMA, "STAGING_ONLY", expected, "NAOMI", "ACTIVE",
        ))
        if os.name == "posix":
            self.assertEqual(stat.S_IMODE(self.dest.stat().st_mode), 0o700)
            for p in self.dest.iterdir():
                self.assertEqual(stat.S_IMODE(p.stat().st_mode), 0o600)

    def test_refuse_to_overwrite_existing_setup_even_identical_name(self):
        first = self.generate()
        self.assertEqual(first["status"], "PASS_OWNER_LOCAL_BUNDLE_CREATED")
        before = {
            p.name: p.read_bytes()
            for p in self.dest.iterdir()
        }
        second = self.generate()
        self.assertEqual(second["status"], "HOLD_OUTPUT_DIRECTORY_MUST_BE_NEW")
        self.assertEqual(
            before, {p.name: p.read_bytes() for p in self.dest.iterdir()}
        )

    def test_no_output_inside_original_repository(self):
        target = setup._ROOT / "original-repo-should-never-get-a-bundle"
        self.assertFalse(target.exists())
        report = self.generate(destination=target)
        self.assertEqual(report["status"],
                         "HOLD_REFUSE_BUNDLE_INSIDE_ORIGINAL_REPOSITORY")
        self.assertFalse(target.exists())
        self.assertFalse(report["git_updates"])

    def test_refuse_existing_symlink_or_missing_parent(self):
        self.dest.symlink_to(self.temp.name, target_is_directory=True)
        report = self.generate()
        self.assertEqual(report["status"], "HOLD_OUTPUT_DIRECTORY_MUST_BE_NEW")
        self.dest.unlink()
        report = self.generate(destination=self.dest / "not-created")
        self.assertEqual(report["status"], "HOLD_PRIVATE_PARENT_MISSING")

    def test_refuse_bogus_db_name_or_injection(self):
        for name in ("", "prod; DROP TABLE memory_records", "name with spaces",
                     "';DELETE FROM memories", "a" * 90):
            with self.subTest(name=name):
                report = self.generate(database_name=name)
                self.assertEqual(report["status"], "HOLD_DATABASE_NAME_INVALID")
                self.assertFalse(self.dest.exists())

    def test_uuid_sql_interpolation_rejects_other_values(self):
        for item in ("' OR 1=1 --", "abc", str(uuid.uuid1()), "8744D4F4-CEA2-4D42-8B68-3F6CD349912A"):
            with self.subTest(item=item):
                with self.assertRaises(ValueError):
                    setup.make_sql(item)

    def test_cli_refuses_implicit_generation_and_keeps_summary_redacted(self):
        sink = io.StringIO()
        with contextlib.redirect_stdout(sink):
            code = setup.main([
                "--destination", str(self.dest), "--database-name", self.name,
            ])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(sink.getvalue())["status"],
                         "HOLD_EXPLICIT_LOCAL_ONLY_FLAG_REQUIRED")
        self.assertFalse(self.dest.exists())
        sink = io.StringIO()
        with contextlib.redirect_stdout(sink):
            code = setup.main([
                "--destination", str(self.dest), "--database-name", self.name,
                "--confirm-local-only",
            ])
        self.assertEqual(code, 0)
        public = json.loads(sink.getvalue())
        self.assertEqual(public["status"], "PASS_OWNER_LOCAL_BUNDLE_CREATED")
        self.assertFalse(public["staging_writes"])
        self.assertNotIn(self.temp.name, sink.getvalue())
        self.assertNotIn(json.loads(
            (self.dest / "stage9v-local-setup-manifest.json").read_text()
        )["staging_uuid"], sink.getvalue())

    def test_duplicate_uuid_marker_in_local_fixture_is_not_accepted(self):
        self.generate()
        data = json.loads(
            (self.dest / "stage9v-local-setup-manifest.json").read_text()
        )
        with sqlite3.connect(":memory:") as db:
            db.executescript(
                (self.dest / "stage9v-new-staging-identity.sql").read_text()
            )
            db.execute(
                "INSERT INTO galaxy_stage9v_staging_identity VALUES (?,?,?,?,?)",
                (probe.IDENTITY_SCHEMA, "STAGING_ONLY", str(uuid.uuid4()), "NAOMI", "ACTIVE"),
            )
            self.assertFalse(probe._identity(db, data["staging_uuid"]))


if __name__ == "__main__":
    unittest.main()
