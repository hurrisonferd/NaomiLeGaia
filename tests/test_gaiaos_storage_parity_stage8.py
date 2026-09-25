"""Stage 8: preserve browser-session-gated storage visibility under HEATDEATH.

CI uses only an isolated temporary SQLite fixture. No real credentials, network
memory reads or production mode changes.
"""
from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))
_TEMP_BOOT = tempfile.TemporaryDirectory(prefix="gaiaos-storage-parity-")
os.environ["MEMCONOS_DB_PATH"] = str(Path(_TEMP_BOOT.name) / "boot.sqlite")
os.environ.pop("TURSO_DATABASE_URL", None)
os.environ.pop("TURSO_AUTH_TOKEN", None)

import browser_memcon_bridge as bridge
import gaiaos_api as base
import gaiaos_memory_mode as mode
import memcon_runtime as runtime


class StorageParityRouteTests(unittest.TestCase):
    def setUp(self):
        self.workdir = tempfile.TemporaryDirectory(prefix="gaiaos-parity-test-")
        self.addCleanup(self.workdir.cleanup)
        self.path = Path(self.workdir.name) / "isolated.sqlite"
        tables = (
            "memory_relations", "memory_gravity", "memory_lifecycle",
            "memory_syntheses", "memory_importance",
        )
        with sqlite3.connect(self.path) as db:
            for table in tables:
                db.execute(f"CREATE TABLE {table} (id INTEGER PRIMARY KEY)")
            for table, n in zip(tables, (9, 9, 1, 1, 1)):
                db.executemany(
                    f"INSERT INTO {table} (id) VALUES (?)",
                    [(i + 1,) for i in range(n)],
                )
        key = patch.object(base, "API_KEY", "ci-storage-parity-only")
        key.start()
        self.addCleanup(key.stop)
        self.client = TestClient(bridge.app, follow_redirects=False)
        self.addCleanup(self.client.close)
        self.client.cookies.set(base.SESSION_COOKIE, base._session_token())
        db = patch.object(runtime, "_db", side_effect=lambda: sqlite3.connect(self.path))
        db.start()
        self.addCleanup(db.stop)
        backend = patch.object(runtime, "storage_status", return_value={
            "backend": "turso_libsql",
            "remote_configured": True,
            "database_url_present": True,
            "auth_token_present": True,
            "local_path": None,
        })
        backend.start()
        self.addCleanup(backend.stop)

    def test_heatdeath_preserves_nonresearch_parity_route(self):
        # This endpoint should not invoke a GALAXY module or a write path.
        with patch.object(mode, "mode_status", side_effect=AssertionError(
            "storage parity must not need experimental mode control"
        )):
            r = self.client.get("/gaiaos/memory/storage-status")
        self.assertEqual(r.status_code, 200, r.text)
        p = r.json()
        self.assertEqual(p["status"], "PASS_REMOTE_READ_ONLY_SNAPSHOT")
        self.assertEqual(p["backend"], "turso_libsql")
        self.assertEqual(p["counts"], {
            "relations": 9, "gravity_scores": 9, "lifecycle_rows": 1,
            "syntheses": 1, "importance_signals": 1,
        })
        self.assertEqual(p["writes_performed"], [])
        self.assertNotIn("auth_token_present", p)
        self.assertNotIn("database_url_present", p)
        self.assertNotIn("local_path", p)
        self.assertEqual(r.headers["cache-control"], "no-store")

    def test_invalid_existing_browser_cookie_cannot_read_counts(self):
        self.client.cookies.set(base.SESSION_COOKIE, "invalid-existing-cookie")
        r = self.client.get("/gaiaos/memory/storage-status")
        self.assertEqual(r.status_code, 401)
        self.assertNotIn("counts", r.text)

    def test_missing_table_is_hold_without_synthesizing_parity(self):
        with sqlite3.connect(self.path) as db:
            db.execute("DROP TABLE memory_gravity")
        r = self.client.get("/gaiaos/memory/storage-status")
        self.assertEqual(r.status_code, 503)
        self.assertEqual(r.json()["status"], "HOLD_STORAGE_READ_FAILED")
        self.assertNotIn("counts", r.json())
        self.assertEqual(r.json()["writes_performed"], [])

    def test_local_backend_is_explicit_hold_not_remote_durability(self):
        with patch.object(runtime, "storage_status", return_value={
            "backend": "local_sqlite", "remote_configured": False,
        }):
            r = self.client.get("/gaiaos/memory/storage-status")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "HOLD_LOCAL_DURABILITY_UNPROVEN")


if __name__ == "__main__":
    unittest.main()
