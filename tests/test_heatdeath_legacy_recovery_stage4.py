"""Stage-4 recovery app tests: isolated startup, strict auth, real read-only SQLite."""
from __future__ import annotations

import builtins
import os
import sqlite3
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))

import gaiaos_legacy_recovery_app as recovery

KEY = "CI-ONLY-RECOVERY-KEY-" + "z" * 42
AUTH = {"Authorization": f"Bearer {KEY}"}

CREATE_TABLE = """
CREATE TABLE memory_records (
    record_id TEXT PRIMARY KEY, authority TEXT NOT NULL,
    record_type TEXT NOT NULL, scope TEXT NOT NULL,
    statement TEXT NOT NULL, source TEXT NOT NULL,
    status TEXT NOT NULL, version TEXT NOT NULL,
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
    supersedes TEXT, notes TEXT NOT NULL DEFAULT ''
)
"""


def seed(path: str) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute(CREATE_TABLE)
        conn.executemany(
            """INSERT INTO memory_records
               (record_id, authority, record_type, scope, statement, source,
                status, version, created_at, updated_at, supersedes, notes)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            [
                ("LEG-1", "NAOMI", "FACT", "MemoryOS",
                 "legacy memory baseline", "owner:original", "ACTIVE", "1",
                 "2026-09-23T10:00:00Z", "2026-09-23T10:00:00Z", None, ""),
                ("LEG-2", "NAOMI", "FACT", "MemoryOS",
                 "legacy memory revision", "owner:revision", "HISTORICAL", "2",
                 "2026-09-24T10:00:00Z", "2026-09-24T10:00:00Z", "LEG-1",
                 "context evidence"),
                ("ELANE-1", "NAOMI", "FACT", "VERA_E_LANE",
                 "legacy member voice", "member:VERA", "ACTIVE", "1",
                 "2026-09-24T11:00:00Z", "2026-09-24T11:00:00Z", None, ""),
            ],
        )


class RecoveryAppTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = str(Path(self.tmp.name) / "existing.sqlite")
        seed(self.db)
        self.patch_env = patch.dict(os.environ, {
            "GAIAOS_RECOVERY_API_KEY": KEY,
            "GAIAOS_RECOVERY_ALLOW_LOCAL_TEST": "1",
            "GAIAOS_RECOVERY_SOURCE_COMMIT": "ci-test-only",
        })
        self.patch_env.start()
        self.addCleanup(self.patch_env.stop)
        self.patch_backend = patch.object(
            recovery.storage, "STORAGE_BACKEND", "local_sqlite"
        )
        self.patch_backend.start()
        self.addCleanup(self.patch_backend.stop)
        self.patch_db = patch.object(
            recovery.storage, "DB_PATH", Path(self.db)
        )
        self.patch_db.start()
        self.addCleanup(self.patch_db.stop)
        self.prev_initialized = recovery.storage._INITIALIZED
        recovery.storage._INITIALIZED = False
        self.addCleanup(setattr, recovery.storage,
                        "_INITIALIZED", self.prev_initialized)
        self.client = TestClient(recovery.app)
        self.addCleanup(self.client.close)

    def test_liveness_does_not_claim_memory_readiness(self):
        res = self.client.get("/healthz")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["memory"], "NOT_CHECKED")
        self.assertTrue(res.json()["recovery_key_configured"])

    def test_missing_or_invalid_auth_denied_before_memory_access(self):
        for headers in ({}, {"Authorization": "Bearer WRONG"},
                        {"Authorization": "Basic " + KEY}):
            result = self.client.get("/legacy/status", headers=headers)
            self.assertEqual(result.status_code, 401)
        self.assertFalse(recovery.storage._INITIALIZED)

    def test_missing_recovery_key_fails_closed(self):
        with patch.dict(os.environ, {"GAIAOS_RECOVERY_API_KEY": ""}):
            res = self.client.get("/legacy/status", headers=AUTH)
            self.assertEqual(res.status_code, 503)
        self.assertFalse(recovery.storage._INITIALIZED)

    def test_local_storage_refused_without_explicit_isolated_test_override(self):
        with patch.dict(os.environ, {"GAIAOS_RECOVERY_ALLOW_LOCAL_TEST": ""}):
            res = self.client.get("/legacy/status", headers=AUTH)
            self.assertEqual(res.status_code, 503)
            self.assertEqual(
                res.json()["detail"],
                "Existing remote memory storage is not configured",
            )
        self.assertFalse(recovery.storage._INITIALIZED)

    def test_ready_only_after_existing_readonly_schema_probe(self):
        response = self.client.get("/legacy/status", headers=AUTH)
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["mode"], "HEATDEATH")
        self.assertEqual(body["effective_mode"], "HEATDEATH")
        self.assertEqual(body["storage_backend"], "local_sqlite")
        self.assertEqual(body["source_commit"], "ci-test-only")
        self.assertFalse(body["ordinary_gaiaos_routes_available"])
        self.assertTrue(recovery.storage._INITIALIZED)
        with sqlite3.connect(self.db) as conn:
            self.assertEqual(
                [row[0] for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )],
                ["memory_records"],
            )

    def test_authenticated_legacy_query_retains_history_and_provenance(self):
        res = self.client.post(
            "/legacy/search", json={"q": "legacy memory", "scope": "MemoryOS"},
            headers=AUTH,
        )
        self.assertEqual(res.status_code, 200, res.text)
        body = res.json()
        self.assertEqual(body["status"], "PASS_LEGACY_READ")
        self.assertEqual(body["record_count"], 2)
        self.assertEqual(
            [row["record_id"] for row in body["retrieval"]["records"]],
            ["LEG-2", "LEG-1"],
        )
        self.assertEqual(
            [row["source"] for row in body["retrieval"]["records"]],
            ["owner:revision", "owner:original"],
        )
        self.assertEqual(body["retrieval"]["records"][0]["status"], "HISTORICAL")
        self.assertFalse(body["semantic_galaxy_applied"])
        self.assertEqual(body["writes_performed"], [])

    def test_notes_and_scope_filters_preserve_original_semantics(self):
        found = self.client.post(
            "/legacy/search", json={"q": "revision evidence", "scope": "MemoryOS"},
            headers=AUTH,
        )
        self.assertEqual(found.status_code, 200)
        self.assertEqual(
            [row["record_id"] for row in found.json()["retrieval"]["records"]],
            ["LEG-2"],
        )
        no_match = self.client.post(
            "/legacy/search", json={"q": "unmatched", "scope": "MemoryOS"},
            headers=AUTH,
        )
        self.assertEqual(no_match.status_code, 200)
        self.assertEqual(no_match.json()["record_count"], 0)

    def test_empty_query_requires_explicit_broad_read(self):
        denied = self.client.post(
            "/legacy/search", json={"q": "", "scope": None}, headers=AUTH
        )
        self.assertEqual(denied.status_code, 422)
        allowed = self.client.post(
            "/legacy/search",
            json={"q": "", "scope": None, "broad_read_approved": True},
            headers=AUTH,
        )
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.json()["record_count"], 3)

    def test_exact_record_recovery_and_negative_read(self):
        match = self.client.post(
            "/legacy/record", json={"record_id": "LEG-2"}, headers=AUTH
        )
        self.assertEqual(match.status_code, 200)
        self.assertEqual(match.json()["record"]["source"], "owner:revision")
        missing = self.client.post(
            "/legacy/record", json={"record_id": "not-found"}, headers=AUTH
        )
        self.assertEqual(missing.status_code, 404)

    def test_known_record_selftest_and_missing_fixture_hold(self):
        good = self.client.post(
            "/legacy/selftest", json={"known_record_id": "LEG-1"},
            headers=AUTH,
        )
        self.assertEqual(good.status_code, 200, good.text)
        self.assertEqual(good.json()["status"], "PASS_RECOVERY_KNOWN_RECORD")
        self.assertEqual(good.json()["galaxy_import_count"], 0)
        missing = self.client.post(
            "/legacy/selftest", json={"known_record_id": "not-found"},
            headers=AUTH,
        )
        self.assertEqual(missing.status_code, 409)

    def test_readonly_actions_leave_records_and_schema_unchanged(self):
        def state():
            with sqlite3.connect(self.db) as conn:
                return {
                    "names": conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall(),
                    "rows": conn.execute(
                        "SELECT * FROM memory_records ORDER BY record_id"
                    ).fetchall(),
                    "changes": conn.total_changes,
                }
        before = state()
        for _ in range(2):
            for path, payload in (
                ("/legacy/search", {"q": "legacy", "scope": "MemoryOS"}),
                ("/legacy/record", {"record_id": "LEG-1"}),
                ("/legacy/selftest", {"known_record_id": "LEG-2"}),
            ):
                response = self.client.post(path, json=payload, headers=AUTH)
                self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(before, state())
        for write_path in ("/memoryos/write", "/legacy/write",
                           "/legacy/promote", "/chat", "/mcp"):
            response = self.client.post(
                write_path, json={"approved": True}, headers=AUTH
            )
            self.assertEqual(response.status_code, 404)

    def test_missing_existing_schema_holds_without_creating_tables(self):
        blank = str(Path(self.tmp.name) / "missing.sqlite")
        with patch.object(recovery.storage, "DB_PATH", Path(blank)):
            result = self.client.get("/legacy/status", headers=AUTH)
            self.assertEqual(result.status_code, 503)
            self.assertEqual(
                result.json()["detail"],
                "Existing legacy memory schema is unavailable",
            )
        with sqlite3.connect(blank) as conn:
            names = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        self.assertEqual(names, [])
        self.assertFalse(recovery.storage._INITIALIZED)

    def test_galaxy_and_main_carrier_import_are_blocked_on_clean_startup(self):
        code = textwrap.dedent("""
            import builtins, json, sys
            original = builtins.__import__
            banned = {'gaiaos_app', 'gaiaos_api', 'browser_memcon_bridge',
                      'host_memory_gateway', 'memcon_entrypoint'}
            def blocked(name, *args, **kwargs):
                if name.startswith('galaxy') or name in banned:
                    raise ImportError("simulated broken GALAXY/main carrier")
                return original(name, *args, **kwargs)
            builtins.__import__ = blocked
            import gaiaos_legacy_recovery_app as app
            print(json.dumps({
                'service': app.SERVICE, 'mode': app.memory_mode.HEATDEATH,
                'loaded': any(m.startswith('galaxy') for m in sys.modules),
            }))
        """)
        proc = subprocess.run(
            [sys.executable, "-c", code], text=True, capture_output=True,
            cwd=ROOT, timeout=35,
            env={**os.environ, "PYTHONPATH": str(ROOT / "api")},
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = __import__("json").loads(proc.stdout)
        self.assertEqual(result, {
            "service": "gaiaos-legacy-recovery",
            "mode": "HEATDEATH",
            "loaded": False,
        })

    def test_source_and_image_import_dependency_boundaries(self):
        source = (ROOT / "api" / "gaiaos_legacy_recovery_app.py").read_text()
        docker = (ROOT / "api" / "Dockerfile.legacy-recovery").read_text()
        for forbidden in (
            "import gaiaos_app", "import gaiaos_api", "import browser_memcon_bridge",
            "import galaxy_frontdoor_context", "import galaxy_production",
        ):
            self.assertNotIn(forbidden, source)
        for forbidden in ("COPY api/gaiaos_app.py", "COPY api/browser_memcon_bridge.py",
                          "COPY api/galaxy_", "COPY api/host_memory_gateway.py",
                          "COPY api/gaiaos_api.py"):
            self.assertNotIn(forbidden, docker)
        self.assertIn("COPY api/legacy_memory_reader.py", docker)
        self.assertIn("COPY api/memcon_runtime.py", docker)
        self.assertNotIn("INSERT INTO", source)
        self.assertNotIn("CREATE TABLE", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
