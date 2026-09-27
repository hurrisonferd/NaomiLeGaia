"""Actual Stage9AG signed-file import -> GaiaOS native/host/MCP read isolation.

The production MemconOS search path previously bypassed the Stage9AE gateway
filter when called by /memconos/search, the MCP memcon_search tool and native
Phase3 candidate scans. This integration test injects the EXACT synthetic,
separately signed 9AG first batch into the actual local native SQLite backend
used by those production functions. No real Turso, Render or private records.
"""
from __future__ import annotations

import importlib.util
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
sys.path.insert(0, str(ROOT / "tests"))

# The actual served-app imports memcon_entrypoint which INITIALIZES the
# backend at module import. Isolate BEFORE that import and ban remote secrets.
_RUNNING = tempfile.TemporaryDirectory(prefix="gaiaos-native-hold-ci-")
os.environ["MEMCONOS_DB_PATH"] = str(Path(_RUNNING.name) / "ci-carrier.db")
os.environ.pop("TURSO_DATABASE_URL", None)
os.environ.pop("TURSO_AUTH_TOKEN", None)
os.environ["RENDER_GIT_COMMIT"] = "CI-NATIVE-HELD-READER-NOT-DEPLOYED"

import memcon_runtime as store
import legacy_memory_reader as legacy
import galaxy_frontdoor_context as preview
import galaxy_phase3_exit
import galaxy_legacy_gravity
import gaiaos_memory_mode as mode
import gaiaos_memory_gateway as gateway
import gaiaos_chat_memory as chat_memory
import gaiaos_api as carrier
import browser_memcon_bridge as served
import memcon_entrypoint as entry
import test_galaxy_stage9ag_staging_historical_import as fixture
from test_bigbang_operational_reader_stage6 import FakeMemory, candidate_pool
from test_galaxy_stage9w_browser_chat_wiring import prepared

# Import the real GaiaOS runtime source, not a mocked retrieve() envelope.
SOURCE = ROOT / "GaiaOS/SystemsOS/Core/MemoryOS/Runtime/GAIAOS-MEMORY.v1.py"
spec = importlib.util.spec_from_file_location("galaxy_native_hold_memory_runtime", SOURCE)
assert spec is not None and spec.loader is not None
memory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(memory)


