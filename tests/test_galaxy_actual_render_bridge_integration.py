"""Release-integration audit: test the ACTUAL Render browser_memcon_bridge app.

Prior Stage 9W/9AF served-app tests exercised gaiaos_app.app's original
gaiaos_api.browser_chat route. Render's Docker CMD actually imports
browser_memcon_bridge, removes THAT route, and registers its own /chat.
These tests ensure the tested route really is the deployed entrypoint.

All memory, sessions, DBs, mode approvals and model responses are synthetic.
BIGBANG exists ONLY as mocked test authorization; the real controller remains
locked in HEATDEATH. No real Turso or OpenAI network access.
"""
from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))
sys.path.insert(0, str(ROOT / "tests"))
# This is a separate process-level CI test invocation, before the import that
# initializes MemconOS. Fail closed on any accidentally configured Turso URL.
_TMP = tempfile.TemporaryDirectory(prefix="galaxy-real-render-bridge-fixture-")
os.environ["MEMCONOS_DB_PATH"] = str(Path(_TMP.name) / "synthetic-memcon.db")
os.environ.pop("TURSO_DATABASE_URL", None)
os.environ.pop("TURSO_AUTH_TOKEN", None)
os.environ["RENDER_GIT_COMMIT"] = "STAGE9REALBRIDGE-SYNTHETIC-COMMIT"
import gaiaos_api as carrier
import gaiaos_memory_mode as mode
import gaiaos_memory_gateway as gateway
import galaxy_phase3_exit
import browser_memcon_bridge as served
from test_bigbang_operational_reader_stage6 import FakeMemory, candidate_pool

QUERY = "gravity contextual influence memory retrieval"
AUTH = {
    "schema": mode.SCHEMA,
    "effective_mode": mode.BIGBANG,
    "configured_mode": mode.BIGBANG,
    "bigbang_activation_enabled": True,
    "reason": "CI_FAKE_FUTURE_RELEASE_NEVER_REAL_AUTHORIZATION",
}
HEATDEATH = {
    "schema": mode.SCHEMA,
    "effective_mode": mode.HEATDEATH,
    "configured_mode": mode.HEATDEATH,
    "bigbang_activation_enabled": False,
    "reason": "CI_HEATDEATH",
}


class _SyntheticModel:
    def __init__(self):
        self.calls: list[dict] = []
        self.responses = SimpleNamespace(create=self.create)

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_text="Fixture-only non-Daemon response.")


class ActualRenderBridgeTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        _TMP.cleanup()

    def setUp(self):
        self.model = _SyntheticModel()
        self.patches = [
            patch.object(carrier, "API_KEY", "CI-OWNER-SESSION-NOT-REAL-SECRET"),
            patch.object(carrier, "OPENAI_API_KEY", "CI-FAKE-MODEL-KEY-NOT-REAL"),
            patch.object(carrier, "OpenAI", return_value=self.model),
            patch.object(carrier, "_load_bundle", return_value={
                "gaiaos": {"source": "STAGE9-ISOLATED-BUILT-IMAGE-REVIEW"},
            }),
            patch.object(
                carrier, "_carrier_instructions",
                return_value="Trusted fixture carrier.",
            ),
            patch.object(served.memcon_runtime, "get_solo_session",
                         return_value=None),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)
        self.client = TestClient(served.app, base_url="https://testserver")
        self.client.cookies.set(carrier.SESSION_COOKIE, carrier._session_token())

    def post(self, **fields):
        return self.client.post("/chat", json={
            "messages": [{"role": "user", "content": QUERY}],
            **fields,
        })

    def test_actual_docker_entrypoint_has_exactly_one_bridge_owned_post_chat(self):
        docker = (ROOT / "api/Dockerfile").read_text()
        self.assertIn("uvicorn browser_memcon_bridge:app", docker)
        self.assertIn(
            "COPY api/galaxy_legacy_gravity.py ./galaxy_legacy_gravity.py",
            docker,
        )
        self.assertIn(
            "COPY api/gaiaos_chat_auto_memory.py ./gaiaos_chat_auto_memory.py",
            docker,
        )
        # Owner-local migration, signing and private archive tooling must NOT
        # ride along in a Render service and must never load on normal /chat.
        for name in (
            "galaxy_stage9ag_staging_historical_import.py",
            "galaxy_stage9ah_signed_staging_rollback.py",
            "galaxy_stage9ab_owner_local_bootstrap.py",
            "galaxy_archive_staging.py",
        ):
            self.assertNotIn("COPY api/" + name, docker)
        browser = [
            r for r in served.app.routes
            if isinstance(r, APIRoute)
            and r.path == "/chat"
            and "POST" in r.methods
        ]
        self.assertEqual(len(browser), 1)
        self.assertIs(browser[0].endpoint, served.browser_chat)
        self.assertIsNot(browser[0].endpoint, carrier.browser_chat)
        self.assertIs(served.app, carrier.app)

    def test_actual_controller_stays_heatdeath_even_with_synthetic_bigbang_row(self):
        class SyntheticModeRuntime:
            def _db(self):
                conn = sqlite3.connect(":memory:")
                conn.execute(
                    "CREATE TABLE gaiaos_memory_mode_control ("
                    "control_id INTEGER, selected_mode TEXT, authority TEXT,"
                    "approved_at TEXT, version INTEGER)"
                )
                conn.execute(
                    "INSERT INTO gaiaos_memory_mode_control VALUES"
                    "(1,'BIGBANG','NAOMI','2026-09-27',1)"
                )
                return conn

        state = mode.mode_status(SyntheticModeRuntime(), environ={})
        self.assertEqual(state["configured_mode"], mode.BIGBANG)
        self.assertEqual(state["effective_mode"], mode.HEATDEATH)
        self.assertFalse(state["bigbang_activation_enabled"])
        self.assertEqual(state["reason"], "BIGBANG_RELEASE_GATE_NOT_YET_IMPLEMENTED")

    def test_actual_served_browser_session_rejects_unauthorized_before_lookup(self):
        self.client.cookies.clear()
        with patch.object(
            gateway, "read",
            side_effect=AssertionError("NO MEMORY READ WITHOUT OWNER SESSION"),
        ):
            result = self.post()
        self.assertEqual(result.status_code, 401)
        self.assertEqual(self.model.calls, [])

    def test_actual_served_heatdeath_makes_no_implicit_memory_lookup(self):
        with patch.object(
            mode, "mode_status", return_value=HEATDEATH,
        ), patch.object(
            gateway, "read",
            side_effect=AssertionError("HEATDEATH MUST NOT READ GALAXY"),
        ):
            result = self.post()
        self.assertEqual(result.status_code, 200, result.text)
        self.assertNotIn("memory_context", result.json())
        self.assertNotIn("memory_gateway_receipt", result.json())
        self.assertEqual(len(self.model.calls), 1)
        self.assertEqual(
            self.model.calls[0]["instructions"], "Trusted fixture carrier.",
        )

    def test_actual_bridge_respects_explicit_opt_out_even_if_bigbang_mocked(self):
        # Previously /chat's real bridge ignored include_memory=False,
        # although tests of the unused gaiaos_api.browser_chat honored it.
        with patch.object(
            mode, "mode_status",
            side_effect=AssertionError(
                "EXPLICIT OPT OUT MUST NOT EVEN READ SHARED CONTROL"
            ),
        ), patch.object(
            gateway, "read",
            side_effect=AssertionError("EXPLICIT OPT OUT MUST NOT SEARCH"),
        ):
            result = self.post(include_memory=False)
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(len(self.model.calls), 1)
        self.assertNotIn("memory_context", result.json())
        self.assertNotIn("memory_gateway_receipt", result.json())
        self.assertEqual(
            self.model.calls[0]["instructions"], "Trusted fixture carrier.",
        )

    def test_mock_future_bigbang_uses_real_reader_gateway_and_final_model(self):
        fake_memory = FakeMemory()
        actual_gateway_read = gateway.read

        def route_to_synthetic_runtime(actual_runtime, query, scope, limit):
            self.assertIs(actual_runtime, served.memcon_runtime)
            self.assertEqual(scope, "MemoryOS")
            self.assertEqual(limit, 4)
            return actual_gateway_read(fake_memory, query, scope, limit)

        with patch.object(
            mode, "mode_status", return_value=AUTH,
        ), patch.object(
            gateway, "read", side_effect=route_to_synthetic_runtime,
        ), patch.object(
            galaxy_phase3_exit, "build_candidate_pool",
            side_effect=candidate_pool,
        ):
            result = self.post()
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(len(self.model.calls), 1)
        instructions = self.model.calls[0]["instructions"]
        self.assertIn("BOUNDED MEMORY CONTEXT", instructions)
        self.assertIn("proof:current", instructions)
        self.assertIn("proof:linked", instructions)
        self.assertNotIn("history context revision memory", instructions)
        response = result.json()
        self.assertEqual(
            response["memory_context"]["status"],
            "BIGBANG_VERIFIED_CONTEXT_USED",
        )
        self.assertEqual(
            response["memory_context"]["current_record_ids"], ["CURRENT"],
        )
        self.assertEqual(
            response["memory_context"]["context_only_record_ids"], ["LINKED"],
        )
        self.assertEqual(
            response["memory_gateway_receipt"]["gateway_status"],
            "PASS_BIGBANG",
        )
        self.assertTrue(
            response["memory_gateway_receipt"]["enhanced_context_used"],
        )

    def test_optional_galaxy_failure_falls_back_to_clean_original_chat(self):
        fake_memory = FakeMemory()
        actual_gateway_read = gateway.read

        def with_missing_optional_dependency(actual_runtime, query, scope, limit):
            with patch.dict(sys.modules, {"galaxy_legacy_gravity": None}):
                return actual_gateway_read(fake_memory, query, scope, limit)

        with patch.object(
            mode, "mode_status", return_value=AUTH,
        ), patch.object(
            gateway, "read", side_effect=with_missing_optional_dependency,
        ), patch.object(
            galaxy_phase3_exit, "build_candidate_pool",
            side_effect=candidate_pool,
        ):
            result = self.post()
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(len(self.model.calls), 1)
        self.assertEqual(
            self.model.calls[0]["instructions"], "Trusted fixture carrier.",
        )
        receipt = result.json()["memory_gateway_receipt"]
        self.assertEqual(receipt["gateway_status"], "PASS_HEATDEATH_FALLBACK")
        self.assertFalse(receipt["enhanced_context_used"])

    def test_staged_archive_cannot_leak_from_misrouted_legacy_into_real_chat(self):
        fake_memory = FakeMemory()
        fake_memory.records["CURRENT"]["status"] = "STAGED_HISTORICAL_HOLD"
        fake_memory.records["CURRENT"]["source"] = (
            "galaxy-archive-v1:" + "a" * 64
        )
        actual_gateway_read = gateway.read

        def read_fixture(actual_runtime, query, scope, limit):
            return actual_gateway_read(fake_memory, query, scope, limit)

        with patch.object(
            mode, "mode_status", return_value=AUTH,
        ), patch.object(
            gateway, "read", side_effect=read_fixture,
        ):
            result = self.post()
        self.assertEqual(result.status_code, 200, result.text)
        self.assertNotIn("memory_context", result.json())
        self.assertEqual(
            result.json()["memory_gateway_receipt"]["gateway_status"],
            "HOLD_UNRELEASED_ARCHIVE_IN_LEGACY",
        )
        instructions = self.model.calls[0]["instructions"]
        self.assertEqual(instructions, "Trusted fixture carrier.")
        self.assertNotIn("galaxy-archive-v1:", result.text)


if __name__ == "__main__":
    unittest.main()
