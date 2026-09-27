"""Real HTTP/MCP + optional preview archive-read boundary, SQLite isolation.

Stage 9AE protected normal chat/gateway, but authenticated direct MemconOS
search/read and the legacy GALAXY preview still returned raw staging records.
These tests use the REAL Render bridge app and REAL local SQLite rows, not a
pretend successful gateway wrapper. No remote Turso or OpenAI calls.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))
_TMP = tempfile.TemporaryDirectory(prefix="galaxy-public-read-synthetic-")
os.environ["MEMCONOS_DB_PATH"] = str(Path(_TMP.name) / "memcon.db")
os.environ.pop("TURSO_DATABASE_URL", None)
os.environ.pop("TURSO_AUTH_TOKEN", None)
os.environ["RENDER_GIT_COMMIT"] = "CI-PUBLIC-READ-NO-REAL-DEPLOY"
import gaiaos_api as carrier
import memcon_runtime as runtime
import memcon_entrypoint as entry
import browser_memcon_bridge as served
import galaxy_frontdoor_context as front
import gaiaos_public_memory_boundary as boundary
import gaiaos_memory_gateway as gateway
import gaiaos_memory_mode as mode

SESSION_KEY = "STAGE-PUBLIC-READ-SYNTHETIC-SIGNED-SESSION"
TOKEN = {"Authorization": "Bearer " + SESSION_KEY}
ARCHIVE_SOURCE = "galaxy-archive-v1:" + "a" * 64
SAFE_SOURCE = "gaiaos:existing:legitimate-source"
HELD_WORDS = "CALIBRATION SAFE PRIVATE STAGING HOLD SECRET"
FORGED_WORDS = "CALIBRATION FORGED ACTIVE ARCHIVE SECRET"
SAFE_WORDS = "CALIBRATION SAFE VERIFIED LEGACY"


class PublicReadIntegrationTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        _TMP.cleanup()

    def setUp(self):
        patches = [
            patch.object(carrier, "API_KEY", SESSION_KEY),
            patch.object(runtime, "STORAGE_BACKEND", "local_sqlite"),
            # Source checkout keeps GaiaOS at repository root; the actual
            # Render Dockerfile correctly copies it under /app alongside api/.
            patch.object(entry.gaiaos_app, "DEPLOYED_ROOT", ROOT),
        ]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)
        self.client = TestClient(served.app, base_url="https://testserver")
        self.client.cookies.set(carrier.SESSION_COOKIE, carrier._session_token())
        # Each method gets an independent synthetic row population even though
        # the process-local temporary SQLite fixture persists across tests.
        with runtime._db() as conn:
            conn.execute("DELETE FROM memory_records")
        self.safe = runtime.write_record(
            authority="NAOMI", approved=True, record_type="TEST",
            scope="MemoryOS", statement=SAFE_WORDS, source=SAFE_SOURCE,
        )["record"]["record_id"]
        self.held = runtime.write_record(
            authority="NAOMI", approved=True, record_type="TEST",
            scope="MemoryOS", statement=HELD_WORDS,
            source="gaiaos:synthetic-staging-fixture",
            status="STAGED_HISTORICAL_HOLD",
        )["record"]["record_id"]
        self.forged = runtime.write_record(
            authority="NAOMI", approved=True, record_type="TEST",
            scope="MemoryOS", statement=FORGED_WORDS,
            source=ARCHIVE_SOURCE, status="ACTIVE",
        )["record"]["record_id"]

    def _no_archive_text(self, response: object):
        serialized = json.dumps(response)
        for sensitive in (HELD_WORDS, FORGED_WORDS, ARCHIVE_SOURCE,
                          self.held, self.forged):
            self.assertNotIn(sensitive, serialized)

    def test_authenticated_exact_http_read_only_exposes_clean_record(self):
        clean = self.client.get("/memconos/read/" + self.safe, headers=TOKEN)
        self.assertEqual(clean.status_code, 200, clean.text)
        self.assertEqual(clean.json()["record"]["statement"], SAFE_WORDS)
        for rid in (self.held, self.forged):
            with self.subTest(rid=rid):
                withheld = self.client.get(
                    "/memconos/read/" + rid, headers=TOKEN,
                )
                unknown = self.client.get(
                    "/memconos/read/MEM-NONEXISTENT", headers=TOKEN,
                )
                self.assertEqual(withheld.status_code, 404)
                self.assertEqual(withheld.json(), unknown.json())
                self._no_archive_text(withheld.json())

    def test_direct_http_mixed_search_fails_entire_response_no_partial_leak(self):
        raw = runtime.search_records("CALIBRATION", 10, "MemoryOS")
        self.assertEqual(raw["count"], 3)
        mixed = self.client.get(
            "/memconos/search", headers=TOKEN,
            params={"q": "CALIBRATION", "scope": "MemoryOS", "limit": 10},
        )
        self.assertEqual(mixed.status_code, 409, mixed.text)
        self.assertEqual(mixed.json()["detail"]["status"], boundary.HOLD)
        self.assertEqual(mixed.json()["detail"]["records"], [])
        self._no_archive_text(mixed.json())

    def test_direct_http_clean_search_preserves_unmodified_native_envelope(self):
        expected = runtime.search_records("VERIFIED LEGACY", 10, "MemoryOS")
        self.assertEqual(expected["count"], 1)
        result = self.client.get(
            "/memconos/search", headers=TOKEN,
            params={"q": "VERIFIED LEGACY", "scope": "MemoryOS", "limit": 10},
        )
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json(), expected)

    def test_direct_http_requires_original_authorization_before_database_read(self):
        self.client.cookies.clear()
        with patch.object(
            runtime, "get_record", side_effect=AssertionError("NO DATABASE READ"),
        ):
            missing = self.client.get("/memconos/read/" + self.safe)
        self.assertEqual(missing.status_code, 401)
        with patch.object(
            runtime, "search_records",
            side_effect=AssertionError("NO DATABASE SEARCH"),
        ):
            wrong = self.client.get(
                "/memconos/search",
                headers={"Authorization": "Bearer WRONG-SECRET"},
            )
        self.assertEqual(wrong.status_code, 401)

    def test_mcp_exact_and_search_apply_same_denial_on_real_rows(self):
        clean = entry.memcon_read(self.safe)
        self.assertTrue(clean["found"])
        self.assertEqual(clean["record"]["statement"], SAFE_WORDS)
        for rid in (self.held, self.forged):
            result = entry.memcon_read(rid)
            self.assertEqual(
                result,
                {"found": False, "record_id": rid,
                 "runtime": runtime.SCHEMA_VERSION},
            )
            self.assertNotIn("record", result)
        mixed = entry.memcon_search("CALIBRATION", 10)
        self.assertEqual(mixed["status"], boundary.HOLD)
        self.assertEqual(mixed["records"], [])
        self._no_archive_text(mixed)
        clean_search = entry.memcon_search("VERIFIED LEGACY", 10)
        self.assertEqual(clean_search,
                         runtime.search_records("VERIFIED LEGACY", 10))

    def test_memoryos_gateway_http_and_host_bootstrap_already_hold_mixed_alias(self):
        retrieve = self.client.get(
            "/memoryos/retrieve", headers=TOKEN,
            params={"q": "CALIBRATION", "scope": "MemoryOS", "limit": 10},
        )
        self.assertEqual(retrieve.status_code, 200, retrieve.text)
        self.assertEqual(
            retrieve.json()["memory_gateway"]["status"],
            "HOLD_UNRELEASED_ARCHIVE_IN_LEGACY",
        )
        self.assertIsNone(retrieve.json()["retrieval"])
        self._no_archive_text(retrieve.json())

        with patch.object(
            entry.gaiaos_app, "_read_local_json",
            return_value={"platform_version": "CI-ISOLATED"},
        ), patch.object(
            entry.gaiaos_app, "_deployed_source",
            return_value="CI-NO-REMOTE-SOURCE",
        ):
            boot = self.client.get(
                "/gaiaos/bootstrap", headers=TOKEN,
                params={"query": "CALIBRATION", "scope": "MemoryOS", "limit": 10},
            )
        self.assertEqual(boot.status_code, 200, boot.text)
        self.assertEqual(
            boot.json()["memory"]["memory_gateway"]["status"],
            "HOLD_UNRELEASED_ARCHIVE_IN_LEGACY",
        )
        self._no_archive_text(boot.json())

    def test_real_host_bootstrap_observe_and_candidate_routes_use_existing_auth(self):
        # CI exposed a separate, pre-existing source-level failure:
        # memcon_entrypoint referenced undefined "base" in these HTTP routes,
        # although it already defines a correct _auth() helper.
        unauthorized = self.client.get(
            "/gaiaos/bootstrap",
            params={"query": "VERIFIED LEGACY"},
        )
        self.assertEqual(unauthorized.status_code, 401)
        unauthorized_candidates = self.client.get("/memoryos/candidates")
        self.assertEqual(unauthorized_candidates.status_code, 401)
        with patch.object(
            entry.gaiaos_app, "_read_local_json",
            return_value={"platform_version": "CI-ISOLATED"},
        ), patch.object(
            entry.gaiaos_app, "_deployed_source",
            return_value="CI-NO-REMOTE-SOURCE",
        ):
            boot = self.client.get(
                "/gaiaos/bootstrap", headers=TOKEN,
                params={"query": "VERIFIED LEGACY",
                        "scope": "MemoryOS", "limit": 10},
            )
        self.assertEqual(boot.status_code, 200, boot.text)
        self.assertEqual(
            boot.json()["memory"]["retrieval"]["records"][0]["record_id"],
            self.safe,
        )
        observed = self.client.post(
            "/memoryos/observe", headers=TOKEN,
            json={
                "source": "ci:synthetic:observe",
                "statement": "Synthetic only observational memory candidate",
                "owner": "ANVIL", "why_material": "CI route proof",
            },
        )
        self.assertEqual(observed.status_code, 200, observed.text)
        self.assertEqual(observed.json()["status"], "CANDIDATE")
        self.assertEqual(observed.json()["durable_write"], "NOT_PERFORMED")
        listed = self.client.get(
            "/memoryos/candidates", headers=TOKEN,
            params={"limit": 2, "status": "CANDIDATE"},
        )
        self.assertEqual(listed.status_code, 200, listed.text)
        listed_post = self.client.post(
            "/memoryos/candidates", headers=TOKEN,
            json={"limit": 2, "status": "CANDIDATE"},
        )
        self.assertEqual(listed_post.status_code, 200, listed_post.text)

    def test_legacy_preview_cannot_return_any_mixed_archive_record(self):
        outcome = front.preview(runtime, "CALIBRATION", 3)
        self.assertEqual(
            outcome["status"],
            "HOLD_UNRELEASED_ARCHIVE_IN_LEGACY_PREVIEW", outcome,
        )
        self.assertEqual(outcome["records"], [])
        self._no_archive_text(outcome)
        clean = front.preview(runtime, "VERIFIED LEGACY", 3)
        self.assertEqual(clean["status"], "PASS_SHADOW_LEGACY_READ", clean)
        self.assertEqual(clean["records"][0]["record"]["record_id"], self.safe)

    def test_legacy_preview_second_record_read_forged_archive_fails_closed(self):
        safe = runtime.get_record(self.safe)
        forged = dict(safe, status="ACTIVE", source=ARCHIVE_SOURCE)
        stub = SimpleNamespace(
            _INITIALIZED=True,
            search_records=lambda *args: {
                "records": [safe], "scope_applied": "MemoryOS",
                "query_filter_active": True,
            },
            galaxy_record=lambda *args: {
                "record": forged, "lifecycle": {"state": "ACTIVE"},
                "relations": [],
            },
            galaxy_governing_state=lambda *args: {
                "record_id": self.safe, "state": "CURRENT",
                "current_default_eligible": True,
            },
        )
        out = front.preview(stub, SAFE_WORDS, 3)
        self.assertEqual(
            out["status"], "HOLD_UNRELEASED_ARCHIVE_IN_LEGACY_PREVIEW",
            out,
        )
        self.assertEqual(out["records"], [])
        self._no_archive_text(out)

    def test_real_browser_orbit_and_gravity_commands_do_not_return_staged_data(self):
        with patch.object(served, "_research_bigbang_authorized",
                          return_value=True):
            for rid in (self.held, self.forged):
                with self.subTest(rid=rid):
                    orbit = self.client.post(
                        "/chat", json={"messages": [
                            {"role": "user", "content": "//PW:ORBIT// " + rid}
                        ]},
                    )
                    self.assertEqual(orbit.status_code, 200, orbit.text)
                    self.assertIn(boundary.HOLD, orbit.json()["output"])
                    self.assertNotIn(HELD_WORDS, orbit.text)
                    self.assertNotIn(FORGED_WORDS, orbit.text)
                    self.assertNotIn(ARCHIVE_SOURCE, orbit.text)
                    gravity = self.client.post(
                        "/chat", json={"messages": [
                            {"role": "user", "content": "//PW:GRAVITY// " + rid}
                        ]},
                    )
                    self.assertEqual(gravity.status_code, 200, gravity.text)
                    self.assertIn(boundary.HOLD, gravity.json()["output"])
                    self.assertNotIn(HELD_WORDS, gravity.text)
                    self.assertNotIn(FORGED_WORDS, gravity.text)
                    self.assertNotIn(ARCHIVE_SOURCE, gravity.text)

    def test_pure_shared_guard_parity_and_no_optional_galaxy_dependency(self):
        self.assertFalse(boundary.unreleased(runtime.get_record(self.safe)))
        self.assertTrue(boundary.unreleased(runtime.get_record(self.held)))
        self.assertTrue(boundary.unreleased(runtime.get_record(self.forged)))
        for rid in (self.safe, self.held, self.forged):
            self.assertEqual(
                gateway._unreleased_staging_row(runtime.get_record(rid)),
                boundary.unreleased(runtime.get_record(rid)),
            )
        with patch.dict(sys.modules, {
            "galaxy_phase3_exit": None, "galaxy_legacy_gravity": None,
        }):
            self.assertTrue(boundary.unreleased(runtime.get_record(self.held)))
            self.assertFalse(boundary.unreleased(runtime.get_record(self.safe)))


if __name__ == "__main__":
    unittest.main()