def native_db(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


class SignedNativeHeldArchiveTests(unittest.TestCase):
    def setUp(self):
        fx = fixture.FirstSignedStagingTests(
            "test_first_batch_atomic_exact_two_hold_rows_and_signed_receipts"
        )
        fx.setUp()
        self.addCleanup(fx.doCleanups)
        self.fx = fx
        signed = fx.run_import(apply=True)
        self.assertEqual(
            signed["status"], "PASS_LOCAL_HELD_STAGING_IMPORT_REOPEN_FIXTURE",
            signed,
        )
        with native_db(fx.stage) as db:
            self.held = [
                dict(row) for row in db.execute(
                    "SELECT * FROM memory_records ORDER BY record_id"
                )
            ]
        self.assertEqual(len(self.held), 2)
        self.patches = [
            patch.object(store, "_db", side_effect=lambda: native_db(fx.stage)),
            patch.object(store, "_INITIALIZED", True),
            patch.object(carrier, "API_KEY", "STAGE9-FAKE-OWNER-KEY"),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    def add_clean(self):
        rows = [
            (
                "MEM-CLEAN-OLDER-CURRENT", "MemoryOS",
                "approved gravity contextual memory recall", "ACTIVE",
                "owner:verified:current", "2000-01-01T00:00:00Z",
            ),
            (
                "MEM-CLEAN-OLDER-HISTORY", "MemoryOS",
                "approved historical memory context", "HISTORICAL",
                "owner:verified:historical", "2000-01-02T00:00:00Z",
            ),
            (
                "MEM-CLEAN-VERA-EXPERIENCE", "VERA_E_LANE",
                "verifiable experience belongs to VERA", "ACTIVE",
                "owner:vera-e-lane", "2000-01-03T00:00:00Z",
            ),
            (
                "MEM-FORGED-ACTIVE-ARCHIVE", "MemoryOS",
                "forged current statement should not be recalled", "ACTIVE",
                "GaLaXy-ArChIvE-V1:" + "f" * 64, "2099-01-01T00:00:00Z",
            ),
            (
                "MEM-FORGED-LOWERCASE-HOLD", "MemoryOS",
                "unreleased lowercase status memory", "staged_historical_hold",
                "owner:forged-status", "2099-01-02T00:00:00Z",
            ),
        ]
        with native_db(self.fx.stage) as db:
            for rid, scope, statement, status, source, now in rows:
                db.execute(
                    "INSERT INTO memory_records VALUES "
                    "(?,?,?,?,?,?,?,?,?,?,?,?)",
                    (rid, "NAOMI", "TEST", scope, statement,
                     source, status, "1", now, now, None, "{}"),
                )

    def test_actual_stage9ag_signed_file_native_default_search_and_before_limit(self):
        self.add_clean()
        before = self.fx.stage.read_bytes()
        unscoped = store.search_records("", limit=100, scope=None)
        memoryos = store.search_records("", limit=1, scope="MemoryOS")
        lane = store.search_records("", limit=50, scope="VERA_E_LANE")
        wanted = {"MEM-CLEAN-OLDER-CURRENT", "MEM-CLEAN-OLDER-HISTORY",
                  "MEM-CLEAN-VERA-EXPERIENCE"}
        self.assertEqual(
            {r["record_id"] for r in unscoped["records"]}, wanted,
        )
        self.assertEqual(unscoped["count"], 3)
        self.assertEqual(
            memoryos["records"][0]["record_id"],
            "MEM-CLEAN-OLDER-HISTORY",
        )
        self.assertEqual(memoryos["count"], 1)
        self.assertEqual(lane["count"], 1)
        self.assertEqual(
            lane["records"][0]["record_id"], "MEM-CLEAN-VERA-EXPERIENCE",
        )
        self.assertEqual(self.fx.stage.read_bytes(), before)
        self.fx.protected()

    def test_actual_signed_held_ids_are_invisible_to_native_and_legacy_search(self):
        for row in self.held:
            rid = row["record_id"]
            for scope in (None, "MemoryOS"):
                with self.subTest(rid=rid, scope=scope):
                    native = store.search_records(rid, 20, scope)
                    orig = legacy.read(store, rid, scope, 20)
                    self.assertEqual(native["records"], [])
                    self.assertEqual(orig["records"], [])
                    self.assertEqual(native["query_terms_applied"], [rid.lower()])
            self.assertEqual(
                store.get_record(rid)["statement"], row["statement"],
                "The privileged explicit-ID audit path must stay available",
            )
        self.fx.protected()

    def test_real_phase3_sql_scan_cannot_consider_imported_or_forged_archive(self):
        self.add_clean()
        pool = store.galaxy_phase3_candidate_pool(
            "approved memory context", scope="MemoryOS", limit=10,
        )
        self.assertEqual(pool["scope_eligible_population_count"], 2)
        every = (
            set(pool["candidate_record_ids"])
            | set(pool["ambiguous_record_ids"])
        )
        for row in self.held:
            self.assertNotIn(row["record_id"], every)
        self.assertFalse(any("FORGED" in rid for rid in every))
        self.fx.protected()

    def test_actual_served_rest_and_mcp_default_search_are_sealed(self):
        self.add_clean()
        client = TestClient(served.app, base_url="https://testserver")
        auth = {"Authorization": "Bearer STAGE9-FAKE-OWNER-KEY"}
        response = client.get(
            "/memconos/search", params={"q": "", "scope": "MemoryOS",
                                        "limit": 20}, headers=auth,
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(
            {r["record_id"] for r in response.json()["records"]},
            {"MEM-CLEAN-OLDER-CURRENT", "MEM-CLEAN-OLDER-HISTORY"},
        )
        response = client.get(
            "/memoryos/retrieve", params={"q": "", "scope": "MemoryOS",
                                          "limit": 20}, headers=auth,
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["retrieval"]["count"], 2)
        self.assertEqual(
            response.json()["memory_gateway"]["effective_mode"],
            mode.HEATDEATH,
        )
        mcp = entry.memcon_search("", limit=100)
        self.assertEqual(mcp["count"], 3)
        for row in self.held:
            self.assertNotIn(row["statement"], response.text)
            self.assertNotIn(row["statement"], str(mcp))
        # Known-ID owner-only raw audit is deliberate, NOT implicit context.
        exact = client.get(
            f"/memconos/read/{self.held[0]['record_id']}", headers=auth,
        )
        self.assertEqual(exact.status_code, 200)
        self.assertEqual(
            exact.json()["record"]["status"], "STAGED_HISTORICAL_HOLD",
        )
        self.fx.protected()

    def test_real_memory_runtime_and_gateway_hold_reads_never_promote(self):
        packet = memory.retrieve(
            self.held[0]["record_id"], "MemoryOS", limit=4,
        )
        self.assertEqual(packet["status"], "OBSERVED")
        self.assertEqual(packet["memory_gateway"]["effective_mode"], "HEATDEATH")
        self.assertEqual(packet["retrieval"]["records"], [])
        self.assertIsNone(packet["galaxy_context"])
        self.assertEqual(
            store.get_record(self.held[0]["record_id"])["status"],
            "STAGED_HISTORICAL_HOLD",
        )
        self.fx.protected()

    def test_native_local_libsql_is_also_sealed_and_read_only(self):
        try:
            import libsql
        except ImportError:
            self.skipTest("CI installs actual public libsql for local file")
        self.add_clean()
        before = self.fx.stage.read_bytes()
        with patch.object(
            store, "_db",
            side_effect=lambda: libsql.connect(database=str(self.fx.stage)),
        ):
            all_rows = store.search_records("", 100, None)
            memoryos = store.search_records("", 100, "MemoryOS")
            pool = store.galaxy_phase3_candidate_pool(
                "approved memory context", scope="MemoryOS", limit=10,
            )
        self.assertEqual(all_rows["count"], 3)
        self.assertEqual(memoryos["count"], 2)
        self.assertEqual(pool["scope_eligible_population_count"], 2)
        self.assertEqual(before, self.fx.stage.read_bytes())
        self.fx.protected()

    def test_preview_independent_guard_rejects_raw_held_without_record_read(self):
        row = dict(self.held[0])
        class MisconfiguredRead:
            _INITIALIZED = True
            def search_records(self, query, limit, scope):
                return {
                    "records": [row], "count": 1, "scope_applied": scope,
                    "query_filter_active": True,
                }
            def galaxy_record(self, rid):
                raise AssertionError("STAGED RECORD DETAILS MUST NOT BE READ")
        out = preview.preview(MisconfiguredRead(), "archived", limit=3)
        self.assertEqual(out["status"], "HOLD_UNRELEASED_STAGED_ARCHIVE")
        self.assertEqual(out["records"], [])
        self.assertEqual(out["writes_performed"], [])
        self.assertNotIn(row["statement"], str(out))

    def test_preview_independent_guard_rejects_forged_active_archive_detail(self):
        clean = {
            "record_id": "MEM-APPROVED", "scope": "MemoryOS",
            "status": "ACTIVE", "statement": "approved memory",
            "source": "owner:clean",
        }
        class SwappedRead:
            _INITIALIZED = True
            def search_records(self, query, limit, scope):
                return {
                    "records": [clean], "count": 1, "scope_applied": scope,
                    "query_filter_active": True,
                }
            def galaxy_record(self, rid):
                return {
                    "record": {
                        **clean, "status": "ACTIVE",
                        "source": "GaLaXy-ArChIvE-V1:" + "a" * 64,
                    },
                }
        out = preview.preview(SwappedRead(), "approved", 3)
        self.assertEqual(out["status"], "HOLD_UNRELEASED_STAGED_ARCHIVE")
        self.assertEqual(out["records"], [])

    def test_operational_and_gateway_independent_lowercase_guard_prevents_scoring(self):
        fake = FakeMemory()
        fake.records["CURRENT"]["status"] = "staged_historical_hold"
        with patch.object(
            galaxy_phase3_exit, "build_candidate_pool",
            side_effect=candidate_pool,
        ), patch.object(
            galaxy_legacy_gravity, "resolve_for_retrieval",
            side_effect=AssertionError("NO SCORING ON HELD ARCHIVE"),
        ):
            out = preview.operational(fake, "gravity contextual influence memory retrieval")
        self.assertEqual(out["status"], "HOLD_UNRELEASED_STAGED_ARCHIVE")
        self.assertEqual(out["records"], [])
        self.assertTrue(gateway._unreleased_staging_row({
            "status": "ACTIVE", "source": "GaLaXy-ArChIvE-V1:" + "a" * 64,
        }))

    def test_model_final_boundary_rejects_mixed_case_ungraduated_archive(self):
        packet = prepared()
        packet["current_records"][0]["source"] = (
            "GaLaXy-ArChIvE-V1:" + "e" * 64
        )
        self.assertFalse(chat_memory.validate_prepared(packet))
        packet = prepared()
        packet["current_records"][0]["status"] = "staged_historical_hold"
        self.assertFalse(chat_memory.validate_prepared(packet))


if __name__ == "__main__":
    unittest.main()
