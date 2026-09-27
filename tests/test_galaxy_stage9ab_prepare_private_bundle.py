"""Stage 9AB owner-private single-command prep, no Turso credential or socket."""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))
import galaxy_stage9ab_prepare_private_bundle as prep
import galaxy_stage9ab_owner_local_bootstrap as ab
import galaxy_stage9v_staging_turso as v


class OneCommandPrivatePrepTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.parent = Path(temp.name)
        self.parent.chmod(0o700)
        self.dest = self.parent / "sovmem-staging-private"

    def test_one_command_creates_only_four_private_review_files(self):
        result = prep.prepare(destination=self.dest)
        self.assertEqual(result["status"], "PASS_PRIVATE_BUNDLE_READY_ZERO_CONNECTION", result)
        self.assertEqual(result["database_connections"], 0)
        self.assertFalse(result["remote_staging_accessed"])
        self.assertFalse(result["main_accessed"])
        self.assertEqual(self.dest.stat().st_mode & 0o777, 0o700)
        self.assertEqual(len(result["relative_files"]), 4)
        for name in result["relative_files"]:
            item = self.dest / name
            self.assertTrue(item.is_file())
            self.assertEqual(item.stat().st_mode & 0o777, 0o600)
        for dirname in ("stage9v", "stage9aa"):
            self.assertEqual(
                (self.dest / dirname).stat().st_mode & 0o777, 0o700
            )
        self.assertNotIn(str(self.dest), json.dumps(result))
        self.assertNotIn("staging_uuid", json.dumps(result))
        # Both reviewed generators must agree with the static source contract.
        with patch.object(v, "_connect_live",
                          side_effect=AssertionError("DRY RUN MUST NOT CONNECT")):
            sink = io.StringIO()
            with contextlib.redirect_stdout(sink):
                result_code = ab.main(["--bundle-dir", str(self.dest)])
        self.assertEqual(result_code, 0)
        self.assertEqual(
            json.loads(sink.getvalue())["status"],
            "PASS_PRIVATE_BUNDLE_DRY_RUN_NO_CONNECTION",
        )

    def test_prepare_cli_requires_confirmation_and_never_connects(self):
        sink = io.StringIO()
        with contextlib.redirect_stdout(sink):
            code = prep.main(["--destination", str(self.dest)])
        self.assertEqual(code, 2)
        self.assertFalse(self.dest.exists())
        self.assertEqual(
            json.loads(sink.getvalue())["status"],
            "HOLD_EXPLICIT_NO_DATABASE_FILE_ONLY_CONFIRMATION_REQUIRED",
        )
        sink = io.StringIO()
        with patch.object(v, "_connect_live",
                          side_effect=AssertionError("PREP MUST NOT CONNECT")):
            with contextlib.redirect_stdout(sink):
                code = prep.main([
                    "--destination", str(self.dest),
                    "--confirm-local-only",
                ])
        self.assertEqual(code, 0)
        self.assertEqual(
            json.loads(sink.getvalue())["status"],
            "PASS_PRIVATE_BUNDLE_READY_ZERO_CONNECTION",
        )

    def test_repeat_or_symlink_or_shared_parent_refused(self):
        self.assertTrue(prep.prepare(destination=self.dest)["status"].startswith("PASS"))
        self.assertEqual(
            prep.prepare(destination=self.dest)["status"],
            "HOLD_BRAND_NEW_DIR_REQUIRED_OUTSIDE_SHARED_REPOSITORY",
        )
        link = self.parent / "unsafe-link"
        link.symlink_to(self.dest)
        self.assertEqual(
            prep.prepare(destination=link)["status"],
            "HOLD_PRIVATE_DIRECTORY_SYMLINK_FORBIDDEN",
        )
        self.parent.chmod(0o755)
        self.assertEqual(
            prep.prepare(destination=self.parent / "new-unsafe")["status"],
            "HOLD_PARENT_NOT_OWNER_PRIVATE",
        )
        self.assertEqual(
            prep.prepare(destination=ROOT / "tests" / "never-create")["status"],
            "HOLD_BRAND_NEW_DIR_REQUIRED_OUTSIDE_SHARED_REPOSITORY",
        )

    def test_source_bundle_dir_symlink_or_file_permission_change_fails_closed(self):
        prep.prepare(destination=self.dest)
        file = self.dest / "stage9v/stage9v-local-setup-manifest.json"
        file.chmod(0o644)
        sink = io.StringIO()
        with contextlib.redirect_stdout(sink):
            code = ab.main(["--bundle-dir", str(self.dest)])
        self.assertEqual(code, 2)
        self.assertEqual(
            json.loads(sink.getvalue())["status"],
            "HOLD_OWNER_PRIVATE_BUNDLE_FILES_INVALID",
        )
        file.chmod(0o600)
        unsafe = self.parent / "bundle-symlink"
        unsafe.symlink_to(self.dest)
        sink = io.StringIO()
        with contextlib.redirect_stdout(sink):
            code = ab.main(["--bundle-dir", str(unsafe)])
        self.assertEqual(code, 2)
        self.assertEqual(
            json.loads(sink.getvalue())["status"],
            "HOLD_OWNER_PRIVATE_BUNDLE_FILES_INVALID",
        )


if __name__ == "__main__":
    unittest.main()
